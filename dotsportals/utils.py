import re
from pathlib import Path
from typing import Any

from gi.repository import Gio, GLib, GObject

from .portals.errors import Failed

INTERFACES_PATH = Path("/usr/share/dbus-1/interfaces/")


def load_iface(iface: str) -> Gio.DBusNodeInfo:
    return Gio.DBusNodeInfo.new_for_xml(
        (INTERFACES_PATH / f"{iface}.xml").read_text()
    ).lookup_interface(iface)


def get_signal_args(flags="run-first", args=()):
    return (
        getattr(GObject.SignalFlags, flags.replace("-", "_").upper()),
        None,
        tuple(args),
    )

def exec_with_output(logger: object, cmd: list, callback, cancellable=None):
    def cb(p: Gio.Subprocess, res):
        try:
            (_, stdout, stderr) = p.communicate_finish(res)
            if p.get_exit_status() > 0:
                logger.error(f"Failed to communicate with {cmd[0]}")
                logger.error(f"stderr: {stderr}")
                logger.error(f"stdout: {stdout}")
            if callback is not None:
                callback(stdout, None, cancellable)
        except Exception as e:
            logger.exception("Failed to finish quickshell call", exc_info=e)
            if callback is not None:
                callback(None, e, cancellable)

    proc = Gio.Subprocess.new(cmd, Gio.SubprocessFlags.STDOUT_PIPE | Gio.SubprocessFlags.STDERR_PIPE)
    proc.communicate_async(None, cancellable, cb)

def variant(sig: str, value: Any):
    return GLib.Variant(sig, value)

def ret_variant(invocation: Gio.DBusMethodInvocation, value: Any):
    info = invocation.get_method_info()
    sig = f"({''.join(a.signature for a in info.out_args)})"

    return variant(sig, value)

def return_with_error(invocation: Gio.DBusMethodInvocation, req, error: Exception):
    invocation.return_dbus_error(Failed.name, " ".join(error.args))
    req.finish()

def systemd_unescape(s: str, path: bool = False) -> str:
    b = s.encode()
    b = b.replace(b"-", b"/")
    b = re.sub(rb"\\x([0-9a-fA-F]{2})", lambda m: bytes([int(m[1], 16)]), b)
    out = b.decode("utf-8", errors="replace")
    if path and not out.startswith("/"):
        out = "/" + out
    return out