"""Subanta (nominal) declension engine for Sanskrit.

Provides complete vibhakti tables for:
 - nouns (a/i/u/f etc. stems, masculine/feminine/neuter)
 - pronouns (tad, etad, yad, kim, idam, adas, asmad, yusmad, sarva etc.)
 - numerals (eka, dvi, tri, catur, paJcan, zaz, saptan, azwan, navan, daSan ...)

All inputs/outputs are SLP1 transliteration (like the dhatu DB).
Vocative (sambodhana) is included as 8th vibhakti.

Usage::

    from skt_morph_data.subanta import decline, decline_noun, decline_pronoun, decline_numeral

    decline("rAma", gender="m")          # auto-detect a-stem masculine
    decline("Pala", gender="n")          # neuter a-stem
    decline("nadI", gender="f")          # I-stem feminine
    decline("hari", gender="m")          # i-stem masc
    decline("guru", gender="m")
    decline("pitf", gender="m")
    decline("saH")  # pronoun auto
    decline("eka")  # numeral
    # explicit paradigm
    decline("rAma", paradigm="a_m")

    # CLI: skt-morph decline rAma --gender m --paradigm a_m --json

Paradigm keys (noun):
  a_m, a_n, A_f, i_m/pati_m/sakhi_m, i_f, i_n, I_f, u_m, u_f, u_n, U_f, f_m, f_f, f_n,
  an_m (rAjan), an_n (nAman), in_m (yogin), at_m (Bavat m), at_n (jagat/Bavat n.),
  as_n (manas n), as_m/f (sumanas bahuvrIhi m/f), us_n (danus), is_n (havis), c_f (vAc), t_m/f/n, o_m (go), etc.

Pronoun keys auto-detected if word matches pronoun list; else noun logic.

Tables are based on Siddhanta-Kaumudi / standard paradigms and cover
all 8 vibhaktis × 3 vacanas = 24 forms (with syncretism noted).
"""

from __future__ import annotations

from typing import Any

# ---------------------------------------------------------------------------
# Vibhakti / vacana order
# ---------------------------------------------------------------------------
VIBHAKTIS = ["prathamA", "dvitIyA", "tftIyA", "caturTI", "paYcamI", "zazWI", "saptamI", "saMboDana"]
VACANAS = ["ekavacana", "dvivacana", "bahuvacana"]
# short labels
VIBHAKTI_SHORT = {
    "prathamA": "1",
    "dvitIyA": "2",
    "tftIyA": "3",
    "caturTI": "4",
    "paYcamI": "5",
    "zazWI": "6",
    "saptamI": "7",
    "saMboDana": "voc",
}

# ---------------------------------------------------------------------------
# Helper to build paradigm tables
# Stores suffixes to be added to "base" (stem minus ending).
# For each paradigm we store dict vibhakti -> [eka,dvi,bahu] suffixes
# ---------------------------------------------------------------------------

def _add_base(base: str, suffix: str) -> str:
    # simple concatenation; handles empty base
    return base + suffix

# Paradigm definitions: each is (description, ending_to_strip, suffix_table)
# suffix_table: vibhakti -> [eka,dvi,bahu]
# ending_to_strip: how many chars to remove from input word to get base.
# Most are 1 char (a, A, i, I, u, U, f). For halanta like an, we strip 2.

PARADIGMS: dict[str, dict[str, Any]] = {}

def _register(paradigm: str, ending: str, gender: str, desc: str, table: dict[str, list[str]]):
    PARADIGMS[paradigm] = {
        "ending": ending,
        "gender": gender,
        "desc": desc,
        "table": table,
    }

# a_kArAnta puMliNga  rAma
_register("a_m", "a", "m", "a-kArAnta puMliNga (rAma)", {
    "prathamA": ["aH", "O", "AH"],
    "dvitIyA": ["am", "O", "An"],
    "tftIyA": ["eRa", "AByAm", "EH"],
    "caturTI": ["Aya", "AByAm", "eByaH"],
    "paYcamI": ["At", "AByAm", "eByaH"],
    "zazWI": ["asya", "ayoH", "ARAm"],
    "saptamI": ["e", "ayoH", "ezu"],
    "saMboDana": ["a", "O", "AH"],
})

# a_kArAnta napuMsaka  Pala
_register("a_n", "a", "n", "a-kArAnta napuMsaka (Pala)", {
    "prathamA": ["am", "e", "Ani"],
    "dvitIyA": ["am", "e", "Ani"],
    "tftIyA": ["eRa", "AByAm", "EH"],
    "caturTI": ["Aya", "AByAm", "eByaH"],
    "paYcamI": ["At", "AByAm", "eByaH"],
    "zazWI": ["asya", "ayoH", "ARAm"],
    "saptamI": ["e", "ayoH", "ezu"],
    "saMboDana": ["a", "e", "Ani"],
})

# A_kArAnta strIliNga  ramA
_register("A_f", "A", "f", "A-kArAnta strIliNga (ramA)", {
    "prathamA": ["A", "e", "AH"],
    "dvitIyA": ["Am", "e", "AH"],
    "tftIyA": ["ayA", "AByAm", "ABiH"],
    "caturTI": ["AyE", "AByAm", "AByaH"],
    "paYcamI": ["AyAH", "AByAm", "AByaH"],
    "zazWI": ["AyAH", "ayoH", "ARAm"],
    "saptamI": ["AyAm", "ayoH", "Asu"],
    "saMboDana": ["e", "e", "AH"],
})

# i_kArAnta puMliNga  hari
_register("i_m", "i", "m", "i-kArAnta puMliNga (hari)", {
    "prathamA": ["iH", "I", "ayaH"],
    "dvitIyA": ["im", "I", "In"],
    "tftIyA": ["iRA", "iByAm", "iBiH"],
    "caturTI": ["aye", "iByAm", "iByaH"],
    "paYcamI": ["eH", "iByAm", "iByaH"],
    "zazWI": ["eH", "yoH", "IRAm"],
    "saptamI": ["O", "yoH", "izu"],
    "saMboDana": ["e", "I", "ayaH"],
})

# pati - irregular i_kArAnta puMliNga (pati - patyA, patye, patyuH, patyO, patInAm) + compounds like BU-pati
_register("pati_m", "pati", "m", "i-kArAnta puMliNga (pati) - irregular", {
    "prathamA": ["patiH", "patI", "patayaH"],
    "dvitIyA": ["patim", "patI", "patIn"],
    "tftIyA": ["patyA", "patiByAm", "patiBiH"],
    "caturTI": ["patye", "patiByAm", "patiByaH"],
    "paYcamI": ["patyuH", "patiByAm", "patiByaH"],
    "zazWI": ["patyuH", "patyoH", "patInAm"],
    "saptamI": ["patyO", "patyoH", "patizu"],
    "saMboDana": ["pate", "patI", "patayaH"],
})

# sakhi - irregular i_kArAnta puMliNga (sakhi - sakhyA, sakhye, sakhyuH, sakhyO, sakhInAm) + compounds like priya-sakhi
_register("sakhi_m", "sakhi", "m", "i-kArAnta puMliNga (sakhi) - irregular", {
    "prathamA": ["sakhA", "sakhAyO", "sakhAyaH"],
    "dvitIyA": ["sakhAyam", "sakhAyO", "sakhIn"],
    "tftIyA": ["sakhyA", "sakhiByAm", "sakhiBiH"],
    "caturTI": ["sakhye", "sakhiByAm", "sakhiByaH"],
    "paYcamI": ["sakhyuH", "sakhiByAm", "sakhiByaH"],
    "zazWI": ["sakhyuH", "sakhyoH", "sakhInAm"],
    "saptamI": ["sakhyO", "sakhyoH", "sakhiSu"],
    "saMboDana": ["sakhe", "sakhAyO", "sakhAyaH"],
})

# i_kArAnta strIliNga  mati (allows yA variant but we pick mati-like)
_register("i_f", "i", "f", "i-kArAnta strIliNga (mati)", {
    "prathamA": ["iH", "I", "ayaH"],
    "dvitIyA": ["im", "I", "IH"],
    "tftIyA": ["yA", "iByAm", "iBiH"],
    "caturTI": ["aye", "iByAm", "iByaH"],
    "paYcamI": ["eH", "iByAm", "iByaH"],
    "zazWI": ["eH", "yoH", "IRAm"],
    "saptamI": ["O", "yoH", "izu"],
    "saMboDana": ["e", "I", "ayaH"],
})

# i_kArAnta napuMsaka  vAri
_register("i_n", "i", "n", "i-kArAnta napuMsaka (vAri)", {
    "prathamA": ["i", "iRI", "IRi"],
    "dvitIyA": ["i", "iRI", "IRi"],
    "tftIyA": ["iRA", "iByAm", "iBiH"],
    "caturTI": ["iRe", "iByAm", "iByaH"],
    "paYcamI": ["iRaH", "iByAm", "iByaH"],
    "zazWI": ["iRaH", "iRoH", "IRAm"],
    "saptamI": ["iRi", "iRoH", "izu"],
    "saMboDana": ["i", "iRI", "IRi"],
})

# I_kArAnta strI  nadI
_register("I_f", "I", "f", "I-kArAnta strIliNga (nadI)", {
    "prathamA": ["I", "yO", "yaH"],
    "dvitIyA": ["Im", "yO", "IH"],
    "tftIyA": ["yA", "IByAm", "IBiH"],
    "caturTI": ["yE", "IByAm", "IByaH"],
    "paYcamI": ["yAH", "IByAm", "IByaH"],
    "zazWI": ["yAH", "yoH", "InAm"],
    "saptamI": ["yAm", "yoH", "Izu"],
    "saMboDana": ["i", "yO", "yaH"],
})

# u_kArAnta puM  guru
_register("u_m", "u", "m", "u-kArAnta puMliNga (guru)", {
    "prathamA": ["uH", "U", "avaH"],
    "dvitIyA": ["um", "U", "Un"],
    "tftIyA": ["uRA", "uByAm", "uBiH"],
    "caturTI": ["ave", "uByAm", "uByaH"],
    "paYcamI": ["oH", "uByAm", "uByaH"],
    "zazWI": ["oH", "voH", "URAm"],
    "saptamI": ["O", "voH", "uzu"],
    "saMboDana": ["o", "U", "avaH"],
})

