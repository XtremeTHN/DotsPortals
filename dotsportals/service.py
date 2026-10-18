import functools

from gi.repository import Gio, GLib

from .portals.errors import PortalException


class Service:
    methods: dict

    def __init_subclass__(cls, **kwargs) -> None:
        super().__init_subclass__(**kwargs)
        cls.methods = {
            name: member
            for name, member in cls.__dict__.items()
            if callable(member) and member.__dict__.get("portal_method", False)
        }

    def method_handler(
        self,
        conn: Gio.DBusConnection,
        sender: str,
        object_path: str,
        interface_name: str,
        method_name: str,
        parameters: GLib.Variant,
        invocation: Gio.DBusMethodInvocation,
    ):
        self.logger.info(f"Calling \"{method_name}\"")
        info = invocation.get_method_info()
        if info is None:
            return

        args = parameters.unpack()
        try:
            func = self.methods[method_name]

            if func.pass_invocation:
                ret_value = func(self, invocation, *args)
                return
            else:
                ret_value = func(self, *args)
        except PortalException as e:
            msg = " ".join(e.args)
            if hasattr(self, "logger"):
                self.logger.error(f"{e.name}: {msg}")
            invocation.return_dbus_error(e.name, msg)
            return

        if len(info.out_args) > 0:
            sig = f"({"".join(a.signature for a in info.out_args)})"
            invocation.return_value(GLib.Variant(sig, ret_value))
        else:
            invocation.return_value()

    def property_get(
        self,
        conn: Gio.DBusConnection,
        sender: str,
        object_path: str,
        interface_name: str,
        property_name: str,
    ) -> GLib.Variant: ...

    def property_set(
        self,
        conn: Gio.DBusConnection,
        sender: str,
        object_path: str,
        interface_name: str,
        property_name: str,
        value: GLib.Variant,
    ) -> bool: ...    

class method:
    def __init__(self, pass_invocation: bool = False):
        self.pass_invocation = pass_invocation

    def __call__(self, func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        wrapper.__dict__["portal_method"] = True
        wrapper.__dict__["pass_invocation"] = self.pass_invocation

        return wrapper

# def method(pass_invocation: bool = False):
#     def layer(func):
#         @functools.wraps(func)
#         def wrapper(*args, **kwargs):
#             return func(*args, **kwargs)

#     wrapper.__dict__["portal_method"] = True
#     return wrapper