from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

from .db import connect

# ---------------------------------------------------------------------------
# Helpers to reconstruct original JSON shape
# ---------------------------------------------------------------------------

def _dict_rows(cur: sqlite3.Cursor) -> list[dict[str, Any]]:
    return [dict(r) for r in cur.fetchall()]


def get_info(dhatu_id: str, db_path: Path | str | None = None) -> list[dict[str, Any]]:
    con = connect(db_path)
    cur = con.execute("SELECT name, value, note, ext_link FROM dhatu_info WHERE dhatu_id=? ORDER BY id", (dhatu_id,))
    rows = []
    for r in cur.fetchall():
        item: dict[str, Any] = {"name": r["name"], "value": r["value"] or ""}
        if r["note"]:
            item["note"] = r["note"]
        if r["ext_link"]:
            item["ext_link"] = r["ext_link"]
        rows.append(item)
    return rows


def get_upasarga_entries(dhatu_id: str, db_path: Path | str | None = None) -> dict[str, Any]:
    con = connect(db_path)
    cur = con.execute("SELECT dhatu, prefix, artha_hindi FROM upasarga_entries WHERE dhatu_id=? ORDER BY id", (dhatu_id,))
    rows = cur.fetchall()
    dhatu_val = rows[0]["dhatu"] if rows else ""
    # fallback: read from dhatus table? but store per dhatu
    return {"dhatu": dhatu_val, "entries": [{"prefix": r["prefix"], "artha_hindi": r["artha_hindi"] or ""} for r in rows]}


def get_chandrika(dhatu_id: str, db_path: Path | str | None = None) -> list[dict[str, Any]]:
    con = connect(db_path)
    cur = con.execute("SELECT prefix, example FROM chandrika_examples WHERE dhatu_id=? ORDER BY id", (dhatu_id,))
    # group by prefix
    grouped: dict[str, list[str]] = {}
    order: list[str] = []
    for r in cur.fetchall():
        p = r["prefix"]
        if p not in grouped:
            grouped[p] = []
            order.append(p)
        grouped[p].append(r["example"])
    return [{"prefix": p, "examples": grouped[p]} for p in order]


def get_prayoga(dhatu_id: str, db_path: Path | str | None = None) -> list[dict[str, Any]]:
    con = connect(db_path)
    cur = con.execute("SELECT id, form, lakaar, purusha, vachana FROM prayoga WHERE dhatu_id=? ORDER BY id", (dhatu_id,))
    result = []
    for r in cur.fetchall():
        pid = r["id"]
        ex_cur = con.execute("SELECT book, reference, text, external FROM prayoga_examples WHERE prayoga_id=? ORDER BY id", (pid,))
        examples = [dict(e) for e in ex_cur.fetchall()]
        result.append({
            "form": r["form"],
            "lakaar": r["lakaar"],
            "purusha": r["purusha"],
            "vachana": r["vachana"],
            "examples": examples,
        })
    return result


def get_conjugations(dhatu_id: str, category: str | None = None, prefix: str = "", db_path: Path | str | None = None) -> dict[str, dict[str, list[str]]]:
    con = connect(db_path)
    q = "SELECT category, form_type, form_value FROM conjugation_forms WHERE dhatu_id=? AND prefix=?"
    params: list[Any] = [dhatu_id, prefix]
    if category:
        q += " AND category=?"
        params.append(category)
    q += " ORDER BY category, form_type, position"
    cur = con.execute(q, params)
    out: dict[str, dict[str, list[str]]] = {}
    for r in cur.fetchall():
        cat = r["category"]
        ft = r["form_type"]
        out.setdefault(cat, {}).setdefault(ft, []).append(r["form_value"])
    return out


def get_participles(dhatu_id: str, category: str | None = None, prefix: str = "", db_path: Path | str | None = None) -> dict[str, dict[str, list[dict[str, str]]]]:
    con = connect(db_path)
    q = "SELECT category, variant, base, m, f, n FROM participle_forms WHERE dhatu_id=? AND prefix=?"
    params: list[Any] = [dhatu_id, prefix]
    if category:
        q += " AND category=?"
        params.append(category)
    q += " ORDER BY category, variant, id"
    cur = con.execute(q, params)
    out: dict[str, dict[str, list[dict[str, str]]]] = {}
    for r in cur.fetchall():
        cat = r["category"]
        var = r["variant"]
        out.setdefault(cat, {}).setdefault(var, []).append({"base": r["base"] or "", "m": r["m"] or "", "f": r["f"] or "", "n": r["n"] or ""})
    return out


