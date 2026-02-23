"""Development dependency cleanup engine."""

import os
import shutil
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional

try:
    import tomllib
except ImportError:
    import tomli as tomllib  # type: ignore

import tomli_w

from simple_dev_cleaner._config import CONFIG_DIR, CONFIG_FILE, HISTORY_FILE, LOG_FILE

APP_DIR = CONFIG_DIR
CONFIG_PATH = CONFIG_FILE
LOG_PATH = LOG_FILE
PLIST_LABEL = "com.simple_dev_cleaner.auto"
PLIST_PATH = Path.home() / "Library" / "LaunchAgents" / f"{PLIST_LABEL}.plist"

DEFAULT_SCAN_DIRS = [
    str(Path.home() / "Desktop"),
    str(Path.home() / "Documents"),
    str(Path.home() / "Developer"),
    str(Path.home() / "Projects"),
]

DEFAULT_TARGETS = ["node_modules", "venv", ".venv", "env", "ENV"]
DEFAULT_TARGET_FILES = [".DS_Store", "*.log", "Thumbs.db"]


def _load_toml(path: Path) -> dict:
    """Load a TOML file. Uses tomllib (3.11+) or tomli."""
    with open(path, "rb") as f:
        return tomllib.load(f)


def _sanitize_for_toml(obj):  # noqa: ANN001
    """Remove None values (TOML does not support them) from dicts/lists recursively."""
    if obj is None:
        return None
    if isinstance(obj, dict):
        return {k: _sanitize_for_toml(v) for k, v in obj.items() if v is not None}
    if isinstance(obj, list):
        return [_sanitize_for_toml(x) for x in obj]
    return obj


def _save_toml(path: Path, data: dict) -> None:
    """Save a dict as TOML (without None values)."""
    path.write_text(tomli_w.dumps(_sanitize_for_toml(data)), encoding="utf-8")


@dataclass
class Config:
    scan_dirs: list[str] = field(default_factory=lambda: list(DEFAULT_SCAN_DIRS))
    target_names: list[str] = field(default_factory=lambda: list(DEFAULT_TARGETS))
    target_files: list[str] = field(default_factory=lambda: list(DEFAULT_TARGET_FILES))
    interval_hours: int = 24
    unused_hours: int = 48
    enabled: bool = True
    lang: str = "es"

    def save(self) -> None:
        data = {"config": asdict(self)}
        _save_toml(CONFIG_PATH, data)

    @classmethod
    def load(cls) -> "Config":
        if CONFIG_PATH.exists():
            try:
                data = _load_toml(CONFIG_PATH)
                cfg = data.get("config") or data
                return cls(**{k: v for k, v in cfg.items() if k in cls.__dataclass_fields__})
            except Exception:
                pass
        # Migration from config.json (previous versions)
        legacy_path = CONFIG_PATH.with_suffix(".json")
        if legacy_path.exists():
            try:
                import json
                data = json.loads(legacy_path.read_text(encoding="utf-8"))
                cfg = cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})
                cfg.save()
                legacy_path.rename(legacy_path.with_suffix(".json.bak"))
                return cfg
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
    is_file: bool = False
    error: Optional[str] = None