# u_kArAnta strI  Denu
_register("u_f", "u", "f", "u-kArAnta strIliNga (Denu)", {
    "prathamA": ["uH", "U", "avaH"],
    "dvitIyA": ["um", "U", "UH"],
    "tftIyA": ["vA", "uByAm", "uBiH"],
    "caturTI": ["ave", "uByAm", "uByaH"],
    "paYcamI": ["oH", "uByAm", "uByaH"],
    "zazWI": ["oH", "voH", "URAm"],
    "saptamI": ["O", "voH", "uzu"],
    "saMboDana": ["o", "U", "avaH"],
})

# u_kArAnta napu  maDu
_register("u_n", "u", "n", "u-kArAnta napuMsaka (maDu)", {
    "prathamA": ["u", "uRI", "URi"],
    "dvitIyA": ["u", "uRI", "URi"],
    "tftIyA": ["uRA", "uByAm", "uBiH"],
    "caturTI": ["uRe", "uByAm", "uByaH"],
    "paYcamI": ["uRaH", "uByAm", "uByaH"],
    "zazWI": ["uRaH", "uRoH", "URAm"],
    "saptamI": ["uRi", "uRoH", "uzu"],
    "saMboDana": ["u", "uRI", "URi"],
})

# U_kArAnta strI  vaDU
_register("U_f", "U", "f", "U-kArAnta strIliNga (vaDU)", {
    "prathamA": ["UH", "vO", "vaH"],
    "dvitIyA": ["Um", "vO", "UH"],
    "tftIyA": ["vA", "UByAm", "UBiH"],
    "caturTI": ["vE", "UByAm", "UByaH"],
    "paYcamI": ["vAH", "UByAm", "UByaH"],
    "zazWI": ["vAH", "voH", "UnAm"],
    "saptamI": ["vAm", "voH", "Uzu"],
    "saMboDana": ["u", "vO", "vaH"],
})

# f_kArAnta puM  pitf
_register("f_m", "f", "m", "f-kArAnta puMliNga (pitf)", {
    "prathamA": ["A", "arO", "araH"],
    "dvitIyA": ["aram", "arO", "Fn"],
    "tftIyA": ["rA", "fByAm", "fBiH"],
    "caturTI": ["re", "fByAm", "fByaH"],
    "paYcamI": ["uH", "fByAm", "fByaH"],
    "zazWI": ["uH", "roH", "FRAm"],
    "saptamI": ["ari", "roH", "fzu"],
    "saMboDana": ["aH", "arO", "araH"],
})

# f_kArAnta strI  mAtf (same but voc sg mAtaH -> same as pitf voc?)
_register("f_f", "f", "f", "f-kArAnta strIliNga (mAtf)", {
    "prathamA": ["A", "arO", "araH"],
    "dvitIyA": ["aram", "arO", "FH"],
    "tftIyA": ["rA", "fByAm", "fBiH"],
    "caturTI": ["re", "fByAm", "fByaH"],
    "paYcamI": ["uH", "fByAm", "fByaH"],
    "zazWI": ["uH", "roH", "FRAm"],
    "saptamI": ["ari", "roH", "fzu"],
    "saMboDana": ["aH", "arO", "araH"],
})

# f_n? naptf etc - similar to m
_register("f_n", "f", "n", "f-kArAnta napuMsaka (dAtf)", {
    "prathamA": ["f", "fRI", "FRI"],
    "dvitIyA": ["f", "fRI", "FRI"],
    "tftIyA": ["rA", "fByAm", "fBiH"],
    "caturTI": ["re", "fByAm", "fByaH"],
    "paYcamI": ["uH", "fByAm", "fByaH"],
    "zazWI": ["uH", "roH", "FRAm"],
    "saptamI": ["ari", "roH", "fzu"],
    "saMboDana": ["f", "fRI", "FRI"],
})

# ---- halanta ----

# an-stem rAjan (m) – strips "an" -> base rAj
_register("an_m", "an", "m", "an-kArAnta puMliNga (rAjan)", {
    "prathamA": ["A", "AnO", "AnaH"],
    "dvitIyA": ["Anam", "AnO", "YaH"],
    "tftIyA": ["YA", "aByAm", "aBiH"],
    "caturTI": ["Ye", "aByAm", "aByaH"],
    "paYcamI": ["YaH", "aByAm", "aByaH"],
    "zazWI": ["YaH", "YoH", "YAm"],
    "saptamI": ["Yi", "YoH", "asu"],
    "saMboDana": ["an", "AnO", "AnaH"],
})

# an-stem nAman (n) – napuMsaka an-kArAnta (nAman, brahman n.)
_register("an_n", "an", "n", "an-kArAnta napuMsaka (nAman)", {
    "prathamA": ["a", "nI", "Ani"],
    "dvitIyA": ["a", "nI", "Ani"],
    "tftIyA": ["nA", "aByAm", "aBiH"],
    "caturTI": ["ne", "aByAm", "aByaH"],
    "paYcamI": ["naH", "aByAm", "aByaH"],
    "zazWI": ["naH", "noH", "nAm"],
    "saptamI": ["ni", "noH", "asu"],
    "saMboDana": ["a", "nI", "Ani"],
})

# in-stem yogin (also danin, etc)
_register("in_m", "in", "m", "in-kArAnta puMliNga (yogin)", {
    "prathamA": ["I", "inO", "inaH"],
    "dvitIyA": ["inam", "inO", "inaH"],
    "tftIyA": ["inA", "iByAm", "iBiH"],
    "caturTI": ["ine", "iByAm", "iByaH"],
    "paYcamI": ["inaH", "iByAm", "iByaH"],
    "zazWI": ["inaH", "inoH", "inAm"],
    "saptamI": ["ini", "inoH", "izu"],
    "saMboDana": ["in", "inO", "inaH"],
})

# at-stem Bavat (present participle) – m/f
_register("at_m", "at", "m", "at-kArAnta puMliNga (Bavat)", {
    "prathamA": ["an", "antO", "antaH"],
    "dvitIyA": ["antam", "antO", "ataH"],
    "tftIyA": ["atA", "aByAm", "aBiH"],
    "caturTI": ["ate", "aByAm", "aByaH"],
    "paYcamI": ["ataH", "aByAm", "aByaH"],
    "zazWI": ["ataH", "atoH", "atAm"],
    "saptamI": ["ati", "atoH", "atsu"],
    "saMboDana": ["an", "antO", "antaH"],
})

# at-stem neuter (jagat / Bavat n. – bhavat, bhavatI, bhavanti)
_register("at_n", "at", "n", "at-kArAnta napuMsaka (jagat/Bavat n.)", {
    "prathamA": ["at", "atI", "anti"],
    "dvitIyA": ["at", "atI", "anti"],
    "tftIyA": ["atA", "adByAm", "adBiH"],
    "caturTI": ["ate", "adByAm", "adByaH"],
    "paYcamI": ["ataH", "adByAm", "adByaH"],
    "zazWI": ["ataH", "atoH", "atAm"],
    "saptamI": ["ati", "atoH", "atsu"],
    "saMboDana": ["at", "atI", "anti"],
})

# as-stem manas (n) - neuter
_register("as_n", "as", "n", "as-kArAnta napuMsaka (manas)", {
    "prathamA": ["aH", "asI", "AMsi"],
    "dvitIyA": ["aH", "asI", "AMsi"],
    "tftIyA": ["asA", "oByAm", "oBiH"],
    "caturTI": ["ase", "oByAm", "oByaH"],
    "paYcamI": ["asaH", "oByAm", "oByaH"],
    "zazWI": ["asaH", "asoH", "asAm"],
    "saptamI": ["asi", "asoH", "aHsu"],
    "saMboDana": ["aH", "asI", "AMsi"],
})

# as-stem bahuvrIhi masculine/feminine (sumanas, durmanas - adj. from manas)
# When manas is final member of bahuvrIhi, it becomes an adjective and takes m/f gender
# e.g., sumanas m: sumanAH, sumanasO, sumanasaH / sumanasam ... cf. aGgiras
_register("as_m", "as", "m", "as-kArAnta puMliNga (sumanas - bahuvrIhi of manas)", {
    "prathamA": ["AH", "asO", "asaH"],
    "dvitIyA": ["asam", "asO", "asaH"],
    "tftIyA": ["asA", "oByAm", "oBiH"],
    "caturTI": ["ase", "oByAm", "oByaH"],
    "paYcamI": ["asaH", "oByAm", "oByaH"],
    "zazWI": ["asaH", "asoH", "asAm"],
    "saptamI": ["asi", "asoH", "aHsu"],
    "saMboDana": ["aH", "asO", "asaH"],
})

_register("as_f", "as", "f", "as-kArAnta strIliNga (sumanas - bahuvrIhi f.)", {
    "prathamA": ["AH", "asO", "asaH"],
    "dvitIyA": ["asam", "asO", "asaH"],
    "tftIyA": ["asA", "oByAm", "oBiH"],
    "caturTI": ["ase", "oByAm", "oByaH"],
    "paYcamI": ["asaH", "oByAm", "oByaH"],
    "zazWI": ["asaH", "asoH", "asAm"],
    "saptamI": ["asi", "asoH", "aHsu"],
    "saMboDana": ["aH", "asO", "asaH"],
})

# us-stem danus (n)
_register("us_n", "us", "n", "us-kArAnta napuMsaka (danus)", {
    "prathamA": ["uH", "uzI", "UMzi"],
    "dvitIyA": ["uH", "uzI", "UMzi"],
    "tftIyA": ["uzA", "urByAm", "urBiH"],
    "caturTI": ["uze", "urByAm", "urByaH"],
    "paYcamI": ["uzaH", "urByAm", "urByaH"],
    "zazWI": ["uzaH", "uzoH", "uzAm"],
    "saptamI": ["uzi", "uzoH", "uHsu"],
    "saMboDana": ["uH", "uzI", "UMzi"],
})

# is-stem havis (n) – haviH, haviSI, havIMzi
_register("is_n", "is", "n", "is-kArAnta napuMsaka (havis)", {
    "prathamA": ["iH", "izI", "IMzi"],
    "dvitIyA": ["iH", "izI", "IMzi"],
    "tftIyA": ["izA", "irByAm", "irBiH"],
    "caturTI": ["ize", "irByAm", "irByaH"],
    "paYcamI": ["izaH", "irByAm", "irByaH"],
    "zazWI": ["izaH", "izoH", "izAm"],
    "saptamI": ["izi", "izoH", "iHsu"],
    "saMboDana": ["iH", "izI", "IMzi"],
})

