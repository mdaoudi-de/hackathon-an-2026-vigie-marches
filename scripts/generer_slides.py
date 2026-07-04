"""Génère le deck de présentation (8 diapositives 16:9) -> hackathon-an-2026/docs/diapositives.pdf.

    python scripts/generer_slides.py

Sans dépendance à un navigateur ni à LibreOffice : reportlab dessine le PDF
directement. Charte alignée sur images/cover.png (bleu marine + accent orange).
"""

from __future__ import annotations

from pathlib import Path

from reportlab.lib.colors import HexColor
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas

RACINE = Path(__file__).resolve().parent.parent
SORTIE = RACINE / "hackathon-an-2026" / "docs" / "diapositives.pdf"

# Charte graphique
MARINE = HexColor("#0d1b3e")
MARINE_CLAIR = HexColor("#183670")
ACCENT = HexColor("#e9543e")
GRIS = HexColor("#b0c4de")
BLANC = HexColor("#ffffff")
VERT = HexColor("#059669")
ORANGE = HexColor("#d97706")
ROUGE = HexColor("#dc2626")

# Format 16:9 en points (33.87 x 19.05 cm)
L, H = 33.87 * cm, 19.05 * cm


def fond(c: canvas.Canvas, sombre: bool = True) -> None:
    c.setFillColor(MARINE if sombre else BLANC)
    c.rect(0, 0, L, H, fill=1, stroke=0)
    # Barre d'accent verticale
    c.setFillColor(ACCENT)
    c.rect(2 * cm, 2 * cm, 0.22 * cm, H - 4 * cm, fill=1, stroke=0)


def pied(c: canvas.Canvas, num: int, sombre: bool = True) -> None:
    c.setFillColor(GRIS if sombre else MARINE_CLAIR)
    c.setFont("Helvetica", 9)
    c.drawString(2.5 * cm, 1.1 * cm, "Vigie Marchés — Hackathon Assemblée nationale 2026")
    c.drawRightString(L - 1.5 * cm, 1.1 * cm, f"{num}/8")


def titre_slide(c: canvas.Canvas, titre: str, sombre=True) -> None:
    c.setFillColor(BLANC if sombre else MARINE)
    c.setFont("Helvetica-Bold", 30)
    c.drawString(2.7 * cm, H - 3.2 * cm, titre)


def puce(c: canvas.Canvas, x: float, y: float, texte: str, taille=15, couleur=None, gras=False) -> None:
    c.setFillColor(couleur or GRIS)
    c.setFont("Helvetica-Bold" if gras else "Helvetica", taille)
    c.drawString(x, y, texte)


def slide_titre(c: canvas.Canvas) -> None:
    fond(c)
    c.setFillColor(BLANC)
    c.setFont("Helvetica-Bold", 62)
    c.drawString(2.7 * cm, H - 8 * cm, "Vigie Marchés")
    c.setFillColor(GRIS)
    c.setFont("Helvetica", 22)
    c.drawString(2.7 * cm, H - 9.8 * cm, "L'IA et l'Open Data au service de la transparence")
    c.drawString(2.7 * cm, H - 10.7 * cm, "des marchés publics")
    c.setFillColor(ACCENT)
    c.setFont("Helvetica-Bold", 14)
    c.drawString(2.7 * cm, H - 13 * cm, "Analyse des candidatures · Score de risque explicable · Sources tracées")
    pied(c, 1)


def slide_probleme(c: canvas.Canvas) -> None:
    fond(c)
    titre_slide(c, "Le problème")
    y = H - 5.2 * cm
    lignes = [
        ("Des milliers de candidatures analysées chaque année", GRIS, True),
        ("par les collectivités et administrations.", GRIS, False),
        ("", GRIS, False),
        ("Vérifier un candidat = consulter manuellement INPI, BODACC,", GRIS, True),
        ("data.gouv, sanctions… : chronophage et difficile à maintenir.", GRIS, False),
        ("", GRIS, False),
        ("Angle mort : il n'existe AUCUN registre public français des", ACCENT, True),
        ("interdictions de soumissionner (art. L2141 CCP). La vérification", GRIS, False),
        ("repose sur la déclaration sur l'honneur du candidat.", GRIS, False),
    ]
    for texte, couleur, gras in lignes:
        puce(c, 2.7 * cm, y, texte, 16, couleur, gras)
        y -= 1.15 * cm
    pied(c, 2)


