"""API REST de Vigie Marchés.

Lancement :  .venv\\Scripts\\uvicorn api.main:app --reload
Doc interactive : http://127.0.0.1:8000/docs

Mode démo hors-ligne (jury sans réseau) : VIGIE_OFFLINE=1 sert les analyses
enregistrées dans data/fixtures/ au lieu d'appeler les APIs publiques.
Le contrat de /api/analyses est le modèle `vigie.modeles.Analyse`, identique
en CLI, en HTTP et via le serveur MCP.
"""

from __future__ import annotations

import json
import os
import re

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from api.cache import CacheTTL
from api.schemas import (
    Bareme,
    CandidatResume,
    MarcheResume,
    ProvenanceLigne,
    Sante,
    ScreeningReponse,
    TrackRecordReponse,
)
from ingestion import config
from ingestion.clients import recherche_entreprise
from vigie import bareme
from vigie.db import Contexte, connexion
from vigie.modeles import Analyse
from vigie.moteur import analyser, normaliser_identifiant
from vigie.signaux import sanctions, track_record

OFFLINE = os.environ.get("VIGIE_OFFLINE") == "1"
FIXTURES = config.DATA_DIR / "fixtures"

app = FastAPI(
    title="Vigie Marchés — API",
    version="0.2.0",
    description=(
        "Analyse de candidatures aux marchés publics à partir de données ouvertes : "
        "score de risque **déterministe et explicable** (barème versionné aligné sur les "
        "interdictions de soumissionner, art. L2141 du Code de la commande publique), "
        "chaque signal étant accompagné de sa **preuve** (source, URL, date de collecte, licence). "
        "Outil open source du hackathon de l'Assemblée nationale 2026."
    ),
    license_info={"name": "MIT"},
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

cache_analyses = CacheTTL(ttl_secondes=900)
cache_candidats = CacheTTL(ttl_secondes=900)


@app.get("/api/sante", response_model=Sante, summary="État de l'API et de la base locale")
def sante() -> Sante:
    conn = connexion()
    tables = 0
    if conn is not None:
        tables = conn.execute("SELECT count(*) FROM _provenance").fetchone()[0]
        conn.close()
    return Sante(
        statut="ok",
        mode_offline=OFFLINE,
        base_locale=conn is not None,
        tables_ingerees=tables,
    )


@app.get(
    "/api/candidats",
    response_model=list[CandidatResume],
    summary="Recherche d'entreprises (autocomplétion)",
)
def candidats(
    q: str = Query(min_length=2, description="Nom, SIREN ou SIRET"),
    limite: int = Query(default=8, le=25),
) -> list[CandidatResume]:
    en_cache = cache_candidats.get(q)
    if en_cache is not None:
        return en_cache
    try:
        reponse = recherche_entreprise(q, per_page=limite)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"API Recherche d'entreprises inaccessible : {e}")
    resultats = [
        CandidatResume(
            siren=r.get("siren"),
            denomination=r.get("nom_complet") or r.get("nom_raison_sociale"),
            siret_siege=(r.get("siege") or {}).get("siret"),
            etat_administratif=r.get("etat_administratif"),
            activite_principale=(r.get("siege") or {}).get("activite_principale")
            or r.get("activite_principale"),
            commune=(r.get("siege") or {}).get("libelle_commune"),
        )
        for r in reponse["data"].get("results", [])
    ]
    cache_candidats.set(q, resultats)
    return resultats


@app.get(
    "/api/analyses/{identifiant}",
    response_model=Analyse,
    summary="Analyse complète d'un candidat (l'endpoint principal)",
    description="SIREN (9 chiffres) ou SIRET (14 chiffres). Réponse = contrat JSON du moteur : "
    "score global, 6 familles de signaux, une preuve par signal. Mise en cache 15 min.",
)
def analyse(identifiant: str) -> Analyse:
    chiffres = re.sub(r"\D", "", identifiant)
    try:
        normaliser_identifiant(chiffres)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    if OFFLINE:
        fixture = FIXTURES / f"analyse_{chiffres}.json"
        if fixture.exists():
            return Analyse(**json.loads(fixture.read_text(encoding="utf-8")))
        raise HTTPException(
            status_code=503,
            detail=f"Mode hors-ligne : aucune fixture pour {chiffres} "
            f"(disponibles : {[f.stem for f in FIXTURES.glob('analyse_*.json')]})",
        )

    en_cache = cache_analyses.get(chiffres)
    if en_cache is not None:
        return en_cache
    resultat = analyser(chiffres)
    cache_analyses.set(chiffres, resultat)
    return resultat


@app.get(
    "/api/analyses/{identifiant}/rapport",
    summary="Rapport d'aide à la décision rédigé par Claude",
    description="L'IA ne calcule rien : elle reçoit uniquement le JSON du moteur (score figé) "
    "et le met en forme en citant la source de chaque fait. Nécessite ANTHROPIC_API_KEY "
    "(fichier .env à la racine). Mise en cache 15 min.",
)
def rapport(identifiant: str) -> dict:
    from vigie.rapport import ClefApiManquante, generer_rapport

    chiffres = re.sub(r"\D", "", identifiant)
    cle_cache = f"rapport:{chiffres}"
    en_cache = cache_analyses.get(cle_cache)
    if en_cache is not None:
        return en_cache

    resultat_analyse = analyse(identifiant)  # réutilise cache/offline/422 de l'endpoint principal
    try:
        resultat = generer_rapport(resultat_analyse)
    except ClefApiManquante as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Génération du rapport impossible : {e}")
    cache_analyses.set(cle_cache, resultat)
    return resultat