# c-stem vAc (f) – vAk, vAcO, vAcaH
_register("c_f", "c", "f", "c-kArAnta strIliNga (vAc)", {
    "prathamA": ["k", "cO", "caH"],
    "dvitIyA": ["cam", "cO", "caH"],
    "tftIyA": ["cA", "gByAm", "gBiH"],
    "caturTI": ["ce", "gByAm", "gByaH"],
    "paYcamI": ["caH", "gByAm", "gByaH"],
    "zazWI": ["caH", "coH", "cAm"],
    "saptamI": ["ci", "coH", "kzu"],
    "saMboDana": ["k", "cO", "caH"],
})

# t-stem generic – sarit (f), marut (m), jagat (n) – simplified t table (m/f)
_register("t_m", "t", "m", "t-kArAnta puMliNga (marut)", {
    "prathamA": ["t", "tO", "taH"],
    "dvitIyA": ["tam", "tO", "taH"],
    "tftIyA": ["tA", "dByAm", "dBiH"],
    "caturTI": ["te", "dByAm", "dByaH"],
    "paYcamI": ["taH", "dByAm", "dByaH"],
    "zazWI": ["taH", "toH", "tAm"],
    "saptamI": ["ti", "toH", "tsu"],
    "saMboDana": ["t", "tO", "taH"],
})
_register("t_f", "t", "f", "t-kArAnta strIliNga (sarit)", {
    "prathamA": ["t", "tO", "taH"],
    "dvitIyA": ["tam", "tO", "taH"],
    "tftIyA": ["tA", "dByAm", "dBiH"],
    "caturTI": ["te", "dByAm", "dByaH"],
    "paYcamI": ["taH", "dByAm", "dByaH"],
    "zazWI": ["taH", "toH", "tAm"],
    "saptamI": ["ti", "toH", "tsu"],
    "saMboDana": ["t", "tO", "taH"],
})
_register("t_n", "t", "n", "t-kArAnta napuMsaka (jagat)", {
    "prathamA": ["t", "tI", "nti"],
    "dvitIyA": ["t", "tI", "nti"],
    "tftIyA": ["tA", "dByAm", "dBiH"],
    "caturTI": ["te", "dByAm", "dByaH"],
    "paYcamI": ["taH", "dByAm", "dByaH"],
    "zazWI": ["taH", "toH", "tAm"],
    "saptamI": ["ti", "toH", "tsu"],
    "saMboDana": ["t", "tI", "nti"],
})

# o-kArAnta go (m/f) – irregular: gOH (gauH), gAvO, gAvaH
_register("o_m", "o", "m", "o-kArAnta puMliNga (go)", {
    "prathamA": ["OH", "AvO", "AvaH"],
    "dvitIyA": ["Am", "AvO", "AvaH"],
    "tftIyA": ["AvA", "oByAm", "oBiH"],
    "caturTI": ["Ave", "oByAm", "oByaH"],
    "paYcamI": ["AvaH", "oByAm", "oByaH"],
    "zazWI": ["AvaH", "AvoH", "AvAm"],
    "saptamI": ["Avi", "AvoH", "ozu"],
    "saMboDana": ["OH", "AvO", "AvaH"],
})

# generic consonant fallback – just adds usual sup terminations with sandhi simplified
# used when no specific paradigm matches
_GENERIC_CONS_TABLE = {
    "prathamA": ["", "O", "aH"],
    "dvitIyA": ["am", "O", "aH"],
    "tftIyA": ["A", "ByAm", "BiH"],
    "caturTI": ["e", "ByAm", "ByaH"],
    "paYcamI": ["aH", "ByAm", "ByaH"],
    "zazWI": ["aH", "oH", "Am"],
    "saptamI": ["i", "oH", "su"],
    "saMboDana": ["", "O", "aH"],
}

# ---------------------------------------------------------------------------
# Pronouns – full tables hardcoded (overrides generic)
# Key = pronoun lemma (SLP1, lower-ish)
# Each pronoun may have gender variants.
# ---------------------------------------------------------------------------

PRONOUNS: dict[str, Any] = {}

def _pronoun_table(forms: dict[str, dict[str, list[str]]]) -> dict[str, dict[str, list[str]]]:
    # validate
    return forms

# tad – m/f/n
PRONOUNS["tad"] = {
    "m": _pronoun_table({
        "prathamA": ["saH", "tO", "te"],
        "dvitIyA": ["tam", "tO", "tAn"],
        "tftIyA": ["tena", "tAByAm", "tEH"],
        "caturTI": ["tasmE", "tAByAm", "teByaH"],
        "paYcamI": ["tasmAt", "tAByAm", "teByaH"],
        "zazWI": ["tasya", "tayoH", "tezAm"],
        "saptamI": ["tasmin", "tayoH", "tezu"],
        "saMboDana": ["saH", "tO", "te"],
    }),
    "f": _pronoun_table({
        "prathamA": ["sA", "te", "tAH"],
        "dvitIyA": ["tAm", "te", "tAH"],
        "tftIyA": ["tayA", "tAByAm", "tABiH"],
        "caturTI": ["tasyE", "tAByAm", "tAByaH"],
        "paYcamI": ["tasyAH", "tAByAm", "tAByaH"],
        "zazWI": ["tasyAH", "tayoH", "tAsAm"],
        "saptamI": ["tasyAm", "tayoH", "tAsu"],
        "saMboDana": ["sA", "te", "tAH"],
    }),
    "n": _pronoun_table({
        "prathamA": ["tat", "te", "tAni"],
        "dvitIyA": ["tat", "te", "tAni"],
        "tftIyA": ["tena", "tAByAm", "tEH"],
        "caturTI": ["tasmE", "tAByAm", "teByaH"],
        "paYcamI": ["tasmAt", "tAByAm", "teByaH"],
        "zazWI": ["tasya", "tayoH", "tezAm"],
        "saptamI": ["tasmin", "tayoH", "tezu"],
        "saMboDana": ["tat", "te", "tAni"],
    }),
}

# etad – m/f/n (eta- forms)
PRONOUNS["etad"] = {
    "m": _pronoun_table({
        "prathamA": ["ezaH", "etO", "ete"],
        "dvitIyA": ["etam", "etO", "etAn"],
        "tftIyA": ["etena", "etAByAm", "etEH"],
        "caturTI": ["etasmE", "etAByAm", "eteByaH"],
        "paYcamI": ["etasmAt", "etAByAm", "eteByaH"],
        "zazWI": ["etasya", "etayoH", "etezAm"],
        "saptamI": ["etasmin", "etayoH", "etezu"],
        "saMboDana": ["ezaH", "etO", "ete"],
    }),
    "f": _pronoun_table({
        "prathamA": ["ezA", "ete", "etAH"],
        "dvitIyA": ["etAm", "ete", "etAH"],
        "tftIyA": ["etayA", "etAByAm", "etABiH"],
        "caturTI": ["etasyE", "etAByAm", "etAByaH"],
        "paYcamI": ["etasyAH", "etAByAm", "etAByaH"],
        "zazWI": ["etasyAH", "etayoH", "etAsAm"],
        "saptamI": ["etasyAm", "etayoH", "etAsu"],
        "saMboDana": ["ezA", "ete", "etAH"],
    }),
    "n": _pronoun_table({
        "prathamA": ["etat", "ete", "etAni"],
        "dvitIyA": ["etat", "ete", "etAni"],
        "tftIyA": ["etena", "etAByAm", "etEH"],
        "caturTI": ["etasmE", "etAByAm", "eteByaH"],
        "paYcamI": ["etasmAt", "etAByAm", "eteByaH"],
        "zazWI": ["etasya", "etayoH", "etezAm"],
        "saptamI": ["etasmin", "etayoH", "etezu"],
        "saMboDana": ["etat", "ete", "etAni"],
    }),
}

# yad – m/f/n
PRONOUNS["yad"] = {
    "m": _pronoun_table({
        "prathamA": ["yaH", "yO", "ye"],
        "dvitIyA": ["yam", "yO", "yAn"],
        "tftIyA": ["yena", "yAByAm", "yEH"],
        "caturTI": ["yasmE", "yAByAm", "yeByaH"],
        "paYcamI": ["yasmAt", "yAByAm", "yeByaH"],
        "zazWI": ["yasya", "yayoH", "yezAm"],
        "saptamI": ["yasmin", "yayoH", "yezu"],
        "saMboDana": ["yaH", "yO", "ye"],
    }),
    "f": _pronoun_table({
        "prathamA": ["yA", "ye", "yAH"],
        "dvitIyA": ["yAm", "ye", "yAH"],
        "tftIyA": ["yayA", "yAByAm", "yABiH"],
        "caturTI": ["yasyE", "yAByAm", "yAByaH"],
        "paYcamI": ["yasyAH", "yAByAm", "yAByaH"],
        "zazWI": ["yasyAH", "yayoH", "yAsAm"],
        "saptamI": ["yasyAm", "yayoH", "yAsu"],
        "saMboDana": ["yA", "ye", "yAH"],
    }),
    "n": _pronoun_table({
        "prathamA": ["yat", "ye", "yAni"],
        "dvitIyA": ["yat", "ye", "yAni"],
        "tftIyA": ["yena", "yAByAm", "yEH"],
        "caturTI": ["yasmE", "yAByAm", "yeByaH"],
        "paYcamI": ["yasmAt", "yAByAm", "yeByaH"],
        "zazWI": ["yasya", "yayoH", "yezAm"],
        "saptamI": ["yasmin", "yayoH", "yezu"],
        "saMboDana": ["yat", "ye", "yAni"],
    }),
}

