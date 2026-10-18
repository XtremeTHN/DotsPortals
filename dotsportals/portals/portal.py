import logging
from collections.abc import Callable

from gi.repository import Gio, GLib, GObject

from ..quickshell import call, wait_for_signal
from ..service import Service
from ..utils import load_iface, ret_variant, return_with_error
from .request import Request, RequestFactory


class Portal(Service):
    NAME: str

    def __init__(self, conn: Gio.DBusConnection, info: Gio.DBusInterfaceInfo):
        self.rq = RequestFactory(self.NAME, conn)

        super().__init__(info)

    def call_and_wait(
        self,
        req: Request,
        invocation: Gio.DBusMethodInvocation,
        callback: Callable[[bool], tuple],
        target: str,
        function: str,
        *args,
    ):
        """
        Calls a quickshell function, waits for its finished signal, and then handles errors, decodes the output and calls the callback with a dismissed argument.
        Finishes request when done calling callback or on an exception.
        """

        def finish_cb(out: GLib.Bytes, error: Exception, _):
            if error is not None:
                return return_with_error(invocation, req, error)

            dismissed = out.get_data().decode().strip() == "true"
            val = callback(dismissed)
            invocation.return_value(ret_variant(invocation, val))

            req.finish()

        call(target, function, *args, cancellable=req.cancellable)
        wait_for_signal(
            target, "finished", callback=finish_cb, cancellable=req.cancellable
        )


class DotsPortals(GObject.Object):
    def __init__(self):
        super().__init__()

        self.bus_id = None
        self.logger = logging.getLogger("DotsPortals")
        self.portals_types: dict[str, Portal] = {}
        self.portals_instances: dict[str, Portal] = {}

    def add_portal(self, portal: Portal):
        self.portals_types[portal.NAME] = portal

    def unown(self):
        Gio.bus_unown_name(self.bus_id)
        self.logger.info("Unowned service")

    def own(self):
        self.bus_id = Gio.bus_own_name(
            Gio.BusType.SESSION,
            "org.freedesktop.impl.portal.desktop.dotsportals",
            Gio.BusNameOwnerFlags.NONE,
            self.bus_acquired,
            self.name_acquired,
            self.name_lost,
        )

        self.logger.info("Owned service")

    def bus_acquired(self, conn: Gio.DBusConnection, name: str):
        for iface, portal in self.portals_types.items():
            self.logger.info(f'Registering portal "{iface}"...')
            info = load_iface(iface)

            p: Portal = portal(conn, info)
            self.portals_instances[iface] = p

            conn.register_object(
                "/org/freedesktop/portal/desktop",
                info,
                p.method_handler,
                p.property_get,
                p.property_set,
            )

    def name_acquired(self, conn, name): ...

    def name_lost(self, conn, name): ...
