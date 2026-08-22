from __future__ import annotations

import os
import shutil
import ssl
import time
import urllib.request
from pathlib import Path

import certifi

from .config import DEFAULT_DB_PATH, DEFAULT_DB_URLS, REPO_DB_CANDIDATES

CHUNK = 1024 * 64


def _progress(msg: str) -> None:
    print(msg, flush=True)


def _copy_bundled(dest: Path) -> bool:
    for cand in REPO_DB_CANDIDATES:
        if cand.is_file():
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(cand, dest)
            _progress(f"Copied bundled DB from {cand} -> {dest}")
            return True
    return False


def _download_url(url: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(".tmp")
    ctx = ssl.create_default_context(cafile=certifi.where()) if "https" in url else None
    _progress(f"Downloading DB from {url} ...")
    req = urllib.request.Request(url, headers={"User-Agent": "skt-morph-data/0.1.0"})
    with urllib.request.urlopen(req, timeout=300, context=ctx) as resp:
        total = resp.headers.get("Content-Length")
        total = int(total) if total and total.isdigit() else None
        downloaded = 0
        start = time.time()
        with tmp.open("wb") as out:
            while True:
                chunk = resp.read(CHUNK)
                if not chunk:
                    break
                out.write(chunk)
                downloaded += len(chunk)
                if total:
                    pct = downloaded * 100 / total
                    elapsed = time.time() - start
                    speed = downloaded / elapsed / 1024 if elapsed else 0
                    print(f"\r  {pct:5.1f}% {downloaded//1024}KB / {total//1024}KB  {speed:.0f} KB/s", end="", flush=True)
            if total:
                print()
    tmp.replace(dest)
    _progress(f"Saved DB to {dest} ({dest.stat().st_size // 1024} KB)")


def download_db(dest: Path | None = None, force: bool = False, url: str | None = None) -> Path:
    """Ensure DB exists at dest (default user cache). Try bundled copy then URLs."""
    dest = Path(dest) if dest else DEFAULT_DB_PATH
    if dest.exists() and not force:
        _progress(f"DB already present at {dest}")
        return dest

    # 1. single URL forced
    if url:
        _download_url(url, dest)
        return dest

    # 2. bundled copy (fast, offline, for dev)
    if not force and _copy_bundled(dest):
        return dest

    # 3. try each default URL until one works
    last_err: Exception | None = None
    for u in DEFAULT_DB_URLS:
        try:
            _download_url(u, dest)
            return dest
        except Exception as e:
            last_err = e
            _progress(f"Failed to download from {u}: {e}")
            # try next
            continue

    raise RuntimeError(
        f"Could not download DB to {dest}. Last error: {last_err}. "
        "Build it locally with: python scripts/json_to_sqlite.py --data-dir data --output data/skt_morph.db"
    )


def ensure_db_interactive() -> Path:
    """Like nltk: prompt / auto-download if missing."""
    if DEFAULT_DB_PATH.exists():
        return DEFAULT_DB_PATH
    _progress(f"DB not found at {DEFAULT_DB_PATH}, attempting download...")
    return download_db(DEFAULT_DB_PATH)