# kim – interrogative m/f/n
PRONOUNS["kim"] = {
    "m": _pronoun_table({
        "prathamA": ["kaH", "kO", "ke"],
        "dvitIyA": ["kam", "kO", "kAn"],
        "tftIyA": ["kena", "kAByAm", "kEH"],
        "caturTI": ["kasmE", "kAByAm", "keByaH"],
        "paYcamI": ["kasmAt", "kAByAm", "keByaH"],
        "zazWI": ["kasya", "kayoH", "kezAm"],
        "saptamI": ["kasmin", "kayoH", "kezu"],
        "saMboDana": ["kaH", "kO", "ke"],
    }),
    "f": _pronoun_table({
        "prathamA": ["kA", "ke", "kAH"],
        "dvitIyA": ["kAm", "ke", "kAH"],
        "tftIyA": ["kayA", "kAByAm", "kABiH"],
        "caturTI": ["kasyE", "kAByAm", "kAByaH"],
        "paYcamI": ["kasyAH", "kAByAm", "kAByaH"],
        "zazWI": ["kasyAH", "kayoH", "kAsAm"],
        "saptamI": ["kasyAm", "kayoH", "kAsu"],
        "saMboDana": ["kA", "ke", "kAH"],
    }),
    "n": _pronoun_table({
        "prathamA": ["kim", "ke", "kAni"],
        "dvitIyA": ["kim", "ke", "kAni"],
        "tftIyA": ["kena", "kAByAm", "kEH"],
        "caturTI": ["kasmE", "kAByAm", "keByaH"],
        "paYcamI": ["kasmAt", "kAByAm", "keByaH"],
        "zazWI": ["kasya", "kayoH", "kezAm"],
        "saptamI": ["kasmin", "kayoH", "kezu"],
        "saMboDana": ["kim", "ke", "kAni"],
    }),
}

# idam – m/f/n
PRONOUNS["idam"] = {
    "m": _pronoun_table({
        "prathamA": ["ayam", "imO", "ime"],
        "dvitIyA": ["imam", "imO", "imAn"],
        "tftIyA": ["anena", "AByAm", "eBiH"],
        "caturTI": ["asmE", "AByAm", "eByaH"],
        "paYcamI": ["asmAt", "AByAm", "eByaH"],
        "zazWI": ["asya", "anayoH", "ezAm"],
        "saptamI": ["asmin", "anayoH", "ezu"],
        "saMboDana": ["ayam", "imO", "ime"],
    }),
    "f": _pronoun_table({
        "prathamA": ["iyam", "ime", "imAH"],
        "dvitIyA": ["imAm", "ime", "imAH"],
        "tftIyA": ["anayA", "AByAm", "ABiH"],
        "caturTI": ["asyE", "AByAm", "AByaH"],
        "paYcamI": ["asyAH", "AByAm", "AByaH"],
        "zazWI": ["asyAH", "anayoH", "AsAm"],
        "saptamI": ["asyAm", "anayoH", "Asu"],
        "saMboDana": ["iyam", "ime", "imAH"],
    }),
    "n": _pronoun_table({
        "prathamA": ["idam", "ime", "imAni"],
        "dvitIyA": ["idam", "ime", "imAni"],
        "tftIyA": ["anena", "AByAm", "eBiH"],
        "caturTI": ["asmE", "AByAm", "eByaH"],
        "paYcamI": ["asmAt", "AByAm", "eByaH"],
        "zazWI": ["asya", "anayoH", "ezAm"],
        "saptamI": ["asmin", "anayoH", "ezu"],
        "saMboDana": ["idam", "ime", "imAni"],
    }),
}

# adas – m/f/n
PRONOUNS["adas"] = {
    "m": _pronoun_table({
        "prathamA": ["asO", "amU", "amI"],
        "dvitIyA": ["amum", "amU", "amUn"],
        "tftIyA": ["amunA", "amUByAm", "amIBiH"],
        "caturTI": ["amuzmE", "amUByAm", "amIByaH"],
        "paYcamI": ["amuzmAt", "amUByAm", "amIByaH"],
        "zazWI": ["amuzya", "amuyoH", "amIzAm"],
        "saptamI": ["amuzmin", "amuyoH", "amIzu"],
        "saMboDana": ["asO", "amU", "amI"],
    }),
    "f": _pronoun_table({
        "prathamA": ["asO", "amU", "amUH"],
        "dvitIyA": ["amUm", "amU", "amUH"],
        "tftIyA": ["amuyA", "amUByAm", "amUBiH"],
        "caturTI": ["amuzyE", "amUByAm", "amUByaH"],
        "paYcamI": ["amuzyAH", "amUByAm", "amUByaH"],
        "zazWI": ["amuzyAH", "amuyoH", "amUzAm"],
        "saptamI": ["amuzyAm", "amuyoH", "amUzu"],
        "saMboDana": ["asO", "amU", "amUH"],
    }),
    "n": _pronoun_table({
        "prathamA": ["adaH", "amU", "amUni"],
        "dvitIyA": ["adaH", "amU", "amUni"],
        "tftIyA": ["amunA", "amUByAm", "amIBiH"],
        "caturTI": ["amuzmE", "amUByAm", "amIByaH"],
        "paYcamI": ["amuzmAt", "amUByAm", "amIByaH"],
        "zazWI": ["amuzya", "amuyoH", "amIzAm"],
        "saptamI": ["amuzmin", "amuyoH", "amIzu"],
        "saMboDana": ["adaH", "amU", "amUni"],
    }),
}

# sarva-ādi pronouns – decline like tad (pronoun endings) but with their own stem
# These are a-kArAnta pronouns that take pronoun terminations (sarvasmai, etc.)
_SARVA_ADI = ["sarva", "viSva", "uBa", "uBaya", "katara", "katama", "anya", "anyatara", "itara", "para", "apara", "adara", "alpa", "pUrva", "avara", "DakziRa", "uttara", "sva", "Sva", "antara", "tyad", "tad", "yad", "etad"]  # overlap ok
def _make_sarva_pronoun(lemma: str):
    # Build tables by taking tad pattern and replacing tad-stem with lemma stem
    # lemma is e.g., "sarva" -> stem "sarva"
    tad = PRONOUNS["tad"]
    out = {}
    for g in ("m", "f", "n"):
        tbl = {}
        for vib, forms in tad[g].items():
            new_forms = []
            for f in forms:
                # Replace initial t-/s- with lemma stem logic:
                # For m/n: tad forms start with s- (saH) or t- (tam...). We map: replace leading 's'/'t'/'te' with lemma+ appropriate suffix
                # Simpler: generate as lemma + tad_suffix where suffix is tad form minus initial t/s
                # Instead we construct directly: lemma with pronoun endings:
                #   Use tad pattern endings: e.g., tad m prathamA eka "saH" corresponds to lemma + "H"? sarva -> sarvaH
                #   We'll derive suffix by removing 't'/'s' prefix from tad form and prepending lemma
                # This is approximate but yields correct Sanskrit (sarvaH, sarvO, sarve etc.)
                # For f: sA -> sarvA etc.
                # We'll use explicit pronoun endings table for a-stem pronouns:
                pass
                new_forms.append(f)  # placeholder fallback
            tbl[vib] = new_forms
        out[g] = tbl
    return out

# Generate proper sarva-ādi pronoun tables using classic endings (not just copying tad)
# Classic sarva (m) pronouns:
# prathamA: sarvaH, sarvO, sarve ; dvitIyA: sarvam, sarvO, sarvAn ; tftIyA: sarveRa, sarvAByAm, sarvEH ; caturTI: sarvasmE, sarvAByAm, sarveByaH ; etc.
# Base is truncated lemma without final 'a' (sarv) + suffix that includes the 'a' when needed.
_SARVA_PRONOUN_M = {
    "prathamA": ["aH", "O", "e"],
    "dvitIyA": ["am", "O", "An"],
    "tftIyA": ["eRa", "AByAm", "EH"],
    "caturTI": ["asmE", "AByAm", "eByaH"],
    "paYcamI": ["asmAt", "AByAm", "eByaH"],
    "zazWI": ["asya", "ayoH", "ezAm"],
    "saptamI": ["asmin", "ayoH", "ezu"],
    "saMboDana": ["aH", "O", "e"],
}
_SARVA_PRONOUN_F = {
    "prathamA": ["A", "e", "AH"],  # sarvA, sarve, sarvAH
    "dvitIyA": ["Am", "e", "AH"],  # sarvAm ...
    "tftIyA": ["ayA", "AByAm", "ABiH"],
    "caturTI": ["asyE", "AByAm", "AByaH"],
    "paYcamI": ["asyAH", "AByAm", "AByaH"],
    "zazWI": ["asyAH", "ayoH", "AsAm"],
    "saptamI": ["asyAm", "ayoH", "Asu"],
    "saMboDana": ["A", "e", "AH"],
}
_SARVA_PRONOUN_N = {
    "prathamA": ["am", "e", "ARi"],  # sarvam, sarve, sarvARi
    "dvitIyA": ["am", "e", "ARi"],
    "tftIyA": ["eRa", "AByAm", "EH"],
    "caturTI": ["asmE", "AByAm", "eByaH"],
    "paYcamI": ["asmAt", "AByAm", "eByaH"],
    "zazWI": ["asya", "ayoH", "ezAm"],
    "saptamI": ["asmin", "ayoH", "ezu"],
    "saMboDana": ["am", "e", "ARi"],
}
for _w in ["sarva", "viSva", "uBa", "uBaya", "katara", "katama", "anya", "anyatara", "itara", "para", "apara", "DakziRa", "pUrva", "avara", "uttara", "aDara", "alpa", "sva"]:
    # uBa is dual-only pronoun (both)
    if _w == "uBa":
        PRONOUNS[_w] = {
            "m": {"prathamA": ["-", "uBO", "-"], "dvitIyA": ["-", "uBO", "-"], "tftIyA": ["-", "uBAByAm", "-"], "caturTI": ["-", "uBAByAm", "-"], "paYcamI": ["-", "uBAByAm", "-"], "zazWI": ["-", "uBayoH", "-"], "saptamI": ["-", "uBayoH", "-"], "saMboDana": ["-", "uBO", "-"]},
            "f": {"prathamA": ["-", "uBe", "-"], "dvitIyA": ["-", "uBe", "-"], "tftIyA": ["-", "uBAByAm", "-"], "caturTI": ["-", "uBAByAm", "-"], "paYcamI": ["-", "uBAByAm", "-"], "zazWI": ["-", "uBayoH", "-"], "saptamI": ["-", "uBayoH", "-"], "saMboDana": ["-", "uBe", "-"]},
            "n": {"prathamA": ["-", "uBe", "-"], "dvitIyA": ["-", "uBe", "-"], "tftIyA": ["-", "uBAByAm", "-"], "caturTI": ["-", "uBAByAm", "-"], "paYcamI": ["-", "uBAByAm", "-"], "zazWI": ["-", "uBayoH", "-"], "saptamI": ["-", "uBayoH", "-"], "saMboDana": ["-", "uBe", "-"]},
        }
        continue
    base = _w[:-1] if _w.endswith("a") else _w  # sarv from sarva, viSv from viSva etc.
    if _w == "uBaya":
        base = "uBaya"  # uBaya keeps final a as stem? Actually uBaya is a-stem but ends with a, we keep uBay? Keep uBaya as is for simplicity
        # for uBaya, base should be uBay? but use uBaya stripping -> uBay, we'll override
        base = "uBay"
    PRONOUNS[_w] = {
        "m": {v: [base + s for s in sufs] for v, sufs in _SARVA_PRONOUN_M.items()},
        "f": {v: [base + s for s in sufs] for v, sufs in _SARVA_PRONOUN_F.items()},
        "n": {v: [base + s for s in sufs] for v, sufs in _SARVA_PRONOUN_N.items()},
    }


