from __future__ import annotations

import logging
from pathlib import Path

LOG_DIR = Path(__file__).resolve().parent.parent / "logs"
LOG_FILE = LOG_DIR / "glyphbound.log"


def setup_logging() -> None:
    """Initialize file logging under the `glyphbound` logger namespace.

    Writes a fresh log/glyphbound.log each launch (mode="w"). A FileHandler
    is used (never a StreamHandler) so logging cannot corrupt the Textual TUI.
    """
    LOG_DIR.mkdir(exist_ok=True)
    handler = logging.FileHandler(LOG_FILE, mode="w", encoding="utf-8")
    handler.setFormatter(logging.Formatter(
        "%(asctime)s %(levelname)-5s %(name)-22s %(message)s",
        datefmt="%H:%M:%S",
    ))
    root = logging.getLogger("glyphbound")
    root.setLevel(logging.DEBUG)
    root.handlers.clear()  # idempotent if called more than once
    root.addHandler(handler)
    root.propagate = False
