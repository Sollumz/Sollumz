"""
Logging module to easily log messages from operators that are extended into many functions. 
"""

from bpy.types import Operator
from abc import ABC, abstractmethod
from typing import Sequence, Iterator
from collections import defaultdict
from contextlib import contextmanager


class LoggerBase(ABC):
    @abstractmethod
    def do_log(self, msg: str, level: str):
        ...


class ConsoleLogger(LoggerBase):
    def do_log(self, msg: str, level: str):
        print(f"{level}: {msg}")


class OperatorLogger(LoggerBase):
    def __init__(self, operator: Operator):
        assert operator is not None
        self._operator = operator
        self._num_logs: dict[str, int] = defaultdict(int)

    def do_log(self, msg: str, level: str):
        self._operator.report({level}, msg)
        self._num_logs[level] += 1

    @property
    def has_warnings_or_errors(self) -> bool:
        return self._num_logs["WARNING"] > 0 or self._num_logs["ERROR"] > 0

    def clear_log_counts(self):
        self._num_logs.clear()


class MultiLogger(LoggerBase):
    def __init__(self, loggers: Sequence[LoggerBase]):
        self._loggers: list[LoggerBase] = list(loggers)

    def do_log(self, msg: str, level: str):
        for logger in self._loggers:
            logger.do_log(msg, level)

    def add_logger(self, logger: LoggerBase):
        self._loggers.append(logger)

    def remove_logger(self, logger: LoggerBase):
        self._loggers.remove(logger)


_root_logger: MultiLogger = MultiLogger([ConsoleLogger()])


def _log(msg: str, level: str):
    _root_logger.do_log(msg, level)


@contextmanager
def use_logger(logger: LoggerBase) -> Iterator[LoggerBase]:
    _root_logger.add_logger(logger)
    try:
        yield logger
    finally:
        _root_logger.remove_logger(logger)


def use_operator_logger(operator: Operator) -> Iterator[OperatorLogger]:
    return use_logger(OperatorLogger(operator))


def info(msg: str):
    _log(msg, "INFO")


def warning(msg: str):
    _log(msg, "WARNING")


def error(msg: str):
    _log(msg, "ERROR")
