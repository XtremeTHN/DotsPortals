import json
import logging
import os

from .ipc import Ipc


class MangoIpc(Ipc):
    def __init__(self):
        self.logger = logging.getLogger("MangoIpc")
        self.last_mango_windows = {}
        super().__init__(os.getenv("MANGO_INSTANCE_SIGNATURE"))

    def init(self):
        self.output.write_all(b"watch all-clients\n", self.cancellable)

    def poll(self):
        (data, _) = self.input.read_line(self.cancellable)
        windows = {}
        mango_windows = json.loads(data)["clients"]
        self.active_window = {}

        if mango_windows == self.last_mango_windows:
            return

        for x in mango_windows:
            data = self.embed_info({
                "address": x["foreign_toplevel_id"],
                "class": x["appid"],
                "pid": x["pid"]
            })

            if data is None:
                continue

            if x["is_focused"]:
                self.active_window = data

            _windows = windows.get(data["address"], [])
            _windows.append(data)
            windows[data["address"]] = _windows

        self.windows = windows
        self.last_mango_windows = mango_windows
        self.emit("windows-changed")