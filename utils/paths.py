import os
import sys
from pathlib import Path


def get_base_dir() -> Path:
    """
    Returns the application root directory.
    Supports PyInstaller bundle (sys._MEIPASS) and normal python execution.
    """
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parent.parent


def get_asset_path(filename: str) -> Path:
    """
    Returns the resolved path to an asset file.
    """
    base = get_base_dir()
    asset_file = base / "assets" / filename
    if not asset_file.exists():
        # Fallback to current working directory if relative
        cwd_asset = Path.cwd() / "assets" / filename
        if cwd_asset.exists():
            return cwd_asset
    return asset_file


def get_log_dir() -> Path:
    """
    Returns the directory where application logs are stored.
    Creates the directory if it does not exist.
    """
    # For desktop application, store logs in the project root or local app directory
    base = Path.cwd()
    log_dir = base / "logs"
    try:
        log_dir.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass
    return log_dir
