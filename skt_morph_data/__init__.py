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
    get_info,
    get_participles,
    get_prayoga,
    get_upasarga_entries,
    get_upasarga_forms,
    list_dhatus,
    query,
    search_dhatus,
    search_forms,
)

__all__ = [
    "connect",
    "ensure_db",
    "get_db_path",
    "get_dhatu",
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
]

__version__ = "0.1.0"
