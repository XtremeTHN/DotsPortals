import logging
from enum import IntEnum

from gi.repository import Gio, GLib

from ..ipc.hyprland import HyprlandIpc
from ..service import Property, method
from ..utils import ret_variant, return_with_error, variant
from .portal import Portal


class State(IntEnum):
    BACKGROUND = 0
    RUNNING = 1
    ACTIVE = 2


class Choice(IntEnum):
    FORBID = 0
    ALLOW = 1
    ALLOW_ONCE = 2


class BackgroundPortal(Portal):
    NAME = "org.freedesktop.impl.portal.Background"

    def __init__(self, conn):
        super().__init__(conn)
        self.state: dict[str, GLib.Variant] = {}
        self.logger = logging.getLogger("BackgroundPortal")
        self.ipc = HyprlandIpc()
        self.ipc.connect("windows-changed", self.on_windows_changed)
        self.ipc.start()

    def on_windows_changed(self, _):
        self.state = {}

        active_address = self.ipc.active_window.get("address", "")
        for windows in self.ipc.windows.values():
            state = State.BACKGROUND
            if len(windows) > 0:
                state = State.RUNNING

            if len([x for x in windows if x["address"] == active_address]) > 0:
                state = State.ACTIVE

            self.state[windows[0]["info"].get_string("Application", "name")] = variant(
                "u", state
            )

        self.emit("RunningApplicationsChanged")

    @method()
    def GetAppState(self):
        return (self.state,)

    @method(pass_invocation=True)
    def NotifyBackground(
        self, invocation: Gio.DBusMethodInvocation, handle: str, app_id: str, name: str
    ):
        req = self.rq.request(handle)

        def on_finish(dismissed: bool) -> tuple[int, dict]:
            if dismissed:
                return (0, {"result": variant("u", Choice.FORBID)})

            return (0, {"result": variant("u", Choice.ALLOW)})

        self.call_and_wait(req, invocation, on_finish, "portals-background", "prompt", name)

    @method()
    def EnableAutostart(
        self, app_id: str, enable: bool, command_line: list[str], flags: int
    ): ...
