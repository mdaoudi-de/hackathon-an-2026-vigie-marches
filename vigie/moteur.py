"""Moteur d'analyse : orchestre les 6 familles de signaux → Analyse traçable.

Déterministe et explicable : aucune IA ici. Chaque famille est isolée dans un
try/except — une source en panne produit un signal `indisponible` visible,
jamais un échec global.
"""

from __future__ import annotations

import re
import time
import traceback
from datetime import date, datetime, timezone

from ingestion.clients import recherche_entreprise
from vigie import bareme
from vigie.db import Contexte
from vigie.modeles import Analyse, Candidat, Famille, Preuve, ScoreGlobal, Signal
from vigie.signaux import financier, identite, lobbying, procedures, sanctions, track_record


def normaliser_identifiant(saisie: str) -> tuple[str, str | None]:
    """Retourne (siren, siret|None) depuis une saisie SIREN (9) ou SIRET (14)."""
    chiffres = re.sub(r"\D", "", saisie or "")
    if len(chiffres) == 14:
        return chiffres[:9], chiffres
    if len(chiffres) == 9:
        return chiffres, None
    raise ValueError(f"Identifiant invalide : « {saisie} » (attendu SIREN 9 ou SIRET 14 chiffres)")


# ---------- Agrégation (pure, testée sans réseau) ----------


def construire_famille(id_famille: str, signaux: list[Signal]) -> Famille:
    """Somme des points des signaux actifs, plafonnée par famille."""
    points = sum(s.points for s in signaux if s.statut in ("declenche", "a_verifier"))
    return Famille(
        id=id_famille,
        libelle=bareme.LIBELLES_FAMILLES.get(id_famille, id_famille),
        points=min(points, bareme.PLAFOND_FAMILLE),
        plafond=bareme.PLAFOND_FAMILLE,
        signaux=signaux,
    )


def agreger(familles: list[Famille]) -> ScoreGlobal:
    total = min(sum(f.points for f in familles), bareme.PLAFOND_GLOBAL)
    tous = [s for f in familles for s in f.signaux]
    redhibitoire = any(s.gravite == "redhibitoire" and s.statut == "declenche" for s in tous)
    nb_a_verifier = sum(1 for s in tous if s.statut == "a_verifier")
    if redhibitoire or total >= bareme.SEUIL_ROUGE:
        niveau = "ROUGE"
    elif total >= bareme.SEUIL_ORANGE or nb_a_verifier > 0:
        niveau = "ORANGE"
    else:
        niveau = "VERT"
    return ScoreGlobal(
        niveau=niveau,
        points=total,
        plafond=bareme.PLAFOND_GLOBAL,
        version_bareme=bareme.VERSION_BAREME,
        redhibitoire=redhibitoire,
        nb_a_verifier=nb_a_verifier,
    )


# ---------- Analyse complète ----------


def _famille_en_panne(id_famille: str, erreur: Exception) -> Famille:
    return construire_famille(
        id_famille,
        [
            Signal(
                id=f"{id_famille}.erreur",
                libelle=bareme.LIBELLES_FAMILLES.get(id_famille, id_famille),
                statut="indisponible",
                valeur=f"Source momentanément indisponible ({type(erreur).__name__})",
                gravite="info",
                points=0,
                preuve=Preuve(source="erreur technique", url="", collecte_le="n/a"),
            )
        ],
    )


def analyser(siren_ou_siret: str) -> Analyse:
    debut = time.perf_counter()
    siren, siret = normaliser_identifiant(siren_ou_siret)
    ctx = Contexte.ouvrir()
    avert = ctx.avertissements

    # Fiche entreprise récupérée UNE fois, partagée entre familles
    denomination = None
    try:
        reponse = recherche_entreprise(siren)
        ctx.entreprise_url = reponse["source_url"]
        for resultat in reponse["data"].get("results", []):
            if resultat.get("siren") == siren:
                ctx.entreprise = resultat
                break
        if ctx.entreprise:
            denomination = ctx.entreprise.get("nom_complet") or ctx.entreprise.get(
                "nom_raison_sociale"
            )
            siret = siret or (ctx.entreprise.get("siege") or {}).get("siret")
    except Exception:
        avert.append("API Recherche d'entreprises inaccessible : identité non vérifiée en ligne.")
        traceback.print_exc()

    candidat = Candidat(
        siren=siren,
        siret=siret,
        denomination=denomination,
        etat_administratif=(ctx.entreprise or {}).get("etat_administratif"),
        preuve=Preuve(
            source="API Recherche d'entreprises (DINUM)",
            url=ctx.entreprise_url or "https://recherche-entreprises.api.gouv.fr",
            collecte_le=date.today().isoformat(),
            licence="Licence Ouverte 2.0",
        ),
    )

    etapes = [
        ("identite", lambda: identite.evaluer(ctx)),
        ("financier", lambda: financier.evaluer(ctx)),
        ("procedures_collectives", lambda: procedures.evaluer(ctx, siren)),
        ("sanctions_integrite", lambda: sanctions.evaluer(ctx, denomination)),
        ("track_record", lambda: track_record.evaluer(ctx, siren)),
        ("lobbying", lambda: lobbying.evaluer(ctx, siren)),
    ]
    familles = []
    for id_famille, etape in etapes:
        try:
            familles.append(construire_famille(id_famille, etape()))
        except Exception as e:
            avert.append(
                f"Famille « {bareme.LIBELLES_FAMILLES.get(id_famille, id_famille)} » indisponible : {e}"
            )
            familles.append(_famille_en_panne(id_famille, e))

    ctx.fermer()
    return Analyse(
        candidat=candidat,
        score=agreger(familles),
        familles=familles,
        avertissements=avert,
        genere_le=datetime.now(timezone.utc).isoformat(timespec="seconds"),
        duree_ms=int((time.perf_counter() - debut) * 1000),
    )
