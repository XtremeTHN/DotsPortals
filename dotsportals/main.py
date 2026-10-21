from gi.repository import GLib

from .logger import init_logger
from .portals.background import BackgroundPortal
from .portals.portal import DotsPortals
from .portals.screenshot import ScreenshotPortal
from .portals.usb import UsbPortal
from .portals.wallpaper import WallpaperPortal


class App:
    def __init__(self):
        init_logger()

        self.service = None

    def activate(self):
        self.service = DotsPortals()
        self.service.add_portal(WallpaperPortal)
        self.service.add_portal(UsbPortal)
        self.service.add_portal(ScreenshotPortal)
        self.service.add_portal(BackgroundPortal)
        self.service.own()

    def deactivate(self):
        self.service.unown()

        back: BackgroundPortal = self.service.get_portal(BackgroundPortal.NAME)
        if back is not None:
            back.ipc.cancellable.cancel()

    def run(self):
        GLib.idle_add(self.activate)
        loop = GLib.MainLoop.new()
        try:
            loop.run()
        except (KeyboardInterrupt, EOFError):
            pass
        finally:
            self.deactivate()


def run():
    a = App()
    a.run()