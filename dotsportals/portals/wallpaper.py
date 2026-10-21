import logging

from gi.repository import Gio, GLib

from ..quickshell import call, wait_for_signal
from ..service import method
from ..utils import exec_with_output
from .errors import Failed, InvalidArgument
from .portal import Portal


class WallpaperPortal(Portal):
    NAME = "org.freedesktop.impl.portal.Wallpaper"

    def __init__(self, conn: Gio.DBusConnection):
        super().__init__(conn)

        self.logger = logging.getLogger("WallpaperPortal")

    @method(pass_invocation=True)
    def SetWallpaperURI(
        self,
        invocation: Gio.DBusMethodInvocation,
        handle: str,
        app_id: str,
        parent_window: str,
        uri: str,
        options: dict,
    ):
        """
        0: Success, the request is carried out
        1: The user cancelled the interaction
        2: The user interaction was ended in some other way
        """
        file = Gio.File.new_for_uri(uri)
        path = file.get_path() if file.is_native() and file.query_exists() else None
        if path is None:
            raise InvalidArgument("Currently not native files are not supported")

        req = self.rq.request(handle)
        completed = False

        def finish_with_result(result: int):
            nonlocal completed
            if completed:
                return
            completed = True

            try:
                invocation.return_value(GLib.Variant("(u)", (result,)))
            finally:
                req.finish()

        def finish_with_error(error: Exception):
            nonlocal completed
            if completed:
                return
            completed = True

            try:
                invocation.return_dbus_error(Failed.name, " ".join(error.args))
            finally:
                req.finish()

        def on_matugen_finished(out: GLib.Bytes, error, _):
            if error is not None:
                finish_with_error(error)
                return

            finish_with_result(0)

        def on_finished(path: str, out: GLib.Bytes, error, cancellable):
            if error is not None:
                finish_with_error(error)
                return

            dismissed = out.get_data().decode().strip() == "true"

            if dismissed:
                finish_with_result(1)
                return

            exec_with_output(
                self.logger,
                ["matugen", "image", path, "--prefer", "lightness"],
                on_matugen_finished,
                cancellable=cancellable,
            )

        def on_preview_finished(_out, error, _cancellable):
            if error is not None:
                finish_with_error(error)

        try:
            call(
                "portals-wallpaper",
                "showPreview",
                path,
                options.get("set-on", "background"),
                callback=on_preview_finished,
                cancellable=req.cancellable,
            )
            wait_for_signal(
                "portals-wallpaper",
                "finished",
                callback=lambda *args: on_finished(path, *args),
                cancellable=req.cancellable,
            )
        except Exception:
            req.finish()
            raise
