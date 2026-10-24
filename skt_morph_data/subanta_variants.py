"""Subanta variant generators for irregular, pronominal, and alternate nominal classes.
Directly implements the Rust reference classes from dhaturupa-wasm/src/engine/subanta.rs:
AMo, ANo, AAFS, PronFlavour, OPlur, IIM2, UUM2, As variants, Has variants, Zam variants, etc.
"""

from __future__ import annotations

from typing import Optional, Callable
from .subanta import Linga, SubantaSlot, VIBHAKTIS, VACANAS, VIBHAKTI_INDEX, VACANA_INDEX, apply_natva
from .subanta_data import A_SARVANAMA, O_PLURALS, SITE_GRIDS


def _make_table(rows: list[tuple[str | list[str], str | list[str], str | list[str]]]) -> list[SubantaSlot]:
    """Helper to construct 24 SubantaSlot objects from 8 (eka, dvi, bahu) tuples."""
    cells: list[SubantaSlot] = []
    for vib_i, row in enumerate(rows):
        vib_idx = vib_i + 1
        for vac_i, col in enumerate(row):
            vac_idx = vac_i + 1
            if isinstance(col, list):
                forms = [apply_natva(f) for f in col]
            else:
                forms = [apply_natva(col)] if col and col != "-" else []
            cells.append(SubantaSlot(vibhakti=vib_idx, vacana=vac_idx, forms=forms))
    return cells


def _put(cells: list[SubantaSlot], row: int, col: int, forms: list[str]) -> None:
    """Set the forms for a specific cell index (row 0-7, col 0-2)."""
    idx = row * 3 + col
    cells[idx] = SubantaSlot(vibhakti=row + 1, vacana=col + 1, forms=[apply_natva(f) for f in forms])

def generate_asm_tables(stem: str, linga: str) -> list[tuple[str, list[SubantaSlot]]]:
    """Generate pure sarvanama tables matching Rust Class::AsmM, AsmN, AsmF."""
    results: list[tuple[str, list[SubantaSlot]]] = []
    if linga == "m" and stem.endswith("a"):
        p = stem[:-1]
        cells = _make_table([
            (p + "aH", p + "O", p + "e"),
            (p + "am", p + "O", p + "An"),
            (p + "ena", p + "AByAm", p + "EH"),
            (p + "asmE", p + "AByAm", p + "eByaH"),
            ([p + "asmAd", p + "asmAt"], p + "AByAm", p + "eByaH"),
            (p + "asya", p + "ayoH", p + "ezAm"),
            (p + "asmin", p + "ayoH", p + "ezu"),
            (stem, p + "O", p + "e"),
        ])
        results.append(("asm-m", cells))
    elif linga == "n" and stem.endswith("a"):
        p = stem[:-1]
        cells = _make_table([
            (p + "am", p + "e", p + "Ani"),
            (p + "am", p + "e", p + "Ani"),
            (p + "ena", p + "AByAm", p + "EH"),
            (p + "asmE", p + "AByAm", p + "eByaH"),
            ([p + "asmAd", p + "asmAt"], p + "AByAm", p + "eByaH"),
            (p + "asya", p + "ayoH", p + "ezAm"),
            (p + "asmin", p + "ayoH", p + "ezu"),
            (stem, p + "e", p + "Ani"),
        ])
        results.append(("asm-n", cells))
    elif linga == "f" and stem.endswith("A") and len(stem) >= 2:
        p = stem[:-1]
        cells = _make_table([
            (stem, p + "e", p + "AH"),
            (p + "Am", p + "e", p + "AH"),
            (p + "ayA", p + "AByAm", p + "ABiH"),
            (p + "asyE", p + "AByAm", p + "AByaH"),
            (p + "asyAH", p + "AByAm", p + "AByaH"),
            (p + "asyAH", p + "ayoH", p + "AsAm"),
            (p + "asyAm", p + "ayoH", p + "Asu"),
            (p + "e", p + "e", p + "AH"),
        ])
        results.append(("asm-f", cells))
    return results
# ---------------------------------------------------------------------------
def generate_amo_tables(stem: str, linga: str = "m") -> list[tuple[str, list[SubantaSlot]]]:
    """Generate all 9 AMo variant tables for masculine a-stems in A_SARVANAMA."""
    if linga != "m" or not stem.endswith("a") or stem not in A_SARVANAMA:
        return []
    p = stem[:-1]
    results: list[tuple[str, list[SubantaSlot]]] = []
    opts = ["e", "en", "en-sm", "comp", "comps", "sm-pairs", "sm", "sm-e", "sm-en"]

    for opt in opts:
        cells = _make_table([
            (p + "aH", p + "O", [p + "AH", p + "e"]),
            (p + "am", p + "O", p + "An"),
            (p + "ena", p + "AByAm", p + "EH"),
            (p + "Aya", p + "AByAm", p + "eByaH"),
            ([p + "Ad", p + "At"], p + "AByAm", p + "eByaH"),
            (p + "asya", p + "ayoH", p + "AnAm"),
            (p + "e", p + "ayoH", p + "ezu"),
            (stem, p + "O", [p + "AH", p + "e"]),
        ])
        if opt == "e":
            pass
        elif opt == "en":
            _put(cells, 2, 0, [p + "eRa"])
            _put(cells, 5, 2, [p + "ARAm"])
        elif opt == "en-sm":
            _put(cells, 2, 0, [p + "eRa"])
            _put(cells, 3, 0, [p + "asmE"])
            _put(cells, 4, 0, [p + "Ad", p + "asmAd", p + "asmAt", p + "At"])
            _put(cells, 5, 2, [p + "ezAm"])
            _put(cells, 6, 0, [p + "e", p + "asmin"])
        elif opt in ("comp", "comps"):
            _put(cells, 0, 2, [p + "e"])
            _put(cells, 7, 2, [p + "e"])
            if opt != "comps":
                _put(cells, 2, 0, [p + "eRa"])
            _put(cells, 3, 0, [p + "asmE"])
            _put(cells, 4, 0, [p + "asmAd", p + "asmAt"])
            _put(cells, 5, 2, [p + "ezAm"])
            _put(cells, 6, 0, [p + "asmin"])
        elif opt == "sm-pairs":
            _put(cells, 0, 2, [p + "AH"])
            _put(cells, 7, 2, [p + "AH"])
            _put(cells, 3, 0, [p + "Aya", p + "asmE"])
            _put(cells, 4, 0, [p + "Ad", p + "asmAd", p + "asmAt", p + "At"])
            _put(cells, 6, 0, [p + "e", p + "asmin"])
        elif opt == "sm":
            _put(cells, 3, 0, [p + "asmE"])
            _put(cells, 4, 0, [p + "asmAd", p + "asmAt"])
            _put(cells, 5, 2, [p + "ezAm"])
            _put(cells, 6, 0, [p + "asmin"])
        elif opt == "sm-e":
            _put(cells, 3, 0, [p + "asmE"])
            _put(cells, 4, 0, [p + "Ad", p + "asmAd", p + "asmAt", p + "At"])
            _put(cells, 5, 2, [p + "ezAm"])
            _put(cells, 6, 0, [p + "e", p + "asmin"])
        elif opt == "sm-en":
            _put(cells, 0, 2, [p + "e"])
            _put(cells, 7, 2, [p + "e"])
            _put(cells, 2, 0, [p + "eRa"])
            _put(cells, 3, 0, [p + "asmE"])
            _put(cells, 4, 0, [p + "asmAd", p + "asmAt"])
            _put(cells, 5, 2, [p + "ezAm"])
            _put(cells, 6, 0, [p + "asmin"])

        results.append((f"a-m-{opt}", cells))
    return results


# ---------------------------------------------------------------------------
# ANo: Neuter a-stems with optional sarvanama flavours (5 flavours)
# ---------------------------------------------------------------------------
def generate_ano_tables(stem: str, linga: str = "n") -> list[tuple[str, list[SubantaSlot]]]:
    """Generate all 5 ANo variant tables for neuter a-stems in A_SARVANAMA."""
    if linga != "n" or not stem.endswith("a") or stem not in A_SARVANAMA:
        return []
    p = stem[:-1]
    results: list[tuple[str, list[SubantaSlot]]] = []
    opts = ["a", "comp", "comps", "sm-pairs", "t"]

    for opt in opts:
        cells = _make_table([
            (p + "am", p + "e", p + "Ani"),
            (p + "am", p + "e", p + "Ani"),
            (p + "ena", p + "AByAm", p + "EH"),
            (p + "Aya", p + "AByAm", p + "eByaH"),
            ([p + "Ad", p + "At"], p + "AByAm", p + "eByaH"),
            (p + "asya", p + "ayoH", p + "AnAm"),
            (p + "e", p + "ayoH", p + "ezu"),
            (stem, p + "e", p + "Ani"),
        ])
        if opt == "a":
            _put(cells, 2, 0, [p + "eRa"])
            _put(cells, 3, 0, [p + "asmE"])
            _put(cells, 4, 0, [p + "Ad", p + "asmAd", p + "asmAt", p + "At"])
            _put(cells, 5, 2, [p + "ezAm"])
            _put(cells, 6, 0, [p + "e", p + "asmin"])
        elif opt in ("comp", "comps"):
            pair = [p + "ad", p + "at"]
            _put(cells, 0, 0, pair)
            _put(cells, 1, 0, pair)
            _put(cells, 7, 0, pair)
            if opt != "comps":
                _put(cells, 2, 0, [p + "eRa"])
            _put(cells, 3, 0, [p + "asmE"])
            _put(cells, 4, 0, [p + "asmAd", p + "asmAt"])
            _put(cells, 5, 2, [p + "ezAm"])
            _put(cells, 6, 0, [p + "asmin"])
        elif opt == "sm-pairs":
            _put(cells, 3, 0, [p + "Aya", p + "asmE"])
            _put(cells, 4, 0, [p + "Ad", p + "asmAd", p + "asmAt", p + "At"])
            _put(cells, 6, 0, [p + "e", p + "asmin"])
        elif opt == "t":
            _put(cells, 2, 0, [p + "eRa"])
            _put(cells, 3, 0, [p + "asmE"])
            _put(cells, 4, 0, [p + "asmAd", p + "asmAt"])
            _put(cells, 5, 2, [p + "ezAm"])
            _put(cells, 6, 0, [p + "asmin"])

        results.append((f"a-n-{opt}", cells))
    return results


# ---------------------------------------------------------------------------
# AAFS: Feminine A-stems with optional Sya-augment pairs (3 flavours)
# ---------------------------------------------------------------------------
def generate_aafs_tables(stem: str, linga: str = "f") -> list[tuple[str, list[SubantaSlot]]]:
    """Generate the 3 AAFS variant tables for feminine A-stems."""
    if linga != "f" or not stem.endswith("A") or len(stem) < 2:
        return []
    p = stem[:-1]
    results: list[tuple[str, list[SubantaSlot]]] = []

    for opt in ["sy", "sygen", "bare"]:
        cells = _make_table([
            (p + "A", p + "e", p + "AH"),
            (p + "Am", p + "e", p + "AH"),
            (p + "ayA", p + "AByAm", p + "ABiH"),
            (p + "AyE", p + "AByAm", p + "AByaH"),
            (p + "AyAH", p + "AByAm", p + "AByaH"),
            (p + "AyAH", p + "ayoH", p + "AnAm"),
            (p + "AyAm", p + "ayoH", p + "Asu"),
            (p + "e", p + "e", p + "AH"),
        ])
        if opt == "bare":
            bare = p + ("a" if p and p[-1] not in "aAiIuUfFxXeEoO" else "")
            _put(cells, 7, 0, [bare])
        else:
            _put(cells, 3, 0, [p + "AyE", p + "asyE"])
            _put(cells, 4, 0, [p + "AyAH", p + "asyAH"])
            _put(cells, 5, 0, [p + "AyAH", p + "asyAH"])
            _put(cells, 6, 0, [p + "AyAm", p + "asyAm"])
            gen = f"{stem}RAm" if opt == "sygen" else f"{stem}nAm"
            _put(cells, 5, 2, [gen, f"{stem}sAm"])

        results.append((f"A-f-{opt}", cells))
    return results


