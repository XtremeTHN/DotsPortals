use tracing_subscriber::{layer::SubscriberExt, util::SubscriberInitExt, EnvFilter};
use tracing_tree::HierarchicalLayer;

pub fn init_logging() {
    let filter = EnvFilter::try_from_default_env().unwrap_or_else(|_| EnvFilter::new("debug"));
    let registry = tracing_subscriber::registry().with(filter);

    // systemd sets JOURNAL_STREAM for services whose output goes to the journal
    // match tracing_journald::layer() {
    //     Ok(journald) => {
    //         registry
    //             .with(journald.with_syslog_identifier("xdg-desktop-portal-dotsportals".into()))
    //             .init();
    //         return;
    //     }
    //     Err(e) => eprintln!("journald unavailable, falling back to stderr: {e}"),
    // }

    registry
        .with(
            HierarchicalLayer::new(2)
                .with_targets(true)
                .with_bracketed_fields(true)
                .with_thread_ids(false),
        )
        .init();
}