import os

from .hyprland import HyprlandIpc
from .ipc import Ipc
from .mango import MangoIpc


def get_current_ipc() -> Ipc:
    hypr = os.getenv("HYPRLAND_INSTANCE_SIGNATURE")
    mango = os.getenv("MANGO_INSTANCE_SIGNATURE")

    if hypr is not None:
        return HyprlandIpc()

    if mango is not None:
        return MangoIpc()