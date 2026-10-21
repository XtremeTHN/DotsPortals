import logging
import typing

from gi.repository import Gio, GObject

from ..service import Service, method
from ..utils import load_iface


class Request(GObject.Object, Service):
    NAME = "org.freedesktop.impl.portal.Request"
    
    def __init__(self, logger, handle: str, connection: Gio.DBusConnection):
        GObject.Object.__init__(self)
        Service.__init__(self, connection)

        self.handle = handle
        self.conn = connection
        self.logger = logger

        self.cancellable = Gio.Cancellable.new()
        self._finished = False

        self.id = connection.register_object(
            handle,
            self.info,
            self.method_handler,
        )
        self.logger.info(f"Registered request on {handle}")

    @method
    def Close(self):
        self.logger.info("Closing request")
        self.finish()

    def finish(self):
        if self._finished:
            return

        self._finished = True
        self.cancellable.cancel()
        self.conn.unregister_object(self.id)
        self.logger.info(f"Unregistered request {self.handle}")

    def __enter__(self) -> typing.Self:
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if exc_type is not None:
            self.logger.exception(
                "Request operation failed", exc_info=(exc_type, exc_value, traceback)
            )

        self.finish()


class RequestFactory:
    def __init__(self, name: str, conn: Gio.DBusConnection):
        self.conn = conn
        self.logger = logging.getLogger(f"Request({name})")

    def request(self, handle: str) -> Request:
        return Request(self.logger, handle, self.conn)
