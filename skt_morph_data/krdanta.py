"""Kṛdanta (verbal participle) declension bridge for Sanskrit.

Connects verbal participles from the SQLite database or raw scraped data
(e.g. kta, ktavatu, Satf, SAnac, tavya, anIyar, yat, Ryat, tfc, kvasu, etc.)
with the subanta nominal engine to provide complete vibhakti tables across
genders, numbers, and cases with exact Pāṇinian and Ashtadhyayi.com parity.

Parity architecture with `dhaturupa-wasm/src/engine/subanta.rs` & `derive_krut.rs`:
 - Supports all 5 verb families: `shuddha` (krut), `nich_krut`, `san_krut`,
   `yang_krut`, and `yangluk_krut`.
 - Full Ashtadhyayi reference matrix (`krt_ref_slot`) over 26+ pratyayas.
 - Root-level overrides: `SATF_ABHYASTA_IDS`, `SATF_TUDATI_IDS`, `AC_DEVI_IDS`.
 - Quirk tables: `atuc_m_table`, `a_value_table`, `i_value_mala_table`,
   `a_short_mala_table`, `a_value_devif_table`.
 - Vas-stem samprasāraṇa & weak derivation (`vas_weak`).
 - Returns full 24-slot `SubantaParadigm` with all valid alternants.
"""

from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import Any, Optional

from .query import get_dhatu, get_participles, resolve_dhatu_input
from .subanta import (
    Linga,
    SubantaParadigm,
    SubantaSlot,
    VACANA_INDEX,
    VACANAS,
    VIBHAKTI_INDEX,
    VIBHAKTIS,
    apply_natva,
    decline,
    to_table,
)

# ---------------------------------------------------------------------------
# Suffix Aliases & Invariants
# ---------------------------------------------------------------------------

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
    "krtya": "kRtya",
    "kftya": "kRtya",
    "kRtya": "kRtya",
}

INDECLINABLE_PRATYAYAS: set[str] = {"ktvA", "lyap", "tumun", "Ramul", "naN"}

# ---------------------------------------------------------------------------
# Ashtadhyayi.com Reference Paradigms
# ---------------------------------------------------------------------------

class KrtParadigm(str, Enum):
    """The 26 site reference paradigms matching `dhaturupa-wasm/src/engine/subanta.rs`."""
    DevaM = "@deva1"
    PhalaN = "@phala1"
    MAlAF = "@mAlA1"
    DevIF = "@devI1"
    GatiF = "@gati1"
    SAdhuM = "@sAdhu1"
    DhenuF = "@dhenu1"
    KaTuN = "@kaTu4"
    InM = "@zazin1"
    InN = "@kSamin2"
    GacchatM = "@gacchat1"
    DadatM = "@dadat1"
    PacatN = "@pacat1"
    ViyatN = "@viyat1"
    TudatN = "@tudat1"
    DadatN = "@dadat2"
    BhavatM = "@bhavat1"
    PhalavatN = "@phalavat2"
    SedivasM = "@sedivas1"
    VidvasN = "@vidvas2"
    DhAtRM = "@dhAtR1"
    DhAtRN = "@dhAtR2"
    Jvs = "@svapnaj1"
    JvsN = "@svapnaj2"
    VanM = "@yajvan1"
    ManN = "@sadman1"


SATF_ABHYASTA_IDS: set[str] = {
    "02.0066", "02.0067", "02.0068", "02.0069", "02.0070", "02.0071", "02.0072",
}

SATF_TUDATI_IDS: set[str] = {
    "02.0046", "02.0047", "02.0048", "02.0049", "02.0050", "02.0051", "02.0052",
    "02.0053", "02.0054", "02.0055", "02.0056", "02.0057", "02.0067",
}

AC_DEVI_IDS: set[str] = {
    "01.0056", "01.0791", "01.1112", "01.0640", "01.1087", "01.1124", "10.0001",
    "01.0736", "01.1085", "03.0018", "04.001", "06.0008", "10.0371", "10.0230", "10.0249",
}


def normalize_pratyaya(pratyaya: str) -> str:
    """Normalize user pratyaya string to standard SLP1 database key."""
    p = pratyaya.strip()
    low = p.lower()
    if low in PRATYAYA_ALIASES:
        return PRATYAYA_ALIASES[low]
    if p in PRATYAYA_ALIASES:
        return PRATYAYA_ALIASES[p]
    return p


def normalize_krut_family(family: str) -> str:
    """Normalize UI family names to engine family keys."""
    fam = family.strip().lower()
    if fam in ("krut", "shuddha", "kartari", "karmani"):
        return "krut"
    if fam in ("san", "san_krut"):
        return "san_krut"
    if fam in ("nich", "nich_krut"):
        return "nich_krut"
    if fam in ("yang", "yang_krut"):
        return "yang_krut"
    if fam in ("yangluk", "yangluk_krut"):
        return "yangluk_krut"
    return fam


