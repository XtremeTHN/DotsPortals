from gi.repository import GObject, GLib, Gio
from typing import ClassVar, TypedDict

from ..utils import get_signal_args

from abc import ABC, abstractmethod

import threading
import logging
import os

Window = TypedDict(
    "Window",
    {
        "info": GLib.KeyFile,
        "address": str,
        "class": str,
        "pid": int,
    },
)


class Ipc(GObject.Object):
    __gsignals__: ClassVar = {
        "windows-changed": get_signal_args()
    }

    windows: dict[str, list[Window]]
    active_window: Window
    logger: logging.Logger

    def __init__(self, socket_path: str):
        super().__init__()

        self.windows = {}
        self.active_window = {}

        self.task = threading.Thread(target=self._run)
        self.cancellable = Gio.Cancellable.new()

        self.connection = self.get_socket(socket_path)
        self.input = self.get_input_stream(self.connection)
        self.output = self.get_output_stream(self.connection)

        self.logger.info(f"Connected to \"{socket_path}\"")

    def start(self):
        self.task.start()

    def get_socket(self, path: str) -> Gio.SocketConnection:
        address = Gio.UnixSocketAddress.new(path)
        sock = Gio.SocketClient.new()
        conn = sock.connect(address, self.cancellable)

        return conn

    def get_input_stream(self, conn: Gio.SocketConnection) -> Gio.DataInputStream:
        stream = conn.get_input_stream()
        return Gio.DataInputStream.new(stream)

    def get_output_stream(self, conn: Gio.SocketConnection) -> Gio.DataOutputStream:
        stream = conn.get_output_stream()
        return Gio.DataOutputStream.new(stream)

    def get_flatpak_info(self, pid: int) -> GLib.KeyFile | None:
        proc = f"/proc/{pid}/root/.flatpak-info"
        if os.path.exists(proc):
            key = GLib.KeyFile.new()
            if key.load_from_file(proc, GLib.KeyFileFlags.NONE) is False:
                return

            return key
        return None

    def embed_info(self, window: Window) -> Window | None:
        info = self.get_flatpak_info(window["pid"])
        if info is None:
            return

        window["info"] = info
        return window

    def _run(self):
        self.init()
        while not self.cancellable.is_cancelled():
            try:
                self.poll()
            except GLib.Error as e:
                if e.message == "Operation was cancelled":
                    self.logger.info("Shutting down...")
                    break
                raise

    def poll(self):
        ...

    def init(self):
        ...