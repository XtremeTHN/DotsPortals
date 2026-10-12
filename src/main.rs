use crate::logger::init_logging;

mod screenshot;
mod desktop;
mod quickshell;
mod wallpaper;
mod usb;
mod logger;

#[tokio::main]
async fn main() -> ashpd::Result<()> {
    init_logging();

    tracing::info!("Registering...");

    let connection = zbus::Connection::session().await?;

    connection
        .object_server()
        .at("/org/freedesktop/portal/desktop", usb::UsbPortal)
        .await?;

    ashpd::backend::Builder::new("org.freedesktop.impl.portal.desktop.dotsportals")?
        .wallpaper(wallpaper::Wallpaper)
        .screenshot(screenshot::Screenshot)
        .build_with_connection(connection)
        .await
        .map_err(From::from)
}