def krt_ref_slot(family: str, krt: str, field: str, baseindex: str = "") -> Optional[KrtParadigm]:
    """Exact site reference paradigm resolver matching `dhaturupa-wasm/src/engine/subanta.rs:krt_ref_slot`.
    
    Returns `None` if the pratyaya is indeclinable (avyaya) or if the field (m/f/n)
    is not declined on the site.
    """
    fam_norm = normalize_krut_family(family)
    is_krut = fam_norm == "krut"
    yangluk = fam_norm == "yangluk_krut"

    p: Optional[KrtParadigm] = None
    s: Optional[KrtParadigm] = None
    n: Optional[KrtParadigm] = None

    if krt in ("ktvA", "lyap", "tumun", "Ramul"):
        return None
    elif krt in ("lyuw", "itra"):
        n = KrtParadigm.PhalaN
    elif krt == "tfc":
        p, s, n = KrtParadigm.DhAtRM, KrtParadigm.DevIF, KrtParadigm.DhAtRN
    elif krt == "atfn":
        p, s, n = KrtParadigm.GacchatM, KrtParadigm.DevIF, KrtParadigm.ViyatN
    elif krt == "ktavatu":
        p, s, n = KrtParadigm.BhavatM, KrtParadigm.DevIF, KrtParadigm.PhalavatN
    elif krt == "kvasu":
        p, s, n = KrtParadigm.SedivasM, KrtParadigm.DevIF, KrtParadigm.VidvasN
    elif krt == "najiN":
        p, s, n = KrtParadigm.Jvs, KrtParadigm.Jvs, KrtParadigm.JvsN
    elif krt == "GinuR":
        p, s, n = KrtParadigm.InM, KrtParadigm.DevIF, KrtParadigm.InN
    elif krt == "Nvanip":
        p, s, n = KrtParadigm.VanM, KrtParadigm.DevIF, KrtParadigm.ManN
    elif krt in ("u", "Aluc", "Aru", "knu", "kru", "gsnu"):
        p, s, n = KrtParadigm.SAdhuM, KrtParadigm.DhenuF, KrtParadigm.KaTuN
    elif krt == "aTuc":
        p = KrtParadigm.BhavatM
    elif krt in ("GaY", "ap", "varac", "nan", "naN"):
        p = KrtParadigm.DevaM
    elif krt == "ktin":
        s = KrtParadigm.GatiF
    elif krt in ("Takan", "Rvuc", "a", "aN"):
        s = KrtParadigm.MAlAF
    elif krt in ("zwran", "zvun"):
        s = KrtParadigm.DevIF
    elif krt in ("Ryuw", "zAkan"):
        p, s, n = KrtParadigm.DevaM, KrtParadigm.DevIF, KrtParadigm.PhalaN
    elif krt == "Satf":
        if (is_krut and (baseindex.startswith("03") or baseindex in SATF_ABHYASTA_IDS)) or yangluk:
            p = KrtParadigm.DadatM
        else:
            p = KrtParadigm.GacchatM

        if is_krut:
            if baseindex.startswith("01") or baseindex.startswith("04") or baseindex.startswith("10"):
                n = KrtParadigm.PacatN
            elif baseindex.startswith("03") or baseindex in SATF_ABHYASTA_IDS:
                n = KrtParadigm.DadatN
            elif baseindex.startswith("06") or baseindex in SATF_TUDATI_IDS:
                n = KrtParadigm.TudatN
            else:
                n = KrtParadigm.ViyatN
        else:
            n = KrtParadigm.PacatN
        s = KrtParadigm.DevIF
    elif krt == "sya-Satf":
        p, s, n = KrtParadigm.GacchatM, KrtParadigm.DevIF, KrtParadigm.TudatN
    elif krt == "ac":
        s = KrtParadigm.DevIF if (is_krut and baseindex in AC_DEVI_IDS) else KrtParadigm.MAlAF
        p, n = KrtParadigm.DevaM, KrtParadigm.PhalaN
    elif krt in (
        "Rvul", "yat", "kyap", "Ryat", "tavya", "anIyar", "kta", "SAnac",
        "sya-SAnac", "BAvakarma-SAnac", "sya-BAvakarma-SAnac", "ukaY", "cAnaS",
        "SAnan", "Ra", "ra", "Sa", "ktri", "kmarac", "Gurac", "kurac", "kvarap",
        "klukan", "krukan", "vuY", "vun", "lyu"
    ):
        p, s, n = KrtParadigm.DevaM, KrtParadigm.MAlAF, KrtParadigm.PhalaN
    else:
        return None

    if field == "m":
        return p
    elif field == "f":
        return s
    elif field == "n":
        return n
    return None


# ---------------------------------------------------------------------------
# Weak Stem Extraction & Shape Derivation
# ---------------------------------------------------------------------------

def weak_for(kind: KrtParadigm, value: str) -> Optional[str]:
    """Derive the declension stem from the clicked/citation value matching `subanta.rs:weak`."""
    v = value.strip()
    if not v or "/" in v:
        return None
    bare = v[:-1] if v.endswith("H") else v

    if kind == KrtParadigm.DevaM:
        if bare.endswith("a"):
            return bare
        return None
    elif kind == KrtParadigm.PhalaN:
        b = v[:-1] if v.endswith("m") else v
        if b.endswith("a"):
            return b
        return None
    elif kind == KrtParadigm.MAlAF:
        if v.endswith("A"):
            return v
        return None
    elif kind == KrtParadigm.DevIF:
        if v.endswith("I"):
            return v
        return None
    elif kind == KrtParadigm.GatiF:
        if bare.endswith("i"):
            return bare
        return None
    elif kind in (KrtParadigm.SAdhuM, KrtParadigm.DhenuF, KrtParadigm.KaTuN):
        if bare.endswith("u"):
            return bare
        return None
    elif kind in (
        KrtParadigm.GacchatM, KrtParadigm.PacatN, KrtParadigm.ViyatN,
        KrtParadigm.TudatN, KrtParadigm.DadatN, KrtParadigm.PhalavatN
    ):
        if bare.endswith("Ant"):
            return bare[:-3] + "At"
        if bare.endswith("ant"):
            return bare[:-3] + "at"
        if bare.endswith("An"):
            return bare[:-2] + "At"
        if bare.endswith("an"):
            return bare[:-2] + "at"
        if bare.endswith("d"):
            return bare[:-1] + "t"
        if bare.endswith("t"):
            return bare
        return None
    elif kind == KrtParadigm.DadatM:
        if bare.endswith("An"):
            return bare[:-2] + "At"
        if bare.endswith("an"):
            return bare[:-2] + "at"
        if bare.endswith("d"):
            return bare[:-1] + "t"
        if bare.endswith("t"):
            return bare
        return None
    elif kind == KrtParadigm.BhavatM:
        if v.endswith("vAn") or v.endswith("vant"):
            return v[:-3] + "vat"
        if v.endswith("vat"):
            return v
        return None
    elif kind == KrtParadigm.SedivasM:
        if v.endswith("An"):
            return v[:-2] + "as"
        if v.endswith("s"):
            return v
        return None
    elif kind == KrtParadigm.VidvasN:
        if v.endswith("at") or v.endswith("ad"):
            return v[:-2] + "as"
        if v.endswith("s"):
            return v
        return None
    elif kind in (KrtParadigm.DhAtRM, KrtParadigm.DhAtRN):
        if v.endswith("A"):
            return v[:-1] + "f"
        if v.endswith("f"):
            return v
        return None
    elif kind in (KrtParadigm.InM, KrtParadigm.InN):
        if v.endswith("I"):
            return v[:-1] + "in"
        if v.endswith("i") and not v.endswith("in"):
            return v + "n"
        if v.endswith("in"):
            return v
        return None
    elif kind in (KrtParadigm.VanM, KrtParadigm.ManN):
        if v.endswith("A") or v.endswith("a"):
            return v[:-1] + "an"
        if v.endswith("an"):
            return v
        return None
    elif kind in (KrtParadigm.Jvs, KrtParadigm.JvsN):
        if v.endswith("k") or v.endswith("g"):
            return v[:-1] + "j"
        if v.endswith("j"):
            return v
        return None
    return bare


