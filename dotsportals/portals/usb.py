import logging

from gi.repository import Gio, GLib

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

    @method(pass_invocation=True)
    def AcquireDevices(self, invocation, handle: str, parent_window: str, app_id: str, devices: list[tuple], options):
        for id, info, access in devices:
            call("portals-usb", "addDevice", "")