@dataclass
class RunSummary:
    timestamp: str
    results: list[dict]
    total_freed_mb: float
    dry_run: bool

    def save(self) -> None:
        history: list[dict] = []
        if HISTORY_FILE.exists():
            try:
                data = _load_toml(HISTORY_FILE)
                history = data.get("runs", [])
            except Exception:
                pass
        run_dict = asdict(self)
        history.insert(0, run_dict)
        history = history[:50]
        _save_toml(HISTORY_FILE, {"runs": history})

    @staticmethod
    def load_last() -> Optional[dict]:
        if HISTORY_FILE.exists():
            try:
                data = _load_toml(HISTORY_FILE)
                runs = data.get("runs", [])
                return runs[0] if runs else None
            except Exception:
                pass
        legacy_path = HISTORY_FILE.with_suffix(".json")
        if legacy_path.exists():
            try:
                import json
                history = json.loads(legacy_path.read_text(encoding="utf-8"))
                return history[0] if history else None
            except Exception:
                pass
        return None

    @staticmethod
    def load_all() -> list[dict]:
        if HISTORY_FILE.exists():
            try:
                data = _load_toml(HISTORY_FILE)
                return data.get("runs", [])
            except Exception:
                pass
        legacy_path = HISTORY_FILE.with_suffix(".json")
        if legacy_path.exists():
            try:
                import json
                history = json.loads(legacy_path.read_text(encoding="utf-8"))
                _save_toml(HISTORY_FILE, {"runs": history[:50]})
                legacy_path.rename(legacy_path.with_suffix(".json.bak"))
                return history[:50]
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
    return path.parts.count("node_modules") > 1


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
                    is_file=False,
                )

                if not dry_run:
                    try:
                        shutil.rmtree(found)
                        marker = found.parent / "install_packages_again"
                        marker.write_text(
                            f"Folder '{found.name}' removed by Simple Dev Cleaner "
                            f"(unused for {hours}h). Reinstall dependencies.\n"
                        )
                        result.deleted = True
                        total_freed += size
                    except Exception as e:
                        result.error = str(e)

                results.append(result)
                if progress_cb:
                    progress_cb(result)

    # Files (target_files: .DS_Store, *.log, etc.)
    for scan_dir in config.scan_dirs:
        scan_path = Path(scan_dir).expanduser()
        if not scan_path.is_dir():
            continue
        file_patterns = getattr(config, "target_files", None) or []
        for pattern in file_patterns:
            try:
                for found in scan_path.rglob(pattern):
                    if not found.is_file():
                        continue
                    hours = _unused_hours(found)
                    if hours < config.unused_hours:
                        continue
                    try:
                        size = found.stat().st_size / (1024 * 1024)
                    except OSError:
                        size = 0.0
                    result = CleanResult(
                        path=str(found),
                        name=found.name,
                        size_mb=round(size, 4) if size < 0.01 else round(size, 2),
                        unused_hours=hours,
                        deleted=False,
                        is_file=True,
                    )
                    if not dry_run:
                        try:
                            found.unlink()
                            result.deleted = True
                            total_freed += size
                        except Exception as e:
                            result.error = str(e)
                    results.append(result)
                    if progress_cb:
                        progress_cb(result)
            except PermissionError:
                continue

    summary = RunSummary(
        timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
        results=[asdict(r) for r in results],
        total_freed_mb=round(total_freed, 1),
        dry_run=dry_run,
    )
    summary.save()

    _write_log(summary)
    return summary


def _write_log(summary: RunSummary) -> None:
    mode = "DRY-RUN" if summary.dry_run else "CLEAN"
    lines = [
        f"[{summary.timestamp}] {mode} — {len(summary.results)} found, {summary.total_freed_mb}MB freed"
    ]
    for r in summary.results:
        status = "DELETED" if r["deleted"] else ("ERROR" if r.get("error") else "SIMULATED")
        lines.append(f"  [{status}] {r['path']} ({r['size_mb']}MB, {r['unused_hours']}h unused)")
    lines.append("")
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def delete_from_summary(summary: RunSummary, progress_cb=None) -> float:
    """Delete folders and files listed in a summary. Return MB freed."""
    total_freed = 0.0
    results = summary.results
    for i, r in enumerate(results):
        path = Path(r["path"])
        if not path.exists():
            if progress_cb:
                progress_cb(i + 1, len(results), r, None)
            continue
        is_file = r.get("is_file", False)
        try:
            size_mb = r.get("size_mb", 0) or 0
            if is_file:
                path.unlink()
            else:
                shutil.rmtree(path)
                marker = path.parent / "install_packages_again"
                marker.write_text(
                    f"Folder '{path.name}' removed by Simple Dev Cleaner "
                    f"(unused for {r.get('unused_hours', 0)}h). Reinstall dependencies.\n"
                )
            total_freed += size_mb
            if progress_cb:
                progress_cb(i + 1, len(results), r, None)
        except Exception as e:
            if progress_cb:
                progress_cb(i + 1, len(results), r, str(e))
    return round(total_freed, 1)


# ── LaunchAgent (macOS) ─────────────────────────────────────────────────────

def install_agent(config: Config) -> bool:
    import sys
    python_path = sys.executable
    script_path = CONFIG_DIR / "run_clean.py"
    _ensure_run_script(script_path)

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
        <string>{script_path}</string>
    </array>
    <key>StartInterval</key>
    <integer>{interval}</integer>
    <key>RunAtLoad</key>
    <true/>
    <key>LowPriorityIO</key>
    <true/>
    <key>StandardOutPath</key>
    <string>{CONFIG_DIR}/agent_stdout.log</string>
    <key>StandardErrorPath</key>
    <string>{CONFIG_DIR}/agent_stderr.log</string>
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


def _ensure_run_script(path: Path) -> None:
    script = '''#!/usr/bin/env python3
"""Auto-run script invoked by LaunchAgent."""
from simple_dev_cleaner.cleaner import Config, scan

config = Config.load()
scan(config, dry_run=False)
'''
    path.write_text(script, encoding="utf-8")
    os.chmod(path, 0o755)