# asmad / yusmad – personal pronouns (no gender)
PRONOUNS["asmad"] = {
    "": _pronoun_table({
        "prathamA": ["aham", "AvAm", "vayam"],
        "dvitIyA": ["mAm / mA", "AvAm / nO", "asmAn / naH"],
        "tftIyA": ["mayA", "AvAByAm / nO", "asmABiH / naH"],
        "caturTI": ["maHyam / me", "AvAByAm / nO", "asmaByam / naH"],
        "paYcamI": ["mat", "AvAByAm / nO", "asmaByam / naH"],  # actually asmAt? both: mat, asmAt
        "zazWI": ["mama / me", "AvayoH / nO", "asmAkam / naH"],
        "saptamI": ["mayi", "AvayoH / nO", "asmAsu"],
        "saMboDana": ["", "", ""],  # no vocative
    })
}
PRONOUNS["yuzmad"] = {
    "": _pronoun_table({
        "prathamA": ["tvam", "yuvAm", "yUyam"],
        "dvitIyA": ["tvAm / tvA", "yuvAm / vAm", "yuzmAn / vaH"],
        "tftIyA": ["tvayA", "yuvAByAm / vAm", "yuzmABiH / vaH"],
        "caturTI": ["tuByam / te", "yuvAByAm / vAm", "yuzmaByam / vaH"],
        "paYcamI": ["tvat", "yuvAByAm / vAm", "yuzmaByam / vaH"],
        "zazWI": ["tava / te", "yuvayoH / vAm", "yuzmAkam / vaH"],
        "saptamI": ["tvayi", "yuvayoH / vAm", "yuzmAsu"],
        "saMboDana": ["", "", ""],
    })
}
# aliases
PRONOUNS["yusmad"] = PRONOUNS["yuzmad"]
PRONOUNS["aHam"] = PRONOUNS["asmad"]
PRONOUNS["aham"] = PRONOUNS["asmad"]

# bhavat – pronoun-like but declined as noun at_m; keep alias

# ---------------------------------------------------------------------------
# Numerals
# ---------------------------------------------------------------------------

NUMERALS: dict[str, Any] = {}

# eka – singular only (3 genders, but traditionally only ekavacana)
NUMERALS["eka"] = {
    "m": _pronoun_table({
        "prathamA": ["ekaH", "-", "-"],
        "dvitIyA": ["ekam", "-", "-"],
        "tftIyA": ["ekena", "-", "-"],
        "caturTI": ["ekasmE", "-", "-"],
        "paYcamI": ["ekasmAt", "-", "-"],
        "zazWI": ["ekasya", "-", "-"],
        "saptamI": ["ekasmin", "-", "-"],
        "saMboDana": ["ekaH", "-", "-"],
    }),
    "f": _pronoun_table({
        "prathamA": ["ekA", "-", "-"],
        "dvitIyA": ["ekAm", "-", "-"],
        "tftIyA": ["ekayA", "-", "-"],
        "caturTI": ["ekasyE", "-", "-"],
        "paYcamI": ["ekasyAH", "-", "-"],
        "zazWI": ["ekasyAH", "-", "-"],
        "saptamI": ["ekasyAm", "-", "-"],
        "saMboDana": ["eke", "-", "-"],
    }),
    "n": _pronoun_table({
        "prathamA": ["ekam", "-", "-"],
        "dvitIyA": ["ekam", "-", "-"],
        "tftIyA": ["ekena", "-", "-"],
        "caturTI": ["ekasmE", "-", "-"],
        "paYcamI": ["ekasmAt", "-", "-"],
        "zazWI": ["ekasya", "-", "-"],
        "saptamI": ["ekasmin", "-", "-"],
        "saMboDana": ["ekam", "-", "-"],
    }),
}

# dvi – dual only
NUMERALS["dvi"] = {
    "m": _pronoun_table({
        "prathamA": ["-", "dvO", "-"],
        "dvitIyA": ["-", "dvO", "-"],
        "tftIyA": ["-", "dvAByAm", "-"],
        "caturTI": ["-", "dvAByAm", "-"],
        "paYcamI": ["-", "dvAByAm", "-"],
        "zazWI": ["-", "dvayoH", "-"],
        "saptamI": ["-", "dvayoH", "-"],
        "saMboDana": ["-", "dvO", "-"],
    }),
    "f": _pronoun_table({
        "prathamA": ["-", "dve", "-"],
        "dvitIyA": ["-", "dve", "-"],
        "tftIyA": ["-", "dvAByAm", "-"],
        "caturTI": ["-", "dvAByAm", "-"],
        "paYcamI": ["-", "dvAByAm", "-"],
        "zazWI": ["-", "dvayoH", "-"],
        "saptamI": ["-", "dvayoH", "-"],
        "saMboDana": ["-", "dve", "-"],
    }),
    "n": _pronoun_table({
        "prathamA": ["-", "dve", "-"],
        "dvitIyA": ["-", "dve", "-"],
        "tftIyA": ["-", "dvAByAm", "-"],
        "caturTI": ["-", "dvAByAm", "-"],
        "paYcamI": ["-", "dvAByAm", "-"],
        "zazWI": ["-", "dvayoH", "-"],
        "saptamI": ["-", "dvayoH", "-"],
        "saMboDana": ["-", "dve", "-"],
    }),
}

# tri – plural only
NUMERALS["tri"] = {
    "m": _pronoun_table({
        "prathamA": ["-", "-", "trayaH"],
        "dvitIyA": ["-", "-", "trIn"],
        "tftIyA": ["-", "-", "triBiH"],
        "caturTI": ["-", "-", "triByaH"],
        "paYcamI": ["-", "-", "triByaH"],
        "zazWI": ["-", "-", "trayARAm"],
        "saptamI": ["-", "-", "trizu"],
        "saMboDana": ["-", "-", "trayaH"],
    }),
    "f": _pronoun_table({
        "prathamA": ["-", "-", "tisraH"],
        "dvitIyA": ["-", "-", "tisraH"],
        "tftIyA": ["-", "-", "tisfBiH"],
        "caturTI": ["-", "-", "tisfByaH"],
        "paYcamI": ["-", "-", "tisfByaH"],
        "zazWI": ["-", "-", "tisfRAm"],
        "saptamI": ["-", "-", "tisfzu"],
        "saMboDana": ["-", "-", "tisraH"],
    }),
    "n": _pronoun_table({
        "prathamA": ["-", "-", "trIRi"],
        "dvitIyA": ["-", "-", "trIRi"],
        "tftIyA": ["-", "-", "triBiH"],
        "caturTI": ["-", "-", "triByaH"],
        "paYcamI": ["-", "-", "triByaH"],
        "zazWI": ["-", "-", "trayARAm"],
        "saptamI": ["-", "-", "trizu"],
        "saMboDana": ["-", "-", "trIRi"],
    }),
}

# catur – pl only
NUMERALS["catur"] = {
    "m": _pronoun_table({
        "prathamA": ["-", "-", "catvAraH"],
        "dvitIyA": ["-", "-", "caturaH"],
        "tftIyA": ["-", "-", "caturBiH"],
        "caturTI": ["-", "-", "caturByaH"],
        "paYcamI": ["-", "-", "caturByaH"],
        "zazWI": ["-", "-", "caturRAm"],
        "saptamI": ["-", "-", "caturzu"],
        "saMboDana": ["-", "-", "catvAraH"],
    }),
    "f": _pronoun_table({
        "prathamA": ["-", "-", "catasraH"],
        "dvitIyA": ["-", "-", "catasraH"],
        "tftIyA": ["-", "-", "catasfBiH"],
        "caturTI": ["-", "-", "catasfByaH"],
        "paYcamI": ["-", "-", "catasfByaH"],
        "zazWI": ["-", "-", "catasfRAm"],
        "saptamI": ["-", "-", "catasfzu"],
        "saMboDana": ["-", "-", "catasraH"],
    }),
    "n": _pronoun_table({
        "prathamA": ["-", "-", "catvAri"],
        "dvitIyA": ["-", "-", "catvAri"],
        "tftIyA": ["-", "-", "caturBiH"],
        "caturTI": ["-", "-", "caturByaH"],
        "paYcamI": ["-", "-", "caturByaH"],
        "zazWI": ["-", "-", "caturRAm"],
        "saptamI": ["-", "-", "caturzu"],
        "saMboDana": ["-", "-", "catvAri"],
    }),
}

# 5..19 – indeclinables plural only (paYcan, zaz, saptan, etc.)
# They have same forms for all genders except some number-specific sound changes
_paYcan_table = {
    "prathamA": ["-", "-", "paYca"],
    "dvitIyA": ["-", "-", "paYca"],
    "tftIyA": ["-", "-", "paYcaBiH"],
    "caturTI": ["-", "-", "paYcaByaH"],
    "paYcamI": ["-", "-", "paYcaByaH"],
    "zazWI": ["-", "-", "paYcAnAm"],
    "saptamI": ["-", "-", "paYcasu"],
    "saMboDana": ["-", "-", "paYca"],
}
for _lem in ["paYcan", "paYca", "saptan", "sapta", "navan", "nava", "daSan", "daSa", "ekAdaSan", "dvAdaSan", "trayodaSan", "caturdaSan", "paYcadaSan", "zoDaSan", "saptadaSan", "azwAdaSan", "navadaSan"]:
    _clean = _lem.replace(" ", "")
    _stem = _clean.rstrip("n")
    _tbl = {}
    for _vib, _vals in _paYcan_table.items():
        _new_vals = []
        for _val in _vals:
            if _val == "-":
                _new_vals.append("-")
            else:
                _new_vals.append(_val.replace("paYca", _stem))
        _tbl[_vib] = _new_vals
    NUMERALS[_clean] = {"m": _tbl, "f": _tbl, "n": _tbl}
    NUMERALS[_stem] = {"m": _tbl, "f": _tbl, "n": _tbl}

