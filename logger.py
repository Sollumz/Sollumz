"""
Logging module to easily log messages from operators that are extended into many functions. 
"""

from bpy.types import Operator
from typing import Optional

_logging_operator: Optional[Operator] = None
_NO_LOGGING_OPERATOR_WARNING = "LOGGER WARNING: No active logging operator has been set!"


def _log(msg: str, level: str):
    print(f"{level}: {msg}")

    if _logging_operator is None:
        print(_NO_LOGGING_OPERATOR_WARNING)
        return

    try:
        _logging_operator.report({level}, msg)
    except ReferenceError:
        print(_NO_LOGGING_OPERATOR_WARNING)


def set_logging_operator(operator: Operator):
    global _logging_operator
    _logging_operator = operator


def info(msg: str):
    _log(msg, "INFO")


def warning(msg: str):
    _log(msg, "WARNING")


def error(msg: str):
    _log(msg, "ERROR")
