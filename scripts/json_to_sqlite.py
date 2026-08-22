#!/usr/bin/env python3
"""
Convert ashtadhyayi JSON dump (data/<gana>/<id>.json) to SQLite DB.

Schema
------
- dhatus(id PK, gana, skipped, skip_reason, label)
- dhatu_info(id PK, dhatu_id FK, name, value, note, ext_link)
- upasarga_entries(id PK, dhatu_id, dhatu, prefix, artha_hindi)
- upasarga_prefix_meta(dhatu_id, prefix, artha_hindi)  -- for upasarga_forms meta
- chandrika_examples(id PK, dhatu_id, prefix, example)
- conjugation_forms(id PK, dhatu_id, prefix, category, form_type, form_value, position)
- participle_forms(id PK, dhatu_id, prefix, category, base, m, f, n)
- prayoga(id PK, dhatu_id, form, lakaar, purusha, vachana)
- prayoga_examples(id PK, prayoga_id FK, book, reference, text, external)

Usage
-----
  python scripts/json_to_sqlite.py --data-dir data --output data/skt_morph.db
  python scripts/json_to_sqlite.py --data-dir ./data --output ~/.local/share/skt_morph_data/skt_morph.db --force
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path

DDL = """
PRAGMA journal_mode=WAL;
PRAGMA synchronous=NORMAL;

DROP TABLE IF EXISTS prayoga_examples;
DROP TABLE IF EXISTS prayoga;
DROP TABLE IF EXISTS participle_forms;
DROP TABLE IF EXISTS conjugation_forms;
DROP TABLE IF EXISTS chandrika_examples;
DROP TABLE IF EXISTS upasarga_prefix_meta;
DROP TABLE IF EXISTS upasarga_entries;
DROP TABLE IF EXISTS dhatu_info;
DROP TABLE IF EXISTS dhatus;

CREATE TABLE dhatus (
    id TEXT PRIMARY KEY,
    gana TEXT NOT NULL,
    skipped INTEGER NOT NULL DEFAULT 0,
    skip_reason TEXT,
    label TEXT
);

CREATE TABLE dhatu_info (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    dhatu_id TEXT NOT NULL REFERENCES dhatus(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    value TEXT,
    note TEXT,
    ext_link TEXT
);

CREATE TABLE upasarga_entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    dhatu_id TEXT NOT NULL REFERENCES dhatus(id) ON DELETE CASCADE,
    dhatu TEXT,
    prefix TEXT NOT NULL,
    artha_hindi TEXT
);

CREATE TABLE upasarga_prefix_meta (
    dhatu_id TEXT NOT NULL REFERENCES dhatus(id) ON DELETE CASCADE,
    prefix TEXT NOT NULL,
    artha_hindi TEXT,
    PRIMARY KEY (dhatu_id, prefix)
);

CREATE TABLE chandrika_examples (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    dhatu_id TEXT NOT NULL REFERENCES dhatus(id) ON DELETE CASCADE,
    prefix TEXT NOT NULL,
    example TEXT
);

CREATE TABLE conjugation_forms (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    dhatu_id TEXT NOT NULL REFERENCES dhatus(id) ON DELETE CASCADE,
    prefix TEXT NOT NULL DEFAULT '',
    category TEXT NOT NULL,
    form_type TEXT NOT NULL,
    form_value TEXT NOT NULL,
    position INTEGER NOT NULL
);

CREATE TABLE participle_forms (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    dhatu_id TEXT NOT NULL REFERENCES dhatus(id) ON DELETE CASCADE,
    prefix TEXT NOT NULL DEFAULT '',
    category TEXT NOT NULL,
    variant TEXT NOT NULL,
    base TEXT,
    m TEXT,
    f TEXT,
    n TEXT
);

CREATE TABLE prayoga (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    dhatu_id TEXT NOT NULL REFERENCES dhatus(id) ON DELETE CASCADE,
    form TEXT,
    lakaar TEXT,
    purusha TEXT,
    vachana TEXT
);

