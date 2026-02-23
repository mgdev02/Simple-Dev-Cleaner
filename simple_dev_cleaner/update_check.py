"""Check for updates on GitHub and run pip/pipx upgrade."""

import json
import subprocess
import sys
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

GITHUB_REPO = "mgdev02/Simple-Dev-Cleaner"
GITHUB_API_LATEST = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
GITHUB_API_TAGS = f"https://api.github.com/repos/{GITHUB_REPO}/tags"
INSTALL_URL = f"git+https://github.com/{GITHUB_REPO}.git"


def _parse_version(version_str: str) -> tuple[int, ...]:
    """Convert '1.0.0' or 'v1.0.1' to (1, 0, 1) for comparison."""
    s = version_str.strip().lstrip("vV")
    parts = []
    for part in s.split(".")[:4]:
        try:
            parts.append(int(part))
        except ValueError:
            parts.append(0)
    return tuple(parts) if parts else (0,)


def _fetch_json(url: str, timeout: float = 5.0) -> dict | list | None:
    """Fetch URL and return parsed JSON, or None on error."""
    try:
        req = Request(url, headers={"Accept": "application/vnd.github.v3+json"})
        with urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode())
    except (URLError, HTTPError, json.JSONDecodeError, OSError):
        return None


def get_latest_version() -> str | None:
    """
    Return the latest version string from GitHub (e.g. '1.0.1').
    Tries releases/latest first, then tags.
    """
    data = _fetch_json(GITHUB_API_LATEST)
    if isinstance(data, dict) and data.get("tag_name"):
        return data["tag_name"].strip().lstrip("vV")
    data = _fetch_json(GITHUB_API_TAGS)
    if isinstance(data, list) and len(data) > 0:
        name = data[0].get("name", "")
        return name.strip().lstrip("vV") if name else None
    return None


def has_newer_version(current: str, latest: str | None) -> bool:
    """Return True if latest is a newer version than current."""
    if not latest:
        return False
    return _parse_version(latest) > _parse_version(current)


def run_update() -> bool:
    """
    Run upgrade: try pipx first, then pip install --user --upgrade.
    Return True if upgrade was run successfully.
    """
    # Prefer pipx (recommended install method)
    try:
        r = subprocess.run(
            [sys.executable, "-m", "pipx", "upgrade", "simple-dev-cleaner"],
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
