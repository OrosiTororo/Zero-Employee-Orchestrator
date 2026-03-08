/// Zero-Employee Orchestrator - Tauri desktop shell
///
/// The desktop app wraps the React frontend and communicates
/// with the Python FastAPI backend running as a sidecar process.

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
