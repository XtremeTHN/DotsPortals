import logging

from gi.repository import Gio, GioUnix, GLib

from ..quickshell import call, wait_for_signal
from ..service import method, Property
from ..utils import exec_with_output
from .errors import Failed, InvalidArgument
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
    def AcquireDevices(self, invocation: Gio.DBusMethodInvocation, handle: str, parent_window: str, app_id: str, devices: list[tuple], options):
        req = self.rq.request(handle)

        def on_finish(out: GLib.Bytes, error, _):
            if error is not None:
                invocation.return_dbus_error(Failed.name, " ".join(error.args))
                req.finish()
                return

            dismissed = out.get_data().decode().strip() == "true"

            if dismissed:
                invocation.return_value(GLib.Variant("(ua{sv})", (1, [])))
            else:
                new_devices = [
                    (id, {"writable": GLib.Variant("b", access["writable"])})
                    for id, _, access in devices
                ]
                results = {
                    "devices": GLib.Variant("a(sa{sv})", new_devices),
                }
                invocation.return_value(GLib.Variant("(ua{sv})", (0, results)))
                
            req.finish()
        
        for id, info, access in devices:
            props = info["properties"]
            name = props.get("ID_MODEL_ENC", "Unknown")
            vendor = props.get("ID_VENDOR_FROM_DATABASE", "Unknown vendor")
            writable = access.get("writable", False)

            call("portals-usb", "addDevice", name, vendor, str(writable).lower())

        call("portals-usb", "prompt", self.get_app_name(app_id))
        wait_for_signal("portals-usb", "finished", callback=on_finish, cancellable=req.cancellable)