# ---------------------------------------------------------------------------
# PronFlavour: Compounded pronouns (atiyuzmad, atyasmad, etc.)
# ---------------------------------------------------------------------------
def _yuz_compound_cells(base: str, pstem: str) -> list[SubantaSlot]:
    dual = base + f"{pstem}Am"
    cells = _make_table([
        (base + "tvam", dual, base + "yUyam"),
        (dual, dual, base + f"{pstem}An"),
        (base + f"{pstem}ayA", base + f"{pstem}AByAm", base + f"{pstem}ABiH"),
        (base + "tuByam", base + f"{pstem}AByAm", base + f"{pstem}aByam"),
        ([base + f"{pstem}ad", base + f"{pstem}at"], base + f"{pstem}AByAm", [base + f"{pstem}ad", base + f"{pstem}at"]),
        (base + "tava", base + f"{pstem}ayoH", base + f"{pstem}Akam"),
        (base + f"{pstem}ayi", base + f"{pstem}ayoH", base + f"{pstem}Asu"),
        (base + "tvam", dual, base + "yUyam"),
    ])
    return cells


def _asm_compound_cells(ati: str, sandhi: str, pstem: str) -> list[SubantaSlot]:
    fbase = ati if pstem == "m" else (sandhi if pstem == "Av" else f"{sandhi}a")
    nom_sg = f"{sandhi}aham"
    nom_pl = ati + "vayam"
    dat_sg = ati + "mahyam"
    gen_sg = ati + "mama"
    dual = fbase + f"{pstem}Am"
    cells = _make_table([
        (nom_sg, dual, nom_pl),
        (dual, dual, fbase + f"{pstem}An"),
        (fbase + f"{pstem}ayA", fbase + f"{pstem}AByAm", fbase + f"{pstem}ABiH"),
        (dat_sg, fbase + f"{pstem}AByAm", fbase + f"{pstem}aByam"),
        ([fbase + f"{pstem}ad", fbase + f"{pstem}at"], fbase + f"{pstem}AByAm", [fbase + f"{pstem}ad", fbase + f"{pstem}at"]),
        (gen_sg, fbase + f"{pstem}ayoH", fbase + f"{pstem}Akam"),
        (fbase + f"{pstem}ayi", fbase + f"{pstem}ayoH", fbase + f"{pstem}Asu"),
        (nom_sg, dual, nom_pl),
    ])
    return cells


def generate_pron_compound_tables(stem: str, linga: str) -> list[tuple[str, list[SubantaSlot]]]:
    """Generate compound pronoun tables matching Rust PronFlavour."""
    if linga != "m":
        return []
    results: list[tuple[str, list[SubantaSlot]]] = []
    if stem.endswith("yuzmad") and len(stem) > 6:
        base = stem[:-6]
        results.append(("pron-tv", _yuz_compound_cells(base, "tv")))
        results.append(("pron-yuv", _yuz_compound_cells(base, "yuv")))
        results.append(("pron-yuzm", _yuz_compound_cells(base, "yuzm")))
    elif stem.endswith("asmad") and len(stem) > 5:
        base = stem[:-5]
        if base.endswith("y"):
            rest = base[:-1]
            ati = rest + "i"
            results.append(("pron-ma", _asm_compound_cells(ati, base, "m")))
            results.append(("pron-av", _asm_compound_cells(ati, base, "Av")))
            results.append(("pron-sm", _asm_compound_cells(ati, base, "sm")))
    return results


# ---------------------------------------------------------------------------
# OPlur: Compound plurals (Agastya -> agastayaH per Rust Class::OPlur)
# ---------------------------------------------------------------------------
def generate_oplur_tables(stem: str, linga: str) -> list[tuple[str, list[SubantaSlot]]]:
    """Generate OPlur tables matching Rust Class::OPlur."""
    if linga != "m":
        return []
    match = next(((x, fam) for (s, x, fam) in O_PLURALS if s == stem), None)
    if match is None:
        return []
    x, fam = match
    if fam == "i":
        nom, acc, instr, dat, gen, loc = f"{x}ayaH", f"{x}In", f"{x}iBiH", f"{x}iByaH", f"{x}InAm", f"{x}izu"
    elif fam == "u":
        nom, acc, instr, dat, gen, loc = f"{x}avaH", f"{x}Un", f"{x}uBiH", f"{x}uByaH", f"{x}UnAm", f"{x}uzu"
    else:
        nom, acc, instr, dat, gen, loc = f"{x}AH", f"{x}An", f"{x}EH", f"{x}eByaH", f"{x}AnAm", f"{x}ezu"

    if stem.endswith("i"):
        p = stem[:-1]
        cells = _make_table([
            (p + "iH", p + "I", p + "ayaH"),
            (p + "im", p + "I", p + "In"),
            (p + "inA", p + "iByAm", p + "iBiH"),
            (p + "aye", p + "iByAm", p + "iByaH"),
            (p + "eH", p + "iByAm", p + "iByaH"),
            (p + "eH", p + "yoH", p + "InAm"),
            (p + "O", p + "yoH", p + "izu"),
            (p + "e", p + "I", p + "ayaH"),
        ])
    elif stem.endswith("a"):
        p = stem[:-1]
        cells = _make_table([
            (p + "aH", p + "O", p + "AH"),
            (p + "am", p + "O", p + "An"),
            (p + "ena", p + "AByAm", p + "EH"),
            (p + "Aya", p + "AByAm", p + "eByaH"),
            ([p + "Ad", p + "At"], p + "AByAm", p + "eByaH"),
            (p + "asya", p + "ayoH", p + "AnAm"),
            (p + "e", p + "ayoH", p + "ezu"),
            (stem, p + "O", p + "AH"),
        ])
    else:
        return []

    _put(cells, 0, 2, [nom])
    _put(cells, 1, 2, [acc])
    _put(cells, 2, 2, [instr])
    _put(cells, 3, 2, [dat])
    _put(cells, 4, 2, [dat])
    _put(cells, 5, 2, [apply_natva(gen)])
    _put(cells, 6, 2, [loc])
    _put(cells, 7, 2, [nom])
    # Apply natva to instr.sg and gen.pl
    _put(cells, 2, 0, [apply_natva(cells[6].forms[0])])
    return [(f"oplur-{fam}-{x}", cells)]


# ---------------------------------------------------------------------------
# IIM2: Masculine I-stems in strong-cell flavours (amI, kumArI, agraRI, etc.)
# ---------------------------------------------------------------------------

def retroflex_cluster(base: str) -> str:
    vowels = set("aAiIuUeEoO")
    vowel_idx = -1
    for i in range(len(base) - 1, -1, -1):
        if base[i] in vowels:
            vowel_idx = i
            break
    if vowel_idx <= 0:
        return base
    last = vowel_idx - 1
    target = last - 1 if (base[last] == 'r' and last > 0 and base[last - 1] == 'd') else last
    if base[target] == 's':
        return base[:target] + 'z' + base[target + 1:]
    elif base[target] == 'd':
        return base[:target] + 'D' + base[target + 1:]
    return base

def vriddhi_stem(base: str) -> str:
    chars = list(base)
    for i in range(len(chars) - 1, -1, -1):
        if chars[i] == 'a':
            chars[i] = 'A'
            break
        elif chars[i] == 'i':
            chars[i] = 'I'
            break
        elif chars[i] == 'u':
            chars[i] = 'U'
            break
    return "".join(chars)

def ac_weak(base: str, flavour: str) -> str:
    core = base.rstrip("aAiIuU")
    if flavour == "U":
        head = core[:-1] if core.endswith("v") else core
        return f"{head}Uc"
    elif flavour == "S":
        head = core[:-1] if core.endswith("y") else core
        return f"{head}aSc"
    else:
        head = core
        if head.endswith("y") or head.endswith("v"):
            head = head[:-1]
        return f"{head}Ic"

def ac_weak_o(stem: str) -> str:
    head = stem[:-1]
    if head.endswith("vA"):
        h = head[:-2]
        if h.endswith("a"):
            h = h[:-1]
        head = f"{h}o"
    elif head.endswith("a"):
        head = head[:-1]
    return f"{head}c"

def vas_weak(core: str, neuter: bool = False) -> str:
    q = core[:-1] if core.endswith('v') else core
    if not neuter and q.endswith('i'):
        q = q[:-1]
    if not q:
        return "uz"
    last = q[-1]
    rest = q[:-1]
    mapping = {
        'a': (rest, "oz"), 'A': (rest, "oz"),
        'i': (rest, "yuz"), 'I': (rest, "yuz"),
        'u': (rest, "Uz"), 'U': (rest, "Uz"),
        'f': (rest, "ruz"), 'F': (rest, "ruz"),
        'x': (rest, "luz"), 'X': (rest, "luz"),
        'e': (rest, "ayuz"),
        'E': (rest, "Ayuz"),
        'o': (rest, "avuz"),
        'O': (rest, "Avuz"),
    }
    if last in mapping:
        b, uz = mapping[last]
        return f"{b}{uz}"
    return f"{q}uz"

def _f(b: str, end: str) -> str:
    return f"{b}{end}"

def ha_final_cells(stem: str, pair: list[str], voiced: str, loc: list[str]) -> list[SubantaSlot]:
    cells = _make_table([
        (_f(stem, "aH"), _f(stem, "O"), _f(stem, "aH")),
        (_f(stem, "am"), _f(stem, "O"), _f(stem, "aH")),
        (_f(stem, "A"), _f(voiced, "ByAm"), _f(voiced, "BiH")),
        (_f(stem, "e"), _f(voiced, "ByAm"), _f(voiced, "ByaH")),
        (_f(stem, "aH"), _f(voiced, "ByAm"), _f(voiced, "ByaH")),
        (_f(stem, "aH"), _f(stem, "oH"), _f(stem, "Am")),
        (_f(stem, "i"), _f(stem, "oH"), _f(stem, "su")),
        (_f(stem, "aH"), _f(stem, "O"), _f(stem, "aH")),
    ])
    _put(cells, 0, 0, pair)
    _put(cells, 7, 0, pair)
    _put(cells, 6, 2, loc)
    return cells

