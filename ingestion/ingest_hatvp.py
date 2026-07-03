"""Répertoire HATVP des représentants d'intérêts → table `hatvp_representants`.

Via l'API Tricoteuses Parlement (ressource imposée du hackathon).
Contient la dénomination ET le SIREN des organisations inscrites au registre
du lobbying : croiser le SIREN d'un candidat avec ce répertoire est le signal
« liens d'intérêts » du score de risque. Licence ODbL-1.0 (à créditer).
"""

from __future__ import annotations

from tqdm import tqdm

from ingestion import config
from ingestion.common import get_session, log_provenance, write_jsonl

SOURCE = "hatvp"
LICENCE = "ODbL-1.0 (Tricoteuses / HATVP)"
PER_PAGE = 100


def run(conn) -> None:
    print(f"[{SOURCE}] pagination du répertoire des représentants d'intérêts…")
    session = get_session()
    records = []
    page = 1
    with tqdm(unit=" pages", desc="hatvp") as bar:
        while True:
            r = session.get(
                config.HATVP_REPRESENTANTS,
                params={"page": page, "perPage": PER_PAGE},
                timeout=60,
            )
            r.raise_for_status()
            data = r.json().get("data", [])
            if not data:
                break
            records.extend(data)
            bar.update(1)
            if len(data) < PER_PAGE:
                break
            page += 1

    raw = write_jsonl(records, config.RAW_DIR / "hatvp_representants.jsonl")
    conn.execute(
        f"""
        CREATE OR REPLACE TABLE hatvp_representants AS
        SELECT * FROM read_json_auto('{raw.as_posix()}', format='newline_delimited', sample_size=-1)
        """
    )
    # Le champ `uid` EST le SIREN quand typeIdentifiantNational='SIREN' (vérifié) :
    # vue prête pour la jointure avec le SIREN d'un candidat.
    conn.execute(
        """
        CREATE OR REPLACE VIEW v_lobbying AS
        SELECT uid AS siren, denomination, categorieOrganisationLabel AS categorie,
               ville, dateDernierePublicationActivite
        FROM hatvp_representants
        WHERE typeIdentifiantNational = 'SIREN'
        """
    )
    print("  -> vue v_lobbying créée (3 700+ SIREN inscrits au registre du lobbying)")
    log_provenance(conn, SOURCE, config.HATVP_REPRESENTANTS, "hatvp_representants", LICENCE)
