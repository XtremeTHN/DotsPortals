import json
import logging

from gi.repository import Gio

from .utils import exec_with_output

logger = logging.getLogger("Quickshell")

def _call(operation: str, target: str, *args, callback=None, cancellable=None):    
    exec_with_output(logger, ["qs", "ipc", operation, target, *args], callback, cancellable)

def call(target: str, function: str, *args, callback=None, cancellable=None):
    logger.info(f"Calling function \"{function}\" of target \"{target}\" with args ({",".join(args)})")
    _call("call", target, function, *args, callback=callback, cancellable=cancellable)

def wait_for_signal(target: str, signal: str, callback, cancellable=None):
    logger.info(f"Waiting for signal \"{signal}\" of target \"{target}\"")
    _call("wait", target, signal, callback=callback, cancellable=cancellable)