@app.get(
    "/api/screening/sanctions",
    response_model=ScreeningReponse,
    summary="Screening d'un nom contre les 5 listes de sanctions/exclusions",
    description="Réutilisable hors marchés publics. Matching flou à 3 zones : une correspondance "
    "est toujours « à vérifier », jamais une condamnation automatique.",
)
def screening(nom: str = Query(min_length=3)) -> ScreeningReponse:
    ctx = Contexte.ouvrir()
    try:
        signaux = sanctions.evaluer(ctx, nom)
    finally:
        ctx.fermer()
    return ScreeningReponse(nom=nom, signaux=signaux)


@app.get(
    "/api/track-record/{identifiant}",
    response_model=TrackRecordReponse,
    summary="Historique de marchés publics d'un SIREN/SIRET (DECP)",
)
def track(identifiant: str, limite: int = Query(default=10, le=50)) -> TrackRecordReponse:
    chiffres = re.sub(r"\D", "", identifiant)
    try:
        siren, _ = normaliser_identifiant(chiffres)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    ctx = Contexte.ouvrir()
    try:
        signaux = track_record.evaluer(ctx, siren)
        marches = []
        if ctx.conn is not None:
            lignes = ctx.conn.execute(
                """
                SELECT any_value(uid), any_value(objet), any_value(acheteur_nom),
                       any_value(montant), any_value(dateNotification),
                       any_value(codeCPV), any_value(procedure), any_value(offresRecues)
                FROM decp WHERE titulaire_id LIKE ?
                GROUP BY uid ORDER BY any_value(dateNotification) DESC LIMIT ?
                """,
                [f"{siren}%", limite],
            ).fetchall()
            marches = [
                MarcheResume(
                    uid=l[0],
                    objet=l[1],
                    acheteur_nom=l[2],
                    montant=l[3],
                    date_notification=str(l[4]) if l[4] else None,
                    code_cpv=l[5],
                    procedure=l[6],
                    offres_recues=l[7],
                )
                for l in lignes
            ]
    finally:
        ctx.fermer()
    return TrackRecordReponse(siren=siren, signaux=signaux, derniers_marches=marches)


@app.get(
    "/api/provenance",
    response_model=list[ProvenanceLigne],
    summary="Traçabilité : origine, date et licence de chaque table locale",
)
def provenance_toutes() -> list[ProvenanceLigne]:
    conn = connexion()
    if conn is None:
        raise HTTPException(status_code=503, detail="Base locale absente : lancer l'ingestion.")
    lignes = conn.execute(
        "SELECT source, url, table_cible, lignes, collecte_le, licence, note "
        "FROM _provenance ORDER BY source, table_cible"
    ).fetchall()
    conn.close()
    return [
        ProvenanceLigne(
            source=l[0],
            url=l[1],
            table_cible=l[2],
            lignes=l[3],
            collecte_le=str(l[4]),
            licence=l[5],
            note=l[6],
        )
        for l in lignes
    ]


@app.get(
    "/api/bareme",
    response_model=Bareme,
    summary="Méthodologie du score (barème versionné)",
)
def bareme_actuel() -> Bareme:
    return Bareme(
        version=bareme.VERSION_BAREME,
        description="Barème aligné sur les interdictions de soumissionner du Code de la commande "
        "publique (art. L2141-1 à L2141-5). Un signal rédhibitoire (ex. liquidation judiciaire en "
        "cours) entraîne le niveau ROUGE quel que soit le total de points. Les correspondances sur "
        "les listes de sanctions sont toujours « à vérifier » (matching de noms, homonymies possibles).",
        points_gravite=bareme.POINTS_GRAVITE,
        plafond_famille=bareme.PLAFOND_FAMILLE,
        plafond_global=bareme.PLAFOND_GLOBAL,
        seuils_niveaux={
            "VERT": f"moins de {bareme.SEUIL_ORANGE} points et aucun signal à vérifier",
            "ORANGE": f"{bareme.SEUIL_ORANGE} à {bareme.SEUIL_ROUGE - 1} points, ou au moins un signal à vérifier",
            "ROUGE": f"{bareme.SEUIL_ROUGE} points ou plus, ou un signal rédhibitoire",
        },
        seuils_matching_sanctions={
            "correspondance_forte": f">= {bareme.SEUIL_MATCH_FORT} % de similarité",
            "correspondance_possible": f">= {bareme.SEUIL_MATCH_POSSIBLE} % de similarité",
            "moderation_pays": "un match hors zone FR/UE proche est rétrogradé d'une zone",
        },
        familles=bareme.LIBELLES_FAMILLES,
    )
