"""Canutes — annuaire des services publics locaux (PostgREST) → tables
`acheteurs_locaux` et `communes` + vue `v_acheteurs`.

Ressource imposée du hackathon (db.code4code.eu/canutes, données DILA) :
référentiel d'identité des acheteurs publics locaux (mairies…) avec
SIREN/SIRET, coordonnées officielles et géolocalisation.
"""

from __future__ import annotations

from tqdm import tqdm

from ingestion import config
from ingestion.common import get_session, log_provenance, write_jsonl

SOURCE = "canutes"
LICENCE = "© DILA (annuaire de l'administration)"
LIMIT = 1000


def _paginer(session, table: str) -> list[dict]:
    records = []
    offset = 0
    # count=exact sur la 1re page pour connaître le total (en-tête Content-Range)
    headers = {"Prefer": "count=exact"}
    total = None
    with tqdm(unit=" lignes", desc=table) as bar:
        while True:
            r = session.get(
                f"{config.CANUTES_BASE}/{table}",
                params={"limit": LIMIT, "offset": offset},
                headers=headers if offset == 0 else {},
                timeout=120,
            )
            r.raise_for_status()
            if offset == 0 and "Content-Range" in r.headers:
                plage = r.headers["Content-Range"]  # ex. "0-999/37400"
                total = int(plage.split("/")[-1]) if "/" in plage else None
                bar.total = total
            page = r.json()
            if not page:
                break
            records.extend(page)
            bar.update(len(page))
            if len(page) < LIMIT:
                break
            offset += LIMIT
    return records


def run(conn) -> None:
    session = get_session()

    print(f"[{SOURCE}] téléchargement de la table services…")
    services = _paginer(session, "services")
    raw_services = write_jsonl(services, config.RAW_DIR / "canutes_services.jsonl")
    conn.execute(
        f"""
        CREATE OR REPLACE TABLE acheteurs_locaux AS
        SELECT * FROM read_json_auto('{raw_services.as_posix()}',
                                     format='newline_delimited', sample_size=-1)
        """
    )
    log_provenance(conn, SOURCE, f"{config.CANUTES_BASE}/services", "acheteurs_locaux", LICENCE)

    print(f"[{SOURCE}] téléchargement de la table communes…")
    communes = _paginer(session, "communes")
    raw_communes = write_jsonl(communes, config.RAW_DIR / "canutes_communes.jsonl")
    conn.execute(
        f"""
        CREATE OR REPLACE TABLE communes AS
        SELECT * FROM read_json_auto('{raw_communes.as_posix()}',
                                     format='newline_delimited', sample_size=-1)
        """
    )
    log_provenance(
        conn,
        SOURCE,
        f"{config.CANUTES_BASE}/communes",
        "communes",
        LICENCE,
        note="table partielle (~7 500 / 35 000 communes)",
    )

    # Vue aplatie prête pour les jointures par SIREN/SIRET
    conn.execute(
        """
        CREATE OR REPLACE VIEW v_acheteurs AS
        SELECT
            id,
            json_extract_string(to_json(data), '$.nom')       AS nom,
            json_extract_string(to_json(data), '$.siren')     AS siren,
            json_extract_string(to_json(data), '$.siret')     AS siret,
            json_extract_string(to_json(data), '$.categorie') AS categorie,
            json_extract_string(to_json(data), '$.adresse_courriel') AS courriel,
            json_extract_string(to_json(data), '$.adresse[0].nom_commune')  AS commune,
            json_extract_string(to_json(data), '$.adresse[0].code_postal')  AS code_postal,
            json_extract_string(to_json(data), '$.adresse[0].latitude')     AS latitude,
            json_extract_string(to_json(data), '$.adresse[0].longitude')    AS longitude
        FROM acheteurs_locaux
        """
    )
    print("  -> vue v_acheteurs créée (nom, siren, siret, commune, géoloc)")
