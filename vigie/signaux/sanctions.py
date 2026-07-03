"""Famille « sanctions et intégrité » : screening contre les 5 listes locales.

Listes (ingérées, tracées dans `_provenance`) : gels des avoirs (DG Trésor),
sanctions financières UE (FSF), EDES, exclusions Banque mondiale, miroir EDES.

Principe assumé : les listes n'ont pas de SIREN → matching flou sur les noms
(rapidfuzz) avec 3 zones de similarité. Une correspondance produit TOUJOURS un
statut `a_verifier` (jamais un rouge automatique) : l'outil ne condamne pas,
il dit à l'acheteur ce qu'il doit vérifier. Les personnes physiques des listes
sont comparées aux dirigeants, pas à la raison sociale.
"""

from __future__ import annotations

import re
import unicodedata
from typing import Optional

from rapidfuzz import fuzz, process

from vigie import bareme
from vigie.db import Contexte, provenance
from vigie.modeles import Preuve, Signal

FAMILLE = "sanctions_integrite"


# ---------- Fonctions pures (testées sans réseau ni base) ----------


def normaliser(nom: str) -> str:
    """Majuscules, sans accents ni ponctuation, sans formes juridiques."""
    nom = unicodedata.normalize("NFKD", nom or "")
    nom = "".join(c for c in nom if not unicodedata.combining(c)).upper()
    nom = nom.replace(".", "")  # « S.A.S. » -> « SAS » (sinon éclaté en lettres isolées)
    nom = re.sub(r"[^A-Z0-9 ]+", " ", nom)
    mots = [m for m in nom.split() if m not in bareme.STOP_WORDS_DENOMINATION]
    return " ".join(mots) if mots else nom.strip()


def classer(similarite: float, pays: Optional[str] = None) -> Optional[str]:
    """Zone de correspondance : 'fort', 'possible' ou None (ignoré).

    Un match dans un pays éloigné (listes qui portent le pays) est rétrogradé
    d'une zone : limite les homonymies internationales.
    """
    if similarite >= bareme.SEUIL_MATCH_FORT:
        zone = "fort"
    elif similarite >= bareme.SEUIL_MATCH_POSSIBLE:
        zone = "possible"
    else:
        return None
    if pays and pays.strip().lower() not in bareme.PAYS_PROCHES:
        return "possible" if zone == "fort" else None
    return zone


def zone_correspondance(
    sim_inclusion: float, sim_stricte: float, pays: Optional[str] = None
) -> Optional[str]:
    """Combine deux similarités : inclusion de tokens (token_set) et stricte (token_sort).

    « ROSNEFT » doit matcher « ROSNEFT OIL COMPANY » (inclusion = 100) alors que
    la comparaison stricte échoue (~54). Mais une correspondance PAR INCLUSION
    SEULE est rétrogradée d'une zone : un nom court inclus dans un nom long
    reste une piste, pas une quasi-identité.
    """
    zone = classer(sim_inclusion, pays)
    if zone == "fort" and sim_stricte < bareme.SEUIL_MATCH_POSSIBLE:
        zone = "possible"
    return zone


# ---------- Chargement des listes locales ----------

# (table, requête -> [nom, pays, motif], cible du matching : 'pm' raison sociale / 'pp' personnes)
LISTES = [
    (
        "gels_avoirs",
        """SELECT CASE WHEN nature = 'Personne physique' AND prenom IS NOT NULL
                       THEN prenom || ' ' || nom ELSE nom END,
                  NULL,
                  coalesce(motifs, fondement_juridique),
                  CASE WHEN nature = 'Personne physique' THEN 'pp' ELSE 'pm' END
           FROM gels_avoirs WHERE nom IS NOT NULL""",
    ),
    (
        "eu_fsf",
        """SELECT DISTINCT NameAlias_WholeName, NULL, Entity_Remark,
                  CASE WHEN lower(Entity_SubjectType) LIKE '%person%' THEN 'pp' ELSE 'pm' END
           FROM eu_fsf WHERE NameAlias_WholeName IS NOT NULL""",
    ),
    (
        "edes",
        "SELECT nom, code_pays, base_legale, 'pm' FROM edes WHERE nom IS NOT NULL",
    ),
    (
        "os_worldbank_debarred",
        "SELECT name, countries, sanctions, 'pm' FROM os_worldbank_debarred WHERE name IS NOT NULL",
    ),
    (
        "os_eu_edes",
        "SELECT name, countries, sanctions, 'pm' FROM os_eu_edes WHERE name IS NOT NULL",
    ),
]

LIBELLES_LISTES = {
    "gels_avoirs": "Registre national des gels des avoirs (DG Trésor)",
    "eu_fsf": "Sanctions financières de l'UE (liste consolidée FSF)",
    "edes": "Exclusions du budget de l'UE (EDES)",
    "os_worldbank_debarred": "Exclusions Banque mondiale (miroir OpenSanctions)",
    "os_eu_edes": "Exclusions EDES (miroir OpenSanctions)",
}


