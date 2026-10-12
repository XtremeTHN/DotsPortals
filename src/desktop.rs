use gio_unix::DesktopAppInfo;

pub fn get_app_name(app_id: &str) -> Option<String> {
    let info = DesktopAppInfo::new(&format!("{}.desktop", app_id))?;

    info.locale_string("Name").and_then(|e| Some(e.to_string().replace(" ", "\\x20")))
}