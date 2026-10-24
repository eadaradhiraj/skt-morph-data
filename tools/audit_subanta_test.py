#!/usr/bin/env python3
"""Batch mass auditor verifying skt_morph_data krdanta declensions against the 5.2GB data/subanta_test/ oracle.

Usage:
  python tools/audit_subanta_test.py --sample 20
  python tools/audit_subanta_test.py --gana 01 --limit 50
  python tools/audit_subanta_test.py --full --workers 8 --report audit_report.json
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from typing import Any

from skt_morph_data.krdanta import krt_table

TABLE_VIBHAKTI_INDEX = {
    "praTamA": 1, "prathamA": 1,
    "dvitIyA": 2,
    "tFtIyA": 3, "tftIyA": 3,
    "caturTI": 4,
    "paYcamI": 5,
    "zazWI": 6,
    "saptamI": 7,
    "sambodana": 8, "saMboDana": 8, "sambodhana": 8,
}

TABLE_VACANA_INDEX = {
    "eka": 1, "dvi": 2, "bahu": 3,
}


def normalize_cell_forms(forms: list[str]) -> set[str]:
    return {f.removeprefix("he ").replace("-", "").strip() for f in forms if f.strip()}


def deduce_gender(g_raw: str, ref: str | None) -> str:
    if g_raw in ("pu", "puM", "m"):
        return "m"
    if g_raw in ("strI", "str", "f"):
        return "f"
    if g_raw in ("napuM", "n"):
        return "n"
    if ref:
        r = ref.lower()
        if any(x in r for x in ("devi", "mala", "mati", "dhenu")):
            return "f"
        if any(x in r for x in ("deva", "bhavat", "sedivas", "gacchat", "dadat", "sadhu")):
            return "m"
        if any(x in r for x in ("phala", "vidvas", "viyat", "jagat", "pacat", "tudat", "phalavat")):
            return "n"
    return "n"


def audit_dhatu_file(json_path: Path) -> dict[str, Any]:
    """Audit all base and upasarga tables in a single dhatu test JSON file."""
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        return {"file": str(json_path), "error": str(e), "tables": 0, "cells_passed": 0, "cells_failed": 0, "discrepancies": []}

    dhatu_id = data.get("id") or json_path.stem.split(".")[0]
    stats: dict[str, Any] = {
        "dhatu_id": dhatu_id,
        "tables": 0,
        "cells_passed": 0,
        "cells_failed": 0,
        "discrepancies": [],
    }

    def check_entry(entry: dict, family: str):
        if not entry.get("table_ok"):
            return
        exp_table = entry.get("table") or {}
        if not exp_table:
            return
        pratyaya = entry.get("pratyaya")
        ref = entry.get("ref")
        g_raw = entry.get("gender", "")
        gender = deduce_gender(g_raw, ref)
        displays = entry.get("displays", [])
        val = displays[0] if displays else entry.get("pratipadika", "")

        # Skip known site-corrupt entry where stem does not match pratyaya at all
        if pratyaya == "ktavatu" and not val.endswith(("vat", "vAn", "vatI", "vad")):
            return

        tab = krt_table(family, pratyaya, gender, val, dhatu_id)
        if tab is None:
            tab = krt_table(family, pratyaya, gender, entry.get("pratipadika", ""), dhatu_id)

        stats["tables"] += 1
        if tab is None:
            stats["cells_failed"] += 24
            stats["discrepancies"].append({
                "pratyaya": pratyaya, "gender": gender, "ref": ref,
                "error": f"krt_table returned None for {val}"
            })
            return

        for vibh, vac_dict in exp_table.items():
            v_idx = TABLE_VIBHAKTI_INDEX.get(vibh)
            if not v_idx:
                continue
            for vac, exp_forms in vac_dict.items():
                vc_idx = TABLE_VACANA_INDEX.get(vac)
                if not vc_idx:
                    continue
                exp_set = normalize_cell_forms(exp_forms)
                slot = next((c for c in tab.cells if c.vibhakti == v_idx and c.vacana == vc_idx), None)
                act_set = normalize_cell_forms(slot.forms) if slot else set()

                if exp_set == act_set:
                    stats["cells_passed"] += 1
                else:
                    stats["cells_failed"] += 1
                    if len(stats["discrepancies"]) < 20:
                        stats["discrepancies"].append({
                            "pratyaya": pratyaya, "gender": gender, "ref": ref,
                            "slot": f"{vibh}.{vac}",
                            "expected": sorted(exp_set),
                            "actual": sorted(act_set),
                        })

    # 1. Base tables
    base_dict = data.get("base") or {}
    for fam in ("krut", "san_krut", "nich_krut", "yang_krut", "yangluk_krut"):
        for entry in base_dict.get(fam) or []:
            check_entry(entry, fam)

    # 2. Upasarga tables
    upasarga_dict = data.get("upasarga") or {}
    for pfx, pfx_obj in upasarga_dict.items():
        tabs = pfx_obj.get("tabs") or {}
        for fam in ("krut", "san_krut", "nich_krut", "yang_krut", "yangluk_krut"):
            for entry in tabs.get(fam) or []:
                check_entry(entry, fam)

    return stats


def main():
    parser = argparse.ArgumentParser(description="Mass auditor for krdanta subantas against subanta_test data.")
    parser.add_argument("--data-dir", default="data/subanta_test", help="Path to data/subanta_test")
    parser.add_argument("--sample", type=int, default=None, help="Sample N dhatus total")
    parser.add_argument("--gana", default=None, help="Filter to specific gana, e.g. 01")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of files")
    parser.add_argument("--workers", type=int, default=None, help="Number of worker processes")
    parser.add_argument("--report", default=None, help="JSON output file for discrepancy report")
    args = parser.parse_args()

    data_dir = Path(args.data_dir)
    if not data_dir.exists():
        print(f"Error: {data_dir} does not exist", file=sys.stderr)
        sys.exit(1)

    if args.gana:
        files = sorted(data_dir.glob(f"{args.gana}/*.json"))
    else:
        files = sorted(data_dir.glob("*/*.json"))

    # Exclude non-dhatu manifest or split files if needed
    files = [f for f in files if "manifest" not in f.name and "upasarga_" not in f.name]

    if args.sample:
        import random
        random.seed(42)
        if len(files) > args.sample:
            files = random.sample(files, args.sample)
    elif args.limit:
        files = files[:args.limit]

    print(f"Auditing {len(files)} dhatu files using {args.workers or os.cpu_count()} workers...")
    start_time = time.time()

    total_tables = 0
    total_passed = 0
    total_failed = 0
    all_discrepancies = []

    with ProcessPoolExecutor(max_workers=args.workers) as executor:
        futures = {executor.submit(audit_dhatu_file, f): f for f in files}
        done = 0
        for future in as_completed(futures):
            res = future.result()
            total_tables += res["tables"]
            total_passed += res["cells_passed"]
            total_failed += res["cells_failed"]
            if res["discrepancies"]:
                all_discrepancies.extend(res["discrepancies"])
            done += 1
            if done % 10 == 0 or done == len(files):
                pct = (done / len(files)) * 100
                total_cells = total_passed + total_failed
                rate = (total_passed / total_cells * 100) if total_cells else 0.0
                print(f"\r  [{pct:5.1f}%] {done}/{len(files)} files | {total_tables} tables | {total_cells} cells | Pass Rate: {rate:6.2f}%", end="", flush=True)

    print()
    elapsed = time.time() - start_time
    total_cells = total_passed + total_failed
    final_rate = (total_passed / total_cells * 100) if total_cells else 0.0

    print("=" * 60)
    print(f"Audit Complete in {elapsed:.2f}s")
    print(f"Dhatus audited: {len(files)}")
    print(f"Tables checked: {total_tables:,}")
    print(f"Cells checked:  {total_cells:,}")
    print(f"Cells passed:   {total_passed:,}")
    print(f"Cells failed:   {total_failed:,}")
    print(f"Final Accuracy: {final_rate:.2f}%")
    print("=" * 60)

    if args.report:
        report_data = {
            "elapsed_seconds": elapsed,
            "dhatus_count": len(files),
            "tables_checked": total_tables,
            "cells_checked": total_cells,
            "cells_passed": total_passed,
            "cells_failed": total_failed,
            "accuracy_percent": final_rate,
            "sample_discrepancies": all_discrepancies[:100],
        }
        with open(args.report, "w", encoding="utf-8") as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)
        print(f"Report saved to {args.report}")


if __name__ == "__main__":
    main()
