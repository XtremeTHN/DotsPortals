use ashpd::{
    MaybeAppID, PortalError, Uri, WindowIdentifier, WindowIdentifierType,
    backend::{Result, request::RequestImpl, screenshot::ScreenshotImpl},
    desktop::{
        Color, HandleToken,
        screenshot::{
            AvailableTargets, ColorOptions, Screenshot as ScreenshotResponse, ScreenshotOptions,
        },
    },
    enumflags2::BitFlags,
};
use gio::{File, NetworkConnectivity::Portal, prelude::FileExt};

use async_trait::async_trait;

use crate::quickshell;

#[derive(Default)]
pub struct Screenshot;

#[async_trait]
impl RequestImpl for Screenshot {
    async fn close(&self, token: HandleToken) {}
}

#[async_trait]
impl ScreenshotImpl for Screenshot {
    fn available_targets(&self) -> BitFlags<AvailableTargets> {
        AvailableTargets::Area | AvailableTargets::Window | AvailableTargets::Screen
    }

    async fn screenshot(
        &self,
        _token: HandleToken,
        _app_id: Option<MaybeAppID>,
        _window_identifier: Option<WindowIdentifierType>,
        _options: ScreenshotOptions,
    ) -> Result<ScreenshotResponse> {
        let (file, _) = gio::File::new_tmp(Some("xdp-dp_XXXXXX.png"))
            .map_err(|e| PortalError::Failed(format!("couldn't make a temporal file: {}", e)))?;

        let target = match _options.target() {
            Some(AvailableTargets::Area) => "area",
            Some(AvailableTargets::Window) => "window",
            Some(AvailableTargets::ActiveWindow) => "activeWindow",
            _ => "screen",
        };

        quickshell::call(
            "screenshot",
            "screenshot",
            &[target, file.path().unwrap().to_str().unwrap()],
        )
        .await?;
        
        if quickshell::wait_for_bool_signal("screenshot", "finished").await? {
            return Err(PortalError::Cancelled("The user cancelled the request".into()))
        };

        Ok(ScreenshotResponse::new(Uri::parse(&file.uri()).unwrap()))
    }

    async fn pick_color(
        &self,
        _token: HandleToken,
        _app_id: Option<MaybeAppID>,
        _window_identifier: Option<WindowIdentifierType>,
        _options: ColorOptions,
    ) -> Result<Color> {
        Ok(Color::new(1.0, 1.0, 1.0))
    }
}
