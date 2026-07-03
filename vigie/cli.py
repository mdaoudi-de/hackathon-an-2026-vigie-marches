"""CLI du moteur d'analyse.

    python -m vigie.cli 552032534           # affichage lisible
    python -m vigie.cli 552032534 --json    # JSON complet (contrat API/front/MCP)
"""

from __future__ import annotations

import argparse
import sys

from vigie.moteur import analyser

ICONES_STATUT = {"ok": "[ok]", "declenche": "[ ! ]", "a_verifier": "[ ? ]", "indisponible": "[ - ]"}


def main() -> int:
    parser = argparse.ArgumentParser(description="Vigie Marchés — analyse d'un candidat")
    parser.add_argument("identifiant", help="SIREN (9 chiffres) ou SIRET (14 chiffres)")
    parser.add_argument("--json", action="store_true", help="sortie JSON complète")
    args = parser.parse_args()

    analyse = analyser(args.identifiant)

    if args.json:
        print(analyse.model_dump_json(indent=2))
        return 0

    c = analyse.candidat
    s = analyse.score
    print()
    print(f"  {c.denomination or 'DENOMINATION INCONNUE'}  (SIREN {c.siren}"
          + (f", SIRET {c.siret}" if c.siret else "") + ")")
    print(f"  Niveau : {s.niveau}  |  {s.points}/{s.plafond} points  |  barème v{s.version_bareme}"
          + ("  |  SIGNAL REDHIBITOIRE" if s.redhibitoire else "")
          + (f"  |  {s.nb_a_verifier} point(s) à vérifier manuellement" if s.nb_a_verifier else ""))
    print("  " + "-" * 76)
    for famille in analyse.familles:
        print(f"  {famille.libelle}  ({famille.points}/{famille.plafond} pts)")
        for signal in famille.signaux:
            print(f"    {ICONES_STATUT[signal.statut]} {signal.libelle} : {signal.valeur}")
            if signal.statut != "ok" and signal.preuve.url:
                print(f"          preuve : {signal.preuve.url} (collecté le {signal.preuve.collecte_le})")
    if analyse.avertissements:
        print("  " + "-" * 76)
        for a in analyse.avertissements:
            print(f"  (!) {a}")
    print(f"\n  Généré le {analyse.genere_le} en {analyse.duree_ms} ms — chaque signal est sourcé.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
