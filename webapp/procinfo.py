"""Memory and processor time of the worldservers, read from Windows directly (psapi, kernel32): no PowerShell and no
tasklist started every minute. Elsewhere, or when Windows refuses, every answer is empty and the page says nothing.
"""
import ctypes
import os
import time

_OK = os.name == "nt"
if _OK:
    from ctypes import wintypes
    try:
        _k32 = ctypes.WinDLL("kernel32", use_last_error=True)
        _psapi = ctypes.WinDLL("psapi", use_last_error=True)
    except OSError:
        _OK = False
if _OK:
    # A handle is 64 bits wide: the default int result would cut it.
    _k32.OpenProcess.restype = wintypes.HANDLE
    _k32.OpenProcess.argtypes = (wintypes.DWORD, wintypes.BOOL, wintypes.DWORD)
    _k32.CloseHandle.argtypes = (wintypes.HANDLE,)
    _k32.QueryFullProcessImageNameW.argtypes = (wintypes.HANDLE, wintypes.DWORD, wintypes.LPWSTR,
                                                ctypes.POINTER(wintypes.DWORD))
    _k32.GetProcessTimes.argtypes = (wintypes.HANDLE,) + (ctypes.POINTER(wintypes.FILETIME),) * 4
    _psapi.GetProcessMemoryInfo.argtypes = (wintypes.HANDLE, ctypes.c_void_p, wintypes.DWORD)
    _psapi.EnumProcesses.argtypes = (ctypes.POINTER(wintypes.DWORD), wintypes.DWORD, ctypes.POINTER(wintypes.DWORD))

QUERY = 0x1000      # PROCESS_QUERY_LIMITED_INFORMATION: enough for the path, the times and the memory


if _OK:
    class _Counters(ctypes.Structure):
        _fields_ = [("cb", wintypes.DWORD), ("PageFaultCount", wintypes.DWORD),
                    ("PeakWorkingSetSize", ctypes.c_size_t), ("WorkingSetSize", ctypes.c_size_t),
                    ("QuotaPeakPagedPoolUsage", ctypes.c_size_t), ("QuotaPagedPoolUsage", ctypes.c_size_t),
                    ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t), ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                    ("PagefileUsage", ctypes.c_size_t), ("PeakPagefileUsage", ctypes.c_size_t),
                    ("PrivateUsage", ctypes.c_size_t)]


def _open(pid):
    return _k32.OpenProcess(QUERY, False, int(pid)) if _OK and pid else None


def pids():
    """Every process id of this machine."""
    if not _OK:
        return []
    size = 4096
    while True:
        array = (wintypes.DWORD * size)()
        needed = wintypes.DWORD()
        if not _psapi.EnumProcesses(array, ctypes.sizeof(array), ctypes.byref(needed)):
            return []
        count = needed.value // ctypes.sizeof(wintypes.DWORD)
        if count < size:
            return list(array[:count])
        size *= 2


def path_of(pid):
    handle = _open(pid)
    if not handle:
        return ""
    try:
        buffer = ctypes.create_unicode_buffer(1024)
        length = wintypes.DWORD(len(buffer))
        if _k32.QueryFullProcessImageNameW(handle, 0, buffer, ctypes.byref(length)):
            return buffer.value
        return ""
    finally:
        _k32.CloseHandle(handle)


def listeners():
    """{port: pid} of the TCP ports (IPv4) a process listens on, from Windows' own table (iphlpapi). {} elsewhere."""
    if not _OK:
        return {}
    try:
        iphlp = ctypes.WinDLL("iphlpapi")
        size = wintypes.DWORD(0)
        iphlp.GetExtendedTcpTable(None, ctypes.byref(size), False, 2, 3, 0)    # AF_INET, TCP_TABLE_OWNER_PID_LISTENER
        for _ in range(3):
            buffer = ctypes.create_string_buffer(size.value + 4096)
            size = wintypes.DWORD(len(buffer))
            if iphlp.GetExtendedTcpTable(buffer, ctypes.byref(size), False, 2, 3, 0) == 0:
                break
        else:
            return {}
        count = wintypes.DWORD.from_buffer(buffer).value
        rows = (wintypes.DWORD * (6 * count)).from_buffer(buffer, 4)    # state, addr, port, raddr, rport, pid
        found = {}
        for i in range(count):
            raw = rows[6 * i + 2]
            found[((raw & 0xFF) << 8) | ((raw >> 8) & 0xFF)] = int(rows[6 * i + 5])
        return found
    except (OSError, ValueError, AttributeError):
        return {}


def find(exe_name):
    """{pid: full path} of the running processes named `exe_name` (worldserver.exe, say)."""
    wanted = exe_name.lower()
    found = {}
    for pid in pids():
        path = path_of(pid)
        if path and os.path.basename(path).lower() == wanted:
            found[pid] = path
    return found


def alive(pid):
    return bool(path_of(pid))


class CpuMeter:
    """Processor use of one process between two readings, in % of one core (100 = one core busy)."""

    def __init__(self):
        self.last = {}

    def sample(self, pid):
        """{"ramMo", "cpu"} of `pid`, or None if it is not running. cpu is None on the first reading."""
        handle = _open(pid)
        if not handle:
            return None
        try:
            counters = _Counters()
            counters.cb = ctypes.sizeof(_Counters)
            if not _psapi.GetProcessMemoryInfo(handle, ctypes.byref(counters), counters.cb):
                return None
            times = [wintypes.FILETIME() for _ in range(4)]
            if not _k32.GetProcessTimes(handle, *[ctypes.byref(t) for t in times]):
                return None
            busy = sum((t.dwHighDateTime << 32 | t.dwLowDateTime) for t in times[2:]) / 1e7   # kernel + user, seconds
        finally:
            _k32.CloseHandle(handle)
        now = time.time()
        cpu = None
        before = self.last.get(pid)
        if before and now > before[0]:
            cpu = round(max(0.0, (busy - before[1]) / (now - before[0]) * 100), 1)
        self.last[pid] = (now, busy)
        return {"ramMo": int(counters.WorkingSetSize // (1024 * 1024)), "cpu": cpu}


def cores():
    return os.cpu_count() or 1
