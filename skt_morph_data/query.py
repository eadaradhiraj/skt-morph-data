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
    """Simple LIKE search over info values, dhatu forms, etc. (legacy, returns dhatu rows only)."""
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


def search_forms(
    text: str,
    exact: bool = False,
    gana: str | None = None,
    limit: int = 50,
    db_path: Path | str | None = None,
) -> list[dict[str, Any]]:
    """Exact or substring search across all forms.

    Returns detailed hits so caller knows *where* the form occurs:
      - dhatu_id, gana, dhatu (OpadeSikasvarUpam), artha, english
      - match_type: 'conjugation' | 'participle'
      - prefix (upasarga, '' if none)
      - category (ting/yak/... or krut/san_krut/...)
      - for conjugations: form_type (plat/plang/...), form_value
      - for participles: variant (kta/ktavatu/.../tavya etc), base/m/f/n and which field matched
    Example: search_forms("BUta", exact=True) -> hits for kta participle etc.
    """
    con = connect(db_path)
    # ensure indexes for speed (no-op if already exists)
    try:
        con.execute("CREATE INDEX IF NOT EXISTS idx_conj_form_value ON conjugation_forms(form_value)")
        con.execute("CREATE INDEX IF NOT EXISTS idx_part_base ON participle_forms(base)")
        con.execute("CREATE INDEX IF NOT EXISTS idx_part_m ON participle_forms(m)")
        con.execute("CREATE INDEX IF NOT EXISTS idx_part_f ON participle_forms(f)")
        con.execute("CREATE INDEX IF NOT EXISTS idx_part_n ON participle_forms(n)")
    except Exception:
        pass

    text = text.strip()
    if not text:
        return []
    gana_filter = gana.zfill(2) if gana and gana.isdigit() else gana

    # helper to fetch dhatu string / artha for display (correlated subquery in SELECT)
    # we include them directly in SQL to avoid N+1
    dhatu_expr = "(SELECT value FROM dhatu_info WHERE dhatu_id = d.id AND name='OpadeSikasvarUpam' LIMIT 1)"
    artha_expr = "(SELECT value FROM dhatu_info WHERE dhatu_id = d.id AND name='arTaH' LIMIT 1)"
    eng_expr = "(SELECT value FROM dhatu_info WHERE dhatu_id = d.id AND name='English Meaning' LIMIT 1)"

    hits: list[dict[str, Any]] = []

    # --- conjugations ---
    if exact:
        conj_sql = f"""
        SELECT c.dhatu_id as dhatu_id, d.gana as gana, c.prefix as prefix,
               c.category as category, c.form_type as form_type, c.form_value as form_value,
               c.position as position,
               {dhatu_expr} as dhatu, {artha_expr} as artha, {eng_expr} as english,
               'conjugation' as match_type
        FROM conjugation_forms c JOIN dhatus d ON d.id = c.dhatu_id
        WHERE c.form_value = ?
        """
        conj_params: list[Any] = [text]
    else:
        conj_sql = f"""
        SELECT c.dhatu_id as dhatu_id, d.gana as gana, c.prefix as prefix,
               c.category as category, c.form_type as form_type, c.form_value as form_value,
               c.position as position,
               {dhatu_expr} as dhatu, {artha_expr} as artha, {eng_expr} as english,
               'conjugation' as match_type
        FROM conjugation_forms c JOIN dhatus d ON d.id = c.dhatu_id
        WHERE c.form_value LIKE ?
        """
        conj_params = [f"%{text}%"]
    if gana_filter:
        conj_sql += " AND d.gana = ?"
        conj_params.append(gana_filter)
    conj_sql += " ORDER BY dhatu_id, prefix, category, form_type LIMIT ?"
    conj_params.append(limit)
    cur = con.execute(conj_sql, conj_params)
    for r in cur.fetchall():
        hits.append({
            "dhatu_id": r["dhatu_id"],
            "gana": r["gana"],
            "dhatu": r["dhatu"] or "",
            "artha": r["artha"] or "",
            "english": r["english"] or "",
            "match_type": "conjugation",
            "prefix": r["prefix"] or "",
            "category": r["category"],
            "pratyaya": r["form_type"],  # alias for uniformity
            "form_type": r["form_type"],
            "form_value": r["form_value"],
            "matched_field": "form_value",
            "matched_value": r["form_value"],
        })

    # --- participles ---
    # search across base/m/f/n
    if exact:
        part_where = "(p.base = ? OR p.m = ? OR p.f = ? OR p.n = ?)"
        part_params: list[Any] = [text, text, text, text]
    else:
        part_where = "(p.base LIKE ? OR p.m LIKE ? OR p.f LIKE ? OR p.n LIKE ?)"
        like = f"%{text}%"
        part_params = [like, like, like, like]
    part_sql = f"""
        SELECT p.dhatu_id as dhatu_id, d.gana as gana, p.prefix as prefix,
               p.category as category, p.variant as variant,
               p.base as base, p.m as m, p.f as f, p.n as n,
               {dhatu_expr} as dhatu, {artha_expr} as artha, {eng_expr} as english,
               'participle' as match_type
        FROM participle_forms p JOIN dhatus d ON d.id = p.dhatu_id
        WHERE {part_where}
    """
    if gana_filter:
        part_sql += " AND d.gana = ?"
        part_params.append(gana_filter)
    part_sql += " ORDER BY dhatu_id, prefix, category, variant LIMIT ?"
    part_params.append(limit)
    cur2 = con.execute(part_sql, part_params)
    for r in cur2.fetchall():
        # determine which field(s) exactly matched
        matched_fields = []
        if exact:
            if r["base"] == text:
                matched_fields.append("base")
            if r["m"] == text:
                matched_fields.append("m")
            if r["f"] == text:
                matched_fields.append("f")
            if r["n"] == text:
                matched_fields.append("n")
        else:
            if text in (r["base"] or ""):
                matched_fields.append("base")
            if text in (r["m"] or ""):
                matched_fields.append("m")
            if text in (r["f"] or ""):
                matched_fields.append("f")
            if text in (r["n"] or ""):
                matched_fields.append("n")
        # emit one hit per matched field so caller sees the field
        for mf in matched_fields or ["base"]:
            hits.append({
                "dhatu_id": r["dhatu_id"],
                "gana": r["gana"],
                "dhatu": r["dhatu"] or "",
                "artha": r["artha"] or "",
                "english": r["english"] or "",
                "match_type": "participle",
                "prefix": r["prefix"] or "",
                "category": r["category"],
                "pratyaya": r["variant"],
                "variant": r["variant"],
                "base": r["base"] or "",
                "m": r["m"] or "",
                "f": r["f"] or "",
                "n": r["n"] or "",
                "matched_field": mf,
                "matched_value": r[mf] if mf in ("base","m","f","n") else "",
            })

    # sort: exact matches first, then by dhatu_id
    # for substring search, prioritize exact equality if any
    def sort_key(h):
        exact_hit = 1 if h.get("matched_value") == text else 0
        # exact hits first
        return (-exact_hit, h["dhatu_id"], h["prefix"], h["category"], h.get("pratyaya",""))
    hits.sort(key=sort_key)
    return hits[:limit]


