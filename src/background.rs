use std::{collections::HashMap, sync::Arc};

use ashpd::{MaybeAppID, backend::{Result, background::{Activity, AppState, AutoStartFlags, Background as BackgroundResponse, BackgroundImpl, BackgroundSignalEmitter}, request::RequestImpl}, desktop::HandleToken, enumflags2::BitFlags};
use async_trait::async_trait;

#[derive(Default)]
struct Background {
    emitter: Option<Arc<dyn BackgroundSignalEmitter>>
}

#[async_trait]
impl RequestImpl for Background {
    async fn close(&self, _token: HandleToken) {}
}

#[async_trait]
impl BackgroundImpl for Background {
    async fn get_app_state(&self) -> Result<HashMap<MaybeAppID, AppState>> {
        return Ok(HashMap::new());
    }

    async fn notify_background(&self, _token: HandleToken, app_id: MaybeAppID, name: &str) -> Result<BackgroundResponse> {
        return Ok(BackgroundResponse::new(Activity::AllowInstance));
    }

    async fn enable_autostart(&self, app_id: MaybeAppID, enable: bool, command_line: Vec<String>, flags: BitFlags<AutoStartFlags>) -> Result<bool> {
        return Ok(false);
    }

    fn set_signal_emitter(&mut self, signal_emitter: Arc<dyn BackgroundSignalEmitter>) {
        self.emitter.replace(signal_emitter);
    }
}