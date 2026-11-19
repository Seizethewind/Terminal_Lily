"""Where things live on disk."""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONFIG_DIR = ROOT / "config"
DATA_DIR = ROOT / "data"
PLUGINS_DIR = ROOT / "plugins"


def ensure_data_dir() -> Path:
    """Create the (gitignored) data folder if it does not exist yet."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    return DATA_DIR


def workplace() -> Path:
    """The one folder Lily works in: Terminal_Lily_Workplace inside LILY_WORKPLACE_DIR (default: home)."""
    base = Path(os.environ.get("LILY_WORKPLACE_DIR") or "~").expanduser()
    folder = (base / "Terminal_Lily_Workplace").resolve()
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def in_workplace(path) -> Path:
    """Resolve a tool path: a relative one starts in the workplace, an absolute one stays as given."""
    return (workplace() / Path(str(path)).expanduser()).resolve()
