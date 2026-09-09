"""Kṛdanta (verbal participle) declension bridge for Sanskrit.

Connects verbal participles from the SQLite database (e.g. kta, ktavatu, Satf,
SAnac, tavya, anIyar, yat, Ryat, tfc, kvasu, etc.) with the subanta nominal
engine to provide complete vibhakti tables across genders, numbers, and cases.

Usage::

    from skt_morph_data.krdanta import decline_participle, list_participle_pratyayas

    # Decline past passive participle of BU in masculine
    res = decline_participle("BU", "kta", gender="m")
    # Decline present active participle of gam in feminine
    res = decline_participle("gam", "Satf", gender="f")
    # Decline across all genders
    res = decline_participle("kf", "ktavatu")
    # Indeclinables report as avyaya
    res = decline_participle("BU", "ktvA")
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .query import get_dhatu, get_participles, resolve_dhatu_input
from .subanta import decline, to_table

PRATYAYA_ALIASES: dict[str, str] = {
    "aniya": "anIyar",
    "aniyar": "anIyar",
    "anIya": "anIyar",
    "satr": "Satf",
    "shatri": "Satf",
    "shatru": "Satf",
    "satf": "Satf",
    "shatf": "Satf",
    "sanac": "SAnac",
    "shanac": "SAnac",
    "shAnac": "SAnac",
    "canas": "cAnaS",
    "chanas": "cAnaS",
    "trc": "tfc",
    "tavya": "tavya",
    "tavyat": "tavya",
    "ktva": "ktvA",
    "lyut": "lyuw",
    "lyu": "lyu",
    "ghany": "GaY",
    "gay": "GaY",
    "ghaj": "GaY",
    "nvul": "Rvul",
    "vul": "vun",
    "nyat": "Ryat",
    "kyap": "kyap",
    "kvasu": "kvasu",
    "vasu": "kvasu",
    "ktin": "ktin",
    "namul": "Ramul",
}

INDECLINABLE_PRATYAYAS: set[str] = {"ktvA", "lyap", "tumun", "Ramul", "naN"}


def normalize_pratyaya(pratyaya: str) -> str:
    """Normalize user pratyaya string to database key."""
    p = pratyaya.strip()
    low = p.lower()
    if low in PRATYAYA_ALIASES:
        return PRATYAYA_ALIASES[low]
    if p in PRATYAYA_ALIASES:
        return PRATYAYA_ALIASES[p]
    return p


def list_participle_pratyayas(
    dhatu_id: str | None = None,
    category: str = "krut",
    db_path: Path | str | None = None,
) -> list[str]:
    """List available participle suffixes (pratyayas)."""
    if dhatu_id:
        ids = resolve_dhatu_input(dhatu_id, db_path=db_path)
        if ids:
            d_id = ids[0]
            parts = get_participles(d_id, category=category, db_path=db_path)
            cat_dict = parts.get(category, {})
            return sorted(cat_dict.keys())
    # Default common krut pratyayas
    return [
        "BAvakarma-SAnac", "GaY", "Ramul", "Rvul", "Ryat", "Satf", "ac",
        "anIyar", "cAnaS", "gsnu", "kta", "ktavatu", "ktin", "ktvA", "kvasu",
        "lyap", "lyuw", "sya-BAvakarma-SAnac", "sya-SAnac", "sya-Satf",
        "tavya", "tfc", "tumun", "ukaY", "vun", "yat",
    ]


def _decline_participle_gender(
    base: str,
    m: str,
    f: str,
    n: str,
    gender: str,
) -> dict[str, Any]:
    """Decline a specific gender from a participle DB row."""
    if gender == "m":
        if base.endswith("vat"):
            return decline(base, gender="m", paradigm="vat_m")
        elif base.endswith("mat"):
            return decline(base, gender="m", paradigm="mat_m")
        elif base.endswith("tf"):
            return decline(base, gender="m", paradigm="tf_m")
        elif base.endswith("vas"):
            if base == "vidvas":
                return decline(base, gender="m", paradigm="vidvas_m")
            try:
                return decline(base, gender="m", paradigm="vas_m")
            except Exception:
                return decline(base, gender="m")
        elif base.endswith("at"):
            return decline(base, gender="m", paradigm="at_m")
        elif m:
            m_stem = m.split("/")[0].strip()
            if m_stem.endswith("H"):
                m_stem = m_stem[:-1]
            return decline(m_stem, gender="m")
        elif base:
            return decline(base, gender="m")
        else:
            raise ValueError(f"No masculine stem available for base '{base}'")

    elif gender == "f":
        if f:
            f_stem = f.split("/")[0].strip()
            if f_stem.endswith("H"):
                f_stem = f_stem[:-1]
            return decline(f_stem, gender="f")
        elif base.endswith("a"):
            return decline(base[:-1] + "A", gender="f", paradigm="A_f")
        elif base.endswith("vat") or base.endswith("mat") or base.endswith("at"):
            return decline(base + "I", gender="f", paradigm="I_f")
        elif base.endswith("tf"):
            return decline(base[:-1] + "trI", gender="f", paradigm="I_f")
        elif base:
            return decline(base, gender="f")
        else:
            raise ValueError(f"No feminine stem available for base '{base}'")

    elif gender == "n":
        if base.endswith("vat") or base.endswith("mat") or base.endswith("at"):
            return decline(base, gender="n", paradigm="at_n")
        elif base.endswith("tf"):
            return decline(base, gender="n", paradigm="f_n")
        elif base.endswith("vas"):
            n_stem = base[:-3] + "vat"
            return decline(n_stem, gender="n", paradigm="at_n")
        elif base.endswith("a"):
            return decline(base, gender="n", paradigm="a_n")
        elif n:
            n_stem = n.split("/")[0].strip()
            if n_stem.endswith("m") and base.endswith("a"):
                return decline(base, gender="n", paradigm="a_n")
            return decline(n_stem, gender="n")
        elif base:
            return decline(base, gender="n")
        else:
            raise ValueError(f"No neuter stem available for base '{base}'")

    else:
        raise ValueError(f"Invalid gender '{gender}'. Must be 'm', 'f', or 'n'.")


def decline_participle(
    dhatu: str,
    pratyaya: str,
    gender: str | None = None,
    prefix: str = "",
    category: str = "krut",
    variant_idx: int = 0,
    db_path: Path | str | None = None,
) -> dict[str, Any]:
    """Decline a verbal participle (kṛdanta) across vibhaktis and vacanas.

    Parameters
    ----------
    dhatu:
        Dhatu identifier (e.g. '01.0001') or dhatu lemma in SLP1 (e.g. 'BU', 'gam', 'kf').
    pratyaya:
        Participle affix (e.g. 'kta', 'ktavatu', 'Satf', 'SAnac', 'tavya', 'anIyar',
        'yat', 'Ryat', 'tfc', 'kvasu', 'ktin', 'lyuw', 'GaY', 'ktvA', 'tumun', 'lyap').
    gender:
        'm' (masculine), 'f' (feminine), 'n' (neuter), or None (all genders).
    prefix:
        Upasarga / prefix string (default: '' for uncompounded root).
    category:
        Participle category: 'krut' (default), 'san_krut', 'nich_krut', 'yang_krut', 'yangluk_krut'.
    variant_idx:
        Index of the variant if multiple entries exist for this pratyaya (default: 0).
    db_path:
        Optional custom SQLite database path.

    Returns
    -------
    dict with participle declension tables.
    """
    dhatu = dhatu.strip()
    if not dhatu:
        raise ValueError("dhatu required")

    ids = resolve_dhatu_input(dhatu, db_path=db_path)
    if not ids:
        raise KeyError(f"Dhatu '{dhatu}' not found in database")
    dhatu_id = ids[0]

    # Resolve OpadeSika name for display
    dhatu_lemma = dhatu
    try:
        info = get_dhatu(dhatu_id, db_path=db_path)
        for inf in info.get("info", []):
            if inf.get("name") == "OpadeSikasvarUpam":
                dhatu_lemma = inf.get("value", dhatu)
                break
    except Exception:
        pass

    # Query participles
    part_dict = get_participles(dhatu_id, category=category, prefix=prefix, db_path=db_path)
    cat_entries = part_dict.get(category, {})
    if not cat_entries:
        raise KeyError(f"No {category} participles found for dhatu {dhatu_id} ({dhatu_lemma})")

    norm_p = normalize_pratyaya(pratyaya)
    if norm_p not in cat_entries:
        available = sorted(cat_entries.keys())
        raise KeyError(f"Pratyaya '{pratyaya}' not found for {dhatu_id}. Available: {', '.join(available)}")

    variants = cat_entries[norm_p]
    if not variants:
        raise ValueError(f"No entries found for {norm_p} in {dhatu_id}")
    if variant_idx >= len(variants):
        variant_idx = 0
    row = variants[variant_idx]

    base = row.get("base", "").strip()
    m = row.get("m", "").strip()
    f = row.get("f", "").strip()
    n = row.get("n", "").strip()

    # Check for avyaya (indeclinable)
    if norm_p in INDECLINABLE_PRATYAYAS or (not m and not f and not n and base):
        return {
            "dhatu": dhatu_lemma,
            "dhatu_id": dhatu_id,
            "pratyaya": norm_p,
            "category": category,
            "prefix": prefix,
            "is_avyaya": True,
            "form": base,
            "type": "participle",
            "desc": f"indeclinable participle {norm_p} of {dhatu_lemma}",
            "forms": {
                "prathamA": [base, "-", "-"],
                "dvitIyA": ["-", "-", "-"],
                "tftIyA": ["-", "-", "-"],
                "caturTI": ["-", "-", "-"],
                "paYcamI": ["-", "-", "-"],
                "zazWI": ["-", "-", "-"],
                "saptamI": ["-", "-", "-"],
                "saMboDana": ["-", "-", "-"],
            },
        }

    # If specific gender requested
    if gender and gender.lower() in ("m", "f", "n"):
        g = gender.lower()
        sub_res = _decline_participle_gender(base, m, f, n, g)
        return {
            "word": f"{dhatu_lemma}+{norm_p}",
            "dhatu": dhatu_lemma,
            "dhatu_id": dhatu_id,
            "pratyaya": norm_p,
            "category": category,
            "prefix": prefix,
            "is_avyaya": False,
            "gender": g,
            "stem": sub_res["word"],
            "paradigm": sub_res["paradigm"],
            "forms": sub_res["forms"],
            "type": "participle",
            "desc": f"participle {norm_p} of {dhatu_lemma} ({g})",
            "all_variants": variants if len(variants) > 1 else None,
        }

    # All three genders
    genders_res: dict[str, dict[str, list[str]]] = {}
    stems_res: dict[str, str] = {}
    paradigms_res: dict[str, str] = {}

    for g in ("m", "f", "n"):
        try:
            sub_res = _decline_participle_gender(base, m, f, n, g)
            genders_res[g] = sub_res["forms"]
            stems_res[g] = sub_res["word"]
            paradigms_res[g] = sub_res["paradigm"]
        except Exception:
            pass

    return {
        "word": f"{dhatu_lemma}+{norm_p}",
        "dhatu": dhatu_lemma,
        "dhatu_id": dhatu_id,
        "pratyaya": norm_p,
        "category": category,
        "prefix": prefix,
        "is_avyaya": False,
        "genders": genders_res,
        "stems": stems_res,
        "paradigms": paradigms_res,
        "type": "participle",
        "desc": f"participle {norm_p} of {dhatu_lemma} (all genders)",
        "all_variants": variants if len(variants) > 1 else None,
    }


def get_dhatu_participles_summary(
    dhatu: str,
    prefix: str = "",
    category: str = "krut",
    db_path: Path | str | None = None,
) -> list[dict[str, Any]]:
    """Get a high-level summary of all participles for a given dhatu."""
    dhatu = dhatu.strip()
    ids = resolve_dhatu_input(dhatu, db_path=db_path)
    if not ids:
        raise KeyError(f"Dhatu '{dhatu}' not found")
    dhatu_id = ids[0]

    parts = get_participles(dhatu_id, category=category, prefix=prefix, db_path=db_path)
    cat_dict = parts.get(category, {})

    summary: list[dict[str, Any]] = []
    for p, rows in sorted(cat_dict.items()):
        for r in rows:
            is_avyaya = p in INDECLINABLE_PRATYAYAS or (not r.get("m") and not r.get("f") and not r.get("n"))
            summary.append({
                "pratyaya": p,
                "base": r.get("base", ""),
                "m": r.get("m", ""),
                "f": r.get("f", ""),
                "n": r.get("n", ""),
                "is_avyaya": is_avyaya,
            })
    return summary
