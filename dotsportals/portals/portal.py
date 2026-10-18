import logging

from gi.repository import Gio, GObject

from ..service import Service
from ..utils import load_iface
from .request import RequestFactory


class Portal(Service):
    NAME: str

    def __init__(self, conn: Gio.DBusConnection):
        self.rq = RequestFactory(self.NAME, conn)

        super().__init__()

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

            p: Portal = portal(conn)
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
