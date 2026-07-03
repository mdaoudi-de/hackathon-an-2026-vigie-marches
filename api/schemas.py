"""Schémas propres à l'API (le contrat d'analyse vit dans vigie/modeles.py)."""

from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field

from vigie.modeles import Signal


class Sante(BaseModel):
    statut: str
    mode_offline: bool
    base_locale: bool
    tables_ingerees: int


class CandidatResume(BaseModel):
    siren: str
    denomination: Optional[str] = None
    siret_siege: Optional[str] = None
    etat_administratif: Optional[str] = None
    activite_principale: Optional[str] = None
    commune: Optional[str] = None


class ScreeningReponse(BaseModel):
    nom: str
    signaux: list[Signal] = Field(description="Un signal par liste contrôlée, avec preuves")


class MarcheResume(BaseModel):
    uid: Optional[str] = None
    objet: Optional[str] = None
    acheteur_nom: Optional[str] = None
    montant: Optional[float] = None
    date_notification: Optional[str] = None
    code_cpv: Optional[str] = None
    procedure: Optional[str] = None
    offres_recues: Optional[float] = None


class TrackRecordReponse(BaseModel):
    siren: str
    signaux: list[Signal]
    derniers_marches: list[MarcheResume]


class ProvenanceLigne(BaseModel):
    source: str
    url: str
    table_cible: str
    lignes: int
    collecte_le: str
    licence: Optional[str] = None
    note: Optional[str] = None


class Bareme(BaseModel):
    version: str
    description: str
    points_gravite: dict[str, int]
    plafond_famille: int
    plafond_global: int
    seuils_niveaux: dict[str, Any]
    seuils_matching_sanctions: dict[str, Any]
    familles: dict[str, str]
