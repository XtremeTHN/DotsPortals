// Thank you claude

use std::{collections::HashMap, sync::Arc};

use ashpd::{
    PortalError, backend::usb::AccessOptions, desktop::{self, usb::UsbDevice}, zvariant::{ObjectPath, OwnedValue, Type, as_value},
};
use serde::Serialize;
use tokio::sync::Notify;
use zbus::interface;

use crate::quickshell;

#[derive(Debug, Serialize, Type)]
#[zvariant(signature = "dict")]
struct AcquireResults {
    #[serde(default, with = "as_value::optional", skip_serializing_if = "Option::is_none")]
    devices: Option<Vec<(String, AccessOptions)>>,
}

impl AcquireResults {
    fn empty() -> Self {
        Self { devices: None }
    }
}

struct Request {
    cancel: Arc<Notify>,
}

#[interface(name = "org.freedesktop.impl.portal.Request")]
impl Request {
    async fn close(&self) {
        self.cancel.notify_one();
    }
}

#[derive(Default)]
pub struct UsbPortal;

#[interface(name = "org.freedesktop.impl.portal.Usb")]
impl UsbPortal {
    #[zbus(property(emits_changed_signal = "const"), name = "version")]
    fn version(&self) -> u32 {
        1
    }

    #[zbus(name = "AcquireDevices")]
    #[zbus(out_args("response", "results"))]
    async fn acquire_devices(
        &self,
        #[zbus(connection)] conn: &zbus::Connection,
        handle: ObjectPath<'_>,
        _parent_window: &str,
        app_id: &str,
        devices: Vec<(String, UsbDevice, AccessOptions)>,
        _options: HashMap<String, OwnedValue>,
    ) -> (u32, AcquireResults) {
        let cancel = Arc::new(Notify::new());

        if let Err(e) = conn
            .object_server()
            .at(handle.clone(), Request { cancel: cancel.clone() })
            .await
        {
            tracing::error!(error = ?e, "failed to export request object");
            return (2, AcquireResults::empty());
        }

        let outcome = tokio::select! {
            r = ask_user(app_id, &devices) => r,
            _ = cancel.notified() => Ok(true),
        };

        let _ = conn.object_server().remove::<Request, _>(handle).await;

        match outcome {
            Ok(false) => {
                // Grant only what the app requested (t.2), never more.
                let granted = devices
                    .iter()
                    .map(|(id, _, requested)| {
                        (id.clone(), AccessOptions::new(requested.is_writable().unwrap_or(false)))
                    })
                    .collect();
                (0, AcquireResults { devices: Some(granted) })
            }
            Ok(true) => (1, AcquireResults::empty()),
            Err(e) => {
                tracing::error!(error = ?e, "acquire_devices failed");
                (2, AcquireResults::empty())
            }
        }
    }
}

async fn ask_user(
    app_id: &str,
    devices: &[(String, UsbDevice, AccessOptions)],
) -> Result<bool, PortalError> {
    let app = if app_id.is_empty() { "UnknownApp" } else { app_id };
    let app_name = crate::desktop::get_app_name(app).unwrap_or(String::from(app));

    for (_id, device, requested) in devices {
        let props = device.properties();
        let name = props.get("ID_MODEL_ENC").map(|v| v.to_string().replace("\"", "").replace("\\x20", " ")).unwrap_or("Unknown".into());
        let vendor = props
            .get("ID_VENDOR_FROM_DATABASE")
            .map(|v| v.to_string())
            .unwrap_or("Unknown\\x20Vendor".into());

        let writable = requested.is_writable().unwrap_or(false).to_string();
        tracing::info!("{:#?} {} {} {}", props, name, vendor, writable);

        quickshell::call("portals-usb", "addDevice", &[&name, &vendor, &writable]).await?;
    }

    quickshell::call("portals-usb", "prompt", &[&app_name]).await?;
    quickshell::wait_for_bool_signal("portals-usb", "finished").await
}