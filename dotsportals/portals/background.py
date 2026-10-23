import logging
from enum import IntEnum

from gi.repository import Gio, GLib

from ..ipc.util import get_current_ipc
from ..service import method
from ..utils import exec_with_output, ret_variant, return_with_error, variant
from .portal import Portal


class State(IntEnum):
    BACKGROUND = 0
    RUNNING = 1
    ACTIVE = 2


class Choice(IntEnum):
    FORBID = 0
    ALLOW = 1
    ALLOW_ONCE = 2

    @classmethod
    def from_action_id(cls, id):
        _id = 0

        if id == 0:
            return cls(1)
        if id == 1:
            return cls(2)
        if id == 2:
            return cls(0)

        return cls(_id)


class BackgroundPortal(Portal):
    NAME = "org.freedesktop.impl.portal.Background"

    def __init__(self, conn):
        super().__init__(conn)
        self.state: dict[str, GLib.Variant] = {}
        self.last_state = {}
        self.logger = logging.getLogger("BackgroundPortal")
        self.ipc = get_current_ipc()
        self.ipc.connect("windows-changed", self.on_windows_changed)
        self.ipc.start()

    def on_windows_changed(self, _):
        self.last_state = self.state
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

        if self.last_state == {} and self.state == {}:
            return

        self.emit("RunningApplicationsChanged")

    @method()
    def GetAppState(self):
        return (self.state,)

    @method(pass_invocation=True)
    def NotifyBackground(
        self, invocation: Gio.DBusMethodInvocation, handle: str, app_id: str, name: str
    ):
        req = self.rq.request(handle)

        def on_finish(out: GLib.Bytes, error, _):
            if error is not None:
                return_with_error(invocation, req, error)
                return

            data = out.get_data()
            if data == b'':
                self.logger.warning(f"Failed to prompt user. {app_id} will be killed")
                invocation.return_value(
                    ret_variant(invocation, (0, {"result": variant("u", Choice.FORBID)}))
                )
                return

            action_id = Choice.from_action_id(int(data.decode().strip()))
            invocation.return_value(
                ret_variant(invocation, (0, {"result": variant("u", action_id)}))
            )
            req.finish()

        exec_with_output(
            self.logger,
            [
                "notify-send",
                f"Let {name} keep running?",
                f"{name} wants to stay active in the background. Denying will kill the application",
                "--app-name=Background Portal",
                "--action=Allow",
                "--action=Allow once",
                "--action=Don't allow"
            ],
            on_finish,
            req.cancellable
        )

    @method()
    def EnableAutostart(
        self, app_id: str, enable: bool, command_line: list[str], flags: int
    ):
        self.logger.warning("Deprecated")