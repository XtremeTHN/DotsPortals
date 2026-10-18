import logging
from enum import IntFlag
from typing import TypedDict

from gi.repository import Gio, GioUnix, GLib

from ..quickshell import call, wait_for_signal
from ..service import Property, method
from ..utils import ret_variant, return_with_error, variant
from .errors import Failed
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
    AvailableTargets = Property(int(Target.SCREEN | Target.WINDOW | Target.AREA | Target.ACTIVEWINDOW))  # all targets

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

        def on_finish(file: Gio.File, out: GLib.Bytes, error: Exception | None, _):
            if error is not None:
                return_with_error(invocation, req, error)
                return

            dismissed = out.get_data().decode().strip() == "true"

            if dismissed:
                invocation.return_value(ret_variant(invocation, (1, {})))
                req.finish()
                return

            invocation.return_value(
                ret_variant(invocation, (0, {"uri": variant("s", file.get_uri())}))
            )
            req.finish()

        try:
            file, _ = Gio.File.new_tmp("xdp-dp_XXXXXX.png")
        except GLib.Error as e:
            return_with_error(invocation, req, e)
            return

        target = Target(options.get("target", 1)).name.lower()

        call(
            "screenshot",
            "screenshot",
            target,
            file.get_path(),
            cancellable=req.cancellable,
        )
        wait_for_signal(
            "screenshot",
            "finished",
            callback=lambda *_: on_finish(file, *_),
            cancellable=req.cancellable,
        )
