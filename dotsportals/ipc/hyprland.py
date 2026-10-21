import json
import logging
import os
import socket
import threading
from typing import ClassVar, TypedDict

from gi.repository import Gio, GLib, GObject

from ..utils import get_signal_args

Window = TypedDict(
    "Window",
    {
        "info": GLib.KeyFile,
        "address": str,
        "class": str,
        "mapped": bool,
        "hidden": bool,
        "visible": bool,
        "pid": int,
    },
)


class HyprlandIpc(GObject.Object):
    __gsignals__: ClassVar = {"windows-changed": get_signal_args()}

    windows: dict[str, list[Window]]
    active_window: Window

    def __init__(self):
        super().__init__()

        self.windows = {}
        self.active_window = {}

        self.logger = logging.getLogger("HyprlandIpc")
        self.cancellable = Gio.Cancellable.new()
        self.thread = threading.Thread(target=self.run)

        runtime_dir = os.getenv("XDG_RUNTIME_DIR")
        sig = os.getenv("HYPRLAND_INSTANCE_SIGNATURE")
        hyprland_path = os.path.join(runtime_dir, "hypr", sig)

        self.socket_path = os.path.join(hyprland_path, ".socket.sock")
        self.events_socket_path = os.path.join(hyprland_path, ".socket2.sock")

    def start(self):
        self.thread.start()

    def exec(self, command: str):
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.connect(self.socket_path)

        flag = "j/"
        sock.sendall((flag + command).encode())

        buffer = b""
        while True:
            chunk = sock.recv(1024)
            if not chunk:
                break
            buffer += chunk

        sock.close()
        return json.loads(buffer)

    def get_flatpak_info(self, pid: int):
        proc = f"/proc/{pid}/root/.flatpak-info"
        if os.path.exists(proc):
            key = GLib.KeyFile.new()
            key.load_from_file(proc, GLib.KeyFileFlags.NONE)

            return key

        return None

    def embed_info(self, window: Window):
        info = self.get_flatpak_info(window["pid"])
        if info is None:
            return
        
        window["info"] = info
        return window

    def __refresh_windows(self):
        windows = {}
        hypr_windows = self.exec("clients")

        for x in hypr_windows:
            w = self.embed_info(x)
            if w is None:
                continue

            _windows = windows.get(w["address"], [])
            _windows.append(w)

            windows[w["address"]] = _windows

        self.windows = windows

    def run(self):
        address = Gio.UnixSocketAddress.new(self.events_socket_path)
        sock = Gio.SocketClient.new()
        conn = sock.connect(address, self.cancellable)

        stream = conn.get_input_stream()

        self.event_socket_stream = Gio.DataInputStream.new(stream)

        self.__refresh_windows()
        self.emit("windows-changed")

        while not self.cancellable.is_cancelled():
            try:
                (event, _) = self.event_socket_stream.read_line(self.cancellable)
            except GLib.Error as e:
                if e.args[0] == "Operation was cancelled":
                    break

            event_name, data = event.split(b">>")

            if event_name == b"activewindow":
                self.__refresh_windows()
                self.active_window = {}
                active_class = data.decode().split(",", 1)[0]

                for address, windows in self.windows.items():
                    for x in windows:
                        if x["class"] != active_class:
                            continue
                        self.active_window = x
                self.emit("windows-changed")
            elif event_name == b"closewindow":
                self.__refresh_windows()
                self.emit("windows-changed")
