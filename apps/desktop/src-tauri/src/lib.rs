/// Zero-Employee Orchestrator - Tauri desktop shell
///
/// The desktop app wraps the React frontend and communicates
/// with the Python FastAPI backend running as a sidecar process.

use std::io::Write;
use std::path::PathBuf;
use std::process::{Child, Command, Stdio};
use std::sync::Mutex;
use std::time::Duration;
use tauri::Manager;

struct BackendProcess(Mutex<Option<Child>>);

/// Cached API directory so we can re-use it for restarts.
struct ApiDir(Mutex<Option<PathBuf>>);

/// Last error message from backend startup, readable by frontend.
struct BackendError(Mutex<Option<String>>);

/// Find the API directory relative to the executable or project root.
fn find_api_dir() -> Option<PathBuf> {
    let mut candidates = vec![
        PathBuf::from("../../api"),
        PathBuf::from("apps/api"),
        PathBuf::from("../api"),
    ];

    if let Ok(exe) = std::env::current_exe() {
        if let Some(exe_dir) = exe.parent() {
            candidates.push(exe_dir.join("../share/zero-employee-orchestrator/api"));
            candidates.push(exe_dir.join("apps/api"));
            candidates.push(exe_dir.join("../../apps/api"));
            candidates.push(exe_dir.join("../Resources/api"));
        }
    }

    for candidate in &candidates {
        let resolved = std::fs::canonicalize(candidate).ok();
        if let Some(ref p) = resolved {
            if p.join("app").join("main.py").exists() {
                eprintln!("[sidecar] found API directory: {}", p.display());
                return resolved;
            }
        }
    }

    eprintln!(
        "[sidecar] could not find API directory. Tried {} paths from cwd={:?}",
        candidates.len(),
        std::env::current_dir().ok()
    );
    None
}

/// Check if `uv` is available on the system.
fn has_uv() -> bool {
    Command::new("uv").arg("--version").output().is_ok()
}

/// Install `uv` automatically if not present.
fn ensure_uv() -> bool {
    if has_uv() {
        return true;
    }

    eprintln!("[sidecar] uv not found, installing automatically...");

    let result = if cfg!(windows) {
        Command::new("powershell")
            .args([
                "-ExecutionPolicy",
                "ByPass",
                "-c",
                "irm https://astral.sh/uv/install.ps1 | iex",
            ])
            .output()
    } else {
        Command::new("sh")
            .args(["-c", "curl -LsSf https://astral.sh/uv/install.sh | sh"])
            .output()
    };

    match result {
        Ok(out) if out.status.success() => {
            eprintln!("[sidecar] uv installed successfully");
            if let Ok(home) = std::env::var("HOME") {
                if let Ok(path) = std::env::var("PATH") {
                    let extra = format!("{}/.local/bin:{}/.cargo/bin", home, home);
                    std::env::set_var("PATH", format!("{}:{}", extra, path));
                }
            }
            if has_uv() {
                return true;
            }
            eprintln!("[sidecar] uv installed but not found on PATH");
            false
        }
        Ok(out) => {
            eprintln!(
                "[sidecar] uv installation failed: {}",
                String::from_utf8_lossy(&out.stderr)
            );
            false
        }
        Err(e) => {
            eprintln!("[sidecar] failed to run uv installer: {e}");
            false
        }
    }
}