# 1. SITE_GRIDS
def generate_site_grid_tables(stem: str, linga: str) -> list[tuple[str, list[SubantaSlot]]]:
    results = []
    for s, l, cells_list in SITE_GRIDS:
        if s == stem and l == linga:
            slots = []
            for i in range(24):
                slots.append(SubantaSlot(vibhakti=(i // 3) + 1, vacana=(i % 3) + 1, forms=list(cells_list[i])))
            results.append(("site-grid", slots))
    return results

# 2. NV2 / IIFN / UUFN
def generate_nv2_tables(stem: str, linga: str) -> list[tuple[str, list[SubantaSlot]]]:
    if linga != "f":
        return []
    results = []
    if stem.endswith("I") and len(stem) >= 2:
        p = stem[:-1]
        # IIFN
        results.append(("IIFN", _make_table([
            (_f(stem, "H"), _f(p, "yO"), _f(p, "yaH")),
            (_f(p, "Im"), _f(p, "yO"), _f(p, "IH")),
            (_f(p, "yA"), _f(p, "IByAm"), _f(p, "IBiH")),
            (_f(p, "yE"), _f(p, "IByAm"), _f(p, "IByaH")),
            (_f(p, "yAH"), _f(p, "IByAm"), _f(p, "IByaH")),
            (_f(p, "yAH"), _f(p, "yoH"), _f(p, "InAm")),
            (_f(p, "yAm"), _f(p, "yoH"), _f(p, "Izu")),
            (_f(p, "i"), _f(p, "yO"), _f(p, "yaH")),
        ])))
        # IIF
        results.append(("IIF", _make_table([
            (stem, _f(p, "yO"), _f(p, "yaH")),
            (_f(p, "Im"), _f(p, "yO"), _f(p, "IH")),
            (_f(p, "yA"), _f(p, "IByAm"), _f(p, "IBiH")),
            (_f(p, "yE"), _f(p, "IByAm"), _f(p, "IByaH")),
            (_f(p, "yAH"), _f(p, "IByAm"), _f(p, "IByaH")),
            (_f(p, "yAH"), _f(p, "yoH"), _f(p, "InAm")),
            (_f(p, "yAm"), _f(p, "yoH"), _f(p, "Izu")),
            (_f(p, "i"), _f(p, "yO"), _f(p, "yaH")),
        ])))
    if stem.endswith("U") and len(stem) >= 2:
        p = stem[:-1]
        # UUFN
        results.append(("UUFN", _make_table([
            (_f(stem, "H"), _f(p, "vO"), _f(p, "vaH")),
            (_f(p, "Um"), _f(p, "vO"), _f(p, "UH")),
            (_f(p, "vA"), _f(p, "UByAm"), _f(p, "UBiH")),
            (_f(p, "vE"), _f(p, "UByAm"), _f(p, "UByaH")),
            (_f(p, "vAH"), _f(p, "UByAm"), _f(p, "UByaH")),
            (_f(p, "vAH"), _f(p, "voH"), _f(p, "UnAm")),
            (_f(p, "vAm"), _f(p, "voH"), _f(p, "Uzu")),
            (_f(p, "u"), _f(p, "vO"), _f(p, "vaH")),
        ])))
        # UUF
        results.append(("UUF", _make_table([
            (stem, _f(p, "vO"), _f(p, "vaH")),
            (_f(p, "Um"), _f(p, "vO"), _f(p, "UH")),
            (_f(p, "vA"), _f(p, "UByAm"), _f(p, "UBiH")),
            (_f(p, "vE"), _f(p, "UByAm"), _f(p, "UByaH")),
            (_f(p, "vAH"), _f(p, "UByAm"), _f(p, "UByaH")),
            (_f(p, "vAH"), _f(p, "voH"), _f(p, "UnAm")),
            (_f(p, "vAm"), _f(p, "voH"), _f(p, "Uzu")),
            (_f(p, "u"), _f(p, "vO"), _f(p, "vaH")),
        ])))

    # NV2
    for opt in ("eka", "strong", "strongn", "solo", "vva"):
        if opt == "vva" and not stem.endswith("U"):
            continue
        if stem.endswith("I"):
            p = stem[:-1]
            strong = f"{p}iy"
            voc = f"{p}i"
        elif stem.endswith("U"):
            p = stem[:-1]
            strong = f"{p}v" if opt == "vva" else f"{p}uv"
            voc = f"{p}u"
        elif stem.endswith("i"):
            p = stem[:-1]
            strong = f"{stem}y"
            voc = f"{p}e"
        else:
            continue
        gen = _f(stem, "nAm") if stem.endswith("U") else _f(stem, "RAm")
        cells = _make_table([
            (_f(stem, "H"), _f(strong, "O"), _f(strong, "aH")),
            (_f(strong, "am"), _f(strong, "O"), _f(strong, "aH")),
            (_f(strong, "A"), _f(stem, "ByAm"), _f(stem, "BiH")),
            (_f(strong, "e"), _f(stem, "ByAm"), _f(stem, "ByaH")),
            (_f(strong, "aH"), _f(stem, "ByAm"), _f(stem, "ByaH")),
            (_f(strong, "aH"), _f(strong, "oH"), _f(strong, "Am")),
            (_f(strong, "i"), _f(strong, "oH"), _f(stem, "zu")),
            (voc, _f(strong, "O"), _f(strong, "aH")),
        ])
        if opt == "eka":
            _put(cells, 0, 0, [stem])
            _put(cells, 1, 0, [_f(strong, "am"), _f(stem, "m")])
            _put(cells, 1, 2, [_f(strong, "aH"), _f(stem, "H")])
            _put(cells, 3, 0, [_f(strong, "E")])
            _put(cells, 4, 0, [_f(strong, "AH")])
            _put(cells, 5, 0, [_f(strong, "AH")])
            _put(cells, 5, 2, [gen])
            _put(cells, 6, 0, [_f(strong, "Am")])
            _put(cells, 7, 0, [voc])
        elif opt in ("strong", "strongn"):
            _put(cells, 3, 0, [_f(strong, "e"), _f(strong, "E")])
            _put(cells, 4, 0, [_f(strong, "aH"), _f(strong, "AH")])
            _put(cells, 5, 0, [_f(strong, "aH"), _f(strong, "AH")])
            g = _f(stem, "nAm") if opt == "strongn" else gen
            _put(cells, 5, 2, [_f(strong, "Am"), g])
            _put(cells, 6, 0, [_f(strong, "i"), _f(strong, "Am")])
            _put(cells, 7, 0, [_f(stem, "H")])
        elif opt in ("solo", "vva"):
            _put(cells, 7, 0, [_f(stem, "H")])
        results.append((f"nadi-{opt}", cells))
    return results

# 3. UUM2 fix
def generate_uum2_tables_fixed(stem: str, linga: str) -> list[tuple[str, list[SubantaSlot]]]:
    if linga != "m" or not stem.endswith("U"):
        return []
    p = stem[:-1]
    v = f"{p}v"
    results = []
    # UUM
    uum_cells = _make_table([
        (_f(stem, "H"), _f(p, "uvO"), _f(p, "uvaH")),
        (_f(p, "uvam"), _f(p, "uvO"), _f(p, "uvaH")),
        (_f(p, "uvA"), _f(stem, "ByAm"), _f(stem, "BiH")),
        (_f(p, "uve"), _f(stem, "ByAm"), _f(stem, "ByaH")),
        (_f(p, "uvaH"), _f(stem, "ByAm"), _f(stem, "ByaH")),
        (_f(p, "uvaH"), _f(p, "uvoH"), _f(p, "uvAm")),
        (_f(p, "uvi"), _f(p, "uvoH"), _f(stem, "zu")),
        (_f(stem, "H"), _f(p, "uvO"), _f(p, "uvaH")),
    ])
    results.append(("U-m", uum_cells))
    # UUM2 vva and vvau
    for opt in ("vva", "vvau"):
        acc_sg, acc_pl = (_f(v, "am"), _f(v, "aH")) if opt == "vva" else (_f(stem, "m"), _f(stem, "n"))
        cells = _make_table([
            (_f(stem, "H"), _f(v, "O"), _f(v, "aH")),
            (acc_sg, _f(v, "O"), acc_pl),
            (_f(v, "A"), _f(stem, "ByAm"), _f(stem, "BiH")),
            (_f(v, "e"), _f(stem, "ByAm"), _f(stem, "ByaH")),
            (_f(v, "aH"), _f(stem, "ByAm"), _f(stem, "ByaH")),
            (_f(v, "aH"), _f(v, "oH"), _f(v, "Am")),
            (_f(v, "i"), _f(v, "oH"), _f(stem, "zu")),
            (_f(stem, "H"), _f(v, "O"), _f(v, "aH")),
        ])
        results.append((f"U-m-{opt}", cells))
    return results

# 4. JasM / AjjM / Jvs / JvsN
def generate_jasm_tables(stem: str, linga: str) -> list[tuple[str, list[SubantaSlot]]]:
    if not stem.endswith("j"):
        return []
    p = stem[:-1]
    results = []
    if linga == "m":
        # JasM
        voiced = _f(p, "q")
        pause = _f(p, "w")
        cells = _make_table([
            ([voiced, pause], _f(stem, "O"), _f(stem, "aH")),
            (_f(stem, "am"), _f(stem, "O"), _f(stem, "aH")),
            (_f(stem, "A"), _f(voiced, "ByAm"), _f(voiced, "BiH")),
            (_f(stem, "e"), _f(voiced, "ByAm"), _f(voiced, "ByaH")),
            (_f(stem, "aH"), _f(voiced, "ByAm"), _f(voiced, "ByaH")),
            (_f(stem, "aH"), _f(stem, "oH"), _f(stem, "Am")),
            (_f(stem, "i"), _f(stem, "oH"), [_f(p, "wsu"), _f(p, "wtsu")]),
            ([voiced, pause], _f(stem, "O"), _f(stem, "aH")),
        ])
        results.append(("jas-m", cells))
        # AjjM
        if stem.endswith("nj") and len(stem) >= 4:
            b = stem[:-2]
            cells_ajj = _make_table([
                (_f(b, "n"), _f(b, "YjO"), _f(b, "YjaH")),
                (_f(b, "Yjam"), _f(b, "YjO"), _f(b, "YjaH")),
                (_f(b, "YjA"), _f(f"{b}n", "ByAm"), _f(f"{b}n", "BiH")),
                (_f(b, "Yje"), _f(f"{b}n", "ByAm"), _f(f"{b}n", "ByaH")),
                (_f(b, "YjaH"), _f(f"{b}n", "ByAm"), _f(f"{b}n", "ByaH")),
                (_f(b, "YjaH"), _f(b, "YjoH"), _f(b, "YjAm")),
                (_f(b, "Yji"), _f(b, "YjoH"), [_f(f"{b}n", "su"), _f(b, "ntsu")]),
                (_f(b, "n"), _f(b, "YjO"), _f(b, "YjaH")),
            ])
            results.append(("ajj-m", cells_ajj))
        # Jvs
        cells_jvs = _make_table([
            ([_f(p, "g"), _f(p, "k")], _f(stem, "O"), _f(stem, "aH")),
            (_f(stem, "am"), _f(stem, "O"), _f(stem, "aH")),
            (_f(stem, "A"), _f(p, "gByAm"), _f(p, "gBiH")),
            (_f(stem, "e"), _f(p, "gByAm"), _f(p, "gByaH")),
            (_f(stem, "aH"), _f(p, "gByAm"), _f(p, "gByaH")),
            (_f(stem, "aH"), _f(stem, "oH"), _f(stem, "Am")),
            (_f(stem, "i"), _f(stem, "oH"), _f(p, "kzu")),
            ([_f(p, "g"), _f(p, "k")], _f(stem, "O"), _f(stem, "aH")),
        ])
        results.append(("j-m/f", cells_jvs))
    elif linga == "f":
        cells_jvs = _make_table([
            ([_f(p, "g"), _f(p, "k")], _f(stem, "O"), _f(stem, "aH")),
            (_f(stem, "am"), _f(stem, "O"), _f(stem, "aH")),
            (_f(stem, "A"), _f(p, "gByAm"), _f(p, "gBiH")),
            (_f(stem, "e"), _f(p, "gByAm"), _f(p, "gByaH")),
            (_f(stem, "aH"), _f(p, "gByAm"), _f(p, "gByaH")),
            (_f(stem, "aH"), _f(stem, "oH"), _f(stem, "Am")),
            (_f(stem, "i"), _f(stem, "oH"), _f(p, "kzu")),
            ([_f(p, "g"), _f(p, "k")], _f(stem, "O"), _f(stem, "aH")),
        ])
        results.append(("j-m/f", cells_jvs))
    elif linga == "n":
        cells_jvsn = _make_table([
            ([_f(p, "g"), _f(p, "k")], _f(stem, "I"), _f(p, "Yji")),
            ([_f(p, "g"), _f(p, "k")], _f(stem, "I"), _f(p, "Yji")),
            (_f(stem, "A"), _f(p, "gByAm"), _f(p, "gBiH")),
            (_f(stem, "e"), _f(p, "gByAm"), _f(p, "gByaH")),
            (_f(stem, "aH"), _f(p, "gByAm"), _f(p, "gByaH")),
            (_f(stem, "aH"), _f(stem, "oH"), _f(stem, "Am")),
            (_f(stem, "i"), _f(stem, "oH"), _f(p, "kzu")),
            ([_f(p, "g"), _f(p, "k")], _f(stem, "I"), _f(p, "Yji")),
        ])
        results.append(("j-n", cells_jvsn))
    return results

# 5. Zam / ZagM / ZamC / ZamF / ZvF
def generate_zamc_tables(stem: str, linga: str) -> list[tuple[str, list[SubantaSlot]]]:
    if not stem.endswith("z"):
        return []
    results = []
    base = stem[:-1]
    if linga == "m":
        # Zam
        b_zam = base[:-1] if base.endswith("k") else base
        voiced = _f(b_zam, "q")
        pause = _f(b_zam, "w")
        cells_zam = _make_table([
            ([voiced, pause], _f(stem, "O"), _f(stem, "aH")),
            (_f(stem, "am"), _f(stem, "O"), _f(stem, "aH")),
            (_f(stem, "A"), _f(voiced, "ByAm"), _f(voiced, "BiH")),
            (_f(stem, "e"), _f(voiced, "ByAm"), _f(voiced, "ByaH")),
            (_f(stem, "aH"), _f(voiced, "ByAm"), _f(voiced, "ByaH")),
            (_f(stem, "aH"), _f(stem, "oH"), _f(stem, "Am")),
            (_f(stem, "i"), _f(stem, "oH"), _f(stem, "su")),
            ([voiced, pause], _f(stem, "O"), _f(stem, "aH")),
        ])
        _put(cells_zam, 6, 2, [_f(b_zam, "wsu"), _f(b_zam, "wtsu")])
        results.append(("zam", cells_zam))
        # ZagM
        if base.endswith("k"):
            v_zag = _f(base[:-1], "g")
            p_zag = base
            loc_zag = [_f(base, "zu")]
        else:
            v_zag = _f(base, "g")
            p_zag = _f(base, "k")
            loc_zag = [_f(base, "kzu")]
        cells_zag = _make_table([
            ([v_zag, p_zag], _f(stem, "O"), _f(stem, "aH")),
            (_f(stem, "am"), _f(stem, "O"), _f(stem, "aH")),
            (_f(stem, "A"), _f(v_zag, "ByAm"), _f(v_zag, "BiH")),
            (_f(stem, "e"), _f(v_zag, "ByAm"), _f(v_zag, "ByaH")),
            (_f(stem, "aH"), _f(v_zag, "ByAm"), _f(v_zag, "ByaH")),
            (_f(stem, "aH"), _f(stem, "oH"), _f(stem, "Am")),
            (_f(stem, "i"), _f(stem, "oH"), loc_zag),
            ([v_zag, p_zag], _f(stem, "O"), _f(stem, "aH")),
        ])
        results.append(("zag-m", cells_zag))
        # ZamC ('C', 'V', 'R')
        vr = vriddhi_stem(base)
        for flv in ('C', 'V', 'R'):
            if flv == 'V':
                nom = _f(vr, "H")
                weak = vr
            elif flv == 'R':
                nom = _f(base[:-1] if base.endswith('r') else base, "H")
                weak = base
            else:
                nom = _f(base, "H")
                weak = base
            bh = weak if weak.endswith('r') else _f(weak, "r")
            cells_zc = _make_table([
                (nom, _f(stem, "O"), _f(stem, "aH")),
                (_f(stem, "am"), _f(stem, "O"), _f(stem, "aH")),
                (_f(stem, "A"), _f(bh, "ByAm"), _f(bh, "BiH")),
                (_f(stem, "e"), _f(bh, "ByAm"), _f(bh, "ByaH")),
                (_f(stem, "aH"), _f(bh, "ByAm"), _f(bh, "ByaH")),
                (_f(stem, "aH"), _f(stem, "oH"), _f(stem, "Am")),
                (_f(stem, "i"), _f(stem, "oH"), _f(stem, "su")),
                (nom, _f(stem, "O"), _f(stem, "aH")),
            ])
            if flv == 'R':
                _put(cells_zc, 6, 2, [_f(base, "zu")])
            else:
                _put(cells_zc, 6, 2, [_f(weak, "Hzu"), _f(weak, "zzu")])
            results.append((f"zam-c-{flv}", cells_zc))
    elif linga == "f":
        # ZamF
        voiced = _f(base, "q")
        pause = _f(base, "w")
        cells_zf = _make_table([
            ([voiced, pause], _f(stem, "O"), _f(stem, "aH")),
            (_f(stem, "am"), _f(stem, "O"), _f(stem, "aH")),
            (_f(stem, "A"), _f(voiced, "ByAm"), _f(voiced, "BiH")),
            (_f(stem, "e"), _f(voiced, "ByAm"), _f(voiced, "ByaH")),
            (_f(stem, "aH"), _f(voiced, "ByAm"), _f(voiced, "ByaH")),
            (_f(stem, "aH"), _f(stem, "oH"), _f(stem, "Am")),
            (_f(stem, "i"), _f(stem, "oH"), _f(stem, "su")),
            ([voiced, pause], _f(stem, "O"), _f(stem, "aH")),
        ])
        _put(cells_zf, 6, 2, [_f(base, "wsu"), _f(base, "wtsu")])
        results.append(("zam-f", cells_zf))
        # ZvF ('i', 'I', 'u')
        short = base[:-1] if base[-1] in "aAiIuUeEoO" else base
        for v in ('i', 'I', 'u'):
            rep_bare = base if v == 'i' else (_f(short, "I") if v == 'I' else _f(short, "U"))
            rep = _f(rep_bare, "H")
            instr = _f(rep_bare, "r")
            cells_zv = _make_table([
                (rep, _f(stem, "O"), _f(stem, "aH")),
                (_f(stem, "am"), _f(stem, "O"), _f(stem, "aH")),
                (_f(stem, "A"), _f(instr, "ByAm"), _f(instr, "BiH")),
                (_f(stem, "e"), _f(instr, "ByAm"), _f(instr, "ByaH")),
                (_f(stem, "aH"), _f(instr, "ByAm"), _f(instr, "ByaH")),
                (_f(stem, "aH"), _f(stem, "oH"), _f(stem, "Am")),
                (_f(stem, "i"), _f(stem, "oH"), _f(stem, "su")),
                (rep, _f(stem, "O"), _f(stem, "aH")),
            ])
            _put(cells_zv, 6, 2, [_f(rep, "zu"), _f(rep_bare, "zzu")])
            results.append((f"zv-f-{v}", cells_zv))
    return results

# 6. Ac variants (AcM2, AccM, AccMV, AcN, AcNV, AncN)
def generate_ac_variants_tables(stem: str, linga: str) -> list[tuple[str, list[SubantaSlot]]]:
    if not stem.endswith("c"):
        return []
    results = []
    base = stem[:-1]
    if linga == "m":
        # AcM2('g')
        vg = _f(base, "g")
        pk = _f(base, "k")
        cells_g = _make_table([
            ([vg, pk], _f(stem, "O"), _f(stem, "aH")),
            (_f(stem, "am"), _f(stem, "O"), _f(stem, "aH")),
            (_f(stem, "A"), _f(vg, "ByAm"), _f(vg, "BiH")),
            (_f(stem, "e"), _f(vg, "ByAm"), _f(vg, "ByaH")),
            (_f(stem, "aH"), _f(vg, "ByAm"), _f(vg, "ByaH")),
            (_f(stem, "aH"), _f(stem, "oH"), _f(stem, "Am")),
            (_f(stem, "i"), _f(stem, "oH"), _f(stem, "su")),
            ([vg, pk], _f(stem, "O"), _f(stem, "aH")),
        ])
        _put(cells_g, 6, 2, [_f(base, "kzu")])
        results.append(("ac-m-g", cells_g))
        # AcM2('q')
        if stem.endswith("Sc") and len(stem) >= 3:
            b_sc = stem[:-2]
            vq = _f(b_sc, "q")
            pw = _f(b_sc, "w")
            cells_q = _make_table([
                ([vq, pw], _f(stem, "O"), _f(stem, "aH")),
                (_f(stem, "am"), _f(stem, "O"), _f(stem, "aH")),
                (_f(stem, "A"), _f(vq, "ByAm"), _f(vq, "BiH")),
                (_f(stem, "e"), _f(vq, "ByAm"), _f(vq, "ByaH")),
                (_f(stem, "aH"), _f(vq, "ByAm"), _f(vq, "ByaH")),
                (_f(stem, "aH"), _f(stem, "oH"), _f(stem, "Am")),
                (_f(stem, "i"), _f(stem, "oH"), _f(stem, "su")),
                ([vq, pw], _f(stem, "O"), _f(stem, "aH")),
            ])
            _put(cells_q, 6, 2, [_f(b_sc, "wsu"), _f(b_sc, "wtsu")])
            results.append(("ac-m-q", cells_q))
        # AccM
        cells_accm = _make_table([
            (_f(base, "N"), _f(base, "YcO"), _f(base, "YcaH")),
            (_f(base, "Ycam"), _f(base, "YcO"), _f(stem, "aH")),
            (_f(stem, "A"), _f(base, "gByAm"), _f(base, "gBiH")),
            (_f(stem, "e"), _f(base, "gByAm"), _f(base, "gByaH")),
            (_f(stem, "aH"), _f(base, "gByAm"), _f(base, "gByaH")),
            (_f(stem, "aH"), _f(stem, "oH"), _f(stem, "Am")),
            (_f(stem, "i"), _f(stem, "oH"), _f(base, "kzu")),
            (_f(base, "N"), _f(base, "YcO"), _f(base, "YcaH")),
        ])
        results.append(("ac-m", cells_accm))
        # AccMV ('I', 'U', 'S')
        for flv in ('I', 'U', 'S'):
            w = ac_weak(base, flv)
            cells_mv = _make_table([
                (_f(base, "N"), _f(base, "YcO"), _f(base, "YcaH")),
                (_f(base, "Ycam"), _f(base, "YcO"), _f(w, "aH")),
                (_f(w, "A"), _f(base, "gByAm"), _f(base, "gBiH")),
                (_f(w, "e"), _f(base, "gByAm"), _f(base, "gByaH")),
                (_f(w, "aH"), _f(base, "gByAm"), _f(base, "gByaH")),
                (_f(w, "aH"), _f(w, "oH"), _f(w, "Am")),
                (_f(w, "i"), _f(w, "oH"), _f(base, "kzu")),
                (_f(base, "N"), _f(base, "YcO"), _f(base, "YcaH")),
            ])
            results.append((f"ac-m-v{flv}", cells_mv))
    elif linga == "n":
        # AcN
        cells_acn = _make_table([
            ([_f(base, "g"), _f(base, "k")], _f(stem, "I"), _f(base, "Yci")),
            ([_f(base, "g"), _f(base, "k")], _f(stem, "I"), _f(base, "Yci")),
            (_f(stem, "A"), _f(base, "gByAm"), _f(base, "gBiH")),
            (_f(stem, "e"), _f(base, "gByAm"), _f(base, "gByaH")),
            (_f(stem, "aH"), _f(base, "gByAm"), _f(base, "gByaH")),
            (_f(stem, "aH"), _f(stem, "oH"), _f(stem, "Am")),
            (_f(stem, "i"), _f(stem, "oH"), _f(base, "kzu")),
            ([_f(base, "g"), _f(base, "k")], _f(stem, "I"), _f(base, "Yci")),
        ])
        results.append(("ac-n", cells_acn))
        # AcNV ('I', 'U', 'S', 'O')
        for flv in ('I', 'U', 'S', 'O'):
            w = ac_weak_o(stem) if flv == 'O' else ac_weak(base, flv)
            cells_nv = _make_table([
                ([_f(base, "g"), _f(base, "k")], _f(w, "I"), _f(base, "Yci")),
                ([_f(base, "g"), _f(base, "k")], _f(w, "I"), _f(base, "Yci")),
                (_f(w, "A"), _f(base, "gByAm"), _f(base, "gBiH")),
                (_f(w, "e"), _f(base, "gByAm"), _f(base, "gByaH")),
                (_f(w, "aH"), _f(base, "gByAm"), _f(base, "gByaH")),
                (_f(w, "aH"), _f(w, "oH"), _f(w, "Am")),
                (_f(w, "i"), _f(w, "oH"), _f(base, "kzu")),
                ([_f(base, "g"), _f(base, "k")], _f(w, "I"), _f(base, "Yci")),
            ])
            results.append((f"ac-n-v{flv}", cells_nv))
        # AncN
        if stem.endswith("nc") and len(stem) >= 3:
            b_nc = stem[:-2]
            ang = _f(b_nc, "N")
            cells_anc = _make_table([
                (ang, _f(b_nc, "YcI"), _f(b_nc, "Yci")),
                (ang, _f(b_nc, "YcI"), _f(b_nc, "Yci")),
                (_f(b_nc, "YcA"), _f(ang, "ByAm"), _f(ang, "BiH")),
                (_f(b_nc, "Yce"), _f(ang, "ByAm"), _f(ang, "ByaH")),
                (_f(b_nc, "YcaH"), _f(ang, "ByAm"), _f(ang, "ByaH")),
                (_f(b_nc, "YcaH"), _f(b_nc, "YcoH"), _f(b_nc, "YcAm")),
                (_f(b_nc, "Yci"), _f(b_nc, "YcoH"), [_f(ang, "zu"), _f(ang, "kzu"), _f(ang, "Kzu")]),
                (ang, _f(b_nc, "YcI"), _f(b_nc, "Yci")),
            ])
            results.append(("anc-n", cells_anc))
    return results

# 7. Has variants
def generate_has_variants_tables(stem: str, linga: str) -> list[tuple[str, list[SubantaSlot]]]:
    if not stem.endswith("h"):
        return []
    results = []
    base = stem[:-1]
    if linga == "m":
        alt = retroflex_cluster(base)
        # HasM
        vq = _f(alt, "q")
        pw = _f(alt, "w")
        cells_hasm = _make_table([
            ([vq, pw], _f(stem, "O"), _f(stem, "aH")),
            (_f(stem, "am"), _f(stem, "O"), _f(stem, "aH")),
            (_f(stem, "A"), _f(vq, "ByAm"), _f(vq, "BiH")),
            (_f(stem, "e"), _f(vq, "ByAm"), _f(vq, "ByaH")),
            (_f(stem, "aH"), _f(vq, "ByAm"), _f(vq, "ByaH")),
            (_f(stem, "aH"), _f(stem, "oH"), _f(stem, "Am")),
            (_f(stem, "i"), _f(stem, "oH"), _f(stem, "su")),
            ([vq, pw], _f(stem, "O"), _f(stem, "aH")),
        ])
        _put(cells_hasm, 6, 2, [_f(alt, "wsu"), _f(alt, "wtsu")])
        results.append(("has-m", cells_hasm))
        # HuhM
        quartet = [_f(alt, "q"), _f(alt, "g"), _f(alt, "k"), _f(alt, "w")]
        bh_pair = [_f(alt, "qByAm"), _f(alt, "gByAm")]
        bhih_pair = [_f(alt, "qBiH"), _f(alt, "gBiH")]
        bhyah_pair = [_f(alt, "qByaH"), _f(alt, "gByaH")]
        loc_huh = [_f(alt, "wsu"), _f(alt, "kzu"), _f(alt, "wtsu")]
        cells_huh = _make_table([
            (quartet, _f(stem, "O"), _f(stem, "aH")),
            (_f(stem, "am"), _f(stem, "O"), _f(stem, "aH")),
            (_f(stem, "A"), bh_pair, bhih_pair),
            (_f(stem, "e"), bh_pair, bhyah_pair),
            (_f(stem, "aH"), bh_pair, bhyah_pair),
            (_f(stem, "aH"), _f(stem, "oH"), _f(stem, "Am")),
            (_f(stem, "i"), _f(stem, "oH"), loc_huh),
            (quartet, _f(stem, "O"), _f(stem, "aH")),
        ])
        results.append(("huh-m", cells_huh))
        # DuhM
        vg = _f(alt, "g")
        pk = _f(alt, "k")
        cells_duhm = _make_table([
            ([vg, pk], _f(stem, "O"), _f(stem, "aH")),
            (_f(stem, "am"), _f(stem, "O"), _f(stem, "aH")),
            (_f(stem, "A"), _f(vg, "ByAm"), _f(vg, "BiH")),
            (_f(stem, "e"), _f(vg, "ByAm"), _f(vg, "ByaH")),
            (_f(stem, "aH"), _f(vg, "ByAm"), _f(vg, "ByaH")),
            (_f(stem, "aH"), _f(stem, "oH"), _f(stem, "Am")),
            (_f(stem, "i"), _f(stem, "oH"), _f(vg, "kzu")),
            ([vg, pk], _f(stem, "O"), _f(stem, "aH")),
        ])
        results.append(("duh-m", cells_duhm))
        # HasVM
        if stem.endswith("quh") and len(stem) >= 5:
            root = base[:-2]
            vrdh = _f(root, "qvAh")
            vrdh_s = _f(root, "qvA")
            v_d = _f(base, "d")
            p_t = _f(base, "t")
            cells_vm = _make_table([
                (_f(vrdh_s, "n"), _f(vrdh, "O"), _f(vrdh, "aH")),
                (_f(vrdh, "am"), _f(vrdh, "O"), _f(stem, "aH")),
                (_f(stem, "A"), _f(v_d, "ByAm"), _f(v_d, "BiH")),
                (_f(stem, "e"), _f(v_d, "ByAm"), _f(v_d, "ByaH")),
                (_f(stem, "aH"), _f(v_d, "ByAm"), _f(v_d, "ByaH")),
                (_f(stem, "aH"), _f(stem, "oH"), _f(stem, "Am")),
                (_f(stem, "i"), _f(stem, "oH"), _f(stem, "su")),
                (_f(root, "qvan"), _f(vrdh, "O"), _f(vrdh, "aH")),
            ])
            _put(cells_vm, 6, 2, [_f(p_t, "su")])
            results.append(("has-vm", cells_vm))
        # HasAM
        if stem.endswith("vAh") and len(base) >= 2:
            head = base[:-2]
            au = _f(head[:-1], "Oh") if head else "Oh"
            alt = retroflex_cluster(base)
            voiced = _f(alt, "q")
            pause = _f(alt, "w")
            cells_am = _make_table([
                ([voiced, pause], _f(stem, "O"), _f(stem, "aH")),
                (_f(stem, "am"), _f(stem, "O"), _f(au, "aH")),
                (_f(au, "A"), _f(voiced, "ByAm"), _f(voiced, "BiH")),
                (_f(au, "e"), _f(voiced, "ByAm"), _f(voiced, "ByaH")),
                (_f(au, "aH"), _f(voiced, "ByAm"), _f(voiced, "ByaH")),
                (_f(au, "aH"), _f(au, "oH"), _f(au, "Am")),
                (_f(au, "i"), _f(au, "oH"), _f(stem, "su")),
                ([voiced, pause], _f(stem, "O"), _f(stem, "aH")),
            ])
            _put(cells_am, 6, 2, [_f(alt, "wsu"), _f(alt, "wtsu")])
            results.append(("has-am", cells_am))
    elif linga == "f":
        # HasF
        results.append(("has-f", ha_final_cells(stem, [_f(base, "d"), _f(base, "t")], _f(base, "d"), [_f(base, "tsu")])))
        # HihF
        results.append(("hih-f", ha_final_cells(stem, [_f(base, "g"), _f(base, "k")], _f(base, "g"), [_f(base, "kzu")])))
        # DuhF
        alt = retroflex_cluster(base)
        results.append(("duh-f", ha_final_cells(stem, [_f(alt, "g"), _f(alt, "k")], _f(alt, "g"), [_f(alt, "kzu")])))
    elif linga == "n":
        # HasN
        if len(base) >= 3:
            root = base[:-2]
            vrdh = _f(root, "qvA")
            vd = _f(base, "d")
            pt = _f(base, "t")
            cells_hasn = _make_table([
                ([vd, pt], _f(base, "hI"), _f(vrdh, "Mhi")),
                ([vd, pt], _f(base, "hI"), _f(vrdh, "Mhi")),
                (_f(stem, "A"), _f(vd, "ByAm"), _f(vd, "BiH")),
                (_f(stem, "e"), _f(vd, "ByAm"), _f(vd, "ByaH")),
                (_f(stem, "aH"), _f(vd, "ByAm"), _f(vd, "ByaH")),
                (_f(stem, "aH"), _f(stem, "oH"), _f(stem, "Am")),
                (_f(stem, "i"), _f(stem, "oH"), _f(stem, "su")),
                ([vd, pt], _f(base, "hI"), _f(vrdh, "Mhi")),
            ])
            _put(cells_hasn, 6, 2, [_f(pt, "su")])
            results.append(("has-n", cells_hasn))
    return results

# 8. As variants
def generate_as_variants_tables(stem: str, linga: str) -> list[tuple[str, list[SubantaSlot]]]:
    if not (stem.endswith("s") or stem.endswith("H")):
        return []
    results = []
    w = stem[:-1] if stem.endswith("H") else stem
    p = w[:-1]
    if linga == "m":
        # AsMV
        if len(w) >= 2:
            q = w[:-2]
            o = f"{q}o"
            cells_mv = _make_table([
                (_f(q, "aH"), _f(w, "O"), _f(w, "aH")),
                (_f(w, "am"), _f(w, "O"), _f(w, "aH")),
                (_f(w, "A"), _f(o, "ByAm"), _f(o, "BiH")),
                (_f(w, "e"), _f(o, "ByAm"), _f(o, "ByaH")),
                (_f(w, "aH"), _f(o, "ByAm"), _f(o, "ByaH")),
                (_f(w, "aH"), _f(w, "oH"), _f(w, "Am")),
                (_f(w, "i"), _f(w, "oH"), [_f(q, "aHsu"), _f(w, "su")]),
                (_f(q, "aH"), _f(w, "O"), _f(w, "aH")),
            ])
            results.append(("asv-m", cells_mv))
        # AsMP
        if len(w) >= 2:
            base = w[:-1]
            vd = _f(base, "d")
            pt = _f(base, "t")
            cells_mp = _make_table([
                ([vd, pt], _f(w, "O"), _f(w, "aH")),
                (_f(w, "am"), _f(w, "O"), _f(w, "aH")),
                (_f(w, "A"), _f(vd, "ByAm"), _f(vd, "BiH")),
                (_f(w, "e"), _f(vd, "ByAm"), _f(vd, "ByaH")),
                (_f(w, "aH"), _f(vd, "ByAm"), _f(vd, "ByaH")),
                (_f(w, "aH"), _f(w, "oH"), _f(w, "Am")),
                (_f(w, "i"), _f(w, "oH"), _f(base, "tsu")),
                ([vd, pt], _f(w, "O"), _f(w, "aH")),
            ])
            results.append(("asp-m", cells_mp))
        # AsMW
        if len(w) >= 2:
            v = vriddhi_stem(w[:-1])
            bh = f"{v}r"
            cells_mw = _make_table([
                (_f(v, "H"), _f(w, "O"), _f(w, "aH")),
                (_f(w, "am"), _f(w, "O"), _f(w, "aH")),
                (_f(w, "A"), _f(bh, "ByAm"), _f(bh, "BiH")),
                (_f(w, "e"), _f(bh, "ByAm"), _f(bh, "ByaH")),
                (_f(w, "aH"), _f(bh, "ByAm"), _f(bh, "ByaH")),
                (_f(w, "aH"), _f(w, "oH"), _f(w, "Am")),
                (_f(w, "i"), _f(w, "oH"), [_f(v, "Hzu"), _f(v, "zzu")]),
                (_f(v, "H"), _f(w, "O"), _f(w, "aH")),
            ])
            results.append(("asw-m", cells_mw))
        # SasV
        if len(w) >= 3:
            base = w[:-1]
            cells_sas = _make_table([
                (_f(base, "H"), _f(w, "O"), _f(w, "aH")),
                (_f(w, "am"), _f(w, "O"), _f(w, "aH")),
                (_f(w, "A"), _f(base, "ByAm"), _f(base, "BiH")),
                (_f(w, "e"), _f(base, "ByAm"), _f(base, "ByaH")),
                (_f(w, "aH"), _f(base, "ByAm"), _f(base, "ByaH")),
                (_f(w, "aH"), _f(w, "oH"), _f(w, "Am")),
                (_f(w, "i"), _f(w, "oH"), [_f(base, "Hsu"), _f(w, "su")]),
                (_f(base, "H"), _f(w, "O"), _f(w, "aH")),
            ])
            results.append(("sas-v", cells_sas))
        # VasM
        if w.endswith("vas") and len(w) >= 3:
            p_vas = w[:-2]
            vams = f"{p_vas}AMs"
            uz = vas_weak(p_vas, False)
            vad = f"{p_vas}ad"
            vat = f"{p_vas}at"
            cells_vas = _make_table([
                (f"{p_vas}An", _f(vams, "O"), _f(vams, "aH")),
                (_f(vams, "am"), _f(vams, "O"), _f(uz, "aH")),
                (_f(uz, "A"), _f(vad, "ByAm"), _f(vad, "BiH")),
                (_f(uz, "e"), _f(vad, "ByAm"), _f(vad, "ByaH")),
                (_f(uz, "aH"), _f(vad, "ByAm"), _f(vad, "ByaH")),
                (_f(uz, "aH"), _f(uz, "oH"), _f(uz, "Am")),
                (_f(uz, "i"), _f(uz, "oH"), _f(vat, "su")),
                (f"{p_vas}an", _f(vams, "O"), _f(vams, "aH")),
            ])
            results.append(("vas-m", cells_vas))
    elif linga == "f":
        # SasV
        if len(w) >= 3:
            base = w[:-1]
            cells_sas = _make_table([
                (_f(base, "H"), _f(w, "O"), _f(w, "aH")),
                (_f(w, "am"), _f(w, "O"), _f(w, "aH")),
                (_f(w, "A"), _f(base, "ByAm"), _f(base, "BiH")),
                (_f(w, "e"), _f(base, "ByAm"), _f(base, "ByaH")),
                (_f(w, "aH"), _f(base, "ByAm"), _f(base, "ByaH")),
                (_f(w, "aH"), _f(w, "oH"), _f(w, "Am")),
                (_f(w, "i"), _f(w, "oH"), [_f(base, "Hsu"), _f(w, "su")]),
                (_f(base, "H"), _f(w, "O"), _f(w, "aH")),
            ])
            results.append(("sas-v", cells_sas))
    elif linga == "n":
        # VasN
        if w.endswith("vas") and len(w) >= 3:
            core = w[:-2]
            vat = f"{core}at"
            vad = f"{core}ad"
            strong = f"{core}AMs"
            uz = vas_weak(core, True)
            cells_vasn = _make_table([
                ([vad, vat], _f(uz, "I"), _f(strong, "i")),
                ([vad, vat], _f(uz, "I"), _f(strong, "i")),
                (_f(uz, "A"), _f(vad, "ByAm"), _f(vad, "BiH")),
                (_f(uz, "e"), _f(vad, "ByAm"), _f(vad, "ByaH")),
                (_f(uz, "aH"), _f(vad, "ByAm"), _f(vad, "ByaH")),
                (_f(uz, "aH"), _f(uz, "oH"), _f(uz, "Am")),
                (_f(uz, "i"), _f(uz, "oH"), _f(vat, "su")),
                ([vad, vat], _f(uz, "I"), _f(strong, "i")),
            ])
            results.append(("vas-n", cells_vasn))
    return results

# 9. DadN (True/False)
def generate_dad_tables(stem: str, linga: str) -> list[tuple[str, list[SubantaSlot]]]:
    if linga != "n" or not stem.endswith("d") or len(stem) < 3:
        return []
    base = stem[:-1]
    pair = [stem, _f(base, "t")]
    results = []
    for ndi in (True, False):
        pl = _f(base, "ndi") if ndi else _f(stem, "i")
        cells = _make_table([
            (pair, _f(stem, "I"), pl),
            (pair, _f(stem, "I"), pl),
            (_f(stem, "A"), _f(stem, "ByAm"), _f(stem, "BiH")),
            (_f(stem, "e"), _f(stem, "ByAm"), _f(stem, "ByaH")),
            (_f(stem, "aH"), _f(stem, "ByAm"), _f(stem, "ByaH")),
            (_f(stem, "aH"), _f(stem, "oH"), _f(stem, "Am")),
            (_f(stem, "i"), _f(stem, "oH"), _f(base, "tsu")),
            (pair, _f(stem, "I"), pl),
        ])
        results.append((f"dad-{'n' if ndi else 'p'}", cells))
    return results

# 10. Rc2 / Sam / RcN
def generate_rc_tables(stem: str, linga: str) -> list[tuple[str, list[SubantaSlot]]]:
    if not stem.endswith("S") or len(stem) < 3:
        return []
    base = stem[:-1]
    results = []
    if linga in ("m", "f"):
        # Rc2
        pair_rc = [_f(base, "g"), _f(base, "k")]
        cells_rc = _make_table([
            (pair_rc, _f(stem, "O"), _f(stem, "aH")),
            (_f(stem, "am"), _f(stem, "O"), _f(stem, "aH")),
            (_f(stem, "A"), _f(base, "gByAm"), _f(base, "gBiH")),
            (_f(stem, "e"), _f(base, "gByAm"), _f(base, "gByaH")),
            (_f(stem, "aH"), _f(base, "gByAm"), _f(base, "gByaH")),
            (_f(stem, "aH"), _f(stem, "oH"), _f(stem, "Am")),
            (_f(stem, "i"), _f(stem, "oH"), _f(base, "kzu")),
            (pair_rc, _f(stem, "O"), _f(stem, "aH")),
        ])
        results.append(("rc-2", cells_rc))
        # Sam
        pair_sam = [_f(base, "q"), _f(base, "w")]
        cells_sam = _make_table([
            (pair_sam, _f(stem, "O"), _f(stem, "aH")),
            (_f(stem, "am"), _f(stem, "O"), _f(stem, "aH")),
            (_f(stem, "A"), _f(base, "qByAm"), _f(base, "qBiH")),
            (_f(stem, "e"), _f(base, "qByAm"), _f(base, "qByaH")),
            (_f(stem, "aH"), _f(base, "qByAm"), _f(base, "qByaH")),
            (_f(stem, "aH"), _f(stem, "oH"), _f(stem, "Am")),
            (_f(stem, "i"), _f(stem, "oH"), [_f(base, "wsu"), _f(base, "wtsu")]),
            (pair_sam, _f(stem, "O"), _f(stem, "aH")),
        ])
        results.append(("sam", cells_sam))
    elif linga == "n":
        pair_rcn = [_f(base, "g"), _f(base, "K"), _f(base, "k")]
        pl = _f(base, "MSi")
        cells_rcn = _make_table([
            (pair_rcn, _f(stem, "I"), pl),
            (pair_rcn, _f(stem, "I"), pl),
            (_f(stem, "A"), _f(base, "gByAm"), _f(base, "gBiH")),
            (_f(stem, "e"), _f(base, "gByAm"), _f(base, "gByaH")),
            (_f(stem, "aH"), _f(base, "gByAm"), _f(base, "gByaH")),
            (_f(stem, "aH"), _f(stem, "oH"), _f(stem, "Am")),
            (_f(stem, "i"), _f(stem, "oH"), _f(base, "kzu")),
            (pair_rcn, _f(stem, "I"), pl),
        ])
        results.append(("rc-n", cells_rcn))
    return results

# 11. BaraM ('l' / 'R')
def generate_baram_tables(stem: str, linga: str) -> list[tuple[str, list[SubantaSlot]]]:
    if linga != "m" or len(stem) < 3:
        return []
    last = stem[-1]
    if last not in ('l', 'R'):
        return []
    base = stem[:-1]
    voiced = stem
    loc = [_f(base, "lzu")] if last == 'l' else [_f(base, "Rsu"), _f(base, "Rwsu"), _f(base, "RWsu")]
    cells = _make_table([
        (stem, _f(stem, "O"), _f(stem, "aH")),
        (_f(stem, "am"), _f(stem, "O"), _f(stem, "aH")),
        (_f(stem, "A"), _f(voiced, "ByAm"), _f(voiced, "BiH")),
        (_f(stem, "e"), _f(voiced, "ByAm"), _f(voiced, "ByaH")),
        (_f(stem, "aH"), _f(voiced, "ByAm"), _f(voiced, "ByaH")),
        (_f(stem, "aH"), _f(stem, "oH"), _f(stem, "Am")),
        (_f(stem, "i"), _f(stem, "oH"), loc),
        (stem, _f(stem, "O"), _f(stem, "aH")),
    ])
    return [(f"bara-m-{last}", cells)]

# 12. TaN2 ('D', 'P', 'A')
def generate_tan2_tables(stem: str, linga: str) -> list[tuple[str, list[SubantaSlot]]]:
    if linga != "n" or not stem.endswith("t") or len(stem) < 3:
        return []
    base = stem[:-1]
    voiced = _f(base, "d")
    results = []
    for flv in ('D', 'P', 'A'):
        if flv == 'P':
            pl = [_f(base, "nti"), _f(stem, "i")]
        elif flv == 'A':
            b = base[:-1] if base.endswith('a') else base
            pl = [_f(b, "Anti")]
        else:
            pl = [_f(base, "nti")]
        dual = [_f(base, "ntI"), _f(stem, "I")] if flv == 'D' else [_f(stem, "I")]
        cells = _make_table([
            ([voiced, stem], dual, pl),
            ([voiced, stem], dual, pl),
            (_f(stem, "A"), _f(voiced, "ByAm"), _f(voiced, "BiH")),
            (_f(stem, "e"), _f(voiced, "ByAm"), _f(voiced, "ByaH")),
            (_f(stem, "aH"), _f(voiced, "ByAm"), _f(voiced, "ByaH")),
            (_f(stem, "aH"), _f(stem, "oH"), _f(stem, "Am")),
            (_f(stem, "i"), _f(stem, "oH"), _f(base, "tsu")),
            ([voiced, stem], dual, pl),
        ])
        results.append((f"ta-n2-{flv}", cells))
    return results

# 13. Rar / Rir
def generate_rar_tables(stem: str, linga: str) -> list[tuple[str, list[SubantaSlot]]]:
    if not stem.endswith("r") or len(stem) < 3:
        return []
    base = stem[:-1]
    results = []
    if linga == "f":
        aa = _f(base, "H") if base.endswith("A") else _f(base, "aH")
        cells_rar = _make_table([
            (aa, _f(stem, "O"), _f(stem, "aH")),
            (_f(stem, "am"), _f(stem, "O"), _f(stem, "aH")),
            (_f(stem, "A"), _f(base, "rByAm"), _f(base, "rBiH")),
            (_f(stem, "e"), _f(base, "rByAm"), _f(base, "rByaH")),
            (_f(stem, "aH"), _f(base, "rByAm"), _f(base, "rByaH")),
            (_f(stem, "aH"), _f(stem, "oH"), _f(stem, "Am")),
            (_f(stem, "i"), _f(stem, "oH"), _f(base, "rzu")),
            (aa, _f(stem, "O"), _f(stem, "aH")),
        ])
        results.append(("rar-f", cells_rar))
        for v in ('i', 'u'):
            long = _f(base[:-1], "I") if v == 'i' and base.endswith('i') else _f(base[:-1], "U")
            cells_rir = _make_table([
                (_f(long, "H"), _f(stem, "O"), _f(stem, "aH")),
                (_f(stem, "am"), _f(stem, "O"), _f(stem, "aH")),
                (_f(stem, "A"), _f(long, "rByAm"), _f(long, "rBiH")),
                (_f(stem, "e"), _f(long, "rByAm"), _f(long, "rByaH")),
                (_f(stem, "aH"), _f(long, "rByAm"), _f(long, "rByaH")),
                (_f(stem, "aH"), _f(stem, "oH"), _f(stem, "Am")),
                (_f(stem, "i"), _f(stem, "oH"), _f(long, "rzu")),
                (_f(long, "H"), _f(stem, "O"), _f(stem, "aH")),
            ])
            results.append((f"rir-f-{v}", cells_rir))
    elif linga == "n":
        aa = _f(base, "H") if base.endswith("A") else _f(base, "aH")
        cells_rarn = _make_table([
            (aa, _f(base, "rI"), _f(stem, "i")),
            (aa, _f(base, "rI"), _f(stem, "i")),
            (_f(stem, "A"), _f(base, "rByAm"), _f(base, "rBiH")),
            (_f(stem, "e"), _f(base, "rByAm"), _f(base, "rByaH")),
            (_f(stem, "aH"), _f(base, "rByAm"), _f(base, "rByaH")),
            (_f(stem, "aH"), _f(stem, "oH"), _f(stem, "Am")),
            (_f(stem, "i"), _f(stem, "oH"), _f(base, "rzu")),
            (aa, _f(base, "rI"), _f(stem, "i")),
        ])
        results.append(("rar-n", cells_rarn))
    return results

# 14. ApM
def generate_apm_tables(stem: str, linga: str) -> list[tuple[str, list[SubantaSlot]]]:
    if linga not in ("m", "f") or not stem.endswith("p") or len(stem) < 2:
        return []
    base = stem[:-1]
    voiced = _f(base, "b")
    fem = f"A{stem[1:]}" if linga == "f" else stem
    nom = [voiced, stem] if linga == "m" else _f(fem, "aH")
    voc = [voiced, stem] if linga == "m" else _f(fem, "aH")
    cells = _make_table([
        (nom, _f(stem, "O"), _f(stem, "aH")),
        (_f(fem, "am"), _f(stem, "O"), _f(stem, "aH")),
        (_f(stem, "A"), _f(voiced, "ByAm"), _f(voiced, "BiH")),
        (_f(stem, "e"), _f(voiced, "ByAm"), _f(voiced, "ByaH")),
        (_f(stem, "aH"), _f(voiced, "ByAm"), _f(voiced, "ByaH")),
        (_f(stem, "aH"), _f(stem, "oH"), _f(stem, "Am")),
        (_f(stem, "i"), _f(stem, "oH"), _f(stem, "su")),
        (voc, _f(stem, "O"), _f(stem, "aH")),
    ])
    return [("ap-m", cells)]

# 15. InV / AnV
def generate_inv_tables(stem: str, linga: str) -> list[tuple[str, list[SubantaSlot]]]:
    results = []
    if linga == "m" and stem.endswith("in") and len(stem) >= 3:
        root = stem[:-2]
        last = root[-1]
        vr = f"{root}AR" if "f" in root else f"{root[:-1]}n{last}An"
        vr_a = vr[:-1]
        cells_inv = _make_table([
            (_f(vr_a, "H"), _f(vr, "O"), _f(vr, "aH")),
            (_f(vr, "am"), _f(vr, "O"), _f(root, "aH")),
            (_f(root, "A"), _f(root, "iByAm"), _f(root, "iBiH")),
            (_f(root, "e"), _f(root, "iByAm"), _f(root, "iByaH")),
            (_f(root, "aH"), _f(root, "iByAm"), _f(root, "iByaH")),
            (_f(root, "aH"), _f(root, "oH"), _f(root, "Am")),
            (_f(root, "i"), _f(root, "oH"), _f(root, "izu")),
            (_f(vr_a, "H"), _f(vr, "O"), _f(vr, "aH")),
        ])
        results.append(("in-m-vr", cells_inv))
    if linga == "m" and stem.endswith("an") and len(stem) >= 4:
        root = stem[:-2]
        strong = f"{root}aR"
        weak = f"{root}R"
        plain = f"{root}a"
        cells_anv = _make_table([
            (_f(root, "A"), _f(strong, "O"), _f(strong, "aH")),
            (_f(strong, "am"), _f(strong, "O"), _f(weak, "aH")),
            (_f(weak, "A"), _f(plain, "ByAm"), _f(plain, "BiH")),
            (_f(weak, "e"), _f(plain, "ByAm"), _f(plain, "ByaH")),
            (_f(weak, "aH"), _f(plain, "ByAm"), _f(plain, "ByaH")),
            (_f(weak, "aH"), _f(weak, "oH"), _f(weak, "Am")),
            ([_f(weak, "i"), _f(strong, "i")], _f(weak, "oH"), _f(plain, "su")),
            (stem, _f(strong, "O"), _f(strong, "aH")),
        ])
        results.append(("an-v", cells_anv))
    return results

# 16. RFA (mAtf, pitf)
def generate_rfa_tables(stem: str, linga: str) -> list[tuple[str, list[SubantaSlot]]]:
    if linga not in ("m", "f") or not stem.endswith("f") or len(stem) < 3:
        return []
    root = stem[:-1]
    if root.endswith("a"):
        root = root[:-1]
    strong = f"{root}ar"
    weak = f"{root}r"
    acc_pl = f"{root}Fn" if linga == "m" else f"{root}FH"
    cells = _make_table([
        (_f(root, "A"), _f(strong, "O"), _f(strong, "aH")),
        (_f(strong, "am"), _f(strong, "O"), acc_pl),
        (_f(weak, "A"), _f(stem, "ByAm"), _f(stem, "BiH")),
        (_f(weak, "e"), _f(stem, "ByAm"), _f(stem, "ByaH")),
        (_f(root, "uH"), _f(stem, "ByAm"), _f(stem, "ByaH")),
        (_f(root, "uH"), _f(weak, "oH"), _f(root, "FRAm")),
        (_f(strong, "i"), _f(weak, "oH"), _f(stem, "zu")),
        (_f(root, "H"), _f(strong, "O"), _f(strong, "aH")),
    ])
    return [("rf-a", cells)]

def jash_voice(base: str) -> str:
    chars = list(base)
    last_idx = -1
    for i in range(len(chars) - 1, -1, -1):
        if chars[i] in ('d', 'b', 'g', 'j'):
            last_idx = i
            break
    if last_idx == -1:
        return base
    voice_map = {'d': 'D', 'b': 'B', 'g': 'G', 'j': 'J'}
    chars[last_idx] = voice_map[chars[last_idx]]
    return "".join(chars)

def an_weak(p: str) -> str:
    if not p:
        return 'keep'
    last = p[-1]
    if last in ('c', 'j'):
        return 'y'
    elif last in ('w', 'D', 'z'):
        return 'drop'
    elif len(p) >= 2 and p[-2] in 'aAiIuUfFxXeEoO':
        return 'drop'
    else:
        return 'keep'

# 2. Consonant stems: Class::Cons
def generate_cons_tables(stem: str, linga: str) -> list[tuple[str, list[SubantaSlot]]]:
    r_chart = stem in ("fc", "fk", "fg")
    if linga not in ("m", "f") or (len(stem) < 3 and not r_chart):
        return []
    if linga == "m" and (stem.endswith("at") or stem.endswith("ant")):
        return []
    c = stem[-1]
    if c in ('t', 'd', 'D', 'T'):
        voiced, middle, voiceless, su_suffix = "d", None, "t", "su"
    elif c == 'B':
        voiced, middle, voiceless, su_suffix = "b", None, "p", "su"
    elif c == 'c':
        if linga == "m":
            return []
        voiced, middle, voiceless, su_suffix = "g", None, "k", "zu"
    elif c == 'S':
        voiced, middle, voiceless, su_suffix = "g", "K", "k", "zu"
    else:
        return []
    base = stem[:-1]
    weak_base = jash_voice(base) if stem.endswith('B') else base
    voiced_stem = _f(weak_base, voiced)
    pausa_stem = _f(weak_base, voiceless)
    dvi_form = _f(stem, "O")
    bahu_form = _f(stem, "aH")
    pair = [voiced_stem]
    if middle:
        pair.append(_f(weak_base, middle))
    pair.append(pausa_stem)
    samb_pair = [_f(weak_base, voiced)]
    if middle:
        samb_pair.append(_f(weak_base, middle))
    samb_pair.append(pausa_stem)
    cells = _make_table([
        (pair, dvi_form, bahu_form),
        (_f(stem, "am"), dvi_form, bahu_form),
        (_f(stem, "A"), _f(voiced_stem, "ByAm"), _f(voiced_stem, "BiH")),
        (_f(stem, "e"), _f(voiced_stem, "ByAm"), _f(voiced_stem, "ByaH")),
        (_f(stem, "aH"), _f(voiced_stem, "ByAm"), _f(voiced_stem, "ByaH")),
        (_f(stem, "aH"), _f(stem, "oH"), _f(stem, "Am")),
        (_f(stem, "i"), _f(stem, "oH"), _f(pausa_stem, su_suffix)),
        (samb_pair, dvi_form, bahu_form),
    ])
    return [("cons", cells)]

# 3. Feminine -an stems: Class::AnF
def generate_anf_tables(stem: str, linga: str) -> list[tuple[str, list[SubantaSlot]]]:
    if linga != "f" or not stem.endswith("an") or len(stem) < 3:
        return []
    p = stem[:-2]
    w = an_weak(p)
    weak = f"{p}Y" if w == "y" else (stem if w == "keep" else f"{p}n")
    an = f"{p}An"
    az = f"{p}a"
    cells = _make_table([
        (_f(p, "A"), _f(an, "O"), _f(an, "aH")),
        (_f(an, "am"), _f(an, "O"), _f(weak, "aH")),
        (_f(weak, "A"), _f(az, "ByAm"), _f(az, "BiH")),
        (_f(weak, "e"), _f(az, "ByAm"), _f(az, "ByaH")),
        (_f(weak, "aH"), _f(az, "ByAm"), _f(az, "ByaH")),
        (_f(weak, "aH"), _f(weak, "oH"), _f(weak, "Am")),
        (_f(weak, "i"), _f(weak, "oH"), _f(az, "su")),
        (stem, _f(an, "O"), _f(an, "aH")),
    ])
    if weak != stem:
        _put(cells, 6, 0, [_f(weak, "i"), _f(stem, "i")])
    return [("an-f", cells)]

# 4. VantM: Class::VantM
def generate_vantm_tables(stem: str, linga: str) -> list[tuple[str, list[SubantaSlot]]]:
    if linga != "m" or len(stem) < 3:
        return []
    letter = None
    for l in ("v", "m", "y"):
        if stem.endswith(f"{l}at"):
            letter = l
            break
    if not letter:
        return []
    p = stem[:-1]
    q = stem[:-3]
    strong = f"{q}{letter}ant"
    d = f"{p}d"
    cells = _make_table([
        (f"{q}{letter}An", _f(strong, "O"), _f(strong, "aH")),
        (_f(strong, "am"), _f(strong, "O"), _f(stem, "aH")),
        (_f(stem, "A"), _f(d, "ByAm"), _f(d, "BiH")),
        (_f(stem, "e"), _f(d, "ByAm"), _f(d, "ByaH")),
        (_f(stem, "aH"), _f(d, "ByAm"), _f(d, "ByaH")),
        (_f(stem, "aH"), _f(stem, "oH"), _f(stem, "Am")),
        (_f(stem, "i"), _f(stem, "oH"), _f(stem, "su")),
        (f"{q}{letter}an", _f(strong, "O"), _f(strong, "aH")),
    ])
    return [("vant-m", cells)]

# 5. AtN: Class::AtN
def generate_atn_tables(stem: str, linga: str) -> list[tuple[str, list[SubantaSlot]]]:
    if linga != "n" or not (stem.endswith("t") or stem.endswith("d")) or len(stem) < 3:
        return []
    w = stem[:-1] + "t" if stem.endswith("d") else stem
    d = w[:-1] + "d"
    strong = w[:-1] + "nt"
    dual = [_f(strong, "I")]
    plural = [_f(strong, "i")]
    cells = _make_table([
        ([d, w], dual, plural),
        ([d, w], dual, plural),
        (_f(w, "A"), _f(d, "ByAm"), _f(d, "BiH")),
        (_f(w, "e"), _f(d, "ByAm"), _f(d, "ByaH")),
        (_f(w, "aH"), _f(d, "ByAm"), _f(d, "ByaH")),
        (_f(w, "aH"), _f(w, "oH"), _f(w, "Am")),
        (_f(w, "i"), _f(w, "oH"), _f(w, "su")),
        ([d, w], dual, plural),
    ])
    return [("at-n", cells)]

# 6. Compound pronouns: Class::Pron(PronFlavour::YuzPara / AsmPara)
YUZMAD_PARA_GRID = [
    ["tvam"], ["yuvAm"], ["yUyam"],
    ["tvAm", "tvA"], ["yuvAm", "vAm"], ["yuzmAn", "vaH"],
    ["tvayA"], ["yuvAByAm"], ["yuzmABiH"],
    ["tuByam", "te"], ["yuvAByAm", "vAm"], ["yuzmaByam", "vaH"],
    ["tvad", "tvat"], ["yuvAByAm"], ["yuzmad", "yuzmat"],
    ["tava", "te"], ["yuvayoH", "vAm"], ["yuzmAkam", "vaH"],
    ["tvayi"], ["yuvayoH"], ["yuzmAsu"],
]

ASMAD_PARA_GRID = [
    ["aham"], ["AvAm"], ["vayam"],
    ["mAm", "mA"], ["AvAm", "nO"], ["asmAn", "naH"],
    ["mayA"], ["AvAByAm"], ["asmABiH"],
    ["mahyam", "me"], ["AvAByAm", "nO"], ["asmaByam", "naH"],
    ["mad", "mat"], ["AvAByAm"], ["asmad", "asmat"],
    ["mama", "me"], ["AvayoH", "nO"], ["asmAkam", "naH"],
    ["mayi"], ["AvayoH"], ["asmAsu"],
]

def para_bases(stem: str):
    if stem.endswith("yuzmad"):
        base = stem[:-len("yuzmad")]
    elif stem.endswith("smad"):
        base = stem[:-len("smad")]
    else:
        return None
    plain = f"{base[:-1]}a" if base.endswith("A") else base
    base_no_a = plain[:-1] if plain.endswith("a") else plain
    sandhi = f"{base_no_a}A"
    return plain, sandhi

def para_form(plain: str, sandhi: str, alt: str) -> str:
    if alt and alt[0] in "aAiIuUfFxXeEoO":
        return f"{sandhi}{alt[1:]}"
    return f"{plain}{alt}"

def generate_para_pronoun_tables(stem: str, linga: str) -> list[tuple[str, list[SubantaSlot]]]:
    if linga != "m":
        return []
    res = para_bases(stem)
    if not res:
        return []
    plain, sandhi = res
    if stem.endswith("yuzmad"):
        grid = YUZMAD_PARA_GRID
        tag = "pron-yuzpara"
    else:
        grid = ASMAD_PARA_GRID
        tag = "pron-asmpara"
    cells = []
    for r in range(7):
        for c in range(3):
            idx = r * 3 + c
            forms = [para_form(plain, sandhi, a) for a in grid[idx]]
            cells.append(SubantaSlot(vibhakti=r+1, vacana=c+1, forms=forms))
    # sambodhana empty
    for c in range(3):
        cells.append(SubantaSlot(vibhakti=8, vacana=c+1, forms=[]))
    return [(tag, cells)]

# 7. Class::AsEM (anehas, uSanas)
def generate_as_em_tables(stem: str, linga: str) -> list[tuple[str, list[SubantaSlot]]]:
    if linga != "m" or not (stem.endswith("s") or stem.endswith("H")) or len(stem) < 2:
        return []
    w = stem[:-1] if stem.endswith("H") else stem
    q = w[:-2]
    o = f"{q}o"
    cells = _make_table([
        (_f(q, "A"), _f(w, "O"), _f(w, "aH")),
        (_f(w, "am"), _f(w, "O"), _f(w, "aH")),
        (_f(w, "A"), _f(o, "ByAm"), _f(o, "BiH")),
        (_f(w, "e"), _f(o, "ByAm"), _f(o, "ByaH")),
        (_f(w, "aH"), _f(o, "ByAm"), _f(o, "ByaH")),
        (_f(w, "aH"), _f(w, "oH"), _f(w, "Am")),
        (_f(w, "i"), _f(w, "oH"), _f(w, "su")),
        (_f(q, "aH"), _f(w, "O"), _f(w, "aH")),
    ])
    _put(cells, 6, 2, [_f(q, "aHsu"), _f(w, "su")])
    return [("as-em", cells)]

# 8. Class::AAN (SrIpA neuter)
def generate_aan_tables(stem: str, linga: str) -> list[tuple[str, list[SubantaSlot]]]:
    if linga != "n" or not stem.endswith("A") or len(stem) < 3:
        return []
    base = stem[:-1]
    cells = _make_table([
        (_f(base, "am"), _f(base, "e"), _f(base, "ARi")),
        (_f(base, "am"), _f(base, "e"), _f(base, "ARi")),
        (_f(base, "eRa"), _f(stem, "ByAm"), _f(base, "EH")),
        (_f(base, "Aya"), _f(stem, "ByAm"), _f(base, "eByaH")),
        ([_f(base, "Ad"), _f(base, "At")], _f(stem, "ByAm"), _f(base, "eByaH")),
        (_f(base, "asya"), _f(base, "ayoH"), _f(base, "ARAm")),
        (_f(base, "e"), _f(base, "ayoH"), _f(base, "ezu")),
        (_f(base, "a"), _f(base, "e"), _f(base, "ARi")),
    ])
    return [("aa-n", cells)]

# 9. Class::InF (mahAjAlin feminine)
def generate_inf_tables(stem: str, linga: str) -> list[tuple[str, list[SubantaSlot]]]:
    if linga != "f" or not stem.endswith("in") or len(stem) < 3:
        return []
    p = stem[:-2]
    strong = f"{p}in"
    weak = f"{p}i"
    cells = _make_table([
        (f"{p}I", _f(strong, "O"), _f(strong, "aH")),
        (_f(strong, "am"), _f(strong, "O"), _f(strong, "aH")),
        (_f(strong, "A"), _f(weak, "ByAm"), _f(weak, "BiH")),
        (_f(strong, "e"), _f(weak, "ByAm"), _f(weak, "ByaH")),
        (_f(strong, "aH"), _f(weak, "ByAm"), _f(weak, "ByaH")),
        (_f(strong, "aH"), _f(strong, "oH"), _f(strong, "Am")),
        (_f(strong, "i"), _f(strong, "oH"), _f(weak, "zu")),
        (stem, _f(strong, "O"), _f(strong, "aH")),
    ])
    return [("in-f", cells)]

# 10. Natva on all variant generators
def generate_nv2_natva_tables(stem: str, linga: str) -> list[tuple[str, list[SubantaSlot]]]:
    raw_tabs = T.generate_nv2_tables(stem, linga)
    fixed = []
    for name, cells in raw_tabs:
        c = copy.deepcopy(cells)
        for slot in c:
            slot.forms = [apply_natva(f) for f in slot.forms]
        fixed.append((name, c))
    return fixed




# ---------------------------------------------------------------------------
# IIM2: Masculine I-stems in strong-cell flavours (amI, kumArI, agraRI, etc.)
# ---------------------------------------------------------------------------
def generate_iim2_tables(stem: str, linga: str) -> list[tuple[str, list[SubantaSlot]]]:
    """Generate IIM2 candidate tables matching Rust Class::IIM2."""
    if linga != "m" or not stem.endswith("I"):
        return []
    p = stem[:-1]
    results: list[tuple[str, list[SubantaSlot]]] = []

    # 1. Plain IIM
    iim_cells = _make_table([
        (stem + "H", p + "yO", p + "yaH"),
        (stem + "m", p + "yO", stem + "n"),
        (p + "yA", stem + "ByAm", stem + "BiH"),
        (p + "ye", stem + "ByAm", stem + "ByaH"),
        (p + "yaH", stem + "ByAm", stem + "ByaH"),
        (p + "yaH", p + "yoH", p + "yAm"),
        (stem, p + "yoH", stem + "zu"),
        (stem + "H", p + "yO", p + "yaH"),
    ])
    results.append(("I-m", iim_cells))

    # 2. Vridhi and VridhiA (strong cells take iy)
    v = p + "iy"
    for opt in ("vridhi", "vridhi-a"):
        loc = v + "Am" if opt == "vridhi-a" else v + "i"
        cells = _make_table([
            (stem + "H", v + "O", v + "aH"),
            (v + "am", v + "O", v + "aH"),
            (v + "A", stem + "ByAm", stem + "BiH"),
            (v + "e", stem + "ByAm", stem + "ByaH"),
            (v + "aH", stem + "ByAm", stem + "ByaH"),
            (v + "aH", v + "oH", v + "Am"),
            (loc, v + "oH", stem + "zu"),
            (stem + "H", v + "O", v + "aH"),
        ])
        results.append((f"I-m-{opt}", cells))

    # 3. Guna variants: guna, gunai, gunau, guna-a, guna-b
    for opt in ("guna", "gunai", "gunau", "guna-a", "guna-b"):
        loc = p + "yAm" if opt in ("guna", "guna-a", "guna-b") else p + "yi"
        cells = _make_table([
            (stem + "H", p + "yO", p + "yaH"),
            (p + "yam", p + "yO", p + "yaH"),
            (p + "yA", stem + "ByAm", stem + "BiH"),
            (p + "ye", stem + "ByAm", stem + "ByaH"),
            (p + "yaH", stem + "ByAm", stem + "ByaH"),
            (p + "yaH", p + "yoH", p + "yAm"),
            (loc, p + "yoH", stem + "zu"),
            (stem + "H", p + "yO", p + "yaH"),
        ])
        if opt == "gunau":
            _put(cells, 4, 0, [p + "yuH"])
            _put(cells, 5, 0, [p + "yuH"])
        if opt in ("guna-a", "guna-b"):
            _put(cells, 3, 0, [p + "yE"])
            _put(cells, 4, 0, [p + "yAH"])
            _put(cells, 5, 0, [p + "yAH"])
            _put(cells, 5, 2, [stem + "nAm"])
            _put(cells, 7, 0, [p + "i"])
        if opt == "guna-b":
            _put(cells, 0, 0, [stem])
        results.append((f"I-m-{opt}", cells))

    return results


ALL_VARIANT_GENERATORS: list[Callable[[str, str], list[tuple[str, list[SubantaSlot]]]]] = [
    generate_site_grid_tables,
    generate_asm_tables,
    generate_amo_tables,
    generate_ano_tables,
    generate_aafs_tables,
    generate_pron_compound_tables,
    generate_oplur_tables,
    generate_iim2_tables,
    generate_uum2_tables_fixed,
    generate_nv2_tables,
    generate_jasm_tables,
    generate_zamc_tables,
    generate_ac_variants_tables,
    generate_has_variants_tables,
    generate_as_variants_tables,
    generate_as_em_tables,
    generate_dad_tables,
    generate_rc_tables,
    generate_baram_tables,
    generate_tan2_tables,
    generate_rar_tables,
    generate_apm_tables,
    generate_inv_tables,
    generate_rfa_tables,
    generate_cons_tables,
    generate_anf_tables,
    generate_vantm_tables,
    generate_atn_tables,
    generate_para_pronoun_tables,
    generate_aan_tables,
    generate_inf_tables,
]
