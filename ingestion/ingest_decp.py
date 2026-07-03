"""DECP consolidées format tabulaire (3,1M de marchés) → table ou vue `decp`
+ vue d'agrégats `v_decp_stats_titulaire` (features du score de risque).

Deux modes :
- par défaut : téléchargement du Parquet quotidien (~200 Mo) puis matérialisation
  en table locale (requêtes instantanées ensuite) ;
- `--decp-remote` : simple VUE DuckDB sur le Parquet distant via httpfs
  (zéro téléchargement, lectures partielles HTTP — parfait pour démarrer vite).

Une ligne = un couple marché-titulaire : dédupliquer par `uid` pour compter
des marchés. Licence Ouverte 2.0 (consolidation communautaire decp.info).
"""

from __future__ import annotations

from ingestion import config
from ingestion.common import download, get_session, log_provenance

SOURCE = "decp"
LICENCE = "Licence Ouverte 2.0 (DECP consolidées, decp.info)"


def _resoudre_url(session) -> str:
    """Suit la redirection data.gouv.fr → static.data.gouv.fr (httpfs ne la suit pas)."""
    r = session.head(config.DECP_PARQUET, allow_redirects=True, timeout=60)
    r.raise_for_status()
    return r.url


def _creer_vue_stats(conn, relation: str) -> None:
    """Agrégats par titulaire (SIRET) : le « track-record » d'un candidat."""
    conn.execute(
        f"""
        CREATE OR REPLACE VIEW v_decp_stats_titulaire AS
        SELECT
            titulaire_id,
            any_value(titulaire_nom)                     AS titulaire_nom,
            count(DISTINCT uid)                          AS nb_marches,
            sum(montant)                                 AS montant_total,
            count(DISTINCT acheteur_id)                  AS nb_acheteurs_distincts,
            max(dateNotification)                        AS dernier_marche,
            avg(CASE WHEN offresRecues = 1 THEN 1.0 ELSE 0.0 END)
                                                         AS part_offre_unique
        FROM {relation}
        WHERE titulaire_id IS NOT NULL
        GROUP BY titulaire_id
        """
    )
    print("  -> vue v_decp_stats_titulaire créée (nb marchés, montants, part offre unique…)")


def run(conn, remote: bool = False) -> None:
    session = get_session()
    url = _resoudre_url(session)

    if remote:
        print(f"[{SOURCE}] création d'une vue sur le Parquet distant (httpfs)…")
        conn.execute("INSTALL httpfs; LOAD httpfs;")
        conn.execute("DROP TABLE IF EXISTS decp")
        conn.execute(f"CREATE OR REPLACE VIEW decp AS SELECT * FROM read_parquet('{url}')")
        note = "vue distante httpfs (aucun téléchargement)"
    else:
        print(f"[{SOURCE}] téléchargement du Parquet consolidé (~200 Mo)…")
        dest = download(session, url, config.RAW_DIR / "decp.parquet", desc="decp.parquet")
        conn.execute("DROP VIEW IF EXISTS decp")
        conn.execute(
            f"CREATE OR REPLACE TABLE decp AS SELECT * FROM read_parquet('{dest.as_posix()}')"
        )
        note = "table matérialisée depuis le Parquet quotidien"

    _creer_vue_stats(conn, "decp")
    log_provenance(conn, SOURCE, url, "decp", LICENCE, note=note)
