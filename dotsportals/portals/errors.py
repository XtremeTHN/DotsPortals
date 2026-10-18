class PortalException(Exception):
    name: str

class Failed(Exception):
    name = "org.freedesktop.portal.Error.Failed"


class InvalidArgument(Exception):
    name = "org.freedesktop.portal.Error.InvalidArgument"


class NotFound(Exception):
    name = "org.freedesktop.portal.Error.NotFound"


class Exists(Exception):
    name = "org.freedesktop.portal.Error.Exists"


class NotAllowed(Exception):
    name = "org.freedesktop.portal.Error.NotAllowed"


class Cancelled(Exception):
    name = "org.freedesktop.portal.Error.Cancelled"


class WindowDestroyed(Exception):
    name = "org.freedesktop.portal.Error.WindowDestroyed"
