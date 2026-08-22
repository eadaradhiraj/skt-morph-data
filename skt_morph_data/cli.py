from __future__ import annotations

import argparse
import json
import sys
import textwrap
from pathlib import Path

from .config import DEFAULT_DB_PATH
from .db import ensure_db, get_db_path
from .query import (
    get_chandrika,
    get_conjugations,
    get_dhatu,
    get_info,
    get_participles,
    get_prayoga,
    get_upasarga_entries,
    get_upasarga_forms,
    list_dhatus,
    query,
    search_dhatus,
    search_forms,
)

# ---------- pretty helpers ----------

def _print_json(obj, pretty: bool = True) -> None:
    json.dump(obj, sys.stdout, ensure_ascii=False, indent=2 if pretty else None)
    sys.stdout.write("\n")


def _print_table(rows: list[dict], headers: list[str] | None = None) -> None:
    if not rows:
        print("(no results)")
        return
    headers = headers or list(rows[0].keys())
    # column widths
    widths = {h: len(h) for h in headers}
    for r in rows:
        for h in headers:
            widths[h] = max(widths[h], len(str(r.get(h, ""))))
    # header
    line = " | ".join(h.ljust(widths[h]) for h in headers)
    print(line)
    print("-+-".join("-" * widths[h] for h in headers))
    for r in rows:
        print(" | ".join(str(r.get(h, "")).ljust(widths[h]) for h in headers))


# ---------- subcommands ----------

def cmd_download(args: argparse.Namespace) -> int:
    dest = Path(args.output) if args.output else None
    try:
        p = ensure_db(force=args.force, url=args.url, dest=dest)
        print(f"DB ready at {p} ({p.stat().st_size//1024} KB)")
        return 0
    except Exception as e:
        print(f"download failed: {e}", file=sys.stderr)
        return 1


def cmd_info(args: argparse.Namespace) -> int:
    try:
        d = get_dhatu(args.dhatu_id, db_path=args.db)
    except (KeyError, FileNotFoundError) as e:
        print(str(e), file=sys.stderr)
        return 1
    if args.json:
        _print_json(d["info"] if "info" in d else d)
    else:
        if d.get("skipped"):
            print(f"{d['id']} skipped ({d.get('skip_reason')}) label={d.get('label')}")
            return 0
        rows = d["info"]
        for item in rows:
            note = f"  note={item['note']}" if item.get("note") else ""
            link = f"  link={item['ext_link']}" if item.get("ext_link") else ""
            print(f"{item['name']:30} {item['value']}{note}{link}")
    return 0


def cmd_show(args: argparse.Namespace) -> int:
    try:
        d = get_dhatu(args.dhatu_id, db_path=args.db)
    except Exception as e:
        print(str(e), file=sys.stderr)
        return 1
    if args.json:
        _print_json(d)
    else:
        _print_json(d)
    return 0


def cmd_list(args: argparse.Namespace) -> int:
    rows = list_dhatus(gana=args.gana, limit=args.limit, offset=args.offset, include_skipped=not args.no_skipped, db_path=args.db)
    if args.json:
        _print_json(rows)
    else:
        # enrich with short info: arTaH + English?
        # For speed, just table
        _print_table(rows, headers=["id", "gana", "skipped", "label"])
        if not args.limit or len(rows) == args.limit:
            print(f"\n({len(rows)} rows shown; use --limit/--offset to page, --json for machine output)")
    return 0


def cmd_search(args: argparse.Namespace) -> int:
    # New detailed search (exact or substring) across all forms
    # Use search_forms which returns prefix, pratyaya, dhatu, id, etc.
    # Keep --exact flag for exact equality, otherwise substring LIKE
    if args.detailed or args.exact or True:  # default to detailed
        rows = search_forms(args.text, exact=args.exact, gana=args.gana, limit=args.limit, db_path=args.db)
        if args.json:
            _print_json(rows)
        else:
            if not rows:
                print("(no matches)")
                return 0
            # pretty table: show most useful columns
            headers = ["dhatu_id","dhatu","artha","match_type","prefix","category","pratyaya","matched_field","matched_value"]
            # shorten artha/english for table
            display = []
            for r in rows:
                display.append({k: (str(v)[:20] if k in ("artha","english") else v) for k,v in r.items() if k in headers})
            _print_table(display, headers=headers)
            print(f"\n{len(rows)} hits (exact={args.exact}) — use --json for full dhatu/english fields")
        return 0
    # fallback legacy (not used)
    rows = search_dhatus(args.text, gana=args.gana, limit=args.limit, db_path=args.db)
    if args.json:
        _print_json(rows)
    else:
        _print_table(rows)
    return 0


