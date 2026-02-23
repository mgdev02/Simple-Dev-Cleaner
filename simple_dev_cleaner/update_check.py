"""Run pip/pipx upgrade from GitHub (main branch, always latest commit)."""

import os
import shutil
import subprocess
import sys

GITHUB_REPO = "mgdev02/Simple-Dev-Cleaner"
INSTALL_URL = f"git+https://github.com/{GITHUB_REPO}.git@main"
PKG_NAME = "simple-dev-cleaner"


def _find_pipx() -> str | None:
    """Find pipx binary (we may run inside pipx venv where PATH is limited)."""
    exe = shutil.which("pipx")
    if exe:
        return exe
    home = os.path.expanduser("~")
    for path in (
        os.path.join(home, ".local", "bin", "pipx"),
        "/opt/homebrew/bin/pipx",
        "/usr/local/bin/pipx",
    ):
        if os.path.isfile(path) and os.access(path, os.X_OK):
            return path
    return None


def _env_with_full_path() -> dict[str, str]:
    """Build env with PATH that includes common locations so pipx/git work."""
    home = os.path.expanduser("~")
    extra = [
        "/usr/local/bin",
        "/opt/homebrew/bin",
        os.path.join(home, ".local", "bin"),
        "/usr/bin",
        "/bin",
    ]
    current = os.environ.get("PATH", "")
    seen: set[str] = set()
    parts: list[str] = []
    for p in extra:
        if p not in seen:
            seen.add(p)
            parts.append(p)
    for p in current.split(os.pathsep):
        if p and p not in seen:
            seen.add(p)
            parts.append(p)
    return {**os.environ, "PATH": os.pathsep.join(parts)}


def run_update() -> bool:
    """
    Reinstall from the latest commit on main. pipx or pip fallback.
    Return True on success.
    """
    env = _env_with_full_path()
    pipx_path = _find_pipx()

    # pipx: uninstall + install ensures we always get the newest commit,
    # regardless of whether the version string changed.
    if pipx_path:
        try:
            subprocess.run(
                [pipx_path, "install", "--force", INSTALL_URL,
                 "--pip-args=--no-cache-dir"],
                capture_output=True,
                text=True,
                timeout=120,
                env=env,
            )
            return True
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass

    # Fallback: pip install --force-reinstall --no-cache-dir from git
    try:
        r = subprocess.run(
            [
                sys.executable,
                "-m",
                "pip",
                "install",
                "--upgrade",
                "--force-reinstall",
                "--no-cache-dir",
                INSTALL_URL,
            ],
            capture_output=True,
            text=True,
            timeout=120,
            env=env,
        )
        return r.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    return False


def run_update_background() -> None:
    """Start upgrade in background (pipx or pip). Does not block."""
    env = _env_with_full_path()
    pipx_path = _find_pipx()
    if pipx_path:
        try:
            subprocess.Popen(
                [pipx_path, "install", "--force", INSTALL_URL,
                 "--pip-args=--no-cache-dir"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
                env=env,
            )
            return
        except (FileNotFoundError, OSError):
            pass
    try:
        subprocess.Popen(
            [
                sys.executable,
                "-m",
                "pip",
                "install",
                "--upgrade",
                "--force-reinstall",
                "--no-cache-dir",
                INSTALL_URL,
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
            env=env,
        )
    except (FileNotFoundError, OSError):
        pass
