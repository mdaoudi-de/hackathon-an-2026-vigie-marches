"""Tests d'intégration légers de l'API en mode HORS-LIGNE.

Sans réseau ni base : le mode VIGIE_OFFLINE sert les fixtures des 3 cas de démo
(commitées dans data/fixtures/). Valide le contrat de l'API de bout en bout.
"""

import os

os.environ["VIGIE_OFFLINE"] = "1"  # avant l'import de l'app (lu à chaque requête de toute façon)

from fastapi.testclient import TestClient  # noqa: E402

from api.main import app  # noqa: E402

client = TestClient(app)


def test_sante_repond():
    r = client.get("/api/sante")
    assert r.status_code == 200
    assert r.json()["statut"] == "ok"


def test_bareme_versionne():
    r = client.get("/api/bareme")
    assert r.status_code == 200
    corps = r.json()
    assert corps["version"]
    assert corps["plafond_famille"] > 0
    assert len(corps["familles"]) == 6


def test_analyse_cas_rouge_avec_preuves():
    # Fixture DAVEO : liquidation judiciaire -> ROUGE rédhibitoire.
    r = client.get("/api/analyses/827879610")
    assert r.status_code == 200
    data = r.json()
    assert data["score"]["niveau"] == "ROUGE"
    assert data["score"]["redhibitoire"] is True
    # Règle du projet : aucun signal sans preuve.
    for famille in data["familles"]:
        for signal in famille["signaux"]:
            assert signal["preuve"]["source"], f"signal sans preuve : {signal['id']}"


def test_analyse_cas_vert():
    r = client.get("/api/analyses/552032534")  # DANONE
    assert r.status_code == 200
    assert r.json()["score"]["niveau"] == "VERT"


def test_identifiant_invalide_422():
    r = client.get("/api/analyses/123")
    assert r.status_code == 422


def test_fixture_absente_503():
    # En mode hors-ligne, un identifiant sans fixture renvoie un 503 explicite (pas un plantage).
    r = client.get("/api/analyses/000000000")
    assert r.status_code == 503