def cmd_conj(args: argparse.Namespace) -> int:
    try:
        data = get_conjugations(args.dhatu_id, category=args.category, prefix=args.prefix or "", db_path=args.db)
    except FileNotFoundError as e:
        print(str(e), file=sys.stderr); return 1
    if args.json:
        _print_json(data)
        return 0
    if not data:
        print("(no conjugations)")
        return 0
    for cat, forms in data.items():
        print(f"\n[{cat}] (prefix='{args.prefix or ''}')")
        for ftype, vals in forms.items():
            print(f"  {ftype:15} {', '.join(vals[:8])}{' ...' if len(vals)>8 else ''}  ({len(vals)} forms)")
    return 0


def cmd_part(args: argparse.Namespace) -> int:
    try:
        data = get_participles(args.dhatu_id, category=args.category, prefix=args.prefix or "", db_path=args.db)
    except FileNotFoundError as e:
        print(str(e), file=sys.stderr); return 1
    if args.json:
        _print_json(data)
        return 0
    if not data:
        print("(no participles)")
        return 0
    for cat, variant_map in data.items():
        print(f"\n[{cat}]")
        for variant, rows in variant_map.items():
            print(f"  {variant:15} ({len(rows)} rows)")
            for r in rows[:3]:
                print(f"    base={r['base']:15} m={r['m']:15} f={r['f']:15} n={r['n']}")
            if len(rows) > 3:
                print(f"    ... {len(rows)-3} more")
    return 0


def cmd_upasarga(args: argparse.Namespace) -> int:
    try:
        if args.chandrika:
            data = get_chandrika(args.dhatu_id, db_path=args.db)
            _print_json(data) if args.json else _print_json(data)
        else:
            data = get_upasarga_entries(args.dhatu_id, db_path=args.db)
            if args.json:
                _print_json(data)
            else:
                print(f"dhatu: {data['dhatu']}")
                for e in data["entries"]:
                    print(f"  {e['prefix']:15} {e['artha_hindi']}")
                if args.with_forms:
                    forms = get_upasarga_forms(args.dhatu_id, db_path=args.db)
                    print("\n--- upasarga forms ---")
                    _print_json(forms)
    except FileNotFoundError as e:
        print(str(e), file=sys.stderr); return 1
    return 0


def cmd_prayoga(args: argparse.Namespace) -> int:
    try:
        data = get_prayoga(args.dhatu_id, db_path=args.db)
    except FileNotFoundError as e:
        print(str(e), file=sys.stderr); return 1
    if args.json:
        _print_json(data)
    else:
        for row in data[:20]:
            print(f"{row['form']:15} {row['lakaar']:30} {row['purusha']:15} {row['vachana']}")
            for ex in row["examples"][:2]:
                print(f"    - {ex['book']} {ex['reference']}: {ex['text'][:60]}")
        if len(data) > 20:
            print(f"... {len(data)-20} more (use --json for full)")
    return 0


