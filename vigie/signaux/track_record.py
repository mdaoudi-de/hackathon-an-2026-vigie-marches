"""Famille « track-record » : l'expérience réelle du candidat dans les DECP.

Source : table locale `decp` (3,1 M de marchés, consolidation quotidienne).
La requête porte sur tous les établissements du SIREN (titulaire_id LIKE
'siren%'). L'absence d'historique n'est PAS un risque (info) ; les anomalies
ne sont évaluées qu'à partir de NB_MARCHES_MIN marchés (données déclaratives).
"""

from __future__ import annotations

from vigie import bareme
from vigie.db import Contexte, provenance
from vigie.modeles import Preuve, Signal

FAMILLE = "track_record"


def evaluer(ctx: Contexte, siren: str) -> list[Signal]:
    if ctx.conn is None:
        return [
            Signal(
                id="track_record.base",
                libelle="Historique de marchés publics (DECP)",
                statut="indisponible",
                valeur="Base locale non disponible — exécuter `python -m ingestion.ingest_all`",
                gravite="info",
                points=0,
                preuve=Preuve(source="base locale vigie.duckdb", url="", collecte_le="n/a"),
            )
        ]

    prefixe = f"{siren}%"
    stats = ctx.conn.execute(
        """
        SELECT count(DISTINCT uid), sum(montant), count(DISTINCT acheteur_id),
               max(dateNotification),
               avg(CASE WHEN offresRecues = 1 THEN 1.0 ELSE 0.0 END)
        FROM decp WHERE titulaire_id LIKE ?
        """,
        [prefixe],
    ).fetchone()
    nb, montant_total, nb_acheteurs, dernier, part_offre_unique = stats

    prov = provenance(ctx.conn, "decp")
    preuve_base = dict(
        source=prov["source"] + " — DECP consolidées",
        url=prov["url"],
        collecte_le=prov["collecte_le"],
        licence=prov["licence"],
    )

    if not nb:
        return [
            Signal(
                id="track_record.volume",
                libelle="Historique de marchés publics",
                statut="ok",
                valeur="Aucun marché public recensé dans les DECP pour ce SIREN "
                "(première candidature possible — pas un risque en soi)",
                gravite="info",
                points=0,
                preuve=Preuve(**preuve_base),
            )
        ]

    signaux = [
        Signal(
            id="track_record.volume",
            libelle="Historique de marchés publics",
            statut="ok",
            valeur=(
                f"{nb} marché(s) recensé(s), {montant_total:,.0f} € cumulés, "
                f"{nb_acheteurs} acheteur(s) distinct(s), dernier marché notifié le {dernier}"
            ).replace(",", " "),
            gravite="info",
            points=0,
            preuve=Preuve(
                **preuve_base,
                detail={
                    "nb_marches": nb,
                    "montant_total": montant_total,
                    "nb_acheteurs": nb_acheteurs,
                    "dernier_marche": str(dernier),
                    "part_offre_unique": round(part_offre_unique or 0, 3),
                },
            ),
        )
    ]

    if nb >= bareme.NB_MARCHES_MIN:
        pou = part_offre_unique or 0
        if pou > bareme.SEUIL_OFFRE_UNIQUE_MINEUR:
            gravite = "majeur" if pou > bareme.SEUIL_OFFRE_UNIQUE_MAJEUR else "mineur"
            signaux.append(
                Signal(
                    id="track_record.offre_unique",
                    libelle="Marchés remportés sans concurrence",
                    statut="declenche",
                    valeur=f"{pou:.0%} des marchés remportés avec une seule offre reçue "
                    "(signal de faible mise en concurrence — données déclaratives à confirmer)",
                    gravite=gravite,
                    points=bareme.POINTS_GRAVITE[gravite],
                    preuve=Preuve(**preuve_base, detail={"part_offre_unique": round(pou, 3)}),
                )
            )

        top = ctx.conn.execute(
            """
            SELECT any_value(acheteur_nom), count(DISTINCT uid) AS n
            FROM decp WHERE titulaire_id LIKE ? GROUP BY acheteur_id
            ORDER BY n DESC LIMIT 1
            """,
            [prefixe],
        ).fetchone()
        if top:
            part_top = top[1] / nb
            if part_top > bareme.SEUIL_CONCENTRATION_ACHETEUR:
                signaux.append(
                    Signal(
                        id="track_record.concentration",
                        libelle="Concentration sur un acheteur",
                        statut="declenche",
                        valeur=f"{part_top:.0%} des marchés obtenus auprès du même acheteur "
                        f"({top[0]}) — récurrence à examiner",
                        gravite="mineur",
                        points=bareme.POINTS_GRAVITE["mineur"],
                        preuve=Preuve(
                            **preuve_base,
                            detail={"acheteur_principal": top[0], "part": round(part_top, 3)},
                        ),
                    )
                )

    return signaux
