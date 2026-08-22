"""Basic smoke tests for skt_morph_data package — run with `pytest -q` inside conda env skt-morph."""
import pathlib
import sqlite3
import pytest

import skt_morph_data as skt
from skt_morph_data import get_db_path

# Use bundled DB if present, else default cache (auto-downloaded)
DB = pathlib.Path("data/skt_morph.db")
if not DB.exists():
    DB = get_db_path()

@pytest.fixture(scope="module")
def db_path():
    # ensure DB exists for tests
    if not DB.exists():
        skt.ensure_db(dest=DB)
    assert DB.exists(), f"DB missing at {DB}"
    return DB

def test_get_dhatu_info(db_path):
    d = skt.get_dhatu("01.0001", db_path=db_path)
    assert d["id"] == "01.0001"
    assert any(i["name"] == "OpadeSikasvarUpam" for i in d["info"])
    assert d["conjugations"]  # at least some
    assert d["participles"]  # nested dict

def test_skipped_dhatu(db_path):
    d = skt.get_dhatu("01.0933", db_path=db_path)
    assert d.get("skipped") is True
    assert d["skip_reason"] in ("ganasutra", "no_forms")

def test_conjugations_category(db_path):
    forms = skt.get_conjugations("01.0001", category="ting", db_path=db_path)
    assert "ting" in forms
    assert "plat" in forms["ting"]
    assert len(forms["ting"]["plat"]) >= 5

def test_participles_nested(db_path):
    data = skt.get_participles("01.0001", category="krut", db_path=db_path)
    assert "krut" in data
    assert "kta" in data["krut"]
    assert data["krut"]["kta"][0]["base"] == "BUta"

def test_list_and_search(db_path):
    rows = skt.list_dhatus(gana="01", limit=5, db_path=db_path)
    assert len(rows) == 5
    assert all(r["gana"] == "01" for r in rows)
    hits = skt.search_dhatus("BU", limit=3, db_path=db_path)
    assert len(hits) >= 1

def test_upasarga_and_prayoga(db_path):
    up = skt.get_upasarga_entries("01.0001", db_path=db_path)
    assert "entries" in up
    ch = skt.get_chandrika("01.0001", db_path=db_path)
    assert isinstance(ch, list)
    pr = skt.get_prayoga("01.0001", db_path=db_path)
    assert isinstance(pr, list)
    assert len(pr) > 0

def test_raw_query(db_path):
    rows = skt.query("SELECT gana, count(*) as c FROM dhatus GROUP BY gana ORDER BY gana", db_path=db_path)
    assert any(r["gana"] == "01" for r in rows)

def test_cli_import():
    # ensures CLI module importable without DB
    from skt_morph_data.cli import build_parser
    p = build_parser()
    assert p is not None

def test_upasarga_forms(db_path):
    forms = skt.get_upasarga_forms("01.0001", db_path=db_path)
    # may be empty for some dhatus, but should be dict
    assert isinstance(forms, dict)
