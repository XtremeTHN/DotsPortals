use ashpd::{
    MaybeAppID, PortalError, Uri, WindowIdentifier, WindowIdentifierType, backend::{Result, request::RequestImpl, wallpaper::WallpaperImpl}, desktop::{HandleToken, wallpaper::{SetOn, WallpaperOptions}},
};

use async_trait::async_trait;
use tokio::process::Command;

use crate::quickshell;

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
            quickshell::call("portals-wallpaper", "showPreview", &[uri.as_str(), &set_on.to_string()]).await?;

            let dismissed = quickshell::wait_for_bool_signal("portals-wallpaper", "finished")
                .await?;

            if dismissed {
                return Err(PortalError::Cancelled("The user cancelled the request".into()))
            }

            return Ok(())
        }

        quickshell::call("portals-wallpaper", "setWallpaper", &[uri.as_str(), &set_on.to_string()]).await?;

        Ok(())
    }
}
