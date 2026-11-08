
"""Native Linux process monitoring using /proc."""

import os
import time


def pids():
    """Return all visible numeric process IDs."""
    try:
        return [
            int(name) for name in os.listdir("/proc")
            if name.isdigit()
        ]
    except OSError:
        return []


def path_of(pid):
    """Return the executable path for a process."""
    try:
        return os.readlink(f"/proc/{int(pid)}/exe")
    except (OSError, ValueError):
        return ""


def find(exe_name):
    """Find processes by executable filename."""
    wanted = exe_name.lower()
    found = {}

    for pid in pids():
        path = path_of(pid)
        if path and os.path.basename(path).lower() == wanted:
            found[pid] = path

    return found


def alive(pid):
    return bool(path_of(pid))


def _process_times(pid):
    """Read process CPU ticks and its unique start time."""
    with open(f"/proc/{pid}/stat", encoding="utf-8") as f:
        data = f.read()

    # The command name is enclosed in parentheses and
    # may contain spaces.
    fields = data[data.rfind(")") + 2:].split()

    # State Z means the process has exited (zombie).
    if fields[0] in ("Z", "X"):
        raise ProcessLookupError("Process has exited")

    ticks = int(fields[11]) + int(fields[12])
    started = int(fields[19])

    return ticks, started


def _memory_mb(pid):
    """Read resident memory usage in MiB."""
    with open(f"/proc/{pid}/status", encoding="utf-8") as f:
        for line in f:
            if line.startswith("VmRSS:"):
                kb = int(line.split()[1])
                return kb // 1024
    return None


class CpuMeter:
    """CPU usage as percentage of a single logical core."""

    def __init__(self):
        self.last = {}
        self.clock_ticks = os.sysconf("SC_CLK_TCK")

    def sample(self, pid):
        try:
            ticks, started = _process_times(pid)
            ram = _memory_mb(pid)
        except (OSError, ValueError, IndexError):
            self.last.pop(pid, None)
            return None

        now = time.monotonic()
        cpu = None
        before = self.last.get(pid)

        if before and before[2] == started:
            elapsed = now - before[0]

            if elapsed > 0:
                cpu_seconds = (
                    ticks - before[1]
                ) / self.clock_ticks

                cpu = round(
                    max(0.0, cpu_seconds / elapsed * 100),
                    1
                )

        self.last[pid] = (now, ticks, started)

        return {
            "ramMo": ram,
            "cpu": cpu
        }


def cores():
    return os.cpu_count() or 1