CREATE TABLE prayoga_examples (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    prayoga_id INTEGER NOT NULL REFERENCES prayoga(id) ON DELETE CASCADE,
    book TEXT,
    reference TEXT,
    text TEXT,
    external TEXT
);

CREATE INDEX idx_dhatus_gana ON dhatus(gana);
CREATE INDEX idx_info_dhatu ON dhatu_info(dhatu_id);
CREATE INDEX idx_conj_dhatu ON conjugation_forms(dhatu_id);
CREATE INDEX idx_conj_prefix ON conjugation_forms(prefix);
CREATE INDEX idx_conj_cat ON conjugation_forms(category);
CREATE INDEX idx_part_dhatu ON participle_forms(dhatu_id);
CREATE INDEX idx_prayoga_dhatu ON prayoga(dhatu_id);
CREATE INDEX idx_chandrika_dhatu ON chandrika_examples(dhatu_id);
"""

def iter_json_files(data_dir: Path):
    for p in sorted(data_dir.rglob("*.json")):
        # skip non-dhatu files like skt_morph.db etc
        if p.name.startswith("."):
            continue
        yield p

def insert_dhatu(cur: sqlite3.Cursor, obj: dict) -> None:
    dhatu_id: str = obj.get("id") or obj.get("baseindex") or ""
    if not dhatu_id:
        raise ValueError(f"Missing id in {obj}")
    gana = dhatu_id.split(".")[0] if "." in dhatu_id else ""
    skipped = 1 if obj.get("skipped") else 0
    skip_reason = obj.get("skip_reason")
    label = obj.get("label")
    cur.execute("INSERT OR REPLACE INTO dhatus(id,gana,skipped,skip_reason,label) VALUES (?,?,?,?,?)",
                (dhatu_id, gana, skipped, skip_reason, label))
    if skipped:
        return

    # info
    for row in obj.get("info", []):
        cur.execute("INSERT INTO dhatu_info(dhatu_id,name,value,note,ext_link) VALUES (?,?,?,?,?)",
                    (dhatu_id, row.get("name"), row.get("value"), row.get("note"), row.get("ext_link")))

    # upasarga
    up = obj.get("upasarga") or {}
    dhatu_val = up.get("dhatu", "")
    for e in up.get("entries", []):
        cur.execute("INSERT INTO upasarga_entries(dhatu_id,dhatu,prefix,artha_hindi) VALUES (?,?,?,?)",
                    (dhatu_id, dhatu_val, e.get("prefix"), e.get("artha_hindi")))
        # also meta for forms
        cur.execute("INSERT OR IGNORE INTO upasarga_prefix_meta(dhatu_id,prefix,artha_hindi) VALUES (?,?,?)",
                    (dhatu_id, e.get("prefix"), e.get("artha_hindi")))

    # chandrika
    for item in obj.get("chandrika", []):
        prefix = item.get("prefix", "")
        for ex in item.get("examples", []):
            cur.execute("INSERT INTO chandrika_examples(dhatu_id,prefix,example) VALUES (?,?,?)",
                        (dhatu_id, prefix, ex))

    # upasarga_forms meta (prefixes without entry duplication)
    for prefix, meta in (obj.get("upasarga_forms") or {}).items():
        # ensure meta row
        cur.execute("INSERT OR IGNORE INTO upasarga_prefix_meta(dhatu_id,prefix,artha_hindi) VALUES (?,?,?)",
                    (dhatu_id, prefix, meta.get("artha_hindi")))

    # conjugations (base + upasarga)
    def insert_conj(prefix: str, conj: dict):
        for cat, form_map in (conj or {}).items():
            for ftype, vals in form_map.items():
                for pos, fv in enumerate(vals):
                    cur.execute("INSERT INTO conjugation_forms(dhatu_id,prefix,category,form_type,form_value,position) VALUES (?,?,?,?,?,?)",
                                (dhatu_id, prefix, cat, ftype, fv, pos))

    insert_conj("", obj.get("conjugations", {}))
    for prefix, meta in (obj.get("upasarga_forms") or {}).items():
        insert_conj(prefix, meta.get("conjugations", {}))

    # participles: part = {category(krut): {variant(kta): [ {base,m,f,n}, ... ], ... }, ... }
    def insert_part(prefix: str, part: dict):
        for cat, variant_map in (part or {}).items():
            if not isinstance(variant_map, dict):
                continue
            for variant, rows in variant_map.items():
                if not isinstance(rows, list):
                    continue
                for r in rows:
                    if not isinstance(r, dict):
                        continue
                    cur.execute("INSERT INTO participle_forms(dhatu_id,prefix,category,variant,base,m,f,n) VALUES (?,?,?,?,?,?,?,?)",
                                (dhatu_id, prefix, cat, variant, r.get("base"), r.get("m"), r.get("f"), r.get("n")))

    insert_part("", obj.get("participles", {}))
    for prefix, meta in (obj.get("upasarga_forms") or {}).items():
        insert_part(prefix, meta.get("participles", {}))

    # prayoga
    for row in obj.get("prayoga", []):
        cur.execute("INSERT INTO prayoga(dhatu_id,form,lakaar,purusha,vachana) VALUES (?,?,?,?,?)",
                    (dhatu_id, row.get("form"), row.get("lakaar"), row.get("purusha"), row.get("vachana")))
        pid = cur.lastrowid
        for ex in row.get("examples", []):
            cur.execute("INSERT INTO prayoga_examples(prayoga_id,book,reference,text,external) VALUES (?,?,?,?,?)",
                        (pid, ex.get("book"), ex.get("reference"), ex.get("text"), ex.get("external")))


def build_db(data_dir: Path, output: Path, force: bool = False) -> Path:
    if output.exists() and not force:
        print(f"DB already exists at {output} (use --force to overwrite)", file=sys.stderr)
        return output
    output.parent.mkdir(parents=True, exist_ok=True)
    tmp = output.with_suffix(".tmp")
    if tmp.exists():
        tmp.unlink()

    con = sqlite3.connect(str(tmp))
    con.executescript(DDL)

    files = list(iter_json_files(data_dir))
    if not files:
        raise RuntimeError(f"No JSON files found under {data_dir}")

    print(f"Found {len(files)} JSON files under {data_dir}")
    cur = con.cursor()
    ok = 0
    skipped = 0
    for i, p in enumerate(files, 1):
        try:
            obj = json.loads(p.read_text(encoding="utf-8"))
            insert_dhatu(cur, obj)
            ok += 1
            if obj.get("skipped"):
                skipped += 1
        except Exception as e:
            print(f"[warn] {p}: {e}", file=sys.stderr)
        if i % 500 == 0:
            print(f"  ... {i}/{len(files)}")
    con.commit()

    # vacuum + stats
    cur.execute("SELECT count(*) FROM dhatus")
    n_dhatus = cur.fetchone()[0]
    cur.execute("SELECT count(*) FROM conjugation_forms")
    n_conj = cur.fetchone()[0]
    cur.execute("SELECT count(*) FROM participle_forms")
    n_part = cur.fetchone()[0]
    con.commit()
    con.close()

    tmp.replace(output)
    print(f"Done: {n_dhatus} dhatus ({skipped} skipped), {n_conj} conjugation forms, {n_part} participles")
    print(f"DB written to {output} ({output.stat().st_size//1024} KB)")
    return output


def main():
    ap = argparse.ArgumentParser(description="Convert JSON data dir to SQLite DB")
    ap.add_argument("--data-dir", type=Path, default=Path("data"), help="root data dir with <gana>/*.json")
    ap.add_argument("--output", "-o", type=Path, default=Path("data/skt_morph.db"), help="output sqlite path")
    ap.add_argument("--force", action="store_true", help="overwrite existing DB")
    args = ap.parse_args()
    build_db(args.data_dir, args.output, force=args.force)


if __name__ == "__main__":
    main()
