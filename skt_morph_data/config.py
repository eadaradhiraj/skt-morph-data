from __future__ import annotations

import os
from pathlib import Path

# Where the sqlite DB lives for end users (nltk-style).
# XDG compliant: $XDG_DATA_HOME or ~/.local/share
def _default_data_dir() -> Path:
    xdg = os.environ.get("XDG_DATA_HOME")
    if xdg:
        return Path(xdg) / "skt_morph_data"
    # also respect SKT_MORPH_DATA_DIR
    custom = os.environ.get("SKT_MORPH_DATA_DIR")
    if custom:
        return Path(custom)
    return Path.home() / ".local" / "share" / "skt_morph_data"

DEFAULT_DATA_DIR = _default_data_dir()
DEFAULT_DB_PATH = DEFAULT_DATA_DIR / "skt_morph.db"

# Github release asset URL — change version tag as you publish releases.
# Users can override with env var SKT_MORPH_DB_URL.
# We try several mirrors in order.
DEFAULT_DB_URLS: list[str] = [
    os.environ.get("SKT_MORPH_DB_URL", "https://github.com/eadaradhiraj/skt-morph-data/releases/download/v0.2.0/skt_morph.db"),
    "https://github.com/eadaradhiraj/skt-morph-data/releases/download/v0.1.0/skt_morph.db",
    # fallback: raw file committed to repo (useful for dev / if release not yet published)
    "https://raw.githubusercontent.com/eadaradhiraj/skt-morph-data/main/data/skt_morph.db",
]

# Bundled DB inside the repo / package (when running from source checkout)
REPO_DB_CANDIDATES: list[Path] = [
    Path(__file__).resolve().parents[1] / "data" / "skt_morph.db",
    Path(__file__).resolve().parents[1] / "skt_morph.db",
    Path(__file__).resolve().parents[2] / "data" / "skt_morph.db",
]

DB_VERSION = "0.2.0"
