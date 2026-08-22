# skt-morph-data

Sanskrit **dhatu morphology** database scraped from [ashtadhyayi.com](https://ashtadhyayi.com) — conjugations (`ting`, `yak`, `san` …), participles (`krt`/`krut`), `upasarga`, `chandrika` and `prayoga` examples. Data is stored as normalized **SQLite** and queried via Python API + CLI. The DB is auto-downloaded on first use (NLTK-style) to `~/.local/share/skt_morph_data/skt_morph.db`.

Install directly from GitHub (no PyPI needed):

```bash
pip install git+https://github.com/eadaradhiraj/skt-morph-data.git
# or with conda pip
pip install git+ssh://git@github.com/eadaradhiraj/skt-morph-data.git
```

## Quick start (Python)

```python
import skt_morph_data as skt

# first call auto-downloads DB to ~/.local/share/skt_morph_data/skt_morph.db
# (bundled data/skt_morph.db is copied if you run from a checkout)
skt.ensure_db()  

# full dhatu (same shape as original JSON)
d = skt.get_dhatu("01.0001")           # BU – sattAyAm
print(d["info"])
print(d["conjugations"]["ting"]["plat"][:3])
print(d["participles"]["krut"]["kta"])
print(d["upasarga"])
print(d["prayoga"][:1])

# list / search
for row in skt.list_dhatus(gana="01", limit=5):
    print(row["id"], row["label"])

for row in skt.search_dhatus("BU", gana="01", limit=5):
    print(row)

# detailed exact search: returns prefix, pratyaya, dhatu, id, etc.
for hit in skt.search_forms("AdAra", exact=True, limit=5):
    print(hit["dhatu_id"], hit["dhatu"], hit["prefix"], hit["pratyaya"], hit["matched_value"])
hits = skt.find("BUta", exact=True)  # alias

# low-level
print(skt.get_conjugations("01.0001", category="ting"))
print(skt.get_participles("01.0001", category="krut"))
print(skt.get_upasarga_entries("01.0001"))
print(skt.get_chandrika("01.0001"))
print(skt.query("SELECT gana, count(*) as n FROM dhatus GROUP BY gana"))

# custom DB path
skt.get_dhatu("01.0001", db_path="data/skt_morph.db")
```

`ensure_db()` honors:
- `SKT_MORPH_DATA_DIR` – override cache dir
- `SKT_MORPH_DB_URL` – override download URL (default: `https://github.com/eadaradhiraj/skt-morph-data/releases/download/v0.1.0/skt_morph.db` with fallback to `raw.githubusercontent.com/.../data/skt_morph.db`)

## CLI

After `pip install`, two entry points are available: `skt-morph` and `skt-morph-data`.

```bash
# download / cache DB
skt-morph download
skt-morph download --force --url https://example.com/skt_morph.db

# show info (SLP1)
skt-morph info 01.0001
skt-morph show 01.0001 --json > /tmp/dhatu.json

# list / search
skt-morph list --gana 01 --limit 20
skt-morph list --gana 06 --limit 50 --json
skt-morph search BU --gana 01 --limit 10      # substring
skt-morph search AdAra --exact --json        # exact: shows prefix/pratyaya/dhatu/id
skt-morph search "sattAyAm" --limit 5

# conjugations / participles (prefix = upasarga)
skt-morph conjugations 01.0001 --category ting
skt-morph conjugations 01.0001 --prefix pra --json
skt-morph participles 01.0001 --category krut
skt-morph participles 01.0001 --category krut --prefix sam

# upasarga / chandrika / prayoga
skt-morph upasarga 01.0001
skt-morph upasarga 01.0001 --chandrika
skt-morph upasarga 01.0001 --with-forms
skt-morph prayoga 01.0001

# raw SQL
skt-morph query "SELECT id, gana FROM dhatus WHERE gana='01' LIMIT 5"
skt-morph query "SELECT prefix, count(*) FROM conjugation_forms GROUP BY prefix LIMIT 5" --json

# use custom DB
skt-morph --db data/skt_morph.db info 01.0001
```

All commands auto-download the DB on first run.

## Data & DB

- Raw JSON: `data/<gana>/<id>.json` (2259 files, ~10 ganas)
- Built SQLite: `data/skt_morph.db` (~1.2 GB, 10M+ conjugation rows)

Build DB locally:

```bash
python scripts/json_to_sqlite.py --data-dir data --output data/skt_morph.db --force
# custom cache location
python scripts/json_to_sqlite.py --data-dir data --output ~/.local/share/skt_morph_data/skt_morph.db --force
```

Schema:
- `dhatus(id, gana, skipped, skip_reason, label)`
- `dhatu_info(dhatu_id, name, value, note, ext_link)`
- `upasarga_entries(dhatu_id, dhatu, prefix, artha_hindi)` + `upasarga_prefix_meta`
- `chandrika_examples(dhatu_id, prefix, example)`
- `conjugation_forms(dhatu_id, prefix, category, form_type, form_value, position)`
- `participle_forms(dhatu_id, prefix, category, variant, base, m, f, n)`
- `prayoga(dhatu_id, form, lakaar, purusha, vachana)` + `prayoga_examples`

## Scraping (scripts)

Combined scraper `scripts/scrape_dhatu.py` merges the old `scrape_dhatu.py` + `scrape_all.py`.

```bash
# single dhatu
python scripts/scrape_dhatu.py 01.0001 -o data

# whole gana
python scripts/scrape_dhatu.py --gana 01 -o data

# all
python scripts/scrape_dhatu.py --all -o data

# explicit list / file
python scripts/scrape_dhatu.py --ids 01.0001,01.0002 -o data
python scripts/scrape_dhatu.py --ids-file ids.txt -o data

# resume support (uses data/completed.txt, failed.txt, dhatu_ids.txt)
python scripts/scrape_dhatu.py --gana 06 --refresh-ids -o data --restart-browser-every 25 --stop-on-error

# rebuild DB after scraping
python scripts/json_to_sqlite.py --data-dir data --output data/skt_morph.db --force
```

Install scraping deps:
```bash
conda activate ./env  # or pip
pip install -r scripts/requirements.txt
```
Requires `chromedriver.exe` next to script or at repo root + Chrome.

## Publishing a DB release (for auto-download)

1. Build `data/skt_morph.db`
2. `gh release create v0.1.0 data/skt_morph.db`  (or upload via GitHub UI)
3. Users `pip install git+https://github.com/eadaradhiraj/skt-morph-data.git` will auto-fetch `.../releases/download/v0.1.0/skt_morph.db`.

## Development

```bash
git clone git@github.com:eadaradhiraj/skt-morph-data.git
cd skt-morph-data
pip install -e .
skt-morph download          # copies bundled data/skt_morph.db if present, else downloads
pytest -q                   # (no tests yet)
```

## License

MIT
