"""Configuration centrale de l'ingestion : chemins et URLs des sources.

Toutes les URLs ont été vérifiées par requêtes réelles le 03/07/2026
(voir docs/SOURCES.md pour l'inventaire complet, les limites et les licences).
"""

from pathlib import Path

# Racine du dépôt (ce fichier est dans ingestion/)
RACINE = Path(__file__).resolve().parent.parent
DATA_DIR = RACINE / "data"
RAW_DIR = DATA_DIR / "raw"
DB_PATH = DATA_DIR / "vigie.duckdb"

USER_AGENT = "vigie-marches/0.1 (hackathon AN 2026; outil open source transparence marches publics)"

# --- Sanctions & intégrité (téléchargement complet, sans clé) ---

# Registre national des gels des avoirs (DG Trésor) — publication quotidienne, JSON ~10 Mo
GELS_AVOIRS_JSON = (
    "https://gels-avoirs.dgtresor.gouv.fr/ApiPublic/api/v1/publication/derniere-publication-fichier-json"
)

# Liste consolidée des sanctions financières de l'UE (FSF) — CSV ~24 Mo, token public générique
EU_FSF_CSV = (
    "https://webgate.ec.europa.eu/fsd/fsf/public/files/csvFullSanctionsList_1_1/content?token=dG9rZW4tMjAxNw"
)

# EDES (exclusions du budget UE) — POST JSON obligatoire, réponse préfixée par la garde anti-XSSI )]}',
EDES_API = "https://ec.europa.eu/edes/api/cases/paginatedList"

# Miroirs OpenSanctions (licence CC-BY-NC 4.0 : OK prototype, licence requise en usage commercial)
OPENSANCTIONS_SLUGS = ["worldbank_debarred", "eu_edes"]
OPENSANCTIONS_CSV = "https://data.opensanctions.org/datasets/latest/{slug}/targets.simple.csv"

# --- Liens d'intérêts (HATVP via API Tricoteuses Parlement, licence ODbL-1.0) ---

HATVP_REPRESENTANTS = "https://parlement.tricoteuses.fr/representantsInterets/json"

# --- Acheteurs publics locaux (Canutes PostgREST, données DILA) ---

CANUTES_BASE = "https://db.code4code.eu/canutes"

# --- Commande publique : DECP consolidées format tabulaire (decp.info / Licence Ouverte 2.0) ---
# URLs stables data.gouv.fr (résolues dynamiquement, suivent une redirection 302 vers static.data.gouv.fr)

DECP_PARQUET = "https://www.data.gouv.fr/api/1/datasets/r/11cea8e8-df3e-4ed1-932b-781e2635e432"
DECP_SCHEMA = "https://www.data.gouv.fr/api/1/datasets/r/9a4144c0-ee44-4dec-bee5-bbef38191d9a"

# --- APIs interrogées à la demande (par candidat — voir ingestion/clients.py) ---

RECHERCHE_ENTREPRISES = "https://recherche-entreprises.api.gouv.fr/search"
BODACC_RECORDS = (
    "https://bodacc-datadila.opendatasoft.com/api/explore/v2.1/catalog/datasets/annonces-commerciales/records"
)
BOAMP_RECORDS = "https://boamp-datadila.opendatasoft.com/api/explore/v2.1/catalog/datasets/boamp/records"
DECP_TABULAR = "https://tabular-api.data.gouv.fr/api/resources/22847056-61df-452d-837d-8b8ceadbfc52/data/"
TED_SEARCH = "https://api.ted.europa.eu/v3/notices/search"