# Requêtes de repli si une colonne optionnelle manque (schémas susceptibles d'évoluer)
FALLBACKS = {
    "eu_fsf": "SELECT DISTINCT NameAlias_WholeName, NULL, NULL, 'pm' FROM eu_fsf "
    "WHERE NameAlias_WholeName IS NOT NULL",
    "gels_avoirs": "SELECT nom, NULL, NULL, 'pm' FROM gels_avoirs WHERE nom IS NOT NULL",
    "os_worldbank_debarred": "SELECT name, NULL, NULL, 'pm' FROM os_worldbank_debarred "
    "WHERE name IS NOT NULL",
    "os_eu_edes": "SELECT name, NULL, NULL, 'pm' FROM os_eu_edes WHERE name IS NOT NULL",
    "edes": "SELECT nom, NULL, NULL, 'pm' FROM edes WHERE nom IS NOT NULL",
}


def _charger(conn, table: str, requete: str) -> list[tuple]:
    """[(nom_normalisé, nom_original, pays, motif, cible)] pour une liste donnée."""
    try:
        brut = conn.execute(requete).fetchall()
    except Exception:
        brut = conn.execute(FALLBACKS[table]).fetchall()
    lignes = []
    for nom, pays, motif, type_cible in brut:
        norme = normaliser(str(nom))
        if norme:
            lignes.append((norme, str(nom), pays, motif, type_cible))
    return lignes


def _matcher(requete_norm: str, entries: list, cible: str) -> list[dict]:
    """Matches d'un nom normalisé contre les entrées d'une liste (zone non nulle)."""
    if not requete_norm:
        return []
    choix = [e[0] for e in entries if (e[4] or "pm") == cible]
    metas = [e for e in entries if (e[4] or "pm") == cible]
    resultats = process.extract(
        requete_norm,
        choix,
        scorer=fuzz.token_set_ratio,  # tolère l'inclusion : « ROSNEFT » ⊂ « ROSNEFT OIL COMPANY »
        score_cutoff=bareme.SEUIL_MATCH_POSSIBLE,
        limit=5,
    )
    matches = []
    for nom_norm, sim_inclusion, idx in resultats:
        _, original, pays, motif, _ = metas[idx]
        sim_stricte = fuzz.token_sort_ratio(requete_norm, nom_norm)
        zone = zone_correspondance(sim_inclusion, sim_stricte, pays)
        if zone:
            matches.append(
                {
                    "nom_liste": original,
                    "similarite": round(sim_inclusion, 1),
                    "similarite_stricte": round(sim_stricte, 1),
                    "zone": zone,
                    "pays": pays,
                    "motif": (str(motif)[:300] if motif else None),
                }
            )
    return matches


def evaluer(ctx: Contexte, denomination: Optional[str]) -> list[Signal]:
    if ctx.conn is None:
        ctx.avertissements.append(
            "Base locale absente : screening sanctions non réalisé (lancer l'ingestion)."
        )
        return [
            Signal(
                id="sanctions.base",
                libelle="Screening sanctions et intégrité",
                statut="indisponible",
                valeur="Base locale non disponible — exécuter `python -m ingestion.ingest_all`",
                gravite="info",
                points=0,
                preuve=Preuve(source="base locale vigie.duckdb", url="", collecte_le="n/a"),
            )
        ]

    denom_norm = normaliser(denomination or "")
    dirigeants = []
    for d in (ctx.entreprise or {}).get("dirigeants", []):
        if d.get("type_dirigeant") == "personne physique" or d.get("nom"):
            nom_complet = f"{d.get('prenoms') or ''} {d.get('nom') or ''}".strip()
            if nom_complet:
                dirigeants.append(nom_complet)

    signaux: list[Signal] = []
    for table, requete in LISTES:
        entries = _charger(ctx.conn, table, requete)
        prov = provenance(ctx.conn, table)
        preuve_base = dict(
            source=prov["source"] + f" — {LIBELLES_LISTES.get(table, table)}",
            url=prov["url"],
            collecte_le=prov["collecte_le"],
            licence=prov["licence"],
        )

        matches = [
            {"cible": f"entreprise « {denomination} »", **m}
            for m in _matcher(denom_norm, entries, "pm")
        ]
        for dirigeant in dirigeants:
            matches += [
                {"cible": f"dirigeant {dirigeant}", **m}
                for m in _matcher(normaliser(dirigeant), entries, "pp")
            ]

        if matches:
            pire = max(matches, key=lambda m: m["similarite"])
            gravite = "majeur" if pire["zone"] == "fort" else "mineur"
            signaux.append(
                Signal(
                    id=f"sanctions.{table}",
                    libelle=LIBELLES_LISTES.get(table, table),
                    statut="a_verifier",
                    valeur=(
                        f"{len(matches)} correspondance(s) de nom — la plus proche : "
                        f"« {pire['nom_liste']} » ({pire['similarite']} % avec {pire['cible']})."
                        " Homonymie possible : vérification manuelle requise, l'outil ne conclut pas."
                    ),
                    gravite=gravite,
                    points=bareme.POINTS_GRAVITE[gravite],
                    preuve=Preuve(**preuve_base, detail={"correspondances": matches}),
                )
            )
        else:
            signaux.append(
                Signal(
                    id=f"sanctions.{table}",
                    libelle=LIBELLES_LISTES.get(table, table),
                    statut="ok",
                    valeur=f"Aucune correspondance ≥ {bareme.SEUIL_MATCH_POSSIBLE} % "
                    f"sur {len(entries):,} entrées contrôlées".replace(",", " "),
                    gravite="info",
                    points=0,
                    preuve=Preuve(**preuve_base),
                )
            )
    return signaux
