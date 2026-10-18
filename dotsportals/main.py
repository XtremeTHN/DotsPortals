from gi.repository import GLib

from .logger import init_logger
from .portals.portal import DotsPortals
from .portals.wallpaper import WallpaperPortal


class App:
    def __init__(self):
        init_logger()

        self.service = None

    def activate(self):
        self.service = DotsPortals()
        self.service.add_portal(WallpaperPortal)
        self.service.own()

    def run(self):
        GLib.idle_add(self.activate)
        loop = GLib.MainLoop.new()
        try:
            loop.run()
        except (KeyboardInterrupt, EOFError):
            pass
        finally:
            self.service.unown()


def run():
    a = App()
    a.run()