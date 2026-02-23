"""Paths and config directory (XDG-style)."""

from pathlib import Path


def get_config_dir() -> Path:
    """
    User data directory.
    Installed (site-packages): ~/.config/simple-dev-cleaner
    From source: package directory (for development).
    """
    pkg_dir = Path(__file__).resolve().parent
    if "site-packages" in str(pkg_dir) or "dist-packages" in str(pkg_dir):
        config_home = Path.home() / ".config" / "simple-dev-cleaner"
        config_home.mkdir(parents=True, exist_ok=True)
        return config_home
    return pkg_dir


CONFIG_DIR = get_config_dir()
CONFIG_FILE = CONFIG_DIR / "config.toml"
HISTORY_FILE = CONFIG_DIR / "history.toml"
LOG_FILE = CONFIG_DIR / "cleaner.log"
