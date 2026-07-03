"""Famille « identité » : existence légale et conformité administrative de base.

Source : API Recherche d'entreprises (la fiche est récupérée une fois par le
moteur et partagée via le Contexte).
"""

from __future__ import annotations

from datetime import date

from vigie import bareme
from vigie.db import Contexte
from vigie.modeles import Preuve, Signal

FAMILLE = "identite"


def _preuve(ctx: Contexte, detail: dict | None = None) -> Preuve:
    return Preuve(
        source="API Recherche d'entreprises (DINUM)",
        url=ctx.entreprise_url or "https://recherche-entreprises.api.gouv.fr",
        collecte_le=date.today().isoformat(),
        licence="Licence Ouverte 2.0",
        detail=detail,
    )


def evaluer(ctx: Contexte) -> list[Signal]:
    e = ctx.entreprise
    if e is None:
        ctx.avertissements.append(
            "Entreprise introuvable dans l'API Recherche d'entreprises : "
            "identité non vérifiable, vérification manuelle indispensable."
        )
        return [
            Signal(
                id="identite.existence",
                libelle="Existence dans le répertoire des entreprises",
                statut="a_verifier",
                valeur="Aucune entreprise trouvée pour cet identifiant",
                gravite="majeur",
                points=bareme.POINTS_GRAVITE["majeur"],
                preuve=_preuve(ctx),
            )
        ]

    signaux = [
        Signal(
            id="identite.existence",
            libelle="Existence dans le répertoire des entreprises",
            statut="ok",
            valeur=f"{e.get('nom_complet', '?')} — SIREN {e.get('siren')}",
            gravite="info",
            points=0,
            preuve=_preuve(ctx, {"nombre_etablissements": e.get("nombre_etablissements")}),
        )
    ]

    etat = e.get("etat_administratif")
    if etat and etat != "A":
        signaux.append(
            Signal(
                id="identite.etat",
                libelle="État administratif",
                statut="declenche",
                valeur="Entreprise administrativement cessée (état "
                f"« {etat} ») : elle ne peut pas exécuter un marché",
                gravite="majeur",
                points=bareme.POINTS_GRAVITE["majeur"],
                preuve=_preuve(ctx, {"etat_administratif": etat}),
            )
        )
    else:
        signaux.append(
            Signal(
                id="identite.etat",
                libelle="État administratif",
                statut="ok",
                valeur="Entreprise active",
                gravite="info",
                points=0,
                preuve=_preuve(ctx),
            )
        )

    creation = e.get("date_creation")
    if creation:
        try:
            annees = (date.today() - date.fromisoformat(creation)).days / 365.25
            if annees < 1:
                signaux.append(
                    Signal(
                        id="identite.anciennete",
                        libelle="Ancienneté",
                        statut="declenche",
                        valeur=f"Entreprise créée il y a moins d'un an ({creation}) : "
                        "capacités difficilement vérifiables",
                        gravite="mineur",
                        points=bareme.POINTS_GRAVITE["mineur"],
                        preuve=_preuve(ctx, {"date_creation": creation}),
                    )
                )
            else:
                signaux.append(
                    Signal(
                        id="identite.anciennete",
                        libelle="Ancienneté",
                        statut="ok",
                        valeur=f"Créée le {creation} ({annees:.0f} ans d'existence)",
                        gravite="info",
                        points=0,
                        preuve=_preuve(ctx),
                    )
                )
        except ValueError:
            pass

    return signaux
