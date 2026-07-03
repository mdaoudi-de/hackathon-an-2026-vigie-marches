"""Accès en LECTURE SEULE à la base data/vigie.duckdb + contexte d'analyse.

Toutes les connexions du moteur sont read_only : aucune écriture hors ingestion
(DuckDB est mono-écrivain). Si la base est absente, le moteur dégrade proprement
(signaux locaux « indisponible ») au lieu d'échouer.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

import duckdb
import requests

from ingestion import config
from ingestion.common import get_session


def connexion() -> Optional[duckdb.DuckDBPyConnection]:
    """Connexion read-only, ou None si la base n'a pas encore été ingérée."""
    if not config.DB_PATH.exists():
        return None
    return duckdb.connect(str(config.DB_PATH), read_only=True)


def provenance(conn: duckdb.DuckDBPyConnection, table: str) -> dict[str, Any]:
    """Métadonnées de traçabilité d'une table locale (alimente les Preuves)."""
    ligne = conn.execute(
        "SELECT source, url, collecte_le, licence FROM _provenance WHERE table_cible = ?",
        [table],
    ).fetchone()
    if not ligne:
        return {"source": table, "url": "", "collecte_le": "inconnue", "licence": None}
    return {
        "source": ligne[0],
        "url": ligne[1],
        "collecte_le": str(ligne[2]),
        "licence": ligne[3],
    }


@dataclass
class Contexte:
    """Ressources partagées par les modules de signaux pendant UNE analyse."""

    conn: Optional[duckdb.DuckDBPyConnection]
    session: requests.Session
    # Fiche recherche-entreprises (récupérée une seule fois par le moteur)
    entreprise: Optional[dict] = None
    entreprise_url: str = ""
    avertissements: list[str] = field(default_factory=list)

    @classmethod
    def ouvrir(cls) -> "Contexte":
        return cls(conn=connexion(), session=get_session())

    def fermer(self) -> None:
        if self.conn is not None:
            self.conn.close()
