"""Barème du score de risque — source unique, versionnée.

Le barème décalque les interdictions de soumissionner du Code de la commande
publique (art. L2141-1 à L2141-5) : une liquidation judiciaire en cours est
rédhibitoire (ROUGE immédiat) ; les autres signaux pèsent des points plafonnés
par famille pour qu'aucune ne domine. Toute modification = nouvelle version,
citée dans chaque analyse (reproductibilité).
"""

VERSION_BAREME = "1.0"

# Points par gravité (un signal « déclenché » ou « à vérifier » rapporte ses points)
POINTS_GRAVITE = {"info": 0, "mineur": 8, "majeur": 20, "redhibitoire": 30}

PLAFOND_FAMILLE = 30
PLAFOND_GLOBAL = 100

# Niveaux : VERT < SEUIL_ORANGE ; ORANGE sinon ; ROUGE si >= SEUIL_ROUGE ou rédhibitoire
SEUIL_ORANGE = 20
SEUIL_ROUGE = 50

# --- Matching de noms sur les listes de sanctions (3 zones, jamais binaire) ---
SEUIL_MATCH_FORT = 95      # correspondance forte  -> a_verifier, gravité majeur
SEUIL_MATCH_POSSIBLE = 88  # correspondance possible -> a_verifier, gravité mineur
# < SEUIL_MATCH_POSSIBLE : ignoré, mais le contrôle effectué est affiché

# Pays considérés « proches » : un match Banque mondiale hors de cette zone est
# rétrogradé d'une zone (limite les faux positifs d'homonymie internationale)
PAYS_PROCHES = {"fr", "be", "lu", "ch", "de", "es", "it", "nl", "pt", "gb", "mc"}

# Formes juridiques et mots creux retirés avant comparaison de dénominations
STOP_WORDS_DENOMINATION = {
    "SA", "SAS", "SASU", "SARL", "EURL", "SNC", "SCI", "SCOP", "SCIC", "SEM", "EPIC",
    "GIE", "EI", "EIRL", "GMBH", "AG", "BV", "NV", "LTD", "LIMITED", "LLC", "INC",
    "CORP", "CORPORATION", "PLC", "SPA", "SRL", "OOO", "JSC", "PJSC",
    "SOCIETE", "COMPANY", "CO", "GROUPE", "GROUP", "HOLDING", "ETABLISSEMENTS", "ETS",
}

# Anomalies de track-record (garde-fou : jamais évaluées sous NB_MARCHES_MIN)
NB_MARCHES_MIN = 5
SEUIL_OFFRE_UNIQUE_MINEUR = 0.5   # > 50 % de marchés remportés en offre unique
SEUIL_OFFRE_UNIQUE_MAJEUR = 0.7
SEUIL_CONCENTRATION_ACHETEUR = 0.8  # > 80 % des marchés avec le même acheteur

# Financier
SEUIL_BAISSE_CA = 0.20  # baisse de CA > 20 % entre les deux derniers exercices publiés

LIBELLES_FAMILLES = {
    "identite": "Identité et conformité administrative",
    "financier": "Santé financière",
    "procedures_collectives": "Procédures collectives et radiations",
    "sanctions_integrite": "Sanctions et intégrité",
    "track_record": "Historique de marchés publics (DECP)",
    "lobbying": "Liens d'intérêts (HATVP)",
}
