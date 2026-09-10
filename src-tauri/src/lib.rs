use std::{
    io::{BufRead, BufReader, Write},
    path::PathBuf,
    process::{Child, ChildStdin, Command, Stdio},
    sync::Mutex,
    thread,
};

use serde_json::{json, Value};
use tauri::{AppHandle, Emitter, Manager, State};

pub struct BridgeState {
    stdin: Mutex<Option<ChildStdin>>,
    _child: Mutex<Option<Child>>,
}

fn start_bridge(app: &AppHandle) -> Result<BridgeState, String> {
    let project_root = PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .parent()
        .ok_or_else(|| "project root tidak ditemukan".to_string())?
        .to_path_buf();
    let bridge = project_root.join("gui_bridge.py");
    let mut child = Command::new("python")
        .arg(&bridge)
        .current_dir(&project_root)
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .spawn()
        .map_err(|error| format!("gagal menjalankan Python bridge: {error}"))?;

    let stdout = child.stdout.take().ok_or_else(|| "stdout bridge tidak tersedia".to_string())?;
    let stderr = child.stderr.take().ok_or_else(|| "stderr bridge tidak tersedia".to_string())?;
    let app_for_stdout = app.clone();
    thread::spawn(move || {
        for line in BufReader::new(stdout).lines().flatten() {
            if let Ok(event) = serde_json::from_str::<Value>(&line) {
                let _ = app_for_stdout.emit("astral-event", event);
            }
        }
    });
    thread::spawn(move || {
        for line in BufReader::new(stderr).lines().flatten() {
            eprintln!("[astral bridge] {line}");
        }
    });

    let stdin = child.stdin.take();
    Ok(BridgeState { stdin: Mutex::new(stdin), _child: Mutex::new(Some(child)) })
}

fn write_command(state: &BridgeState, command: Value) -> Result<(), String> {
    let mut guard = state.stdin.lock().map_err(|_| "bridge lock rusak".to_string())?;
    let stdin = guard.as_mut().ok_or_else(|| "Python bridge tidak aktif".to_string())?;
    writeln!(stdin, "{}", command).map_err(|error| format!("gagal mengirim command: {error}"))?;
    stdin.flush().map_err(|error| format!("gagal flush command: {error}"))
}

#[tauri::command]
fn send_message(state: State<'_, BridgeState>, text: String) -> Result<(), String> {
    write_command(&state, json!({"type": "user_message", "text": text}))
}

#[tauri::command]
fn permission_response(state: State<'_, BridgeState>, id: String, approved: bool) -> Result<(), String> {
    write_command(&state, json!({"type": "permission_result", "id": id, "approved": approved}))
}

#[tauri::command]
fn reset_session(state: State<'_, BridgeState>) -> Result<(), String> {
    write_command(&state, json!({"type": "new_chat"}))
}

#[tauri::command]
fn bridge_status(state: State<'_, BridgeState>) -> bool {
    state.stdin.lock().map(|guard| guard.is_some()).unwrap_or(false)
}

#[tauri::command]
fn set_provider(state: State<'_, BridgeState>, provider: String) -> Result<(), String> {
    write_command(&state, json!({"type": "set_provider", "provider": provider}))
}

#[tauri::command]
fn bridge_command(state: State<'_, BridgeState>, command: Value) -> Result<(), String> {
    write_command(&state, command)
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .setup(|app| {
            let state = start_bridge(&app.handle())?;
            app.manage(state);
            Ok(())
        })
        .invoke_handler(tauri::generate_handler![send_message, permission_response, reset_session, bridge_status, set_provider, bridge_command])
        .run(tauri::generate_context!())
        .expect("error while running Astral");
}