def slide_solution(c: canvas.Canvas) -> None:
    fond(c, sombre=False)
    titre_slide(c, "La solution", sombre=False)
    c.setFillColor(MARINE_CLAIR)
    c.setFont("Helvetica", 17)
    c.drawString(2.7 * cm, H - 4.6 * cm, "Un outil open source qui croise automatiquement les données ouvertes")
    c.drawString(2.7 * cm, H - 5.4 * cm, "et produit un score de risque déterministe, explicable et traçable.")
    cartes = [
        ("Agréger", "7 familles de sources\nOpen Data en une base"),
        ("Vérifier", "Conformité, finances,\nprocédures, sanctions"),
        ("Scorer", "Barème public aligné\nsur le Code (L2141)"),
        ("Décider", "Rapport d'aide à la\ndécision + preuves"),
    ]
    lc = (L - 5.4 * cm) / 4
    for i, (t, d) in enumerate(cartes):
        x = 2.7 * cm + i * lc
        c.setFillColor(MARINE)
        c.roundRect(x, H - 11 * cm, lc - 0.5 * cm, 4 * cm, 8, fill=1, stroke=0)
        c.setFillColor(ACCENT)
        c.setFont("Helvetica-Bold", 17)
        c.drawString(x + 0.5 * cm, H - 8.2 * cm, t)
        c.setFillColor(GRIS)
        c.setFont("Helvetica", 11)
        for j, ligne in enumerate(d.split("\n")):
            c.drawString(x + 0.5 * cm, H - 9 * cm - j * 0.55 * cm, ligne)
    pied(c, 3, sombre=False)


def slide_donnees(c: canvas.Canvas) -> None:
    fond(c)
    titre_slide(c, "Les données agrégées")
    sources = [
        "Recherche d'entreprises (DINUM) — identité, dirigeants, finances",
        "BODACC — procédures collectives, radiations (le signal juridique)",
        "DECP — 3,1 M de marchés publics : le track-record par SIRET",
        "Gels des avoirs (DG Trésor), sanctions UE, EDES, Banque mondiale",
        "HATVP (via Tricoteuses) — répertoire des représentants d'intérêts",
        "Canutes (DILA) — 37 400 acheteurs publics locaux",
    ]
    y = H - 5 * cm
    for s in sources:
        c.setFillColor(ACCENT)
        c.circle(2.9 * cm, y + 0.15 * cm, 0.12 * cm, fill=1, stroke=0)
        puce(c, 3.3 * cm, y, s, 15, GRIS)
        y -= 1.5 * cm
    c.setFillColor(MARINE_CLAIR)
    c.roundRect(2.7 * cm, 2.2 * cm, L - 4.4 * cm, 1.3 * cm, 6, fill=1, stroke=0)
    c.setFillColor(BLANC)
    c.setFont("Helvetica-Bold", 13)
    c.drawString(3.1 * cm, 2.65 * cm, "Toutes vérifiées en conditions réelles · table de provenance : source, date, licence")
    pied(c, 4)


def slide_score(c: canvas.Canvas) -> None:
    fond(c, sombre=False)
    titre_slide(c, "Un score explicable, jamais une boîte noire", sombre=False)
    points = [
        "Barème public et versionné, aligné sur les interdictions de soumissionner (L2141)",
        "6 familles de signaux, points plafonnés — aucune famille ne domine",
        "Règle absolue : aucun signal sans preuve (source, URL, date, licence)",
        "Une correspondance sur une liste de sanctions est « à vérifier », jamais",
        "une condamnation : l'outil signale, l'acheteur décide",
    ]
    y = H - 5 * cm
    for p in points:
        c.setFillColor(ACCENT)
        c.setFont("Helvetica-Bold", 16)
        c.drawString(2.7 * cm, y, "›")
        c.setFillColor(MARINE_CLAIR)
        c.setFont("Helvetica", 15)
        c.drawString(3.3 * cm, y, p)
        y -= 1.4 * cm
    # Pastilles de niveau
    for i, (lab, col) in enumerate([("VERT", VERT), ("ORANGE", ORANGE), ("ROUGE", ROUGE)]):
        x = 2.7 * cm + i * 4 * cm
        c.setFillColor(col)
        c.roundRect(x, 2.6 * cm, 3.4 * cm, 1.1 * cm, 12, fill=1, stroke=0)
        c.setFillColor(BLANC)
        c.setFont("Helvetica-Bold", 14)
        c.drawCentredString(x + 1.7 * cm, 2.95 * cm, lab)
    pied(c, 5, sombre=False)