def find(text: str, exact: bool = False, gana: str | None = None, limit: int = 50, db_path: Path | str | None = None) -> list[dict[str, Any]]:
    """Alias for search_forms."""
    return search_forms(text, exact=exact, gana=gana, limit=limit, db_path=db_path)


def get_ids_by_dhatu(dhatu: str, db_path: Path | str | None = None) -> list[str]:
    """Resolve SLP1 dhatu string (OpadeSikasvarUpam) to list of dhatu ids.
    Exact match on value. Returns sorted ids."""
    con = connect(db_path)
    dhatu = dhatu.strip()
    if not dhatu:
        return []
    cur = con.execute(
        "SELECT dhatu_id FROM dhatu_info WHERE name='OpadeSikasvarUpam' AND value=? ORDER BY dhatu_id",
        (dhatu,)
    )
    ids = [r["dhatu_id"] for r in cur.fetchall()]
    # fallback: also try dhatu column in upasarga_entries (sometimes differs)
    if not ids:
        cur2 = con.execute("SELECT DISTINCT dhatu_id FROM upasarga_entries WHERE dhatu=? ORDER BY dhatu_id", (dhatu,))
        ids = [r["dhatu_id"] for r in cur2.fetchall()]
    return ids


def resolve_dhatu_input(inp: str, db_path: Path | str | None = None) -> list[str]:
    """If inp looks like NN.NNNN treat as id, else treat as dhatu string.
    Returns list of ids (empty if not found). For id, validates existence."""
    import re
    inp = inp.strip()
    if re.match(r"^\d{2}\.\d{4}$", inp):
        # verify exists
        con = connect(db_path)
        row = con.execute("SELECT id FROM dhatus WHERE id=?", (inp,)).fetchone()
        return [inp] if row else []
    # else treat as dhatu string
    return get_ids_by_dhatu(inp, db_path=db_path)


def query(sql: str, params: tuple | dict | None = None, db_path: Path | str | None = None) -> list[dict[str, Any]]:
    """Run arbitrary SELECT and return rows as dicts."""
    con = connect(db_path)
    cur = con.execute(sql, params or ())
    cols = [d[0] for d in cur.description] if cur.description else []
    return [dict(zip(cols, row)) for row in cur.fetchall()]
