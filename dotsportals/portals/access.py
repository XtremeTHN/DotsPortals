import json
import logging

from gi.repository import Gio, GLib

from ..service import method

from ..utils import variant
from .portal import Portal

from typing import Any


class AccessPortal(Portal):
    NAME = "org.freedesktop.impl.portal.Access"

    def __init__(self, conn):
        super().__init__(conn)

        self.logger = logging.getLogger("AccessPortal")

    @method(pass_invocation=True)
    def AccessDialog(
        self,
        invocation: Gio.DBusMethodInvocation,
        handle: str,
        app_id: str,
        parent_window: str,
        title: str,
        subtitle: str,
        body: str,
        options: dict,
    ):
        req = self.rq.request(handle)

        def on_finish(data: dict[str, str]) -> tuple[int, dict]:
            dismissed = data.pop("dismissed")

            if dismissed:
                return (1, {})

            selected = [(_id, value) for _id, value in data.items()]
            return (0, {"choices": variant("a(ss)", selected)})

        args = json.dumps({
            "title": title,
            "subtitle": subtitle,
            "body": body,
            "options": options
        })

        self.call_and_wait(
            req,
            invocation,
            on_finish,
            "portals-access",
            "prompt",
            args,
            _json=True
        )