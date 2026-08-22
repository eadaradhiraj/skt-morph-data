# API Reference

## Python

```python
import skt_morph_data as skt

skt.ensure_db(dest=None, force=False)  # auto-copies bundled or downloads
skt.get_db_path()  # -> ~/.local/share/skt_morph_data/skt_morph.db

skt.get_dhatu("01.0001", db_path=None)  # full reconstructed JSON
skt.get_info("01.0001")
skt.get_conjugations("01.0001", category="ting", prefix="")
skt.get_participles("01.0001", category="krut", prefix="")
skt.get_upasarga_entries("01.0001")
skt.get_chandrika("01.0001")
skt.get_prayoga("01.0001")
skt.get_upasarga_forms("01.0001")
skt.list_dhatus(gana="01", limit=50, offset=0, include_skipped=True)
skt.search_dhatus("BU", gana="01", limit=20)  # legacy: returns dhatu rows
skt.search_forms("AdAra", exact=True, gana="06", limit=20)  # detailed: prefix, pratyaya, dhatu, id
skt.find("BUta", exact=True)  # alias for search_forms
skt.query("SELECT * FROM dhatus LIMIT 5")
```

All query functions accept `db_path` optional; if omitted they use `~/.local/share/skt_morph_data/skt_morph.db` and auto-download/copy if missing (NTLK-style).

## CLI

```
skt-morph download [--force --url URL --output PATH]
skt-morph info <id> [--json]
skt-morph show <id> [--json]
skt-morph list [--gana 01 --limit 50 --offset 0 --no-skipped --json]
skt-morph search <text> [--exact --gana 01 --limit 20 --json]  # exact or substring, returns prefix/pratyaya/dhatu/id
skt-morph find <text> [--exact --gana 01 --limit 20 --json]  # alias
skt-morph conjugations <id> [--category ting --prefix pra --json]
skt-morph participles <id> [--category krut --prefix sam --json]
skt-morph upasarga <id> [--chandrika --with-forms --json]
skt-morph prayoga <id> [--json]
skt-morph query "SELECT ..." [--json]
```

## DB Schema

See `scripts/json_to_sqlite.py` DDL.

## Scripts

* `scripts/scrape_dhatu.py` – unified scraper (single `--ids` or batch `--gana/--all`)
* `scripts/json_to_sqlite.py` – builds `data/skt_morph.db`
* `scripts/requirements.txt` – scrape deps

Requires `scripts/requirements.txt` + Chrome + chromedriver.
