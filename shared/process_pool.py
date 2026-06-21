import subprocess
from collections.abc import Sequence

from .. import logger


class ProcessPool:
    def __init__(self, commands: Sequence[Sequence[str]], max_parallel: int = 8):
        self.commands = commands
        self.max_parallel = max_parallel
        self.return_codes = []
        self._remaining_commands = list(commands)
        self._processes = []

    @property
    def num_completed(self) -> int:
        return len(self.return_codes)

    def _collect_finished(self):
        still_running = []
        for proc in self._processes:
            retcode = proc.poll()
            if retcode is not None:
                self.return_codes.append(retcode)
            else:
                still_running.append(proc)
        self._processes = still_running

    def update(self) -> bool:
        self._collect_finished()

        # Launch new processes until we reach the limit
        while self._remaining_commands and len(self._processes) < self.max_parallel:
            cmd = self._remaining_commands.pop()
            logger.info(f"Launching subprocess: {cmd}")
            p = subprocess.Popen(cmd)
            self._processes.append(p)

        # Still busy while anything is running or queued
        return bool(self._processes or self._remaining_commands)
