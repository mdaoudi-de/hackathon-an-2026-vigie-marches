"""Rapport d'aide à la décision rédigé par Claude.

GARDE-FOU CENTRAL : l'IA ne calcule RIEN. Elle reçoit exclusivement le JSON
produit par le moteur déterministe (vigie/moteur.py) — score déjà figé — et le
met en forme pour un acheteur public, en citant la source de chaque fait.

Clé API : variable d'environnement ANTHROPIC_API_KEY, ou fichier .env à la
racine du dépôt (ignoré par git). Sans clé, ClefApiManquante est levée et le
reste de l'application fonctionne normalement.
"""

from __future__ import annotations

import os
from datetime import datetime, timezone

from ingestion import config
from vigie.modeles import Analyse

MODELE = "claude-opus-4-8"

# Prompt système STABLE (aucune donnée variable : indispensable au cache de prompt).
PROMPT_SYSTEME = """Tu es l'assistant d'un acheteur public français. Tu rédiges une note
d'aide à la décision (1 à 2 pages, Markdown, en français) à partir du résultat JSON d'une
analyse AUTOMATIQUE et DÉTERMINISTE d'un candidat à un marché public.

RÈGLES ABSOLUES :
1. Tu ne calcules ni ne modifies AUCUN score : le niveau (VERT/ORANGE/ROUGE) et les points
   sont définitifs. Tu les restitues tels quels.
2. Tu n'affirmes RIEN qui ne figure pas dans le JSON fourni. Aucune connaissance externe
   sur l'entreprise, aucune supposition.
3. Après chaque fait, cite sa source entre crochets : [BODACC], [DECP], [Recherche
   d'entreprises], [HATVP], [Gels des avoirs], etc. — d'après le champ preuve.source.
4. Les correspondances « à vérifier » (listes de sanctions) sont des homonymies possibles,
   jamais des accusations : formule-les comme des points de vérification manuelle.
5. Termine par la mention : « Ce rapport est une aide à la décision générée automatiquement ;
   la décision d'admission ou d'exclusion appartient à l'acheteur (art. L2141 s. CCP). »

PLAN IMPOSÉ :
# Note d'aide à la décision — [dénomination] (SIREN ...)
## Synthèse (3-5 lignes : niveau, points, faits saillants)
## Proposition (poursuivre l'examen / demander des pièces / vigilance renforcée / motif
   d'exclusion à instruire — selon le niveau et les signaux, formulée comme une proposition)
## Détail par famille de signaux (uniquement les familles avec signaux non-ok, plus une
   ligne récapitulative pour les familles sans anomalie)
## Points à vérifier manuellement (chaque signal a_verifier ou indisponible, avec la
   démarche concrète : quel registre consulter, quelle pièce demander au candidat)
## Limites de l'analyse (avertissements du JSON + rappel que seules des sources ouvertes
   ont été consultées)"""


class ClefApiManquante(RuntimeError):
    """Aucune clé API Anthropic disponible."""


def _charger_dotenv() -> None:
    """Charge RACINE/.env (KEY=VALUE) dans os.environ sans écraser l'existant."""
    dotenv = config.RACINE / ".env"
    if not dotenv.exists():
        return
    for ligne in dotenv.read_text(encoding="utf-8").splitlines():
        ligne = ligne.strip()
        if ligne and not ligne.startswith("#") and "=" in ligne:
            cle, _, valeur = ligne.partition("=")
            os.environ.setdefault(cle.strip(), valeur.strip())


def generer_rapport(analyse: Analyse) -> dict:
    """Rédige la note en Markdown. Lève ClefApiManquante si aucune clé n'est configurée."""
    _charger_dotenv()
    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise ClefApiManquante(
            "Aucune clé API Anthropic : ajouter ANTHROPIC_API_KEY=... dans un fichier .env "
            "à la racine du projet (le reste de l'application fonctionne sans)."
        )

    import anthropic  # import tardif : le moteur/l'API restent utilisables sans le SDK

    client = anthropic.Anthropic()
    with client.messages.stream(
        model=MODELE,
        max_tokens=8000,
        thinking={"type": "adaptive"},
        system=[
            {
                "type": "text",
                "text": PROMPT_SYSTEME,
                # Prompt stable → cacheable (ne prend effet qu'au-delà du seuil du modèle)
                "cache_control": {"type": "ephemeral"},
            }
        ],
        messages=[
            {
                "role": "user",
                "content": "Voici le résultat JSON de l'analyse. Rédige la note.\n\n"
                + analyse.model_dump_json(indent=2),
            }
        ],
    ) as flux:
        message = flux.get_final_message()

    markdown = "".join(bloc.text for bloc in message.content if bloc.type == "text")
    return {
        "markdown": markdown,
        "modele": MODELE,
        "genere_le": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "usage": {
            "tokens_entree": message.usage.input_tokens,
            "tokens_sortie": message.usage.output_tokens,
        },
    }
