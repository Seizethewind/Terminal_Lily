"""Where things live on disk."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONFIG_DIR = ROOT / "config"
DATA_DIR = ROOT / "data"
PLUGINS_DIR = ROOT / "plugins"


def ensure_data_dir() -> Path:
    """Create the (gitignored) data folder if it does not exist yet."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    return DATA_DIR
