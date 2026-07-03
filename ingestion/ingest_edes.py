"""EDES — Early Detection and Exclusion System (UE) → table `edes`.

Opérateurs économiques formellement exclus des marchés et financements UE
(fraude, faute professionnelle grave…). Peu d'entrées publiées mais signal
très fort. Pièges gérés : POST obligatoire (GET → 500) et préfixe anti-XSSI.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone

from ingestion import config
from ingestion.common import get_session, log_provenance, strip_xssi, write_jsonl

SOURCE = "edes"
LICENCE = "Commission européenne (liste publiée EDES)"
PAGE_SIZE = 100


def _epoch_ms_vers_date(valeur):
    if valeur is None:
        return None
    try:
        return datetime.fromtimestamp(int(valeur) / 1000, tz=timezone.utc).date().isoformat()
    except (ValueError, OSError, OverflowError):
        return None


def run(conn) -> None:
    print(f"[{SOURCE}] récupération des exclusions publiées…")
    session = get_session()
    lignes = []
    page = 1
    while True:
        r = session.post(
            config.EDES_API,
            json={"pageNumber": page, "pageSize": PAGE_SIZE, "sortColumn": "", "sortOrder": ""},
            headers={"Content-Type": "application/json"},
            timeout=60,
        )
        r.raise_for_status()
        contenu = json.loads(strip_xssi(r.text)).get("content", [])
        if not contenu:
            break
        for cas in contenu:
            lignes.append(
                {
                    "nom": cas.get("ecOpName"),
                    "adresse": cas.get("ecOpAddress"),
                    "code_pays": cas.get("ecOpCountryCode"),
                    "type": cas.get("type"),
                    "type_libelle": cas.get("typeLabel"),
                    "sanction_financiere": cas.get("fpAmount"),
                    "debut": _epoch_ms_vers_date(cas.get("from")),
                    "fin": _epoch_ms_vers_date(cas.get("to")),
                    "base_legale": cas.get("grounds"),
                    "commentaires": cas.get("comments"),
                }
            )
        if len(contenu) < PAGE_SIZE:
            break
        page += 1

    raw = write_jsonl(lignes, config.RAW_DIR / "edes.jsonl")
    conn.execute(
        f"""
        CREATE OR REPLACE TABLE edes AS
        SELECT * FROM read_json_auto('{raw.as_posix()}', format='newline_delimited', sample_size=-1)
        """
    )
    log_provenance(conn, SOURCE, config.EDES_API, "edes", LICENCE)
