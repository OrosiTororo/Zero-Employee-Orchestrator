/// Zero-Employee Orchestrator - Tauri desktop shell
///
/// The desktop app wraps the React frontend and communicates
/// with the Python FastAPI backend running as a sidecar process.

use std::path::PathBuf;
use std::process::{Child, Command};
use std::sync::Mutex;
use std::time::Duration;
use tauri::Manager;

struct BackendProcess(Mutex<Option<Child>>);

/// Cached API directory so we can re-use it for restarts.
struct ApiDir(Mutex<Option<PathBuf>>);

/// Find the API directory relative to the executable or project root.
fn find_api_dir() -> Option<PathBuf> {
    // Build a list of candidate paths from multiple strategies.
    let mut candidates = vec![
        // When running from apps/desktop/src-tauri (cargo tauri dev)
        PathBuf::from("../../api"),
        // When running from project root
        PathBuf::from("apps/api"),
        // When running from apps/desktop
        PathBuf::from("../api"),
    ];

    // Also try paths relative to the executable location (production builds)
    if let Ok(exe) = std::env::current_exe() {
        if let Some(exe_dir) = exe.parent() {
            // e.g. /usr/bin/../share/zero-employee-orchestrator/api
            candidates.push(exe_dir.join("../share/zero-employee-orchestrator/api"));
            // Portable layout: executable next to apps/api
            candidates.push(exe_dir.join("apps/api"));
            candidates.push(exe_dir.join("../../apps/api"));
            // macOS .app bundle: Contents/MacOS/../../Resources/api
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
/// Uses the official installer script (https://docs.astral.sh/uv/getting-started/installation/).
fn ensure_uv() -> bool {
    if has_uv() {
        return true;
    }

    eprintln!("[sidecar] uv not found, installing automatically...");

    let result = if cfg!(windows) {
        // Windows: powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
        Command::new("powershell")
            .args([
                "-ExecutionPolicy",
                "ByPass",
                "-c",
                "irm https://astral.sh/uv/install.ps1 | iex",
            ])
            .output()
    } else {
        // macOS/Linux: curl -LsSf https://astral.sh/uv/install.sh | sh
        Command::new("sh")
            .args(["-c", "curl -LsSf https://astral.sh/uv/install.sh | sh"])
            .output()
    };

    match result {
        Ok(out) if out.status.success() => {
            eprintln!("[sidecar] uv installed successfully");
            // The installer adds uv to ~/.local/bin or ~/.cargo/bin.
            // Update PATH for the current process so subsequent Commands can find it.
            if let Ok(home) = std::env::var("HOME") {
                if let Ok(path) = std::env::var("PATH") {
                    let extra = format!("{}/.local/bin:{}/.cargo/bin", home, home);
                    std::env::set_var("PATH", format!("{}:{}", extra, path));
                }
            }
            // Verify it's actually available now
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
/// `uv` also auto-downloads Python 3.12 if not present on the system.
/// Returns (python_path, did_auto_setup).
fn find_python(api_dir: &PathBuf) -> (String, bool) {
    // Prefer the virtual environment bundled with the API
    let venv_python = if cfg!(windows) {
        api_dir.join(".venv").join("Scripts").join("python.exe")
    } else {
        api_dir.join(".venv").join("bin").join("python")
    };
    if venv_python.exists() {
        return (venv_python.to_string_lossy().to_string(), false);
    }

    // Ensure uv is available (auto-install if needed)
    if !ensure_uv() {
        // Last resort: try system Python directly
        eprintln!("[sidecar] warning: could not install uv, falling back to system python");
        if cfg!(windows) {
            return ("python".to_string(), false);
        } else {
            return ("python3".to_string(), false);
        }
    }

    // uv is available — create venv with Python 3.12 (uv auto-downloads Python if needed)
    eprintln!("[sidecar] .venv not found, auto-setup with uv (Python will be downloaded if needed)...");
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
    // Even if venv creation failed, uv run can still work
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

        // Fallback: try a raw TCP connect if curl is unavailable
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

fn spawn_backend_inner(api_dir: &PathBuf) -> Option<Child> {
    let (python, did_auto_setup) = find_python(api_dir);
    eprintln!(
        "[sidecar] starting backend: python={}, dir={}, auto_setup={}",
        python,
        api_dir.display(),
        did_auto_setup,
    );

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
            .spawn()
    };

    match child {
        Ok(mut c) => {
            eprintln!("[sidecar] backend process spawned (pid={})", c.id());
            // Brief pause then check if the process crashed immediately
            std::thread::sleep(Duration::from_millis(500));
            match c.try_wait() {
                Ok(Some(status)) => {
                    eprintln!(
                        "[sidecar] backend process exited immediately with {status}. \
                         Check that Python >= 3.12 is installed and dependencies are set up \
                         (run: cd apps/api && uv venv --python 3.12 .venv && uv pip install -e .)"
                    );
                    return None;
                }
                Ok(None) => { /* still running — good */ }
                Err(e) => eprintln!("[sidecar] could not check process status: {e}"),
            }
            // Wait for backend to respond. Don't block too long here —
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
            Some(c)
        }
        Err(e) => {
            eprintln!("[sidecar] failed to start backend: {e}");
            None
        }
    }
}

fn spawn_backend() -> (Option<Child>, Option<PathBuf>) {
    let api_dir = match find_api_dir() {
        Some(d) => d,
        None => {
            eprintln!("[sidecar] could not locate apps/api directory");
            return (None, None);
        }
    };

    let child = spawn_backend_inner(&api_dir);
    (child, Some(api_dir))
}

/// Tauri command: restart the backend process from the frontend.
#[tauri::command]
fn restart_backend(
    backend: tauri::State<'_, BackendProcess>,
    api_dir_state: tauri::State<'_, ApiDir>,
) -> Result<String, String> {
    // Kill existing process if any
    if let Ok(mut guard) = backend.0.lock() {
        if let Some(mut child) = guard.take() {
            eprintln!("[sidecar] killing existing backend (pid={})", child.id());
            let _ = child.kill();
            let _ = child.wait();
        }
    }

    // Determine API directory
    let api_dir = {
        let dir_guard = api_dir_state
            .0
            .lock()
            .map_err(|e| format!("lock error: {e}"))?;
        dir_guard.clone()
    };

    let api_dir = match api_dir.or_else(find_api_dir) {
        Some(d) => d,
        None => return Err("API directory not found".to_string()),
    };

    let child = spawn_backend_inner(&api_dir);
    if child.is_some() {
        if let Ok(mut guard) = backend.0.lock() {
            *guard = child;
        }
        Ok("started".to_string())
    } else {
        Err("Backend failed to start".to_string())
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

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .plugin(tauri_plugin_updater::Builder::new().build())
        .invoke_handler(tauri::generate_handler![
            restart_backend,
            check_backend_health
        ])
        .setup(|app| {
            // Spawn the Python backend as a sidecar process
            let (child, api_dir) = spawn_backend();
            app.manage(BackendProcess(Mutex::new(child)));
            app.manage(ApiDir(Mutex::new(api_dir)));
            Ok(())
        })
        .on_window_event(|window, event| {
            if let tauri::WindowEvent::Destroyed = event {
                // Kill the backend process when the window is closed
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
