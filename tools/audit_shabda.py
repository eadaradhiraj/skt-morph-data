#!/usr/bin/env python3
"""Batch auditor verifying skt_morph_data subanta declensions against the 9,007-word shabda_data2.json oracle.

Usage:
  python tools/audit_shabda.py --sample 200
  python tools/audit_shabda.py --full --report shabda_audit_report.json
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any

from skt_morph_data.subanta import (
    SubantaSlot,
    deva_to_slp1,
    generate_tables,
    VIBHAKTIS,
    VACANAS,
    VIBHAKTI_INDEX,
    VACANA_INDEX,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_PATHS = [
    REPO_ROOT.parent / "dhaturupa-wasm" / "data" / "shabda_data2.json",
    REPO_ROOT / "data" / "shabda_data2.json",
]


def find_shabda_path() -> Path:
    for p in CANDIDATE_PATHS:
        if p.exists():
            return p
    raise FileNotFoundError(
        "shabda_data2.json not found; looked in: " + ", ".join(str(x) for x in CANDIDATE_PATHS)
    )


def parse_site_forms(forms: str) -> list[SubantaSlot]:
    raw = str(forms or "").split(";")
    if len(raw) != 24:
        return []
    slots: list[SubantaSlot] = []
    VOC = "\u0939\u0947"
    for i, s in enumerate(raw):
        vib_i = i // 3
        vac_i = i % 3
        vib = VIBHAKTIS[vib_i]
        vac = VACANAS[vac_i]
        token = s.strip()
        alts = [p.strip() for p in token.replace("/", "-").split("-") if p.strip()]
        forms_list: list[str] = []
        for alt in alts:
            if alt.startswith(VOC + " "):
                alt = alt[len(VOC) + 1:].strip()
            elif vib_i == 7 and alt.startswith(VOC):
                alt = alt[len(VOC):].strip()
            slp = deva_to_slp1(alt)
            if slp and slp not in forms_list:
                forms_list.append(slp)
        slots.append(
            SubantaSlot(vibhakti=VIBHAKTI_INDEX[vib], vacana=VACANA_INDEX[vac], forms=forms_list)
        )
    return slots


def audit_shabda(sample: int | None = None, report_path: Path | None = None) -> dict[str, Any]:
    path = find_shabda_path()
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    entries = data.get("data") if isinstance(data, dict) else data

    if sample and sample < len(entries):
        entries = entries[:sample]

    total = len(entries)
    checked = 0
    matched = 0
    discrepancies: list[dict[str, Any]] = []

    t0 = time.time()
    for e in entries:
        word = e.get("word", "")
        linga_raw = e.get("linga", "")
        linga_s = "m" if linga_raw == "P" else ("f" if linga_raw == "S" else "n")
        slp_stem = deva_to_slp1(word)
        if not slp_stem:
            continue

        raw_forms = (e.get("forms") or "").split(";")
        exp_slots = parse_site_forms(e.get("forms") or "")
        if len(exp_slots) != 24 or len(raw_forms) != 24:
            continue

        # Non-empty cells: matching dhaturupa-wasm/web/audit-site-grids.cjs,
        # cells where the dictionary lists no form (empty string) carry no information
        # and are skipped in comparison.
        listed = [i for i, c in enumerate(raw_forms) if c.strip() != ""]

        checked += 1
        try:
            tabs = generate_tables(slp_stem, linga_s)
        except Exception as exc:
            if len(discrepancies) < 50:
                discrepancies.append({
                    "word": word, "stem": slp_stem, "linga": linga_s,
                    "urlid": e.get("urlid"), "error": f"Exception: {exc}"
                })
            continue

        entry_matched = False
        for tab in tabs:
            if all(set(tab.cells[i].forms) == set(exp_slots[i].forms) for i in listed):
                entry_matched = True
                break

        if entry_matched:
            matched += 1
        else:
            if len(discrepancies) < 50:
                first_diff = None
                if tabs:
                    tab = tabs[0]
                    for idx in listed:
                        act = tab.cells[idx]
                        exp = exp_slots[idx]
                        if set(act.forms) != set(exp.forms):
                            first_diff = {
                                "vibhakti": VIBHAKTIS[idx // 3],
                                "vacana": VACANAS[idx % 3],
                                "actual": act.forms,
                                "expected": exp.forms,
                            }
                            break
                discrepancies.append({
                    "word": word, "stem": slp_stem, "linga": linga_s,
                    "urlid": e.get("urlid"), "first_diff": first_diff
                })

    dur = time.time() - t0
    rate = matched / checked if checked else 0.0

    result = {
        "total_entries": total,
        "checked": checked,
        "matched": matched,
        "failed": checked - matched,
        "pass_rate_pct": round(rate * 100, 2),
        "elapsed_seconds": round(dur, 2),
        "discrepancies_sample": discrepancies,
    }

    print("\n" + "=" * 60)
    print(" SHABDA NOMINAL 9,007-WORD ORACLE AUDIT REPORT")
    print("=" * 60)
    print(f"Total entries:   {total}")
    print(f"Checked words:   {checked}")
    print(f"Exact 24/24:     {matched} ({rate * 100:.2f}%)")
    print(f"Failed words:    {checked - matched}")
    print(f"Elapsed time:    {dur:.2f}s ({checked / max(dur, 0.001):.0f} words/sec)")
    print("=" * 60)

    if report_path:
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print(f"Report written to: {report_path}")

    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit skt_morph_data against shabda_data2.json oracle")
    parser.add_argument("--sample", type=int, help="Sample N words to audit")
    parser.add_argument("--full", action="store_true", help="Audit all 9,007 nominal words")
    parser.add_argument("--report", type=Path, help="Path to write JSON audit report")
    args = parser.parse_args()

    sample_val = None if args.full else (args.sample or 200)
    res = audit_shabda(sample=sample_val, report_path=args.report)
    if res["pass_rate_pct"] < 90.0:
        sys.exit(1)


if __name__ == "__main__":
    main()
