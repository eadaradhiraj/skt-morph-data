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
  a_m, a_n, A_f, A_m (viSvapA root A-stem), i_m, pati_m, sakhi_m, i_f, i_n, asthi_n (daDi/akzi/asTi/sakTi),
  I_f (nadI), sri_f (SrI/hrI/DI), sudhi_m (suDI iyaN), I_m (senAnI yaR), lakzmi_f, stri_f,
  u_m (guru), krozwu_m (krozwu/krozwf), u_f (Denu), u_n (maDu), U_f (vaDU), bhu_f (BU/BrU),
  f_m (pitf kinship), tf_m (kartf agent noun), f_f (mAtf), svasf_f (svasf), f_n (dAtf),
  r_f (dvAr), gir_f (gir), pur_f (pur), div_f/div_m (div/dyu heaven),
  an_m (Atman), rajan_m (rAjan), an_n (nAman), karman_n (karman), in_m (yogin), in_n (balin),
  at_m (participle Bavat), bhavat_m (honorific Bavat), at_n (jagat), mahat_m, mahat_n,
  pathin_m (panTA), vat_m (Danavat), mat_m (budDimat), vidvas_m (vidvAn),
  yas_m (Sreyas m.), yas_n (Sreyas n.), as_n (manas), as_m/as_f (sumanas), candramas_m (candramas),
  us_n (danus), is_n (havis), c_f (vAc), pranc_m (prAYc), pratyanc_m (pratyaYc), udanc_m (udaYc),
  t_m (marut), t_f (sarit), t_n (jagat), d_f (sampad), kzuD_f (kzuD), dh_f (samiD),
  j_m (Bizaj), yuj_m (yuj), Buj_m/Buj_f (Buj), dis_f/dis_m (diS/viS),
  o_m/o_f (go), ahan_n (ahan), pums_m (pums), svan_m (Svan), yuvan_m (yuvan),
  vftrahan_m (vftrahan), han_m (han-compounds), maghavan_m (maGavan),
  anaquh_m (anaquh ox), ap_f (ap water), nau_f (nO), glau_m (glO), rai_m/rai_f (rE), etc.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional

from .subanta_data import CELL_ALTS

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

VIBHAKTI_INDEX: dict[str, int] = {v: i + 1 for i, v in enumerate(VIBHAKTIS)}
VACANA_INDEX: dict[str, int] = {v: i + 1 for i, v in enumerate(VACANAS)}
VIBHAKTI_ORDERED = list(VIBHAKTIS)

# ---------------------------------------------------------------------------
# Parity architecture with dhaturupa-wasm (Rust) — see docs/SUBANTA_KRDANTA_PARITY_PLAN.md
# New class-based paradigm types mirroring `engine/subanta.rs` (~9.2k lines).
# ---------------------------------------------------------------------------
class Linga(str, Enum):
    """Linga (gender/literality class) of a nominal paradigm: m | f | n."""

    M = "m"  # Pullinga
    F = "f"  # Strilinga
    N = "n"  # Napumsakalinga

    @classmethod
    def parse(cls, s: Optional[str]) -> Optional["Linga"]:
        if s is None:
            return None
        t = str(s).strip().lower()
        if not t:
            return None
        for lg in cls:
            if lg.value == t:
                return lg
        return None

    def __str__(self) -> str:
        return self.value

    @property
    def label(self) -> str:
        return self.value


@dataclass(slots=True)
class SubantaSlot:
    """One vibhakti × vacana cell of a paradigm (8 × 3 = 24 slots)."""

    vibhakti: int  # 1 to 8 (8 = saMboDana / sambodhana)
    vacana: int  # 1: eka, 2: dvi, 3: bahu
    forms: list[str]  # e.g. ["BavanAd", "BavanAt"]


@dataclass(slots=True)
class SubantaParadigm:
    """A single declined paradigm: stem + linga + class + 24 cells."""

    stem: str
    linga: Linga
    class_id: str
    cells: list[SubantaSlot]  # Exactly 24 slots (8 x 3)


def _gender_of_liga(lg: Linga) -> str:
    if lg is None:
        return "m"
    return {"m": "m", "f": "f", "n": "n"}.get(str(lg), "m")


def _slot(vibhakti: str, vacana: str, forms: list[str]) -> SubantaSlot:
    return SubantaSlot(
        vibhakti=int(VIBHAKTI_INDEX[vibhakti]),
        vacana=int(VACANA_INDEX[vacana]),
        forms=[f.strip() for f in forms] if forms else ["-"],
    )


def site_grid_cells(spec: str) -> list[SubantaSlot]:
    """Expand one SITE_GRIDS spec (row-major `|`-joined cells, `/`-joined alternants)."""
    vibs = list(VIBHAKTIS)
    vacs = list(VACANAS)
    cells = spec.split("|")
    out: list[SubantaSlot] = []
    for i, cell in enumerate(cells):
        vib_i = i // 3
        vac_i = i % 3
        if vib_i >= len(vibs) or vac_i >= len(vacs):
            break
        vib = vibs[vib_i]
        vac = vacs[vac_i]
        if cell.strip() == "":
            forms: list[str] = []
        else:
            forms = [f.strip() for f in cell.split("/") if f.strip()]
        out.append(SubantaSlot(vibhakti=int(VIBHAKTI_INDEX[vib]), vacana=int(VACANA_INDEX[vac]), forms=forms))
    return out


