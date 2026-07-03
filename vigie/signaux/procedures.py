"""Famille « procédures collectives » : le signal juridique le plus dur.

Source : BODACC (annonces commerciales, DILA) — c'est LA donnée absente de
l'API Recherche d'entreprises (vérifié). Une liquidation judiciaire en cours
est une interdiction de soumissionner (art. L2141-3 CCP) : rédhibitoire.
"""

from __future__ import annotations

from datetime import date

from ingestion.clients import bodacc_annonces
from vigie import bareme
from vigie.db import Contexte
from vigie.modeles import Preuve, Signal

FAMILLE = "procedures_collectives"

# nature de jugement (minuscules) -> (gravité, résumé)
NATURES = [
    ("liquidation", ("redhibitoire", "liquidation judiciaire")),
    ("redressement", ("majeur", "redressement judiciaire")),
    ("sauvegarde", ("mineur", "procédure de sauvegarde")),
]


def _jugement_texte(annonce: dict) -> str:
    jugement = annonce.get("jugement")
    if isinstance(jugement, dict):
        return " ".join(str(v) for v in jugement.values() if v)
    return str(jugement or "")


def evaluer(ctx: Contexte, siren: str) -> list[Signal]:
    reponse = bodacc_annonces(siren, famille="Procédures collectives", limit=20)
    annonces = reponse["data"].get("results", [])
    preuve_base = dict(
        source="BODACC — annonces commerciales (DILA)",
        url=reponse["source_url"],
        collecte_le=date.today().isoformat(),
        licence="etalab-2.0",
    )

    signaux: list[Signal] = []
    if not annonces:
        signaux.append(
            Signal(
                id="procedures.collectives",
                libelle="Procédures collectives (BODACC)",
                statut="ok",
                valeur="Aucune procédure collective publiée au BODACC",
                gravite="info",
                points=0,
                preuve=Preuve(**preuve_base),
            )
        )
    else:
        # L'annonce la plus récente donne l'état courant de la procédure
        recentes = sorted(annonces, key=lambda a: a.get("dateparution") or "", reverse=True)
        derniere = recentes[0]
        texte = _jugement_texte(derniere).lower()
        gravite, resume = "mineur", "procédure collective"
        for motif, (g, r) in NATURES:
            if motif in texte:
                gravite, resume = g, r
                break
        cloturee = "clôture" in texte or "cloture" in texte
        if cloturee:
            gravite = "mineur"
        signaux.append(
            Signal(
                id="procedures.collectives",
                libelle="Procédures collectives (BODACC)",
                statut="declenche",
                valeur=(
                    f"{len(annonces)} annonce(s) de procédure collective — dernière : {resume}"
                    f" (parution {derniere.get('dateparution')})"
                    + (" — procédure clôturée" if cloturee else "")
                    + (
                        " ⇒ interdiction de soumissionner, art. L2141-3 du Code de la commande publique"
                        if gravite == "redhibitoire"
                        else ""
                    )
                ),
                gravite=gravite,
                points=bareme.POINTS_GRAVITE[gravite],
                preuve=Preuve(
                    **preuve_base,
                    detail={
                        "derniere_annonce": {
                            "dateparution": derniere.get("dateparution"),
                            "tribunal": derniere.get("tribunal"),
                            "jugement": derniere.get("jugement"),
                        }
                    },
                ),
            )
        )

    # Radiations du RCS
    rep_rad = bodacc_annonces(siren, famille="Radiations", limit=5)
    radiations = rep_rad["data"].get("results", [])
    if radiations:
        derniere_rad = radiations[0]
        signaux.append(
            Signal(
                id="procedures.radiation",
                libelle="Radiation du RCS (BODACC)",
                statut="declenche",
                valeur=f"Radiation publiée au BODACC (parution {derniere_rad.get('dateparution')})",
                gravite="majeur",
                points=bareme.POINTS_GRAVITE["majeur"],
                preuve=Preuve(
                    source="BODACC — annonces commerciales (DILA)",
                    url=rep_rad["source_url"],
                    collecte_le=date.today().isoformat(),
                    licence="etalab-2.0",
                    detail={"dateparution": derniere_rad.get("dateparution")},
                ),
            )
        )

    return signaux
