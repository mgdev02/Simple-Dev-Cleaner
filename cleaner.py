"""Motor de limpieza de dependencias de desarrollo."""

import json
import os
import shutil
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional

def _get_app_dir() -> Path:
    """Directorio de datos: proyecto si corre desde fuente, ~/.config/simple-dev-cleaner si está instalado."""
    pkg_dir = Path(__file__).resolve().parent
    if "site-packages" in str(pkg_dir) or "dist-packages" in str(pkg_dir):
        app_dir = Path.home() / ".config" / "simple-dev-cleaner"
        app_dir.mkdir(parents=True, exist_ok=True)
        return app_dir
    return pkg_dir

APP_DIR = _get_app_dir()
CONFIG_PATH = APP_DIR / "config.json"
LOG_PATH = APP_DIR / "cleaner.log"
PLIST_LABEL = "com.devcleaner.auto"
PLIST_PATH = Path.home() / "Library" / "LaunchAgents" / f"{PLIST_LABEL}.plist"

DEFAULT_SCAN_DIRS = [
    str(Path.home() / "Desktop"),
    str(Path.home() / "Documents"),
    str(Path.home() / "Developer"),
    str(Path.home() / "Projects"),
]

DEFAULT_TARGETS = ["node_modules", "venv", ".venv", "env", "ENV"]


@dataclass
class Config:
    scan_dirs: list[str] = field(default_factory=lambda: list(DEFAULT_SCAN_DIRS))
    target_names: list[str] = field(default_factory=lambda: list(DEFAULT_TARGETS))
    interval_hours: int = 24
    unused_hours: int = 48
    enabled: bool = True
    lang: str = "es"  # "es" | "en" — persiste idioma de la CLI

    def save(self):
        CONFIG_PATH.write_text(json.dumps(asdict(self), indent=2, ensure_ascii=False))

    @classmethod
    def load(cls) -> "Config":
        if CONFIG_PATH.exists():
            try:
                data = json.loads(CONFIG_PATH.read_text())
                return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})
            except Exception:
                pass
        cfg = cls()
        cfg.save()
        return cfg


@dataclass
class CleanResult:
    path: str
    name: str
    size_mb: float
    unused_hours: int
    deleted: bool
    error: Optional[str] = None


@dataclass
class RunSummary:
    timestamp: str
    results: list[dict]
    total_freed_mb: float
    dry_run: bool

    def save(self):
        history_path = APP_DIR / "history.json"
        history = []
        if history_path.exists():
            try:
                history = json.loads(history_path.read_text())
            except Exception:
                pass
        history.insert(0, asdict(self))
        history = history[:50]
        history_path.write_text(json.dumps(history, indent=2, ensure_ascii=False))

    @staticmethod
    def load_last() -> Optional[dict]:
        history_path = APP_DIR / "history.json"
        if history_path.exists():
            try:
                history = json.loads(history_path.read_text())
                return history[0] if history else None
            except Exception:
                pass
        return None

    @staticmethod
    def load_all() -> list[dict]:
        history_path = APP_DIR / "history.json"
        if history_path.exists():
            try:
                return json.loads(history_path.read_text())
            except Exception:
                pass
        return []


def _is_real_dep(path: Path) -> bool:
    name = path.name
    parent = path.parent
    if name == "node_modules":
        return (parent / "package.json").exists()
    if name in ("venv", ".venv", "env", "ENV", "env.bak", "venv.bak"):
        return (path / "bin" / "activate").exists() or (path / "pyvenv.cfg").exists()
    return False


def _is_nested_node_modules(path: Path) -> bool:
    parts = path.parts
    return parts.count("node_modules") > 1


def _unused_hours(path: Path) -> int:
    try:
        atime = path.stat().st_atime
        return int((time.time() - atime) / 3600)
    except OSError:
        return 0


def _dir_size_mb(path: Path) -> float:
    total = 0
    try:
        for entry in path.rglob("*"):
            try:
                if entry.is_file(follow_symlinks=False):
                    total += entry.stat(follow_symlinks=False).st_size
            except OSError:
                continue
    except OSError:
        pass
    return total / (1024 * 1024)


