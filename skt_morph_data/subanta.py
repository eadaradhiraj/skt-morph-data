"""Subanta (nominal) declension engine for Sanskrit.

Provides complete vibhakti tables for:
 - nouns (a/i/u/f etc. stems, masculine/feminine/neuter, halanta, irregulars)
 - pronouns (tad, etad, yad, kim, idam, adas, asmad, yuzmad, tyad, sarva etc.)
 - numerals (eka, dvi, tri, catur, paYcan, zaz, saptan, azwan, navan, daSan ...)

All inputs/outputs are SLP1 transliteration (like the dhatu DB).
Vocative (sambodhana) is included as 8th vibhakti.

Usage::

    from skt_morph_data.subanta import decline, decline_noun, decline_pronoun, decline_numeral

    decline("rAma", gender="m")          # auto-detect a-stem masculine
    decline("deva", gender="m")          # automatic natva (devena, devAnAm)
    decline("Pala", gender="n")          # neuter a-stem
    decline("kartf", gender="m")         # agent noun in -tf (kartA, kartArO, kartAraH)
    decline("pitf", gender="m")          # kinship noun (pitA, pitarO, pitaraH)
    decline("go", gender="m")            # o-stem (gOH, gAm, gavA, gave, goH, gavi)
    decline("Bavat", gender="m")         # honorific Bavat (BavAn, BavantO...)
    decline("daDi", gender="n")          # asthy-adi (daDi, daDinI, daDnA, daDne...)
    decline("aham")                      # personal pronoun
    decline("eka")                       # numeral

Paradigm keys (noun):
  a_m, a_n, A_f, i_m, pati_m, sakhi_m, i_f, i_n, asthi_n (daDi/akzi/asTi/sakTi),
  I_f (nadI), sri_f (SrI/hrI/DI), lakzmi_f, stri_f,
  u_m (guru), u_f (Denu), u_n (maDu), U_f (vaDU), bhu_f (BU/BrU),
  f_m (pitf kinship), tf_m (kartf agent noun), f_f (mAtf), svasf_f (svasf), f_n (dAtf),
  an_m (Atman), rajan_m (rAjan), an_n (nAman), karman_n (karman), in_m (yogin), in_n (balin),
  at_m (participle Bavat), bhavat_m (honorific Bavat), at_n (jagat), mahat_m, mahat_n,
  pathin_m (panTA), vat_m (Danavat), mat_m (budDimat), vidvas_m (vidvAn),
  yas_m (Sreyas m.), yas_n (Sreyas n.), as_n (manas), as_m/as_f (sumanas),
  us_n (danus), is_n (havis), c_f (vAc), t_m (marut), t_f (sarit), t_n (jagat),
  d_f (sampad), j_m (Bizaj), dis_f/dis_m (diS/viS),
  o_m/o_f (go), ahan_n (ahan), pums_m (pums), svan_m (Svan), yuvan_m (yuvan),
  ap_f (ap water), nau_f (nO), glau_m (glO), rai_m/rai_f (rE), etc.
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
# Paninian Natva (r/f/F/z -> n becomes R)
# ---------------------------------------------------------------------------
def apply_natva(s: str) -> str:
    """Applies Paninian natva (r/f/F/z -> n becomes R) within a pada.
    Follows Panini 8.4.1 (raṣābhyāṁ no ṇaḥ samānapade) and 8.4.2 (aṭkupvāṅnumvyavāye'pi).
    Blocks when intervening consonants are not in aṭ, ku, pu, or num (M).
    Protects padānta n per Panini 8.4.37 (padāntasya).
    """
    triggers = {'r', 'f', 'F', 'z'}
    at_ku_pu = set('aAiIuUfFxXeEoO' + 'yvrh' + 'kKgGN' + 'pPbBm' + 'M')
    chars = list(s)
    last_trig = -1
    for i, c in enumerate(chars):
        if c in triggers:
            last_trig = i
        elif c == 'n' and last_trig != -1:
            blocked = False
            for j in range(last_trig + 1, i):
                if chars[j] not in at_ku_pu:
                    blocked = True
                    break
            if not blocked:
                # padanta check: n at the very end does not change (e.g. rAmAn, rAjan)
                if i < len(chars) - 1 and chars[i + 1] in set('aAiIuUfFxXeEoO' + 'myvn'):
                    chars[i] = 'R'
    return ''.join(chars)

# ---------------------------------------------------------------------------
# Helper to build paradigm tables
# Stores suffixes to be added to "base" (stem minus ending).
# For each paradigm we store dict vibhakti -> [eka,dvi,bahu] suffixes
# ---------------------------------------------------------------------------

def _add_base(base: str, suffix: str) -> str:
    return base + suffix

PARADIGMS: dict[str, dict[str, Any]] = {}

def _register(paradigm: str, ending: str, gender: str, desc: str, table: dict[str, list[str]]):
    PARADIGMS[paradigm] = {
        "ending": ending,
        "gender": gender,
        "desc": desc,
        "table": table,
    }

# ---------------------------------------------------------------------------
# Vowel Stems (Ajanta)
# ---------------------------------------------------------------------------

# a_kArAnta puMliNga  rAma / deva
_register("a_m", "a", "m", "a-kArAnta puMliNga (rAma)", {
    "prathamA": ["aH", "O", "AH"],
    "dvitIyA": ["am", "O", "An"],
    "tftIyA": ["ena", "AByAm", "EH"],
    "caturTI": ["Aya", "AByAm", "eByaH"],
    "paYcamI": ["At", "AByAm", "eByaH"],
    "zazWI": ["asya", "ayoH", "AnAm"],
    "saptamI": ["e", "ayoH", "ezu"],
    "saMboDana": ["a", "O", "AH"],
})

# a_kArAnta napuMsaka  Pala
_register("a_n", "a", "n", "a-kArAnta napuMsaka (Pala)", {
    "prathamA": ["am", "e", "Ani"],
    "dvitIyA": ["am", "e", "Ani"],
    "tftIyA": ["ena", "AByAm", "EH"],
    "caturTI": ["Aya", "AByAm", "eByaH"],
    "paYcamI": ["At", "AByAm", "eByaH"],
    "zazWI": ["asya", "ayoH", "AnAm"],
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
    "zazWI": ["AyAH", "ayoH", "AnAm"],
    "saptamI": ["AyAm", "ayoH", "Asu"],
    "saMboDana": ["e", "e", "AH"],
})

# i_kArAnta puMliNga  hari
_register("i_m", "i", "m", "i-kArAnta puMliNga (hari)", {
    "prathamA": ["iH", "I", "ayaH"],
    "dvitIyA": ["im", "I", "In"],
    "tftIyA": ["inA", "iByAm", "iBiH"],
    "caturTI": ["aye", "iByAm", "iByaH"],
    "paYcamI": ["eH", "iByAm", "iByaH"],
    "zazWI": ["eH", "yoH", "InAm"],
    "saptamI": ["O", "yoH", "izu"],
    "saMboDana": ["e", "I", "ayaH"],
})

# pati - irregular i_kArAnta puMliNga (pati uncompounded: patyA, patye, patyuH, patyO)
# Note: In compounds (BUpati, nfpati), declined regularly like hari (Pāṇini 1.4.8 patiḥ samāsa eva)
_register("pati_m", "pati", "m", "i-kArAnta puMliNga (pati) - irregular uncompounded", {
    "prathamA": ["patiH", "patI", "patayaH"],
    "dvitIyA": ["patim", "patI", "patIn"],
    "tftIyA": ["patyA", "patiByAm", "patiBiH"],
    "caturTI": ["patye", "patiByAm", "patiByaH"],
    "paYcamI": ["patyuH", "patiByAm", "patiByaH"],
    "zazWI": ["patyuH", "patyoH", "patInAm"],
    "saptamI": ["patyO", "patyoH", "patizu"],
    "saMboDana": ["pate", "patI", "patayaH"],
})

# sakhi - irregular i_kArAnta puMliNga (sakhi: sakhA, sakhAyO, sakhAyaH)
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

# i_kArAnta strIliNga  mati
_register("i_f", "i", "f", "i-kArAnta strIliNga (mati)", {
    "prathamA": ["iH", "I", "ayaH"],
    "dvitIyA": ["im", "I", "IH"],
    "tftIyA": ["yA", "iByAm", "iBiH"],
    "caturTI": ["aye / yE", "iByAm", "iByaH"],
    "paYcamI": ["eH / yAH", "iByAm", "iByaH"],
    "zazWI": ["eH / yAH", "yoH", "InAm"],
    "saptamI": ["O / yAm", "yoH", "izu"],
    "saMboDana": ["e", "I", "ayaH"],
})

# i_kArAnta napuMsaka  vAri
_register("i_n", "i", "n", "i-kArAnta napuMsaka (vAri)", {
    "prathamA": ["i", "inI", "Ini"],
    "dvitIyA": ["i", "inI", "Ini"],
    "tftIyA": ["inA", "iByAm", "iBiH"],
    "caturTI": ["ine", "iByAm", "iByaH"],
    "paYcamI": ["inaH", "iByAm", "iByaH"],
    "zazWI": ["inaH", "inoH", "InAm"],
    "saptamI": ["ini", "inoH", "izu"],
    "saMboDana": ["i / e", "inI", "Ini"],
})

# asthy-adi irregular neuter i-stems (daDi, akzi, asTi, sakTi - Panini 7.1.75)
_register("asthi_n", "i", "n", "i-kArAnta napuMsaka (daDi/akzi/asTi/sakTi) - irregular", {
    "prathamA": ["i", "inI", "Ini"],
    "dvitIyA": ["i", "inI", "Ini"],
    "tftIyA": ["nA", "iByAm", "iBiH"],
    "caturTI": ["ne", "iByAm", "iByaH"],
    "paYcamI": ["naH", "iByAm", "iByaH"],
    "zazWI": ["naH", "noH", "nAm"],
    "saptamI": ["ni / ani", "noH", "izu"],
    "saMboDana": ["i / e", "inI", "Ini"],
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

# SrI / hrI / DI root I-stem taking iyaṅ (Panini 6.4.77)
_register("sri_f", "SrI", "f", "I-kArAnta strIliNga (SrI/hrI/DI) - iyaN-AdeSa", {
    "prathamA": ["SrIH", "SriyO", "SriyaH"],
    "dvitIyA": ["Sriyam", "SriyO", "SriyaH / SrIH"],
    "tftIyA": ["SriyA", "SrIByAm", "SrIBiH"],
    "caturTI": ["Sriye / SriyE", "SrIByAm", "SrIByaH"],
    "paYcamI": ["SriyaH / SriyAH", "SrIByAm", "SrIByaH"],
    "zazWI": ["SriyaH / SriyAH", "SriyoH", "SriyAm / SrIRAm"],
    "saptamI": ["Sriyi / SriyAm", "SriyoH", "SrIzu"],
    "saMboDana": ["SrIH", "SriyO", "SriyaH"],
})

# lakzmI - like nadI but nom sg has visarga (lakzmIH)
_register("lakzmi_f", "lakzmI", "f", "I-kArAnta strIliNga (lakzmI)", {
    "prathamA": ["lakzmIH", "lakzmyO", "lakzmyaH"],
    "dvitIyA": ["lakzmIm", "lakzmyO", "lakzmIH"],
    "tftIyA": ["lakzmyA", "lakzmIByAm", "lakzmIBiH"],
    "caturTI": ["lakzmyE", "lakzmIByAm", "lakzmIByaH"],
    "paYcamI": ["lakzmyAH", "lakzmIByAm", "lakzmIByaH"],
    "zazWI": ["lakzmyAH", "lakzmyoH", "lakzmInAm"],
    "saptamI": ["lakzmyAm", "lakzmyoH", "lakzmIzu"],
    "saMboDana": ["lakzmi", "lakzmyO", "lakzmyaH"],
})

# strI - irregular I-stem (strI, striyam/strIm, striyA, striyE)
_register("stri_f", "strI", "f", "I-kArAnta strIliNga (strI) - irregular", {
    "prathamA": ["strI", "striyO", "striyaH"],
    "dvitIyA": ["striyam / strIm", "striyO", "striyaH / strIH"],
    "tftIyA": ["striyA", "strIByAm", "strIBiH"],
    "caturTI": ["striyE", "strIByAm", "strIByaH"],
    "paYcamI": ["striyAH", "strIByAm", "strIByaH"],
    "zazWI": ["striyAH", "striyoH", "strIRAm"],
    "saptamI": ["striyAm", "striyoH", "strIzu"],
    "saMboDana": ["stri", "striyO", "striyaH"],
})

# u_kArAnta puM  guru
_register("u_m", "u", "m", "u-kArAnta puMliNga (guru)", {
    "prathamA": ["uH", "U", "avaH"],
    "dvitIyA": ["um", "U", "Un"],
    "tftIyA": ["unA", "uByAm", "uBiH"],
    "caturTI": ["ave", "uByAm", "uByaH"],
    "paYcamI": ["oH", "uByAm", "uByaH"],
    "zazWI": ["oH", "voH", "UnAm"],
    "saptamI": ["O", "voH", "uzu"],
    "saMboDana": ["o", "U", "avaH"],
})

# u_kArAnta strI  Denu
_register("u_f", "u", "f", "u-kArAnta strIliNga (Denu)", {
    "prathamA": ["uH", "U", "avaH"],
    "dvitIyA": ["um", "U", "UH"],
    "tftIyA": ["vA", "uByAm", "uBiH"],
    "caturTI": ["ave / vE", "uByAm", "uByaH"],
    "paYcamI": ["oH / vAH", "uByAm", "uByaH"],
    "zazWI": ["oH / vAH", "voH", "UnAm"],
    "saptamI": ["O / vAm", "voH", "uzu"],
    "saMboDana": ["o", "U", "avaH"],
})

# u_kArAnta napu  maDu
_register("u_n", "u", "n", "u-kArAnta napuMsaka (maDu)", {
    "prathamA": ["u", "unI", "Uni"],
    "dvitIyA": ["u", "unI", "Uni"],
    "tftIyA": ["unA", "uByAm", "uBiH"],
    "caturTI": ["une", "uByAm", "uByaH"],
    "paYcamI": ["unaH", "uByAm", "uByaH"],
    "zazWI": ["unaH", "unoH", "UnAm"],
    "saptamI": ["uni", "unoH", "uzu"],
    "saMboDana": ["u / o", "unI", "Uni"],
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

# BU / BrU root U-stem taking uvaṅ (Panini 6.4.77)
_register("bhu_f", "BU", "f", "U-kArAnta strIliNga (BU/BrU) - uvaN-AdeSa", {
    "prathamA": ["BUH", "BuvO", "BuvaH"],
    "dvitIyA": ["Buvam", "BuvO", "BuvaH"],
    "tftIyA": ["BuvA", "BUByAm", "BUBiH"],
    "caturTI": ["Buve / BuvE", "BUByAm", "BUByaH"],
    "paYcamI": ["BuvaH / BuvAH", "BUByAm", "BUByaH"],
    "zazWI": ["BuvaH / BuvAH", "BuvoH", "BuvAm / BUnAm"],
    "saptamI": ["Buvi / BuvAm", "BuvoH", "BUzu"],
    "saMboDana": ["BUH", "BuvO", "BuvaH"],
})

# f_kArAnta puM  pitf (kinship nouns: pitf, BrAtf, jAmAtf - guṇa ar in strong cases)
_register("f_m", "f", "m", "f-kArAnta puMliNga (pitf - kinship: guRa ar)", {
    "prathamA": ["A", "arO", "araH"],
    "dvitIyA": ["aram", "arO", "Fn"],
    "tftIyA": ["rA", "fByAm", "fBiH"],
    "caturTI": ["re", "fByAm", "fByaH"],
    "paYcamI": ["uH", "fByAm", "fByaH"],
    "zazWI": ["uH", "roH", "FnAm"],
    "saptamI": ["ari", "roH", "fzu"],
    "saMboDana": ["aH", "arO", "araH"],
})

# tf_m agent nouns in -tf and naptf (kartf, dAtf, netf - vṛddhi Ar in strong cases, Panini 7.3.34)
_register("tf_m", "f", "m", "f-kArAnta puMliNga agent noun (kartf/dAtf - vfdi Ar)", {
    "prathamA": ["A", "ArO", "AraH"],
    "dvitIyA": ["Aram", "ArO", "Fn"],
    "tftIyA": ["rA", "fByAm", "fBiH"],
    "caturTI": ["re", "fByAm", "fByaH"],
    "paYcamI": ["uH", "fByAm", "fByaH"],
    "zazWI": ["uH", "roH", "FnAm"],
    "saptamI": ["ari", "roH", "fzu"],
    "saMboDana": ["aH", "ArO", "AraH"],
})

# f_kArAnta strI  mAtf (mAtf, duhitf)
_register("f_f", "f", "f", "f-kArAnta strIliNga (mAtf)", {
    "prathamA": ["A", "arO", "araH"],
    "dvitIyA": ["aram", "arO", "FH"],
    "tftIyA": ["rA", "fByAm", "fBiH"],
    "caturTI": ["re", "fByAm", "fByaH"],
    "paYcamI": ["uH", "fByAm", "fByaH"],
    "zazWI": ["uH", "roH", "FnAm"],
    "saptamI": ["ari", "roH", "fzu"],
    "saMboDana": ["aH", "arO", "araH"],
})

# svasf (sister) - takes Ar in strong cases (svasA, svasArO, svasAraH)
_register("svasf_f", "f", "f", "f-kArAnta strIliNga (svasf - vfdi Ar)", {
    "prathamA": ["A", "ArO", "AraH"],
    "dvitIyA": ["Aram", "ArO", "FH"],
    "tftIyA": ["rA", "fByAm", "fBiH"],
    "caturTI": ["re", "fByAm", "fByaH"],
    "paYcamI": ["uH", "fByAm", "fByaH"],
    "zazWI": ["uH", "roH", "FnAm"],
    "saptamI": ["ari", "roH", "fzu"],
    "saMboDana": ["aH", "ArO", "AraH"],
})

# f_kArAnta napuMsaka  dAtf n.
_register("f_n", "f", "n", "f-kArAnta napuMsaka (dAtf)", {
    "prathamA": ["f", "fnI", "FnI"],
    "dvitIyA": ["f", "fnI", "FnI"],
    "tftIyA": ["fnA", "fByAm", "fBiH"],
    "caturTI": ["fne", "fByAm", "fByaH"],
    "paYcamI": ["fnaH", "fByAm", "fByaH"],
    "zazWI": ["fnaH", "fnoH", "FnAm"],
    "saptamI": ["fni", "fnoH", "fzu"],
    "saMboDana": ["f", "fnI", "FnI"],
})

# ---------------------------------------------------------------------------
# Diphthong Stems
# ---------------------------------------------------------------------------

# o-kArAnta go (m/f: bull/cow) - Panini 6.1.93 auto'mśasoḥ, 6.1.110 ṅasiṅyośca
_register("o_m", "go", "m", "o-kArAnta puMliNga (go - bull)", {
    "prathamA": ["gOH", "gAvO", "gAvaH"],
    "dvitIyA": ["gAm", "gAvO", "gAH"],
    "tftIyA": ["gavA", "goByAm", "goBiH"],
    "caturTI": ["gave", "goByAm", "goByaH"],
    "paYcamI": ["goH", "goByAm", "goByaH"],
    "zazWI": ["goH", "gavoH", "gavAm"],
    "saptamI": ["gavi", "gavoH", "gozu"],
    "saMboDana": ["gOH", "gAvO", "gAvaH"],
})
_register("o_f", "go", "f", "o-kArAnta strIliNga (go - cow)", {
    "prathamA": ["gOH", "gAvO", "gAvaH"],
    "dvitIyA": ["gAm", "gAvO", "gAH"],
    "tftIyA": ["gavA", "goByAm", "goBiH"],
    "caturTI": ["gave", "goByAm", "goByaH"],
    "paYcamI": ["goH", "goByAm", "goByaH"],
    "zazWI": ["goH", "gavoH", "gavAm"],
    "saptamI": ["gavi", "gavoH", "gozu"],
    "saMboDana": ["gOH", "gAvO", "gAvaH"],
})

# nO (nau - boat, f.)
_register("nau_f", "nO", "f", "O-kArAnta strIliNga (nO - boat)", {
    "prathamA": ["nOH", "nAvO", "nAvaH"],
    "dvitIyA": ["nAvam", "nAvO", "nAvaH"],
    "tftIyA": ["nAvA", "nOByAm", "nOBiH"],
    "caturTI": ["nAve", "nOByAm", "nOByaH"],
    "paYcamI": ["nAvaH", "nOByAm", "nOByaH"],
    "zazWI": ["nAvaH", "nAvoH", "nAvAm"],
    "saptamI": ["nAvi", "nAvoH", "nOzu"],
    "saMboDana": ["nOH", "nAvO", "nAvaH"],
})

# glO (glau - moon, m.)
_register("glau_m", "glO", "m", "O-kArAnta puMliNga (glO - moon)", {
    "prathamA": ["glOH", "glAvO", "glAvaH"],
    "dvitIyA": ["glAvam", "glAvO", "glAvaH"],
    "tftIyA": ["glAvA", "glOByAm", "glOBiH"],
    "caturTI": ["glAve", "glOByAm", "glOByaH"],
    "paYcamI": ["glAvaH", "glOByAm", "glOByaH"],
    "zazWI": ["glAvaH", "glAvoH", "glAvAm"],
    "saptamI": ["glAvi", "glAvoH", "glOzu"],
    "saMboDana": ["glOH", "glAvO", "glAvaH"],
})

# rE (rai - wealth, m./f.)
_register("rai_m", "rE", "m", "E-kArAnta puMliNga (rE - wealth)", {
    "prathamA": ["rAH", "rAyO", "rAyaH"],
    "dvitIyA": ["rAyam", "rAyO", "rAyaH"],
    "tftIyA": ["rAyA", "rAByAm", "rABiH"],
    "caturTI": ["rAye", "rAByAm", "rAByaH"],
    "paYcamI": ["rAyaH", "rAByAm", "rAByaH"],
    "zazWI": ["rAyaH", "rAyoH", "rAyAm"],
    "saptamI": ["rAyi", "rAyoH", "rAsu"],
    "saMboDana": ["rAH", "rAyO", "rAyaH"],
})
_register("rai_f", "rE", "f", "E-kArAnta strIliNga (rE - wealth)", {
    "prathamA": ["rAH", "rAyO", "rAyaH"],
    "dvitIyA": ["rAyam", "rAyO", "rAyaH"],
    "tftIyA": ["rAyA", "rAByAm", "rABiH"],
    "caturTI": ["rAye", "rAByAm", "rAByaH"],
    "paYcamI": ["rAyaH", "rAByAm", "rAByaH"],
    "zazWI": ["rAyaH", "rAyoH", "rAyAm"],
    "saptamI": ["rAyi", "rAyoH", "rAsu"],
    "saMboDana": ["rAH", "rAyO", "rAyaH"],
})

# ---------------------------------------------------------------------------
# Consonant Stems (Halanta)
# ---------------------------------------------------------------------------

# an-stem rAjan (m) - drops 'a' (Panini 6.4.134 allopo'naḥ), j+n -> jY (ścutva)
_register("rajan_m", "an", "m", "an-kArAnta puMliNga (rAjan)", {
    "prathamA": ["A", "AnO", "AnaH"],
    "dvitIyA": ["Anam", "AnO", "YaH"],
    "tftIyA": ["YA", "aByAm", "aBiH"],
    "caturTI": ["Ye", "aByAm", "aByaH"],
    "paYcamI": ["YaH", "aByAm", "aByaH"],
    "zazWI": ["YaH", "YoH", "YAm"],
    "saptamI": ["Yi / ani", "YoH", "asu"],
    "saMboDana": ["an", "AnO", "AnaH"],
})

# an-stem Atman / regular an-stem (m) - conjunct with m/v: no elision (Panini 6.4.135 na saṁyogād vamantāt)
_register("an_m", "an", "m", "an-kArAnta puMliNga (Atman/brahman m.)", {
    "prathamA": ["A", "AnO", "AnaH"],
    "dvitIyA": ["Anam", "AnO", "anaH"],
    "tftIyA": ["anA", "aByAm", "aBiH"],
    "caturTI": ["ane", "aByAm", "aByaH"],
    "paYcamI": ["anaH", "aByAm", "aByaH"],
    "zazWI": ["anaH", "anoH", "anAm"],
    "saptamI": ["ani", "anoH", "asu"],
    "saMboDana": ["an", "AnO", "AnaH"],
})

# an-stem nAman (n) - simple consonant before an: elision nAmnA, nAmne
_register("an_n", "an", "n", "an-kArAnta napuMsaka (nAman)", {
    "prathamA": ["a", "nI / anI", "Ani"],
    "dvitIyA": ["a", "nI / anI", "Ani"],
    "tftIyA": ["nA", "aByAm", "aBiH"],
    "caturTI": ["ne", "aByAm", "aByaH"],
    "paYcamI": ["naH", "aByAm", "aByaH"],
    "zazWI": ["naH", "noH", "nAm"],
    "saptamI": ["ni / ani", "noH", "asu"],
    "saMboDana": ["a", "nI / anI", "Ani"],
})

# an-stem karman (n) - conjunct with m/v: no elision (karmaRA, karmaRe)
_register("karman_n", "an", "n", "an-kArAnta napuMsaka (karman - no elision)", {
    "prathamA": ["a", "anI", "Ani"],
    "dvitIyA": ["a", "anI", "Ani"],
    "tftIyA": ["anA", "aByAm", "aBiH"],
    "caturTI": ["ane", "aByAm", "aByaH"],
    "paYcamI": ["anaH", "aByAm", "aByaH"],
    "zazWI": ["anaH", "anoH", "anAm"],
    "saptamI": ["ani", "anoH", "asu"],
    "saMboDana": ["a", "anI", "Ani"],
})

# in-stem yogin (m)
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

# in-stem balin / dAnin (n)
_register("in_n", "in", "n", "in-kArAnta napuMsaka (balin/dAnin)", {
    "prathamA": ["i", "inI", "Ini"],
    "dvitIyA": ["i", "inI", "Ini"],
    "tftIyA": ["inA", "iByAm", "iBiH"],
    "caturTI": ["ine", "iByAm", "iByaH"],
    "paYcamI": ["inaH", "iByAm", "iByaH"],
    "zazWI": ["inaH", "inoH", "inAm"],
    "saptamI": ["ini", "inoH", "izu"],
    "saMboDana": ["i / in", "inI", "Ini"],
})

# at-stem participle (Bavat m., gacchat m.)
_register("at_m", "at", "m", "at-kArAnta puMliNga participle (Bavat/gacchat)", {
    "prathamA": ["an", "antO", "antaH"],
    "dvitIyA": ["antam", "antO", "ataH"],
    "tftIyA": ["atA", "adByAm", "adBiH"],
    "caturTI": ["ate", "adByAm", "adByaH"],
    "paYcamI": ["ataH", "adByAm", "adByaH"],
    "zazWI": ["ataH", "atoH", "atAm"],
    "saptamI": ["ati", "atoH", "atsu"],
    "saMboDana": ["an", "antO", "antaH"],
})

# Bavat honorific pronoun / noun ("You, sir" - BavAn)
_register("bhavat_m", "Bavat", "m", "at-kArAnta puMliNga honorific (Bavat - BavAn)", {
    "prathamA": ["BavAn", "BavantO", "BavantaH"],
    "dvitIyA": ["Bavantam", "BavantO", "BavataH"],
    "tftIyA": ["BavatA", "BavadByAm", "BavadBiH"],
    "caturTI": ["Bavate", "BavadByAm", "BavadByaH"],
    "paYcamI": ["BavataH", "BavadByAm", "BavadByaH"],
    "zazWI": ["BavataH", "BavatoH", "BavatAm"],
    "saptamI": ["Bavati", "BavatoH", "Bavatsu"],
    "saMboDana": ["Bavan", "BavantO", "BavantaH"],
})

# at-stem neuter (jagat / Bavat n.)
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

# mahat (great, m.) - Panini 7.1.84 mahataḥ pūjāyām (long A in sarvanāmasthāna)
_register("mahat_m", "mahat", "m", "at-kArAnta puMliNga (mahat - mahAn)", {
    "prathamA": ["mahAn", "mahAntO", "mahAntaH"],
    "dvitIyA": ["mahAntam", "mahAntO", "mahataH"],
    "tftIyA": ["mahatA", "mahadByAm", "mahadBiH"],
    "caturTI": ["mahate", "mahadByAm", "mahadByaH"],
    "paYcamI": ["mahataH", "mahadByAm", "mahadByaH"],
    "zazWI": ["mahataH", "mahatoH", "mahatAm"],
    "saptamI": ["mahati", "mahatoH", "mahatsu"],
    "saMboDana": ["mahan", "mahAntO", "mahAntaH"],
})

# mahat (great, n.) - mahat, mahatI, mahAnti
_register("mahat_n", "mahat", "n", "at-kArAnta napuMsaka (mahat)", {
    "prathamA": ["mahat", "mahatI", "mahAnti"],
    "dvitIyA": ["mahat", "mahatI", "mahAnti"],
    "tftIyA": ["mahatA", "mahadByAm", "mahadBiH"],
    "caturTI": ["mahate", "mahadByAm", "mahadByaH"],
    "paYcamI": ["mahataH", "mahadByAm", "mahadByaH"],
    "zazWI": ["mahataH", "mahatoH", "mahatAm"],
    "saptamI": ["mahati", "mahatoH", "mahatsu"],
    "saMboDana": ["mahat", "mahatI", "mahAnti"],
})

# pathin irregular (panTA) - Panini 7.1.86 pathimathyṛbhukṣāmāt
_register("pathin_m", "paTin", "m", "in-kArAnta puMliNga (pathin) - irregular", {
    "prathamA": ["panTAH", "panTAnO", "panTAnaH"],
    "dvitIyA": ["panTAnam", "panTAnO", "paTaH"],
    "tftIyA": ["paTA", "paTiByAm", "paTiBiH"],
    "caturTI": ["paTe", "paTiByAm", "paTiByaH"],
    "paYcamI": ["paTaH", "paTiByAm", "paTiByaH"],
    "zazWI": ["paTaH", "paToH", "paTAm"],
    "saptamI": ["paTi", "paToH", "paTsu"],
    "saMboDana": ["panTAH", "panTAnO", "panTAnaH"],
})

# vat/mat (matup) – dhanavat, buddhimat
_register("vat_m", "vat", "m", "vat-kArAnta puMliNga (dhanavat) - matup", {
    "prathamA": ["vAn", "vantO", "vantaH"],
    "dvitIyA": ["vantam", "vantO", "vataH"],
    "tftIyA": ["vatA", "vadByAm", "vadBiH"],
    "caturTI": ["vate", "vadByAm", "vadByaH"],
    "paYcamI": ["vataH", "vadByAm", "vadByaH"],
    "zazWI": ["vataH", "vatoH", "vatAm"],
    "saptamI": ["vati", "vatoH", "vatsu"],
    "saMboDana": ["van", "vantO", "vantaH"],
})

_register("mat_m", "mat", "m", "mat-kArAnta puMliNga (buddhimat) - matup", {
    "prathamA": ["mAn", "mantO", "mantaH"],
    "dvitIyA": ["mantam", "mantO", "mataH"],
    "tftIyA": ["matA", "madByAm", "madBiH"],
    "caturTI": ["mate", "madByAm", "madByaH"],
    "paYcamI": ["mataH", "madByAm", "madByaH"],
    "zazWI": ["mataH", "matoH", "matAm"],
    "saptamI": ["mati", "matoH", "matsu"],
    "saMboDana": ["man", "mantO", "mantaH"],
})

# vidvas (scholar, vas-participle) - Panini 6.4.131 vasoḥ samprasāraṇam
_register("vidvas_m", "vidvas", "m", "vas-kArAnta puMliNga (vidvas) - samprasAraRa", {
    "prathamA": ["vidvAn", "vidvAMsO", "vidvAMsaH"],
    "dvitIyA": ["vidvAMsam", "vidvAMsO", "viduzaH"],
    "tftIyA": ["viduzA", "vidvadByAm", "vidvadBiH"],
    "caturTI": ["viduze", "vidvadByAm", "vidvadByaH"],
    "paYcamI": ["viduzaH", "vidvadByAm", "vidvadByaH"],
    "zazWI": ["viduzaH", "viduzoH", "viduzAm"],
    "saptamI": ["viduzi", "viduzoH", "vidvatsu"],
    "saMboDana": ["vidvan", "vidvAMsO", "vidvAMsaH"],
})

# comparatives in -Iyas / -yas (Sreyas, balIyas - m.)
_register("yas_m", "yas", "m", "Iyas-kArAnta puMliNga comparative (Sreyas)", {
    "prathamA": ["yAn", "yAMsO", "yAMsaH"],
    "dvitIyA": ["yAMsam", "yAMsO", "yasaH"],
    "tftIyA": ["yasA", "yoByAm", "yoBiH"],
    "caturTI": ["yase", "yoByAm", "yoByaH"],
    "paYcamI": ["yasaH", "yoByAm", "yoByaH"],
    "zazWI": ["yasaH", "yasoH", "yasAm"],
    "saptamI": ["yasi", "yasoH", "yaHsu"],
    "saMboDana": ["yan", "yAMsO", "yAMsaH"],
})

# comparatives in -Iyas / -yas (Sreyas n.)
_register("yas_n", "yas", "n", "Iyas-kArAnta napuMsaka comparative (Sreyas)", {
    "prathamA": ["yaH", "yasI", "yAMsi"],
    "dvitIyA": ["yaH", "yasI", "yAMsi"],
    "tftIyA": ["yasA", "yoByAm", "yoBiH"],
    "caturTI": ["yase", "yoByAm", "yoByaH"],
    "paYcamI": ["yasaH", "yoByAm", "yoByaH"],
    "zazWI": ["yasaH", "yasoH", "yasAm"],
    "saptamI": ["yasi", "yasoH", "yaHsu"],
    "saMboDana": ["yaH", "yasI", "yAMsi"],
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

# as-stem bahuvrIhi masculine/feminine (sumanas)
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

# is-stem havis (n)
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

# c-stem vAc (f)
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

# t-stem marut (m), sarit (f), jagat (n)
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

# d-stem sampad / Apad / vipad (f)
_register("d_f", "d", "f", "d-kArAnta strIliNga (sampad)", {
    "prathamA": ["t", "dO", "daH"],
    "dvitIyA": ["dam", "dO", "daH"],
    "tftIyA": ["dA", "dByAm", "dBiH"],
    "caturTI": ["de", "dByAm", "dByaH"],
    "paYcamI": ["daH", "dByAm", "dByaH"],
    "zazWI": ["daH", "doH", "dAm"],
    "saptamI": ["di", "doH", "tsu"],
    "saMboDana": ["t", "dO", "daH"],
})

# j-stem Bizaj / ftvij (m)
_register("j_m", "j", "m", "j-kArAnta puMliNga (Bizaj)", {
    "prathamA": ["k", "jO", "jaH"],
    "dvitIyA": ["jam", "jO", "jaH"],
    "tftIyA": ["jA", "GByAm", "GBiH"],
    "caturTI": ["je", "GByAm", "GByaH"],
    "paYcamI": ["jaH", "GByAm", "GByaH"],
    "zazWI": ["jaH", "joH", "jAm"],
    "saptamI": ["ji", "joH", "kzu"],
    "saMboDana": ["k", "jO", "jaH"],
})

# palatal sibilant diS (f.) / viS (m.)
_register("dis_f", "diS", "f", "S-kArAnta strIliNga (diS)", {
    "prathamA": ["dik", "diSO", "diSaH"],
    "dvitIyA": ["diSam", "diSO", "diSaH"],
    "tftIyA": ["diSA", "digByAm", "digBiH"],
    "caturTI": ["diSe", "digByAm", "digByaH"],
    "paYcamI": ["diSaH", "digByAm", "digByaH"],
    "zazWI": ["diSaH", "diSoH", "diSAm"],
    "saptamI": ["diSi", "diSoH", "dikzu"],
    "saMboDana": ["dik", "diSO", "diSaH"],
})
_register("dis_m", "diS", "m", "S-kArAnta puMliNga (viS)", {
    "prathamA": ["dik", "diSO", "diSaH"],
    "dvitIyA": ["diSam", "diSO", "diSaH"],
    "tftIyA": ["diSA", "digByAm", "digBiH"],
    "caturTI": ["diSe", "digByAm", "digByaH"],
    "paYcamI": ["diSaH", "digByAm", "digByaH"],
    "zazWI": ["diSaH", "diSoH", "diSAm"],
    "saptamI": ["diSi", "diSoH", "dikzu"],
    "saMboDana": ["dik", "diSO", "diSaH"],
})

# ahan (day, n.) - Panini 8.2.68
_register("ahan_n", "ahan", "n", "an-kArAnta napuMsaka (ahan - day)", {
    "prathamA": ["ahaH", "ahnI / ahanI", "ahAni"],
    "dvitIyA": ["ahaH", "ahnI / ahanI", "ahAni"],
    "tftIyA": ["ahnA", "ahoByAm", "ahoBiH"],
    "caturTI": ["ahne", "ahoByAm", "ahoByaH"],
    "paYcamI": ["ahnaH", "ahoByAm", "ahoByaH"],
    "zazWI": ["ahnaH", "ahnoH", "ahnAm"],
    "saptamI": ["ahni / ahani", "ahnoH", "ahaHsu"],
    "saMboDana": ["ahaH", "ahnI / ahanI", "ahAni"],
})

# pums (man, m.) - Panini 7.1.89 pumso'suṅ
_register("pums_m", "pums", "m", "s-kArAnta puMliNga (pums - man)", {
    "prathamA": ["pumAn", "pumAMsO", "pumAMsaH"],
    "dvitIyA": ["pumAMsam", "pumAMsO", "puMsaH"],
    "tftIyA": ["puMsA", "pumByAm", "pumBiH"],
    "caturTI": ["puMse", "pumByAm", "pumByaH"],
    "paYcamI": ["puMsaH", "pumByAm", "pumByaH"],
    "zazWI": ["puMsaH", "puMsoH", "puMsAm"],
    "saptamI": ["puMsi", "puMsoH", "puMsu"],
    "saMboDana": ["puman", "pumAMsO", "pumAMsaH"],
})

# Svan (dog, m.) - Panini 6.4.133 samprasāraṇa (SunA, Sune, SunaH)
_register("svan_m", "Svan", "m", "an-kArAnta puMliNga (Svan - dog) - samprasAraRa", {
    "prathamA": ["SvA", "SvAnO", "SvAnaH"],
    "dvitIyA": ["SvAnam", "SvAnO", "SunaH"],
    "tftIyA": ["SunA", "SvaByAm", "SvaBiH"],
    "caturTI": ["Sune", "SvaByAm", "SvaByaH"],
    "paYcamI": ["SunaH", "SvaByAm", "SvaByaH"],
    "zazWI": ["SunaH", "SunoH", "SunAm"],
    "saptamI": ["Suni", "SunoH", "Svasu"],
    "saMboDana": ["Svan", "SvAnO", "SvAnaH"],
})

# yuvan (youth, m.) - samprasāraṇa (yUnA, yUne, yUnaH)
_register("yuvan_m", "yuvan", "m", "an-kArAnta puMliNga (yuvan - youth) - samprasAraRa", {
    "prathamA": ["yuvA", "yuvAnO", "yuvAnaH"],
    "dvitIyA": ["yuvAnam", "yuvAnO", "yUnaH"],
    "tftIyA": ["yUnA", "yuvaByAm", "yuvaBiH"],
    "caturTI": ["yUne", "yuvaByAm", "yuvaByaH"],
    "paYcamI": ["yUnaH", "yuvaByAm", "yuvaByaH"],
    "zazWI": ["yUnaH", "yUnoH", "yUnAm"],
    "saptamI": ["yUni", "yUnoH", "yuvasu"],
    "saMboDana": ["yuvan", "yuvAnO", "yuvAnaH"],
})

# ap (water, f. nitya-bahuvacana)
_register("ap_f", "ap", "f", "p-kArAnta strIliNga (ap - water, plural only)", {
    "prathamA": ["-", "-", "ApaH"],
    "dvitIyA": ["-", "-", "apaH"],
    "tftIyA": ["-", "-", "adBiH"],
    "caturTI": ["-", "-", "adByaH"],
    "paYcamI": ["-", "-", "adByaH"],
    "zazWI": ["-", "-", "apAm"],
    "saptamI": ["-", "-", "apsu"],
    "saMboDana": ["-", "-", "ApaH"],
})

# generic consonant fallback
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
# Pronouns
# ---------------------------------------------------------------------------

PRONOUNS: dict[str, Any] = {}

def _pronoun_table(forms: dict[str, dict[str, list[str]]]) -> dict[str, dict[str, list[str]]]:
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
        "saMboDana": ["-", "-", "-"],
    }),
    "f": _pronoun_table({
        "prathamA": ["sA", "te", "tAH"],
        "dvitIyA": ["tAm", "te", "tAH"],
        "tftIyA": ["tayA", "tAByAm", "tABiH"],
        "caturTI": ["tasyE", "tAByAm", "tAByaH"],
        "paYcamI": ["tasyAH", "tAByAm", "tAByaH"],
        "zazWI": ["tasyAH", "tayoH", "tAsAm"],
        "saptamI": ["tasyAm", "tayoH", "tAsu"],
        "saMboDana": ["-", "-", "-"],
    }),
    "n": _pronoun_table({
        "prathamA": ["tat", "te", "tAni"],
        "dvitIyA": ["tat", "te", "tAni"],
        "tftIyA": ["tena", "tAByAm", "tEH"],
        "caturTI": ["tasmE", "tAByAm", "teByaH"],
        "paYcamI": ["tasmAt", "tAByAm", "teByaH"],
        "zazWI": ["tasya", "tayoH", "tezAm"],
        "saptamI": ["tasmin", "tayoH", "tezu"],
        "saMboDana": ["-", "-", "-"],
    }),
}

# etad – m/f/n
PRONOUNS["etad"] = {
    "m": _pronoun_table({
        "prathamA": ["ezaH", "etO", "ete"],
        "dvitIyA": ["etam", "etO", "etAn"],
        "tftIyA": ["etena", "etAByAm", "etEH"],
        "caturTI": ["etasmE", "etAByAm", "eteByaH"],
        "paYcamI": ["etasmAt", "etAByAm", "eteByaH"],
        "zazWI": ["etasya", "etayoH", "etezAm"],
        "saptamI": ["etasmin", "etayoH", "etezu"],
        "saMboDana": ["-", "-", "-"],
    }),
    "f": _pronoun_table({
        "prathamA": ["ezA", "ete", "etAH"],
        "dvitIyA": ["etAm", "ete", "etAH"],
        "tftIyA": ["etayA", "etAByAm", "etABiH"],
        "caturTI": ["etasyE", "etAByAm", "etAByaH"],
        "paYcamI": ["etasyAH", "etAByAm", "etAByaH"],
        "zazWI": ["etasyAH", "etayoH", "etAsAm"],
        "saptamI": ["etasyAm", "etayoH", "etAsu"],
        "saMboDana": ["-", "-", "-"],
    }),
    "n": _pronoun_table({
        "prathamA": ["etat", "ete", "etAni"],
        "dvitIyA": ["etat", "ete", "etAni"],
        "tftIyA": ["etena", "etAByAm", "etEH"],
        "caturTI": ["etasmE", "etAByAm", "eteByaH"],
        "paYcamI": ["etasmAt", "etAByAm", "eteByaH"],
        "zazWI": ["etasya", "etayoH", "etezAm"],
        "saptamI": ["etasmin", "etayoH", "etezu"],
        "saMboDana": ["-", "-", "-"],
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
        "saMboDana": ["-", "-", "-"],
    }),
    "f": _pronoun_table({
        "prathamA": ["yA", "ye", "yAH"],
        "dvitIyA": ["yAm", "ye", "yAH"],
        "tftIyA": ["yayA", "yAByAm", "yABiH"],
        "caturTI": ["yasyE", "yAByAm", "yAByaH"],
        "paYcamI": ["yasyAH", "yAByAm", "yAByaH"],
        "zazWI": ["yasyAH", "yayoH", "yAsAm"],
        "saptamI": ["yasyAm", "yayoH", "yAsu"],
        "saMboDana": ["-", "-", "-"],
    }),
    "n": _pronoun_table({
        "prathamA": ["yat", "ye", "yAni"],
        "dvitIyA": ["yat", "ye", "yAni"],
        "tftIyA": ["yena", "yAByAm", "yEH"],
        "caturTI": ["yasmE", "yAByAm", "yeByaH"],
        "paYcamI": ["yasmAt", "yAByAm", "yeByaH"],
        "zazWI": ["yasya", "yayoH", "yezAm"],
        "saptamI": ["yasmin", "yayoH", "yezu"],
        "saMboDana": ["-", "-", "-"],
    }),
}

# tyad – m/f/n (that)
PRONOUNS["tyad"] = {
    "m": _pronoun_table({
        "prathamA": ["syaH", "tyO", "tye"],
        "dvitIyA": ["tyam", "tyO", "tyAn"],
        "tftIyA": ["tyena", "tyAByAm", "tyEH"],
        "caturTI": ["tyasmE", "tyAByAm", "tyeByaH"],
        "paYcamI": ["tyasmAt", "tyAByAm", "tyeByaH"],
        "zazWI": ["tyasya", "tyayoH", "tyezAm"],
        "saptamI": ["tyasmin", "tyayoH", "tyezu"],
        "saMboDana": ["-", "-", "-"],
    }),
    "f": _pronoun_table({
        "prathamA": ["syA", "tye", "tyAH"],
        "dvitIyA": ["tyAm", "tye", "tyAH"],
        "tftIyA": ["tyayA", "tyAByAm", "tyABiH"],
        "caturTI": ["tyasyE", "tyAByAm", "tyAByaH"],
        "paYcamI": ["tyasyAH", "tyAByAm", "tyAByaH"],
        "zazWI": ["tyasyAH", "tyayoH", "tyAsAm"],
        "saptamI": ["tyasyAm", "tyayoH", "tyAsu"],
        "saMboDana": ["-", "-", "-"],
    }),
    "n": _pronoun_table({
        "prathamA": ["tyat", "tye", "tyAni"],
        "dvitIyA": ["tyat", "tye", "tyAni"],
        "tftIyA": ["tyena", "tyAByAm", "tyEH"],
        "caturTI": ["tyasmE", "tyAByAm", "tyeByaH"],
        "paYcamI": ["tyasmAt", "tyAByAm", "tyeByaH"],
        "zazWI": ["tyasya", "tyayoH", "tyezAm"],
        "saptamI": ["tyasmin", "tyayoH", "tyezu"],
        "saMboDana": ["-", "-", "-"],
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
        "saMboDana": ["-", "-", "-"],
    }),
    "f": _pronoun_table({
        "prathamA": ["kA", "ke", "kAH"],
        "dvitIyA": ["kAm", "ke", "kAH"],
        "tftIyA": ["kayA", "kAByAm", "kABiH"],
        "caturTI": ["kasyE", "kAByAm", "kAByaH"],
        "paYcamI": ["kasyAH", "kAByAm", "kAByaH"],
        "zazWI": ["kasyAH", "kayoH", "kAsAm"],
        "saptamI": ["kasyAm", "kayoH", "kAsu"],
        "saMboDana": ["-", "-", "-"],
    }),
    "n": _pronoun_table({
        "prathamA": ["kim", "ke", "kAni"],
        "dvitIyA": ["kim", "ke", "kAni"],
        "tftIyA": ["kena", "kAByAm", "kEH"],
        "caturTI": ["kasmE", "kAByAm", "keByaH"],
        "paYcamI": ["kasmAt", "kAByAm", "keByaH"],
        "zazWI": ["kasya", "kayoH", "kezAm"],
        "saptamI": ["kasmin", "kayoH", "kezu"],
        "saMboDana": ["-", "-", "-"],
    }),
}

# idam – m/f/n
PRONOUNS["idam"] = {
    "m": _pronoun_table({
        "prathamA": ["ayam", "imO", "ime"],
        "dvitIyA": ["imam / enam", "imO / enO", "imAn / enAn"],
        "tftIyA": ["anena / enena", "AByAm", "eBiH"],
        "caturTI": ["asmE", "AByAm", "eByaH"],
        "paYcamI": ["asmAt", "AByAm", "eByaH"],
        "zazWI": ["asya", "anayoH / enayoH", "ezAm"],
        "saptamI": ["asmin", "anayoH / enayoH", "ezu"],
        "saMboDana": ["-", "-", "-"],
    }),
    "f": _pronoun_table({
        "prathamA": ["iyam", "ime", "imAH"],
        "dvitIyA": ["imAm / enAm", "ime / ene", "imAH / enAH"],
        "tftIyA": ["anayA / enayA", "AByAm", "ABiH"],
        "caturTI": ["asyE", "AByAm", "AByaH"],
        "paYcamI": ["asyAH", "AByAm", "AByaH"],
        "zazWI": ["asyAH", "anayoH / enayoH", "AsAm"],
        "saptamI": ["asyAm", "anayoH / enayoH", "Asu"],
        "saMboDana": ["-", "-", "-"],
    }),
    "n": _pronoun_table({
        "prathamA": ["idam", "ime", "imAni"],
        "dvitIyA": ["idam / enat", "ime / ene", "imAni / enAni"],
        "tftIyA": ["anena / enena", "AByAm", "eBiH"],
        "caturTI": ["asmE", "AByAm", "eByaH"],
        "paYcamI": ["asmAt", "AByAm", "eByaH"],
        "zazWI": ["asya", "anayoH / enayoH", "ezAm"],
        "saptamI": ["asmin", "anayoH / enayoH", "ezu"],
        "saMboDana": ["-", "-", "-"],
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
        "saMboDana": ["-", "-", "-"],
    }),
    "f": _pronoun_table({
        "prathamA": ["asO", "amU", "amUH"],
        "dvitIyA": ["amUm", "amU", "amUH"],
        "tftIyA": ["amuyA", "amUByAm", "amUBiH"],
        "caturTI": ["amuzyE", "amUByAm", "amUByaH"],
        "paYcamI": ["amuzyAH", "amUByAm", "amUByaH"],
        "zazWI": ["amuzyAH", "amuyoH", "amUzAm"],
        "saptamI": ["amuzyAm", "amuyoH", "amUzu"],
        "saMboDana": ["-", "-", "-"],
    }),
    "n": _pronoun_table({
        "prathamA": ["adaH", "amU", "amUni"],
        "dvitIyA": ["adaH", "amU", "amUni"],
        "tftIyA": ["amunA", "amUByAm", "amIBiH"],
        "caturTI": ["amuzmE", "amUByAm", "amIByaH"],
        "paYcamI": ["amuzmAt", "amUByAm", "amIByaH"],
        "zazWI": ["amuzya", "amuyoH", "amIzAm"],
        "saptamI": ["amuzmin", "amuyoH", "amIzu"],
        "saMboDana": ["-", "-", "-"],
    }),
}

# sarva-ādi pronouns
_SARVA_PRONOUN_M = {
    "prathamA": ["aH", "O", "e"],
    "dvitIyA": ["am", "O", "An"],
    "tftIyA": ["ena", "AByAm", "EH"],
    "caturTI": ["asmE", "AByAm", "eByaH"],
    "paYcamI": ["asmAt", "AByAm", "eByaH"],
    "zazWI": ["asya", "ayoH", "ezAm"],
    "saptamI": ["asmin", "ayoH", "ezu"],
    "saMboDana": ["a", "O", "e"],
}
_SARVA_PRONOUN_F = {
    "prathamA": ["A", "e", "AH"],
    "dvitIyA": ["Am", "e", "AH"],
    "tftIyA": ["ayA", "AByAm", "ABiH"],
    "caturTI": ["asyE", "AByAm", "AByaH"],
    "paYcamI": ["asyAH", "AByAm", "AByaH"],
    "zazWI": ["asyAH", "ayoH", "AsAm"],
    "saptamI": ["asyAm", "ayoH", "Asu"],
    "saMboDana": ["e", "e", "AH"],
}
_SARVA_PRONOUN_N = {
    "prathamA": ["am", "e", "Ani"],
    "dvitIyA": ["am", "e", "Ani"],
    "tftIyA": ["ena", "AByAm", "EH"],
    "caturTI": ["asmE", "AByAm", "eByaH"],
    "paYcamI": ["asmAt", "AByAm", "eByaH"],
    "zazWI": ["asya", "ayoH", "ezAm"],
    "saptamI": ["asmin", "ayoH", "ezu"],
    "saMboDana": ["am", "e", "Ani"],
}

# ḍatara/ḍatama class words take -at/-ad in neuter prathamA/dvitIyA (Panini 7.1.25)
_DATARA_WORDS = {"anya", "anyatara", "itara", "katara", "katama"}

for _w in ["sarva", "viSva", "uBa", "uBaya", "katara", "katama", "anya", "anyatara", "itara", "para", "apara", "DakziRa", "pUrva", "avara", "uttara", "aDara", "alpa", "sva"]:
    if _w == "uBa":
        PRONOUNS[_w] = {
            "m": {"prathamA": ["-", "uBO", "-"], "dvitIyA": ["-", "uBO", "-"], "tftIyA": ["-", "uBAByAm", "-"], "caturTI": ["-", "uBAByAm", "-"], "paYcamI": ["-", "uBAByAm", "-"], "zazWI": ["-", "uBayoH", "-"], "saptamI": ["-", "uBayoH", "-"], "saMboDana": ["-", "uBO", "-"]},
            "f": {"prathamA": ["-", "uBe", "-"], "dvitIyA": ["-", "uBe", "-"], "tftIyA": ["-", "uBAByAm", "-"], "caturTI": ["-", "uBAByAm", "-"], "paYcamI": ["-", "uBAByAm", "-"], "zazWI": ["-", "uBayoH", "-"], "saptamI": ["-", "uBayoH", "-"], "saMboDana": ["-", "uBe", "-"]},
            "n": {"prathamA": ["-", "uBe", "-"], "dvitIyA": ["-", "uBe", "-"], "tftIyA": ["-", "uBAByAm", "-"], "caturTI": ["-", "uBAByAm", "-"], "paYcamI": ["-", "uBAByAm", "-"], "zazWI": ["-", "uBayoH", "-"], "saptamI": ["-", "uBayoH", "-"], "saMboDana": ["-", "uBe", "-"]},
        }
        continue
    base = _w[:-1] if _w.endswith("a") else _w
    if _w == "uBaya":
        base = "uBay"

    n_table = dict(_SARVA_PRONOUN_N)
    if _w in _DATARA_WORDS:
        n_table["prathamA"] = ["at", "e", "Ani"]
        n_table["dvitIyA"] = ["at", "e", "Ani"]
        n_table["saMboDana"] = ["at", "e", "Ani"]

    PRONOUNS[_w] = {
        "m": {v: [apply_natva(base + s) for s in sufs] for v, sufs in _SARVA_PRONOUN_M.items()},
        "f": {v: [apply_natva(base + s) for s in sufs] for v, sufs in _SARVA_PRONOUN_F.items()},
        "n": {v: [apply_natva(base + s) for s in sufs] for v, sufs in n_table.items()},
    }

# asmad / yuzmad – personal pronouns (no gender, enclitics only in 2, 4, 6)
PRONOUNS["asmad"] = {
    "": _pronoun_table({
        "prathamA": ["aham", "AvAm", "vayam"],
        "dvitIyA": ["mAm / mA", "AvAm / nO", "asmAn / naH"],
        "tftIyA": ["mayA", "AvAByAm", "asmABiH"],
        "caturTI": ["mahyam / me", "AvAByAm / nO", "asmaByam / naH"],
        "paYcamI": ["mat", "AvAByAm", "asmat"],
        "zazWI": ["mama / me", "AvayoH / nO", "asmAkam / naH"],
        "saptamI": ["mayi", "AvayoH", "asmAsu"],
        "saMboDana": ["-", "-", "-"],
    })
}
PRONOUNS["yuzmad"] = {
    "": _pronoun_table({
        "prathamA": ["tvam", "yuvAm", "yUyam"],
        "dvitIyA": ["tvAm / tvA", "yuvAm / vAm", "yuzmAn / vaH"],
        "tftIyA": ["tvayA", "yuvAByAm", "yuzmABiH"],
        "caturTI": ["tuByam / te", "yuvAByAm / vAm", "yuzmaByam / vaH"],
        "paYcamI": ["tvat", "yuvAByAm", "yuzmat"],
        "zazWI": ["tava / te", "yuvayoH / vAm", "yuzmAkam / vaH"],
        "saptamI": ["tvayi", "yuvayoH", "yuzmAsu"],
        "saMboDana": ["-", "-", "-"],
    })
}
# aliases
PRONOUNS["yusmad"] = PRONOUNS["yuzmad"]
PRONOUNS["aHam"] = PRONOUNS["asmad"]
PRONOUNS["aham"] = PRONOUNS["asmad"]

# ---------------------------------------------------------------------------
# Numerals
# ---------------------------------------------------------------------------

NUMERALS: dict[str, Any] = {}

# eka – singular only (3 genders)
NUMERALS["eka"] = {
    "m": _pronoun_table({
        "prathamA": ["ekaH", "-", "-"],
        "dvitIyA": ["ekam", "-", "-"],
        "tftIyA": ["ekena", "-", "-"],
        "caturTI": ["ekasmE", "-", "-"],
        "paYcamI": ["ekasmAt", "-", "-"],
        "zazWI": ["ekasya", "-", "-"],
        "saptamI": ["ekasmin", "-", "-"],
        "saMboDana": ["eka", "-", "-"],
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

# catur – plural only
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

# 5..19 – indeclinables plural only (paYcan, saptan, navan, daSan etc.)
def _make_numeral_table_5_to_19(stem: str) -> dict[str, list[str]]:
    base = stem[:-1] if stem.endswith("a") else stem
    return {
        "prathamA": ["-", "-", stem],
        "dvitIyA": ["-", "-", stem],
        "tftIyA": ["-", "-", f"{stem}BiH"],
        "caturTI": ["-", "-", f"{stem}ByaH"],
        "paYcamI": ["-", "-", f"{stem}ByaH"],
        "zazWI": ["-", "-", f"{base}AnAm"],
        "saptamI": ["-", "-", f"{stem}su"],
        "saMboDana": ["-", "-", stem],
    }

for _lem in ["paYcan", "paYca", "saptan", "sapta", "navan", "nava", "daSan", "daSa", "ekAdaSan", "ekAdaSa", "dvAdaSan", "dvAdaSa", "trayodaSan", "trayodaSa", "caturdaSan", "caturdaSa", "paYcadaSan", "paYcadaSa", "zoDaSan", "zoDaSa", "saptadaSan", "saptadaSa", "azwAdaSan", "azwAdaSa", "navadaSan", "navadaSa"]:
    _clean = _lem.replace(" ", "")
    _stem = _clean.rstrip("n")
    _tbl = _make_numeral_table_5_to_19(_stem)
    NUMERALS[_clean] = {"m": _tbl, "f": _tbl, "n": _tbl}
    NUMERALS[_stem] = {"m": _tbl, "f": _tbl, "n": _tbl}

# zaz / zaR / zaw
_zaz_table = {
    "prathamA": ["-", "-", "zat / zaw"],
    "dvitIyA": ["-", "-", "zat / zaw"],
    "tftIyA": ["-", "-", "zaRBiH"],
    "caturTI": ["-", "-", "zaRByaH"],
    "paYcamI": ["-", "-", "zaRByaH"],
    "zazWI": ["-", "-", "zaRRAm"],
    "saptamI": ["-", "-", "zaTsu / zawsu"],
    "saMboDana": ["-", "-", "zat / zaw"],
}
NUMERALS["zaz"] = NUMERALS["zaR"] = NUMERALS["zaw"] = {"m": _zaz_table, "f": _zaz_table, "n": _zaz_table}

# azwan has two variants (azwO / azwa)
_azwan_table = {
    "prathamA": ["-", "-", "azwO / azwa"],
    "dvitIyA": ["-", "-", "azwO / azwa"],
    "tftIyA": ["-", "-", "azwABiH / azwaBiH"],
    "caturTI": ["-", "-", "azwAByaH / azwaByaH"],
    "paYcamI": ["-", "-", "azwAByaH / azwaByaH"],
    "zazWI": ["-", "-", "azwAnAm"],
    "saptamI": ["-", "-", "azwAsu / azwasu"],
    "saMboDana": ["-", "-", "azwO / azwa"],
}
NUMERALS["azwan"] = NUMERALS["azwa"] = NUMERALS["azwO"] = {"m": _azwan_table, "f": _azwan_table, "n": _azwan_table}

# Higher numerals: viMSati etc. are feminine nouns (decline fully)
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
    stem = _h[:-1]
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

for _h in ["zazwi", "saptati", "aSIti", "navati"]:
    stem_base = _h[:-1]
    _tbl = {}
    for _vib, _vals in _viMSati_full.items():
        _tbl[_vib] = [v.replace("viMSat", stem_base, 1) if v.startswith("viMSat") else v for v in _vals]
    NUMERALS[_h] = {"f": _tbl, "m": _tbl, "n": _tbl}

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
NUMERALS["Satam"] = NUMERALS["Sata"] = {"n": _Satam_full, "m": _Satam_full, "f": _Satam_full}

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
NUMERALS["sahasram"] = NUMERALS["sahasra"] = {"n": _sahasra_full, "m": _sahasra_full, "f": _sahasra_full}

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
        if len(ending) == 1:
            base = word[:-1] if word else ""
        else:
            base = word
    out: dict[str, list[str]] = {}
    for vib, suffixes in table.items():
        forms = []
        for suf in suffixes:
            if suf == "-":
                forms.append("-")
            else:
                if " / " in suf:
                    parts = [apply_natva(base + p.strip()) for p in suf.split("/")]
                    forms.append(" / ".join(parts))
                else:
                    forms.append(apply_natva(base + suf))
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

    # asthy-adi irregular neuter i-stems (daDi, akzi, asTi, sakTi)
    if word in ("daDi", "akzi", "asTi", "sakTi"):
        if gender is None or gender == "n":
            return ["asthi_n", "i_n"]

    # irregular pati (uncompounded) vs compounds (BUpati declines like hari: Panini 1.4.8)
    if word == "pati":
        if gender is None or gender == "m":
            return ["pati_m", "i_m"] if gender == "m" else ["pati_m"]
    elif word.endswith("pati"):
        if gender is None or gender == "m":
            return ["i_m"]

    # irregular sakhi
    if word == "sakhi" or word.endswith("sakhi"):
        if gender is None or gender == "m":
            return ["sakhi_m", "i_m"] if gender == "m" else ["sakhi_m"]

    # o-stem go (bull / cow)
    if word == "go" or word.endswith("go"):
        if gender == "f":
            return ["o_f"]
        elif gender == "m":
            return ["o_m"]
        else:
            return ["o_m", "o_f"]

    # root vowels SrI, BU, strI, lakzmI
    if word in ("SrI", "hrI", "DI") or word.endswith("SrI"):
        return ["sri_f"]
    if word in ("BU", "BrU") or (word.endswith("BU") and len(word) <= 4):
        return ["bhu_f"]
    if word == "strI" or word.endswith("strI"):
        return ["stri_f"]
    if word == "lakzmI" or word.endswith("lakzmI"):
        return ["lakzmi_f"]

    # diphthongs nO, glO, rE
    if word in ("nO", "nau") or word.endswith("nO"):
        return ["nau_f"]
    if word in ("glO", "glau") or word.endswith("glO"):
        return ["glau_m"]
    if word in ("rE", "rai") or word.endswith("rE"):
        return ["rai_f"] if gender == "f" else ["rai_m", "rai_f"]

    # special irregulars: ahan, pums, Svan, yuvan, ap, diS
    if word == "ahan" or word.endswith("ahan"):
        return ["ahan_n"]
    if word in ("pums", "pumAMs") or word.endswith("pums"):
        return ["pums_m"]
    if word == "Svan" or word.endswith("Svan"):
        return ["svan_m"]
    if word == "yuvan" or word.endswith("yuvan"):
        return ["yuvan_m"]
    if word == "ap":
        return ["ap_f"]
    if word in ("diS", "dfS", "viS") or word.endswith("diS"):
        return ["dis_f"] if gender != "m" else ["dis_m"]
    if word in ("sampad", "vipad", "Apad") or (word.endswith("pad") and len(word) > 3):
        return ["d_f"]
    if word in ("Bizaj", "ftvij"):
        return ["j_m"]

    # vidvas (scholar)
    if word in ("vidvas", "vidvAn") or word.endswith("vidvas"):
        return ["vidvas_m"]

    # mahat (great)
    if word == "mahat" or word.endswith("mahat"):
        if gender in (None, "m"):
            return ["mahat_m", "at_m"]
        elif gender == "n":
            return ["mahat_n", "at_n"]

    # Bavat: honorific bhavan (bhavat_m) vs participle (at_m) vs neuter (at_n) vs feminine (I_f)
    if word == "Bavat" or word == "BavAt":
        if gender == "n":
            return ["at_n"]
        elif gender == "f":
            return ["I_f"]
        elif gender == "m":
            return ["bhavat_m", "at_m"]
        else:
            return ["bhavat_m", "at_m"]

    if word == "jagat" or word.endswith("jagat"):
        return ["at_n", "t_n"] if gender == "n" else ["at_n"]

    # comparatives in -yas (Sreyas, balIyas, garIyas)
    if word.endswith("yas"):
        if gender in (None, "m"):
            return ["yas_m", "as_m"]
        elif gender == "n":
            return ["yas_n", "as_n"]

    # an-stem neuter karman (conjunct) vs nAman (simple) vs masculine rAjan vs Atman
    if word == "rAjan" or word.endswith("rAjan"):
        return ["rajan_m"]
    if word in ("karman", "janman", "parvan", "varman", "carman", "veSman", "BAsman") or word.endswith("karman"):
        return ["karman_n"] if gender in (None, "n") else ["karman_n", "an_m"]
    if word in ("nAman", "brahman", "vyoman", "sAman", "DAman") or word.endswith("nAman"):
        if word == "brahman" and gender == "m":
            return ["an_m"]
        return ["an_n", "an_m"] if gender == "n" else ["an_n"]
    if word == "Atman" or word.endswith("Atman"):
        return ["an_m"]

    # f-stem: agent nouns in -tf (kartf, dAtf) take vṛddhi Ar (tf_m); kinship (pitf, BrAtf) take guṇa ar (f_m)
    if word.endswith("f"):
        if gender == "f":
            if word == "svasf":
                return ["svasf_f", "f_f"]
            return ["f_f"]
        elif gender == "n":
            return ["f_n"]
        else:
            if word in ("pitf", "BrAtf", "jAmAtf", "devf"):
                return ["f_m"]
            return ["tf_m", "f_m"]

    if word == "manas" and (gender is None or gender == "n"):
        return ["as_n", "as_m"] if gender == "n" else ["as_n"]

    # pathin compounds
    if word.endswith("paTin") and (gender is None or gender == "m"):
        return ["pathin_m", "in_m"] if gender == "m" else ["pathin_m"]

    # check endings longest first
    for paradigm, meta in sorted(PARADIGMS.items(), key=lambda x: -len(x[1]["ending"])):
        ending = meta["ending"]
        g = meta["gender"]
        if gender and g != gender:
            continue
        if word.endswith(ending):
            candidates.append(paradigm)

    if not candidates and not gender:
        for paradigm, meta in sorted(PARADIGMS.items(), key=lambda x: -len(x[1]["ending"])):
            if word.endswith(meta["ending"]):
                candidates.append(paradigm)

    if not candidates:
        candidates = ["generic"]

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
    if paradigm is None:
        candidates = detect_paradigm(word, gender)
        noun_cands = [c for c in candidates if not c.startswith("pronoun") and not c.startswith("numeral") and c != "generic"]
        if noun_cands:
            paradigm = noun_cands[0]
        else:
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
        "forms": table,
        "type": "noun",
    }

def decline_pronoun(word: str, gender: str | None = None) -> dict[str, Any]:
    """Decline pronoun."""
    key = word.strip()
    alias_map = {
        "saH": "tad", "sA": "tad", "tat": "tad",
        "ezaH": "etad", "ezA": "etad", "etat": "etad",
        "yaH": "yad", "yA": "yad", "yat": "yad",
        "syaH": "tyad", "syA": "tyad", "tyat": "tyad",
        "kaH": "kim", "kA": "kim", "kim": "kim",
        "ayam": "idam", "iyam": "idam", "idam": "idam",
        "asO": "adas", "adaH": "adas",
        "aham": "asmad", "asmat": "asmad", "asmad": "asmad",
        "tvam": "yuzmad", "yuzmad": "yuzmad", "yusmad": "yuzmad",
    }
    if key in alias_map:
        key = alias_map[key]
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
            table = entry[""]
            return {"word": word, "lemma": key, "gender": gender, "forms": table, "type": "pronoun", "desc": f"pronoun {key}"}
    else:
        if "" in entry and len(entry) == 1:
            return {"word": word, "lemma": key, "gender": "", "forms": entry[""], "type": "pronoun", "desc": f"pronoun {key}"}
        return {"word": word, "lemma": key, "genders": {g: tbl for g, tbl in entry.items()}, "type": "pronoun", "desc": f"pronoun {key} (all genders)"}

def decline_numeral(word: str, gender: str | None = None) -> dict[str, Any]:
    """Decline numeral."""
    key = word.strip()
    if key not in NUMERALS and key.lower() in NUMERALS:
        key = key.lower()
    if key not in NUMERALS:
        raise ValueError(f"Unknown numeral '{word}'. Known: {', '.join(sorted(NUMERALS)[:20])} ...")
    entry = NUMERALS[key]
    if gender:
        if gender not in entry:
            raise ValueError(f"Numeral '{key}' has no gender '{gender}'. Available: {', '.join(entry)}")
        return {"word": word, "lemma": key, "gender": gender, "forms": entry[gender], "type": "numeral", "desc": f"numeral {key} ({gender})"}
    else:
        return {"word": word, "lemma": key, "genders": entry, "type": "numeral", "desc": f"numeral {key} (all genders)"}

def decline(word: str, gender: str | None = None, paradigm: str | None = None, category: str | None = None) -> dict[str, Any]:
    """Unified entry point."""
    word = word.strip()
    if not word:
        raise ValueError("word required")
    if category == "pronoun":
        return decline_pronoun(word, gender)
    if category == "numeral":
        return decline_numeral(word, gender)
    if category == "noun":
        return decline_noun(word, gender, paradigm)

    # auto detect
    low_lower = word.lower()
    if word in PRONOUNS or low_lower in PRONOUNS:
        try:
            return decline_pronoun(word, gender)
        except Exception:
            pass
    alias_map = {"saH": "tad", "sA": "tad", "ezaH": "etad", "yaH": "yad", "kaH": "kim", "ayam": "idam", "asO": "adas", "aham": "asmad", "tvam": "yuzmad"}
    if word in alias_map:
        return decline_pronoun(alias_map[word], gender)
    if word in NUMERALS or low_lower in NUMERALS:
        return decline_numeral(word, gender)
    if low_lower in ("eka", "dvi", "tri", "catur", "paYcan", "paYca", "zaz", "zaR", "zaw", "saptan", "azwan", "azwO", "navan", "daSan"):
        return decline_numeral(low_lower, gender)

    return decline_noun(word, gender, paradigm)

def get_declension(word: str, gender: str | None = None, paradigm: str | None = None, category: str | None = None) -> dict[str, Any]:
    return decline(word, gender=gender, paradigm=paradigm, category=category)

def list_paradigms() -> list[dict[str, str]]:
    return [{"paradigm": k, "ending": v["ending"], "gender": v["gender"], "desc": v["desc"]} for k, v in sorted(PARADIGMS.items())]

def list_pronouns() -> list[str]:
    return sorted(PRONOUNS.keys())

def list_numerals() -> list[str]:
    return sorted(NUMERALS.keys())

def flatten_forms(result: dict[str, Any]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    forms = result.get("forms")
    if forms is not None:
        for vib in VIBHAKTIS:
            if vib not in forms:
                continue
            for idx, vac in enumerate(VACANAS):
                rows.append({"vibhakti": vib, "vacana": vac, "form": forms[vib][idx]})
        return rows
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
    lines = []
    lines.append(f"# {result.get('word')}  [{result.get('type')}]  {result.get('desc','')}  gender={result.get('gender','') or ','.join(result.get('genders',{}))}  paradigm={result.get('paradigm','')}")
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

def decline_to_dict(word: str, gender: str | None = None, paradigm: str | None = None, category: str | None = None) -> dict[str, Any]:
    res = decline(word, gender=gender, paradigm=paradigm, category=category)
    res["_flat"] = flatten_forms(res)
    return res

# ---------------------------------------------------------------------------
# Reverse analysis: given inflected form, find possible lemma + vibhakti/vacana
# ---------------------------------------------------------------------------

def _norm_loose(s: str) -> str:
    return s.replace("R", "n").replace("N", "n").replace("S", "s").replace("z", "s")

# Paradigms where entire word is stored as suffix (empty base permitted during analysis)
_ALLOW_EMPTY_BASE_PARADIGMS = {
    "pati_m", "sakhi_m", "pathin_m", "rajan_m", "o_m", "o_f", "go_m", "go_f", "asthi_n", "ahan_n",
    "pums_m", "svan_m", "yuvan_m", "mahat_m", "mahat_n", "vidvas_m", "bhavat_m",
    "sri_f", "bhu_f", "stri_f", "lakzmi_f", "nau_f", "glau_m", "rai_m", "rai_f",
    "ap_f", "dis_f", "dis_m",
}

def analyze_form(word: str, limit: int = 20, loose: bool = True) -> list[dict[str, Any]]:
    """Analyze inflected nominal form -> list of possible analyses."""
    word = word.strip()
    if not word:
        return []
    hits: list[dict[str, Any]] = []
    word_norm = _norm_loose(word) if loose else word

    # --- pronouns: exact form match (handles slash variants) ---
    for lemma, genders in PRONOUNS.items():
        for g, tbl in genders.items():
            for vib, forms in tbl.items():
                for idx, f in enumerate(forms):
                    if f == "-" or f == "":
                        continue
                    variants = [p.strip() for p in f.split("/")] if "/" in f else [f]
                    for part in variants:
                        part_norm = _norm_loose(part) if loose else part
                        if word == part or word_norm == part_norm:
                            hits.append({
                                "type": "pronoun",
                                "match_type": "pronoun",
                                "lemma": lemma,
                                "word": word,
                                "matched_form": part,
                                "gender": g or "m",
                                "vibhakti": vib,
                                "vacana": VACANAS[idx],
                                "paradigm": f"pronoun:{lemma}",
                                "paradigm_desc": f"pronoun {lemma}",
                                "suffix": part,
                            })
                            if len(hits) >= limit:
                                return hits[:limit]

    # --- numerals: exact form match ---
    for lemma, genders in NUMERALS.items():
        for g, tbl in genders.items():
            for vib, forms in tbl.items():
                for idx, f in enumerate(forms):
                    if f == "-" or f == "":
                        continue
                    variants = [p.strip() for p in f.split("/")] if "/" in f else [f]
                    for part in variants:
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

    # --- nouns: suffix stripping -> lemma reconstruction ---
    candidates: list[tuple[int, dict[str, Any]]] = []
    for paradigm, meta in PARADIGMS.items():
        ending = meta["ending"]
        gender = meta["gender"]
        table = meta["table"]
        desc = meta["desc"]
        for vib, suffixes in table.items():
            for idx, suf_raw in enumerate(suffixes):
                if suf_raw == "-" or suf_raw == "":
                    continue
                variants = [p.strip() for p in suf_raw.split("/")] if "/" in suf_raw else [suf_raw]
                for suf in variants:
                    suf_norm = _norm_loose(suf) if loose else suf
                    if word_norm.endswith(suf_norm):
                        if len(word) < len(suf):
                            continue
                        base = word[: len(word) - len(suf)] if len(suf) else word
                        lemma = base + ending
                        if not lemma or (len(base) == 0 and paradigm not in _ALLOW_EMPTY_BASE_PARADIGMS):
                            continue
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
                lemma = base
                if not lemma:
                    continue
                score = len(suf) * 5
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

    candidates.sort(key=lambda x: (-x[0], x[1]["paradigm"], x[1]["vibhakti"]))
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
    """Unified analyzer: verb conjugations + nominal declensions."""
    hits: list[dict[str, Any]] = []
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
    try:
        remaining = limit - len(hits)
        if remaining > 0:
            nom = analyze_form(word, limit=remaining, loose=loose)
            hits.extend(nom)
    except Exception:
        pass
    return hits[:limit]