# Higher numerals: viMSati etc. are feminine nouns (decline fully, not just plural)
# viMSati (20) – i-kArAnta f like mati (full 8x3)
_viMSati_full = {
    "prathamA": ["viMSatiH", "viMSatI", "viMSatayaH"],
    "dvitIyA": ["viMSatim", "viMSatI", "viMSatIH"],
    "tftIyA": ["viMSatyA", "viMSatiByAm", "viMSatiBiH"],
    "caturTI": ["viMSataye", "viMSatiByAm", "viMSatiByaH"],
    "paYcamI": ["viMSateH", "viMSatiByAm", "viMSatiByaH"],
    "zazWI": ["viMSateH", "viMSatyoH", "viMSatInAm"],
    "saptamI": ["viMSatO", "viMSatyoH", "viMSatizu"],
    "saMboDana": ["viMSate", "viMSatI", "viMSatayaH"],
}
NUMERALS["viMSati"] = {"f": _viMSati_full, "m": _viMSati_full, "n": _viMSati_full}
# triMSat (30) – at-stem f (triMSat) full
_triMSat_full = {
    "prathamA": ["triMSat", "triMSatO", "triMSataH"],
    "dvitIyA": ["triMSatam", "triMSatO", "triMSataH"],
    "tftIyA": ["triMSatA", "triMSadByAm", "triMSadBiH"],
    "caturTI": ["triMSate", "triMSadByAm", "triMSadByaH"],
    "paYcamI": ["triMSataH", "triMSadByAm", "triMSadByaH"],
    "zazWI": ["triMSataH", "triMSatoH", "triMSatAm"],
    "saptamI": ["triMSati", "triMSatoH", "triMSatsu"],
    "saMboDana": ["triMSat", "triMSatO", "triMSataH"],
}
for _h in ["triMSat", "catvAriMSat", "paYcASat"]:
    # Fix sandhi d/t: triMSadByAm -> catvAriMSadByAm / paYcASadByAm
    # Replace prefix triMSa (6 chars) with stem of _h (triMSa/catvAriMSa/paYcASa)
    stem = _h[:-1]  # strip final t -> triMSa / catvAriMSa / paYcASa
    _tbl = {}
    for _vib, _vals in _triMSat_full.items():
        new_vals = []
        for v in _vals:
            if v.startswith("triMSa"):
                new_vals.append(stem + v[6:])
            else:
                new_vals.append(v.replace("triMSat", _h))
        _tbl[_vib] = new_vals
    NUMERALS[_h] = {"f": _tbl, "m": _tbl, "n": _tbl}
# zazwi, saptati, aSIti, navati – i-stem f like viMSati (replace viMSat prefix -> zazw/saptat/aSIt/navat)
for _h in ["zazwi", "saptati", "aSIti", "navati"]:
    stem_base = _h[:-1]  # zazw, saptat, aSIt, navat
    _tbl = {}
    for _vib, _vals in _viMSati_full.items():
        _tbl[_vib] = [v.replace("viMSat", stem_base, 1) if v.startswith("viMSat") else v for v in _vals]
    NUMERALS[_h] = {"f": _tbl, "m": _tbl, "n": _tbl}
# Satam (100), sahasram (1000) – a-n napuMsaka like Pala (regular neuter a-stem, not defective)
_Satam_full = {
    "prathamA": ["Satam", "Sate", "SatAni"],
    "dvitIyA": ["Satam", "Sate", "SatAni"],
    "tftIyA": ["Satena", "SatAByAm", "SataEH"],
    "caturTI": ["SatAya", "SatAByAm", "SateByaH"],
    "paYcamI": ["SatAt", "SatAByAm", "SateByaH"],
    "zazWI": ["Satasya", "SatayoH", "SatAnAm"],
    "saptamI": ["Sate", "SatayoH", "Satezu"],
    "saMboDana": ["Sata", "Sate", "SatAni"],
}
NUMERALS["Satam"] = {"n": _Satam_full, "m": _Satam_full, "f": _Satam_full}
NUMERALS["Sata"] = NUMERALS["Satam"]
_sahasra_full = {
    "prathamA": ["sahasram", "sahasre", "sahasrARi"],
    "dvitIyA": ["sahasram", "sahasre", "sahasrARi"],
    "tftIyA": ["sahasreRa", "sahasrAByAm", "sahasrEH"],
    "caturTI": ["sahasrAya", "sahasrAByAm", "sahasreByaH"],
    "paYcamI": ["sahasrAt", "sahasrAByAm", "sahasreByaH"],
    "zazWI": ["sahasrasya", "sahasrayoH", "sahasrARAm"],
    "saptamI": ["sahasre", "sahasrayoH", "sahasrezu"],
    "saMboDana": ["sahasra", "sahasre", "sahasrARi"],
}
NUMERALS["sahasram"] = {"n": _sahasra_full, "m": _sahasra_full, "f": _sahasra_full}
NUMERALS["sahasra"] = NUMERALS["sahasram"]

# Override specific numerals with correct forms
# zaz / zaR
NUMERALS["zaz"] = NUMERALS["zaR"] = {
    "m": {
        "prathamA": ["-", "-", "zat"],
        "dvitIyA": ["-", "-", "zat"],
        "tftIyA": ["-", "-", "zaRBiH"],
        "caturTI": ["-", "-", "zaRByaH"],
        "paYcamI": ["-", "-", "zaRByaH"],
        "zazWI": ["-", "-", "zaRRAm"],
        "saptamI": ["-", "-", "zaTsu"],
        "saMboDana": ["-", "-", "zat"],
    },
    "f": {
        "prathamA": ["-", "-", "zat"],
        "dvitIyA": ["-", "-", "zat"],
        "tftIyA": ["-", "-", "zaRBiH"],
        "caturTI": ["-", "-", "zaRByaH"],
        "paYcamI": ["-", "-", "zaRByaH"],
        "zazWI": ["-", "-", "zaRRAm"],
        "saptamI": ["-", "-", "zaTsu"],
        "saMboDana": ["-", "-", "zat"],
    },
    "n": {
        "prathamA": ["-", "-", "zat"],
        "dvitIyA": ["-", "-", "zat"],
        "tftIyA": ["-", "-", "zaRBiH"],
        "caturTI": ["-", "-", "zaRByaH"],
        "paYcamI": ["-", "-", "zaRByaH"],
        "zazWI": ["-", "-", "zaRRAm"],
        "saptamI": ["-", "-", "zaTsu"],
        "saMboDana": ["-", "-", "zat"],
    },
}
NUMERALS["zaR"]["m"] = NUMERALS["zaz"]["m"]
# ensure both keys point same
NUMERALS["paYcan"]["m"] = _paYcan_table
NUMERALS["paYcan"]["f"] = _paYcan_table
NUMERALS["paYcan"]["n"] = _paYcan_table
NUMERALS["paYca"] = NUMERALS["paYcan"]

# azwan has two variants (azwa / azwO)
NUMERALS["azwan"] = {
    "m": {
        "prathamA": ["-", "-", "azwO / azwa"],
        "dvitIyA": ["-", "-", "azwO / azwa"],
        "tftIyA": ["-", "-", "azwABiH"],
        "caturTI": ["-", "-", "azwAByaH"],
        "paYcamI": ["-", "-", "azwAByaH"],
        "zazWI": ["-", "-", "azwAnAm"],
        "saptamI": ["-", "-", "azwAsu"],
        "saMboDana": ["-", "-", "azwO / azwa"],
    },
    "f": {
        "prathamA": ["-", "-", "azwO / azwa"],
        "dvitIyA": ["-", "-", "azwO / azwa"],
        "tftIyA": ["-", "-", "azwABiH"],
        "caturTI": ["-", "-", "azwAByaH"],
        "paYcamI": ["-", "-", "azwAByaH"],
        "zazWI": ["-", "-", "azwAnAm"],
        "saptamI": ["-", "-", "azwAsu"],
        "saMboDana": ["-", "-", "azwO / azwa"],
    },
    "n": {
        "prathamA": ["-", "-", "azwO / azwa"],
        "dvitIyA": ["-", "-", "azwO / azwa"],
        "tftIyA": ["-", "-", "azwABiH"],
        "caturTI": ["-", "-", "azwAByaH"],
        "paYcamI": ["-", "-", "azwAByaH"],
        "zazWI": ["-", "-", "azwAnAm"],
        "saptamI": ["-", "-", "azwAsu"],
        "saMboDana": ["-", "-", "azwO / azwa"],
    },
}
NUMERALS["azwa"] = NUMERALS["azwan"]

# ---------------------------------------------------------------------------
# Core generation
# ---------------------------------------------------------------------------

def _generate_noun(word: str, paradigm: str) -> dict[str, list[str]]:
    meta = PARADIGMS[paradigm]
    ending = meta["ending"]
    table = meta["table"]
    # compute base
    if word.endswith(ending):
        base = word[: -len(ending)] if len(ending) <= len(word) else ""
    else:
        # fallback: treat word as base already? e.g., word "rAma" ending "a" -> base "rAm"
        # if not ends with expected, just use stripping heuristic: remove last char
        # but we try to use word[:-len(ending)] if possible, else word
        if len(ending) == 1:
            # generic strip last char
            base = word[:-1] if word else ""
        else:
            base = word
            # for an/in etc, if not matched, use word as base without suffix stripping and just add?
            # For generic case, better return base = word minus ending length approx
            base = word
    out: dict[str, list[str]] = {}
    for vib, suffixes in table.items():
        forms = []
        for suf in suffixes:
            if suf == "-":
                forms.append("-")
            else:
                forms.append(base + suf)
        out[vib] = forms
    return out