# ---------------------------------------------------------------------------
# Quirk Tables & Special Paradigm Builders
# ---------------------------------------------------------------------------

def _make_slots(rows: list[tuple[Any, Any, Any]]) -> list[SubantaSlot]:
    """Convert 8 tuples of (eka, dvi, bahu) into 24 SubantaSlots."""
    cells: list[SubantaSlot] = []
    for vib_idx, (e, d, b) in enumerate(rows, start=1):
        for vac_idx, val in enumerate((e, d, b), start=1):
            if isinstance(val, (list, tuple)):
                forms = [str(x) for x in val if str(x).strip()]
            else:
                forms = [str(val)] if str(val).strip() else []
            cells.append(SubantaSlot(vibhakti=vib_idx, vacana=vac_idx, forms=forms))
    return cells


def a_value_table(kind: KrtParadigm, value: str) -> Optional[list[SubantaSlot]]:
    """The site's @deva1/@phala1 table when the row value is an ā-final stem (upasaryA, vrajyA)."""
    if not value.endswith("A"):
        return None
    p = value[:-1]
    if kind == KrtParadigm.DevaM:
        rows = [
            (value + "H", p + "O", value + "H"),
            (value + "m", p + "O", value + "n"),
            (value, value + "ByAm", value + "BiH"),
            (p + "E", value + "ByAm", value + "ByaH"),
            (value + "H", value + "ByAm", value + "ByaH"),
            (value + "H", p + "OH", value + "m"),
            (p + "e", p + "OH", value + "su"),
            (value + "H", p + "O", value + "H"),
        ]
        return _make_slots(rows)
    elif kind == KrtParadigm.PhalaN:
        ni = apply_natva(value + "ni", len(value))
        rows = [
            (value, p + "e", ni),
            (value, p + "e", ni),
            (value, value + "ByAm", value + "BiH"),
            (p + "E", value + "ByAm", value + "ByaH"),
            (value + "H", value + "ByAm", value + "ByaH"),
            (value + "H", p + "OH", value + "m"),
            (p + "e", p + "OH", value + "su"),
            (value, p + "e", ni),
        ]
        return _make_slots(rows)
    return None


def i_value_mala_table(value: str) -> Optional[list[SubantaSlot]]:
    """The site's @mAlA1 table when the row value ends in ī (sftvarI)."""
    if not value.endswith("I"):
        return None
    p = value[:-1] + "y"
    gen_pl = apply_natva(value + "nAm", len(value))
    rows = [
        (value, value, p + "aH"),
        (value + "m", value, value + "H"),
        (p + "A", value + "ByAm", value + "BiH"),
        (p + "e", value + "ByAm", value + "ByaH"),
        (p + "aH", value + "ByAm", value + "ByaH"),
        (p + "aH", value + "os", gen_pl),
        (value, value + "os", value + "zu"),
        (value + "H", value, p + "aH"),
    ]
    return _make_slots(rows)


def a_short_mala_table(value: str) -> Optional[list[SubantaSlot]]:
    """The site's @mAlA1 table when the value ends in short a (DAka)."""
    if not value.endswith("a"):
        return None
    p = value[:-1]
    gen_pl = apply_natva(p + "AnAm", len(p))
    rows = [
        (p + "aH", p + "e", p + "AH"),
        (p + "am", p + "e", p + "AH"),
        (p + "A", p + "AByAm", p + "EH"),
        (p + "E", p + "AByAm", p + "eByaH"),
        (p + "AH", p + "AByAm", p + "eByaH"),
        (p + "AH", p + "ayoH", gen_pl),
        (p + "e", p + "ayoH", p + "ezu"),
        (p + "aH", p + "e", p + "AH"),
    ]
    return _make_slots(rows)


def atuc_m_table(value: str) -> Optional[list[SubantaSlot]]:
    """The site's @bhavat2 table applied to aTuc u-stems (nandaTu -> nandaTU/nandaTUnO...)."""
    if not value.endswith("u"):
        return None
    p = value[:-1]
    strong = f"{p}Un"
    rows = [
        (p + "U", strong + "O", strong + "aH"),
        (strong + "am", strong + "O", strong),
        (p + "vA", p + "uByAm", p + "uBiH"),
        (p + "ve", p + "uByAm", p + "uByaH"),
        (p + "vaH", p + "uByAm", p + "uByaH"),
        (p + "vaH", p + "voH", strong + "Am"),
        (p + "vi", p + "voH", p + "uzu"),
        (p + "un", strong + "O", strong + "aH"),
    ]
    return _make_slots(rows)


def a_value_devif_table(value: str) -> Optional[list[SubantaSlot]]:
    """The site's @devI1 table when the row value ends in ā (anusarA)."""
    if not value.endswith("A"):
        return None
    p = value[:-1]
    gen_pl = apply_natva(value + "nAm", len(value))
    rows = [
        (value, p + "O", value + "H"),
        (value + "m", p + "O", value + "H"),
        (value, value + "ByAm", value + "BiH"),
        (p + "E", value + "ByAm", value + "ByaH"),
        (value + "H", value + "ByAm", value + "ByaH"),
        (value + "H", p + "OH", gen_pl),
        (value + "m", p + "OH", value + "su"),
        (p + "a", p + "O", value + "H"),
    ]
    return _make_slots(rows)


