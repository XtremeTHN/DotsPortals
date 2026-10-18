import logging
from pathlib import Path

from gi.repository import GLib
from rich.logging import RichHandler
from rich.traceback import install

Flags = GLib.LogLevelFlags
PRINT_GLIB_DEBUG_MESSAGES = False


def g_log_writer(log_level: Flags, log_fields: list[GLib.LogField], size: int):
    msg = GLib.log_writer_format_fields(log_level, log_fields, False).strip()
    logger = logging.getLogger("GLib")
    match log_level:
        case Flags.LEVEL_MESSAGE:
            logger.info(msg)
        case Flags.LEVEL_ERROR:
            logger.error(msg)
        case Flags.LEVEL_CRITICAL:
            logger.critical(msg)
        case Flags.LEVEL_DEBUG | Flags.LEVEL_INFO:
            if PRINT_GLIB_DEBUG_MESSAGES:
                logger.debug(msg)
        case Flags.LEVEL_WARNING:
            logger.warning(msg)

    return GLib.LogWriterOutput.HANDLED


def init_logger():
    install(show_locals=True)
    logging.basicConfig(
        level=logging.DEBUG,
        format="[%(name)s] [%(funcName)s] %(message)s",
        handlers=[
            RichHandler(rich_tracebacks=True),
        ],
    )

    GLib.log_set_writer_func(g_log_writer)