/// Find a working Python interpreter (prefer .venv inside api dir).
/// Automatically installs `uv` if needed, then creates venv and installs deps.
/// Returns (python_path, did_auto_setup).
fn find_python(api_dir: &PathBuf) -> (String, bool) {
    let venv_python = if cfg!(windows) {
        api_dir.join(".venv").join("Scripts").join("python.exe")
    } else {
        api_dir.join(".venv").join("bin").join("python")
    };
    if venv_python.exists() {
        return (venv_python.to_string_lossy().to_string(), false);
    }

    if !ensure_uv() {
        eprintln!("[sidecar] warning: could not install uv, falling back to system python");
        if cfg!(windows) {
            return ("python".to_string(), false);
        } else {
            return ("python3".to_string(), false);
        }
    }

    eprintln!("[sidecar] .venv not found, auto-setup with uv...");
    let venv_result = Command::new("uv")
        .args(["venv", "--python", "3.12", ".venv"])
        .current_dir(api_dir)
        .output();
    match venv_result {
        Ok(out) if out.status.success() => {
            eprintln!("[sidecar] created .venv with Python 3.12");
            let install_result = Command::new("uv")
                .args(["pip", "install", "-e", "."])
                .current_dir(api_dir)
                .output();
            match install_result {
                Ok(out) if out.status.success() => {
                    eprintln!("[sidecar] dependencies installed successfully");
                }
                Ok(out) => {
                    eprintln!(
                        "[sidecar] dependency install failed: {}",
                        String::from_utf8_lossy(&out.stderr)
                    );
                }
                Err(e) => eprintln!("[sidecar] failed to run uv pip install: {e}"),
            }
            if venv_python.exists() {
                return (venv_python.to_string_lossy().to_string(), true);
            }
        }
        Ok(out) => {
            eprintln!(
                "[sidecar] uv venv creation failed: {}",
                String::from_utf8_lossy(&out.stderr)
            );
        }
        Err(e) => eprintln!("[sidecar] failed to run uv: {e}"),
    }
    ("uv".to_string(), true)
}

/// Wait until the backend health endpoint responds.
fn wait_for_backend(max_attempts: u32) -> bool {
    for i in 0..max_attempts {
        let delay = if i == 0 { 500 } else { 1000 };
        std::thread::sleep(Duration::from_millis(delay));

        if let Ok(output) = Command::new("curl")
            .args(["-sf", "http://127.0.0.1:18234/healthz"])
            .output()
        {
            if output.status.success() {
                return true;
            }
        }

        if std::net::TcpStream::connect_timeout(
            &"127.0.0.1:18234".parse().unwrap(),
            Duration::from_secs(1),
        )
        .is_ok()
        {
            return true;
        }
    }
    eprintln!("[sidecar] backend did not become ready within timeout");
    false
}

/// Generate a .env file in the API directory if it doesn't already exist.
/// This mirrors the setup logic in start.sh that the sidecar would otherwise skip.
fn ensure_env_file(api_dir: &PathBuf) {
    let env_path = api_dir.join(".env");
    if env_path.exists() {
        return;
    }

    eprintln!("[sidecar] .env not found, generating default configuration...");

    // Generate a random secret key using Python or a fallback
    let secret = Command::new("python3")
        .args(["-c", "import secrets; print(secrets.token_urlsafe(32))"])
        .output()
        .ok()
        .filter(|o| o.status.success())
        .and_then(|o| String::from_utf8(o.stdout).ok())
        .map(|s| s.trim().to_string())
        .unwrap_or_else(|| {
            // Fallback: generate a simple random string in Rust
            use std::time::{SystemTime, UNIX_EPOCH};
            let ts = SystemTime::now()
                .duration_since(UNIX_EPOCH)
                .unwrap_or_default()
                .as_millis();
            format!("auto-tauri-{}", ts)
        });

    let env_content = format!(
        r#"DATABASE_URL=sqlite+aiosqlite:///./zero_employee_orchestrator.db
SECRET_KEY={}
DEBUG=true
CORS_ORIGINS=["http://localhost:5173","http://localhost:3000","tauri://localhost","https://tauri.localhost"]
DEFAULT_EXECUTION_MODE=subscription
USE_G4F=true
"#,
        secret
    );

    match std::fs::File::create(&env_path) {
        Ok(mut f) => {
            if f.write_all(env_content.as_bytes()).is_ok() {
                eprintln!("[sidecar] .env file created successfully");
            } else {
                eprintln!("[sidecar] failed to write .env file");
            }
        }
        Err(e) => eprintln!("[sidecar] failed to create .env file: {e}"),
    }
}