def scan(config: Config, dry_run: bool = True, progress_cb=None) -> RunSummary:
    results: list[CleanResult] = []
    total_freed = 0.0

    for scan_dir in config.scan_dirs:
        scan_path = Path(scan_dir).expanduser()
        if not scan_path.is_dir():
            continue

        for target_name in config.target_names:
            try:
                matches = list(scan_path.rglob(target_name))
            except PermissionError:
                continue

            for found in matches:
                if not found.is_dir():
                    continue
                if _is_nested_node_modules(found):
                    continue
                if not _is_real_dep(found):
                    continue

                hours = _unused_hours(found)
                if hours < config.unused_hours:
                    continue

                size = _dir_size_mb(found)
                result = CleanResult(
                    path=str(found),
                    name=found.name,
                    size_mb=round(size, 1),
                    unused_hours=hours,
                    deleted=False,
                )

                if not dry_run:
                    try:
                        shutil.rmtree(found)
                        marker = found.parent / "install_packages_again"
                        marker.write_text(
                            f"Carpeta '{found.name}' eliminada por DevCleaner "
                            f"(sin uso por {hours}h). Reinstalar dependencias.\n"
                        )
                        result.deleted = True
                        total_freed += size
                    except Exception as e:
                        result.error = str(e)

                results.append(result)
                if progress_cb:
                    progress_cb(result)

    summary = RunSummary(
        timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
        results=[asdict(r) for r in results],
        total_freed_mb=round(total_freed, 1),
        dry_run=dry_run,
    )
    summary.save()

    _write_log(summary)
    return summary


def _write_log(summary: RunSummary):
    mode = "DRY-RUN" if summary.dry_run else "CLEAN"
    lines = [f"[{summary.timestamp}] {mode} — {len(summary.results)} encontrados, {summary.total_freed_mb}MB liberados"]
    for r in summary.results:
        status = "BORRADO" if r["deleted"] else ("ERROR" if r.get("error") else "SIMULADO")
        lines.append(f"  [{status}] {r['path']} ({r['size_mb']}MB, {r['unused_hours']}h sin uso)")
    lines.append("")

    with open(LOG_PATH, "a") as f:
        f.write("\n".join(lines) + "\n")


def delete_from_summary(summary: RunSummary, progress_cb=None) -> float:
    """Elimina las carpetas listadas en un summary (de un dry-run previo). Retorna MB liberados."""
    import shutil
    total_freed = 0.0
    results = summary.results
    for i, r in enumerate(results):
        path = Path(r["path"])
        if not path.exists():
            if progress_cb:
                progress_cb(i + 1, len(results), r, None)
            continue
        try:
            size_mb = r.get("size_mb", 0) or 0
            shutil.rmtree(path)
            marker = path.parent / "install_packages_again"
            marker.write_text(
                f"Carpeta '{path.name}' eliminada por DevCleaner "
                f"(sin uso por {r.get('unused_hours', 0)}h). Reinstalar dependencias.\n"
            )
            total_freed += size_mb
            if progress_cb:
                progress_cb(i + 1, len(results), r, None)
        except Exception as e:
            if progress_cb:
                progress_cb(i + 1, len(results), r, str(e))
    return round(total_freed, 1)


# ── LaunchAgent management ──────────────────────────────────────────────────

def install_agent(config: Config) -> bool:
    python_path = os.path.join(APP_DIR, ".venv", "bin", "python3")
    if not os.path.exists(python_path):
        python_path = "/usr/bin/python3"

    cleaner_script = str(APP_DIR / "run_clean.py")
    _ensure_run_script(cleaner_script)

    interval = config.interval_hours * 3600

    plist = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>{PLIST_LABEL}</string>
    <key>ProgramArguments</key>
    <array>
        <string>{python_path}</string>
        <string>{cleaner_script}</string>
    </array>
    <key>StartInterval</key>
    <integer>{interval}</integer>
    <key>RunAtLoad</key>
    <true/>
    <key>LowPriorityIO</key>
    <true/>
    <key>StandardOutPath</key>
    <string>{APP_DIR}/agent_stdout.log</string>
    <key>StandardErrorPath</key>
    <string>{APP_DIR}/agent_stderr.log</string>
</dict>
</plist>"""

    try:
        os.system(f"launchctl unload '{PLIST_PATH}' 2>/dev/null")
        PLIST_PATH.parent.mkdir(parents=True, exist_ok=True)
        PLIST_PATH.write_text(plist)
        os.system(f"launchctl load '{PLIST_PATH}'")
        return True
    except Exception:
        return False


def uninstall_agent() -> bool:
    try:
        os.system(f"launchctl unload '{PLIST_PATH}' 2>/dev/null")
        if PLIST_PATH.exists():
            PLIST_PATH.unlink()
        return True
    except Exception:
        return False


def is_agent_installed() -> bool:
    return PLIST_PATH.exists()


def _ensure_run_script(path: str):
    from pathlib import Path as P
    script_dir = P(path).parent
    # Si el script está en ~/.config (instalado con pip), no tocar sys.path
    config_home = Path.home() / ".config" / "simple-dev-cleaner"
    path_insert = "" if script_dir == config_home else "import sys\nsys.path.insert(0, str(Path(__file__).parent))\n"
    script = f'''#!/usr/bin/env python3
"""Auto-run script invoked by LaunchAgent."""
from pathlib import Path
{path_insert}from cleaner import Config, scan

config = Config.load()
scan(config, dry_run=False)
'''
    P(path).write_text(script)
    os.chmod(path, 0o755)
