use ashpd::{
    MaybeAppID, PortalError, Uri, WindowIdentifier, WindowIdentifierType, backend::{Result, request::RequestImpl, wallpaper::WallpaperImpl}, desktop::{HandleToken, wallpaper::{SetOn, WallpaperOptions}},
};

use async_trait::async_trait;
use tokio::process::Command;

#[derive(Default)]
pub struct Wallpaper;

#[async_trait]
impl RequestImpl for Wallpaper {
    async fn close(&self, token: HandleToken) {}
}

#[async_trait]
impl WallpaperImpl for Wallpaper {
    async fn with_uri(
        &self,
        token: HandleToken,
        app_id: Option<MaybeAppID>,
        window_identifier: Option<WindowIdentifierType>,
        uri: Uri,
        options: WallpaperOptions,
    ) -> Result<()> {
        let name = match app_id {
            Some(id) => id.to_string(),
            None => String::from("Unknown"),
        };

        let show_preview = options.show_preview().unwrap_or(true);
        let set_on = options.set_on().unwrap_or(SetOn::Background);

        tracing::info!("\"{:?}\" requested to change the system wallpaper", name);
        tracing::info!("setting the {:?} wallpaper", set_on);

        let (schema, rest) = uri
            .as_str()
            .split_once("://")
            .ok_or(PortalError::InvalidArgument(String::from("Invalid uri")))?;

        if schema != "file" {
            return Err(PortalError::Failed(String::from(
                "Only supporting file:// uris",
            )));
        }

        if show_preview {
            let out = Command::new("qs")
                .args(&["ipc", "call", "portal", "previewWallpaper", rest])
                .spawn()
                .map_err(|e| PortalError::Failed(format!("failed to spawn qs: {}", e)))?
                .wait_with_output()
                .await
                .map_err(|e| PortalError::Failed(format!("failed to wait for qs: {}", e)))?;
            
            let stdout = String::from_utf8_lossy(&out.stdout).to_string();

            if stdout.parse::<bool>().expect("unexpected output") {
                return Err(PortalError::Cancelled("Request dismissed by the user".into()));
            }
        }

        let exit_code = Command::new("awww")
            .arg("img")
            .arg(rest)
            .args(&["--transition-type", "center"])
            .spawn()
            .map_err(|e| PortalError::Failed(format!("failed to spawn awww: {}", e)))?
            .wait()
            .await
            .map_err(|e| PortalError::Failed(format!("failed to wait for awww: {}", e)))?
            .code();

        if let Some(code) = exit_code && code != 0 {
            return Err(PortalError::Failed(format!("awww failed with code: {}", code)));
        }

        Ok(())
    }
}