/// Kill any existing process listening on port 18234.
fn kill_port_18234() {
    if cfg!(windows) {
        // netstat -ano | findstr :18234 → taskkill /PID ... /F
        if let Ok(output) = Command::new("cmd")
            .args(["/C", "for /f \"tokens=5\" %a in ('netstat -ano ^| findstr :18234 ^| findstr LISTENING') do taskkill /PID %a /F"])
            .output()
        {
            if output.status.success() {
                eprintln!("[sidecar] killed existing process on port 18234");
            }
        }
    } else {
        // lsof -ti :18234 | xargs kill -9
        if let Ok(output) = Command::new("sh")
            .args(["-c", "lsof -ti :18234 | xargs kill -9 2>/dev/null"])
            .output()
        {
            if output.status.success() {
                eprintln!("[sidecar] killed existing process on port 18234");
                std::thread::sleep(Duration::from_millis(500));
            }
        }
    }
}

/// Check if port 18234 is already in use.
fn is_port_in_use() -> bool {
    std::net::TcpStream::connect_timeout(
        &"127.0.0.1:18234".parse().unwrap(),
        Duration::from_millis(500),
    )
    .is_ok()
}

fn spawn_backend_inner(api_dir: &PathBuf) -> Result<Child, String> {
    // Ensure .env file exists (equivalent to start.sh's auto-generation)
    ensure_env_file(api_dir);

    // If port is already in use, try to free it
    if is_port_in_use() {
        eprintln!("[sidecar] port 18234 is already in use, attempting to free it...");
        kill_port_18234();
        if is_port_in_use() {
            return Err(
                "ポート 18234 が他のプロセスに使用されています。\
                 前回のプロセスが残っている可能性があります。"
                    .to_string(),
            );
        }
    }

    let (python, did_auto_setup) = find_python(api_dir);
    eprintln!(
        "[sidecar] starting backend: python={}, dir={}, auto_setup={}",
        python,
        api_dir.display(),
        did_auto_setup,
    );

    // Capture stderr so we can report errors to the frontend
    let child = if python == "uv" {
        Command::new("uv")
            .args([
                "run",
                "uvicorn",
                "app.main:app",
                "--host",
                "127.0.0.1",
                "--port",
                "18234",
            ])
            .current_dir(api_dir)
            .stderr(Stdio::piped())
            .spawn()
    } else {
        Command::new(&python)
            .args([
                "-m",
                "uvicorn",
                "app.main:app",
                "--host",
                "127.0.0.1",
                "--port",
                "18234",
            ])
            .current_dir(api_dir)
            .stderr(Stdio::piped())
            .spawn()
    };

    match child {
        Ok(mut c) => {
            eprintln!("[sidecar] backend process spawned (pid={})", c.id());
            std::thread::sleep(Duration::from_millis(500));
            match c.try_wait() {
                Ok(Some(status)) => {
                    // Process crashed immediately — read stderr for the reason
                    let mut error_msg = format!("バックエンドが起動直後にクラッシュしました (exit {status})");
                    if let Some(stderr) = c.stderr.take() {
                        use std::io::Read;
                        let mut buf = String::new();
                        let mut reader = std::io::BufReader::new(stderr);
                        let _ = reader.read_to_string(&mut buf);
                        if !buf.is_empty() {
                            // Take last 500 chars of stderr for useful error context
                            let tail: String = buf.chars().rev().take(500).collect::<Vec<_>>().into_iter().rev().collect();
                            eprintln!("[sidecar] backend stderr:\n{}", tail);
                            error_msg = format!("{}\n\n{}", error_msg, tail.trim());
                        }
                    }
                    return Err(error_msg);
                }
                Ok(None) => { /* still running — good */ }
                Err(e) => eprintln!("[sidecar] could not check process status: {e}"),
            }
            // Wait for backend to respond. Don't block too long —
            // the frontend BackendGuard will continue polling and retrying.
            let max_wait = if did_auto_setup { 30 } else { 15 };
            let ready = wait_for_backend(max_wait);
            if !ready {
                eprintln!(
                    "[sidecar] backend not yet ready after {}s, \
                     frontend will continue polling",
                    max_wait
                );
            }
            Ok(c)
        }
        Err(e) => {
            Err(format!(
                "バックエンドプロセスの起動に失敗しました: {e}"
            ))
        }
    }
}