def vas_weak(core: str, neuter: bool = False) -> str:
    """क्वसु/वस् weak stem resolver with samprasāraṇa & internal sandhi matching `subanta.rs:vas_weak`."""
    q = core[:-1] if core.endswith("v") else core
    if not neuter and q.endswith("i"):
        q = q[:-1]
    last = q[-1] if q else ""
    if last in ("a", "A"):
        return q[:-1] + "oz"
    elif last in ("i", "I"):
        return q[:-1] + "yuz"
    elif last in ("u", "U"):
        return q[:-1] + "Uz"
    elif last in ("f", "F"):
        return q[:-1] + "ruz"
    elif last in ("x", "X"):
        return q[:-1] + "luz"
    elif last == "e":
        return q[:-1] + "ayuz"
    elif last == "E":
        return q[:-1] + "Ayuz"
    elif last == "o":
        return q[:-1] + "avuz"
    elif last == "O":
        return q[:-1] + "Avuz"
    return q + "uz"


# ---------------------------------------------------------------------------
# Exact Reference Table Generators
# ---------------------------------------------------------------------------

def decline_krt_reference(kind: KrtParadigm, weak: str, linga: str) -> list[SubantaSlot]:
    """Generate exact 24 slots with site alternants for a reference paradigm."""
    w = weak
    if kind == KrtParadigm.DevaM:
        p = w[:-1] if w.endswith("a") else w
        ins_sg = apply_natva(p + "ena", len(p))
        gen_pl = apply_natva(p + "AnAm", len(p))
        rows = [
            (p + "aH", p + "O", p + "AH"),
            (p + "am", p + "O", p + "An"),
            (ins_sg, p + "AByAm", p + "EH"),
            (p + "Aya", p + "AByAm", p + "eByaH"),
            ([p + "Ad", p + "At"], p + "AByAm", p + "eByaH"),
            (p + "asya", p + "ayoH", gen_pl),
            (p + "e", p + "ayoH", p + "ezu"),
            (p + "a", p + "O", p + "AH"),
        ]
        return _make_slots(rows)

    elif kind == KrtParadigm.PhalaN:
        p = w[:-1] if w.endswith("a") else w
        nom_pl = apply_natva(p + "Ani", len(p))
        ins_sg = apply_natva(p + "ena", len(p))
        gen_pl = apply_natva(p + "AnAm", len(p))
        rows = [
            (p + "am", p + "e", nom_pl),
            (p + "am", p + "e", nom_pl),
            (ins_sg, p + "AByAm", p + "EH"),
            (p + "Aya", p + "AByAm", p + "eByaH"),
            ([p + "Ad", p + "At"], p + "AByAm", p + "eByaH"),
            (p + "asya", p + "ayoH", gen_pl),
            (p + "e", p + "ayoH", p + "ezu"),
            (p + "a", p + "e", nom_pl),
        ]
        return _make_slots(rows)

    elif kind == KrtParadigm.MAlAF:
        p = w[:-1] if w.endswith("A") else w
        gen_pl = apply_natva(p + "AnAm", len(p))
        rows = [
            (p + "A", p + "e", p + "AH"),
            (p + "Am", p + "e", p + "AH"),
            (p + "ayA", p + "AByAm", p + "ABiH"),
            (p + "AyE", p + "AByAm", p + "AByaH"),
            (p + "AyAH", p + "AByAm", p + "AByaH"),
            (p + "AyAH", p + "ayoH", gen_pl),
            (p + "AyAm", p + "ayoH", p + "Asu"),
            (p + "e", p + "e", p + "AH"),
        ]
        return _make_slots(rows)

    elif kind == KrtParadigm.DevIF:
        p = w[:-1] if w.endswith("I") else w
        gen_pl = apply_natva(p + "InAm", len(p))
        rows = [
            (p + "I", p + "yO", p + "yaH"),
            (p + "Im", p + "yO", p + "IH"),
            (p + "yA", p + "IByAm", p + "IBiH"),
            (p + "yE", p + "IByAm", p + "IByaH"),
            (p + "yAH", p + "IByAm", p + "IByaH"),
            (p + "yAH", p + "yoH", gen_pl),
            (p + "yAm", p + "yoH", p + "Izu"),
            (p + "i", p + "yO", p + "yaH"),
        ]
        return _make_slots(rows)

    elif kind == KrtParadigm.GatiF:
        p = w[:-1] if w.endswith("i") else w
        gen_pl = apply_natva(p + "InAm", len(p))
        rows = [
            (p + "iH", p + "I", p + "ayaH"),
            (p + "im", p + "I", p + "IH"),
            (p + "yA", p + "iByAm", p + "iBiH"),
            ([p + "aye", p + "yE"], p + "iByAm", p + "iByaH"),
            ([p + "eH", p + "yAH"], p + "iByAm", p + "iByaH"),
            ([p + "eH", p + "yAH"], p + "yoH", gen_pl),
            ([p + "O", p + "yAm"], p + "yoH", p + "izu"),
            (p + "e", p + "I", p + "ayaH"),
        ]
        return _make_slots(rows)

    elif kind in (KrtParadigm.SAdhuM, KrtParadigm.KaTuN, KrtParadigm.DhenuF):
        p = w[:-1] if w.endswith("u") else w
        gen_pl = apply_natva(p + "UnAm", len(p))
        if kind == KrtParadigm.KaTuN:
            nom_pl = apply_natva(p + "Uni", len(p))
            dvi = apply_natva(p + "unI", len(p))
            ins_sg = apply_natva(p + "unA", len(p))
            dat_sg = [apply_natva(p + "une", len(p)), p + "ave"]
            abl_gen_sg = [apply_natva(p + "unaH", len(p)), p + "oH"]
            gen_loc_dvi = [apply_natva(p + "unoH", len(p)), apply_natva(p + "voH", len(p))]
            loc_sg = [apply_natva(p + "uni", len(p)), p + "O"]
            rows = [
                (p + "u", dvi, nom_pl),
                (p + "u", dvi, nom_pl),
                (ins_sg, p + "uByAm", p + "uBiH"),
                (dat_sg, p + "uByAm", p + "uByaH"),
                (abl_gen_sg, p + "uByAm", p + "uByaH"),
                (abl_gen_sg, gen_loc_dvi, gen_pl),
                (loc_sg, gen_loc_dvi, p + "uzu"),
                ([p + "o", p + "u"], dvi, nom_pl),
            ]
            return _make_slots(rows)
        elif kind == KrtParadigm.DhenuF:
            rows = [
                (p + "uH", p + "U", p + "avaH"),
                (p + "um", p + "U", p + "UH"),
                (p + "vA", p + "uByAm", p + "uBiH"),
                ([p + "ave", p + "vE"], p + "uByAm", p + "uByaH"),
                ([p + "oH", p + "vAH"], p + "uByAm", p + "uByaH"),
                ([p + "oH", p + "vAH"], p + "voH", gen_pl),
                ([p + "O", p + "vAm"], p + "voH", p + "uzu"),
                (p + "o", p + "U", p + "avaH"),
            ]
            return _make_slots(rows)
        else:  # SAdhuM
            ins_sg = apply_natva(p + "unA", len(p))
            rows = [
                (p + "uH", p + "U", p + "avaH"),
                (p + "um", p + "U", p + "Un"),
                (ins_sg, p + "uByAm", p + "uBiH"),
                (p + "ave", p + "uByAm", p + "uByaH"),
                (p + "oH", p + "uByAm", p + "uByaH"),
                (p + "oH", p + "voH", gen_pl),
                (p + "O", p + "voH", p + "uzu"),
                (p + "o", p + "U", p + "avaH"),
            ]
            return _make_slots(rows)

    elif kind in (KrtParadigm.GacchatM, KrtParadigm.DadatM):
        p = w[:-1] if w.endswith("t") else w
        d = p + "d"
        strong = p + "nt"
        if kind == KrtParadigm.GacchatM:
            nom_sg = p + "n"
            dvi = strong + "O"
            bahu = strong + "aH"
            acc_sg = strong + "am"
            acc_bahu = p + "taH"
            rows = [
                (nom_sg, dvi, bahu),
                (acc_sg, dvi, acc_bahu),
                (p + "tA", d + "ByAm", d + "BiH"),
                (p + "te", d + "ByAm", d + "ByaH"),
                (p + "taH", d + "ByAm", d + "ByaH"),
                (p + "taH", p + "toH", p + "tAm"),
                (p + "ti", p + "toH", p + "tsu"),
                (nom_sg, dvi, bahu),
            ]
            return _make_slots(rows)
        else:  # DadatM (abhyasta, no num)
            dvi = p + "tO"
            bahu = p + "taH"
            rows = [
                ([d, p + "t"], dvi, bahu),
                (p + "tam", dvi, bahu),
                (p + "tA", d + "ByAm", d + "BiH"),
                (p + "te", d + "ByAm", d + "ByaH"),
                (p + "taH", d + "ByAm", d + "ByaH"),
                (p + "taH", p + "toH", p + "tAm"),
                (p + "ti", p + "toH", p + "tsu"),
                ([d, p + "t"], dvi, bahu),
            ]
            return _make_slots(rows)

    elif kind in (KrtParadigm.PacatN, KrtParadigm.ViyatN, KrtParadigm.TudatN, KrtParadigm.DadatN, KrtParadigm.PhalavatN):
        p = w[:-1] if w.endswith("t") else w
        d = p + "d"
        strong = p + "nt"
        if kind == KrtParadigm.PacatN:
            dual = [strong + "I"]
            plural = [strong + "i"]
        elif kind in (KrtParadigm.ViyatN, KrtParadigm.PhalavatN):
            dual = [p + "tI"]
            plural = [strong + "i"]
        elif kind == KrtParadigm.TudatN:
            dual = [strong + "I", p + "tI"]
            plural = [strong + "i"]
        else:  # DadatN
            dual = [p + "tI"]
            plural = [strong + "i", p + "ti"]

        nom_acc = ([d, p + "t"], dual, plural)
        rows = [
            nom_acc,
            nom_acc,
            (p + "tA", d + "ByAm", d + "BiH"),
            (p + "te", d + "ByAm", d + "ByaH"),
            (p + "taH", d + "ByAm", d + "ByaH"),
            (p + "taH", p + "toH", p + "tAm"),
            (p + "ti", p + "toH", p + "tsu"),
            nom_acc,
        ]
        return _make_slots(rows)

    elif kind == KrtParadigm.BhavatM:
        l = "v" if w.endswith("vat") else ("m" if w.endswith("mat") else "y")
        q = w[:-3]
        strong = f"{q}{l}ant"
        d = f"{q}{l}ad"
        rows = [
            (f"{q}{l}An", strong + "O", strong + "aH"),
            (strong + "am", strong + "O", w + "aH"),
            (w + "A", d + "ByAm", d + "BiH"),
            (w + "e", d + "ByAm", d + "ByaH"),
            (w + "aH", d + "ByAm", d + "ByaH"),
            (w + "aH", w + "oH", w + "Am"),
            (w + "i", w + "oH", w + "su"),
            (f"{q}{l}an", strong + "O", strong + "aH"),
        ]
        return _make_slots(rows)

    elif kind in (KrtParadigm.SedivasM, KrtParadigm.VidvasN):
        core = w[:-2] if w.endswith("as") else w
        vat = core + "at"
        vad = core + "ad"
        strong = core + "AMs"
        if kind == KrtParadigm.SedivasM:
            uz = vas_weak(core, False)
            rows = [
                (core + "An", strong + "O", strong + "aH"),
                (strong + "am", strong + "O", uz + "aH"),
                (uz + "A", vad + "ByAm", vad + "BiH"),
                (uz + "e", vad + "ByAm", vad + "ByaH"),
                (uz + "aH", vad + "ByAm", vad + "ByaH"),
                (uz + "aH", uz + "oH", uz + "Am"),
                (uz + "i", uz + "oH", vat + "su"),
                (core + "an", strong + "O", strong + "aH"),
            ]
            return _make_slots(rows)
        else:  # VidvasN
            uz = vas_weak(core, True)
            nom_acc = ([vad, vat], uz + "I", strong + "i")
            rows = [
                nom_acc,
                nom_acc,
                (uz + "A", vad + "ByAm", vad + "BiH"),
                (uz + "e", vad + "ByAm", vad + "ByaH"),
                (uz + "aH", vad + "ByAm", vad + "ByaH"),
                (uz + "aH", uz + "oH", uz + "Am"),
                (uz + "i", uz + "oH", vat + "su"),
                nom_acc,
            ]
            return _make_slots(rows)

    elif kind in (KrtParadigm.DhAtRM, KrtParadigm.DhAtRN):
        p = w[:-1] if w.endswith("f") else w
        gen_pl = apply_natva(p + "FRAm", len(p))
        if kind == KrtParadigm.DhAtRM:
            rows = [
                (p + "A", p + "ArO", p + "AraH"),
                (p + "Aram", p + "ArO", p + "Fn"),
                (p + "rA", p + "fByAm", p + "fBiH"),
                (p + "re", p + "fByAm", p + "fByaH"),
                (p + "uH", p + "fByAm", p + "fByaH"),
                (p + "uH", p + "roH", gen_pl),
                (p + "ari", p + "roH", p + "fzu"),
                (p + "aH", p + "ArO", p + "AraH"),
            ]
            return _make_slots(rows)
        else:  # DhAtRN: optional pairs per @dhAtR2
            pl = apply_natva(p + "FRi", len(p))
            nom_acc = (p + "f", p + "fRI", pl)
            rows = [
                nom_acc,
                nom_acc,
                ([p + "fRA", p + "rA"], p + "fByAm", p + "fBiH"),
                ([p + "fRe", p + "re"], p + "fByAm", p + "fByaH"),
                ([p + "fRaH", p + "uH"], p + "fByAm", p + "fByaH"),
                ([p + "fRaH", p + "uH"], [p + "fRoH", p + "roH"], gen_pl),
                ([p + "fRi", p + "ari"], [p + "fRoH", p + "roH"], p + "fzu"),
                ([p + "f", p + "aH"], p + "fRI", pl),
            ]
            return _make_slots(rows)

    elif kind in (KrtParadigm.InM, KrtParadigm.InN):
        p = w[:-2] if w.endswith("in") else w
        def _n(end: str) -> str:
            return apply_natva(p + end, len(p))

        if kind == KrtParadigm.InM:
            rows = [
                (p + "I", _n("inO"), _n("inaH")),
                (_n("inam"), _n("inO"), _n("inaH")),
                (_n("inA"), p + "iByAm", p + "iBiH"),
                (_n("ine"), p + "iByAm", p + "iByaH"),
                (_n("inaH"), p + "iByAm", p + "iByaH"),
                (_n("inaH"), _n("inoH"), _n("inAm")),
                (_n("ini"), _n("inoH"), p + "izu"),
                (p + "in", _n("inO"), _n("inaH")),
            ]
            return _make_slots(rows)
        else:  # InN
            nom_acc = (p + "i", _n("inI"), _n("Ini"))
            rows = [
                nom_acc,
                nom_acc,
                (_n("inA"), p + "iByAm", p + "iBiH"),
                (_n("ine"), p + "iByAm", p + "iByaH"),
                (_n("inaH"), p + "iByAm", p + "iByaH"),
                (_n("inaH"), _n("inoH"), _n("inAm")),
                (_n("ini"), _n("inoH"), p + "izu"),
                ([p + "in", p + "i"], _n("inI"), _n("Ini")),
            ]
            return _make_slots(rows)

    elif kind in (KrtParadigm.VanM, KrtParadigm.ManN):
        p = w[:-2] if w.endswith("an") else w
        if kind == KrtParadigm.VanM:
            rows = [
                (p + "A", p + "AnO", p + "AnaH"),
                (p + "Anam", p + "AnO", p + "naH"),
                (p + "nA", p + "aByAm", p + "aBiH"),
                (p + "ne", p + "aByAm", p + "aByaH"),
                (p + "naH", p + "aByAm", p + "aByaH"),
                (p + "naH", p + "noH", p + "nAm"),
                ([p + "ni", p + "ani"], p + "noH", p + "asu"),
                (p + "an", p + "AnO", p + "AnaH"),
            ]
            return _make_slots(rows)
        else:  # ManN
            nom_acc = (p + "a", p + "anI", p + "Ani")
            rows = [
                nom_acc,
                nom_acc,
                (p + "nA", p + "aByAm", p + "aBiH"),
                (p + "ne", p + "aByAm", p + "aByaH"),
                (p + "naH", p + "aByAm", p + "aByaH"),
                (p + "naH", p + "noH", p + "nAm"),
                ([p + "ni", p + "ani"], p + "noH", p + "asu"),
                nom_acc,
            ]
            return _make_slots(rows)

    elif kind in (KrtParadigm.Jvs, KrtParadigm.JvsN):
        p = w[:-1] if w.endswith("j") else w
        if kind == KrtParadigm.Jvs:
            nom_acc1 = ([p + "g", p + "k"], p + "jO", p + "jaH")
            rows = [
                nom_acc1,
                (p + "jam", p + "jO", p + "jaH"),
                (p + "jA", p + "gByAm", p + "gBiH"),
                (p + "je", p + "gByAm", p + "gByaH"),
                (p + "jaH", p + "gByAm", p + "gByaH"),
                (p + "jaH", p + "joH", p + "jAm"),
                (p + "ji", p + "joH", p + "kzu"),
                nom_acc1,
            ]
            return _make_slots(rows)
        else:  # JvsN
            nom_acc = ([p + "g", p + "k"], p + "jI", p + "Yji")
            rows = [
                nom_acc,
                nom_acc,
                (p + "jA", p + "gByAm", p + "gBiH"),
                (p + "je", p + "gByAm", p + "gByaH"),
                (p + "jaH", p + "gByAm", p + "gByaH"),
                (p + "jaH", p + "joH", p + "jAm"),
                (p + "ji", p + "joH", p + "kzu"),
                nom_acc,
            ]
            return _make_slots(rows)

    # Fallback to standard nominal decline()
    sub_res = decline(w, gender=linga)
    cells: list[SubantaSlot] = []
    for vib_idx, vib in enumerate(VIBHAKTIS, start=1):
        forms_list = sub_res["forms"].get(vib, [])
        for vac_idx in range(1, 4):
            val = forms_list[vac_idx - 1] if vac_idx - 1 < len(forms_list) else "-"
            f_list = [val] if val != "-" else []
            cells.append(SubantaSlot(vibhakti=vib_idx, vacana=vac_idx, forms=f_list))
    return cells


