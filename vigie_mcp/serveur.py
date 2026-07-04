"""Serveur MCP « vigie-marches » — l'analyse de candidats exposée en outils agentiques.

Le livrable différenciant du hackathon : aucun serveur MCP DECP/BODACC n'existait.
Ce serveur expose le MÊME moteur déterministe que la CLI et l'API REST : un agent
IA (Claude…) peut instruire un dossier de candidature en enchaînant les outils,
chaque résultat portant ses preuves (source, URL, date, licence).

Lancement (stdio) :  python -m vigie_mcp.serveur
Déclaré dans le .mcp.json du projet pour Claude Code.
"""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

mcp = FastMCP(
    "vigie-marches",
    instructions=(
        "Outils d'analyse des candidats aux marchés publics français, fondés sur des "
        "données ouvertes (DECP, BODACC, sanctions, HATVP…). Le score est déterministe "
        "et explicable : chaque signal porte une preuve (source, URL, date de collecte). "
        "Une correspondance sur une liste de sanctions est TOUJOURS « à vérifier » "
        "(homonymies possibles) : ne jamais la présenter comme une condamnation. "
        "Outil d'entrée recommandé : analyser_candidat."
    ),
)


@mcp.tool()
def analyser_candidat(siren_ou_siret: str) -> dict:
    """Analyse complète d'un candidat à un marché public (l'outil principal).

    Croise 6 familles de signaux : identité/conformité (Recherche d'entreprises),
    santé financière, procédures collectives et radiations (BODACC), sanctions et
    intégrité (gels des avoirs, UE, EDES, Banque mondiale), historique de marchés
    publics (DECP, 3,1 M de marchés) et liens d'intérêts (répertoire HATVP).

    Args:
        siren_ou_siret: SIREN (9 chiffres) ou SIRET (14 chiffres), espaces acceptés.

    Returns:
        Score global (VERT/ORANGE/ROUGE, points, barème versionné, rédhibitoire),
        familles de signaux avec preuves, avertissements. Un niveau ROUGE avec
        `redhibitoire=true` signale un motif d'interdiction de soumissionner
        (art. L2141 du Code de la commande publique) à instruire par l'acheteur.
    """
    from vigie.moteur import analyser

    return analyser(siren_ou_siret).model_dump()


@mcp.tool()
def screening_sanctions(nom: str) -> dict:
    """Screening d'un nom (entreprise ou personne) contre 5 listes de sanctions/exclusions.

    Listes locales : registre national des gels des avoirs (DG Trésor), sanctions
    financières de l'UE (FSF), exclusions du budget de l'UE (EDES) et exclusions
    Banque mondiale. Matching flou à 3 zones avec gestion des homonymies : une
    correspondance est un point de vérification manuelle, jamais une conclusion.

    Args:
        nom: Dénomination sociale ou nom de personne (3 caractères minimum).
    """
    from vigie.db import Contexte
    from vigie.signaux import sanctions

    ctx = Contexte.ouvrir()
    try:
        signaux = sanctions.evaluer(ctx, nom)
    finally:
        ctx.fermer()
    return {"nom": nom, "signaux": [s.model_dump() for s in signaux]}


@mcp.tool()
def track_record_marches(siren_ou_siret: str, limite: int = 10) -> dict:
    """Historique de marchés publics d'une entreprise dans les DECP consolidées.

    Statistiques agrégées (nombre de marchés, montant cumulé, acheteurs distincts,
    part de marchés remportés en offre unique) + liste des derniers marchés
    (objet, acheteur, montant, CPV, procédure, offres reçues).

    Args:
        siren_ou_siret: SIREN ou SIRET de l'entreprise.
        limite: Nombre de derniers marchés à détailler (max 50).
    """
    from vigie.db import Contexte
    from vigie.moteur import normaliser_identifiant
    from vigie.signaux import track_record

    siren, _ = normaliser_identifiant(siren_ou_siret)
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
                [f"{siren}%", min(limite, 50)],
            ).fetchall()
            marches = [
                {
                    "uid": l[0],
                    "objet": l[1],
                    "acheteur": l[2],
                    "montant": l[3],
                    "date_notification": str(l[4]) if l[4] else None,
                    "code_cpv": l[5],
                    "procedure": l[6],
                    "offres_recues": l[7],
                }
                for l in lignes
            ]
    finally:
        ctx.fermer()
    return {
        "siren": siren,
        "signaux": [s.model_dump() for s in signaux],
        "derniers_marches": marches,
    }


@mcp.tool()
def rechercher_entreprise(recherche: str) -> dict:
    """Recherche d'entreprises françaises par nom, SIREN ou SIRET (autocomplétion).

    Interroge l'API Recherche d'entreprises (DINUM). Utile pour trouver le SIREN
    d'un candidat avant d'appeler analyser_candidat.

    Args:
        recherche: Nom d'entreprise, SIREN ou SIRET (3 caractères minimum).
    """
    from ingestion.clients import recherche_entreprise as chercher

    reponse = chercher(recherche, per_page=8)
    return {
        "source_url": reponse["source_url"],
        "resultats": [
            {
                "siren": r.get("siren"),
                "denomination": r.get("nom_complet"),
                "siret_siege": (r.get("siege") or {}).get("siret"),
                "etat_administratif": r.get("etat_administratif"),
                "commune": (r.get("siege") or {}).get("libelle_commune"),
            }
            for r in reponse["data"].get("results", [])
        ],
    }


@mcp.tool()
def sources_donnees() -> dict:
    """Traçabilité : origine, date de collecte, volume et licence de chaque table locale.

    Permet à l'agent de citer précisément ses sources dans un rapport (exigence de
    transparence du sujet). Retourne le contenu de la table _provenance.
    """
    from vigie.db import connexion

    conn = connexion()
    if conn is None:
        return {"erreur": "Base locale absente : exécuter `python -m ingestion.ingest_all`."}
    lignes = conn.execute(
        "SELECT source, url, table_cible, lignes, collecte_le, licence, note "
        "FROM _provenance ORDER BY source, table_cible"
    ).fetchall()
    conn.close()
    return {
        "tables": [
            {
                "source": l[0],
                "url": l[1],
                "table": l[2],
                "lignes": l[3],
                "collecte_le": str(l[4]),
                "licence": l[5],
                "note": l[6],
            }
            for l in lignes
        ]
    }


if __name__ == "__main__":
    mcp.run()
