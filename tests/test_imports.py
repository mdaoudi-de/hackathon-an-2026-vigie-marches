"""Vérifie que tous les modules du projet s'importent proprement.

Détecte les erreurs de syntaxe et de dépendances manquantes sans réseau ni base :
c'est le test de reproductibilité le plus élémentaire (l'environnement est complet).
"""

import importlib

import pytest

MODULES = [
    "vigie.modeles",
    "vigie.bareme",
    "vigie.db",
    "vigie.moteur",
    "vigie.cli",
    "vigie.rapport",
    "vigie.signaux.identite",
    "vigie.signaux.financier",
    "vigie.signaux.procedures",
    "vigie.signaux.sanctions",
    "vigie.signaux.track_record",
    "vigie.signaux.lobbying",
    "ingestion.config",
    "ingestion.common",
    "ingestion.clients",
    "api.main",
    "api.schemas",
    "api.cache",
    "vigie_mcp.serveur",
]


@pytest.mark.parametrize("module", MODULES)
def test_import(module: str) -> None:
    importlib.import_module(module)