def get_upasarga_forms(dhatu_id: str, db_path: Path | str | None = None) -> dict[str, Any]:
    con = connect(db_path)
    # distinct prefixes that have forms
    cur = con.execute("SELECT DISTINCT prefix, artha_hindi FROM upasarga_prefix_meta WHERE dhatu_id=?", (dhatu_id,))
    result: dict[str, Any] = {}
    for r in cur.fetchall():
        p = r["prefix"]
        result[p] = {
            "prefix": p,
            "artha_hindi": r["artha_hindi"] or "",
            "conjugations": get_conjugations(dhatu_id, prefix=p, db_path=db_path),
            "participles": get_participles(dhatu_id, prefix=p, db_path=db_path),
        }
    # also include prefixes that may only have DB rows but not meta (fallback)
    if not result:
        cur2 = con.execute("SELECT DISTINCT prefix FROM conjugation_forms WHERE dhatu_id=? AND prefix!=''", (dhatu_id,))
        for r in cur2.fetchall():
            p = r["prefix"]
            if p not in result:
                result[p] = {
                    "prefix": p,
                    "artha_hindi": "",
                    "conjugations": get_conjugations(dhatu_id, prefix=p, db_path=db_path),
                    "participles": get_participles(dhatu_id, prefix=p, db_path=db_path),
                }
    return result


def get_dhatu(dhatu_id: str, db_path: Path | str | None = None) -> dict[str, Any]:
    con = connect(db_path)
    row = con.execute("SELECT id, gana, skipped, skip_reason, label FROM dhatus WHERE id=?", (dhatu_id,)).fetchone()
    if not row:
        raise KeyError(f"Dhatu {dhatu_id} not found")
    if row["skipped"]:
        return {
            "id": row["id"],
            "skipped": True,
            "skip_reason": row["skip_reason"] or "",
            "label": row["label"] or "",
            "info": [],
            "conjugations": {},
            "participles": {},
            "upasarga": {"dhatu": "", "entries": []},
            "chandrika": [],
            "prayoga": [],
            "upasarga_forms": {},
        }
    return {
        "id": row["id"],
        "info": get_info(dhatu_id, db_path),
        "conjugations": get_conjugations(dhatu_id, prefix="", db_path=db_path),
        "participles": get_participles(dhatu_id, prefix="", db_path=db_path),
        "upasarga": get_upasarga_entries(dhatu_id, db_path),
        "chandrika": get_chandrika(dhatu_id, db_path),
        "prayoga": get_prayoga(dhatu_id, db_path),
        "upasarga_forms": get_upasarga_forms(dhatu_id, db_path),
    }


def list_dhatus(
    gana: str | None = None,
    limit: int | None = None,
    offset: int = 0,
    include_skipped: bool = True,
    db_path: Path | str | None = None,
) -> list[dict[str, Any]]:
    con = connect(db_path)
    q = "SELECT id, gana, skipped, skip_reason, label FROM dhatus"
    clauses: list[str] = []
    params: list[Any] = []
    if gana:
        clauses.append("gana=?")
        params.append(gana.zfill(2) if gana.isdigit() else gana)
    if not include_skipped:
        clauses.append("skipped=0")
    if clauses:
        q += " WHERE " + " AND ".join(clauses)
    q += " ORDER BY id"
    if limit is not None:
        q += " LIMIT ? OFFSET ?"
        params.extend([limit, offset])
    elif offset:
        q += " LIMIT -1 OFFSET ?"
        params.append(offset)
    cur = con.execute(q, params)
    return _dict_rows(cur)


def search_dhatus(
    text: str,
    field: str = "all",
    gana: str | None = None,
    limit: int = 20,
    db_path: Path | str | None = None,
) -> list[dict[str, Any]]:
    """Simple LIKE search over info values, dhatu forms, etc."""
    con = connect(db_path)
    like = f"%{text}%"
    # search in info values, conjugation forms, and dhatu id
    gana_clause = " AND d.gana=?" if gana else ""
    params: list[Any] = []
    # Use UNION to dedup
    sql = f"""
    SELECT DISTINCT d.id, d.gana, d.skipped, d.label FROM dhatus d
    LEFT JOIN dhatu_info i ON i.dhatu_id=d.id
    LEFT JOIN conjugation_forms c ON c.dhatu_id=d.id
    WHERE (d.id LIKE ? OR i.value LIKE ? OR c.form_value LIKE ?)
    {gana_clause}
    ORDER BY d.id LIMIT ?
    """
    params = [like, like, like]
    if gana:
        params.append(gana.zfill(2) if gana.isdigit() else gana)
    params.append(limit)
    cur = con.execute(sql, params)
    return _dict_rows(cur)


def query(sql: str, params: tuple | dict | None = None, db_path: Path | str | None = None) -> list[dict[str, Any]]:
    """Run arbitrary SELECT and return rows as dicts."""
    con = connect(db_path)
    cur = con.execute(sql, params or ())
    cols = [d[0] for d in cur.description] if cur.description else []
    return [dict(zip(cols, row)) for row in cur.fetchall()]
