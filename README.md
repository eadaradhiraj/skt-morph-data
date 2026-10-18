# skt-morph-data

Comprehensive Sanskrit morphology engine and database:
- **Dhatu Morphology (Verbal)**: 2,200+ dhātus scraped from [ashtadhyayi.com](https://ashtadhyayi.com) — complete conjugations (`ting`, `yak`, `san`, `yaṅ`), participles (`krut`), `upasarga` variants, `chandrika` and `prayoga` usage examples. Data is stored in normalized **SQLite**.
- **Subanta Engine (Nominal Declensions)**: Complete 8-vibhakti × 3-vacana tables across **105 classical paradigms** (vowel and consonant stems, root `-h` stems, classical irregulars like `anaquh`, `div`/`dyu`, `nf`, `pad`/`pat`, `krozwu`, `candramas`, `yuj`, `vftrahan`, `maGavan`), paddan-ādi optional stems (`danta`, `hfdaya`, `mAsa`, `pAda`, `niSA`, `udaka`), pronouns (`asmad`, `yuzmad`, `tad`, `etad`, `sarva`, `sama`, `sIma`, `nema`...), and numerals (`eka` through `sahasra`, with classical *sadaikatve strītvam* for 20–99).
- **Kṛdanta Bridge (Participle Declensions)**: Connects verbal participles (`kta`, `ktavatu`, `Satf`, `SAnac`, `tavya`, `anIyar`, `yat`, `tfc`, `kvasu`, etc.) with the subanta engine to generate complete nominal declension tables across all genders and cases.
- **Reverse Morphological Analyzer**: Analyze inflected Sanskrit forms back to their base lemma, vibhakti, vacana, or dhātu.
- **Pāṇinian Natva Engine**: Exact implementation of *raṣābhyāṁ no ṇaḥ samānapade* (8.4.1) and *aṭkupvāṅnumvyavāye'pi* (8.4.2).

All inputs and outputs use standard **SLP1** transliteration.

The SQLite database is auto-downloaded on first use (NLTK-style) to `~/.local/share/skt_morph_data/skt_morph.db`.

## Installation

Install directly from GitHub:

```bash
pip install git+https://github.com/eadaradhiraj/skt-morph-data.git
# or with SSH
pip install git+ssh://git@github.com/eadaradhiraj/skt-morph-data.git
```

---

## Quick Start (Python)

### 1. Subanta (Nominal Declensions)

```python
from skt_morph_data import decline, analyze_form, to_table, to_markdown, to_anki, format_declension

# Regular vowel stems (with automatic Paninian natva)
decline("rAma", gender="m")    # a-stem (rAmeRa, rAmARAm)
decline("deva", gender="m")    # a-stem (devena, devAnAm)
decline("Pala", gender="n")    # a-stem neuter
decline("nadI", gender="f")    # I-stem feminine

# Consonant and classical irregular stems
decline("nf", gender="m")      # man (nA, narO, naraH; Panini 6.4.11-12)
decline("pad", gender="m")     # foot (pAt, padO, padaH; Panini 6.4.130)
decline("anaquh", gender="m")  # ox/bull (anaqvAn, anaqvAhO, anaqudByAm, anaqutsu)
decline("duh", gender="m")     # milker (Duk/Dug, duhO, duhaH; throwback aspiration)
decline("lih", gender="m")     # licker (liw/liq, lihO, lihaH; cerebral)
decline("div", gender="f")     # heaven/sky (dyOH, divam, divA, dyuByAm)
decline("krozwu", gender="m")  # jackal (krozwA, krozwrA/krozwunA)
decline("candramas", gender="m") # moon (candramAH, candramoByAm)
decline("yuj", gender="m")     # companion (yuN, yuYjO, yugByAm)
decline("tiryac", gender="m")  # animal/crooked (tiryaN, tiryaYcO, tiraScaH)
decline("vftrahan", gender="m")# slayer of Vritra (vftrahA, vftrahaRO, vftraGRaH)
decline("maGavan", gender="m") # Indra (maGavAn, maGavAntO, maGonaH)
decline("go", gender="m")      # bull/cow (gOH, gAm, gavA, gave)
decline("pitf", gender="m")    # kinship (pitA, pitarO, pitaraH)
decline("kartf", gender="m")   # agent noun (kartA, kartArO, kartAraH)

# Paddan-adi optional substitutions (Panini 6.1.63)
decline("danta", gender="m")   # dantAn/dataH, dantena/datA, dantAByAm/dadByAm...
decline("hfdaya", gender="n")  # hfdayena/hfdA, hfdayezu/hftsu...

# Pronouns (with correct enclitic distribution & vocatives)
decline("asmad")               # aham, AvAm, vayam; mAm/mA; mahyam/me...
decline("yuzmad")              # tvam, yuvAm, yUyam; tvAm/tvA; tuByam/te...
decline("tad", gender="m")     # saH, tO, te
decline("sarva", gender="m")   # sarvaH, sarvO, sarve (vocative: he sarva)
decline("sama", gender="m")    # samasmE, samasmAt... (sarvanama)
decline("praTama", gender="m") # optional Jas plural: praTamAH / praTame

# Numerals
decline("tri", gender="f")     # tisraH, tisfBiH, tisfRAm
decline("catur", gender="m")   # catvAraH, caturaH, caturBiH
decline("viMSati")             # 20-99 singular feminine only (viMSatiH, viMSatyA...)

# Pretty table & multi-format export (table, markdown, html, csv, latex, anki, json)
print(to_table(decline("rAma", gender="m")))
print(to_markdown(decline("rAma", gender="m")))
print(to_anki(decline("rAma", gender="m")))            # Anki flashcard TSV
print(format_declension(decline("rAma", gender="m"), fmt="latex"))

# Reverse morphological analysis (inflected form -> lemma + vibhakti/vacana)
hits = analyze_form("anaqvAn")
# -> [{'lemma': 'anaquh', 'vibhakti': 'prathamA', 'vacana': 'ekavacana', ...}]
hits = analyze_form("datA")    # paddan-adi form
# -> [{'lemma': 'danta', 'vibhakti': 'tftIyA', 'vacana': 'ekavacana', ...}]
hits = analyze_form("Duk")     # root -h stem
# -> [{'lemma': 'duh', 'vibhakti': 'prathamA', 'vacana': 'ekavacana', ...}]
```

### 2. Kṛdanta (Verbal Participles)

```python
from skt_morph_data import decline_participle, list_participle_pratyayas

# Past passive participle (kta)
res = decline_participle("BU", "kta", gender="m")
# -> BUtaH, BUtO, BUtAH...

# Present active participle (Satf)
res = decline_participle("gam", "Satf", gender="f")
# -> gacCantI, gacCantyO, gacCantyaH...

# Past active participle (ktavatu) across all 3 genders
res = decline_participle("kf", "ktavatu")
# res["genders"]["m"] -> kftavAn...
# res["genders"]["f"] -> kftavatI...
# res["genders"]["n"] -> kftavat...

# Agent noun (tfc)
res = decline_participle("BU", "tfc", gender="m")
# -> BavitA, BavitArO, BavitAraH...

# Indeclinables (avyaya)
res = decline_participle("BU", "ktvA")   # BUtvA
res = decline_participle("gam", "tumun") # gantum

# Available suffixes for a root
print(list_participle_pratyayas("BU"))
```

### 3. Dhatu Morphology (Verbal)

```python
import skt_morph_data as skt

# Auto-downloads DB to ~/.local/share/skt_morph_data/skt_morph.db on first call
skt.ensure_db()

# Full dhatu details
d = skt.get_dhatu("01.0001")           # BU – sattAyAm
print(d["info"])
print(d["conjugations"]["ting"]["plat"][:3])
print(d["participles"]["krut"]["kta"])
print(d["upasarga"])
print(d["prayoga"][:1])

# Search dhatus and forms
for row in skt.list_dhatus(gana="01", limit=5):
    print(row["id"], row["label"])

for hit in skt.search_forms("AdAra", exact=True, limit=5):
    print(hit["dhatu_id"], hit["dhatu"], hit["prefix"], hit["pratyaya"])

# Unified verb + nominal analyzer
results = skt.analyze("Bavati")   # conjugation of BU
results = skt.analyze("rAmeRa")   # declension of rAma
```

---

## CLI

Two command-line aliases are provided: `skt-morph` and `skt-morph-data`.

### Subanta (Declension)

```bash
# Decline nouns, pronouns, numerals
skt-morph decline rAma --gender m
skt-morph decline nf --gender m                         # irregular kinship / guRa
skt-morph decline pad --gender m                        # foot (pAt, padO, padaH)
skt-morph decline anaquh --gender m
skt-morph decline duh --gender m                        # -h stem (Duk/Dug, duhO)
skt-morph decline tiryac --gender m                     # directional irregular
skt-morph decline danta --gender m                      # paddan-adi optional stems
skt-morph decline div --gender f
skt-morph decline asmad
skt-morph decline sarva --gender m
skt-morph decline pUrva --category pronoun --gender m   # Panini 1.1.32-36 optional forms
skt-morph decline tri --gender f
skt-morph decline viMSati                               # feminine singular only

# Export in multiple formats: markdown, html, csv, latex, anki, json
skt-morph decline rAma --gender m --format markdown
skt-morph decline rAma --gender m --format html
skt-morph decline rAma --gender m --format csv
skt-morph decline rAma --gender m --format latex
skt-morph decline rAma --gender m --format anki > anki_cards.tsv  # Anki flashcards (Front <TAB> Back <TAB> Tag)

# List supported paradigms
skt-morph paradigms
skt-morph pronouns
skt-morph numerals
```

### Kṛdanta (Participles)

```bash
# Decline participles
skt-morph decline-participle BU kta --gender m
skt-morph decline-participle gam Satf --gender f
skt-morph decline-participle kf ktavatu             # all genders (m, f, n)
skt-morph decline-participle BU tfc --gender m
skt-morph decline-participle BU ktvA                # avyaya (indeclinable)
skt-morph decline-participle gam tumun

# Export participle declensions directly to Anki flashcards
skt-morph decline-participle BU ktavatu --gender m --format anki
```

### Morphological Analysis

```bash
# Analyze any inflected word (verb conjugation, noun declension, or verbal participle)
skt-morph analyze rAmeRa
skt-morph analyze Bavati
skt-morph analyze anaqvAn
skt-morph analyze --json gacCan

# Filter options: restrict to nominals, strict SLP1 matching, or limit results
skt-morph analyze datA --nominal-only               # paddan-adi: maps to danta
skt-morph analyze nA --strict                       # strict transliteration
skt-morph analyze rAmaH --limit 5

# Participle inflections are automatically bridged back to root + pratyaya:
skt-morph analyze BUtavatA
# -> tftIyA ekavacana (m) of root "BU" + "ktavatu" (nominal stem "BUtavat")
skt-morph analyze gacCatA
# -> tftIyA ekavacana (m) of root "gamx~" + "Satf" (nominal stem "gacCat")
skt-morph analyze kftena
# -> tftIyA ekavacana (m) of root "qukfY"/"kfY" + "kta" (nominal stem "kfta")
```

### Dhatu Queries

```bash
# Download / verify DB
skt-morph download
skt-morph download --force

# Dhatu info and search
skt-morph info 01.0001
skt-morph search BU --gana 01
skt-morph search AdAra --exact

# Conjugations & participles
skt-morph conjugations 01.0001 --category ting
skt-morph conjugations 01.0001 --prefix pra
skt-morph participles 01.0001 --category krut

# Upasarga, Chandrika, Prayoga
skt-morph upasarga 01.0001 --with-forms
skt-morph prayoga 01.0001

# Raw SQL
skt-morph query "SELECT id, gana FROM dhatus WHERE gana='01' LIMIT 5"
```

---

## Supported Subanta Paradigms (105 total)

| Category | Paradigms |
| :--- | :--- |
| **Ajanta (Vowels)** | `a_m` (rAma), `a_n` (Pala), `A_f` (ramA), `A_m` (viSvapA root A), `i_m` (hari), `pati_m` (pati uncompounded), `sakhi_m` (sakhi), `i_f` (mati), `i_n` (vAri), `asthi_n` (daDi, akzi, asTi, sakTi), `I_f` (nadI), `sri_f` (SrI/hrI/DI iyaṅ), `sudhi_m` (suDI iyaṅ), `I_m` (senAnI yaṇ), `lakzmi_f` (lakzmI), `stri_f` (strI), `u_m` (guru), `krozwu_m` (krozwu/krozwf), `u_f` (Denu), `u_n` (maDu), `U_f` (vaDU), `bhu_f` (BU/BrU uvaṅ), `f_m` (pitf kinship), `tf_m` (kartf agent noun), `f_f` (mAtf), `svasf_f` (svasf), `f_n` (dAtf), `nr_m` (nf man, Pāṇini 6.4.11-12) |
| **Diphthongs** | `o_m` / `o_f` (go bull/cow), `nau_f` (nO boat), `glau_m` (glO moon), `rai_m` / `rai_f` (rE wealth) |
| **Halanta (Consonants)** | `t_m` (marut), `t_f` (sarit), `t_n` (jagat), `d_f` (sampad, Apad), `pad_m` (pad/pat/pada foot, Pāṇini 6.4.130), `kzuD_f` (kzuD), `dh_f` (samiD), `c_f` (vAc), `j_m` (Bizaj), `yuj_m` (yuj), `Buj_m` / `Buj_f` (Buj ruler/enjoyer), `dis_f` / `dis_m` (diS/viS), `r_f` (dvAr), `gir_f` (gir), `pur_f` (pur), `div_f` / `div_m` (div/dyu heaven), `anaquh_m` (anaquh ox), `ap_f` (ap water plural) |
| **Root Stems in `-h`** | `duh_m` / `duh_f` (duh milker, throwback aspiration Pāṇini 8.2.32/37), `lih_m` / `lih_f` (lih licker, cerebral Pāṇini 8.2.31), `druh_m` / `druh_f` (druh enemy, optional velar/cerebral Pāṇini 8.2.33), `muh_m` / `muh_f` (muh bewildered), `snih_m` / `snih_f` (snih attached) |
| **Velar Root Stems** | `drs_m` / `drs_f` (dfS seeing/eye, Pāṇini 8.2.36, 8.2.62), `spfs_m` / `spfs_f` (spfS touching, Pāṇini 8.2.36, 8.2.62) |
| **-at / -vat / -mat Stems** | `at_m` (participle Bavat/gacchat), `bhavat_m` (honorific BavAn), `at_n` (jagat), `mahat_m` (mahAn), `mahat_n` (mahat), `vat_m` (Danavat), `mat_m` (budDimat) |
| **-an / -in Stems** | `an_m` (Atman), `rajan_m` (rAjan), `an_n` (nAman), `karman_n` (karman), `in_m` (yogin), `in_n` (balin), `pathin_m` (panTA), `ahan_n` (ahan), `pums_m` (pums), `svan_m` (Svan), `yuvan_m` (yuvan), `vftrahan_m` (vftrahan), `han_m` (Satruhan), `maghavan_m` (maGavan) |
| **-as / -is / -us Stems** | `as_n` (manas), `as_m` / `as_f` (sumanas), `candramas_m` (candramas), `yas_m` / `yas_n` (Sreyas), `vidvas_m` / `vas_m` (vidvAn / kvasu participles), `is_n` (havis), `us_n` (Danus) |
| **Directional -aYc Stems** | `pranc_m` (prAYc), `pratyanc_m` (pratyaYc), `udanc_m` (udaYc), `tiryac_m` / `tiryac_n` (tiryac animal/crooked, Pāṇini 6.4.113) |
| **Paddan-ādi Stems (Pāṇini 6.1.63)** | Optional secondary substitutions from acc. pl. onward: `danta` (dat), `mAsa` (mAs), `hfdaya` (hfd), `pAda` (pad), `niSA` (niS), `udaka` (udan) |
| **Pronouns** | `asmad`, `yuzmad`, `tad`, `etad`, `yad`, `kim`, `idam`, `adas`, `tyad`, `sarva`, `viSva`, `uBa`, `uBaya`, `anya`, `anyatara`, `itara`, `katara`, `katama`, `pUrva`, `para`, `avara`, `dakziRa`, `uttara`, `apara`, `aDara`, `sama`, `sIma`, `nema`, `praTama`, `carama`, `alpa`, `sva`, `antara` |
| **Numerals** | `eka`, `dvi`, `tri`, `catur`, `paYcan`, `zaz`, `saptan`, `azwan`, `navan`, `daSan`, teens 11–19; tens 20–90 (`viMSati` to `navati` — singular feminine only per *viṁśatyādayaḥ sadaikatve strītvam*), `Sata`, `sahasra` |

---

## Data & Database Schema

The SQLite database (~1.2 GB, 10M+ conjugation rows) normalizes:
- `dhatus(id, gana, skipped, skip_reason, label)`
- `dhatu_info(dhatu_id, name, value, note, ext_link)`
- `conjugation_forms(dhatu_id, prefix, category, form_type, form_value, position)`
- `participle_forms(dhatu_id, prefix, category, variant, base, m, f, n)`
- `upasarga_entries(dhatu_id, dhatu, prefix, artha_hindi)` + `upasarga_prefix_meta`
- `chandrika_examples(dhatu_id, prefix, example)`
- `prayoga(dhatu_id, form, lakaar, purusha, vachana)` + `prayoga_examples`

Rebuild database locally from raw JSON:
```bash
python scripts/json_to_sqlite.py --data-dir data --output data/skt_morph.db --force
```

---

## Running Tests

Run the full test suite (subanta, krdanta, search, query, CLI):

```bash
pytest
```

---

## License

MIT
