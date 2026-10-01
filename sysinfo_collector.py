import ctypes
import getpass
import json
import os
import platform
import shutil
import socket
import sys
from datetime import datetime


def get_os():
    system = platform.system()
    info = {
        "system": system,
        "release": platform.release(),
        "version": platform.version(),
        "machine": platform.machine(),
    }
    if system == "Linux":
        try:
            info["distro"] = platform.freedesktop_os_release().get("PRETTY_NAME")
        except (AttributeError, OSError):
            info["distro"] = None
    elif system == "Darwin":
        info["mac_version"] = platform.mac_ver()[0]
    elif system == "Windows":
        info["windows_build"] = platform.win32_ver()[1]
        info["windows_edition"] = platform.win32_edition()
    return info


def get_python():
    return {"version": platform.python_version(), "executable": sys.executable}


def get_host():
    now = datetime.now().astimezone()
    admin = ctypes.windll.shell32.IsUserAnAdmin() if system == "Windows" else os.geteuid() == 0
    return {
        "hostname": socket.gethostname(),
        "user": getpass.getuser(),
        "home_dir": os.path.expanduser("~"),
        "timezone": now.tzname(),
        "utc_offset_hours": now.utcoffset().total_seconds() / 3600,
        "is_admin": bool(admin),
    }


def get_cpu():
    info = {"logical_cores": os.cpu_count()}
    if system == "Windows":
        info["model"] = os.environ.get("PROCESSOR_IDENTIFIER")
    else:
        info["load_average"] = [round(x, 2) for x in os.getloadavg()]
    return info


def get_memory():
    GB = 1024 ** 3
    if system == "Windows":
        status = (ctypes.c_ulonglong * 8)()
        status[0] = ctypes.sizeof(status)
        ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status))
        total, free = status[1], status[2]
    else:
        page = os.sysconf("SC_PAGE_SIZE")
        total = page * os.sysconf("SC_PHYS_PAGES")
        free = page * os.sysconf("SC_AVPHYS_PAGES") if "SC_AVPHYS_PAGES" in os.sysconf_names else None
    info = {"total_gb": round(total / GB, 2)}
    if free is not None:
        info["available_gb"] = round(free / GB, 2)
        info["used_percent"] = round((total - free) / total * 100, 1)
    return info


def get_disk():
    GB = 1024 ** 3
    root = "C:\\" if system == "Windows" else "/"
    total, used, free = shutil.disk_usage(root)
    return {
        "root": root,
        "total_gb": round(total / GB, 2),
        "used_gb": round(used / GB, 2),
        "free_gb": round(free / GB, 2),
        "used_percent": round(used / total * 100, 1),
    }


def get_network():
    return {"hostname": socket.gethostname(),
            "ip_addresses": socket.gethostbyname_ex(socket.gethostname())[2]}


def safe(func):
    try:
        return func()
    except Exception:
        return None


os_info = get_os()
system = os_info["system"]

report = {
    "collected_at": datetime.now().astimezone().isoformat(),
    "os": os_info,
    "python": safe(get_python),
    "host": safe(get_host),
    "cpu": safe(get_cpu),
    "memory": safe(get_memory),
    "disk": safe(get_disk),
    "network": safe(get_network),
}

path = sys.argv[1] if len(sys.argv) > 1 else "system_info.json"
with open(path, "w", encoding="utf-8") as f:
    json.dump(report, f, ensure_ascii=False, indent=4)
