use crate::logger::init_logging;

mod wallpaper;
mod logger;

#[tokio::main]
async fn main() -> ashpd::Result<()> {
    init_logging();

    tracing::info!("Registering...");
    ashpd::backend::Builder::new("org.freedesktop.impl.portal.desktop.dotsportals")?
        .wallpaper(wallpaper::Wallpaper)
        .build()
        .await
        .map_err(From::from)
}