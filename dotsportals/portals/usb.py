import logging

from gi.repository import Gio, GioUnix, GLib

from ..quickshell import call
from ..service import Property, method
from .portal import Portal


class UsbPortal(Portal):
    NAME = "org.freedesktop.impl.portal.Usb"
    version = Property(1)

    def __init__(self, conn: Gio.DBusConnection, info):
        super().__init__(conn, info)

        self.logger = logging.getLogger("UsbPortal")

    def get_app_name(self, app_id: str):
        info = GioUnix.DesktopAppInfo.new(f"{app_id}.desktop")
        return info.get_locale_string("Name")

    @method(pass_invocation=True)
    def AcquireDevices(
        self,
        invocation: Gio.DBusMethodInvocation,
        handle: str,
        _parent_window: str,
        app_id: str,
        devices: list[tuple],
        _options,
    ):
        def on_finish(dismissed: bool):
            if dismissed:
                return (1, [])

            new_devices = [
                (id, {"writable": GLib.Variant("b", access["writable"])})
                for id, _, access in devices
            ]
            results = {
                "devices": GLib.Variant("a(sa{sv})", new_devices),
            }

            return (0, results)

        req = self.rq.request(handle)

        for id, info, access in devices:
            props = info["properties"]
            name = props.get("ID_MODEL_ENC", "Unknown")
            vendor = props.get("ID_VENDOR_FROM_DATABASE", "Unknown vendor")
            writable = access.get("writable", False)

            call("portals-usb", "addDevice", name, vendor, str(writable).lower())

        self.call_and_wait(
            req,
            invocation,
            on_finish,
            "portals-usb",
            "prompt",
            self.get_app_name(app_id),
        )
