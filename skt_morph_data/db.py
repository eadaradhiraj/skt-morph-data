from __future__ import annotations

import sqlite3
from pathlib import Path

from .config import DEFAULT_DB_PATH
from .download import download_db

_conn_cache: dict[str, sqlite3.Connection] = {}


def get_db_path() -> Path:
    return DEFAULT_DB_PATH


def ensure_db(force: bool = False, url: str | None = None, dest: Path | None = None) -> Path:
    """Ensure DB exists, downloading if needed. Returns path."""
    target = Path(dest) if dest else DEFAULT_DB_PATH
    if target.exists() and not force:
        return target
    return download_db(dest=target, force=force, url=url)


def connect(db_path: Path | str | None = None, ensure: bool = True) -> sqlite3.Connection:
    """Return sqlite3 connection (ROW factory). Auto-downloads if missing and ensure=True."""
    path = Path(db_path) if db_path else DEFAULT_DB_PATH
    if ensure and not path.exists():
        ensure_db(dest=path)
    if not path.exists():
        raise FileNotFoundError(
            f"DB not found at {path}. Run `skt-morph download` or "
            f"`python -m skt_morph_data.download` or build with scripts/json_to_sqlite.py"
        )
    key = str(path.resolve())
    if key in _conn_cache:
        try:
            _conn_cache[key].execute("SELECT 1")
            return _conn_cache[key]
        except sqlite3.ProgrammingError:
            pass
    con = sqlite3.connect(str(path))
    con.row_factory = sqlite3.Row
    # performance pragmas
    con.execute("PRAGMA journal_mode=WAL;")
    con.execute("PRAGMA synchronous=NORMAL;")
    con.execute("PRAGMA foreign_keys=ON;")
    _conn_cache[key] = con
    return con