# Site-verbatim paradigm grids (irregular words the site grids in full).
# Tuple: (stem, linga, cells-spec) — cells are row-major over 8 vibhaktis x 3 vacanas.
SITE_GRIDS: list[tuple[str, str, str]] = [
    ("x", "m", "A|alO|alaH|alam|alO|Fn|lA|xByAm|xBiH|le|xByAm|xByaH|ul|xByAm|xByaH|ul|loH|FRAm|ali|loH|xzu|al|alO|alaH"),
    ("kF", "m", "kFH/kIH|krO/kirO|kraH/kiraH|kFm/kiram|krO/kirO|kFn/kiraH|krA/kirA|kFByAm/kIrByAm|kFBiH/kIrBiH|kre/kire|kFByAm/kIrByAm|kFByaH/kIrByaH|kraH/kiraH|kFByAm/kIrByAm|kFByaH/kIrByaH|kraH/kiraH|kroH/kiroH|krAm/kirAm|kri/kiri|kroH/kiroH|kFzu/kIrzu|kFH/kIH|krO/kirO|kraH/kiraH"),
    ("gamx", "m", "gamA|gamalO|gamalaH|gamalam|gamalO|gamFn|gamlA|gamxByAm|gamxBiH|gamle|gamxByAm|gamxByaH|gamul|gamxByAm|gamxByaH|gamul|gamloH|gamFRAm|gamali|gamloH|gamxzu|gamal|gamalO|gamalaH"),
    ("gamx", "n", "gamx|gamxnI|gamFRi|gamx|gamxnI|gamFRi|gamxnA/gamlA|gamxByAm|gamxBiH|gamxne/gamle|gamxByAm|gamxByaH|gamxnaH/gamul|gamxByAm|gamxByaH|gamxnaH/gamul|gamxnoH/gamloH|gamFRAm|gamxni/gamali|gamxnoH/gamloH|gamxzu|gamx/gamal|gamxnI|gamFRi"),
    ("tF", "m", "tFH/tIH|trO/tirO|traH/tiraH|tFm/tiram|trO/tirO|tFn/tiraH|trA/tirA|tFByAm/tIrByAm|tFBiH/tIrBiH|tre/tire|tFByAm/tIrByAm|tFByaH/tIrByaH|traH/tiraH|tFByAm/tIrByAm|tFByaH/tIrByaH|traH/tiraH|troH/tiroH|trAm/tirAm|tri/tiri|troH/tiroH|tFzu/tIrzu|tFH/tIH|trO/tirO|traH/tiraH"),
    ("Sakx", "m", "SakA|SakalO|SakalaH|Sakalam|SakalO|SakFn|SaklA|SakxByAm|SakxBiH|Sakle|SakxByAm|SakxByaH|Sakul|SakxByAm|SakxByaH|Sakul|SakloH|SakFRAm|Sakali|SakloH|Sakxzu|Sakal|SakalO|SakalaH"),
    ("div", "f", "dyOH|divO|divaH|divam|divO|divaH|divA|dyuByAm|dyuBiH|dive|dyuByAm|dyuByaH|divaH|dyuByAm|dyuByaH|divaH|divoH|divAm|divi|divoH|dyuzu|dyOH|divO|divaH"),
    ("dyo", "f", "dyOH|dyAvO|dyAvaH|dyAm|dyAvO|dyAH|dyavA|dyoByAm|dyoBiH|dyave|dyoByAm|dyoByaH|dyoH|dyoByAm|dyoByaH|dyoH|dyavoH|dyavAm|dyavi|dyavoH|dyozu|dyOH|dyAvO|dyAvaH"),
    ("pradyo", "n", "pradyu|pradyunI|pradyUni|pradyu|pradyunI|pradyUni|pradyunA|pradyuByAm|pradyuBiH|pradyune|pradyuByAm|pradyuByaH|pradyunaH|pradyuByAm|pradyuByaH|pradyunaH|pradyunoH|pradyUnAm|pradyuni|pradyunoH|pradyuzu|pradyu/pradyo|pradyunI|pradyUni"),
    ("sudyo", "m", "sudyOH|sudyAvO|sudyAvaH|sudyAm|sudyAvO|sudyAH|sudyavA|sudyoByAm|sudyoBiH|sudyave|sudyoByAm|sudyoByaH|sudyoH|sudyoByAm|sudyoByaH|sudyoH|sudyavoH|sudyavAm|sudyavi|sudyavoH|sudyozu|sudyOH|sudyAvO|sudyAvaH"),
    ("sudiv", "m", "sudyOH|sudivO|sudivaH|sudivam|sudivO|sudivaH|sudivA|sudyuByAm|sudyuBiH|sudive|sudyuByAm|sudyuByaH|sudivaH|sudyuByAm|sudyuByaH|sudivaH|sudivoH|sudivAm|sudivi|sudivoH|sudyuzu|sudyOH|sudivO|sudivaH"),
    ("vimaladiv", "n", "vimaladyu|vimaladivI|vimaladivi|vimaladyu|vimaladivI|vimaladivi|vimaladivA|vimaladyuByAm|vimaladyuBiH|vimaladive|vimaladyuByAm|vimaladyuByaH|vimaladivaH|vimaladyuByAm|vimaladyuByaH|vimaladivaH|vimaladivoH|vimaladivAm|vimaladivi|vimaladivoH|vimaladyuzu|vimaladyu|vimaladivI|vimaladivi"),
    ("praDI", "m", "praDIH|praDyO|praDyaH|praDyam|praDyO|praDyaH|praDyA|praDIByAm|praDIBiH|praDyE|praDIByAm|praDIByaH|praDyAH|praDIByAm|praDIByaH|praDyAH|praDyoH|praDInAm|praDyAm|praDyoH|praDIzu|praDi|praDyO|praDyaH"),
    ("praDI", "m", "praDIH|praDyO|praDyaH|praDyam|praDyO|praDyaH|praDyA|praDIByAm|praDIBiH|praDye|praDIByAm|praDIByaH|praDyaH|praDIByAm|praDIByaH|praDyaH|praDyoH|praDyAm|praDyi|praDyoH|praDIzu|praDIH|praDyO|praDyaH"),
    ("praDI", "f", "praDIH|praDyO|praDyaH|praDyam|praDyO|praDyaH|praDyA|praDIByAm|praDIBiH|praDye/praDyE|praDIByAm|praDIByaH|praDyaH/praDyAH|praDIByAm|praDIByaH|praDyaH/praDyAH|praDyoH|praDyAm/praDInAm|praDyi/praDyAm|praDyoH|praDIzu|praDIH/praDi|praDyO|praDyaH"),
    ("praDI", "f", "praDIH|praDyO|praDyaH|praDyam|praDyO|praDyaH|praDyA|praDIByAm|praDIBiH|praDyE|praDIByAm|praDIByaH|praDyAH|praDIByAm|praDIByaH|praDyAH|praDyoH|praDInAm|praDyAm|praDyoH|praDIzu|praDi|praDyO|praDyaH"),
    ("praDI", "n", "praDi|praDinI|praDIni|praDi|praDinI|praDIni|praDinA/praDyA|praDiByAm|praDiBiH|praDine/praDye|praDiByAm|praDiByaH|praDinaH/praDyaH|praDiByAm|praDiByaH|praDinaH/praDyaH|praDinoH/praDyoH|praDInAm/praDyAm|praDini/praDyi|praDinoH/praDyoH|praDizu|praDi/praDe|praDinI|praDIni"),
    ("suDI", "m", "suDIH|suDiyO|suDiyaH|suDiyam|suDiyO|suDiyaH|suDiyA|suDIByAm|suDIBiH|suDiye|suDIByAm|suDIByaH|suDiyaH|suDIByAm|suDIByaH|suDiyaH|suDiyoH|suDiyAm|suDiyi|suDiyoH|suDIzu|suDIH|suDiyO|suDiyaH"),
    ("suDI", "f", "suDIH|suDiyO|suDiyaH|suDiyam|suDiyO|suDiyaH|suDiyA|suDIByAm|suDIBiH|suDiye/suDiyE|suDIByAm|suDIByaH|suDiyaH/suDiyAH|suDIByAm|suDIByaH|suDiyaH/suDiyAH|suDiyoH|suDiyAm/suDInAm|suDiyi/suDiyAm|suDiyoH|suDIzu|suDIH|suDiyO|suDiyaH"),
    ("suDI", "n", "suDi|suDinI|suDIni|suDi|suDinI|suDIni|suDinA/suDiyA|suDiByAm|suDiBiH|suDine/suDiye|suDiByAm|suDiByaH|suDinaH/suDiyaH|suDiByAm|suDiByaH|suDinaH/suDiyaH|suDinoH/suDiyoH|suDInAm/suDiyAm|suDini/suDiyi|suDinoH/suDiyoH|suDizu|suDi/suDe|suDinI|suDIni"),
    ("prarE", "n", "prari|prariRI|prarIRi|prari|prariRI|prarIRi|prariRA|prarAByAm|prarABiH|prariRe|prarAByAm|prarAByaH|prariRaH|prarAByAm|prarAByaH|prariRaH|prariRoH|prarIRAm|prariRi|prariRoH|prarAsu|prari/prare|prariRI|prarIRi"),
    ("sunO", "n", "sunu|sununI|sunUni|sunu|sununI|sunUni|sununA|sunuByAm|sunuBiH|sunune|sunuByAm|sunuByaH|sununaH|sunuByAm|sunuByaH|sununaH|sununoH|sunUnAm|sununi|sununoH|sunuzu|sunu/suno|sununI|sunUni"),
    ("sulU", "m", "sulUH|sulvO|sulvaH|sulvam|sulvO|sulvaH|sulvA|sulUByAm|sulUBiH|sulve|sulUByAm|sulUByaH|sulvaH|sulUByAm|sulUByaH|sulvaH|sulvoH|sulvAm|sulvi|sulvoH|sulUzu|sulUH|sulvO|sulvaH"),
    ("sulU", "n", "sulu|sulunI|sulUni|sulu|sulunI|sulUni|sulunA/sulvA|suluByAm|suluBiH|sulune/sulve|suluByAm|suluByaH|sulunaH/sulvaH|suluByAm|suluByaH|sulunaH/sulvaH|sulunoH/sulvoH|sulUnAm/sulvAm|suluni/sulvi|sulunoH/sulvoH|suluzu|sulu/sulo|sulunI|sulUni"),
    ("se", "m", "seH|sayO|sayaH|sayam|sayO|sayaH|sayA|seByAm|seBiH|saye|seByAm|seByaH|seH|seByAm|seByaH|seH|sayoH|sayAm|sayi|sayoH|sezu|se|sayO|sayaH"),
    ("smfte", "m", "smfteH|smftayO|smftayaH|smftayam|smftayO|smftayaH|smftayA|smfteByAm|smfteBiH|smftaye|smfteByAm|smfteByaH|smfteH|smfteByAm|smfteByaH|smfteH|smftayoH|smftayAm|smftayi|smftayoH|smftezu|smfte|smftayO|smftayaH"),
    ("smfto", "m", "smftOH|smftAvO|smftAvaH|smftAm|smftAvO|smftAH|smftavA|smftoByAm|smftoBiH|smftave|smftoByAm|smftoByaH|smftoH|smftoByAm|smftoByaH|smftoH|smftavoH|smftavAm|smftavi|smftavoH|smftozu|smftOH|smftAvO|smftAvaH"),
    ("susmfte", "n", "susmfti|susmftinI|susmftIni|susmfti|susmftinI|susmftIni|susmftinA|susmftiByAm|susmftiBiH|susmftine|susmftiByAm|susmftiByaH|susmftinaH|susmftiByAm|susmftiByaH|susmftinaH|susmftinoH|susmftInAm|susmftini|susmftinoH|susmftizu|susmfti/susmfte|susmftinI|susmftIni"),
    ("praSAm", "m", "praSAn|praSAmO|praSAmaH|praSAmam|praSAmO|praSAmaH|praSAmA|praSAnByAm|praSAnBiH|praSAme|praSAnByAm|praSAnByaH|praSAmaH|praSAnByAm|praSAnByaH|praSAmaH|praSAmoH|praSAmAm|praSAmi|praSAmoH|praSAnsu/praSAntsu|praSAn|praSAmO|praSAmaH"),
    ("svap", "n", "svab/svap|svapI|svampi/svAmpi|svab/svap|svapI|svampi/svAmpi|svapA|svadByAm|svadBiH|svape|svadByAm|svadByaH|svapaH|svadByAm|svadByaH|svapaH|svapoH|svapAm|svapi|svapoH|svapsu|svab/svap|svapI|svampi/svAmpi"),
    ("paramacatur", "m", "||paramacatvAraH|||paramacaturaH|||paramacaturBiH|||paramacaturByaH|||paramacaturByaH|||paramacaturRAm|||paramacaturzu|||paramacatvAraH"),
    ("priyacatur", "m", "priyacatvAH|priyacatvArO|priyacatvAraH|priyacatvAram|priyacatvArO|priyacaturaH|priyacaturA|priyacaturByAm|priyacaturBiH|priyacature|priyacaturByAm|priyacaturByaH|priyacaturaH|priyacaturByAm|priyacaturByaH|priyacaturaH|priyacaturoH|priyacaturAm|priyacaturi|priyacaturoH|priyacaturzu|priyacatvaH|priyacatvArO|priyacatvAraH"),
    ("idakam", "m", "ayakam|imakO|imake|imakam/enam|imakO/enO|imakAn/enAn|imakena/enena|imakAByAm/AByAm|imakEH/eBiH|imakasmE/asmE|imakAByAm/AByAm|imakeByaH/eByaH|imakasmAd/asmAd/asmAt/imakasmAt|imakAByAm/AByAm|imakeByaH/eByaH|imakasya/asya|imakayoH/enayoH|imakezAm/ezAm|imakasmin/asmin|imakayoH/enayoH|imakezu/ezu|||"),
    ("aticamU", "m", "aticamUH|aticamvO|aticamvaH|aticamUm|aticamvO|aticamUn|aticamvA|aticamUByAm|aticamUBiH|aticamvE|aticamUByAm|aticamUByaH|aticamvAH|aticamUByAm|aticamUByaH|aticamvAH|aticamvoH|aticamUnAm|aticamvAm|aticamvoH|aticamUzu|aticamu|aticamvO|aticamvaH"),
    ("atilakzmI", "m", "atilakzmIH|atilakzmyO|atilakzmyaH|atilakzmIm|atilakzmyO|atilakzmIn|atilakzmyA|atilakzmIByAm|atilakzmIBiH|atilakzmyE|atilakzmIByAm|atilakzmIByaH|atilakzmyAH|atilakzmIByAm|atilakzmIByaH|atilakzmyAH|atilakzmyoH|atilakzmIRAm|atilakzmyAm|atilakzmyoH|atilakzmIzu|atilakzmi|atilakzmyO|atilakzmyaH"),
    ("atisaKi", "m", "atisaKA|atisaKAyO|atisaKAyaH|atisaKAyam|atisaKAyO|atisaKIn|atisaKinA|atisaKiByAm|atisaKiBiH|atisaKaye|atisaKiByAm|atisaKiByaH|atisaKeH|atisaKiByAm|atisaKiByaH|atisaKeH|atisaKyoH|atisaKInAm|atisaKO|atisaKyoH|atisaKizu|atisaKe|atisaKAyO|atisaKAyaH"),
    ("atistri", "m", "atistriH|atistriyO|atistriyaH|atistriyam/atistrim|atistriyO|atistriyaH/atistrIn|atistriRA|atistriByAm|atistriBiH|atistraye|atistriByAm|atistriByaH|atistreH|atistriByAm|atistriByaH|atistreH|atistriyoH|atistrIRAm|atistrO|atistriyoH|atistrizu|atistre|atistriyO|atistriyaH"),
    ("atistri", "f", "atistriH|atistriyO|atistriyaH|atistriyam/atistrim|atistriyO|atistriyaH/atistrIH|atistriyA|atistriByAm|atistriBiH|atistraye/atistriyE|atistriByAm|atistriByaH|atistreH/atistriyAH|atistriByAm|atistriByaH|atistreH/atistriyAH|atistriyoH|atistrIRAm|atistrO/atistriyAm|atistriyoH|atistrizu|atistre|atistriyO|atistriyaH"),
    ("ap", "f", "||ApaH|||apaH|||adBiH|||adByaH|||adByaH|||apAm|||apsu|||ApaH"),
    ("arvan", "m", "arvA|arvantO|arvantaH|arvantam|arvantO|arvataH|arvatA|arvadByAm|arvadBiH|arvate|arvadByAm|arvadByaH|arvataH|arvadByAm|arvadByaH|arvataH|arvatoH|arvatAm|arvati|arvatoH|arvatsu|arvan|arvantO|arvantaH"),
    ("ahan", "n", "ahaH|ahnI/ahanI|ahAni|ahaH|ahnI/ahanI|ahAni|ahnA|ahoByAm|ahoBiH|ahne|ahoByAm|ahoByaH|ahnaH|ahoByAm|ahoByaH|ahnaH|ahnoH|ahnAm|ahni/ahani|ahnoH|ahaHsu/ahassu|ahaH|ahnI/ahanI|ahAni"),
    ("ANgirasa", "m", "ANgirasaH|ANgirasO|aNgirasaH|ANgirasam|ANgirasO|aNgirasaH|ANgirasena|ANgirasAByAm|aNgiroBiH|ANgirasAya|ANgirasAByAm|aNgiroByaH|ANgirasAd/ANgirasAt|ANgirasAByAm|aNgiroByaH|ANgirasasya|ANgirasayoH|aNgirasAm|ANgirase|ANgirasayoH|aNgiraHsu/aNgirassu|ANgirasa|ANgirasO|aNgirasaH"),
    ("Urj", "n", "Urg/Urk|UrjI|Unrji|Urg/Urk|UrjI|Unrji|UrjA|UrgByAm|UrgBiH|Urje|UrgByAm|UrgByaH|UrjaH|UrgByAm|UrgByaH|UrjaH|UrjoH|UrjAm|Urji|UrjoH|Urkzu|Urg/Urk|UrjI|Unrji"),
    ("f", "m", "A|arO|araH|aram|arO|Fn|rA|fByAm|fBiH|re|fByAm|fByaH|uH|fByAm|fByaH|uH|roH|FRAm|ari|roH|fzu|aH|arO|araH"),
    ("kati", "m", "||kati|||kati|||katiBiH|||katiByaH|||katiByaH|||katInAm|||katizu|||kati"),
    ("kati", "f", "||kati|||kati|||katiBiH|||katiByaH|||katiByaH|||katInAm|||katizu|||kati"),
    ("kati", "n", "||kati|||kati|||katiBiH|||katiByaH|||katiByaH|||katInAm|||katizu|||kati"),
    ("krunc", "m", "kruN|kruYcO|kruYcaH|kruYcam|kruYcO|kruYcaH|kruYcA|kruNByAm|kruNBiH|kruYce|kruNByAm|kruNByaH|kruYcaH|kruNByAm|kruNByaH|kruYcaH|kruYcoH|kruYcAm|kruYci|kruYcoH|kruNzu/kruNkzu/kruNKzu|kruN|kruYcO|kruYcaH"),
    ("krozwu", "m", "krozwA|krozwArO|krozwAraH|krozwAram|krozwArO|krozwUn|krozwrA/krozwunA|krozwuByAm|krozwuBiH|krozwre/krozwave|krozwuByAm|krozwuByaH|krozwuH/krozwoH|krozwuByAm|krozwuByaH|krozwuH/krozwoH|krozwroH/krozwvoH|krozwUnAm|krozwari/krozwO|krozwroH/krozwvoH|krozwuzu|krozwo|krozwArO|krozwAraH"),
    ("krozwu", "f", "krozwrI|krozwryO|krozwryaH|krozwrIm|krozwryO|krozwrIH|krozwryA|krozwrIByAm|krozwrIBiH|krozwryE|krozwrIByAm|krozwrIByaH|krozwryAH|krozwrIByAm|krozwrIByaH|krozwryAH|krozwryoH|krozwrIRAm|krozwryAm|krozwryoH|krozwrIzu|krozwri|krozwryO|krozwryaH"),
    ("gopA", "f", "gopAH|gopO|gopAH|gopAm|gopO|gopaH|gopA|gopAByAm|gopABiH|gope|gopAByAm|gopAByaH|gopaH|gopAByAm|gopAByaH|gopaH|gopoH|gopAm|gopi|gopoH|gopAsu|gopAH|gopO|gopAH"),
    ("goviz", "n", "goviq/goviw|govizI|goviMzi|goviq/goviw|govizI|goviMzi|govizA|goviqByAm|goviqBiH|govize|goviqByAm|goviqByaH|govizaH|goviqByAm|goviqByaH|govizaH|govizoH|govizAm|govizi|govizoH|goviwsu/goviwtsu|goviq/goviw|govizI|goviMzi"),
    ("grAmaRI", "f", "grAmaRIH|grAmaRyO|grAmaRyaH|grAmaRyam|grAmaRyO|grAmaRyaH|grAmaRyA|grAmaRIByAm|grAmaRIBiH|grAmaRye|grAmaRIByAm|grAmaRIByaH|grAmaRyaH|grAmaRIByAm|grAmaRIByaH|grAmaRyaH|grAmaRyoH|grAmaRyAm|grAmaRyAm|grAmaRyoH|grAmaRIzu|grAmaRIH|grAmaRyO|grAmaRyaH"),
    ("tamisrahan", "m", "tamisrahA|tamisrahaRO|tamisrahaRaH|tamisrahaRam|tamisrahaRO|tamisraGnaH|tamisraGnA|tamisrahaByAm|tamisrahaBiH|tamisraGne|tamisrahaByAm|tamisrahaByaH|tamisraGnaH|tamisrahaByAm|tamisrahaByaH|tamisraGnaH|tamisraGnoH|tamisraGnAm|tamisraGni/tamisrahaRi|tamisraGnoH|tamisrahasu|tamisrahan|tamisrahaRO|tamisrahaRaH"),
    ("tyad", "m", "syaH|tyO|tye|tyam|tyO|tyAn|tyena|tyAByAm|tyEH|tyasmE|tyAByAm|tyeByaH|tyasmAd/tyasmAt|tyAByAm|tyeByaH|tyasya|tyayoH|tyezAm|tyasmin|tyayoH|tyezu|||"),
    ("tyad", "f", "syA|tye|tyAH|tyAm|tye|tyAH|tyayA|tyAByAm|tyABiH|tyasyE|tyAByAm|tyAByaH|tyasyAH|tyAByAm|tyAByaH|tyasyAH|tyayoH|tyAsAm|tyasyAm|tyayoH|tyAsu|||"),
    ("tyad", "n", "tyad/tyat|tye|tyAni|tyad/tyat|tye|tyAni|tyena|tyAByAm|tyEH|tyasmE|tyAByAm|tyeByaH|tyasmAd/tyasmAt|tyAByAm|tyeByaH|tyasya|tyayoH|tyezAm|tyasmin|tyayoH|tyezu|||"),
    ("dIrGAhan", "m", "dIrGAhAH|dIrGAhAnO|dIrGAhAnaH|dIrGAhAnam|dIrGAhAnO|dIrGAhnaH|dIrGAhnA|dIrGAhoByAm|dIrGAhoBiH|dIrGAhne|dIrGAhoByAm|dIrGAhoByaH|dIrGAhnaH|dIrGAhoByAm|dIrGAhoByaH|dIrGAhnaH|dIrGAhnoH|dIrGAhnAm|dIrGAhni/dIrGAhani|dIrGAhnoH|dIrGAhaHsu/dIrGAhassu|dIrGAhaH|dIrGAhAnO|dIrGAhAnaH"),
    ("nf", "m", "nA|narO|naraH|naram|narO|nFn|nrA|nfByAm|nfBiH|nre|nfByAm|nfByaH|nuH|nfByAm|nfByaH|nuH|nroH|nFRAm/nfRAm|nari|nroH|nfzu|naH|narO|naraH"),
    ("pati", "m", "patiH|patI|patayaH|patim|patI|patIn|patyA|patiByAm|patiBiH|patye|patiByAm|patiByaH|patyuH|patiByAm|patiByaH|patyuH|patyoH|patInAm|patyO|patyoH|patizu|pate|patI|patayaH"),
    ("paramatad", "m", "paramasaH|paramatO|paramate|paramatam|paramatO|paramatAn|paramatena|paramatAByAm|paramatEH|paramatasmE|paramatAByAm|paramateByaH|paramatasmAd/paramatasmAt|paramatAByAm|paramateByaH|paramatasya|paramatayoH|paramatezAm|paramatasmin|paramatayoH|paramatezu|||"),
    ("paramatri", "m", "||paramatrayaH|||paramatrIn|||paramatriBiH|||paramatriByaH|||paramatriByaH|||paramatrayARAm|||paramatrizu|||paramatrayaH"),
    ("paramatri", "f", "||paramatisraH|||paramatisraH|||paramatisfBiH|||paramatisfByaH|||paramatisfByaH|||paramatisfRAm|||paramatisfzu|||paramatisraH"),
    ("paramadvi", "m", "|paramadvO|||paramadvO|||paramadvAByAm|||paramadvAByAm|||paramadvAByAm|||paramadvayoH|||paramadvayoH||||"),
    ("paramapaYcan", "m", "||paramapaYca|||paramapaYca|||paramapaYcaBiH|||paramapaYcaByaH|||paramapaYcaByaH|||paramapaYcAnAm|||paramapaYcasu|||paramapaYca"),
    ("paramazaz", "m", "||paramazaq/paramazaw|||paramazaq/paramazaw|||paramazaqBiH|||paramazaqByaH|||paramazaqByaH|||paramazaRRAm|||paramazawsu/paramazawtsu|||paramazaq/paramazaw"),
    ("paramasaKi", "m", "paramasaKA|paramasaKAyO|paramasaKAyaH|paramasaKAyam|paramasaKAyO|paramasaKIn|paramasaKinA|paramasaKiByAm|paramasaKiBiH|paramasaKaye|paramasaKiByAm|paramasaKiByaH|paramasaKeH|paramasaKiByAm|paramasaKiByaH|paramasaKeH|paramasaKyoH|paramasaKInAm|paramasaKO|paramasaKyoH|paramasaKizu|paramasaKe|paramasaKAyO|paramasaKAyaH"),
    ("paramAzwan", "m", "||paramAzwa/paramAzwO|||paramAzwa/paramAzwO|||paramAzwaBiH/paramAzwABiH|||paramAzwaByaH/paramAzwAByaH|||paramAzwaByaH/paramAzwAByaH|||paramAzwAnAm|||paramAzwasu/paramAzwAsu|||paramAzwa/paramAzwO"),
    ("pipaWiz", "n", "pipaWIH|pipaWizI|pipaWizi|pipaWIH|pipaWizI|pipaWizi|pipaWizA|pipaWIrByAm|pipaWIrBiH|pipaWize|pipaWIrByAm|pipaWIrByaH|pipaWizaH|pipaWIrByAm|pipaWIrByaH|pipaWizaH|pipaWizoH|pipaWizAm|pipaWizi|pipaWizoH|pipaWIHzu/pipaWIzzu|pipaWIH|pipaWizI|pipaWizi"),
    ("punarBU", "f", "punarBUH|punarBvO|punarBvaH|punarBvam|punarBvO|punarBvaH|punarBvA|punarBUByAm|punarBUBiH|punarBvE|punarBUByAm|punarBUByaH|punarBvAH|punarBUByAm|punarBUByaH|punarBvAH|punarBvoH|punarBURAm|punarBvAm|punarBvoH|punarBUzu|punarBu|punarBvO|punarBvaH"),
    ("pums", "m", "pumAn|pumAMsO|pumAMsaH|pumAMsam|pumAMsO|puMsaH|puMsA|puMByAm/pumByAm|puMBiH/pumBiH|puMse|puMByAm/pumByAm|puMByaH/pumByaH|puMsaH|puMByAm/pumByAm|puMByaH/pumByaH|puMsaH|puMsoH|puMsAm|puMsi|puMsoH|puMsu|puman|pumAMsO|pumAMsaH"),
    ("pratidivan", "m", "pratidivA|pratidivAnO|pratidivAnaH|pratidivAnam|pratidivAnO|pratidIvnaH|pratidIvnA|pratidivaByAm|pratidivaBiH|pratidIvne|pratidivaByAm|pratidivaByaH|pratidIvnaH|pratidivaByAm|pratidivaByaH|pratidIvnaH|pratidIvnoH|pratidIvnAm|pratidIvni/pratidivani|pratidIvnoH|pratidivasu|pratidivan|pratidivAnO|pratidivAnaH"),
    ("pratyeka", "m", "pratyekam|pratyekam|pratyekam|pratyekam|pratyekam|pratyekam|pratyekena/pratyekam|pratyekAByAm/pratyekam|pratyekEH/pratyekam|pratyekam|pratyekam|pratyekam|pratyekasmAd/pratyekasmAt|pratyekAByAm|pratyekeByaH|pratyekam|pratyekam|pratyekam|pratyekasmin/pratyekam|pratyekayoH/pratyekam|pratyekezu/pratyekam|pratyekam|pratyekam|pratyekam"),
    ("prAnc", "m", "prAN|prAYcO|prAYcaH|prAYcam|prAYcO|prAYcaH|prAYcA|prANByAm|prANBiH|prAYce|prANByAm|prANByaH|prAYcaH|prANByAm|prANByaH|prAYcaH|prAYcoH|prAYcAm|prAYci|prAYcoH|prANzu/prANkzu/prANKzu|prAN|prAYcO|prAYcaH"),
    ("priyatri", "m", "priyatriH|priyatrI|priyatrayaH|priyatrim|priyatrI|priyatrIn|priyatriRA|priyatriByAm|priyatriBiH|priyatraye|priyatriByAm|priyatriByaH|priyatreH|priyatriByAm|priyatriByaH|priyatreH|priyatryoH|priyatrayARAm|priyatrO|priyatryoH|priyatrizu|priyatre|priyatrI|priyatrayaH"),
    ("priyatri", "m", "priyatisA|priyatisrO|priyatisraH|priyatisram|priyatisrO|priyatisraH|priyatisrA|priyatisfByAm|priyatisfBiH|priyatisre|priyatisfByAm|priyatisfByaH|priyatisraH|priyatisfByAm|priyatisfByaH|priyatisraH|priyatisroH|priyatisfRAm|priyatisri|priyatisroH|priyatisfzu|priyatisaH|priyatisrO|priyatisraH"),
    ("priyatri", "f", "priyatriH|priyatrI|priyatrayaH|priyatrim|priyatrI|priyatrIH|priyatryA|priyatriByAm|priyatriBiH|priyatraye/priyatryE|priyatriByAm|priyatriByaH|priyatreH/priyatryAH|priyatriByAm|priyatriByaH|priyatreH/priyatryAH|priyatryoH|priyatrayARAm|priyatrO/priyatryAm|priyatryoH|priyatrizu|priyatre|priyatrI|priyatrayaH"),
    ("priyatri", "f", "priyatisA|priyatisrO|priyatisraH|priyatisram|priyatisrO|priyatisraH|priyatisrA|priyatisfByAm|priyatisfBiH|priyatisre|priyatisfByAm|priyatisfByaH|priyatisraH|priyatisfByAm|priyatisfByaH|priyatisraH|priyatisroH|priyatisfRAm|priyatisri|priyatisroH|priyatisfzu|priyatisaH|priyatisrO|priyatisraH"),
    ("priyatri", "n", "priyatri/priyatisf|priyatisfRI|priyatisFRi|priyatri/priyatisf|priyatisfRI|priyatisFRi|priyatisfRA/priyatisrA|priyatisfByAm|priyatisfBiH|priyatisfRe/priyatisre|priyatisfByAm|priyatisfByaH|priyatisfRaH/priyatisraH|priyatisfByAm|priyatisfByaH|priyatisfRaH/priyatisraH|priyatisfRoH/priyatisroH|priyatisFRAm/priyatisfRAm|priyatisfRi/priyatisri|priyatisfRoH/priyatisroH|priyatisfzu|priyatri/priyatisf/priyatre|priyatisfRI|priyatisFRi"),
    ("bahupAd", "m", "bahupAd/bahupAt|bahupAdO|bahupAdaH|bahupAdam|bahupAdO|bahupadaH|bahupadA|bahupAdByAm|bahupAdBiH|bahupade|bahupAdByAm|bahupAdByaH|bahupadaH|bahupAdByAm|bahupAdByaH|bahupadaH|bahupadoH|bahupadAm|bahupadi|bahupadoH|bahupAtsu|bahupAd/bahupAt|bahupAdO|bahupAdaH"),
    ("bahuvftrahan", "n", "bahuvftraha|bahuvftraGnI/bahuvftrahaRI|bahuvftrahARi|bahuvftraha|bahuvftraGnI/bahuvftrahaRI|bahuvftrahARi|bahuvftraGnA|bahuvftrahaByAm|bahuvftrahaBiH|bahuvftraGne|bahuvftrahaByAm|bahuvftrahaByaH|bahuvftraGnaH|bahuvftrahaByAm|bahuvftrahaByaH|bahuvftraGnaH|bahuvftraGnoH|bahuvftraGnAm|bahuvftraGni/bahuvftrahaRi|bahuvftraGnoH|bahuvftrahasu|bahuvftrahan/bahuvftraha|bahuvftraGnI/bahuvftrahaRI|bahuvftrahARi"),
    ("bahuSreyasI", "m", "bahuSreyasI|bahuSreyasyO|bahuSreyasyaH|bahuSreyasIm|bahuSreyasyO|bahuSreyasIn|bahuSreyasyA|bahuSreyasIByAm|bahuSreyasIBiH|bahuSreyasyE|bahuSreyasIByAm|bahuSreyasIByaH|bahuSreyasyAH|bahuSreyasIByAm|bahuSreyasIByaH|bahuSreyasyAH|bahuSreyasyoH|bahuSreyasInAm|bahuSreyasyAm|bahuSreyasyoH|bahuSreyasIzu|bahuSreyasi|bahuSreyasyO|bahuSreyasyaH"),
    ("bahusaKi", "m", "bahusaKA|bahusaKAyO|bahusaKAyaH|bahusaKAyam|bahusaKAyO|bahusaKIn|bahusaKinA|bahusaKiByAm|bahusaKiBiH|bahusaKaye|bahusaKiByAm|bahusaKiByaH|bahusaKeH|bahusaKiByAm|bahusaKiByaH|bahusaKeH|bahusaKyoH|bahusaKInAm|bahusaKO|bahusaKyoH|bahusaKizu|bahusaKe|bahusaKAyO|bahusaKAyaH"),
    ("buD", "m", "Bud/But|buDO|buDaH|buDam|buDO|buDaH|buDA|BudByAm|BudBiH|buDe|BudByAm|BudByaH|buDaH|BudByAm|BudByaH|buDaH|buDoH|buDAm|buDi|buDoH|Butsu|Bud/But|buDO|buDaH"),
    ("Bavat", "m", "BavAn|BavantO|BavantaH|Bavantam|BavantO|BavataH|BavatA|BavadByAm|BavadBiH|Bavate|BavadByAm|BavadByaH|BavataH|BavadByAm|BavadByaH|BavataH|BavatoH|BavatAm|Bavati|BavatoH|Bavatsu|Bavan|BavantO|BavantaH"),
    ("Bfsj", "m", "Bfq/Bfw|BfjjO|BfjjaH|Bfjjam|BfjjO|BfjjaH|BfjjA|BfqByAm|BfqBiH|Bfjje|BfqByAm|BfqByaH|BfjjaH|BfqByAm|BfqByaH|BfjjaH|BfjjoH|BfjjAm|Bfjji|BfjjoH|Bfwsu/Bfwtsu|Bfq/Bfw|BfjjO|BfjjaH"),
    ("maGavan", "m", "maGavA/maGavAn|maGavAnO/maGavantO|maGavAnaH/maGavantaH|maGavAnam/maGavantam|maGavAnO/maGavantO|maGonaH/maGavataH|maGonA/maGavatA|maGavaByAm/maGavadByAm|maGavaBiH/maGavadBiH|maGone/maGavate|maGavaByAm/maGavadByAm|maGavaByaH/maGavadByaH|maGonaH/maGavataH|maGavaByAm/maGavadByAm|maGavaByaH/maGavadByaH|maGonaH/maGavataH|maGonoH/maGavatoH|maGonAm/maGavatAm|maGoni/maGavati|maGonoH/maGavatoH|maGavasu/maGavatsu|maGavan|maGavAnO/maGavantO|maGavAnaH/maGavantaH"),
    ("marmaspfS", "n", "marmaspfg/marmaspfk|marmaspfSI|marmaspfMSi|marmaspfg/marmaspfk|marmaspfSI|marmaspfMSi|marmaspfSA|marmaspfgByAm|marmaspfgBiH|marmaspfSe|marmaspfgByAm|marmaspfgByaH|marmaspfSaH|marmaspfgByAm|marmaspfgByaH|marmaspfSaH|marmaspfSoH|marmaspfSAm|marmaspfSi|marmaspfSoH|marmaspfkzu|marmaspfg/marmaspfk|marmaspfSI|marmaspfMSi"),
    ("mahat", "m", "mahAn|mahAntO|mahAntaH|mahAntam|mahAntO|mahataH|mahatA|mahadByAm|mahadBiH|mahate|mahadByAm|mahadByaH|mahataH|mahadByAm|mahadByaH|mahataH|mahatoH|mahatAm|mahati|mahatoH|mahatsu|mahan|mahAntO|mahAntaH"),
    ("mAtfzvasf", "f", "mAtfzvasA|mAtfzvasArO|mAtfzvasAraH|mAtfzvasAram|mAtfzvasArO|mAtfzvasFH|mAtfzvasrA|mAtfzvasfByAm|mAtfzvasfBiH|mAtfzvasre|mAtfzvasfByAm|mAtfzvasfByaH|mAtfzvasuH|mAtfzvasfByAm|mAtfzvasfByaH|mAtfzvasuH|mAtfzvasroH|mAtfzvasFRAm|mAtfzvasari|mAtfzvasroH|mAtfzvasfzu|mAtfzvasaH|mAtfzvasArO|mAtfzvasAraH"),
    ("yAt", "m", "yAn|yAntO|yAntaH|yAntam|yAntO|yAtaH|yAtA|yAdByAm|yAdBiH|yAte|yAdByAm|yAdByaH|yAtaH|yAdByAm|yAdByaH|yAtaH|yAtoH|yAtAm|yAti|yAtoH|yAtsu|yAn|yAntO|yAntaH"),
    ("yuj", "m", "yuN|yuYjO|yuYjaH|yuYjam|yuYjO|yujaH|yujA|yugByAm|yugBiH|yuje|yugByAm|yugByaH|yujaH|yugByAm|yugByaH|yujaH|yujoH|yujAm|yuji|yujoH|yukzu|yuN|yuYjO|yuYjaH"),
    ("yuvan", "m", "yuvA|yuvAnO|yuvAnaH|yuvAnam|yuvAnO|yUnaH|yUnA|yuvaByAm|yuvaBiH|yUne|yuvaByAm|yuvaByaH|yUnaH|yuvaByAm|yuvaByaH|yUnaH|yUnoH|yUnAm|yUni|yUnoH|yuvasu|yuvan|yuvAnO|yuvAnaH"),
    ("viSvapA", "n", "viSvapam|viSvape|viSvapAni|viSvapam|viSvape|viSvapAni|viSvapena|viSvapAByAm|viSvapEH|viSvapAya|viSvapAByAm|viSvapeByaH|viSvapAd/viSvapAt|viSvapAByAm|viSvapeByaH|viSvapasya|viSvapayoH|viSvapAnAm|viSvape|viSvapayoH|viSvapezu|viSvapa|viSvape|viSvapAni"),
    ("viSvarAj", "m", "viSvArAq/viSvArAw|viSvarAjO|viSvarAjaH|viSvarAjam|viSvarAjO|viSvarAjaH|viSvarAjA|viSvArAqByAm|viSvArAqBiH|viSvarAje|viSvArAqByAm|viSvArAqByaH|viSvarAjaH|viSvArAqByAm|viSvArAqByaH|viSvarAjaH|viSvarAjoH|viSvarAjAm|viSvarAji|viSvarAjoH|viSvArAwsu/viSvArAwtsu|viSvArAq/viSvArAw|viSvarAjO|viSvarAjaH"),
    ("vIrahan", "m", "vIrahA|vIrahaRO|vIrahaRaH|vIrahaRam|vIrahaRO|vIraGnaH|vIraGnA|vIrahaByAm|vIrahaBiH|vIraGne|vIrahaByAm|vIrahaByaH|vIraGnaH|vIrahaByAm|vIrahaByaH|vIraGnaH|vIraGnoH|vIraGnAm|vIraGni/vIrahaRi|vIraGnoH|vIrahasu|vIrahan|vIrahaRO|vIrahaRaH"),
    ("vftrahan", "m", "vftrahA|vftrahaRO|vftrahaRaH|vftrahaRam|vftrahaRO|vftraGnaH|vftraGnA|vftrahaByAm|vftrahaBiH|vftraGne|vftrahaByAm|vftrahaByaH|vftraGnaH|vftrahaByAm|vftrahaByaH|vftraGnaH|vftraGnoH|vftraGnAm|vftraGni/vftrahaRi|vftraGnoH|vftrahasu|vftrahan|vftrahaRO|vftrahaRaH"),
    ("vyAGrapAd", "m", "vyAGrapAd/vyAGrapAt|vyAGrapAdO|vyAGrapAdaH|vyAGrapAdam|vyAGrapAdO|vyAGrapadaH|vyAGrapadA|vyAGrapAdByAm|vyAGrapAdBiH|vyAGrapade|vyAGrapAdByAm|vyAGrapAdByaH|vyAGrapadaH|vyAGrapAdByAm|vyAGrapAdByaH|vyAGrapadaH|vyAGrapadoH|vyAGrapadAm|vyAGrapadi|vyAGrapadoH|vyAGrapAtsu|vyAGrapAd/vyAGrapAt|vyAGrapAdO|vyAGrapAdaH"),
    ("Samanasvasf", "f", "SamanasvasA|SamanasvasArO|SamanasvasAraH|SamanasvasAram|SamanasvasArO|SamanasvasFH|SamanasvasrA|SamanasvasfByAm|SamanasvasfBiH|Samanasvasre|SamanasvasfByAm|SamanasvasfByaH|SamanasvasuH|SamanasvasfByAm|SamanasvasfByaH|SamanasvasuH|SamanasvasroH|SamanasvasFRAm|Samanasvasari|SamanasvasroH|Samanasvasfzu|SamanasvasaH|SamanasvasArO|SamanasvasAraH"),
    ("Svan", "m", "SvA|SvAnO|SvAnaH|SvAnam|SvAnO|SunaH|SunA|SvaByAm|SvaBiH|Sune|SvaByAm|SvaByaH|SunaH|SvaByAm|SvaByaH|SunaH|SunoH|SunAm|Suni|SunoH|Svasu|Svan|SvAnO|SvAnaH"),
    ("saKi", "m", "saKA|saKAyO|saKAyaH|saKAyam|saKAyO|saKIn|saKyA|saKiByAm|saKiBiH|saKye|saKiByAm|saKiByaH|saKyuH|saKiByAm|saKiByaH|saKyuH|saKyoH|saKInAm|saKyO|saKyoH|saKizu|saKe|saKAyO|saKAyaH"),
    ("saKI", "m", "saKA|saKAyO|saKAyaH|saKAyam|saKAyO|saKyaH|saKyA|saKIByAm|saKIBiH|saKye|saKIByAm|saKIByaH|saKyuH|saKIByAm|saKIByaH|saKyuH|saKyoH|saKyAm|saKyi|saKyoH|saKIzu|saKIH|saKAyO|saKAyaH"),
    ("supaTin", "n", "supaTi|supaTI|supanTAni|supaTi|supaTI|supanTAni|supaTA|supaTiByAm|supaTiBiH|supaTe|supaTiByAm|supaTiByaH|supaTaH|supaTiByAm|supaTiByaH|supaTaH|supaToH|supaTAm|supaTi|supaToH|supaTizu|supaTin/supaTi|supaTI|supanTAni"),
    ("supAd", "m", "supAd/supAt|supAdO|supAdaH|supAdam|supAdO|supadaH|supadA|supAdByAm|supAdBiH|supade|supAdByAm|supAdByaH|supadaH|supAdByAm|supAdByaH|supadaH|supadoH|supadAm|supadi|supadoH|supAtsu|supAd/supAt|supAdO|supAdaH"),
    ("supums", "n", "supum|supuMsI|supumAMsi|supum|supuMsI|supumAMsi|supuMsA|supuMByAm/supumByAm|supuMBiH/supumBiH|supuMse|supuMByAm/supumByAm|supuMByaH/supumByaH|supuMsaH|supuMByAm/supumByAm|supuMByaH/supumByaH|supuMsaH|supuMsoH|supuMsAm|supuMsi|supuMsoH|supuMsu|supum|supuMsI|supumAMsi"),
    ("susaKi", "m", "susaKA|susaKAyO|susaKAyaH|susaKAyam|susaKAyO|susaKIn|susaKinA|susaKiByAm|susaKiBiH|susaKaye|susaKiByAm|susaKiByaH|susaKeH|susaKiByAm|susaKiByaH|susaKeH|susaKyoH|susaKInAm|susaKO|susaKyoH|susaKizu|susaKe|susaKAyO|susaKAyaH"),
    ("suhins", "m", "suhin|suhiMsO|suhiMsaH|suhiMsam|suhiMsO|suhiMsaH|suhiMsA|suhinByAm|suhinBiH|suhiMse|suhinByAm|suhinByaH|suhiMsaH|suhinByAm|suhinByaH|suhiMsaH|suhiMsoH|suhiMsAm|suhiMsi|suhiMsoH|suhinsu/suhintsu|suhin|suhiMsO|suhiMsaH"),
    ("sva", "n", "svam|sve|svAni|svam|sve|svAni|svena|svAByAm|svEH|svasmE|svAByAm|sveByaH|svAd/svasmAd/svasmAt/svAt|svAByAm|sveByaH|svasya|svayoH|svezAm|sve/svasmin|svayoH|svezu|sva|sve|svAni"),
    ("svasf", "f", "svasA|svasArO|svasAraH|svasAram|svasArO|svasFH|svasrA|svasfByAm|svasfBiH|svasre|svasfByAm|svasfByaH|svasuH|svasfByAm|svasfByaH|svasuH|svasroH|svasFRAm|svasari|svasroH|svasfzu|svasaH|svasArO|svasAraH"),
    ("hAhA", "m", "hAhAH|hAhO|hAhAH|hAhAm|hAhO|hAhAn|hAhA|hAhAByAm|hAhABiH|hAhE|hAhAByAm|hAhAByaH|hAhAH|hAhAByAm|hAhAByaH|hAhAH|hAhOH|hAhAm|hAhe|hAhOH|hAhAsu|hAhAH|hAhO|hAhAH"),
]

