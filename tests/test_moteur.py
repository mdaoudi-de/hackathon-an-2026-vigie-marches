"""Tests de la partie PURE du moteur (aucun réseau, aucune base)."""

from vigie import bareme
from vigie.modeles import Famille, Preuve, Signal
from vigie.moteur import agreger, construire_famille, normaliser_identifiant
from vigie.signaux.sanctions import classer, normaliser

PREUVE = Preuve(source="test", url="http://test", collecte_le="2026-07-03")


def _signal(statut="declenche", gravite="mineur", points=None):
    return Signal(
        id="t.t",
        libelle="t",
        statut=statut,
        valeur="t",
        gravite=gravite,
        points=bareme.POINTS_GRAVITE[gravite] if points is None else points,
        preuve=PREUVE,
    )


def test_normaliser_denomination():
    assert normaliser("Danone S.A.") == "DANONE"
    assert normaliser("Société Générale SA") == "GENERALE"
    assert normaliser("HEBEI CONSTRUCTION GROUP CORPORATION LIMITED") == "HEBEI CONSTRUCTION"
    assert normaliser("Café de l'Étoile") == "CAFE DE L ETOILE"


def test_classer_zones_similarite():
    assert classer(97) == "fort"
    assert classer(90) == "possible"
    assert classer(80) is None
    # Rétrogradation d'une zone pour un pays éloigné
    assert classer(97, pays="cn") == "possible"
    assert classer(90, pays="cn") is None
    assert classer(97, pays="fr") == "fort"


def test_zone_correspondance_inclusion():
    from vigie.signaux.sanctions import zone_correspondance

    # Quasi-identité stricte : zone forte conservée
    assert zone_correspondance(100, 100) == "fort"
    # Inclusion seule (« ROSNEFT » dans « ROSNEFT OIL COMPANY ») : rétrogradée à possible
    assert zone_correspondance(100, 54) == "possible"
    # Inclusion moyenne : reste possible
    assert zone_correspondance(90, 54) == "possible"
    # Sous le seuil : ignoré
    assert zone_correspondance(80, 80) is None
    # Cumul inclusion seule + pays éloigné : possible (pays) puis inchangé
    assert zone_correspondance(100, 54, pays="cn") == "possible"


def test_normaliser_identifiant():
    assert normaliser_identifiant("552 032 534") == ("552032534", None)
    assert normaliser_identifiant("75058171200015") == ("750581712", "75058171200015")
    try:
        normaliser_identifiant("123")
        assert False, "identifiant invalide accepté"
    except ValueError:
        pass


def test_plafond_famille():
    famille = construire_famille("financier", [_signal(gravite="majeur") for _ in range(3)])
    assert famille.points == bareme.PLAFOND_FAMILLE  # 60 points bruts plafonnés à 30
    # Les signaux ok/indisponible ne comptent pas
    famille2 = construire_famille("financier", [_signal(statut="ok", points=20)])
    assert famille2.points == 0


def test_agreger_niveaux():
    # VERT : rien à signaler
    vert = agreger([construire_famille("identite", [_signal(statut="ok", gravite="info")])])
    assert vert.niveau == "VERT" and vert.points == 0

    # ORANGE : points au-dessus du seuil
    orange = agreger([construire_famille("financier", [_signal(gravite="majeur")])])
    assert orange.niveau == "ORANGE"

    # ORANGE : un signal à vérifier suffit, même à 8 points
    a_verifier = agreger(
        [construire_famille("sanctions_integrite", [_signal(statut="a_verifier")])]
    )
    assert a_verifier.niveau == "ORANGE" and a_verifier.nb_a_verifier == 1

    # ROUGE : un rédhibitoire déclenché, quel que soit le total
    rouge = agreger(
        [construire_famille("procedures_collectives", [_signal(gravite="redhibitoire")])]
    )
    assert rouge.niveau == "ROUGE" and rouge.redhibitoire


def test_aucun_signal_sans_preuve():
    # Le modèle Pydantic refuse un signal sans preuve
    import pydantic
    import pytest

    with pytest.raises(pydantic.ValidationError):
        Signal(id="x", libelle="x", statut="ok", valeur="x")