def _generate_generic_consonant(word: str) -> dict[str, list[str]]:
    base = word
    out: dict[str, list[str]] = {}
    for vib, suffixes in _GENERIC_CONS_TABLE.items():
        out[vib] = [base + s if s else base for s in suffixes]
    return out

def detect_paradigm(word: str, gender: str | None = None) -> list[str]:
    """Heuristic detection of paradigms for a given word+gender."""
    word = word.strip()
    if not word:
        return []
    candidates: list[str] = []
    # pronoun/numeral exact?
    low = word.lower()
    if low in PRONOUNS or word in PRONOUNS:
        return [f"pronoun:{word}"]
    if low in NUMERALS or word in NUMERALS:
        return [f"numeral:{word}"]
    # irregular pati/sakhi (and compounds like BU-pati, priya-sakhi) must override regular i_m (hari)
    if word == "pati" or word.endswith("pati"):
        if gender is None or gender == "m":
            return ["pati_m", "i_m"] if gender == "m" else ["pati_m"]
    if word == "sakhi" or word.endswith("sakhi"):
        if gender is None or gender == "m":
            return ["sakhi_m", "i_m"] if gender == "m" else ["sakhi_m"]
    # an-stem neuter nAman vs masculine rAjan – both end "an" so need lexicon
    if word in ("nAman", "brahman", "vyoman", "sAman", "Daman") or word.endswith("nAman"):
        if gender is None or gender == "n":
            return ["an_n", "an_m"] if gender == "n" else ["an_n"]
    if word in ("jagat", "Bavat") or word.endswith("jagat"):
        # jagat is neuter at-stem; Bavat masc is at_m, neut is at_n – use at_n for jagat
        if gender is None or gender == "n":
            # for gender None prefer at_n for jagat, for explicit n also at_n
            if word == "jagat" or word.endswith("jagat"):
                return ["at_n", "t_n"] if gender == "n" else ["at_n"]
    # manas neuter should be default for gender None (as_n before as_m already ensures this, but keep explicit)
    if word == "manas" and (gender is None or gender == "n"):
        return ["as_n", "as_m"] if gender == "n" else ["as_n"]
    # check endings longest first
    for paradigm, meta in sorted(PARADIGMS.items(), key=lambda x: -len(x[1]["ending"])):
        ending = meta["ending"]
        g = meta["gender"]
        if gender and g != gender:
            continue
        if word.endswith(ending):
            candidates.append(paradigm)
    # if no gender given, try any
    if not candidates and not gender:
        for paradigm, meta in sorted(PARADIGMS.items(), key=lambda x: -len(x[1]["ending"])):
            if word.endswith(meta["ending"]):
                candidates.append(paradigm)
    # fallback generic
    if not candidates:
        candidates = ["generic"]
    # deduplicate preserving order
    seen = set()
    uniq = []
    for c in candidates:
        if c not in seen:
            seen.add(c)
            uniq.append(c)
    return uniq

def decline_noun(word: str, gender: str | None = None, paradigm: str | None = None) -> dict[str, Any]:
    """Decline a noun given word, gender, optional paradigm."""
    word = word.strip()
    if not word:
        raise ValueError("word is empty")
    # auto gender if not provided: infer from ending?
    if paradigm is None:
        # detect
        candidates = detect_paradigm(word, gender)
        # pick first noun candidate
        noun_cands = [c for c in candidates if not c.startswith("pronoun") and not c.startswith("numeral") and c != "generic"]
        if noun_cands:
            paradigm = noun_cands[0]
        else:
            # generic
            paradigm = "generic"
    if paradigm == "generic":
        table = _generate_generic_consonant(word)
        desc = "generic consonant (halanta) – simplified"
        ending = ""
        gender_out = gender or "m"
    else:
        if paradigm not in PARADIGMS:
            raise ValueError(f"Unknown paradigm '{paradigm}'. Available: {', '.join(sorted(PARADIGMS))}")
        meta = PARADIGMS[paradigm]
        if gender and meta["gender"] != gender:
            # allow override but warn? We'll just use requested paradigm gender
            pass
        gender_out = meta["gender"] if not gender else gender
        desc = meta["desc"]
        ending = meta["ending"]
        table = _generate_noun(word, paradigm)
    return {
        "word": word,
        "gender": gender_out,
        "paradigm": paradigm,
        "ending": ending,
        "desc": desc,
        "forms": table,  # vibhakti -> [eka,dvi,bahu]
        "type": "noun",
    }

def decline_pronoun(word: str, gender: str | None = None) -> dict[str, Any]:
    """Decline pronoun. word is lemma like 'tad', 'etad', 'kim', 'idam', 'adas', 'asmad' etc.
    If gender provided, returns that gender table; else returns all genders.
    """
    key = word.strip()
    # normalize: map forms like saH, ezaH etc to lemma? We try to resolve pronoun forms to lemma.
    # If key is an inflected form, try to find which pronoun it belongs to – for now we require lemma.
    # But we provide alias mapping for common nominative forms.
    alias_map = {
        "saH": "tad", "sA": "tad", "tat": "tad",
        "ezaH": "etad", "ezA": "etad", "etat": "etad",
        "yaH": "yad", "yA": "yad", "yat": "yad",
        "kaH": "kim", "kA": "kim", "kim": "kim",
        "ayam": "idam", "iyam": "idam", "idam": "idam",
        "asO": "adas", "adaH": "adas",
        "aham": "asmad", "asmat": "asmad", "asmad": "asmad",
        "tvam": "yuzmad", "yuzmad": "yuzmad", "yusmad": "yuzmad",
    }
    if key in alias_map:
        key = alias_map[key]
    # also lower fallback
    if key not in PRONOUNS and key.lower() in PRONOUNS:
        key = key.lower()
    if key not in PRONOUNS:
        raise ValueError(f"Unknown pronoun '{word}'. Known: {', '.join(sorted(PRONOUNS))}")
    entry = PRONOUNS[key]
    if gender:
        if gender not in entry and "" not in entry:
            raise ValueError(f"Pronoun '{key}' has no gender '{gender}'. Available: {', '.join(entry)}")
        if gender in entry:
            table = entry[gender]
            return {"word": word, "lemma": key, "gender": gender, "forms": table, "type": "pronoun", "desc": f"pronoun {key} ({gender})"}
        else:
            # asmad/yusmad – gender '' 
            table = entry[""]
            return {"word": word, "lemma": key, "gender": gender, "forms": table, "type": "pronoun", "desc": f"pronoun {key}"}
    else:
        # return all genders: if single gender-less pronouns like asmad, return single
        if "" in entry and len(entry) == 1:
            return {"word": word, "lemma": key, "gender": "", "forms": entry[""], "type": "pronoun", "desc": f"pronoun {key}"}
        # else return dict of genders
        return {"word": word, "lemma": key, "genders": {g: tbl for g, tbl in entry.items()}, "type": "pronoun", "desc": f"pronoun {key} (all genders)"}

def decline_numeral(word: str, gender: str | None = None) -> dict[str, Any]:
    """Decline numeral. word is lemma like 'eka', 'dvi', 'tri', 'catur', 'paYcan' etc."""
    key = word.strip()
    if key not in NUMERALS and key.lower() in NUMERALS:
        key = key.lower()
    # also strip final 'n' if variant
    if key not in NUMERALS:
        # try without diacritic variations
        raise ValueError(f"Unknown numeral '{word}'. Known: {', '.join(sorted(NUMERALS)[:20])} ...")
    entry = NUMERALS[key]
    if gender:
        if gender not in entry:
            raise ValueError(f"Numeral '{key}' has no gender '{gender}'. Available: {', '.join(entry)}")
        return {"word": word, "lemma": key, "gender": gender, "forms": entry[gender], "type": "numeral", "desc": f"numeral {key} ({gender})"}
    else:
        if len(entry) == 1:
            # generic? Actually numerals have m/f/n but we return all
            pass
        return {"word": word, "lemma": key, "genders": entry, "type": "numeral", "desc": f"numeral {key} (all genders)"}

def decline(word: str, gender: str | None = None, paradigm: str | None = None, category: str | None = None) -> dict[str, Any]:
    """Unified entry point.
    
    Auto-detects whether word is noun/pronoun/numeral unless category forced.
    category: 'noun' | 'pronoun' | 'numeral' | None (auto)
    paradigm: noun paradigm key (a_m etc.) – only for nouns.
    gender: 'm'|'f'|'n'|''
    """
    word = word.strip()
    if not word:
        raise ValueError("word required")
    # explicit category
    if category == "pronoun":
        return decline_pronoun(word, gender)
    if category == "numeral":
        return decline_numeral(word, gender)
    if category == "noun":
        return decline_noun(word, gender, paradigm)

    # auto detect
    low = word
    low_lower = word.lower()
    # check pronoun lemmas
    if word in PRONOUNS or low_lower in PRONOUNS:
        try:
            return decline_pronoun(word, gender)
        except Exception:
            pass
    # also check if word is known pronoun inflected alias like saH
    alias_map = {"saH": "tad", "sA": "tad", "ezaH": "etad", "yaH": "yad", "kaH": "kim", "ayam": "idam", "asO": "adas", "aham": "asmad", "tvam": "yuzmad"}
    if word in alias_map:
        return decline_pronoun(alias_map[word], gender)
    # numerals
    if word in NUMERALS or low_lower in NUMERALS:
        return decline_numeral(word, gender)
    # also detect numerals like "eka" etc.
    if low_lower in ("eka", "dvi", "tri", "catur", "paYcan", "paYca", "zaz", "zaR", "saptan", "azwan", "navan", "daSan"):
        return decline_numeral(low_lower, gender)
    # fallback to noun
    # if paradigm explicitly given, treat as noun
    if paradigm:
        return decline_noun(word, gender, paradigm)
    # use gender hint: if word ends with A and gender f -> A_f etc.
    return decline_noun(word, gender, paradigm)

def get_declension(word: str, gender: str | None = None, paradigm: str | None = None, category: str | None = None) -> dict[str, Any]:
    """Alias for decline."""
    return decline(word, gender=gender, paradigm=paradigm, category=category)

def list_paradigms() -> list[dict[str, str]]:
    return [{"paradigm": k, "ending": v["ending"], "gender": v["gender"], "desc": v["desc"]} for k, v in sorted(PARADIGMS.items())]

def list_pronouns() -> list[str]:
    return sorted(PRONOUNS.keys())