fn spawn_backend() -> (Option<Child>, Option<PathBuf>, Option<String>) {
    let api_dir = match find_api_dir() {
        Some(d) => d,
        None => {
            return (
                None,
                None,
                Some("API ディレクトリが見つかりません。".to_string()),
            );
        }
    };

    match spawn_backend_inner(&api_dir) {
        Ok(child) => (Some(child), Some(api_dir), None),
        Err(err) => (None, Some(api_dir), Some(err)),
    }
}

/// Tauri command: restart the backend process from the frontend.
#[tauri::command]
fn restart_backend(
    backend: tauri::State<'_, BackendProcess>,
    api_dir_state: tauri::State<'_, ApiDir>,
    error_state: tauri::State<'_, BackendError>,
) -> Result<String, String> {
    // Kill existing process if any
    if let Ok(mut guard) = backend.0.lock() {
        if let Some(mut child) = guard.take() {
            eprintln!("[sidecar] killing existing backend (pid={})", child.id());
            let _ = child.kill();
            let _ = child.wait();
        }
    }

    let api_dir = {
        let dir_guard = api_dir_state
            .0
            .lock()
            .map_err(|e| format!("lock error: {e}"))?;
        dir_guard.clone()
    };

    let api_dir = match api_dir.or_else(find_api_dir) {
        Some(d) => d,
        None => return Err("API ディレクトリが見つかりません。".to_string()),
    };

    match spawn_backend_inner(&api_dir) {
        Ok(child) => {
            if let Ok(mut guard) = backend.0.lock() {
                *guard = Some(child);
            }
            if let Ok(mut err) = error_state.0.lock() {
                *err = None;
            }
            Ok("started".to_string())
        }
        Err(e) => {
            if let Ok(mut err) = error_state.0.lock() {
                *err = Some(e.clone());
            }
            Err(e)
        }
    }
}

/// Tauri command: check if the backend health endpoint is reachable.
#[tauri::command]
fn check_backend_health() -> bool {
    if let Ok(output) = Command::new("curl")
        .args(["-sf", "http://127.0.0.1:18234/healthz"])
        .output()
    {
        if output.status.success() {
            return true;
        }
    }
    std::net::TcpStream::connect_timeout(
        &"127.0.0.1:18234".parse().unwrap(),
        Duration::from_secs(2),
    )
    .is_ok()
}

/// Tauri command: get the last backend startup error (if any).
#[tauri::command]
fn get_backend_error(error_state: tauri::State<'_, BackendError>) -> Option<String> {
    error_state.0.lock().ok().and_then(|e| e.clone())
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .plugin(tauri_plugin_updater::Builder::new().build())
        .invoke_handler(tauri::generate_handler![
            restart_backend,
            check_backend_health,
            get_backend_error
        ])
        .setup(|app| {
            let (child, api_dir, error) = spawn_backend();
            app.manage(BackendProcess(Mutex::new(child)));
            app.manage(ApiDir(Mutex::new(api_dir)));
            app.manage(BackendError(Mutex::new(error)));
            Ok(())
        })
        .on_window_event(|window, event| {
            if let tauri::WindowEvent::Destroyed = event {
                if let Some(state) = window.try_state::<BackendProcess>() {
                    if let Ok(mut guard) = state.0.lock() {
                        if let Some(mut child) = guard.take() {
                            eprintln!("[sidecar] shutting down backend (pid={})", child.id());
                            let _ = child.kill();
                            let _ = child.wait();
                        }
                    }
                }
            }
        })
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