def krt_table(
    family: str,
    krt: str,
    field: str,
    value: str,
    baseindex: str = "",
) -> Optional[SubantaParadigm]:
    """Exact single paradigm for a kṛdanta form matching `dhaturupa-wasm/src/engine/subanta.rs:krt_table`."""
    field_norm = field.strip().lower()
    if field_norm not in ("m", "f", "n"):
        return None
    linga = Linga(field_norm)

    slot_paradigm = krt_ref_slot(family, krt, field_norm, baseindex)
    if slot_paradigm is None:
        return None

    # Quirk 1: aTuc u-stems typed Bhavat
    if krt == "aTuc" and field_norm == "m":
        cells = atuc_m_table(value)
        if cells is not None:
            return SubantaParadigm(stem=value, linga=linga, class_id=slot_paradigm.value, cells=cells)

    # Citation strip for a-stems
    a_val = value
    if slot_paradigm == KrtParadigm.DevaM and value.endswith("H"):
        a_val = value[:-1]
    elif slot_paradigm == KrtParadigm.PhalaN and value.endswith("m"):
        a_val = value[:-1]

    # Quirk 2: MAlAF / DevIF quirks
    special: Optional[list[SubantaSlot]] = None
    if slot_paradigm == KrtParadigm.MAlAF:
        special = i_value_mala_table(value) or a_short_mala_table(value)
    elif slot_paradigm == KrtParadigm.DevIF:
        special = a_value_devif_table(value) or a_value_table(slot_paradigm, a_val)
    else:
        special = a_value_table(slot_paradigm, a_val)

    if special is not None:
        return SubantaParadigm(stem=value, linga=linga, class_id=slot_paradigm.value, cells=special)

    # Weak stem extraction
    weak = weak_for(slot_paradigm, value)
    if weak is not None:
        cells = decline_krt_reference(slot_paradigm, weak, field_norm)
        return SubantaParadigm(stem=value, linga=linga, class_id=slot_paradigm.value, cells=cells)

    return None


