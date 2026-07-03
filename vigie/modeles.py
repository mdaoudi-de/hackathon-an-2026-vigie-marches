"""Modèles Pydantic du moteur d'analyse.

Ces modèles SONT le contrat de sortie : ils servent tels quels de schémas
FastAPI (Run 2) et de format d'échange pour le front, le rapport IA et le
serveur MCP. Règle absolue : aucun Signal sans Preuve.
"""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import BaseModel, Field

Statut = Literal["ok", "declenche", "a_verifier", "indisponible"]
Gravite = Literal["info", "mineur", "majeur", "redhibitoire"]
Niveau = Literal["VERT", "ORANGE", "ROUGE"]


class Preuve(BaseModel):
    """Traçabilité d'un signal : d'où vient l'information, quand, sous quelle licence."""

    source: str = Field(description="Nom de la source (ex. « BODACC — annonces commerciales »)")
    url: str = Field(description="URL exacte consultée ou de référence")
    collecte_le: str = Field(description="Date/heure de collecte ISO 8601")
    licence: Optional[str] = None
    detail: Optional[dict[str, Any]] = Field(
        default=None, description="Données brutes utiles à la vérification manuelle"
    )


class Signal(BaseModel):
    id: str = Field(description="Identifiant stable, ex. « procedures.liquidation »")
    libelle: str
    statut: Statut
    valeur: str = Field(description="Constat en français, lisible par l'acheteur")
    gravite: Gravite = "info"
    points: int = 0
    preuve: Preuve


class Famille(BaseModel):
    id: str
    libelle: str
    points: int
    plafond: int
    signaux: list[Signal]


class ScoreGlobal(BaseModel):
    niveau: Niveau
    points: int
    plafond: int
    version_bareme: str
    redhibitoire: bool
    nb_a_verifier: int


class Candidat(BaseModel):
    siren: str
    siret: Optional[str] = None
    denomination: Optional[str] = None
    etat_administratif: Optional[str] = Field(
        default=None, description="A = actif, C/F = cessé (source Recherche d'entreprises)"
    )
    preuve: Optional[Preuve] = None


class Analyse(BaseModel):
    candidat: Candidat
    score: ScoreGlobal
    familles: list[Famille]
    avertissements: list[str]
    genere_le: str
    duree_ms: int
