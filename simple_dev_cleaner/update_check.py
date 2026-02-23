"""Run pip/pipx upgrade from GitHub (main branch)."""

import shutil
import subprocess
import sys

GITHUB_REPO = "mgdev02/Simple-Dev-Cleaner"
INSTALL_URL = f"git+https://github.com/{GITHUB_REPO}.git"


def run_update() -> bool:
    """
    Run upgrade: try pipx from PATH first, then pip.
    Return True if upgrade was run successfully.
    """
    # Prefer pipx (must use binary from PATH when we run inside pipx venv)
    pipx_path = shutil.which("pipx")
    if pipx_path:
        try:
            r = subprocess.run(
                [pipx_path, "upgrade", "simple-dev-cleaner"],
                capture_output=True,
                text=True,
                timeout=120,
            )
            if r.returncode == 0:
                return True
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass
    # Fallback: pip install --user --upgrade
    try:
        r = subprocess.run(
            [
                sys.executable,
                "-m",
                "pip",
                "install",
                "--user",
                "--upgrade",
                INSTALL_URL,
            ],
            capture_output=True,
            text=True,
            timeout=120,
        )
        return r.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    return False


def run_update_background() -> None:
    """
    Start upgrade in background (pipx or pip). Does not block.
    """
    pipx_path = shutil.which("pipx")
    if pipx_path:
        try:
            subprocess.Popen(
                [pipx_path, "upgrade", "simple-dev-cleaner"],
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
