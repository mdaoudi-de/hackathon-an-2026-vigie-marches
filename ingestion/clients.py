"""Clients des APIs interrogées à la demande (par candidat, au moment de l'analyse).

Ces sources ne s'ingèrent pas en masse (millions de lignes, données du jour) :
on les interroge par SIREN/SIRET quand une candidature est analysée.
Chaque fonction retourne le JSON brut de l'API + l'URL appelée (traçabilité).

Rate limits à respecter (vérifiés) :
- recherche-entreprises : 7 req/s/IP (429 + Retry-After au-delà)
- API tabulaire data.gouv : page_size max 50
"""

from __future__ import annotations

from typing import Any

from ingestion import config
from ingestion.common import get_session

_session = None


def _s():
    global _session
    if _session is None:
        _session = get_session()
    return _session


def _get(url: str, params: dict | None = None) -> dict[str, Any]:
    r = _s().get(url, params=params, timeout=60)
    r.raise_for_status()
    return {"source_url": r.url, "data": r.json()}


def recherche_entreprise(q: str, page: int = 1, per_page: int = 10) -> dict:
    """Identité, dirigeants, finances (CA/résultat), labels — par nom, SIREN ou SIRET.

    ⚠️ Ne contient PAS les procédures collectives : utiliser bodacc_annonces().
    """
    return _get(config.RECHERCHE_ENTREPRISES, {"q": q, "page": page, "per_page": per_page})


def bodacc_annonces(siren: str, famille: str | None = None, limit: int = 20) -> dict:
    """Annonces BODACC d'un SIREN. `famille` ex. : "Procédures collectives", "Radiations"."""
    where = f'registre like "{siren}"'
    if famille:
        where += f' and familleavis_lib="{famille}"'
    return _get(
        config.BODACC_RECORDS,
        {"where": where, "order_by": "dateparution desc", "limit": limit},
    )


def decp_marches_par_siret(siret: str, page_size: int = 50, page: int = 1) -> dict:
    """Marchés publics remportés par un SIRET (API tabulaire, sans téléchargement).

    Équivalent en local (plus riche) : table `decp` / vue `v_decp_stats_titulaire`.
    """
    return _get(
        config.DECP_TABULAR,
        {"titulaire_id__exact": siret, "page_size": page_size, "page": page},
    )


def boamp_avis(recherche_odsql: str, limit: int = 20) -> dict:
    """Avis BOAMP via clause ODSQL. Ex. : 'nature="ATTRIBUTION" and dateparution>="2026-01-01"'.

    ⚠️ ODSQL : préfixe avec joker `like "35*"` (pas `like "35"`).
    """
    return _get(
        config.BOAMP_RECORDS,
        {"where": recherche_odsql, "order_by": "dateparution desc", "limit": limit},
    )


def ted_recherche(query: str, fields: list[str] | None = None, limit: int = 10) -> dict:
    """Marchés européens TED (POST, sans clé). Syntaxe expert query.

    Ex. : 'buyer-country=FRA AND publication-date>20260101'
    """
    r = _s().post(
        config.TED_SEARCH,
        json={
            "query": query,
            "fields": fields or ["publication-number", "notice-title", "buyer-name", "publication-date"],
            "limit": limit,
        },
        timeout=60,
    )
    r.raise_for_status()
    return {"source_url": config.TED_SEARCH, "data": r.json()}
