#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

// The desktop shell is intentionally minimal: it loads the SvelteKit build
// (in release) or the dev server (in debug) and calls out to the FastAPI
// backend over HTTP, exactly like the browser version.
fn main() {
    tauri::Builder::default()
        .run(tauri::generate_context!())
        .expect("error while running Pro-AI Control desktop app");
}
