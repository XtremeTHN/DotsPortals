use serde::Deserialize;
use std::{
    collections::HashMap, env::{VarError, var}, io::Error,
};
use tokio::{
    io::{AsyncBufReadExt, AsyncWriteExt, BufReader},
    net::{UnixSocket, UnixStream},
    sync::broadcast::{Sender, Receiver, channel},
};

use thiserror::Error;

#[derive(Error, Debug)]
pub enum IpcError {
    #[error("no hyprland env var")]
    NoEnvVar(#[from] VarError),
    #[error("failed to open hyprland socket")]
    SocketError(#[from] Error),
}

#[derive(Error, Debug)]
pub enum CtlError {
    #[error("failed to communicate with hyprland socket")]
    Socket(#[from] Error),
    #[error("failed to parse response from hyprland socket")]
    Deserialize(#[from] serde_json::Error)
}

#[derive(Deserialize)]
pub struct Window {
    address: String,
    mapped: bool,
    hidden: bool,
    visible: bool,
    class: String,
    title: String,
    pid: u32,
}

#[derive(Clone)]
pub enum HyprSignals {
    OpenWindow(String),
    CloseWindow(String),
    ActiveWindow(String),
}

pub struct HyprIpc {
    event_socket: BufReader<UnixStream>,

    ctl_path: String,
    sender: Sender<HyprSignals>,
    pub active_window: Option<String>,
    pub windows: HashMap<String, Window>,
}

impl HyprIpc {
    pub async fn new() -> Result<Self, IpcError> {
        let sig = var("HYPRLAND_INSTANCE_SIGNATURE")?;
        let runtime_dir = var("XDG_RUNTIME_DIR")?;
        let event_path = format!("{}/hypr/{}/.socket2.sock", runtime_dir, sig);
        let ctl_path = format!("{}/hypr/{}/.socket.sock", runtime_dir, sig);

        let (sender, _) = channel::<HyprSignals>(1);

        Ok(Self {
            event_socket: BufReader::new(UnixSocket::new_stream()?.connect(event_path).await?),
            ctl_path,
            sender,
            active_window: None,
            windows: HashMap::new(),
        })
    }

    async fn call(&mut self, flags: &str, cmd: &str) -> Result<String, CtlError> {
        let mut buffer = String::new();
        let mut stream = BufReader::new(UnixSocket::new_stream()?.connect(&self.ctl_path).await?);

        let command = format!("{}/{}", flags, cmd);
        stream.write_all(command.as_bytes()).await?;
        stream.read_line(&mut buffer).await?;

        Ok(buffer)
    }

    async fn get_windows(&mut self) -> Result<Vec<Window>, CtlError> {
        let buffer = self.call("j", "clients").await?;
        Ok(serde_json::from_str::<Vec<Window>>(&buffer)?)
    }

    async fn update_windows(&mut self) {
        match self.get_windows().await {
            Ok(windows) => {
                self.windows = windows.into_iter().map(|w| (w.address.clone(), w)).collect();
            }
            Err(e) => {
                tracing::warn!("couldn't update hyprland windows: {}", e);
            }
        }
    }

    pub async fn refresh(&mut self) {
        self.update_windows().await;
    }

    pub async fn poll_events(&mut self) {
        let mut buffer = String::new();
        loop {
            buffer.clear();
            let event = self.event_socket.read_line(&mut buffer).await;

            if let Err(e) = event {
                tracing::warn!("couldn't read from hyprland event socket: {}", e);
                continue;
            }
            
            match buffer.split_once(">>") {
                Some((event_name, event_data)) => {
                    let Some((address, _)) = event_data.split_once(",") else {
                        tracing::warn!("event {} triggered without arguments", event_name);
                        continue;
                    };

                    match event_name {
                        "openwindow" => {
                            self.update_windows().await;
                            self.sender.send(HyprSignals::OpenWindow(address.into()));
                        }
                        "closewindow" => {
                            self.windows.remove(address);
                            self.sender.send(HyprSignals::CloseWindow(address.into()));
                        }
                        "activewindow" => {
                            self.active_window = Some(address.into());
                            self.sender.send(HyprSignals::ActiveWindow(address.into()));
                        }
                        _ => {}
                    }
                },
                None => {}
            }
        }
    }

    pub fn subscribe(&self) -> Receiver<HyprSignals> {
        self.sender.subscribe()
    }
}
