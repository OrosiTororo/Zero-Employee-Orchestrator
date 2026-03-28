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

/// Find a working Python interpreter (prefer .venv inside api dir).
/// If no .venv exists but `uv` is available, automatically create one and install deps.
fn find_python(api_dir: &PathBuf) -> String {
    // Prefer the virtual environment bundled with the API
    let venv_python = if cfg!(windows) {
        api_dir.join(".venv").join("Scripts").join("python.exe")
    } else {
        api_dir.join(".venv").join("bin").join("python")
    };
    if venv_python.exists() {
        return venv_python.to_string_lossy().to_string();
    }

    // No .venv found — try to auto-create with uv if available
    if Command::new("uv").arg("--version").output().is_ok() {
        eprintln!("[sidecar] .venv not found, attempting auto-setup with uv...");
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
                    return venv_python.to_string_lossy().to_string();
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
        return "uv".to_string();
    }

    // Fallback to system Python
    eprintln!("[sidecar] warning: no .venv and uv not found, using system python");
    if cfg!(windows) { "python".to_string() } else { "python3".to_string() }
}

/// Wait until the backend health endpoint responds (up to ~10 s).
fn wait_for_backend(max_attempts: u32) {
    for i in 0..max_attempts {
        let delay = if i == 0 { 500 } else { 1000 };
        std::thread::sleep(Duration::from_millis(delay));

        if let Ok(output) = Command::new("curl")
            .args(["-sf", "http://127.0.0.1:18234/healthz"])
            .output()
        {
            if output.status.success() {
                return;
            }
        }

        // Fallback: try a raw TCP connect if curl is unavailable
        if std::net::TcpStream::connect_timeout(
            &"127.0.0.1:18234".parse().unwrap(),
            Duration::from_secs(1),
        )
        .is_ok()
        {
            return;
        }
    }
    eprintln!("[sidecar] backend did not become ready within timeout");
}

fn spawn_backend() -> Option<Child> {
    let api_dir = match find_api_dir() {
        Some(d) => d,
        None => {
            eprintln!("[sidecar] could not locate apps/api directory");
            return None;
        }
    };

    let python = find_python(&api_dir);
    eprintln!(
        "[sidecar] starting backend: python={}, dir={}",
        python,
        api_dir.display()
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
            .current_dir(&api_dir)
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
            .current_dir(&api_dir)
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
            // Give the backend time to fully start
            wait_for_backend(15);
            Some(c)
        }
        Err(e) => {
            eprintln!("[sidecar] failed to start backend: {e}");
            None
        }
    }
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .plugin(tauri_plugin_updater::Builder::new().build())
        .setup(|app| {
            // Spawn the Python backend as a sidecar process
            let child = spawn_backend();
            app.manage(BackendProcess(Mutex::new(child)));
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
