"""skt_morph_data — query ashtadhyayi dhatu morphology from a local SQLite DB.

The DB is auto-downloaded on first use (like nltk data) to a user cache dir.

Quick start::

    import skt_morph_data as skt
    skt.ensure_db()                     # downloads if missing
    d = skt.get_dhatu("01.0001")        # full dict like original JSON
    for row in skt.list_dhatus(gana="01", limit=5):
        print(row)
    forms = skt.get_conjugations("01.0001", category="ting")
"""

from __future__ import annotations

from .db import (
    connect,
    ensure_db,
    get_db_path,
)
from .query import (
    find,
    get_chandrika,
    get_conjugations,
    get_dhatu,
    get_ids_by_dhatu,
    get_info,
    get_participles,
    get_prayoga,
    get_upasarga_entries,
    get_upasarga_forms,
    list_dhatus,
    query,
    resolve_dhatu_input,
    search_dhatus,
    search_forms,
)
from .subanta import (
    analyze,
    analyze_form,
    decline,
    decline_noun,
    decline_numeral,
    decline_pronoun,
    decline_to_dict,
    detect_paradigm,
    flatten_forms,
    get_declension,
    list_numerals,
    list_paradigms,
    list_pronouns,
    to_table,
)
from .krdanta import (
    decline_participle,
    get_dhatu_participles_summary,
    list_participle_pratyayas,
)

__all__ = [
    "connect",
    "ensure_db",
    "get_db_path",
    "get_dhatu",
    "get_ids_by_dhatu",
    "resolve_dhatu_input",
    "get_info",
    "get_conjugations",
    "get_participles",
    "get_upasarga_entries",
    "get_chandrika",
    "get_prayoga",
    "get_upasarga_forms",
    "list_dhatus",
    "search_dhatus",
    "search_forms",
    "find",
    "query",
    # subanta / nominal declension
    "decline",
    "get_declension",
    "decline_noun",
    "decline_pronoun",
    "decline_numeral",
    "decline_to_dict",
    "detect_paradigm",
    "flatten_forms",
    "list_paradigms",
    "list_pronouns",
    "list_numerals",
    "to_table",
    "analyze",
    "analyze_form",
    # krdanta / participle declension
    "decline_participle",
    "list_participle_pratyayas",
    "get_dhatu_participles_summary",
]

__version__ = "0.1.0"
