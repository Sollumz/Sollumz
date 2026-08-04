import atexit
import subprocess
from collections.abc import Sequence

from .. import logger

# Pools with live subprocesses. Blender doesn't wait for them on quit, so without this the workers
# outlive the Blender window as orphaned headless processes.
_live_pools = []


@atexit.register
def _kill_live_processes():
    for pool in _live_pools:
        for proc in pool._processes:
            proc.kill()


class ProcessPool:
    def __init__(self, commands: Sequence[Sequence[str]], max_parallel: int = 8):
        self.commands = commands
        self.max_parallel = max_parallel
        self.return_codes = []
        self._remaining_commands = list(commands)
        self._processes = []
        _live_pools.append(self)

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
        busy = bool(self._processes or self._remaining_commands)
        if not busy and self in _live_pools:
            _live_pools.remove(self)
        return busy
