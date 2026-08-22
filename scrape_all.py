"""Scrape all ashtadhyayi.com dhatus with restartable progress tracking."""

from __future__ import annotations

import argparse
import sys
import time
from datetime import datetime
from pathlib import Path

from scrape_dhatu import (
    DEFAULT_FAILED_FILE,
    DEFAULT_IDS_FILE,
    DEFAULT_PROGRESS_FILE,
    ScrapeSession,
    append_id,
    create_driver,
    dhatu_output_path,
    fetch_all_dhatu_ids,
    fetch_dhatu_ids_from_github,
    load_id_set,
    save_dhatu_json,
    scrape_dhatu,
)


def log(message: str) -> None:
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{stamp}] {message}", flush=True)


def write_dhatu_ids(ids: list[str], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(ids) + "\n", encoding="utf-8")


def load_or_fetch_dhatu_ids(
    ids_file: Path,
    refresh: bool,
) -> list[str]:
    if ids_file.exists() and not refresh:
        ids = [line.strip() for line in ids_file.read_text(encoding="utf-8").splitlines() if line.strip()]
        if ids:
            log(f"Loaded {len(ids)} dhatu ids from {ids_file}")
            return ids

    log("Fetching dhatu id list from GitHub (fast, no browser)...")
    try:
        ids = fetch_dhatu_ids_from_github()
    except Exception:
        log("GitHub fetch failed; falling back to browser (slow, may take several minutes)...")
        driver = create_driver(headless=True)
        session = ScrapeSession()
        try:
            ids = fetch_all_dhatu_ids(driver, session)
        finally:
            driver.quit()

    write_dhatu_ids(ids, ids_file)
    log(f"Saved {len(ids)} dhatu ids to {ids_file}")
    return ids


def append_failed(failed_file: Path, dhatu_id: str, error: str) -> None:
    failed_file.parent.mkdir(parents=True, exist_ok=True)
    with failed_file.open("a", encoding="utf-8") as f:
        f.write(f"{dhatu_id}\t{error}\n")


def scrape_all(args: argparse.Namespace) -> int:
    output_dir = Path(args.output_dir)
    progress_file = output_dir / args.progress_file
    failed_file = output_dir / args.failed_file
    ids_file = output_dir / args.ids_file

    completed = load_id_set(progress_file)
    if completed:
        log(f"Resuming: {len(completed)} dhatus already completed")

    ids = load_or_fetch_dhatu_ids(ids_file, args.refresh_ids)
    if args.gana:
        ids = [d for d in ids if d.startswith(f"{args.gana}.")]
        log(f"Filtered to gana {args.gana}: {len(ids)} dhatus")

    pending = [d for d in ids if d not in completed]
    log(f"Pending: {len(pending)} / {len(ids)} dhatus")

    driver = create_driver(headless=not args.no_headless)
    session = ScrapeSession()
    failures = 0

    try:
        for index, dhatu_id in enumerate(pending, start=1):
            if args.restart_browser_every and index > 1 and (index - 1) % args.restart_browser_every == 0:
                log("Restarting browser to free memory...")
                driver.quit()
                driver = create_driver(headless=not args.no_headless)
                session = ScrapeSession()

            started = time.time()
            log(f"[{index}/{len(pending)}] Scraping {dhatu_id}...")
            try:
                data = scrape_dhatu(driver, dhatu_id, session)
                out_path = save_dhatu_json(data, output_dir)
                append_id(progress_file, dhatu_id)
                completed.add(dhatu_id)
                elapsed = time.time() - started
                if data.get("skipped"):
                    log(
                        f"Skipped {dhatu_id} ({data.get('skip_reason')}: "
                        f"{data.get('label') or 'no forms'}) -> {out_path} ({elapsed:.0f}s)"
                    )
                else:
                    log(f"Done {dhatu_id} -> {out_path} ({elapsed:.0f}s)")
            except KeyboardInterrupt:
                log(f"Interrupted during {dhatu_id}; it was NOT marked complete and will retry on resume")
                raise
            except Exception as exc:
                failures += 1
                append_failed(failed_file, dhatu_id, str(exc))
                log(f"FAILED {dhatu_id}: {exc}")
                if args.stop_on_error:
                    return 1

    except KeyboardInterrupt:
        log("Cancelled. Re-run the same command to resume.")
        return 130

    finally:
        driver.quit()

    log(f"Finished. Completed={len(completed)} failures={failures}")
    return 1 if failures else 0


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(
        description="Scrape all dhatus from ashtadhyayi.com (restartable batch job)",
    )
    parser.add_argument(
        "-o",
        "--output-dir",
        default="output",
        help="Root output directory (default: output)",
    )
    parser.add_argument(
        "--progress-file",
        default=DEFAULT_PROGRESS_FILE,
        help=f"Completed dhatu ids file inside output dir (default: {DEFAULT_PROGRESS_FILE})",
    )
    parser.add_argument(
        "--failed-file",
        default=DEFAULT_FAILED_FILE,
        help=f"Failed dhatu ids file inside output dir (default: {DEFAULT_FAILED_FILE})",
    )
    parser.add_argument(
        "--ids-file",
        default=DEFAULT_IDS_FILE,
        help=f"Cached full dhatu id list inside output dir (default: {DEFAULT_IDS_FILE})",
    )
    parser.add_argument(
        "--gana",
        help="Scrape only one gana folder, e.g. 06 for 06.xxxx dhatus",
    )
    parser.add_argument(
        "--refresh-ids",
        action="store_true",
        help="Re-fetch dhatu id list from site instead of using cached file",
    )
    parser.add_argument(
        "--restart-browser-every",
        type=int,
        default=25,
        help="Restart browser every N dhatus to avoid memory leaks (default: 25, 0=never)",
    )
    parser.add_argument(
        "--stop-on-error",
        action="store_true",
        help="Stop immediately on first failure instead of continuing",
    )
    parser.add_argument(
        "--no-headless",
        action="store_true",
        help="Run browser with UI visible",
    )
    args = parser.parse_args()
    raise SystemExit(scrape_all(args))


if __name__ == "__main__":
    main()
