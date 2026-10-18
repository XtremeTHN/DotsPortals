import logging
from enum import IntFlag
from typing import TypedDict

from gi.repository import Gio, GLib

from ..service import Property, method
from ..utils import return_with_error, variant
from .portal import Portal


class Target(IntFlag):
    SCREEN = 1
    WINDOW = 2
    AREA = 4
    ACTIVEWINDOW = 8


class ScreenshotOptions(TypedDict):
    modal: bool
    interactive: bool
    target: int
    permission_store_checked: bool


class ScreenshotPortal(Portal):
    NAME = "org.freedesktop.impl.portal.Screenshot"
    version = Property(3)
    AvailableTargets = Property(
        int(Target.SCREEN | Target.WINDOW | Target.AREA | Target.ACTIVEWINDOW)
    )  # all targets

    def __init__(self, conn, info):
        super().__init__(conn, info)
        self.logger = logging.getLogger("ScreenshotPortal")

    @method(pass_invocation=True)
    def Screenshot(
        self,
        invocation: Gio.DBusMethodInvocation,
        handle: str,
        app_id: str,
        parent_window: str,
        options: ScreenshotOptions,
    ):
        """
        Returns:
            u: Numeric response
            a{sv}: Result ({"uri": URI})
        """
        req = self.rq.request(handle)

        def on_finish(file: Gio.File, dismissed: bool):
            if dismissed:
                return (1, {})

            return (0, {"uri": variant("s", file.get_uri())})

        try:
            file, _ = Gio.File.new_tmp("xdp-dp_XXXXXX.png")
        except GLib.Error as e:
            self.logger.exception("Couldn't create temporal file", exc_info=e)
            return return_with_error(invocation, req, e)

        target = Target(options.get("target", 1)).name.lower()
        self.call_and_wait(
            req,
            invocation,
            lambda d: on_finish(file, d),
            "screenshot",
            "screenshot",
            target,
            file.get_path(),
        )
