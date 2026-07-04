"""Capture les 3 écrans du front pour la galerie du DEFI.md.

    python scripts/captures.py

Prérequis : API (VIGIE_OFFLINE=1 conseillé) sur :8000 et front sur :3000.
Produit hackathon-an-2026/images/ecran-*.png via Chromium (Playwright).
"""

from __future__ import annotations

import time
from pathlib import Path

from playwright.sync_api import sync_playwright

RACINE = Path(__file__).resolve().parent.parent
IMAGES = RACINE / "hackathon-an-2026" / "images"
BASE = "http://127.0.0.1:3000"

ECRANS = [
    ("ecran-accueil", "/", None),
    ("ecran-analyse-rouge", "/analyse/827879610", "h1"),
    ("ecran-methodologie", "/methodologie", "table"),
]


def main() -> None:
    IMAGES.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        navigateur = p.chromium.launch()
        page = navigateur.new_page(viewport={"width": 1280, "height": 900})
        for nom, chemin, attendre in ECRANS:
            page.goto(BASE + chemin, wait_until="networkidle")
            if attendre:
                page.wait_for_selector(attendre, timeout=30000)
            time.sleep(1.5)  # laisse les accordéons/jauge se peindre
            cible = IMAGES / f"{nom}.png"
            page.screenshot(path=str(cible), full_page=True)
            print(f"-> {cible.name}")
        navigateur.close()


if __name__ == "__main__":
    main()
