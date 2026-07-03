"""Registre national des gels des avoirs (DG Trésor) → table `gels_avoirs`.

Source officielle française, juridiquement opposable : toute personne/entité
sous gel des avoirs applicable en France (ONU + UE + gels nationaux).
Publication quotidienne. Champs MOTIFS et FONDEMENT_JURIDIQUE conservés
pour un rapport d'aide à la décision explicable. Sans clé API.
"""

from __future__ import annotations

import json

from ingestion import config
from ingestion.common import get_session, log_provenance, write_jsonl

SOURCE = "gels_avoirs"
LICENCE = "Registre public DG Trésor"

# Champs extraits en colonnes dédiées (le détail complet reste dans `detail_json`)
CHAMPS = [
    "PRENOM",
    "ALIAS",
    "SEXE",
    "DATE_DE_NAISSANCE",
    "LIEU_DE_NAISSANCE",
    "NATIONALITE",
    "TITRE",
    "ADRESSE_PM",
    "ADRESSE_PP",
    "IDENTIFICATION",
    "AUTRE_IDENTITE",
    "REFERENCE_UE",
    "REFERENCE_ONU",
    "FONDEMENT_JURIDIQUE",
    "MOTIFS",
]


def _valeurs_en_texte(valeurs) -> str:
    """Aplati la liste `Valeur` d'un TypeChamp en texte lisible."""
    morceaux = []
    for v in valeurs or []:
        if isinstance(v, dict):
            morceaux.append(" ".join(str(x) for x in v.values() if x not in (None, "")))
        else:
            morceaux.append(str(v))
    return " | ".join(m for m in morceaux if m)


def run(conn) -> None:
    print(f"[{SOURCE}] téléchargement du registre…")
    session = get_session()
    r = session.get(config.GELS_AVOIRS_JSON, timeout=180)
    r.raise_for_status()
    payload = r.json()

    publications = payload.get("Publications", {})
    date_publication = publications.get("DatePublication")
    details = publications.get("PublicationDetail", [])

    lignes = []
    for entree in details:
        ligne = {
            "id_registre": entree.get("IdRegistre"),
            "nature": entree.get("Nature"),
            "nom": entree.get("Nom"),
            "date_publication": date_publication,
        }
        par_champ: dict[str, list] = {}
        for detail in entree.get("RegistreDetail", []):
            champ = detail.get("TypeChamp")
            if champ:
                par_champ.setdefault(champ, []).extend(detail.get("Valeur") or [])
        for champ in CHAMPS:
            ligne[champ.lower()] = _valeurs_en_texte(par_champ.get(champ)) or None
        ligne["detail_json"] = json.dumps(entree.get("RegistreDetail", []), ensure_ascii=False)
        lignes.append(ligne)

    raw = write_jsonl(lignes, config.RAW_DIR / "gels_avoirs.jsonl")
    conn.execute(
        f"""
        CREATE OR REPLACE TABLE gels_avoirs AS
        SELECT * FROM read_json_auto('{raw.as_posix()}', format='newline_delimited', sample_size=-1)
        """
    )
    log_provenance(
        conn,
        SOURCE,
        config.GELS_AVOIRS_JSON,
        "gels_avoirs",
        LICENCE,
        note=f"publication du {date_publication}",
    )
