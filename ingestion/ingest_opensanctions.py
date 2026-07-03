"""Miroirs OpenSanctions (bulk data, sans clé) → tables `os_<slug>`.

Par défaut : `worldbank_debarred` (exclusions Banque mondiale + cross-debarment
BAD/BERD/BID — l'API directe de la Banque mondiale n'est pas fiable) et
`eu_edes` (miroir EDES).

⚠️ Licence CC-BY-NC 4.0 : gratuit pour le prototype/hackathon, licence
OpenSanctions requise pour un usage commercial en production.
"""

from __future__ import annotations

from ingestion import config
from ingestion.common import download, get_session, log_provenance

SOURCE = "opensanctions"
LICENCE = "CC-BY-NC 4.0 (OpenSanctions — non commercial)"


def run(conn, slugs: list[str] | None = None) -> None:
    session = get_session()
    for slug in slugs or config.OPENSANCTIONS_SLUGS:
        url = config.OPENSANCTIONS_CSV.format(slug=slug)
        table = f"os_{slug}"
        print(f"[{SOURCE}] téléchargement du dataset {slug}…")
        dest = download(session, url, config.RAW_DIR / f"os_{slug}.csv", desc=f"os_{slug}.csv")
        conn.execute(
            f"""
            CREATE OR REPLACE TABLE "{table}" AS
            SELECT * FROM read_csv('{dest.as_posix()}', header=true,
                                   ignore_errors=true, sample_size=-1)
            """
        )
        log_provenance(conn, SOURCE, url, table, LICENCE)
