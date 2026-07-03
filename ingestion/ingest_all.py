"""Orchestrateur d'ingestion : construit/rafraîchit la base data/vigie.duckdb.

Usage (depuis la racine du dépôt, venv activé) :

    python -m ingestion.ingest_all                     # tout (DECP téléchargé, ~200 Mo)
    python -m ingestion.ingest_all --decp-remote       # tout, DECP en vue distante (rapide)
    python -m ingestion.ingest_all --only gels_avoirs edes
    python -m ingestion.ingest_all --skip decp hatvp

La table `_provenance` journalise chaque source (URL, date, nb lignes, licence).
"""

from __future__ import annotations

import argparse
import sys
import traceback

from ingestion import (
    ingest_canutes,
    ingest_decp,
    ingest_edes,
    ingest_eu_fsf,
    ingest_gels_avoirs,
    ingest_hatvp,
    ingest_opensanctions,
)
from ingestion.common import connect_db

SOURCES = {
    "gels_avoirs": lambda conn, args: ingest_gels_avoirs.run(conn),
    "eu_fsf": lambda conn, args: ingest_eu_fsf.run(conn),
    "edes": lambda conn, args: ingest_edes.run(conn),
    "opensanctions": lambda conn, args: ingest_opensanctions.run(conn),
    "hatvp": lambda conn, args: ingest_hatvp.run(conn),
    "canutes": lambda conn, args: ingest_canutes.run(conn),
    "decp": lambda conn, args: ingest_decp.run(conn, remote=args.decp_remote),
}


def main() -> int:
    parser = argparse.ArgumentParser(description="Ingestion des sources Open Data de Vigie Marchés")
    parser.add_argument("--only", nargs="+", choices=SOURCES, help="n'ingérer que ces sources")
    parser.add_argument("--skip", nargs="+", choices=SOURCES, default=[], help="sources à sauter")
    parser.add_argument(
        "--decp-remote",
        action="store_true",
        help="DECP en vue DuckDB sur le Parquet distant (pas de téléchargement de 200 Mo)",
    )
    args = parser.parse_args()

    cibles = args.only or [s for s in SOURCES if s not in args.skip]
    conn = connect_db()
    echecs = []

    for nom in cibles:
        print(f"\n=== {nom} ===")
        try:
            SOURCES[nom](conn, args)
        except Exception:
            echecs.append(nom)
            traceback.print_exc()
            print(f"[{nom}] ÉCHEC — on continue avec les sources suivantes.")

    print("\n=== Provenance (traçabilité) ===")
    for ligne in conn.execute(
        "SELECT source, table_cible, lignes, collecte_le, licence FROM _provenance ORDER BY source"
    ).fetchall():
        print(f"  {ligne[0]:<15} {ligne[1]:<25} {ligne[2]:>9,} lignes  {str(ligne[3])[:16]}  [{ligne[4]}]".replace(",", " "))

    conn.close()
    if echecs:
        print(f"\n{len(echecs)} source(s) en échec : {', '.join(echecs)}")
        return 1
    print("\nIngestion terminée sans erreur.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