def cmd_query(args: argparse.Namespace) -> int:
    try:
        rows = query(args.sql, db_path=args.db)
    except Exception as e:
        print(f"query error: {e}", file=sys.stderr); return 1
    if args.json:
        _print_json(rows)
    else:
        _print_table(rows)
        print(f"\n{len(rows)} rows")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="skt-morph",
        description="Query Sanskrit dhatu morphology DB (auto-downloads on first use)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""
        examples:
          skt-morph download
          skt-morph info 01.0001
          skt-morph show 01.0001 --json > dhatu.json
          skt-morph list --gana 01 --limit 20
          skt-morph conjugations 01.0001 --category ting
          skt-morph participles 01.0001 --category krut
          skt-morph upasarga 01.0001
          skt-morph prayoga 01.0001
          skt-morph search Bavati --exact        # exact match
          skt-morph search BU --gana 01            # substring
          skt-morph search AdAra --exact --json    # detailed JSON with prefix/pratyaya/dhatu/id
          skt-morph query "SELECT id, gana FROM dhatus WHERE gana='01' LIMIT 5"

        DB location: ~/.local/share/skt_morph_data/skt_morph.db
        Override with --db or $SKT_MORPH_DATA_DIR / $SKT_MORPH_DB_URL
        """),
    )
    p.add_argument("--db", help="path to skt_morph.db (default auto location)", default=None)
    p.add_argument("--version", action="version", version="skt-morph-data 0.1.0")

    sub = p.add_subparsers(dest="cmd", required=True)

    # download
    d = sub.add_parser("download", help="download/cache the SQLite DB")
    d.add_argument("--force", action="store_true", help="re-download even if exists")
    d.add_argument("--url", help="custom URL to download from")
    d.add_argument("--output", help="output path (default user cache)")
    d.set_defaults(func=cmd_download)

    # info
    s = sub.add_parser("info", help="show dhatu info fields")
    s.add_argument("dhatu_id", help="e.g. 01.0001")
    s.add_argument("--json", action="store_true", help="output JSON")
    s.set_defaults(func=cmd_info)

    # show (full dhatu)
    sh = sub.add_parser("show", help="show full dhatu JSON (all tables)")
    sh.add_argument("dhatu_id")
    sh.add_argument("--json", action="store_true", default=True, help="output JSON (default)")
    sh.set_defaults(func=cmd_show)

    # list
    ls = sub.add_parser("list", help="list dhatus")
    ls.add_argument("--gana", help="filter by gana, e.g. 01 or 1")
    ls.add_argument("--limit", type=int, default=50)
    ls.add_argument("--offset", type=int, default=0)
    ls.add_argument("--no-skipped", action="store_true", help="hide ganasutra/skipped")
    ls.add_argument("--json", action="store_true")
    ls.set_defaults(func=cmd_list)

    # search (detailed, exact or substring)
    se = sub.add_parser("search", aliases=["find"], help="search forms (conjugation/participle) — returns prefix, pratyaya, dhatu, id")
    se.add_argument("text", help="search text (SLP1), e.g. Bavati, BUta, AdAra")
    se.add_argument("--gana", help="filter gana")
    se.add_argument("--limit", type=int, default=20)
    se.add_argument("--exact", action="store_true", help="exact equality (=) instead of substring LIKE (%%text%%)")
    se.add_argument("--detailed", action="store_true", help="(default) show detailed hits")
    se.add_argument("--json", action="store_true")
    se.set_defaults(func=cmd_search)

    # conjugations
    c = sub.add_parser("conjugations", aliases=["conj", "ting"], help="conjugation forms")
    c.add_argument("dhatu_id")
    c.add_argument("--category", help="e.g. ting, yak, san ...")
    c.add_argument("--prefix", help="upasarga prefix e.g. pra, sam", default="")
    c.add_argument("--json", action="store_true")
    c.set_defaults(func=cmd_conj)

    # participles
    pt = sub.add_parser("participles", aliases=["krt", "krut"], help="krdanta/participle forms")
    pt.add_argument("dhatu_id")
    pt.add_argument("--category", help="e.g. krut, san_krut ...")
    pt.add_argument("--prefix", default="")
    pt.add_argument("--json", action="store_true")
    pt.set_defaults(func=cmd_part)

    # upasarga
    up = sub.add_parser("upasarga", help="upasarga entries / chandrika")
    up.add_argument("dhatu_id")
    up.add_argument("--chandrika", action="store_true", help="show chandrika examples instead")
    up.add_argument("--with-forms", action="store_true", help="also dump upasarga_forms")
    up.add_argument("--json", action="store_true")
    up.set_defaults(func=cmd_upasarga)

    # prayoga
    pr = sub.add_parser("prayoga", help="show prayoga examples")
    pr.add_argument("dhatu_id")
    pr.add_argument("--json", action="store_true")
    pr.set_defaults(func=cmd_prayoga)

    # raw query
    q = sub.add_parser("query", help="run raw SQL SELECT")
    q.add_argument("sql", help='SQL, e.g. "SELECT * FROM dhatus LIMIT 5"')
    q.add_argument("--json", action="store_true")
    q.set_defaults(func=cmd_query)

    return p


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    # normalize --db
    if getattr(args, "db", None):
        args.db = Path(args.db)
    else:
        args.db = None
        # trigger auto-download unless command is download itself (which handles it)
        if args.cmd != "download":
            # ensure DB exists before any query
            try:
                ensure_db()
            except Exception as e:
                # allow list/query to fail gracefully with helpful message
                if args.cmd in ("list", "search", "query"):
                    print(f"DB not available: {e}\nRun `skt-morph download` first.", file=sys.stderr)
                    raise SystemExit(1)
    raise SystemExit(args.func(args))


if __name__ == "__main__":
    main()