# ---------------------------------------------------------------------------
# Public Bridge Functions
# ---------------------------------------------------------------------------

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
    return [
        "BAvakarma-SAnac", "GaY", "Ramul", "Rvul", "Ryat", "Satf", "ac",
        "anIyar", "cAnaS", "gsnu", "kta", "ktavatu", "ktin", "ktvA", "kvasu",
        "lyap", "lyuw", "sya-BAvakarma-SAnac", "sya-SAnac", "sya-Satf",
        "tavya", "tfc", "tumun", "ukaY", "vun", "yat",
    ]


def _slots_to_forms_dict(cells: list[SubantaSlot]) -> dict[str, list[str]]:
    """Convert 24 SubantaSlots to standard forms dict with vibhakti keys."""
    res: dict[str, list[str]] = {}
    for vib in VIBHAKTIS:
        v_idx = VIBHAKTI_INDEX[vib]
        vac_forms: list[str] = []
        for vac_idx in range(1, 4):
            slot = next((c for c in cells if c.vibhakti == v_idx and c.vacana == vac_idx), None)
            if slot and slot.forms:
                # Store primary or slash-joined string
                vac_forms.append(" / ".join(slot.forms))
            else:
                vac_forms.append("-")
        res[vib] = vac_forms
    return res


def _decline_participle_gender(
    base: str,
    m: str,
    f: str,
    n: str,
    gender: str,
    pratyaya: str = "",
    dhatu_id: str = "",
    family: str = "krut",
) -> dict[str, Any]:
    """Decline a specific gender using the exact Ashtadhyayi reference matrix."""
    g = gender.lower().strip()
    val = m if g == "m" else (f if g == "f" else n)
    if not val and base:
        val = base

    # First try exact krt_table
    if val and pratyaya:
        # If the pratyaya is a known nitya-linga affix in this family (e.g. 'a' in san/yang is feminine-only),
        # prevent leaking to fallback heuristics in other genders.
        any_slot = any(krt_ref_slot(family, pratyaya, x, dhatu_id) is not None for x in ("m", "f", "n"))
        this_slot = krt_ref_slot(family, pratyaya, g, dhatu_id)
        if any_slot and this_slot is None:
            raise ValueError(f"Pratyaya '{pratyaya}' does not decline in gender '{g}'")

        # If alternants in value, take first for primary declension
        first_val = val.split("/")[0].strip()
        tab = krt_table(family, pratyaya, g, first_val, dhatu_id)
        if tab is not None:
            forms_dict = _slots_to_forms_dict(tab.cells)
            return {
                "word": first_val,
                "paradigm": tab.class_id,
                "forms": forms_dict,
                "paradigm_obj": tab,
            }

    # Fallback to classical subanta.decline heuristics
    if g == "m":
        if base.endswith("vat"):
            return decline(base, gender="m", paradigm="vat_m")
        elif base.endswith("mat"):
            return decline(base, gender="m", paradigm="mat_m")
        elif base.endswith("tf"):
            return decline(base, gender="m", paradigm="tf_m")
        elif base.endswith("vas"):
            return decline(base, gender="m", paradigm="vas_m")
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

    elif g == "f":
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

    elif g == "n":
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

    raise ValueError(f"Invalid gender '{gender}'. Must be 'm', 'f', or 'n'.")


