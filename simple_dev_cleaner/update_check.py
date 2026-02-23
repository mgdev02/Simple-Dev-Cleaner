"""Run pip/pipx upgrade from GitHub (main branch)."""

import os
import shutil
import subprocess
import sys

GITHUB_REPO = "mgdev02/Simple-Dev-Cleaner"
INSTALL_URL = f"git+https://github.com/{GITHUB_REPO}.git"
INSTALL_SCRIPT_URL = f"https://raw.githubusercontent.com/{GITHUB_REPO}/main/install.sh"


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
    seen = set()
    parts = []
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
    Run upgrade: pipx upgrade --force, or install script with --force, or pip.
    Return True on success.
    """
    env = _env_with_full_path()
    pipx_path = _find_pipx()
    if pipx_path:
        try:
            r = subprocess.run(
                [pipx_path, "upgrade", "--force", "simple-dev-cleaner"],
                capture_output=True,
                text=True,
                timeout=120,
                env=env,
            )
            if r.returncode == 0:
                return True
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass
    # Fallback: run install script with --force (same as user would run)
    try:
        r = subprocess.run(
            [
                "bash",
                "-c",
                f'curl -fsSL "{INSTALL_SCRIPT_URL}" | bash -s -- --force',
            ],
            capture_output=True,
            text=True,
            timeout=120,
            env=env,
        )
        if r.returncode == 0:
            return True
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    try:
        r = subprocess.run(
            [
                sys.executable,
                "-m",
                "pip",
                "install",
                "--user",
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
    """
    Start upgrade in background (pipx or pip). Does not block.
    """
    pipx_path = _find_pipx()
    if pipx_path:
        try:
            subprocess.Popen(
                [pipx_path, "upgrade", "--force", "simple-dev-cleaner"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
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
                "--user",
                "--upgrade",
                INSTALL_URL,
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
    except (FileNotFoundError, OSError):
        pass
