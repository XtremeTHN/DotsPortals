import json
import logging
import os
import socket

from .ipc import Ipc


class HyprlandIpc(Ipc):
    def __init__(self):
        self.logger = logging.getLogger("HyprlandIpc")

        runtime_dir = os.getenv("XDG_RUNTIME_DIR")
        sig = os.getenv("HYPRLAND_INSTANCE_SIGNATURE")
        hyprland_path = os.path.join(runtime_dir, "hypr", sig)
        self.socket_path = os.path.join(hyprland_path, ".socket.sock")
        events_socket_path = os.path.join(hyprland_path, ".socket2.sock")

        super().__init__(events_socket_path)

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

    def init(self):
        self.__refresh_windows()
        self.emit("windows-changed")

    def poll(self):
        (event, _) = self.input.read_line(self.cancellable)
        event_name, data = event.split(b">>", 1)

        if event_name in (
            b"movewindow",
            b"movewindowv2",
            b"resizewindow",
            b"resizewindowv2",
        ):
            return

        if event_name == b"activewindow":
            previous_active_address = self.active_window.get("address")
            self.__refresh_windows()
            self.active_window = {}
            active_class = data.decode().split(",", 1)[0]

            for windows in self.windows.values():
                for x in windows:
                    if x["class"] != active_class:
                        continue
                    self.active_window = x
            if self.active_window.get("address") != previous_active_address:
                self.emit("windows-changed")
        elif event_name == b"closewindow":
            self.__refresh_windows()
            self.emit("windows-changed")
