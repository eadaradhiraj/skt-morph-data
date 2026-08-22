import skt_morph_data as skt

def test_search_forms_exact():
    hits = skt.search_forms("AdAra", exact=True, limit=5)
    assert len(hits) >= 1
    h = hits[0]
    assert "dhatu_id" in h and "dhatu" in h and "prefix" in h and "pratyaya" in h
    assert h["matched_value"] == "AdAra"
    # check that prefix/pratyaya present for this hit
    assert h["prefix"] in ("AN", "")
    assert h["category"] in ("krut", "nich_krut")

def test_search_forms_substring():
    hits = skt.search_forms("BU", exact=False, limit=3)
    assert len(hits) >= 1
    assert any("BU" in h["matched_value"] for h in hits)

def test_find_alias():
    hits = skt.find("Bavati", exact=True, limit=2)
    assert len(hits) >= 1
    assert hits[0]["match_type"] == "conjugation"
    assert hits[0]["form_value"] == "Bavati"

def test_search_cli_import():
    from skt_morph_data.cli import build_parser
    p = build_parser()
    args = p.parse_args(["search", "AdAra", "--exact", "--json"])
    assert args.text == "AdAra" and args.exact is True
