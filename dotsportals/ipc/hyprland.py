import json
import logging
import os
import socket

from gi.repository import GLib

from .ipc import Ipc


class HyprlandIpc(Ipc):
    def __init__(self):
        super().__init__()

        self.logger = logging.getLogger("HyprlandIpc")

        runtime_dir = os.getenv("XDG_RUNTIME_DIR")
        sig = os.getenv("HYPRLAND_INSTANCE_SIGNATURE")
        hyprland_path = os.path.join(runtime_dir, "hypr", sig)

        self.socket_path = os.path.join(hyprland_path, ".socket.sock")
        self.events_socket_path = os.path.join(hyprland_path, ".socket2.sock")

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
        sock = self.get_socket(self.events_socket_path)
        self.event_socket_stream = self.get_input_stream(sock)
        self.__refresh_windows()
        self.emit("windows-changed")

    def poll(self):
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

                for windows in self.windows.values():
                    for x in windows:
                        if x["class"] != active_class:
                            continue
                        self.active_window = x
                self.emit("windows-changed")
            elif event_name == b"closewindow":
                self.__refresh_windows()
                self.emit("windows-changed")
