"""Logging to data/lily.log only, so the terminal stays clean."""
import logging

from lily.utils.paths import ensure_data_dir

_configured = False


def get_logger(name: str = "lily") -> logging.Logger:
    global _configured
    if not _configured:
        logging.basicConfig(
            filename=ensure_data_dir() / "lily.log",
            level=logging.INFO,
            format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        )
        _configured = True
    return logging.getLogger(name)
