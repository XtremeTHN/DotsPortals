use ashpd::{PortalError, backend::Result};
use tokio::process::Command;

async fn _call(operation: &str, target: &str, args: &[&str], user_args: &[&str]) -> Result<String> {
    let out = Command::new("sh")
        .args(&["-c", &format!("qs ipc {} {} {} {}", operation, target, args.join(" "), user_args.join(" "))])
        .output()
        .await
        .map_err(|e| PortalError::Failed(format!("failed to spawn qs: {}", e)))?;

    let out = String::from_utf8_lossy(&out.stdout).to_string();

    // tracing::info!("output: {}", out);

    return Ok(out);
}

pub async fn call(target: &str, function: &str, args: &[&str]) -> Result<String> {
    tracing::info!("calling {} on target {} with args: {}", function, target, args.join(" "));
    _call("call", target, &[function], args)
        .await
}

pub async fn wait_for_signal(target: &str, signal: &str) -> Result<String> {
    tracing::info!("waiting for signal {} on target {}...", signal, target);
    _call("wait", target, &[signal], &[]).await
}

pub async fn wait_for_bool_signal(target: &str, signal: &str) -> Result<bool> {
    wait_for_signal(target, signal)
        .await?
        .trim()
        .parse::<bool>()
        .map_err(|e| PortalError::Failed(format!("Couldn't parse quickshell response: {}", e)))
}