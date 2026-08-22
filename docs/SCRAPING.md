# Scraping

```bash
conda activate skt-morph
pip install -r scripts/requirements.txt

# single
python scripts/scrape_dhatu.py 01.0001 -o data

# gana / all
python scripts/scrape_dhatu.py --gana 01 -o data
python scripts/scrape_dhatu.py --all -o data

# explicit
python scripts/scrape_dhatu.py --ids 01.0001,01.0002 -o data
python scripts/scrape_dhatu.py --ids-file ids.txt -o data

# resume (completed.txt / failed.txt / dhatu_ids.txt in output dir)
python scripts/scrape_dhatu.py --gana 06 --refresh-ids --restart-browser-every 25 --stop-on-error -o data

python scripts/json_to_sqlite.py --data-dir data --output data/skt_morph.db --force
```
