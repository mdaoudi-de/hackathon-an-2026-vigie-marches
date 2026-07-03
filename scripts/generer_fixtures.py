"""Génère les fixtures des cas de démo (mode hors-ligne VIGIE_OFFLINE=1).

    python scripts/generer_fixtures.py

Écrit data/fixtures/analyse_<identifiant>.json pour chaque cas de cas_demo.md.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ingestion import config  # noqa: E402
from vigie.moteur import analyser  # noqa: E402

CAS_DEMO = ["552032534", "75058171200015", "827879610"]


def main() -> None:
    dossier = config.DATA_DIR / "fixtures"
    dossier.mkdir(parents=True, exist_ok=True)
    for identifiant in CAS_DEMO:
        print(f"analyse de {identifiant}…")
        analyse = analyser(identifiant)
        cible = dossier / f"analyse_{identifiant}.json"
        cible.write_text(analyse.model_dump_json(indent=2), encoding="utf-8")
        print(f"  -> {cible.name} ({analyse.score.niveau}, {analyse.duree_ms} ms)")


if __name__ == "__main__":
    main()