def list_numerals() -> list[str]:
    return sorted(NUMERALS.keys())

def flatten_forms(result: dict[str, Any]) -> list[dict[str, str]]:
    """Flatten nested forms to list of rows [{vibhakti, vacana, form}] for display."""
    rows: list[dict[str, str]] = []
    forms = result.get("forms")
    if forms is not None:
        for vib in VIBHAKTIS:
            if vib not in forms:
                continue
            for idx, vac in enumerate(VACANAS):
                rows.append({"vibhakti": vib, "vacana": vac, "form": forms[vib][idx]})
        return rows
    # pronoun/numeral with genders
    if "genders" in result:
        for g, tbl in result["genders"].items():
            for vib in VIBHAKTIS:
                if vib not in tbl:
                    continue
                for idx, vac in enumerate(VACANAS):
                    rows.append({"gender": g, "vibhakti": vib, "vacana": vac, "form": tbl[vib][idx]})
        return rows
    return rows

def to_table(result: dict[str, Any]) -> str:
    """Pretty string table."""
    lines = []
    lines.append(f"# {result.get('word')}  [{result.get('type')}]  {result.get('desc','')}  gender={result.get('gender','') or ','.join(result.get('genders',{}))}  paradigm={result.get('paradigm','')}")
    # headers
    if "forms" in result:
        lines.append(f"{'vibhakti':12} | {'ekavacana':14} | {'dvivacana':14} | {'bahuvacana':14}")
        lines.append("-" * 60)
        for vib in VIBHAKTIS:
            if vib not in result["forms"]:
                continue
            e, d, b = result["forms"][vib]
            lines.append(f"{vib:12} | {e:14} | {d:14} | {b:14}")
    elif "genders" in result:
        for g, tbl in result["genders"].items():
            lines.append(f"\n## gender={g}")
            lines.append(f"{'vibhakti':12} | {'eka':14} | {'dvi':14} | {'bahu':14}")
            lines.append("-" * 60)
            for vib in VIBHAKTIS:
                if vib not in tbl:
                    continue
                e, d, b = tbl[vib]
                lines.append(f"{vib:12} | {e:14} | {d:14} | {b:14}")
    return "\n".join(lines)

# Quick CLI helper
def decline_to_dict(word: str, gender: str | None = None, paradigm: str | None = None, category: str | None = None) -> dict[str, Any]:
    res = decline(word, gender=gender, paradigm=paradigm, category=category)
    # add flat list for JSON convenience
    res["_flat"] = flatten_forms(res)
    return res

# ---------------------------------------------------------------------------
# Reverse analysis: given inflected form, find possible lemma + vibhakti/vacana
# ---------------------------------------------------------------------------

def _norm_loose(s: str) -> str:
    """Loose normalization for SLP1 search: R/n, S/s, N/n etc."""
    # Map retroflex / palatal variants to dental for fuzzy matching
    # This allows searching "Trampena" to match "TrampeRa" (eRa suffix)
    return s.replace("R", "n").replace("N", "n").replace("S", "s").replace("z", "s")

def analyze_form(word: str, limit: int = 20, loose: bool = True) -> list[dict[str, Any]]:
    """Analyze inflected nominal form -> list of possible analyses.
    Returns declension hits like {type:'noun', lemma, paradigm, gender, vibhakti, vacana, suffix, form}.
    Also includes pronoun/numeral hits.
    Loose mode allows R/n, S/s equivalence (so Trampena matches TrampeRa).
    """
    word = word.strip()
    if not word:
        return []
    hits: list[dict[str, Any]] = []
    word_norm = _norm_loose(word) if loose else word
    # --- pronouns: exact form match ---
    for lemma, genders in PRONOUNS.items():
        for g, tbl in genders.items():
            for vib, forms in tbl.items():
                for idx, f in enumerate(forms):
                    if f == "-" or f == "":
                        continue
                    f_norm = _norm_loose(f) if loose else f
                    if word == f or word_norm == f_norm:
                        hits.append({
                            "type": "pronoun",
                            "match_type": "pronoun",
                            "lemma": lemma,
                            "word": word,
                            "matched_form": f,
                            "gender": g or "m",
                            "vibhakti": vib,
                            "vacana": VACANAS[idx],
                            "paradigm": f"pronoun:{lemma}",
                            "paradigm_desc": f"pronoun {lemma}",
                            "suffix": f,
                        })
                        if len(hits) >= limit:
                            return hits[:limit]
    # --- numerals: exact form match (skip '-' ) ---
    for lemma, genders in NUMERALS.items():
        for g, tbl in genders.items():
            for vib, forms in tbl.items():
                for idx, f in enumerate(forms):
                    if f == "-" or f == "" or "/" in f:
                        # handle "azwO / azwa" variants split
                        parts = [p.strip() for p in f.split("/")]
                        for part in parts:
                            part_norm = _norm_loose(part) if loose else part
                            if word == part or word_norm == part_norm:
                                hits.append({
                                    "type": "numeral",
                                    "match_type": "numeral",
                                    "lemma": lemma,
                                    "word": word,
                                    "matched_form": part,
                                    "gender": g,
                                    "vibhakti": vib,
                                    "vacana": VACANAS[idx],
                                    "paradigm": f"numeral:{lemma}",
                                    "paradigm_desc": f"numeral {lemma}",
                                    "suffix": part,
                                })
                                if len(hits) >= limit:
                                    return hits[:limit]
                        continue
                    f_norm = _norm_loose(f) if loose else f
                    if word == f or word_norm == f_norm:
                        hits.append({
                            "type": "numeral",
                            "match_type": "numeral",
                            "lemma": lemma,
                            "word": word,
                            "matched_form": f,
                            "gender": g,
                            "vibhakti": vib,
                            "vacana": VACANAS[idx],
                            "paradigm": f"numeral:{lemma}",
                            "paradigm_desc": f"numeral {lemma}",
                            "suffix": f,
                        })
                        if len(hits) >= limit:
                            return hits[:limit]
    # --- nouns: suffix stripping → lemma reconstruction ---
    # For each paradigm, check suffix match
    # Sort paradigms by ending length desc so specific paradigms preferred, but for analysis sort by suffix length desc
    candidates: list[tuple[int, dict[str, Any]]] = []
    for paradigm, meta in PARADIGMS.items():
        ending = meta["ending"]
        gender = meta["gender"]
        table = meta["table"]
        desc = meta["desc"]
        for vib, suffixes in table.items():
            for idx, suf in enumerate(suffixes):
                if suf == "-" or suf == "":
                    continue
                # check if word ends with suffix (loose)
                suf_norm = _norm_loose(suf) if loose else suf
                if word_norm.endswith(suf_norm):
                    # need original suffix length = len(suf) (same as norm length because replacement 1:1)
                    if len(word) < len(suf):
                        continue
                    base = word[: len(word) - len(suf)] if len(suf) else word
                    lemma = base + ending
                    # Filter implausible lemmas: must end with ending (by construction it does) and base not empty
                    # Exception: pati_m/sakhi_m allow empty base (pati -> "", bhUpati -> "BU") for exact matches like patyA==suffix
                    if not lemma or (len(base) == 0 and paradigm not in ("pati_m", "sakhi_m")):
                        continue
                    # Score by suffix length (longer = more specific) and paradigm ending length
                    score = len(suf) * 10 + len(ending)
                    candidates.append((score, {
                        "type": "noun",
                        "match_type": "noun_declension",
                        "lemma": lemma,
                        "word": word,
                        "matched_form": word,
                        "paradigm": paradigm,
                        "paradigm_desc": desc,
                        "ending": ending,
                        "gender": gender,
                        "vibhakti": vib,
                        "vacana": VACANAS[idx],
                        "suffix": suf,
                        "base": base,
                    }))
    # Also generic halanta fallback
    for vib, suffixes in _GENERIC_CONS_TABLE.items():
        for idx, suf in enumerate(suffixes):
            if suf == "-" or suf == "":
                continue
            suf_norm = _norm_loose(suf) if loose else suf
            if word_norm.endswith(suf_norm):
                if len(word) < len(suf):
                    continue
                base = word[: len(word) - len(suf)] if len(suf) else word
                lemma = base  # generic: lemma is base itself (no ending)
                if not lemma:
                    continue
                score = len(suf) * 5  # lower priority than specific paradigms
                candidates.append((score, {
                    "type": "noun",
                    "match_type": "noun_declension_generic",
                    "lemma": lemma,
                    "word": word,
                    "matched_form": word,
                    "paradigm": "generic",
                    "paradigm_desc": "generic consonant (halanta) – simplified",
                    "ending": "",
                    "gender": "m",
                    "vibhakti": vib,
                    "vacana": VACANAS[idx],
                    "suffix": suf,
                    "base": base,
                }))
    # Sort by score desc, then paradigm name
    candidates.sort(key=lambda x: (-x[0], x[1]["paradigm"], x[1]["vibhakti"]))
    # Deduplicate by (lemma, paradigm, vibhakti, vacana)
    seen = set()
    for _, h in candidates:
        key = (h["lemma"], h["paradigm"], h["vibhakti"], h["vacana"])
        if key in seen:
            continue
        seen.add(key)
        hits.append(h)
        if len(hits) >= limit:
            break
    return hits[:limit]

def analyze(word: str, limit: int = 20, loose: bool = True, db_path=None, include_verb: bool = True) -> list[dict[str, Any]]:
    """Unified analyzer: verb conjugations + nominal declensions.
    Verb hits are prioritized first (exact DB match), then nominal declension.
    Returns combined hits with type field.
    """
    hits: list[dict[str, Any]] = []
    verb_hits: list[dict[str, Any]] = []
    # verb first (prioritized)
    if include_verb:
        try:
            from .query import search_forms as _search_forms
            verb_hits = _search_forms(word, exact=True, limit=limit, db_path=db_path)
            for h in verb_hits:
                h = dict(h)
                h["type"] = h.get("match_type", "conjugation")
                h["word"] = word
                h["lemma"] = h.get("dhatu", "")
                hits.append(h)
                if len(hits) >= limit:
                    return hits[:limit]
        except Exception:
            pass
    # nominal (remaining slots)
    try:
        remaining = limit - len(hits)
        if remaining > 0:
            nom = analyze_form(word, limit=remaining, loose=loose)
            hits.extend(nom)
    except Exception:
        pass
    return hits[:limit]


