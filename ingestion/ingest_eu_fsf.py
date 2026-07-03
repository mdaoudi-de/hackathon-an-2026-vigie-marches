"""Sanctions financières de l'UE (FSF, liste consolidée) → table `eu_fsf`.

Chaque entrée référence le règlement UE et son URL EUR-Lex : base légale
citable telle quelle dans le rapport d'aide à la décision.
CSV ~24 Mo (séparateur ;), accessible avec le token public générique.
"""

from __future__ import annotations

from ingestion import config
from ingestion.common import download, get_session, log_provenance

SOURCE = "eu_fsf"
LICENCE = "Commission européenne (FSF, réutilisation libre)"


def run(conn) -> None:
    print(f"[{SOURCE}] téléchargement de la liste consolidée UE…")
    session = get_session()
    dest = download(session, config.EU_FSF_CSV, config.RAW_DIR / "eu_fsf.csv", desc="eu_fsf.csv")

    conn.execute(
        f"""
        CREATE OR REPLACE TABLE eu_fsf AS
        SELECT * FROM read_csv('{dest.as_posix()}', delim=';', header=true,
                               ignore_errors=true, sample_size=-1)
        """
    )
    log_provenance(conn, SOURCE, config.EU_FSF_CSV, "eu_fsf", LICENCE)