def slide_demo(c: canvas.Canvas) -> None:
    fond(c)
    titre_slide(c, "Démonstration — 3 cas réels")
    cas = [
        ("DANONE", "VERT", VERT, "Saine — mais détectée au", "registre HATVP du lobbying"),
        ("NEOLEDGE", "VERT", VERT, "74 marchés publics restitués", "en une requête (DECP)"),
        ("DAVEO", "ROUGE", ROUGE, "« Active » au répertoire… mais", "en liquidation au BODACC"),
    ]
    lc = (L - 5.4 * cm) / 3
    for i, (nom, niv, col, l1, l2) in enumerate(cas):
        x = 2.7 * cm + i * lc
        c.setFillColor(MARINE_CLAIR)
        c.roundRect(x, H - 12 * cm, lc - 0.5 * cm, 6 * cm, 8, fill=1, stroke=0)
        c.setFillColor(BLANC)
        c.setFont("Helvetica-Bold", 19)
        c.drawString(x + 0.6 * cm, H - 6.5 * cm, nom)
        c.setFillColor(col)
        c.roundRect(x + 0.6 * cm, H - 7.8 * cm, 2.8 * cm, 0.95 * cm, 10, fill=1, stroke=0)
        c.setFillColor(BLANC)
        c.setFont("Helvetica-Bold", 13)
        c.drawCentredString(x + 2 * cm, H - 7.5 * cm, niv)
        c.setFillColor(GRIS)
        c.setFont("Helvetica", 11.5)
        c.drawString(x + 0.6 * cm, H - 9.3 * cm, l1)
        c.drawString(x + 0.6 * cm, H - 9.9 * cm, l2)
    c.setFillColor(ACCENT)
    c.setFont("Helvetica-Bold", 14)
    c.drawString(2.7 * cm, 2.7 * cm, "Le cas DAVEO : l'angle mort comblé en 2 secondes, preuve BODACC à l'appui.")
    pied(c, 6)


def slide_differenciant(c: canvas.Canvas) -> None:
    fond(c)
    titre_slide(c, "Ce qui nous différencie")
    blocs = [
        ("Serveur MCP maison « vigie-marches »",
         ["Aucun serveur MCP DECP/BODACC n'existait.",
          "Un agent IA (Claude…) instruit un dossier en",
          "enchaînant nos 5 outils — preuves à l'appui."]),
        ("Une API REST réutilisable",
         ["7 endpoints documentés (OpenAPI).",
          "Toute collectivité peut brancher l'outil",
          "sur son propre système."]),
        ("Transparence de bout en bout",
         ["Score déterministe (aucune IA dans le calcul).",
          "Chaque signal remonte à sa source datée.",
          "Code open source (MIT)."]),
    ]
    y = H - 5.3 * cm
    for titre, lignes in blocs:
        c.setFillColor(ACCENT)
        c.setFont("Helvetica-Bold", 16)
        c.drawString(2.7 * cm, y, titre)
        c.setFillColor(GRIS)
        c.setFont("Helvetica", 12.5)
        for j, ligne in enumerate(lignes):
            c.drawString(2.9 * cm, y - 0.7 * cm - j * 0.55 * cm, ligne)
        y -= 3.1 * cm
    pied(c, 7)


def slide_conclusion(c: canvas.Canvas) -> None:
    fond(c)
    c.setFillColor(BLANC)
    c.setFont("Helvetica-Bold", 34)
    c.drawString(2.7 * cm, H - 6 * cm, "L'outil signale et source ;")
    c.setFillColor(ACCENT)
    c.drawString(2.7 * cm, H - 7.8 * cm, "la décision reste humaine.")
    c.setFillColor(GRIS)
    c.setFont("Helvetica", 15)
    lignes = [
        "Vigie Marchés fait gagner un temps considérable à l'acheteur public,",
        "objective le risque et trace chaque signal — sans jamais se substituer",
        "à son jugement ni prétendre à une vérité juridique que l'Open Data n'a pas.",
    ]
    y = H - 10 * cm
    for l in lignes:
        c.drawString(2.7 * cm, y, l)
        y -= 0.85 * cm
    c.setFillColor(BLANC)
    c.setFont("Helvetica-Bold", 13)
    c.drawString(2.7 * cm, 3 * cm, "Prototype open source · Python + FastAPI + Next.js + MCP · Licence MIT")
    pied(c, 8)


def main() -> None:
    SORTIE.parent.mkdir(parents=True, exist_ok=True)
    c = canvas.Canvas(str(SORTIE), pagesize=(L, H))
    for slide in (
        slide_titre, slide_probleme, slide_solution, slide_donnees,
        slide_score, slide_demo, slide_differenciant, slide_conclusion,
    ):
        slide(c)
        c.showPage()
    c.save()
    print(f"-> {SORTIE} ({SORTIE.stat().st_size // 1024} Ko, 8 diapositives)")


if __name__ == "__main__":
    main()
