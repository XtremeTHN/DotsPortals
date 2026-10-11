use tracing::{info, instrument, warn, debug};
use tracing_subscriber::{layer::SubscriberExt, util::SubscriberInitExt, EnvFilter};
use tracing_tree::HierarchicalLayer;

pub fn init_logging() {
    tracing_subscriber::registry()
        .with(EnvFilter::try_from_default_env().unwrap_or_else(|_| EnvFilter::new("debug")))
        .with(
            HierarchicalLayer::new(2)      // 2 spaces of indent per level
                .with_targets(true)        // show the module path
                .with_bracketed_fields(true)
                .with_thread_ids(false),
        )
        .init();
}
