"""Famille « liens d'intérêts » : inscription au répertoire HATVP.

Source : vue locale `v_lobbying` (répertoire des représentants d'intérêts via
l'API Tricoteuses Parlement — ressource imposée du hackathon). Être inscrit au
registre du lobbying est LÉGAL et n'est PAS un risque : signal informatif
0 point, présenté comme élément de vigilance déontologique pour l'acheteur.
"""

from __future__ import annotations

from vigie.db import Contexte, provenance
from vigie.modeles import Preuve, Signal

FAMILLE = "lobbying"


def evaluer(ctx: Contexte, siren: str) -> list[Signal]:
    if ctx.conn is None:
        return [
            Signal(
                id="lobbying.base",
                libelle="Répertoire HATVP des représentants d'intérêts",
                statut="indisponible",
                valeur="Base locale non disponible — exécuter `python -m ingestion.ingest_all`",
                gravite="info",
                points=0,
                preuve=Preuve(source="base locale vigie.duckdb", url="", collecte_le="n/a"),
            )
        ]

    prov = provenance(ctx.conn, "hatvp_representants")
    preuve_base = dict(
        source=prov["source"] + " — répertoire HATVP via API Tricoteuses Parlement",
        url=prov["url"],
        collecte_le=prov["collecte_le"],
        licence=prov["licence"],
    )

    ligne = ctx.conn.execute(
        "SELECT denomination, categorie, dateDernierePublicationActivite FROM v_lobbying WHERE siren = ?",
        [siren],
    ).fetchone()

    if ligne:
        return [
            Signal(
                id="lobbying.hatvp",
                libelle="Répertoire HATVP des représentants d'intérêts",
                statut="declenche",
                valeur=(
                    f"Inscrit au répertoire des représentants d'intérêts ({ligne[1]}), "
                    f"dernière activité publiée le {str(ligne[2])[:10]}. "
                    "Élément de vigilance déontologique (pas un risque en soi) : "
                    "vérifier l'absence de lien avec l'acheteur ou les élus concernés."
                ),
                gravite="info",
                points=0,
                preuve=Preuve(**preuve_base, detail={"denomination": ligne[0]}),
            )
        ]
    return [
        Signal(
            id="lobbying.hatvp",
            libelle="Répertoire HATVP des représentants d'intérêts",
            statut="ok",
            valeur="Non inscrit au répertoire des représentants d'intérêts (3 718 SIREN contrôlés)",
            gravite="info",
            points=0,
            preuve=Preuve(**preuve_base),
        )
    ]
