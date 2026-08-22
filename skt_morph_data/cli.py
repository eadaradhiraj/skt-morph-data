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
    get_ids_by_dhatu,
    get_info,
    get_participles,
    get_prayoga,
    get_upasarga_entries,
    get_upasarga_forms,
    list_dhatus,
    query,
    resolve_dhatu_input,
    search_dhatus,
    search_forms,
)
from .subanta import (
    analyze,
    analyze_form,
    decline,
    list_numerals,
    list_paradigms,
    list_pronouns,
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


def _resolve_ids(inp: str, db_path) -> list[str]:
    ids = resolve_dhatu_input(inp, db_path=db_path)
    if not ids:
        # also try as-is (maybe id with typo)
        return []
    return ids

def _require_one_id(inp: str, db_path) -> tuple[str | None, list[str]]:
    ids = _resolve_ids(inp, db_path)
    if not ids:
        return None, []
    return ids[0], ids

def cmd_info(args: argparse.Namespace) -> int:
    ids = _resolve_ids(args.dhatu, db_path=args.db)
    if not ids:
        print(f"No dhatu found for '{args.dhatu}' (try id 01.0001 or dhatu BU)", file=sys.stderr)
        return 1
    # if multiple (same dhatu string occurs in multiple ganas), show all
    for dhatu_id in ids:
        try:
            d = get_dhatu(dhatu_id, db_path=args.db)
        except (KeyError, FileNotFoundError) as e:
            print(str(e), file=sys.stderr)
            continue
        if len(ids) > 1:
            print(f"=== {dhatu_id} ({d.get('info',[{}])[2].get('value','') if len(d.get('info',[]))>2 else ''}) ===")
        if args.json:
            _print_json(d["info"] if "info" in d else d)
        else:
            if d.get("skipped"):
                print(f"{d['id']} skipped ({d.get('skip_reason')}) label={d.get('label')}")
                continue
            rows = d["info"]
            for item in rows:
                note = f"  note={item['note']}" if item.get("note") else ""
                link = f"  link={item['ext_link']}" if item.get("ext_link") else ""
                print(f"{item['name']:30} {item['value']}{note}{link}")
    return 0


def cmd_show(args: argparse.Namespace) -> int:
    ids = _resolve_ids(args.dhatu, db_path=args.db)
    if not ids:
        print(f"No dhatu found for '{args.dhatu}'", file=sys.stderr)
        return 1
    # if multiple, return list
    if len(ids) == 1:
        try:
            d = get_dhatu(ids[0], db_path=args.db)
        except Exception as e:
            print(str(e), file=sys.stderr)
            return 1
        _print_json(d)
        return 0
    # multiple
    out = []
    for did in ids:
        try:
            out.append(get_dhatu(did, db_path=args.db))
        except Exception as e:
            print(f"{did}: {e}", file=sys.stderr)
    _print_json(out)
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
    # Unified search: verb conjugations/participles (DB) + nominal declensions (generated)
    # If exact=True, do exact match; else substring LIKE for verbs and loose contains for nominal
    verb_rows = []
    try:
        verb_rows = search_forms(args.text, exact=args.exact, gana=args.gana, limit=args.limit, db_path=args.db)
    except Exception as e:
        if args.json:
            pass
        else:
            print(f"(verb search skipped: {e})", file=sys.stderr)
        verb_rows = []
    # nominal declension analysis (exact or substring)
    nominal_rows = []
    try:
        if args.exact:
            hits = analyze_form(args.text, limit=args.limit, loose=True)
            for h in hits:
                nominal_rows.append({
                    "dhatu_id": "",
                    "dhatu": h.get("lemma",""),
                    "artha": h.get("paradigm_desc",""),
                    "match_type": h.get("match_type","noun_declension"),
                    "prefix": "",
                    "category": h.get("vibhakti","") + "/" + h.get("vacana",""),
                    "pratyaya": h.get("paradigm",""),
                    "matched_field": f"{h.get('vibhakti','')}:{h.get('vacana','')}",
                    "matched_value": h.get("matched_form", args.text),
                    "gender": h.get("gender",""),
                    "lemma": h.get("lemma",""),
                    "vibhakti": h.get("vibhakti",""),
                    "vacana": h.get("vacana",""),
                    "suffix": h.get("suffix",""),
                })
        else:
            # substring for nominal: check if query is substring of any generated declension form (loose, limited)
            # We do quick check: for common paradigms generate sample lemmas? Too expensive to generate all.
            # Instead do: if query appears inside any pronoun/numeral form or inside suffix match, we already handled exact.
            # For substring nominal we can show declension analyses where query is substring of matched_form (already exact hits cover most)
            # We'll also try to see if query is substring of any declension form for a heuristic lemma set (rAma etc.)
            pass
    except Exception as e:
        print(f"nominal analysis error: {e}", file=sys.stderr)
    rows = verb_rows + nominal_rows
    # fallback legacy if no hits and not exact: try substring verb search via LIKE already done
    if args.json:
        # merge verb + nominal; keep verb rows as before plus nominal with extra fields
        _print_json(rows if rows else verb_rows or nominal_rows)
    else:
        if not rows:
            print("(no matches)")
            # still show hint about declension analyze
            if not verb_rows:
                print(f"Tip: try exact SLP1 form e.g. 'rAmeRa' for tRtiyA, or use 'skt-morph analyze {args.text}'")
            return 0
        headers = ["dhatu_id","dhatu","artha","match_type","prefix","category","pratyaya","matched_field","matched_value","gender","vibhakti","vacana","lemma"]
        # filter headers to those present
        present = [h for h in headers if any(h in r for r in rows)]
        display = []
        for r in rows:
            display.append({k: (str(v)[:24] if k in ("artha","english") else v) for k,v in r.items() if k in present})
        _print_table(display, headers=present)
        print(f"\n{len(verb_rows)} verb hits + {len(nominal_rows)} declension hits (exact={args.exact}) — use --json for full fields")
        if nominal_rows:
            print("Declension hit example: \"rAmeRa\" → lemma rAma (a_m) tRtiyA ekavacana, suffix eRa")
    return 0

def cmd_analyze(args: argparse.Namespace) -> int:
    word = args.word
    try:
        hits = analyze(word, limit=args.limit, loose=not args.strict, db_path=args.db, include_verb=not args.nominal_only)
        # Filter to nominal only if requested? analyze includes both; if nominal_only filter out verb
        if args.nominal_only:
            hits = [h for h in hits if h.get("match_type","").startswith("noun") or h.get("type") in ("noun","pronoun","numeral")]
    except Exception as e:
        print(f"analyze error: {e}", file=sys.stderr)
        return 1
    if args.json:
        _print_json(hits)
        return 0
    if not hits:
        print("(no analysis found)")
        print(f"Tip: word \"{word}\" not found as verb form nor as nominal declension. Try SLP1 (rAmeRa not rampena) or use --strict/--nominal-only")
        return 0
    # pretty per hit
    rows = []
    for h in hits:
        if h.get("match_type") in ("conjugation", "participle") or h.get("type") == "conjugation":
            rows.append({
                "type": h.get("match_type", h.get("type","conjugation")),
                "lemma": h.get("dhatu","") or h.get("lemma",""),
                "dhatu_id": h.get("dhatu_id",""),
                "category": h.get("category",""),
                "pratyaya": h.get("pratyaya", h.get("form_type","")),
                "form": h.get("matched_value", h.get("form_value","")),
                "prefix": h.get("prefix",""),
            })
        else:
            rows.append({
                "type": h.get("match_type", h.get("type")),
                "lemma": h.get("lemma",""),
                "paradigm": h.get("paradigm",""),
                "gender": h.get("gender",""),
                "vibhakti": h.get("vibhakti",""),
                "vacana": h.get("vacana",""),
                "suffix": h.get("suffix",""),
                "form": h.get("matched_form", h.get("word","")),
            })
    _print_table(rows)
    print(f"\n{len(hits)} analyses for \"{word}\" (loose={not args.strict})")
    # Show explanation for first noun hit
    for h in hits:
        if h.get("vibhakti"):
            print(f"→ \"{h.get('word')}\" = {h.get('vibhakti')} {h.get('vacana')} of \"{h.get('lemma')}\" [{h.get('paradigm')}] suffix \"{h.get('suffix')}\"")
            break
    return 0


def cmd_conj(args: argparse.Namespace) -> int:
    ids = _resolve_ids(args.dhatu, db_path=args.db)
    if not ids:
        print(f"No dhatu found for '{args.dhatu}' (try BU or 01.0001)", file=sys.stderr)
        return 1
    for did in ids:
        if len(ids) > 1:
            print(f"\n=== {did} ===")
        try:
            data = get_conjugations(did, category=args.category, prefix=args.prefix or "", db_path=args.db)
        except FileNotFoundError as e:
            print(str(e), file=sys.stderr); continue
        if args.json:
            # if multiple, wrap with id
            if len(ids) > 1:
                _print_json({did: data})
            else:
                _print_json(data)
            continue
        if not data:
            print(f"{did}: (no conjugations)")
            continue
        for cat, forms in data.items():
            print(f"\n[{cat}] {did} (prefix='{args.prefix or ''}')")
            for ftype, vals in forms.items():
                print(f"  {ftype:15} {', '.join(vals[:8])}{' ...' if len(vals)>8 else ''}  ({len(vals)} forms)")
    return 0


def cmd_part(args: argparse.Namespace) -> int:
    ids = _resolve_ids(args.dhatu, db_path=args.db)
    if not ids:
        print(f"No dhatu found for '{args.dhatu}'", file=sys.stderr)
        return 1
    for did in ids:
        if len(ids) > 1:
            print(f"\n=== {did} ===")
        try:
            data = get_participles(did, category=args.category, prefix=args.prefix or "", db_path=args.db)
        except FileNotFoundError as e:
            print(str(e), file=sys.stderr); continue
        if args.json:
            if len(ids) > 1:
                _print_json({did: data})
            else:
                _print_json(data)
            continue
        if not data:
            print(f"{did}: (no participles)")
            continue
        for cat, variant_map in data.items():
            print(f"\n[{cat}] {did}")
            for variant, rows in variant_map.items():
                print(f"  {variant:15} ({len(rows)} rows)")
                for r in rows[:3]:
                    print(f"    base={r['base']:15} m={r['m']:15} f={r['f']:15} n={r['n']}")
                if len(rows) > 3:
                    print(f"    ... {len(rows)-3} more")
    return 0


def cmd_upasarga(args: argparse.Namespace) -> int:
    ids = _resolve_ids(args.dhatu, db_path=args.db)
    if not ids:
        print(f"No dhatu found for '{args.dhatu}'", file=sys.stderr)
        return 1
    for did in ids:
        if len(ids) > 1:
            print(f"=== {did} ===")
        try:
            if args.chandrika:
                data = get_chandrika(did, db_path=args.db)
                _print_json(data)
            else:
                data = get_upasarga_entries(did, db_path=args.db)
                if args.json:
                    _print_json({did: data} if len(ids)>1 else data)
                else:
                    print(f"dhatu: {data['dhatu']}")
                    for e in data["entries"]:
                        print(f"  {e['prefix']:15} {e['artha_hindi']}")
                    if args.with_forms:
                        forms = get_upasarga_forms(did, db_path=args.db)
                        print("\n--- upasarga forms ---")
                        _print_json(forms)
        except FileNotFoundError as e:
            print(str(e), file=sys.stderr); continue
    return 0


def cmd_prayoga(args: argparse.Namespace) -> int:
    ids = _resolve_ids(args.dhatu, db_path=args.db)
    if not ids:
        print(f"No dhatu found for '{args.dhatu}'", file=sys.stderr)
        return 1
    for did in ids:
        if len(ids)>1:
            print(f"=== {did} ===")
        try:
            data = get_prayoga(did, db_path=args.db)
        except FileNotFoundError as e:
            print(str(e), file=sys.stderr); continue
        if args.json:
            _print_json({did: data} if len(ids)>1 else data)
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


def cmd_decline(args: argparse.Namespace) -> int:
    word = args.word
    try:
        res = decline(word, gender=args.gender, paradigm=args.paradigm, category=args.category)
    except Exception as e:
        print(f"declension error: {e}", file=sys.stderr)
        return 1
    if args.json:
        _print_json(res)
        return 0
    # pretty
    from .subanta import to_table
    print(to_table(res))
    return 0


def cmd_paradigms(args: argparse.Namespace) -> int:
    rows = list_paradigms()
    if args.json:
        _print_json(rows)
    else:
        _print_table(rows, headers=["paradigm","ending","gender","desc"])
    return 0


def cmd_pronouns(args: argparse.Namespace) -> int:
    rows = [{"pronoun": p} for p in list_pronouns()]
    if args.json:
        _print_json(rows)
    else:
        _print_table(rows)
        print("\nUse: skt-morph decline <pronoun> --category pronoun [--gender m|f|n] --json")
    return 0


def cmd_numerals(args: argparse.Namespace) -> int:
    rows = [{"numeral": n} for n in list_numerals()]
    if args.json:
        _print_json(rows)
    else:
        _print_table(rows)
        print("\nUse: skt-morph decline <numeral> --category numeral [--gender m|f|n] --json")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="skt-morph",
        description="Query Sanskrit dhatu morphology DB (auto-downloads on first use)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""
        examples:
          skt-morph download
          skt-morph info 01.0001          # or: skt-morph info BU
          skt-morph show 01.0001 --json > dhatu.json
          skt-morph list --gana 01 --limit 20
          skt-morph conjugations 01.0001 --category ting
          skt-morph conjugations BU --category ting   # by dhatu string
          skt-morph participles BU --category krut
          skt-morph upasarga BU
          skt-morph prayoga BU
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
    s.add_argument("dhatu", help="dhatu id e.g. 01.0001 or dhatu string e.g. BU")
    s.add_argument("--json", action="store_true", help="output JSON")
    s.set_defaults(func=cmd_info)

    # show (full dhatu)
    sh = sub.add_parser("show", help="show full dhatu JSON (all tables)")
    sh.add_argument("dhatu", help="dhatu id or dhatu string")
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

    # conjugations (accept id or dhatu string)
    c = sub.add_parser("conjugations", aliases=["conj", "ting"], help="conjugation forms (id or dhatu string)")
    c.add_argument("dhatu", help="dhatu id e.g. 01.0001 or dhatu string e.g. BU")
    c.add_argument("--category", help="e.g. ting, yak, san ...")
    c.add_argument("--prefix", help="upasarga prefix e.g. pra, sam", default="")
    c.add_argument("--json", action="store_true")
    c.set_defaults(func=cmd_conj)

    # participles
    pt = sub.add_parser("participles", aliases=["krt", "krut"], help="krdanta/participle forms")
    pt.add_argument("dhatu", help="dhatu id or dhatu string e.g. BU")
    pt.add_argument("--category", help="e.g. krut, san_krut ...")
    pt.add_argument("--prefix", default="")
    pt.add_argument("--json", action="store_true")
    pt.set_defaults(func=cmd_part)

    # upasarga
    up = sub.add_parser("upasarga", help="upasarga entries / chandrika")
    up.add_argument("dhatu", help="dhatu id or dhatu string")
    up.add_argument("--chandrika", action="store_true", help="show chandrika examples instead")
    up.add_argument("--with-forms", action="store_true", help="also dump upasarga_forms")
    up.add_argument("--json", action="store_true")
    up.set_defaults(func=cmd_upasarga)

    # prayoga
    pr = sub.add_parser("prayoga", help="show prayoga examples")
    pr.add_argument("dhatu", help="dhatu id or dhatu string")
    pr.add_argument("--json", action="store_true")
    pr.set_defaults(func=cmd_prayoga)

    # raw query
    q = sub.add_parser("query", help="run raw SQL SELECT")
    q.add_argument("sql", help='SQL, e.g. "SELECT * FROM dhatus LIMIT 5"')
    q.add_argument("--json", action="store_true")
    q.set_defaults(func=cmd_query)

    # declension – nouns / pronouns / numerals
    dc = sub.add_parser("decline", aliases=["declines", "declension", "subanta", "nominal"], help="decline noun/pronoun/numeral – complete 8×3 vibhakti table")
    dc.add_argument("word", help="word to decline (SLP1), e.g. rAma, nadI, hari, pitf, tad, eka")
    dc.add_argument("--gender", help="gender: m|f|n (optional – auto-detect if omitted)", default=None)
    dc.add_argument("--paradigm", help="force noun paradigm e.g. a_m, a_n, A_f, i_m, I_f, u_m, f_m, an_m, in_m, at_m, as_n", default=None)
    dc.add_argument("--category", help="force category: noun|pronoun|numeral", choices=["noun","pronoun","numeral"], default=None)
    dc.add_argument("--json", action="store_true", help="output JSON")
    dc.set_defaults(func=cmd_decline)

    # analyze – unified verb+nominal morphological analyzer
    an = sub.add_parser("analyze", aliases=["parse", "analyse"], help="analyze inflected form (verb or declension) → lemma, vibhakti/vacana or dhatu")
    an.add_argument("word", help="inflected form to analyze (SLP1), e.g. rAmeRa, TrampeRa, Bavati, rAmaH")
    an.add_argument("--limit", type=int, default=20, help="max analyses")
    an.add_argument("--strict", action="store_true", help="strict SLP1 (no R/n, S/s loose matching)")
    an.add_argument("--nominal-only", action="store_true", help="only nominal declension, skip verb DB")
    an.add_argument("--json", action="store_true", help="output JSON")
    an.set_defaults(func=cmd_analyze)

    # helper listings
    pm = sub.add_parser("paradigms", help="list available noun paradigms")
    pm.add_argument("--json", action="store_true")
    pm.set_defaults(func=cmd_paradigms)

    pn = sub.add_parser("pronouns", help="list available pronouns")
    pn.add_argument("--json", action="store_true")
    pn.set_defaults(func=cmd_pronouns)

    nm = sub.add_parser("numerals", help="list available numerals")
    nm.add_argument("--json", action="store_true")
    nm.set_defaults(func=cmd_numerals)

    return p


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    # normalize --db
    if getattr(args, "db", None):
        args.db = Path(args.db)
    else:
        args.db = None
        # trigger auto-download unless command is download/decline/paradigms/analyze which don't need DB (analyze can work nominal-only)
        if args.cmd not in ("download", "decline", "declines", "declension", "subanta", "nominal", "paradigms", "pronouns", "numerals", "analyze", "parse", "analyse"):
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