# ---------------------------------------------------------------------------
# Devanagari <-> SLP1 transliteration (display bridge; mirrors Rust translit.rs)
# ---------------------------------------------------------------------------
_DEV_VIRAMA = "\u094d"
_DEV_AVAGRAHA = "\u093d"
_DEV_ANUSVARA = "\u0902"
_DEV_CANDRABINDU = "\u0901"
DEV_VISARGA = "\u0903"
DEV_INDEP_VOWELS: dict[str, str] = {
    "अ": "a",
    "आ": "A",
    "इ": "i",
    "ई": "I",
    "उ": "u",
    "ऊ": "U",
    "ऋ": "f",
    "ॠ": "F",
    "ऌ": "x",
    "ॡ": "X",
    "ए": "e",
    "ऍ": "e",
    "ऎ": "e",
    "ऐ": "E",
    "ओ": "o",
    "ऑ": "o",
    "ऒ": "o",
    "औ": "O",
}
DEV_MATRAS: dict[str, str] = {
    "ा": "A",
    "ि": "i",
    "ी": "I",
    "ु": "u",
    "ू": "U",
    "ृ": "f",
    "ॄ": "F",
    "ॢ": "x",
    "ॣ": "X",
    "े": "e",
    "ॅ": "e",
    "ॆ": "e",
    "ै": "E",
    "ो": "o",
    "ॉ": "o",
    "ॊ": "o",
    "ौ": "O",
}
DEV_CONSONANTS: dict[str, str] = {
    "क": "k",
    "ख": "K",
    "ग": "g",
    "घ": "G",
    "ङ": "N",
    "च": "c",
    "छ": "C",
    "ज": "j",
    "झ": "J",
    "ञ": "Y",
    "ट": "w",
    "ठ": "W",
    "ड": "q",
    "ढ": "Q",
    "ण": "R",
    "त": "t",
    "थ": "T",
    "द": "d",
    "ध": "D",
    "न": "n",
    "प": "p",
    "फ": "P",
    "ब": "b",
    "भ": "B",
    "म": "m",
    "य": "y",
    "र": "r",
    "ल": "l",
    "ळ": "L",
    "व": "v",
    "श": "S",
    "ष": "z",
    "स": "s",
    "ह": "h",
}
SLP1_VOWELS: dict[str, tuple[str, str, str]] = {
    "a": ("a", "अ", ""),
    "A": ("A", "आ", "ा"),
    "i": ("i", "इ", "ि"),
    "I": ("I", "ई", "ी"),
    "u": ("u", "उ", "ु"),
    "U": ("U", "ऊ", "ू"),
    "f": ("f", "ऋ", "ा"),
    "F": ("F", "ॠ", "ॴ"),
    "x": ("x", "ঌ", "ং"),
    "X": ("X", "ঁ", "ঃ"),
    "e": ("e", "ए", "े"),
    "E": ("E", "ऐ", "ह"),
    "o": ("o", "ओ", "ो"),
    "O": ("O", "औ", "ौ"),
}
DEV_TO_SLP1_CONSONANT: dict[str, str] = {s: d for d, s in DEV_CONSONANTS.items()}
DEV_TO_SLP1_INDEP: dict[str, str] = dict(DEV_INDEP_VOWELS)

def contains_deva(s: str) -> bool:
    """True when `s` contains any Devanagari codepoint (U+0900-U+097F)."""
    return any("\u0900" <= c <= "\u097F" for c in s)

def deva_to_slp1(text: str) -> Optional[str]:
    """One Devanagari token (no separators) -> SLP1, e.g. deva_to_slp1("\u0926\u093e\u0935") -> "dAvA"."""
    if not text:
        return None
    chars = list(text)
    out: list[str] = []
    idx = 0
    while idx < len(chars):
        ch = chars[idx]
        if ch in DEV_INDEP_VOWELS:
            out.append(DEV_INDEP_VOWELS[ch])
            idx += 1
        elif ch in DEV_CONSONANTS:
            cons = DEV_CONSONANTS[ch]
            nxt = chars[idx + 1] if idx + 1 < len(chars) else None
            if nxt == _DEV_VIRAMA:
                out.append(cons)
                idx += 2
            elif nxt is not None and nxt in DEV_MATRAS:
                out.append(cons)
                out.append(DEV_MATRAS[nxt])
                idx += 2
            else:
                out.append(cons)
                out.append("a")
                idx += 1
        elif ch == _DEV_ANUSVARA or ch == _DEV_CANDRABINDU:
            out.append("M")
            idx += 1
        elif ch == DEV_VISARGA:
            out.append("H")
            idx += 1
        elif ch == _DEV_AVAGRAHA:
            out.append(chr(39))
            idx += 1
        elif ch == "_":
            out.append("_")
            idx += 1
        elif ch == "-":
            out.append("-")
            idx += 1
        else:
            return None
    return "".join(out)

def slp1_to_deva(text: str) -> Optional[str]:
    if not text or not all((c.isascii() and c.isalpha()) or c in (chr(39), "_", "-") for c in text):
        return None
    out: list[str] = []
    idx = 0
    chars = list(text)
    while idx < len(chars):
        ch = chars[idx]
        if ch in DEV_TO_SLP1_CONSONANT:
            deva = DEV_TO_SLP1_CONSONANT[ch]
            out.append(deva)
            nxt = chars[idx + 1] if idx + 1 < len(chars) else None
            if nxt == "a":
                idx += 2
            elif nxt is not None and nxt in SLP1_VOWELS:
                _v, _i, sign = SLP1_VOWELS[nxt]
                out.append(sign)
                idx += 2
            elif nxt in ("M", "H"):
                idx += 1
            else:
                out.append(_DEV_VIRAMA)
                idx += 1
        elif ch == "-":
            out.append("-")
            idx += 1
        elif ch == "a":
            out.append("\u0905")
            idx += 1
        elif ch in SLP1_VOWELS:
            _v, _i, indep = SLP1_VOWELS[ch]
            out.append(indep)
            idx += 1
        elif ch == "M":
            out.append(_DEV_ANUSVARA)
            idx += 1
        elif ch == "H":
            out.append(DEV_VISARGA)
            idx += 1
        elif ch == "'":
            out.append(_DEV_AVAGRAHA)
            idx += 1
        elif ch == "_":
            out.append("_")
            idx += 1
        else:
            return None
    return "".join(out)

def deva_stack_to_slp1(stack: str) -> Optional[str]:
    toks: list[str] = []
    for part in stack.replace(";", "+").split("+"):
        t = part.strip()
        if not t:
            continue
        if "-" in t:
            segs = []
            for seg in t.split("-"):
                v = deva_to_slp1(seg)
                if v is None:
                    return None
                segs.append(v)
            toks.append("-".join(segs))
        else:
            v = deva_to_slp1(t)
            if v is None:
                return None
            toks.append(v)
    if not toks:
        return None
    return ";".join(toks)

def normalize_stack_slp1(stack_slp1: str) -> str:
    return ";".join("AN" if tok == "A" else tok for tok in stack_slp1.split(";"))



def _generic_cells(stem: str, lg: Linga) -> list[SubantaSlot]:
    """Fallback generic consonant (halanta) paradigm for unmapped stems."""
    tbl = _GENERIC_CONS_TABLE
    cells: list[SubantaSlot] = []
    idx = 0
    for vib in VIBHAKTIS:
        for vac_i, vac in enumerate(VACANAS):
            suf = (tbl.get(vib) or ["-"])[vac_i] if vib in tbl else "-"
            if suf == "-":
                forms: list[str] = []
            elif " / " in suf:
                forms = [f.strip() for f in suf.split(" / ") if f.strip()]
            else:
                forms = [s.strip() for s in suf.split("/") if s.strip()]
            cells.append(SubantaSlot(vibhakti=int(VIBHAKTI_INDEX[vib]), vacana=int(VACANA_INDEX[vac]), forms=forms))
            idx += 1
    return cells


def _cells_for_paradigm(stem: str, paradigm: str) -> list[SubantaSlot]:
    """Build the 24 SubantaSlots for a registered paradigm from its suffix table."""
    tbl = _generate_noun(stem, paradigm)
    cells: list[SubantaSlot] = []
    for vib in VIBHAKTIS:
        forms = tbl.get(vib) or []
        for vac_i, vac in enumerate(VACANAS):
            raw = forms[vac_i] if vac_i < len(forms) else "-"
            if raw == "-":
                cell_forms: list[str] = []
            elif " / " in raw:
                cell_forms = [f.strip() for f in raw.split(" / ") if f.strip()]
            elif "/" in raw:
                cell_forms = [f.strip() for f in raw.split("/") if f.strip()]
            else:
                cell_forms = [raw.strip()] if raw.strip() else []
            cells.append(SubantaSlot(vibhakti=int(VIBHAKTI_INDEX[vib]), vacana=int(VACANA_INDEX[vac]), forms=cell_forms))

    # Stems ending in -hna carry 3 locative alternants per P. 8.4.27 / ashtadhyayi.com (e.g. azwAhne / azwAhni / azwAhani)
    if paradigm == "a_m" and stem.endswith("hna") and len(stem) > 3:
        p = stem[:-1]
        hna_base = stem[:-2]
        for i, c in enumerate(cells):
            if c.vibhakti == 7 and c.vacana == 1:
                cells[i] = SubantaSlot(vibhakti=7, vacana=1, forms=[f"{p}e", f"{p}i", f"{hna_base}ani"])
                break

    return cells


