"""Recolecta información del sistema macOS."""

import platform
import shutil
import subprocess


def _run(cmd: str) -> str:
    try:
        return subprocess.check_output(cmd, shell=True, text=True, timeout=5).strip()
    except Exception:
        return "N/A"


def get_system_info() -> dict:
    disk = shutil.disk_usage("/")
    total_gb = disk.total / (1024 ** 3)
    used_gb = disk.used / (1024 ** 3)
    free_gb = disk.free / (1024 ** 3)
    pct = (disk.used / disk.total) * 100

    chip = _run("sysctl -n machdep.cpu.brand_string")
    if chip == "N/A" or "Apple" not in chip:
        chip = _run("system_profiler SPHardwareDataType | awk '/Chip:/{$1=\"\"; print $0}'").strip()
        if not chip or chip == "N/A":
            chip = platform.processor() or "Desconocido"

    ram_bytes = _run("sysctl -n hw.memsize")
    try:
        ram_gb = int(ram_bytes) / (1024 ** 3)
        ram = f"{ram_gb:.0f} GB"
    except ValueError:
        ram = "N/A"

    macos_name = _run("sw_vers -productName")
    macos_ver = _run("sw_vers -productVersion")
    build = _run("sw_vers -buildVersion")

    arch = platform.machine()
    arch_label = "Apple Silicon" if arch == "arm64" else "Intel"

    return {
        "chip": chip,
        "arch": arch_label,
        "ram": ram,
        "macos": f"{macos_name} {macos_ver} ({build})",
        "disk_total": f"{total_gb:.1f} GB",
        "disk_used": f"{used_gb:.1f} GB",
        "disk_free": f"{free_gb:.1f} GB",
        "disk_pct": pct,
        "hostname": platform.node(),
    }
