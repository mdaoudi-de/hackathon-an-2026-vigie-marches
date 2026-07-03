"""Famille « financier » : capacité économique d'après les comptes publiés.

Source : bloc `finances` de l'API Recherche d'entreprises (ratios issus des
comptes déposés à l'INPI). Absence de comptes = statut `indisponible`,
0 point mais affiché : la transparence sur les trous de données fait partie
du produit.
"""

from __future__ import annotations

from datetime import date

from vigie import bareme
from vigie.db import Contexte
from vigie.modeles import Preuve, Signal

FAMILLE = "financier"


def _preuve(ctx: Contexte, detail: dict | None = None) -> Preuve:
    return Preuve(
        source="API Recherche d'entreprises (DINUM) — ratios financiers INPI",
        url=ctx.entreprise_url or "https://recherche-entreprises.api.gouv.fr",
        collecte_le=date.today().isoformat(),
        licence="Licence Ouverte 2.0",
        detail=detail,
    )


def evaluer(ctx: Contexte) -> list[Signal]:
    e = ctx.entreprise or {}
    finances = e.get("finances") or {}

    if not finances:
        ctx.avertissements.append(
            "Aucun compte publié trouvé : santé financière non évaluable depuis l'Open Data "
            "(demander les liasses au candidat ou consulter l'INPI/RNE avec un compte)."
        )
        return [
            Signal(
                id="financier.comptes",
                libelle="Comptes annuels publiés",
                statut="indisponible",
                valeur="Aucune donnée financière publiée (comptes non déposés ou confidentiels)",
                gravite="info",
                points=0,
                preuve=_preuve(ctx),
            )
        ]

    annees = sorted(finances.keys(), reverse=True)
    derniere = annees[0]
    dern = finances[derniere] or {}
    ca, resultat = dern.get("ca"), dern.get("resultat_net")

    signaux = [
        Signal(
            id="financier.comptes",
            libelle="Comptes annuels publiés",
            statut="ok",
            valeur=f"Dernier exercice publié : {derniere} — CA {ca:,.0f} € , résultat net {resultat:,.0f} €".replace(
                ",", " "
            )
            if ca is not None and resultat is not None
            else f"Dernier exercice publié : {derniere}",
            gravite="info",
            points=0,
            preuve=_preuve(ctx, {"finances": finances}),
        )
    ]

    if int(derniere) < date.today().year - 2:
        signaux.append(
            Signal(
                id="financier.fraicheur",
                libelle="Fraîcheur des comptes",
                statut="declenche",
                valeur=f"Derniers comptes publiés en {derniere} : plus de 2 exercices sans publication",
                gravite="mineur",
                points=bareme.POINTS_GRAVITE["mineur"],
                preuve=_preuve(ctx),
            )
        )

    if resultat is not None and resultat < 0:
        signaux.append(
            Signal(
                id="financier.resultat",
                libelle="Résultat net",
                statut="declenche",
                valeur=f"Résultat net négatif en {derniere} ({resultat:,.0f} €)".replace(",", " "),
                gravite="mineur",
                points=bareme.POINTS_GRAVITE["mineur"],
                preuve=_preuve(ctx),
            )
        )

    if len(annees) >= 2:
        prec = finances[annees[1]] or {}
        ca_prec = prec.get("ca")
        if ca is not None and ca_prec:
            variation = (ca - ca_prec) / ca_prec
            if variation < -bareme.SEUIL_BAISSE_CA:
                signaux.append(
                    Signal(
                        id="financier.ca",
                        libelle="Évolution du chiffre d'affaires",
                        statut="declenche",
                        valeur=f"CA en baisse de {abs(variation):.0%} entre {annees[1]} et {derniere}",
                        gravite="mineur",
                        points=bareme.POINTS_GRAVITE["mineur"],
                        preuve=_preuve(ctx, {"ca": {annees[1]: ca_prec, derniere: ca}}),
                    )
                )

    return signaux