def generate_tables(stem: str, linga: "Linga | str") -> list[SubantaParadigm]:
    """Generate all plausible nominal paradigms for (stem, linga).

    Mirrors Rust `generate_tables(stem, linga) -> Vec<Paradigm>`: derived
    classes first, then site-verbatim grids. Ambiguous stems yield several
    paradigms (e.g. `vidvas` -> scholar + kvasu; `BU` -> BUti/bhu_f...).
    """
    lg = Linga.parse(linga) if not isinstance(linga, Linga) else linga
    if lg is None:
        raise ValueError(f"Invalid linga '{linga}'. Must be one of 'm', 'f', 'n'.")
    stem_clean = stem.strip()
    gender = _gender_of_liga(lg)

    out: list[SubantaParadigm] = []

    def add(cls_id: str, use_stem: str) -> None:
        if cls_id.startswith("SiteGrid:"):
            idx = int(cls_id.split(":", 1)[1])
            grid_stem, grid_lg, spec = SITE_GRIDS[idx]
            grid_linga = Linga.parse(grid_lg) or lg
            out.append(SubantaParadigm(stem=grid_stem, linga=grid_linga, class_id=cls_id, cells=site_grid_cells(spec)))
            return
        if cls_id == "generic":
            out.append(SubantaParadigm(stem=use_stem, linga=lg, class_id="generic", cells=_generic_cells(use_stem, lg)))
            return
        if cls_id.startswith("pronoun:"):
            lemma = cls_id.split(":", 1)[1]
            try:
                res = decline_pronoun(lemma, gender)
                forms_tbl = res.get("forms", {})
                cells: list[SubantaSlot] = []
                for vib in VIBHAKTIS:
                    row = forms_tbl.get(vib, [])
                    for vac_i, vac in enumerate(VACANAS):
                        raw = row[vac_i] if vac_i < len(row) else "-"
                        if raw == "-" or not raw:
                            f_list = []
                        elif " / " in raw:
                            f_list = [f.strip() for f in raw.split(" / ") if f.strip()]
                        else:
                            f_list = [f.strip() for f in raw.split("/") if f.strip()]
                        cells.append(SubantaSlot(vibhakti=VIBHAKTI_INDEX[vib], vacana=VACANA_INDEX[vac], forms=f_list))
                out.append(SubantaParadigm(stem=lemma, linga=lg, class_id=cls_id, cells=cells))
            except Exception:
                pass
            return
        if cls_id.startswith("numeral:"):
            lemma = cls_id.split(":", 1)[1]
            try:
                res = decline_numeral(lemma, gender)
                forms_tbl = res.get("forms", {})
                cells: list[SubantaSlot] = []
                for vib in VIBHAKTIS:
                    row = forms_tbl.get(vib, [])
                    for vac_i, vac in enumerate(VACANAS):
                        raw = row[vac_i] if vac_i < len(row) else "-"
                        if raw == "-" or not raw:
                            f_list = []
                        elif " / " in raw:
                            f_list = [f.strip() for f in raw.split(" / ") if f.strip()]
                        else:
                            f_list = [f.strip() for f in raw.split("/") if f.strip()]
                        cells.append(SubantaSlot(vibhakti=VIBHAKTI_INDEX[vib], vacana=VACANA_INDEX[vac], forms=f_list))
                out.append(SubantaParadigm(stem=lemma, linga=lg, class_id=cls_id, cells=cells))
            except Exception:
                pass
            return
        if cls_id not in PARADIGMS:
            return
        out.append(SubantaParadigm(stem=use_stem, linga=lg, class_id=cls_id, cells=_cells_for_paradigm(use_stem, cls_id)))

    for cls_id in detect_paradigm(stem_clean, gender):
        add(cls_id, stem_clean)

    for i, (s, l, _spec) in enumerate(SITE_GRIDS):
        if s == stem_clean and str(l) == str(lg):
            add(f"SiteGrid:{i}", stem_clean)

    # Alternate & pronominal candidate variants from ALL_VARIANT_GENERATORS
    from .subanta_variants import ALL_VARIANT_GENERATORS

    for gen in ALL_VARIANT_GENERATORS:
        for cid, vcells in gen(stem_clean, gender):
            out.append(SubantaParadigm(stem=stem_clean, linga=lg, class_id=cid, cells=vcells))

    # td_slots for asmad and yuzmad
    if stem_clean == "asmad":
        td_tabs: list[SubantaParadigm] = []
        for p in out:
            c = [SubantaSlot(vibhakti=s.vibhakti, vacana=s.vacana, forms=list(s.forms)) for s in p.cells]
            if len(c) > 14:
                c[12].forms = ["mad", "mat"]
                c[14].forms = ["asmad", "asmat"]
            td_tabs.append(SubantaParadigm(stem=p.stem, linga=p.linga, class_id=f"{p.class_id}:td", cells=c))
        out.extend(td_tabs)
    elif stem_clean == "yuzmad":
        td_tabs: list[SubantaParadigm] = []
        for p in out:
            c = [SubantaSlot(vibhakti=s.vibhakti, vacana=s.vacana, forms=list(s.forms)) for s in p.cells]
            if len(c) > 14:
                c[12].forms = ["tvad", "tvat"]
                c[14].forms = ["yuzmad", "yuzmat"]
            td_tabs.append(SubantaParadigm(stem=p.stem, linga=p.linga, class_id=f"{p.class_id}:td", cells=c))
        out.extend(td_tabs)

    # Apply word-level CELL_ALTS substitutions matching Rust reference engine
    alts = CELL_ALTS.get((stem_clean, gender))
    if alts:
        alts_tabs: list[SubantaParadigm] = []
        for p in out:
            new_cells: list[SubantaSlot] = []
            for idx, c in enumerate(p.cells):
                if idx in alts:
                    new_cells.append(SubantaSlot(vibhakti=c.vibhakti, vacana=c.vacana, forms=alts[idx]))
                else:
                    new_cells.append(c)
            alts_tabs.append(SubantaParadigm(stem=p.stem, linga=p.linga, class_id=f"{p.class_id}:alts", cells=new_cells))
        out.extend(alts_tabs)

    if not out:
        out.append(SubantaParadigm(stem=stem_clean, linga=lg, class_id="generic", cells=_generic_cells(stem_clean, lg)))
    return out


def classes_for(stem: str, linga: "Linga | str") -> list[str]:
    """Strict-plausible class ids for (stem, linga) — derived + site grids."""
    lg = Linga.parse(linga) if not isinstance(linga, Linga) else linga
    stem_clean = stem.strip()
    gender = _gender_of_liga(lg) if lg is not None else "m"
    out: list[str] = []
    for cls_id in detect_paradigm(stem_clean, gender):
        if cls_id not in out:
            out.append(cls_id)
    for i, (s, l, _spec) in enumerate(SITE_GRIDS):
        if s == stem_clean and str(l) == str(lg):
            cid = f"SiteGrid:{i}"
            if cid not in out:
                out.append(cid)
    return out


# ---------------------------------------------------------------------------
# Paninian Natva (r/f/F/z -> n becomes R)
# ---------------------------------------------------------------------------
def apply_natva(s: str, min_index: int = 0) -> str:
    """Applies Paninian natva (r/f/F/z -> n becomes R) within a pada.
    Follows Panini 8.4.1 (raṣābhyāṁ no ṇaḥ samānapade) and 8.4.2 (aṭkupvāṅnumvyavāye'pi).
    Blocks when intervening consonants are not in aṭ, ku, pu, or num (M).
    Protects padānta n per Panini 8.4.37 (padāntasya).
    `min_index`: only mutate n at or after `min_index`, preventing corruption of
    pre-existing lexical n in base prātipadikas across compound boundaries.
    """
    triggers = {'r', 'f', 'F', 'z'}
    at_ku_pu = set('aAiIuUfFxXeEoO' + 'yvrh' + 'kKgGN' + 'pPbBm' + 'M')
    chars = list(s)
    last_trig = -1
    for i, c in enumerate(chars):
        if c in triggers:
            last_trig = i
        elif c == 'n' and last_trig != -1:
            if i < min_index:
                continue
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
    "paYcamI": ["Ad / At", "AByAm", "eByaH"],
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
    "paYcamI": ["Ad / At", "AByAm", "eByaH"],
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