def decline_participle(
    dhatu: str,
    pratyaya: str,
    gender: str | None = None,
    prefix: str = "",
    category: str = "krut",
    variant_idx: int = 0,
    db_path: Path | str | None = None,
    base: str | None = None,
    m: str | None = None,
    f: str | None = None,
    n: str | None = None,
) -> dict[str, Any]:
    """Decline a verbal participle (kṛdanta) across vibhaktis and vacanas.
    
    Supports both database querying (via `dhatu` name/id) and direct memory
    execution (when `base`/`m`/`f`/`n` are provided).
    """
    norm_p = normalize_pratyaya(pratyaya)
    fam_norm = normalize_krut_family(category)

    # Direct memory path (e.g. from test or preloaded data)
    if base is not None or m is not None or f is not None or n is not None:
        base_s = base or ""
        m_s = m or ""
        f_s = f or ""
        n_s = n or ""
        dhatu_id = dhatu if ("." in dhatu or dhatu.isdigit()) else ""
        dhatu_lemma = dhatu

        if norm_p in INDECLINABLE_PRATYAYAS or (not m_s and not f_s and not n_s and base_s):
            return {
                "dhatu": dhatu_lemma,
                "dhatu_id": dhatu_id,
                "pratyaya": norm_p,
                "category": fam_norm,
                "prefix": prefix,
                "is_avyaya": True,
                "form": base_s,
                "forms": {v: [base_s, "-", "-"] if v in ("prathamA", "dvitIyA") else ["-", "-", "-"] for v in VIBHAKTIS},
            }

        if gender and gender.lower() in ("m", "f", "n"):
            g = gender.lower()
            sub_res = _decline_participle_gender(base_s, m_s, f_s, n_s, g, norm_p, dhatu_id, fam_norm)
            return {
                "word": sub_res["word"],
                "dhatu": dhatu_lemma,
                "dhatu_id": dhatu_id,
                "pratyaya": norm_p,
                "category": fam_norm,
                "prefix": prefix,
                "is_avyaya": False,
                "gender": g,
                "stem": sub_res["word"],
                "paradigm": sub_res["paradigm"],
                "forms": sub_res["forms"],
                "paradigm_obj": sub_res.get("paradigm_obj"),
            }

        genders_res: dict[str, dict[str, list[str]]] = {}
        stems_res: dict[str, str] = {}
        paradigms_res: dict[str, str] = {}
        for g in ("m", "f", "n"):
            try:
                sub_res = _decline_participle_gender(base_s, m_s, f_s, n_s, g, norm_p, dhatu_id, fam_norm)
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
            "category": fam_norm,
            "prefix": prefix,
            "is_avyaya": False,
            "genders": genders_res,
            "stems": stems_res,
            "paradigms": paradigms_res,
        }

    # Database query path
    dhatu = dhatu.strip()
    if not dhatu:
        raise ValueError("dhatu required")

    ids = resolve_dhatu_input(dhatu, db_path=db_path)
    if not ids:
        raise KeyError(f"Dhatu '{dhatu}' not found in database")
    dhatu_id = ids[0]

    dhatu_lemma = dhatu
    try:
        info = get_dhatu(dhatu_id, db_path=db_path)
        for inf in info.get("info", []):
            if inf.get("name") == "OpadeSikasvarUpam":
                dhatu_lemma = inf.get("value", dhatu)
                break
    except Exception:
        pass

    part_dict = get_participles(dhatu_id, category=fam_norm, prefix=prefix, db_path=db_path)
    cat_entries = part_dict.get(fam_norm, {}) or part_dict.get(category, {})
    if not cat_entries:
        raise KeyError(f"No {fam_norm} participles found for dhatu {dhatu_id} ({dhatu_lemma})")

    if norm_p == "kRtya":
        results = {}
        for kp in ("tavya", "anIyar", "yat", "Ryat", "kyap"):
            if kp in cat_entries:
                results[kp] = decline_participle(dhatu, kp, gender=gender, prefix=prefix, category=category, db_path=db_path)
        if not results:
            raise KeyError(f"No kRtya participles found for {dhatu_id}")
        return {
            "word": f"{dhatu_lemma}+kRtya",
            "dhatu": dhatu_lemma,
            "dhatu_id": dhatu_id,
            "pratyaya": "kRtya",
            "category": fam_norm,
            "prefix": prefix,
            "is_collection": True,
            "participles": results,
            "type": "participle_collection",
            "desc": f"kRtya participles of {dhatu_lemma} ({', '.join(results.keys())})",
        }

    if norm_p not in cat_entries:
        available = sorted(cat_entries.keys())
        raise KeyError(f"Pratyaya '{pratyaya}' not found for {dhatu_id}. Available: {', '.join(available)}")

    variants = cat_entries[norm_p]
    if not variants:
        raise ValueError(f"No entries found for {norm_p} in {dhatu_id}")
    if variant_idx >= len(variants):
        variant_idx = 0
    row = variants[variant_idx]

    base_s = row.get("base", "").strip()
    m_s = row.get("m", "").strip()
    f_s = row.get("f", "").strip()
    n_s = row.get("n", "").strip()

    if norm_p in INDECLINABLE_PRATYAYAS or (not m_s and not f_s and not n_s and base_s):
        return {
            "dhatu": dhatu_lemma,
            "dhatu_id": dhatu_id,
            "pratyaya": norm_p,
            "category": fam_norm,
            "prefix": prefix,
            "is_avyaya": True,
            "form": base_s,
            "type": "participle",
            "desc": f"indeclinable participle {norm_p} of {dhatu_lemma}",
            "forms": {v: [base_s, "-", "-"] if v in ("prathamA", "dvitIyA") else ["-", "-", "-"] for v in VIBHAKTIS},
        }

    if gender and gender.lower() in ("m", "f", "n"):
        g = gender.lower()
        sub_res = _decline_participle_gender(base_s, m_s, f_s, n_s, g, norm_p, dhatu_id, fam_norm)
        return {
            "word": f"{dhatu_lemma}+{norm_p}",
            "dhatu": dhatu_lemma,
            "dhatu_id": dhatu_id,
            "pratyaya": norm_p,
            "category": fam_norm,
            "prefix": prefix,
            "is_avyaya": False,
            "gender": g,
            "stem": sub_res["word"],
            "paradigm": sub_res["paradigm"],
            "forms": sub_res["forms"],
            "paradigm_obj": sub_res.get("paradigm_obj"),
            "type": "participle",
            "desc": f"participle {norm_p} of {dhatu_lemma} ({g})",
            "all_variants": variants if len(variants) > 1 else None,
        }

    genders_res = {}
    stems_res = {}
    paradigms_res = {}
    for g in ("m", "f", "n"):
        try:
            sub_res = _decline_participle_gender(base_s, m_s, f_s, n_s, g, norm_p, dhatu_id, fam_norm)
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
        "category": fam_norm,
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