# ambArtha strIliNga  ambA / akkA / allA / ammA (Panini 7.3.107 ambArthanadyorhrasvaH)
_register("amba_f", "A", "f", "ambArtha strIliNga (ambA/akkA/allA) - hrasva saMboDana", {
    "prathamA": ["A", "e", "AH"],
    "dvitIyA": ["Am", "e", "AH"],
    "tftIyA": ["ayA", "AByAm", "ABiH"],
    "caturTI": ["AyE", "AByAm", "AByaH"],
    "paYcamI": ["AyAH", "AByAm", "AByaH"],
    "zazWI": ["AyAH", "ayoH", "AnAm"],
    "saptamI": ["AyAm", "ayoH", "Asu"],
    "saMboDana": ["a", "e", "AH"],
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

# i_kArAnta napuMsaka with optional pumvad-bhāva (Panini 7.1.74 iko'ci vibhaktau)
_register("i_opt_n", "i", "n", "i-kArAnta napuMsaka (optional pumvad-bhAva - anAdi)", {
    "prathamA": ["i", "inI", "Ini"],
    "dvitIyA": ["i", "inI", "Ini"],
    "tftIyA": ["inA", "iByAm", "iBiH"],
    "caturTI": ["ine / aye", "iByAm", "iByaH"],
    "paYcamI": ["inaH / eH", "iByAm", "iByaH"],
    "zazWI": ["inaH / eH", "inoH / yoH", "InAm"],
    "saptamI": ["ini / O", "inoH / yoH", "izu"],
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

# u_kArAnta napuMsaka with optional pumvad-bhāva (Panini 7.1.74 iko'ci vibhaktau)
_register("u_opt_n", "u", "n", "u-kArAnta napuMsaka (optional pumvad-bhAva - anfju/atinu)", {
    "prathamA": ["u", "unI", "Uni"],
    "dvitIyA": ["u", "unI", "Uni"],
    "tftIyA": ["unA", "uByAm", "uBiH"],
    "caturTI": ["une / ave", "uByAm", "uByaH"],
    "paYcamI": ["unaH / oH", "uByAm", "uByaH"],
    "zazWI": ["unaH / oH", "unoH / voH", "UnAm"],
    "saptamI": ["uni / O", "unoH / voH", "uzu"],
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
_register("bhu_m", "BU", "m", "U-kArAnta puMliNga (agniBU) - uvaN-AdeSa", {
    "prathamA": ["BUH", "BuvO", "BuvaH"],
    "dvitIyA": ["Buvam", "BuvO", "BuvaH"],
    "tftIyA": ["BuvA", "BUByAm", "BUBiH"],
    "caturTI": ["Buve", "BUByAm", "BUByaH"],
    "paYcamI": ["BuvaH", "BUByAm", "BUByaH"],
    "zazWI": ["BuvaH", "BuvoH", "BuvAm"],
    "saptamI": ["Buvi", "BuvoH", "BUzu"],
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

# f_kArAnta napuMsaka  dAtf n. (with optional bhāṣite puṁvad forms, Panini 7.1.74)
_register("f_n", "f", "n", "f-kArAnta napuMsaka (dAtf)", {
    "prathamA": ["f", "fnI", "Fni"],
    "dvitIyA": ["f", "fnI", "Fni"],
    "tftIyA": ["fnA / rA", "fByAm", "fBiH"],
    "caturTI": ["fne / re", "fByAm", "fByaH"],
    "paYcamI": ["fnaH / uH", "fByAm", "fByaH"],
    "zazWI": ["fnaH / uH", "fnoH / roH", "FnAm"],
    "saptamI": ["fni / ari", "fnoH / roH", "fzu"],
    "saMboDana": ["f / aH", "fnI", "Fni"],
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

# an-stem mUrDan / aRiman (m) - single consonant before an: elision (Panini 6.4.134 allopo'naH)
_register("an_drop_m", "an", "m", "an-kArAnta puMliNga (allopo'naH - mUrDan/aRiman)", {
    "prathamA": ["A", "AnO", "AnaH"],
    "dvitIyA": ["Anam", "AnO", "naH"],
    "tftIyA": ["nA", "aByAm", "aBiH"],
    "caturTI": ["ne", "aByAm", "aByaH"],
    "paYcamI": ["naH", "aByAm", "aByaH"],
    "zazWI": ["naH", "noH", "nAm"],
    "saptamI": ["ni / ani", "noH", "asu"],
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
    "saMboDana": ["an / a", "nI / anI", "Ani"],
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
    "saMboDana": ["an / a", "anI", "Ani"],
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
    "saptamI": ["paTi", "paToH", "paTizu"],
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

# vas-stem participles (kvasu - Panini 6.4.131 vasoḥ samprasāraṇam)
_register("vas_m", "vas", "m", "vas-kArAnta puMliNga (kvasu participle) - samprasAraRa", {
    "prathamA": ["vAn", "vAMsO", "vAMsaH"],
    "dvitIyA": ["vAMsam", "vAMsO", "uzaH"],
    "tftIyA": ["uzA", "vadByAm", "vadBiH"],
    "caturTI": ["uze", "vadByAm", "vadByaH"],
    "paYcamI": ["uzaH", "vadByAm", "vadByaH"],
    "zazWI": ["uzaH", "uzoH", "uzAm"],
    "saptamI": ["uzi", "uzoH", "vatsu"],
    "saMboDana": ["van", "vAMsO", "vAMsaH"],
})

# comparatives in -Iyas / -yas (Sreyas, balIyas - m.)
_register("yas_m", "yas", "m", "Iyas-kArAnta puMliNga comparative (Sreyas)", {
    "prathamA": ["yAn", "yAMsO", "yAMsaH"],
    "dvitIyA": ["yAMsam", "yAMsO", "yasaH"],
    "tftIyA": ["yasA", "yoByAm", "yoBiH"],
    "caturTI": ["yase", "yoByAm", "yoByaH"],
    "paYcamI": ["yasaH", "yoByAm", "yoByaH"],
    "zazWI": ["yasaH", "yasoH", "yasAm"],
    "saptamI": ["yasi", "yasoH", "yaHsu / yassu"],
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
    "saptamI": ["yasi", "yasoH", "yaHsu / yassu"],
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
    "saptamI": ["asi", "asoH", "aHsu / assu"],
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
    "saptamI": ["asi", "asoH", "aHsu / assu"],
    "saMboDana": ["aH", "asO", "asaH"],
})

_register("as_f", "as", "f", "as-kArAnta strIliNga (sumanas - bahuvrIhi f.)", {
    "prathamA": ["AH", "asO", "asaH"],
    "dvitIyA": ["asam", "asO", "asaH"],
    "tftIyA": ["asA", "oByAm", "oBiH"],
    "caturTI": ["ase", "oByAm", "oByaH"],
    "paYcamI": ["asaH", "oByAm", "oByaH"],
    "zazWI": ["asaH", "asoH", "asAm"],
    "saptamI": ["asi", "asoH", "aHsu / assu"],
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
    "saptamI": ["uzi", "uzoH", "uHzu / uzzu"],
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
    "saptamI": ["izi", "izoH", "iHzu / izzu"],
    "saMboDana": ["iH", "izI", "IMzi"],
})

# c-stem vAc (f)
_register("c_f", "c", "f", "c-kArAnta strIliNga (vAc)", {
    "prathamA": ["g / k", "cO", "caH"],
    "dvitIyA": ["cam", "cO", "caH"],
    "tftIyA": ["cA", "gByAm", "gBiH"],
    "caturTI": ["ce", "gByAm", "gByaH"],
    "paYcamI": ["caH", "gByAm", "gByaH"],
    "zazWI": ["caH", "coH", "cAm"],
    "saptamI": ["ci", "coH", "kzu"],
    "saMboDana": ["g / k", "cO", "caH"],
})

# t-stem marut (m), sarit (f), jagat (n)
_register("t_m", "t", "m", "t-kArAnta puMliNga (marut)", {
    "prathamA": ["d / t", "tO", "taH"],
    "dvitIyA": ["tam", "tO", "taH"],
    "tftIyA": ["tA", "dByAm", "dBiH"],
    "caturTI": ["te", "dByAm", "dByaH"],
    "paYcamI": ["taH", "dByAm", "dByaH"],
    "zazWI": ["taH", "toH", "tAm"],
    "saptamI": ["ti", "toH", "tsu"],
    "saMboDana": ["d / t", "tO", "taH"],
})
_register("t_f", "t", "f", "t-kArAnta strIliNga (sarit)", {
    "prathamA": ["d / t", "tO", "taH"],
    "dvitIyA": ["tam", "tO", "taH"],
    "tftIyA": ["tA", "dByAm", "dBiH"],
    "caturTI": ["te", "dByAm", "dByaH"],
    "paYcamI": ["taH", "dByAm", "dByaH"],
    "zazWI": ["taH", "toH", "tAm"],
    "saptamI": ["ti", "toH", "tsu"],
    "saMboDana": ["d / t", "tO", "taH"],
})
_register("t_n", "t", "n", "t-kArAnta napuMsaka (jagat)", {
    "prathamA": ["d / t", "tI", "nti"],
    "dvitIyA": ["d / t", "tI", "nti"],
    "tftIyA": ["tA", "dByAm", "dBiH"],
    "caturTI": ["te", "dByAm", "dByaH"],
    "paYcamI": ["taH", "dByAm", "dByaH"],
    "zazWI": ["taH", "toH", "tAm"],
    "saptamI": ["ti", "toH", "tsu"],
    "saMboDana": ["d / t", "tI", "nti"],
})

# d-stem sampad / Apad / vipad (f) & suhfd (m)
_register("d_f", "d", "f", "d-kArAnta strIliNga (sampad)", {
    "prathamA": ["d / t", "dO", "daH"],
    "dvitIyA": ["dam", "dO", "daH"],
    "tftIyA": ["dA", "dByAm", "dBiH"],
    "caturTI": ["de", "dByAm", "dByaH"],
    "paYcamI": ["daH", "dByAm", "dByaH"],
    "zazWI": ["daH", "doH", "dAm"],
    "saptamI": ["di", "doH", "tsu"],
    "saMboDana": ["d / t", "dO", "daH"],
})
_register("d_m", "d", "m", "d-kArAnta puMliNga (suhfd)", {
    "prathamA": ["d / t", "dO", "daH"],
    "dvitIyA": ["dam", "dO", "daH"],
    "tftIyA": ["dA", "dByAm", "dBiH"],
    "caturTI": ["de", "dByAm", "dByaH"],
    "paYcamI": ["daH", "dByAm", "dByaH"],
    "zazWI": ["daH", "doH", "dAm"],
    "saptamI": ["di", "doH", "tsu"],
    "saMboDana": ["d / t", "dO", "daH"],
})

# th-stem agnimaT (m)
_register("th_m", "T", "m", "th-kArAnta puMliNga (agnimaT)", {
    "prathamA": ["d / t", "TO", "TaH"],
    "dvitIyA": ["Tam", "TO", "TaH"],
    "tftIyA": ["TA", "dByAm", "dBiH"],
    "caturTI": ["Te", "dByAm", "dByaH"],
    "paYcamI": ["TaH", "dByAm", "dByaH"],
    "zazWI": ["TaH", "ToH", "TAm"],
    "saptamI": ["Ti", "ToH", "tsu"],
    "saMboDana": ["d / t", "TO", "TaH"],
})

# j-stem Bizaj / ftvij (m)
_register("j_m", "j", "m", "j-kArAnta puMliNga (Bizaj)", {
    "prathamA": ["g / k", "jO", "jaH"],
    "dvitIyA": ["jam", "jO", "jaH"],
    "tftIyA": ["jA", "gByAm", "gBiH"],
    "caturTI": ["je", "gByAm", "gByaH"],
    "paYcamI": ["jaH", "gByAm", "gByaH"],
    "zazWI": ["jaH", "joH", "jAm"],
    "saptamI": ["ji", "joH", "kzu"],
    "saMboDana": ["g / k", "jO", "jaH"],
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

# anaquh (ox / bull, m.) - Panini 7.1.98, 7.1.99, 8.2.72
_register("anaquh_m", "anaquh", "m", "h-kArAnta puMliNga (anaquh - ox/bull) - irregular", {
    "prathamA": ["anaqvAn", "anaqvAhO", "anaqvAhaH"],
    "dvitIyA": ["anaqvAham", "anaqvAhO", "anaquhaH"],
    "tftIyA": ["anaquhA", "anaqudByAm", "anaqudBiH"],
    "caturTI": ["anaquhe", "anaqudByAm", "anaqudByaH"],
    "paYcamI": ["anaquhaH", "anaqudByAm", "anaqudByaH"],
    "zazWI": ["anaquhaH", "anaquhoH", "anaquhAm"],
    "saptamI": ["anaquhi", "anaquhoH", "anaqutsu / anaqvatsu"],
    "saMboDana": ["anaqvan", "anaqvAhO", "anaqvAhaH"],
})

# A-stem masculine (root stems like viSvapA, somapA - Panini 6.4.140 Ato DdtoH)
_register("A_m", "A", "m", "A-kArAnta puMliNga (viSvapA - root A-stem)", {
    "prathamA": ["AH", "O", "AH"],
    "dvitIyA": ["Am", "O", "aH"],
    "tftIyA": ["A", "AByAm", "ABiH"],
    "caturTI": ["e", "AByAm", "AByaH"],
    "paYcamI": ["aH", "AByAm", "AByaH"],
    "zazWI": ["aH", "oH", "Am"],
    "saptamI": ["i", "oH", "Asu"],
    "saMboDana": ["AH", "O", "AH"],
})

# I-stem masculine (suDI - iyaN-AdeSa per Panini 6.4.85)
_register("sudhi_m", "I", "m", "I-kArAnta puMliNga (suDI - iyaN-AdeSa)", {
    "prathamA": ["IH", "iyO", "iyaH"],
    "dvitIyA": ["iyam", "iyO", "iyaH"],
    "tftIyA": ["iyA", "IByAm", "IBiH"],
    "caturTI": ["iye", "IByAm", "IByaH"],
    "paYcamI": ["iyaH", "IByAm", "IByaH"],
    "zazWI": ["iyaH", "iyoH", "iyAm"],
    "saptamI": ["iyi", "iyoH", "Izu"],
    "saMboDana": ["IH", "iyO", "iyaH"],
})

# I-stem masculine (senAnI / grAmaRI - yaR-AdeSa per Panini 6.4.82, 7.3.116 nerAm nIByaH)
_register("I_m", "I", "m", "I-kArAnta puMliNga (senAnI - yaR-AdeSa)", {
    "prathamA": ["IH", "yO", "yaH"],
    "dvitIyA": ["yam", "yO", "yaH"],
    "tftIyA": ["yA", "IByAm", "IBiH"],
    "caturTI": ["ye", "IByAm", "IByaH"],
    "paYcamI": ["yaH", "IByAm", "IByaH"],
    "zazWI": ["yaH", "yoH", "yAm"],
    "saptamI": ["yAm", "yoH", "Izu"],
    "saMboDana": ["IH", "yO", "yaH"],
})

# r-stem feminine (gir - speech/voice: dIrGa ikaH Panini 8.2.76)
_register("gir_f", "gir", "f", "r-kArAnta strIliNga (gir - voice/speech)", {
    "prathamA": ["gIH", "girO", "giraH"],
    "dvitIyA": ["giram", "girO", "giraH"],
    "tftIyA": ["girA", "gIrByAm", "gIrBiH"],
    "caturTI": ["gire", "gIrByAm", "gIrByaH"],
    "paYcamI": ["giraH", "gIrByAm", "gIrByaH"],
    "zazWI": ["giraH", "giroH", "girAm"],
    "saptamI": ["giri", "giroH", "gIrzu"],
    "saMboDana": ["gIH", "girO", "giraH"],
})

# r-stem feminine (pur - city: dIrGa ikaH Panini 8.2.76)
_register("pur_f", "pur", "f", "r-kArAnta strIliNga (pur - city)", {
    "prathamA": ["pUH", "purO", "puraH"],
    "dvitIyA": ["puram", "purO", "puraH"],
    "tftIyA": ["purA", "pUrByAm", "pUrBiH"],
    "caturTI": ["pure", "pUrByAm", "pUrByaH"],
    "paYcamI": ["puraH", "pUrByAm", "pUrByaH"],
    "zazWI": ["puraH", "puroH", "purAm"],
    "saptamI": ["puri", "puroH", "pUrzu"],
    "saMboDana": ["pUH", "purO", "puraH"],
})

# r-stem feminine (dvAr - door)
_register("r_f", "r", "f", "r-kArAnta strIliNga (dvAr - door)", {
    "prathamA": ["H", "rO", "raH"],
    "dvitIyA": ["ram", "rO", "raH"],
    "tftIyA": ["rA", "rByAm", "rBiH"],
    "caturTI": ["re", "rByAm", "rByaH"],
    "paYcamI": ["raH", "rByAm", "rByaH"],
    "zazWI": ["raH", "roH", "rAm"],
    "saptamI": ["ri", "roH", "rzu"],
    "saMboDana": ["H", "rO", "raH"],
})

# div / dyu (heaven/sky - Panini 6.1.131 diva aut)
_register("div_f", "div", "f", "v-kArAnta strIliNga (div/dyu - heaven/sky)", {
    "prathamA": ["dyOH", "divO", "divaH"],
    "dvitIyA": ["divam", "divO", "divaH"],
    "tftIyA": ["divA", "dyuByAm", "dyuBiH"],
    "caturTI": ["dive", "dyuByAm", "dyuByaH"],
    "paYcamI": ["divaH", "dyuByAm", "dyuByaH"],
    "zazWI": ["divaH", "divoH", "divAm"],
    "saptamI": ["divi", "divoH", "dyuzu"],
    "saMboDana": ["dyOH", "divO", "divaH"],
})
_register("div_m", "div", "m", "v-kArAnta puMliNga (div/dyu - heaven/sky)", {
    "prathamA": ["dyOH", "divO", "divaH"],
    "dvitIyA": ["divam", "divO", "divaH"],
    "tftIyA": ["divA", "dyuByAm", "dyuBiH"],
    "caturTI": ["dive", "dyuByAm", "dyuByaH"],
    "paYcamI": ["divaH", "dyuByAm", "dyuByaH"],
    "zazWI": ["divaH", "divoH", "divAm"],
    "saptamI": ["divi", "divoH", "dyuzu"],
    "saMboDana": ["dyOH", "divO", "divaH"],
})

# Directional adjectives in -aYc (prAYc / pratyaYc / udaYc / anvac)
_register("anvac_m", "anvac", "m", "c-kArAnta puMliNga (anvac - following) - irregular", {
    "prathamA": ["anvaN", "anvaYcO", "anvaYcaH"],
    "dvitIyA": ["anvaYcam", "anvaYcO", "anUcaH"],
    "tftIyA": ["anUcA", "anvagByAm", "anvagBiH"],
    "caturTI": ["anUce", "anvagByAm", "anvagByaH"],
    "paYcamI": ["anUcaH", "anvagByAm", "anvagByaH"],
    "zazWI": ["anUcaH", "anUcoH", "anUcAm"],
    "saptamI": ["anUci", "anUcoH", "anvakzu"],
    "saMboDana": ["anvaN", "anvaYcO", "anvaYcaH"],
})
_register("pranc_m", "prAYc", "m", "c-kArAnta puMliNga (prAYc - eastern/forward)", {
    "prathamA": ["prAN", "prAYcO", "prAYcaH"],
    "dvitIyA": ["prAYcam", "prAYcO", "prAcaH"],
    "tftIyA": ["prAcA", "prAgByAm", "prAgBiH"],
    "caturTI": ["prAce", "prAgByAm", "prAgByaH"],
    "paYcamI": ["prAcaH", "prAgByAm", "prAgByaH"],
    "zazWI": ["prAcaH", "prAcoH", "prAcAm"],
    "saptamI": ["prAci", "prAcoH", "prAkzu"],
    "saMboDana": ["prAN", "prAYcO", "prAYcaH"],
})

_register("pratyanc_m", "pratyaYc", "m", "c-kArAnta puMliNga (pratyaYc - western/backward)", {
    "prathamA": ["pratyaN", "pratyaYcO", "pratyaYcaH"],
    "dvitIyA": ["pratyaYcam", "pratyaYcO", "pratIcaH"],
    "tftIyA": ["pratIcA", "pratyagByAm", "pratyagBiH"],
    "caturTI": ["pratIce", "pratyagByAm", "pratyagByaH"],
    "paYcamI": ["pratIcaH", "pratyagByAm", "pratyagByaH"],
    "zazWI": ["pratIcaH", "pratIcoH", "pratIcAm"],
    "saptamI": ["pratIci", "pratIcoH", "pratyakzu"],
    "saMboDana": ["pratyaN", "pratyaYcO", "pratyaYcaH"],
})

_register("udanc_m", "udaYc", "m", "c-kArAnta puMliNga (udaYc - northern/upward)", {
    "prathamA": ["udaN", "udaYcO", "udaYcaH"],
    "dvitIyA": ["udaYcam", "udaYcO", "udIcaH"],
    "tftIyA": ["udIcA", "udagByAm", "udagBiH"],
    "caturTI": ["udIce", "udagByAm", "udagByaH"],
    "paYcamI": ["udIcaH", "udagByAm", "udagByaH"],
    "zazWI": ["udIcaH", "udIcoH", "udIcAm"],
    "saptamI": ["udIci", "udIcoH", "udakzu"],
    "saMboDana": ["udaN", "udaYcO", "udaYcaH"],
})

# krozwu (jackal, m.) - Panini 7.1.95 (tftIyAdisu tftvam)
_register("krozwu_m", "krozwu", "m", "u-kArAnta puMliNga (krozwu - jackal) - tf-AdeSa", {
    "prathamA": ["krozwA", "krozwArO", "krozwAraH"],
    "dvitIyA": ["krozwAram", "krozwArO", "krozwUn"],
    "tftIyA": ["krozwrA / krozwunA", "krozwuByAm", "krozwuBiH"],
    "caturTI": ["krozwre / krozwave", "krozwuByAm", "krozwuByaH"],
    "paYcamI": ["krozwuH / krozwOH", "krozwuByAm", "krozwuByaH"],
    "zazWI": ["krozwuH / krozwOH", "krozwroH / krozwvoH", "krozwFRAm / krozwUnAm"],
    "saptamI": ["krozwari / krozwO", "krozwroH / krozwvoH", "krozwuzu"],
    "saMboDana": ["krozwo", "krozwArO", "krozwAraH"],
})

# candramas (moon, m.) - as-stem masculine
_register("candramas_m", "candramas", "m", "as-kArAnta puMliNga (candramas - moon)", {
    "prathamA": ["candramAH", "candramasO", "candramasaH"],
    "dvitIyA": ["candramasam", "candramasO", "candramasaH"],
    "tftIyA": ["candramasA", "candramoByAm", "candramoBiH"],
    "caturTI": ["candramase", "candramoByAm", "candramoByaH"],
    "paYcamI": ["candramasaH", "candramoByAm", "candramoByaH"],
    "zazWI": ["candramasaH", "candramasoH", "candramasAm"],
    "saptamI": ["candramasi", "candramasoH", "candramaHsu / candramassu"],
    "saMboDana": ["candramaH", "candramasO", "candramasaH"],
})

# yuj (companion / yoke, m.) - Panini 7.1.71 yuje-rasamAse (num in sarvanAmasthAna)
_register("yuj_m", "yuj", "m", "j-kArAnta puMliNga (yuj - companion/yoke) - irregular", {
    "prathamA": ["yuN", "yuYjO", "yuYjaH"],
    "dvitIyA": ["yuYjam", "yuYjO", "yujaH"],
    "tftIyA": ["yujA", "yugByAm", "yugBiH"],
    "caturTI": ["yuje", "yugByAm", "yugByaH"],
    "paYcamI": ["yujaH", "yugByAm", "yugByaH"],
    "zazWI": ["yujaH", "yujoH", "yujAm"],
    "saptamI": ["yuji", "yujoH", "yukzu"],
    "saMboDana": ["yuN", "yuYjO", "yuYjaH"],
})

# Buj (enjoyer / ruler / eater, m./f.) - regular j-stem with kutva
_register("Buj_m", "Buj", "m", "j-kArAnta puMliNga (Buj - ruler/enjoyer)", {
    "prathamA": ["Bug / Buk", "BujO", "BujaH"],
    "dvitIyA": ["Bujam", "BujO", "BujaH"],
    "tftIyA": ["BujA", "BugByAm", "BugBiH"],
    "caturTI": ["Buje", "BugByAm", "BugByaH"],
    "paYcamI": ["BujaH", "BugByAm", "BugByaH"],
    "zazWI": ["BujaH", "BujoH", "BujAm"],
    "saptamI": ["Buji", "BujoH", "Bukzu"],
    "saMboDana": ["Bug / Buk", "BujO", "BujaH"],
})
_register("Buj_f", "Buj", "f", "j-kArAnta strIliNga (Buj - ruler/enjoyer)", {
    "prathamA": ["Bug / Buk", "BujO", "BujaH"],
    "dvitIyA": ["Bujam", "BujO", "BujaH"],
    "tftIyA": ["BujA", "BugByAm", "BugBiH"],
    "caturTI": ["Buje", "BugByAm", "BugByaH"],
    "paYcamI": ["BujaH", "BugByAm", "BugByaH"],
    "zazWI": ["BujaH", "BujoH", "BujAm"],
    "saptamI": ["Buji", "BujoH", "Bukzu"],
    "saMboDana": ["Bug / Buk", "BujO", "BujaH"],
})

# kzuD (hunger, f.) & dh-stems (samiD)
_register("kzuD_f", "kzuD", "f", "D-kArAnta strIliNga (kzuD - hunger)", {
    "prathamA": ["kzut / kzud", "kzuDO", "kzuDaH"],
    "dvitIyA": ["kzuDam", "kzuDO", "kzuDaH"],
    "tftIyA": ["kzuDA", "kzudByAm", "kzudBiH"],
    "caturTI": ["kzuDe", "kzudByAm", "kzudByaH"],
    "paYcamI": ["kzuDaH", "kzudByAm", "kzudByaH"],
    "zazWI": ["kzuDaH", "kzuDoH", "kzuDAm"],
    "saptamI": ["kzuDi", "kzuDoH", "kzutsu"],
    "saMboDana": ["kzut / kzud", "kzuDO", "kzuDaH"],
})
_register("dh_f", "D", "f", "D-kArAnta strIliNga (samiD - fuel)", {
    "prathamA": ["t / d", "DO", "DaH"],
    "dvitIyA": ["Dam", "DO", "DaH"],
    "tftIyA": ["DA", "dByAm", "dBiH"],
    "caturTI": ["De", "dByAm", "dByaH"],
    "paYcamI": ["DaH", "dByAm", "dByaH"],
    "zazWI": ["DaH", "DoH", "DAm"],
    "saptamI": ["Di", "DoH", "tsu"],
    "saMboDana": ["t / d", "DO", "DaH"],
})

# vftrahan (slayer of Vritra, m.) - Panini 6.4.98, 7.3.54
_register("vftrahan_m", "vftrahan", "m", "an-kArAnta puMliNga (vftrahan - slayer of Vritra) - irregular", {
    "prathamA": ["vftrahA", "vftrahaRO", "vftrahaRaH"],
    "dvitIyA": ["vftrahaRam", "vftrahaRO", "vftraGRaH"],
    "tftIyA": ["vftraGRA", "vftrahaByAm", "vftrahaBiH"],
    "caturTI": ["vftraGRe", "vftrahaByAm", "vftrahaByaH"],
    "paYcamI": ["vftraGRaH", "vftrahaByAm", "vftrahaByaH"],
    "zazWI": ["vftraGRaH", "vftraGRoH", "vftraGRAm"],
    "saptamI": ["vftrahaRi / vftraGNi", "vftraGRoH", "vftrahasu"],
    "saMboDana": ["vftrahan", "vftrahaRO", "vftrahaRaH"],
})

# han-compounds (Satruhan, ripuhan - slayer, m.)
_register("han_m", "han", "m", "an-kArAnta puMliNga (han-compounds - slayer) - irregular", {
    "prathamA": ["hA", "haRO / hanO", "haRaH / hanaH"],
    "dvitIyA": ["haRam / hanam", "haRO / hanO", "GnaH / GRaH"],
    "tftIyA": ["GnA / GRA", "haByAm", "haBiH"],
    "caturTI": ["Gne / GRe", "haByAm", "haByaH"],
    "paYcamI": ["GnaH / GRaH", "haByAm", "haByaH"],
    "zazWI": ["GnaH / GRaH", "GnoH / GRoH", "GnAm / GRAm"],
    "saptamI": ["haRi / hani / Gni / GNi", "GnoH / GRoH", "hasu"],
    "saMboDana": ["han", "haRO / hanO", "haRaH / hanaH"],
})

# maGavan (Indra, m.) - Panini 6.4.128 maGavA bahulam (samprasAraRa maGonaH)
_register("maghavan_m", "maGavan", "m", "an-kArAnta puMliNga (maGavan - Indra) - samprasAraRa", {
    "prathamA": ["maGavAn", "maGavAntO", "maGavAntaH"],
    "dvitIyA": ["maGavAntam", "maGavAntO", "maGonaH"],
    "tftIyA": ["maGonA", "maGavadByAm", "maGavadBiH"],
    "caturTI": ["maGone", "maGavadByAm", "maGavadByaH"],
    "paYcamI": ["maGonaH", "maGavadByAm", "maGavadByaH"],
    "zazWI": ["maGonaH", "maGonoH", "maGonAm"],
    "saptamI": ["maGoni", "maGonoH", "maGavatsu"],
    "saMboDana": ["maGavan", "maGavAntO", "maGavAntaH"],
})

# nf (man, m.) - Panini 6.4.11-12 (guRa in sarvanAmasTAna, optional dirgha in zazWI bahuvacana)
_register("nr_m", "nf", "m", "f-kArAnta puMliNga (nf - man) - irregular (Panini 6.4.11-12)", {
    "prathamA": ["nA", "narO", "naraH"],
    "dvitIyA": ["naram", "narO", "nfn"],
    "tftIyA": ["nrA", "nfByAm", "nfBiH"],
    "caturTI": ["nre", "nfByAm", "nfByaH"],
    "paYcamI": ["nuH", "nfByAm", "nfByaH"],
    "zazWI": ["nuH", "nroH", "nfRAm / nFRAM"],
    "saptamI": ["nari", "nroH", "nfzu"],
    "saMboDana": ["nar / naH", "narO", "naraH"],
})

# pad / pat (foot, m.) - Panini 6.4.130 pAdaH pat
_register("pad_m", "pad", "m", "d-kArAnta puMliNga (pad - foot) - irregular (Panini 6.4.130)", {
    "prathamA": ["pAt", "padO", "padaH"],
    "dvitIyA": ["padam", "padO", "padaH"],
    "tftIyA": ["padA", "padByAm", "padBiH"],
    "caturTI": ["pade", "padByAm", "padByaH"],
    "paYcamI": ["padaH", "padByAm", "padByaH"],
    "zazWI": ["padaH", "padoH", "padAm"],
    "saptamI": ["padi", "padoH", "patsu"],
    "saMboDana": ["pAt", "padO", "padaH"],
})

# duh (milker, m/f) - Panini 8.2.32, 8.2.37 (dāder dhātor ghaḥ + Grassmann throwback bhaṣ)
_register("duh_m", "duh", "m", "h-kArAnta puMliNga (duh - milker) - throwback aspiration (Panini 8.2.32, 8.2.37)", {
    "prathamA": ["Duk / Dug", "duhO", "duhaH"],
    "dvitIyA": ["duham", "duhO", "duhaH"],
    "tftIyA": ["duhA", "DugByAm", "DugBiH"],
    "caturTI": ["duhe", "DugByAm", "DugByaH"],
    "paYcamI": ["duhaH", "DugByAm", "DugByaH"],
    "zazWI": ["duhaH", "duhoH", "duhAm"],
    "saptamI": ["duhi", "duhoH", "Dukzu"],
    "saMboDana": ["Duk / Dug", "duhO", "duhaH"],
})
_register("duh_f", "duh", "f", "h-kArAnta strIliNga (duh - milker) - throwback aspiration (Panini 8.2.32, 8.2.37)", {
    "prathamA": ["Duk / Dug", "duhO", "duhaH"],
    "dvitIyA": ["duham", "duhO", "duhaH"],
    "tftIyA": ["duhA", "DugByAm", "DugBiH"],
    "caturTI": ["duhe", "DugByAm", "DugByaH"],
    "paYcamI": ["duhaH", "DugByAm", "DugByaH"],
    "zazWI": ["duhaH", "duhoH", "duhAm"],
    "saptamI": ["duhi", "duhoH", "Dukzu"],
    "saMboDana": ["Duk / Dug", "duhO", "duhaH"],
})

# lih (licker, m/f) - Panini 8.2.31 ho ḍhaḥ -> liṭ/liḍ
_register("lih_m", "lih", "m", "h-kArAnta puMliNga (lih - licker) - cerebral (Panini 8.2.31)", {
    "prathamA": ["liw / liq", "lihO", "lihaH"],
    "dvitIyA": ["liham", "lihO", "lihaH"],
    "tftIyA": ["lihA", "liqByAm", "liqBiH"],
    "caturTI": ["lihe", "liqByAm", "liqByaH"],
    "paYcamI": ["lihaH", "liqByAm", "liqByaH"],
    "zazWI": ["lihaH", "lihoH", "lihAm"],
    "saptamI": ["lihi", "lihoH", "liwsu"],
    "saMboDana": ["liw / liq", "lihO", "lihaH"],
})
_register("lih_f", "lih", "f", "h-kArAnta strIliNga (lih - licker) - cerebral (Panini 8.2.31)", {
    "prathamA": ["liw / liq", "lihO", "lihaH"],
    "dvitIyA": ["liham", "lihO", "lihaH"],
    "tftIyA": ["lihA", "liqByAm", "liqBiH"],
    "caturTI": ["lihe", "liqByAm", "liqByaH"],
    "paYcamI": ["lihaH", "liqByAm", "liqByaH"],
    "zazWI": ["lihaH", "lihoH", "lihAm"],
    "saptamI": ["lihi", "lihoH", "liwsu"],
    "saMboDana": ["liw / liq", "lihO", "lihaH"],
})

# druh (enemy, m/f) - Panini 8.2.33 vā droha-moha-snehānucidām (optional gh/ḍh with throwback aspiration)
_register("druh_m", "druh", "m", "h-kArAnta puMliNga (druh - enemy) - optional gh/dh (Panini 8.2.33)", {
    "prathamA": ["Druk / Drug / Druw / Druq", "druhO", "druhaH"],
    "dvitIyA": ["druham", "druhO", "druhaH"],
    "tftIyA": ["druhA", "DrugByAm / DruqByAm", "DrugBiH / DruqBiH"],
    "caturTI": ["druhe", "DrugByAm / DruqByAm", "DrugByaH / DruqByaH"],
    "paYcamI": ["druhaH", "DrugByAm / DruqByAm", "DrugByaH / DruqByaH"],
    "zazWI": ["druhaH", "druhoH", "druhAm"],
    "saptamI": ["druhi", "druhoH", "Drukzu / Druwsu"],
    "saMboDana": ["Druk / Drug / Druw / Druq", "druhO", "druhaH"],
})
_register("druh_f", "druh", "f", "h-kArAnta strIliNga (druh - enemy) - optional gh/dh (Panini 8.2.33)", {
    "prathamA": ["Druk / Drug / Druw / Druq", "druhO", "druhaH"],
    "dvitIyA": ["druham", "druhO", "druhaH"],
    "tftIyA": ["druhA", "DrugByAm / DruqByAm", "DrugBiH / DruqBiH"],
    "caturTI": ["druhe", "DrugByAm / DruqByAm", "DrugByaH / DruqByaH"],
    "paYcamI": ["druhaH", "DrugByAm / DruqByAm", "DrugByaH / DruqByaH"],
    "zazWI": ["druhaH", "druhoH", "druhAm"],
    "saptamI": ["druhi", "druhoH", "Drukzu / Druwsu"],
    "saMboDana": ["Druk / Drug / Druw / Druq", "druhO", "druhaH"],
})

# muh (confused, m/f) - Panini 8.2.33
_register("muh_m", "muh", "m", "h-kArAnta puMliNga (muh - bewildered) - optional gh/dh (Panini 8.2.33)", {
    "prathamA": ["muk / mug / muw / muq", "muhO", "muhaH"],
    "dvitIyA": ["muham", "muhO", "muhaH"],
    "tftIyA": ["muhA", "mugByAm / muqByAm", "mugBiH / muqBiH"],
    "caturTI": ["muhe", "mugByAm / muqByAm", "mugByaH / muqByaH"],
    "paYcamI": ["muhaH", "mugByAm / muqByAm", "mugByaH / muqByaH"],
    "zazWI": ["muhaH", "muhoH", "muhAm"],
    "saptamI": ["muhi", "muhoH", "mukzu / muwsu"],
    "saMboDana": ["muk / mug / muw / muq", "muhO", "muhaH"],
})
_register("muh_f", "muh", "f", "h-kArAnta strIliNga (muh - bewildered) - optional gh/dh (Panini 8.2.33)", {
    "prathamA": ["muk / mug / muw / muq", "muhO", "muhaH"],
    "dvitIyA": ["muham", "muhO", "muhaH"],
    "tftIyA": ["muhA", "mugByAm / muqByAm", "mugBiH / muqBiH"],
    "caturTI": ["muhe", "mugByAm / muqByAm", "mugByaH / muqByaH"],
    "paYcamI": ["muhaH", "mugByAm / muqByAm", "mugByaH / muqByaH"],
    "zazWI": ["muhaH", "muhoH", "muhAm"],
    "saptamI": ["muhi", "muhoH", "mukzu / muwsu"],
    "saMboDana": ["muk / mug / muw / muq", "muhO", "muhaH"],
})

# snih (affectionate, m/f) - Panini 8.2.33
_register("snih_m", "snih", "m", "h-kArAnta puMliNga (snih - attached) - optional gh/dh (Panini 8.2.33)", {
    "prathamA": ["snik / snig / sniw / sniq", "snihO", "snihaH"],
    "dvitIyA": ["sniham", "snihO", "snihaH"],
    "tftIyA": ["snihA", "snigByAm / sniqByAm", "snigBiH / sniqBiH"],
    "caturTI": ["snihe", "snigByAm / sniqByAm", "snigByaH / sniqByaH"],
    "paYcamI": ["snihaH", "snigByAm / sniqByAm", "snigByaH / sniqByaH"],
    "zazWI": ["snihaH", "snihoH", "snihAm"],
    "saptamI": ["snihi", "snihoH", "snikzu / sniwsu"],
    "saMboDana": ["snik / snig / sniw / sniq", "snihO", "snihaH"],
})
_register("snih_f", "snih", "f", "h-kArAnta strIliNga (snih - attached) - optional gh/dh (Panini 8.2.33)", {
    "prathamA": ["snik / snig / sniw / sniq", "snihO", "snihaH"],
    "dvitIyA": ["sniham", "snihO", "snihaH"],
    "tftIyA": ["snihA", "snigByAm / sniqByAm", "snigBiH / sniqBiH"],
    "caturTI": ["snihe", "snigByAm / sniqByAm", "snigByaH / sniqByaH"],
    "paYcamI": ["snihaH", "snigByAm / sniqByAm", "snigByaH / sniqByaH"],
    "zazWI": ["snihaH", "snihoH", "snihAm"],
    "saptamI": ["snihi", "snihoH", "snikzu / sniwsu"],
    "saMboDana": ["snik / snig / sniw / sniq", "snihO", "snihaH"],
})

# dfS (seeing, m/f/n) - Panini 8.2.36, 8.2.62 (velar g/K/k)
_register("drs_m", "dfS", "m", "S-kArAnta puMliNga (dfS - seeing) - velar (Panini 8.2.36, 8.2.62)", {
    "prathamA": ["dfg / dfK / dfk", "dfSO", "dfSaH"],
    "dvitIyA": ["dfSam", "dfSO", "dfSaH"],
    "tftIyA": ["dfSA", "dfgByAm", "dfgBiH"],
    "caturTI": ["dfSe", "dfgByAm", "dfgByaH"],
    "paYcamI": ["dfSaH", "dfgByAm", "dfgByaH"],
    "zazWI": ["dfSaH", "dfSoH", "dfSAm"],
    "saptamI": ["dfSi", "dfSoH", "dfkzu"],
    "saMboDana": ["dfg / dfK / dfk", "dfSO", "dfSaH"],
})
_register("drs_f", "dfS", "f", "S-kArAnta strIliNga (dfS - eye/sight) - velar (Panini 8.2.36, 8.2.62)", {
    "prathamA": ["dfg / dfK / dfk", "dfSO", "dfSaH"],
    "dvitIyA": ["dfSam", "dfSO", "dfSaH"],
    "tftIyA": ["dfSA", "dfgByAm", "dfgBiH"],
    "caturTI": ["dfSe", "dfgByAm", "dfgByaH"],
    "paYcamI": ["dfSaH", "dfgByAm", "dfgByaH"],
    "zazWI": ["dfSaH", "dfSoH", "dfSAm"],
    "saptamI": ["dfSi", "dfSoH", "dfkzu"],
    "saMboDana": ["dfg / dfK / dfk", "dfSO", "dfSaH"],
})
_register("drs_n", "dfS", "n", "S-kArAnta napuMsaka (dfS) - velar (Panini 8.2.36, 8.2.62)", {
    "prathamA": ["dfg / dfK / dfk", "dfSI", "dfMSi"],
    "dvitIyA": ["dfg / dfK / dfk", "dfSI", "dfMSi"],
    "tftIyA": ["dfSA", "dfgByAm", "dfgBiH"],
    "caturTI": ["dfSe", "dfgByAm", "dfgByaH"],
    "paYcamI": ["dfSaH", "dfgByAm", "dfgByaH"],
    "zazWI": ["dfSaH", "dfSoH", "dfSAm"],
    "saptamI": ["dfSi", "dfSoH", "dfkzu"],
    "saMboDana": ["dfg / dfK / dfk", "dfSI", "dfMSi"],
})

# spfS (touching, m/f) - Panini 8.2.36, 8.2.62 (velar g/K/k)
_register("spfs_m", "spfS", "m", "S-kArAnta puMliNga (spfS - touching) - velar (Panini 8.2.36, 8.2.62)", {
    "prathamA": ["spfg / spfK / spfk", "spfSO", "spfSaH"],
    "dvitIyA": ["spfSam", "spfSO", "spfSaH"],
    "tftIyA": ["spfSA", "spfgByAm", "spfgBiH"],
    "caturTI": ["spfSe", "spfgByAm", "spfgByaH"],
    "paYcamI": ["spfSaH", "spfgByAm", "spfgByaH"],
    "zazWI": ["spfSaH", "spfSoH", "spfSAm"],
    "saptamI": ["spfSi", "spfSoH", "spfkzu"],
    "saMboDana": ["spfg / spfK / spfk", "spfSO", "spfSaH"],
})
_register("spfs_f", "spfS", "f", "S-kArAnta strIliNga (spfS - touching) - velar (Panini 8.2.36, 8.2.62)", {
    "prathamA": ["spfg / spfK / spfk", "spfSO", "spfSaH"],
    "dvitIyA": ["spfSam", "spfSO", "spfSaH"],
    "tftIyA": ["spfSA", "spfgByAm", "spfgBiH"],
    "caturTI": ["spfSe", "spfgByAm", "spfgByaH"],
    "paYcamI": ["spfSaH", "spfgByAm", "spfgByaH"],
    "zazWI": ["spfSaH", "spfSoH", "spfSAm"],
    "saptamI": ["spfSi", "spfSoH", "spfkzu"],
    "saMboDana": ["spfg / spfK / spfk", "spfSO", "spfSaH"],
})

# tiryac / tiraYc (transverse/animal, m/n) - Panini 6.4.113 tiryacas tiryateḥ
_register("tiryac_m", "tiryac", "m", "ac-kArAnta puMliNga (tiryac - animal) - Panini 6.4.113", {
    "prathamA": ["tiryaN", "tiryaYcO", "tiryaYcaH"],
    "dvitIyA": ["tiryaYcam", "tiryaYcO", "tiraScaH"],
    "tftIyA": ["tiraScA", "tiryakByAm / tiryagByAm", "tiryakBiH / tiryagBiH"],
    "caturTI": ["tiraSce", "tiryakByAm / tiryagByAm", "tiryakByaH / tiryagByaH"],
    "paYcamI": ["tiraScaH", "tiryakByAm / tiryagByAm", "tiryakByaH / tiryagByaH"],
    "zazWI": ["tiraScaH", "tiraScoH", "tiraScAm"],
    "saptamI": ["tiraSci", "tiraScoH", "tiryakzu"],
    "saMboDana": ["tiryaN", "tiryaYcO", "tiryaYcaH"],
})
_register("tiryac_n", "tiryac", "n", "ac-kArAnta napuMsakaliNga (tiryac) - Panini 6.4.113", {
    "prathamA": ["tiryak", "tiraScI", "tiryaYci"],
    "dvitIyA": ["tiryak", "tiraScI", "tiryaYci"],
    "tftIyA": ["tiraScA", "tiryakByAm / tiryagByAm", "tiryakBiH / tiryagBiH"],
    "caturTI": ["tiraSce", "tiryakByAm / tiryagByAm", "tiryakByaH / tiryagByaH"],
    "paYcamI": ["tiraScaH", "tiryakByAm / tiryagByAm", "tiryakByaH / tiryagByaH"],
    "zazWI": ["tiraScaH", "tiraScoH", "tiraScAm"],
    "saptamI": ["tiraSci", "tiraScoH", "tiryakzu"],
    "saMboDana": ["tiryak", "tiraScI", "tiryaYci"],
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
        "paYcamI": ["tasmAd / tasmAt", "tAByAm", "teByaH"],
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
        "prathamA": ["tad / tat", "te", "tAni"],
        "dvitIyA": ["tad / tat", "te", "tAni"],
        "tftIyA": ["tena", "tAByAm", "tEH"],
        "caturTI": ["tasmE", "tAByAm", "teByaH"],
        "paYcamI": ["tasmAd / tasmAt", "tAByAm", "teByaH"],
        "zazWI": ["tasya", "tayoH", "tezAm"],
        "saptamI": ["tasmin", "tayoH", "tezu"],
        "saMboDana": ["-", "-", "-"],
    }),
}

# etad – m/f/n
PRONOUNS["etad"] = {
    "m": _pronoun_table({
        "prathamA": ["ezaH", "etO", "ete"],
        "dvitIyA": ["etam / enam", "etO / enO", "etAn / enAn"],
        "tftIyA": ["etena / enena", "etAByAm", "etEH"],
        "caturTI": ["etasmE", "etAByAm", "eteByaH"],
        "paYcamI": ["etasmAd / etasmAt", "etAByAm", "eteByaH"],
        "zazWI": ["etasya", "etayoH / enayoH", "etezAm"],
        "saptamI": ["etasmin", "etayoH / enayoH", "etezu"],
        "saMboDana": ["-", "-", "-"],
    }),
    "f": _pronoun_table({
        "prathamA": ["ezA", "ete", "etAH"],
        "dvitIyA": ["etAm / enAm", "ete / ene", "etAH / enAH"],
        "tftIyA": ["etayA / enayA", "etAByAm", "etABiH"],
        "caturTI": ["etasyE", "etAByAm", "etAByaH"],
        "paYcamI": ["etasyAH", "etAByAm", "etAByaH"],
        "zazWI": ["etasyAH", "etayoH / enayoH", "etAsAm"],
        "saptamI": ["etasyAm", "etayoH / enayoH", "etAsu"],
        "saMboDana": ["-", "-", "-"],
    }),
    "n": _pronoun_table({
        "prathamA": ["etad / etat", "ete", "etAni"],
        "dvitIyA": ["etad / enad / enat / etat", "ete / ene", "etAni / enAni"],
        "tftIyA": ["etena / enena", "etAByAm", "etEH"],
        "caturTI": ["etasmE", "etAByAm", "eteByaH"],
        "paYcamI": ["etasmAd / etasmAt", "etAByAm", "eteByaH"],
        "zazWI": ["etasya", "etayoH / enayoH", "etezAm"],
        "saptamI": ["etasmin", "etayoH / enayoH", "etezu"],
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
        "paYcamI": ["yasmAd / yasmAt", "yAByAm", "yeByaH"],
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
        "prathamA": ["yad / yat", "ye", "yAni"],
        "dvitIyA": ["yad / yat", "ye", "yAni"],
        "tftIyA": ["yena", "yAByAm", "yEH"],
        "caturTI": ["yasmE", "yAByAm", "yeByaH"],
        "paYcamI": ["yasmAd / yasmAt", "yAByAm", "yeByaH"],
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
        "paYcamI": ["tyasmAd / tyasmAt", "tyAByAm", "tyeByaH"],
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
        "prathamA": ["tyad / tyat", "tye", "tyAni"],
        "dvitIyA": ["tyad / tyat", "tye", "tyAni"],
        "tftIyA": ["tyena", "tyAByAm", "tyEH"],
        "caturTI": ["tyasmE", "tyAByAm", "tyeByaH"],
        "paYcamI": ["tyasmAd / tyasmAt", "tyAByAm", "tyeByaH"],
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
        "paYcamI": ["kasmAd / kasmAt", "kAByAm", "keByaH"],
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
        "paYcamI": ["kasmAd / kasmAt", "kAByAm", "keByaH"],
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
        "paYcamI": ["asmAd / asmAt", "AByAm", "eByaH"],
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
        "dvitIyA": ["idam / enad / enat", "ime / ene", "imAni / enAni"],
        "tftIyA": ["anena / enena", "AByAm", "eBiH"],
        "caturTI": ["asmE", "AByAm", "eByaH"],
        "paYcamI": ["asmAd / asmAt", "AByAm", "eByaH"],
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
        "paYcamI": ["amuzmAd / amuzmAt", "amUByAm", "amIByaH"],
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
        "paYcamI": ["amuzmAd / amuzmAt", "amUByAm", "amIByaH"],
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
    "paYcamI": ["asmAd / asmAt", "AByAm", "eByaH"],
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
    "paYcamI": ["asmAd / asmAt", "AByAm", "eByaH"],
    "zazWI": ["asya", "ayoH", "ezAm"],
    "saptamI": ["asmin", "ayoH", "ezu"],
    "saMboDana": ["a", "e", "Ani"],
}

# ḍatara/ḍatama class words take -at/-ad in neuter prathamA/dvitIyA (Panini 7.1.25)
_DATARA_WORDS = {"anya", "anyatara", "itara", "katara", "katama"}

# Pūrvādi directional and optional sarvanāmas (Panini 1.1.32 vibhāṣā jasi, 1.1.34-36 pūrvaparāvara...)
_PURVADI_WORDS = {"pUrva", "para", "avara", "dakziRa", "DakziRa", "uttara", "apara", "aDara", "sva", "antara"}

def _add_pronoun_suf(base: str, suf: str) -> str:
    if " / " in suf:
        return " / ".join(apply_natva(base + p.strip(), len(base)) for p in suf.split("/"))
    return apply_natva(base + suf, len(base))

for _w in ["sarva", "viSva", "uBa", "uBaya", "katara", "katama", "anya", "anyatara", "itara", "para", "apara", "dakziRa", "DakziRa", "pUrva", "avara", "uttara", "aDara", "alpa", "sva", "antara", "sama", "sIma", "nema", "aneka"]:
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

    m_table = dict(_SARVA_PRONOUN_M)
    f_table = dict(_SARVA_PRONOUN_F)
    n_table = dict(_SARVA_PRONOUN_N)

    if _w in _DATARA_WORDS:
        n_table["prathamA"] = ["ad / at", "e", "Ani"]
        n_table["dvitIyA"] = ["ad / at", "e", "Ani"]
        n_table["saMboDana"] = ["ad / at", "e", "Ani"]

    if _w in _PURVADI_WORDS:
        # Panini 1.1.32 vibhāṣā jasi: prathamA bahuvacana e / AH
        m_table["prathamA"] = ["aH", "O", "e / AH"]
        m_table["saMboDana"] = ["a", "O", "e / AH"]
        # Panini 1.1.34 pūrvaparāvara...: pañcamI ekavacana asmAd / asmAt / Ad / At, saptamI asmin / e
        m_table["paYcamI"] = ["asmAd / asmAt / Ad / At", "AByAm", "eByaH"]
        m_table["saptamI"] = ["asmin / e", "ayoH", "ezu"]

        n_table["paYcamI"] = ["asmAd / asmAt / Ad / At", "AByAm", "eByaH"]
        n_table["saptamI"] = ["asmin / e", "ayoH", "ezu"]

        f_table["caturTI"] = ["asyE / AyE", "AByAm", "AByaH"]
        f_table["paYcamI"] = ["asyAH / AyAH", "AByAm", "AByaH"]
        f_table["zazWI"] = ["asyAH / AyAH", "ayoH", "AsAm"]
        f_table["saptamI"] = ["asyAm / AyAm", "ayoH", "Asu"]

    PRONOUNS[_w] = {
        "m": {v: [_add_pronoun_suf(base, s) for s in sufs] for v, sufs in m_table.items()},
        "f": {v: [_add_pronoun_suf(base, s) for s in sufs] for v, sufs in f_table.items()},
        "n": {v: [_add_pronoun_suf(base, s) for s in sufs] for v, sufs in n_table.items()},
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
        "paYcamI": ["ekasmAd / ekasmAt", "-", "-"],
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
        "paYcamI": ["ekasmAd / ekasmAt", "-", "-"],
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
    "prathamA": ["-", "-", "zaq / zaw"],
    "dvitIyA": ["-", "-", "zaq / zaw"],
    "tftIyA": ["-", "-", "zaqBiH"],
    "caturTI": ["-", "-", "zaqByaH"],
    "paYcamI": ["-", "-", "zaqByaH"],
    "zazWI": ["-", "-", "zaRRAm"],
    "saptamI": ["-", "-", "zawsu / zawtsu"],
    "saMboDana": ["-", "-", "zaq / zaw"],
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

# Higher numerals: viMSati etc. are feminine nouns, singular only (viMSatyAdayaH sadaikatve strItvam)
_viMSati_full = {
    "prathamA": ["viMSatiH", "-", "-"],
    "dvitIyA": ["viMSatim", "-", "-"],
    "tftIyA": ["viMSatyA", "-", "-"],
    "caturTI": ["viMSataye", "-", "-"],
    "paYcamI": ["viMSateH", "-", "-"],
    "zazWI": ["viMSateH", "-", "-"],
    "saptamI": ["viMSatO", "-", "-"],
    "saMboDana": ["viMSate", "-", "-"],
}
NUMERALS["viMSati"] = {"f": _viMSati_full}

# triMSat (30) – at-stem f (triMSat), singular only
_triMSat_full = {
    "prathamA": ["triMSat", "-", "-"],
    "dvitIyA": ["triMSatam", "-", "-"],
    "tftIyA": ["triMSatA", "-", "-"],
    "caturTI": ["triMSate", "-", "-"],
    "paYcamI": ["triMSataH", "-", "-"],
    "zazWI": ["triMSataH", "-", "-"],
    "saptamI": ["triMSati", "-", "-"],
    "saMboDana": ["triMSat", "-", "-"],
}
for _h in ["triMSat", "catvAriMSat", "paYcASat"]:
    stem = _h[:-1]
    _tbl = {}
    for _vib, _vals in _triMSat_full.items():
        new_vals = []
        for v in _vals:
            if v == "-":
                new_vals.append("-")
            elif v.startswith("triMSa"):
                new_vals.append(stem + v[6:])
            else:
                new_vals.append(v.replace("triMSat", _h))
        _tbl[_vib] = new_vals
    NUMERALS[_h] = {"f": _tbl}

for _h in ["zazwi", "saptati", "aSIti", "navati"]:
    stem_base = _h[:-1]
    _tbl = {}
    for _vib, _vals in _viMSati_full.items():
        _tbl[_vib] = [v.replace("viMSat", stem_base, 1) if v.startswith("viMSat") else v for v in _vals]
    NUMERALS[_h] = {"f": _tbl}

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
    elif paradigm == "us_n" and word.endswith("uz"):
        base = word[:-2]
    elif paradigm == "is_n" and word.endswith("iz"):
        base = word[:-2]
    elif paradigm == "pad_m":
        if word.endswith("pada"):
            base = word[:-4]
        elif word.endswith("pad") or word.endswith("pat"):
            base = word[:-3]
        else:
            base = ""
    elif paradigm == "d_f" and word.endswith("pat"):
        base = word[:-1]
    elif paradigm in ("div_f", "div_m") and word.endswith("dyu"):
        base = word[:-3]
    elif paradigm in ("tiryac_m", "tiryac_n"):
        if word.endswith("tiryac"):
            base = word[:-6]
        elif word.endswith("tiraYc"):
            base = word[:-6]
        else:
            base = word
    elif paradigm == "pranc_m" and word.endswith("prAc"):
        base = word[:-4]
    elif paradigm == "pratyanc_m" and word.endswith("pratIc"):
        base = word[:-6]
    elif paradigm == "udanc_m" and word.endswith("udIc"):
        base = word[:-4]
    elif paradigm == "anaquh_m" and word.endswith("anaqvat"):
        base = word[:-7]
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
                    parts = [apply_natva(base + p.strip(), len(base)) for p in suf.split("/")]
                    forms.append(" / ".join(parts))
                else:
                    forms.append(apply_natva(base + suf, len(base)))
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
    if word in PRONOUNS:
        cands = [f"pronoun:{word}"]
        if word.endswith("a"):
            if gender == "m":
                cands.append("a_m")
            elif gender == "n":
                cands.append("a_n")
        elif word.endswith("A") and gender == "f":
            cands.append("A_f")
        elif word.endswith("d"):
            if gender == "m":
                cands.append("d_m")
            elif gender == "n":
                cands.append("d_n")
        return cands
    if word in NUMERALS:
        cands = [f"numeral:{word}"]
        if word.endswith("i") and gender == "f":
            cands.append("i_f")
        elif word.endswith("t") and gender == "f":
            cands.append("t_f")
        return cands

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

    # ambArtha strIliNga (ambA / akkA / allA / ammA)
    if word in ("akkA", "allA", "ammA", "ambA"):
        return ["amba_f", "A_f"]

    # o-stem go (bull / cow)
    if word == "go" or word.endswith("go"):
        if gender == "f":
            return ["o_f"]
        elif gender == "m":
            return ["o_m"]
        else:
            return ["o_m", "o_f"]

    # root vowels SrI, BU, strI, lakzmI, suDI, senAnI, viSvapA
    if word == "DI":
        return ["sudhi_m"] if gender == "m" else ["sri_f"]
    if word in ("SrI", "hrI") or word.endswith("SrI"):
        return ["sri_f"]
    if word in ("suDI", "praDI") or (word.endswith("DI") and word not in ("DI", "hrI", "SrI")):
        return ["sudhi_m", "I_m"] if gender in (None, "m") else ["sudhi_m", "I_f"]
    if word in ("senAnI", "grAmaRI") or ((word.endswith("nI") or word.endswith("RI")) and gender == "m"):
        return ["I_m", "sudhi_m"]
    if word in ("viSvapA", "somapA", "DUpapA", "balapA") or (word.endswith("pA") and gender == "m"):
        return ["A_m"]
    if word in ("BU", "BrU") or word.endswith("BU"):
        return ["bhu_m"] if gender == "m" else (["bhu_f"] if gender == "f" else ["bhu_m", "bhu_f"])
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

    # special irregulars: anaquh, div/dyu, gir/pur/dvAr, krozwu, candramas, yuj, Buj, kzuD/samiD, vftrahan/han/maGavan
    if word in ("anaquh", "anaqvat") or word.endswith("anaquh"):
        return ["anaquh_m"]
    if word in ("div", "dyu") or word.endswith("div") or word.endswith("dyu"):
        return ["div_f", "div_m"] if gender is None else (["div_f"] if gender == "f" else ["div_m"])
    if word == "gir" or word.endswith("gir"):
        return ["gir_f", "r_f"]
    if word == "pur" or word.endswith("pur"):
        return ["pur_f", "r_f"]
    if word == "dvAr" or word.endswith("dvAr") or (word.endswith("r") and gender == "f"):
        return ["r_f"]
    if word in ("prAYc", "prAc") or word.endswith("prAYc") or word.endswith("prAc"):
        return ["pranc_m"]
    if word in ("pratyaYc", "pratIc") or word.endswith("pratyaYc") or word.endswith("pratIc"):
        return ["pratyanc_m"]
    if word in ("udaYc", "udIc") or word.endswith("udaYc") or word.endswith("udIc"):
        return ["udanc_m"]
    if word == "krozwu" or word.endswith("krozwu"):
        if gender == "n":
            return ["u_n"]
        elif gender == "f":
            return ["u_f"]
        return ["krozwu_m", "u_m"]
    if word == "candramas" or word.endswith("candramas"):
        return ["candramas_m", "as_m"]
    if word == "yuj":
        return ["yuj_m", "j_m"]
    if word == "Buj" or word.endswith("Buj"):
        return ["Buj_f"] if gender == "f" else ["Buj_m"] if gender == "m" else ["Buj_m", "Buj_f"]
    if word == "kzuD" or word.endswith("kzuD"):
        return ["kzuD_f", "dh_f"]
    if (word.endswith("D") or word.endswith("dh")) and gender == "f":
        return ["dh_f"]
    if word == "vftrahan" or word.endswith("vftrahan"):
        return ["vftrahan_m", "han_m"]
    if word.endswith("han") and word != "plIhan" and (gender is None or gender == "m"):
        return ["han_m"]
    if word == "maGavan" or word.endswith("maGavan"):
        return ["maghavan_m"]

    # other irregulars: ahan, pums, Svan, yuvan, ap, diS
    if word == "ahan" or word.endswith("ahan"):
        return ["ahan_n"]
    if word in ("pums", "pumAMs") or word.endswith("pums"):
        return ["pums_m"]
    if word == "Svan" or (word.endswith("Svan") and word != "mAtariSvan"):
        return ["svan_m"]
    if word == "yuvan" or word.endswith("yuvan"):
        return ["yuvan_m"]
    if word == "ap":
        return ["ap_f"]
    # nf (man) - Panini 6.4.11-12
    if word == "nf" or word.endswith("nf"):
        if gender is None or gender == "m":
            return ["nr_m"]

    # pad / pat / pada (foot)
    if word in ("pad", "pat") or word.endswith("pad") or word.endswith("pat"):
        if word in ("sampad", "vipad", "Apad"):
            return ["d_f"]
        if gender == "f":
            return ["d_f"]
        elif gender == "m":
            return ["pad_m"]
        else:
            return ["pad_m", "d_f"]
    if word == "pada" or (word.endswith("pada") and gender == "m"):
        if gender == "m":
            return ["pad_m", "a_m"]
        elif gender == "n":
            return ["a_n"]
        else:
            return ["a_n", "pad_m"]

    # root consonant nouns in -h
    if word == "duh" or word.endswith("duh"):
        return ["duh_m"] if gender == "m" else ["duh_f"] if gender == "f" else ["duh_m", "duh_f"]
    if word == "lih" or word.endswith("lih"):
        return ["lih_m"] if gender == "m" else ["lih_f"] if gender == "f" else ["lih_m", "lih_f"]
    if word == "druh" or word.endswith("druh"):
        return ["druh_m"] if gender == "m" else ["druh_f"] if gender == "f" else ["druh_m", "druh_f"]
    if word == "muh" or word.endswith("muh"):
        return ["muh_m"] if gender == "m" else ["muh_f"] if gender == "f" else ["muh_m", "muh_f"]
    if word == "snih" or word.endswith("snih"):
        return ["snih_m"] if gender == "m" else ["snih_f"] if gender == "f" else ["snih_m", "snih_f"]

    # dfS, spfS, diS, viS, anvac
    if word == "anvac" or word.endswith("anvac"):
        return ["anvac_m"]
    if word == "dfS" or word.endswith("dfS"):
        return ["drs_m"] if gender == "m" else (["drs_f"] if gender == "f" else (["drs_n"] if gender == "n" else ["drs_m", "drs_f", "drs_n"]))
    if word == "spfS" or word.endswith("spfS"):
        return ["spfs_m"] if gender == "m" else (["spfs_f"] if gender == "f" else ["spfs_m", "spfs_f"])
    if word == "diS" or word.endswith("diS"):
        return ["dis_f"] if gender != "m" else ["dis_m"]
    if word == "viS" or word.endswith("viS"):
        return ["dis_m"] if gender == "m" else ["dis_f"]

    # tiryac / tiraYc
    if word in ("tiryac", "tiraYc") or word.endswith("tiryac") or word.endswith("tiraYc"):
        if gender == "n":
            return ["tiryac_n"]
        elif gender == "m":
            return ["tiryac_m"]
        else:
            return ["tiryac_m", "tiryac_n"]

    # praTama, carama, katipaya, dvitaya, tritaya (Panini 1.1.33)
    if word in ("praTama", "carama", "katipaya", "dvitaya", "tritaya"):
        if gender == "m":
            return ["a_m"]
        elif gender == "f":
            return ["A_f"]
        elif gender == "n":
            return ["a_n"]
        else:
            return ["a_m", "A_f", "a_n"]

    if word in ("sampad", "vipad", "Apad"):
        return ["d_f"]
    if word in ("Bizaj", "ftvij"):
        return ["j_m"]

    # vidvas (scholar) & vas participles (kvasu) vs Sravas (fame / ears)
    if word in ("vidvas", "vidvAn") or word.endswith("vidvas"):
        return ["vidvas_m", "vas_m"]
    if word.endswith("Sravas"):
        if gender == "n":
            return ["as_n"]
        return ["as_m", "candramas_m"]
    if word.endswith("vas") and (gender is None or gender == "m"):
        return ["vas_m", "as_m"]

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

    # an-stem neuter karman (conjunct) vs nAman (simple) vs masculine rAjan vs Atman vs mUrDan/aRiman
    if word.endswith("an"):
        p = word[:-2]
        # Pāṇini 6.4.134 allopo'naḥ vs 6.4.135 na saṁyogād vamantāt
        last = p[-1] if p else ""
        if last in ('c', 'j'):
            w = "y"
        elif last in ('w', 'D', 'z'):
            w = "drop"
        elif len(p) >= 2 and p[-2] in "aAiIuUfFxXeEoO":
            w = "drop"
        else:
            w = "keep"

        if gender == "m":
            if word == "rAjan" or word.endswith("rAjan") or w == "y":
                return ["rajan_m", "an_drop_m", "an_m"]
            elif w == "drop":
                return ["an_drop_m", "an_m"]
            else:
                return ["an_m", "an_drop_m"]
        elif gender in (None, "n"):
            if w == "drop":
                return ["an_n", "karman_n"]
            else:
                return ["karman_n", "an_n"]

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

    if (word.endswith("us") or word.endswith("uz")) and gender in (None, "n"):
        return ["us_n"]
    if (word.endswith("is") or word.endswith("iz")) and gender in (None, "n"):
        return ["is_n"]

    # check endings longest first
    for paradigm, meta in sorted(PARADIGMS.items(), key=lambda x: -len(x[1]["ending"])):
        ending = meta["ending"]
        g = meta["gender"]
        if gender and g != gender:
            continue
        if paradigm == "rajan_m" and not (word == "rAjan" or word.endswith("rAjan")):
            continue
        if paradigm == "amba_f" and word not in ("akkA", "allA", "ammA", "ambA"):
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

# Paddan-adi optional consonant stem substitutions (Panini 6.1.63)
_PADDAN_MAP = {
    "danta": {
        ("dvitIyA", 2): "dataH",
        ("tftIyA", 0): "datA",
        ("tftIyA", 1): "dadByAm",
        ("tftIyA", 2): "dadBiH",
        ("caturTI", 0): "date",
        ("caturTI", 1): "dadByAm",
        ("caturTI", 2): "dadByaH",
        ("paYcamI", 0): "dataH",
        ("paYcamI", 1): "dadByAm",
        ("paYcamI", 2): "dadByaH",
        ("zazWI", 0): "dataH",
        ("zazWI", 1): "datoH",
        ("zazWI", 2): "datAm",
        ("saptamI", 0): "dati",
        ("saptamI", 1): "datoH",
        ("saptamI", 2): "datsu",
    },
    "mAsa": {
        ("dvitIyA", 2): "mAsaH",
        ("tftIyA", 0): "mAsA",
        ("tftIyA", 1): "mAsoByAm",
        ("tftIyA", 2): "mAsoBiH",
        ("caturTI", 0): "mAse",
        ("caturTI", 1): "mAsoByAm",
        ("caturTI", 2): "mAseByaH",
        ("paYcamI", 0): "mAsaH",
        ("paYcamI", 1): "mAsoByAm",
        ("paYcamI", 2): "mAseByaH",
        ("zazWI", 0): "mAsaH",
        ("zazWI", 1): "mAsoH",
        ("zazWI", 2): "mAsAm",
        ("saptamI", 0): "mAsi",
        ("saptamI", 1): "mAsoH",
        ("saptamI", 2): "mAssu / mAHsu",
    },
    "hfdaya": {
        ("dvitIyA", 2): "hfdaH",
        ("tftIyA", 0): "hfdA",
        ("tftIyA", 1): "hfdByAm",
        ("tftIyA", 2): "hfdBiH",
        ("caturTI", 0): "hfde",
        ("caturTI", 1): "hfdByAm",
        ("caturTI", 2): "hfdByaH",
        ("paYcamI", 0): "hfdaH",
        ("paYcamI", 1): "hfdByAm",
        ("paYcamI", 2): "hfdByaH",
        ("zazWI", 0): "hfdaH",
        ("zazWI", 1): "hfdoH",
        ("zazWI", 2): "hfdAm",
        ("saptamI", 0): "hfdi",
        ("saptamI", 1): "hfdoH",
        ("saptamI", 2): "hftsu",
    },
    "pAda": {
        ("dvitIyA", 2): "padaH",
        ("tftIyA", 0): "padA",
        ("tftIyA", 1): "padByAm",
        ("tftIyA", 2): "padBiH",
        ("caturTI", 0): "pade",
        ("caturTI", 1): "padByAm",
        ("caturTI", 2): "padByaH",
        ("paYcamI", 0): "padaH",
        ("paYcamI", 1): "padByAm",
        ("paYcamI", 2): "padByaH",
        ("zazWI", 0): "padaH",
        ("zazWI", 1): "padoH",
        ("zazWI", 2): "padAm",
        ("saptamI", 0): "padi",
        ("saptamI", 1): "padoH",
        ("saptamI", 2): "patsu",
    },
    "niSA": {
        ("dvitIyA", 2): "niSaH",
        ("tftIyA", 0): "niSA",
        ("tftIyA", 1): "nigByAm",
        ("tftIyA", 2): "nigBiH",
        ("caturTI", 0): "niSe",
        ("caturTI", 1): "nigByAm",
        ("caturTI", 2): "nigByaH",
        ("paYcamI", 0): "niSaH",
        ("paYcamI", 1): "nigByAm",
        ("paYcamI", 2): "nigByaH",
        ("zazWI", 0): "niSaH",
        ("zazWI", 1): "niSoH",
        ("zazWI", 2): "niSAm",
        ("saptamI", 0): "niSi",
        ("saptamI", 1): "niSoH",
        ("saptamI", 2): "nikzu",
    },
    "udaka": {
        ("tftIyA", 0): "udnA",
        ("tftIyA", 1): "udaByAm",
        ("tftIyA", 2): "udaBiH",
        ("caturTI", 0): "udne",
        ("caturTI", 1): "udaByAm",
        ("caturTI", 2): "udaByaH",
        ("paYcamI", 0): "udnaH",
        ("paYcamI", 1): "udaByAm",
        ("paYcamI", 2): "udaByaH",
        ("zazWI", 0): "udnaH",
        ("zazWI", 1): "udnoH",
        ("zazWI", 2): "udnAm",
        ("saptamI", 0): "udani / udni",
        ("saptamI", 1): "udnoH",
        ("saptamI", 2): "udasu",
    },
}

_PADDAN_REVERSE: dict[str, list[tuple[str, str, str, str, str]]] = {
    # dat -> danta (m)
    "dataH": [("danta", "a_m", "m", "dvitIyA", "bahuvacana"), ("danta", "a_m", "m", "paYcamI", "ekavacana"), ("danta", "a_m", "m", "zazWI", "ekavacana")],
    "datA": [("danta", "a_m", "m", "tftIyA", "ekavacana")],
    "dadByAm": [("danta", "a_m", "m", "tftIyA", "dvivacana"), ("danta", "a_m", "m", "caturTI", "dvivacana"), ("danta", "a_m", "m", "paYcamI", "dvivacana")],
    "dadBiH": [("danta", "a_m", "m", "tftIyA", "bahuvacana")],
    "date": [("danta", "a_m", "m", "caturTI", "ekavacana")],
    "dadByaH": [("danta", "a_m", "m", "caturTI", "bahuvacana"), ("danta", "a_m", "m", "paYcamI", "bahuvacana")],
    "datoH": [("danta", "a_m", "m", "zazWI", "dvivacana"), ("danta", "a_m", "m", "saptamI", "dvivacana")],
    "datAm": [("danta", "a_m", "m", "zazWI", "bahuvacana")],
    "dati": [("danta", "a_m", "m", "saptamI", "ekavacana")],
    "datsu": [("danta", "a_m", "m", "saptamI", "bahuvacana")],

    # hfd -> hfdaya (n)
    "hfdaH": [("hfdaya", "a_n", "n", "dvitIyA", "bahuvacana"), ("hfdaya", "a_n", "n", "paYcamI", "ekavacana"), ("hfdaya", "a_n", "n", "zazWI", "ekavacana")],
    "hfdA": [("hfdaya", "a_n", "n", "tftIyA", "ekavacana")],
    "hfdByAm": [("hfdaya", "a_n", "n", "tftIyA", "dvivacana"), ("hfdaya", "a_n", "n", "caturTI", "dvivacana"), ("hfdaya", "a_n", "n", "paYcamI", "dvivacana")],
    "hfdBiH": [("hfdaya", "a_n", "n", "tftIyA", "bahuvacana")],
    "hfde": [("hfdaya", "a_n", "n", "caturTI", "ekavacana")],
    "hfdByaH": [("hfdaya", "a_n", "n", "caturTI", "bahuvacana"), ("hfdaya", "a_n", "n", "paYcamI", "bahuvacana")],
    "hfdoH": [("hfdaya", "a_n", "n", "zazWI", "dvivacana"), ("hfdaya", "a_n", "n", "saptamI", "dvivacana")],
    "hfdAm": [("hfdaya", "a_n", "n", "zazWI", "bahuvacana")],
    "hfdi": [("hfdaya", "a_n", "n", "saptamI", "ekavacana")],
    "hftsu": [("hfdaya", "a_n", "n", "saptamI", "bahuvacana")],

    # mAs -> mAsa (m)
    "mAsA": [("mAsa", "a_m", "m", "tftIyA", "ekavacana")],
    "mAsoByAm": [("mAsa", "a_m", "m", "tftIyA", "dvivacana"), ("mAsa", "a_m", "m", "caturTI", "dvivacana"), ("mAsa", "a_m", "m", "paYcamI", "dvivacana")],
    "mAsoBiH": [("mAsa", "a_m", "m", "tftIyA", "bahuvacana")],
    "mAseByaH": [("mAsa", "a_m", "m", "caturTI", "bahuvacana"), ("mAsa", "a_m", "m", "paYcamI", "bahuvacana")],
    "mAsAm": [("mAsa", "a_m", "m", "zazWI", "bahuvacana")],
    "mAsi": [("mAsa", "a_m", "m", "saptamI", "ekavacana")],
    "mAssu": [("mAsa", "a_m", "m", "saptamI", "bahuvacana")],
    "mAHsu": [("mAsa", "a_m", "m", "saptamI", "bahuvacana")],

    # niS -> niSA (f)
    "niSaH": [("niSA", "A_f", "f", "dvitIyA", "bahuvacana"), ("niSA", "A_f", "f", "paYcamI", "ekavacana"), ("niSA", "A_f", "f", "zazWI", "ekavacana")],
    "nigByAm": [("niSA", "A_f", "f", "tftIyA", "dvivacana"), ("niSA", "A_f", "f", "caturTI", "dvivacana"), ("niSA", "A_f", "f", "paYcamI", "dvivacana")],
    "nigBiH": [("niSA", "A_f", "f", "tftIyA", "bahuvacana")],
    "niSe": [("niSA", "A_f", "f", "caturTI", "ekavacana")],
    "nigByaH": [("niSA", "A_f", "f", "caturTI", "bahuvacana"), ("niSA", "A_f", "f", "paYcamI", "bahuvacana")],
    "niSoH": [("niSA", "A_f", "f", "zazWI", "dvivacana"), ("niSA", "A_f", "f", "saptamI", "dvivacana")],
    "niSAm": [("niSA", "A_f", "f", "zazWI", "bahuvacana")],
    "niSi": [("niSA", "A_f", "f", "saptamI", "ekavacana")],
    "nikzu": [("niSA", "A_f", "f", "saptamI", "bahuvacana")],

    # udan -> udaka (n)
    "udnA": [("udaka", "a_n", "n", "tftIyA", "ekavacana")],
    "udaByAm": [("udaka", "a_n", "n", "tftIyA", "dvivacana"), ("udaka", "a_n", "n", "caturTI", "dvivacana"), ("udaka", "a_n", "n", "paYcamI", "dvivacana")],
    "udaBiH": [("udaka", "a_n", "n", "tftIyA", "bahuvacana")],
    "udne": [("udaka", "a_n", "n", "caturTI", "ekavacana")],
    "udaByaH": [("udaka", "a_n", "n", "caturTI", "bahuvacana"), ("udaka", "a_n", "n", "paYcamI", "bahuvacana")],
    "udnaH": [("udaka", "a_n", "n", "paYcamI", "ekavacana"), ("udaka", "a_n", "n", "zazWI", "ekavacana")],
    "udnoH": [("udaka", "a_n", "n", "zazWI", "dvivacana"), ("udaka", "a_n", "n", "saptamI", "dvivacana")],
    "udnAm": [("udaka", "a_n", "n", "zazWI", "bahuvacana")],
    "udani": [("udaka", "a_n", "n", "saptamI", "ekavacana")],
    "udni": [("udaka", "a_n", "n", "saptamI", "ekavacana")],
    "udasu": [("udaka", "a_n", "n", "saptamI", "bahuvacana")],
}

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

    # Paddan-adi optional forms (Panini 6.1.63)
    if word in _PADDAN_MAP:
        for (v, idx), alt_form in _PADDAN_MAP[word].items():
            if v in table and idx < len(table[v]):
                orig = table[v][idx]
                if alt_form not in orig:
                    table[v][idx] = f"{orig} / {alt_form}"

    # Panini 1.1.33 optional plural -e for praTama, carama, katipaya, dvitaya, tritaya
    if word in ("praTama", "carama", "katipaya", "dvitaya", "tritaya") and gender_out == "m":
        base_w = word[:-1]
        if "prathamA" in table and len(table["prathamA"]) > 2:
            table["prathamA"][2] = f"{base_w}AH / {base_w}e"
        if "saMboDana" in table and len(table["saMboDana"]) > 2:
            table["saMboDana"][2] = f"{base_w}AH / {base_w}e"

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
    if result.get("is_collection"):
        return "\n\n".join(to_table(p_res) for p_res in result.get("participles", {}).values())
    if result.get("is_avyaya"):
        d = result.get("dhatu", "")
        p = result.get("pratyaya", "")
        form = result.get("form", "")
        return f"# {d} + {p} [avyaya] (indeclinable)\nform: {form}"
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

def to_markdown(result: dict[str, Any]) -> str:
    """Format declension result as a GitHub Flavored Markdown table."""
    if result.get("is_collection"):
        return "\n\n---\n\n".join(to_markdown(p_res) for p_res in result.get("participles", {}).values())
    if result.get("is_avyaya"):
        d = result.get("dhatu", "")
        p = result.get("pratyaya", "")
        form = result.get("form", "")
        return f"# {d} + {p} [avyaya] (indeclinable)\n\n**Form:** `{form}`"
    lines = []
    title = f"# {result.get('word', '')}"
    meta = []
    if result.get("type"):
        meta.append(f"type: {result['type']}")
    if result.get("paradigm"):
        meta.append(f"paradigm: {result['paradigm']}")
    if result.get("desc"):
        meta.append(result["desc"])
    if meta:
        lines.append(f"{title} ({', '.join(meta)})\n")
    else:
        lines.append(f"{title}\n")

    if "forms" in result:
        lines.append("| vibhakti | ekavacana | dvivacana | bahuvacana |")
        lines.append("| --- | --- | --- | --- |")
        for vib in VIBHAKTIS:
            if vib not in result["forms"]:
                continue
            e, d, b = result["forms"][vib]
            lines.append(f"| {vib} | {e} | {d} | {b} |")
    elif "genders" in result:
        for g, tbl in result["genders"].items():
            lines.append(f"\n### gender: {g}\n")
            lines.append("| vibhakti | ekavacana | dvivacana | bahuvacana |")
            lines.append("| --- | --- | --- | --- |")
            for vib in VIBHAKTIS:
                if vib not in tbl:
                    continue
                e, d, b = tbl[vib]
                lines.append(f"| {vib} | {e} | {d} | {b} |")
    return "\n".join(lines)

def to_html(result: dict[str, Any]) -> str:
    """Format declension result as semantic HTML."""
    import html
    if result.get("is_avyaya"):
        d = html.escape(str(result.get("dhatu", "")))
        p = html.escape(str(result.get("pratyaya", "")))
        form = html.escape(str(result.get("form", "")))
        return f'<div class="subanta-declension">\n  <h3>{d} + {p} [avyaya] (indeclinable)</h3>\n  <p><strong>Form:</strong> {form}</p>\n</div>'

    word = html.escape(str(result.get("word", "")))
    lines = ['<div class="subanta-declension">']
    title_parts = [f"<h3>{word}"]
    if result.get("gender"):
        title_parts.append(f" (gender={html.escape(str(result['gender']))}")
        if result.get("paradigm"):
            title_parts.append(f", paradigm={html.escape(str(result['paradigm']))}")
        title_parts.append(")")
    title_parts.append("</h3>")
    lines.append("  " + "".join(title_parts))

    def _render_table(forms_map: dict[str, list[str]], indent: str = "  ") -> list[str]:
        t = [
            f'{indent}<table class="subanta-table">',
            f'{indent}  <thead>',
            f'{indent}    <tr><th>vibhakti</th><th>ekavacana</th><th>dvivacana</th><th>bahuvacana</th></tr>',
            f'{indent}  </thead>',
            f'{indent}  <tbody>',
        ]
        for vib in VIBHAKTIS:
            if vib not in forms_map:
                continue
            e, d, b = forms_map[vib]
            t.append(f'{indent}    <tr><td>{html.escape(vib)}</td><td>{html.escape(e)}</td><td>{html.escape(d)}</td><td>{html.escape(b)}</td></tr>')
        t.append(f'{indent}  </tbody>')
        t.append(f'{indent}</table>')
        return t

    if "forms" in result:
        lines.extend(_render_table(result["forms"]))
    elif "genders" in result:
        for g, tbl in result["genders"].items():
            lines.append(f'  <h4>gender: {html.escape(g)}</h4>')
            lines.extend(_render_table(tbl))
    lines.append('</div>')
    return "\n".join(lines)

def to_csv(result: dict[str, Any]) -> str:
    """Format declension result as CSV."""
    import csv
    import io
    output = io.StringIO()
    writer = csv.writer(output)
    if result.get("is_avyaya"):
        writer.writerow(["type", "dhatu", "pratyaya", "form"])
        writer.writerow(["avyaya", result.get("dhatu", ""), result.get("pratyaya", ""), result.get("form", "")])
        return output.getvalue().rstrip()

    if "forms" in result:
        writer.writerow(["vibhakti", "ekavacana", "dvivacana", "bahuvacana"])
        for vib in VIBHAKTIS:
            if vib not in result["forms"]:
                continue
            e, d, b = result["forms"][vib]
            writer.writerow([vib, e, d, b])
    elif "genders" in result:
        writer.writerow(["gender", "vibhakti", "ekavacana", "dvivacana", "bahuvacana"])
        for g, tbl in result["genders"].items():
            for vib in VIBHAKTIS:
                if vib not in tbl:
                    continue
                e, d, b = tbl[vib]
                writer.writerow([g, vib, e, d, b])
    return output.getvalue().rstrip()

def to_latex(result: dict[str, Any]) -> str:
    """Format declension result as LaTeX tabular."""
    if result.get("is_avyaya"):
        d = result.get("dhatu", "")
        p = result.get("pratyaya", "")
        form = result.get("form", "")
        return f"% {d} + {p} [avyaya]\n\\textbf{{{d} + {p}}} (avyaya): \\texttt{{{form}}}"

    lines = []
    word = result.get("word", "")
    lines.append(f"% {word} [{result.get('type','')}] {result.get('paradigm','')}")

    def _render_tabular(tbl: dict[str, list[str]]) -> list[str]:
        t = [
            "\\begin{tabular}{|l|l|l|l|}",
            "\\hline",
            "\\textbf{vibhakti} & \\textbf{ekavacana} & \\textbf{dvivacana} & \\textbf{bahuvacana} \\\\",
            "\\hline",
        ]
        for vib in VIBHAKTIS:
            if vib not in tbl:
                continue
            e, d, b = tbl[vib]
            t.append(f"{vib} & {e} & {d} & {b} \\\\")
        t.append("\\hline")
        t.append("\\end{tabular}")
        return t

    if "forms" in result:
        lines.extend(_render_tabular(result["forms"]))
    elif "genders" in result:
        for g, tbl in result["genders"].items():
            lines.append(f"\n% gender: {g}")
            lines.append(f"\\subsubsection*{{Gender: {g}}}")
            lines.extend(_render_tabular(tbl))
    return "\n".join(lines)

def to_anki(result: dict[str, Any]) -> str:
    """Export to TSV suitable for Anki flashcard import (Front <TAB> Back <TAB> Tag)."""
    if result.get("is_avyaya"):
        d = result.get("dhatu", "")
        p = result.get("pratyaya", "")
        form = result.get("form", "")
        return f"{d} + {p} [avyaya]\t{form}\tavyaya"

    word = result.get("word", "")
    paradigm = result.get("paradigm", "") or result.get("type", "nominal")
    tag = f"subanta:{paradigm}" if not result.get("pratyaya") else f"krdanta:{result.get('pratyaya')}"

    cards = []
    if "forms" in result:
        gender = result.get("gender", "")
        gender_tag = f" [{gender}]" if gender else ""
        for vib in VIBHAKTIS:
            if vib not in result["forms"]:
                continue
            row = result["forms"][vib]
            for idx, vac in enumerate(VACANAS):
                val = row[idx].strip()
                if not val or val == "-":
                    continue
                front = f"{word}{gender_tag} - {vib} {vac}"
                cards.append(f"{front}\t{val}\t{tag}")
    elif "genders" in result:
        for g, tbl in result["genders"].items():
            for vib in VIBHAKTIS:
                if vib not in tbl:
                    continue
                row = tbl[vib]
                for idx, vac in enumerate(VACANAS):
                    val = row[idx].strip()
                    if not val or val == "-":
                        continue
                    front = f"{word} [{g}] - {vib} {vac}"
                    cards.append(f"{front}\t{val}\t{tag}")
    return "\n".join(cards)

def format_declension(result: dict[str, Any], fmt: str = "table") -> str:
    """Format declension result according to specified format."""
    import json
    fmt = fmt.lower().strip()
    if fmt in ("table", "ascii", "text", "txt"):
        return to_table(result)
    elif fmt in ("markdown", "md"):
        return to_markdown(result)
    elif fmt == "html":
        return to_html(result)
    elif fmt == "csv":
        return to_csv(result)
    elif fmt in ("latex", "tex"):
        return to_latex(result)
    elif fmt in ("anki", "tsv", "flashcards"):
        return to_anki(result)
    elif fmt == "json":
        return json.dumps(result, ensure_ascii=False, indent=2)
    else:
        raise ValueError(f"Unknown format '{fmt}'. Choose from: table, markdown, html, csv, latex, anki, json")

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
    "anaquh_m", "div_f", "div_m", "krozwu_m", "candramas_m", "yuj_m", "Buj_m", "Buj_f",
    "kzuD_f", "vftrahan_m", "maghavan_m", "pranc_m", "pratyanc_m", "udanc_m", "gir_f", "pur_f",
    "nr_m", "pad_m", "duh_m", "duh_f", "lih_m", "lih_f", "druh_m", "druh_f",
    "muh_m", "muh_f", "snih_m", "snih_f", "drs_m", "drs_f", "spfs_m", "spfs_f",
    "tiryac_m", "tiryac_n",
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

    # --- Paddan-adi reverse forms (Panini 6.1.63) ---
    if word in _PADDAN_REVERSE:
        for lemma, para, g, vib, vac in _PADDAN_REVERSE[word]:
            hits.append({
                "type": "noun",
                "match_type": "noun_declension_paddan",
                "lemma": lemma,
                "word": word,
                "matched_form": word,
                "paradigm": para,
                "paradigm_desc": f"paddan-Adi alternative form of {lemma}",
                "ending": "",
                "gender": g,
                "vibhakti": vib,
                "vacana": vac,
                "suffix": "",
                "base": lemma,
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

def _find_participles_for_lemmas(lemmas: list[str], db_path=None) -> dict[str, list[dict[str, Any]]]:
    """Look up participle records matching candidate bases or feminine stems."""
    if not lemmas:
        return {}
    try:
        from .db import connect
        con = connect(db_path)
    except Exception:
        return {}

    base_map: dict[str, list[str]] = {}
    all_cands: set[str] = set()
    for l in lemmas:
        cands = [l]
        if l.endswith("I"):
            cands.append(l[:-1])
            if l.endswith("trI"):
                cands.append(l[:-3] + "tf")
        elif l.endswith("A"):
            cands.append(l[:-1] + "a")
        base_map[l] = cands
        all_cands.update(cands)

    if not all_cands:
        return {}

    cands_list = list(all_cands)
    placeholders = ",".join("?" for _ in cands_list)
    q = f"""
    SELECT pf.dhatu_id, pf.prefix, pf.category, pf.variant as pratyaya, pf.base, pf.f,
           di_dhatu.value as dhatu, di_artha.value as arTaH, di_eng.value as english
    FROM participle_forms pf
    LEFT JOIN dhatu_info di_dhatu ON di_dhatu.dhatu_id = pf.dhatu_id AND di_dhatu.name = 'OpadeSikasvarUpam'
    LEFT JOIN dhatu_info di_artha ON di_artha.dhatu_id = pf.dhatu_id AND di_artha.name = 'arTaH'
    LEFT JOIN dhatu_info di_eng   ON di_eng.dhatu_id   = pf.dhatu_id AND di_eng.name   = 'English Meaning'
    WHERE pf.base IN ({placeholders}) OR pf.f IN ({placeholders})
    """
    try:
        cur = con.execute(q, cands_list + cands_list)
        rows = cur.fetchall()
    except Exception:
        return {}

    results_by_cand: dict[str, list[dict[str, Any]]] = {}
    for r in rows:
        item = {
            "dhatu_id": r["dhatu_id"],
            "prefix": r["prefix"] or "",
            "category": r["category"],
            "pratyaya": r["pratyaya"],
            "base": r["base"],
            "f": r["f"] or "",
            "dhatu": r["dhatu"] or "",
            "artha": r["arTaH"] or "",
            "english": r["english"] or "",
        }
        b = r["base"]
        results_by_cand.setdefault(b, []).append(item)
        if r["f"]:
            results_by_cand.setdefault(r["f"], []).append(item)
            if "/" in r["f"]:
                for part in r["f"].split("/"):
                    results_by_cand.setdefault(part.strip(), []).append(item)

    lemma_to_parts: dict[str, list[dict[str, Any]]] = {}
    for l in lemmas:
        seen = set()
        matched = []
        for c in base_map.get(l, []):
            for item in results_by_cand.get(c, []):
                key = (item["dhatu_id"], item["prefix"], item["category"], item["pratyaya"])
                if key not in seen:
                    seen.add(key)
                    matched.append(item)
        if matched:
            lemma_to_parts[l] = matched
    return lemma_to_parts

def analyze(word: str, limit: int = 20, loose: bool = True, db_path=None, include_verb: bool = True) -> list[dict[str, Any]]:
    """Unified analyzer: verb conjugations + nominal declensions + participle linking."""
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
            nom = analyze_form(word, limit=max(limit * 3, 60), loose=loose)
            part_map = _find_participles_for_lemmas(list({h["lemma"] for h in nom}), db_path=db_path) if include_verb else {}

            participle_hits: list[dict[str, Any]] = []
            noun_hits: list[dict[str, Any]] = []

            for h in nom:
                l = h["lemma"]
                if l in part_map:
                    for p in part_map[l]:
                        ph = dict(h)
                        ph["type"] = "participle"
                        ph["match_type"] = "participle_declension"
                        ph["dhatu"] = p["dhatu"]
                        ph["dhatu_id"] = p["dhatu_id"]
                        ph["participle_dhatu"] = p["dhatu"]
                        ph["participle_dhatu_id"] = p["dhatu_id"]
                        ph["pratyaya"] = p["pratyaya"]
                        ph["category"] = p["category"]
                        ph["prefix"] = p["prefix"]
                        ph["participle_base"] = p["base"]
                        ph["artha"] = p["artha"]
                        ph["english"] = p["english"]
                        participle_hits.append(ph)
                else:
                    noun_hits.append(h)

            seen = set()
            for h in participle_hits + noun_hits:
                key = (h.get("match_type"), h.get("dhatu_id"), h.get("lemma"), h.get("gender"), h.get("vibhakti"), h.get("vacana"))
                if key in seen:
                    continue
                seen.add(key)
                hits.append(h)
                if len(hits) >= limit:
                    break
    except Exception:
        pass
    return hits[:limit]
