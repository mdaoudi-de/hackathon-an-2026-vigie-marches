# Vigie Marchés — Hackathon AN 2026 · Transparence des marchés publics par l'IA et l'Open Data

Prototype **open source** d'aide aux acheteurs publics pour l'analyse des candidatures aux marchés publics :
agrégation automatique de sources Open Data, vérification de conformité administrative, analyse de documents,
**score de risque explicable**, tableaux de bord et **rapport d'aide à la décision** — avec transparence et traçabilité.

## Dossier réglementaire du hackathon

Le dossier [hackathon-an-2026/](hackathon-an-2026/) suit la structure imposée par l'organisation :
- [DEFI.md](hackathon-an-2026/DEFI.md) — fiche du défi (template officiel) ; son contenu alimente la page publique du défi
- `docs/` et `images/` — **tout document ou image référencé dans DEFI.md doit être placé dans ces deux dossiers**

## État du projet

- [x] Recensement et **vérification en conditions réelles** de ~80 endpoints / 30 sources (03/07/2026) → [docs/SOURCES.md](docs/SOURCES.md)
- [x] Initialisation des serveurs MCP du projet → [.mcp.json](.mcp.json)
- [x] Scripts d'ingestion → base DuckDB locale avec table de provenance → [ingestion/](ingestion/)
- [x] Feuille de route par runs → [docs/ROADMAP.md](docs/ROADMAP.md)
- [x] **Run 1 — Moteur de score explicable** (6 familles de signaux, barème v1.0, CLI) → [vigie/](vigie/)
- [x] **Run 2 — API REST FastAPI** (7 endpoints documentés, cache, mode hors-ligne) → [api/](api/)
- [x] **Run 3 — Interface Next.js** (recherche, fiche d'analyse avec preuves, méthodologie) → [front/](front/)
- [x] **Run 4 — Rapport d'aide à la décision par Claude** (l'IA met en forme le JSON, ne calcule rien) → [vigie/rapport.py](vigie/rapport.py)
- [x] **Run 5 — Serveur MCP maison `vigie-marches`** (5 outils agentiques) → [vigie_mcp/](vigie_mcp/)
- [ ] Run 6 — Polish + livrables hackathon

## Rapport IA (Run 4)

`GET /api/analyses/{id}/rapport` : Claude rédige une note d'aide à la décision (Markdown) à partir
du **seul** JSON du moteur — le score est déjà figé, l'IA ne fait que la mise en forme sourcée
(chaque fait cité `[BODACC]`, `[DECP]`…). Bouton « Générer le rapport » sur la fiche d'analyse.
Nécessite une clé : créer un fichier `.env` à la racine avec `ANTHROPIC_API_KEY=...` (ignoré par git ;
sans clé, l'app fonctionne, l'endpoint renvoie un 503 explicite). Modèle `claude-opus-4-8`, streaming.

## Serveur MCP `vigie-marches` (Run 5) — le livrable différenciant

Aucun serveur MCP DECP/BODACC n'existait : `vigie_mcp/serveur.py` (FastMCP, stdio) expose le **même
moteur** en 5 outils pour un agent IA — `analyser_candidat`, `screening_sanctions`,
`track_record_marches`, `rechercher_entreprise`, `sources_donnees`. Déclaré dans [.mcp.json](.mcp.json)
(serveur `vigie`) à côté des 4 serveurs distants. Démo : dans Claude Code ouvert sur ce dossier,
« Analyse la candidature de NEOLEDGE (SIRET 75058171200015), sanctions + historique, compare avec Danone ».

## Interface web (Run 3)

```powershell
# Terminal 1 : l'API           # Terminal 2 : le front
.\.venv\Scripts\uvicorn api.main:app        cd front; npm install; npm run dev
# puis http://localhost:3000
```

Trois écrans : **accueil** (recherche avec autocomplétion + 3 cas de démo cliquables),
**fiche d'analyse** (pastille VERT/ORANGE/ROUGE, jauge, une carte par famille, chaque signal
avec son lien « preuve » sourcé et daté), **méthodologie** (barème public + table de provenance).

## API REST (Run 2)

```powershell
.\.venv\Scripts\uvicorn api.main:app --reload      # doc interactive : http://127.0.0.1:8000/docs
```

| Endpoint | Rôle |
|---|---|
| `GET /api/analyses/{siren_ou_siret}` | **Analyse complète** (contrat JSON du moteur, cache 15 min) |
| `GET /api/candidats?q=` | Autocomplétion (nom, SIREN, SIRET) |
| `GET /api/screening/sanctions?nom=` | Screening d'un nom seul contre les 5 listes |
| `GET /api/track-record/{id}` | Historique DECP + derniers marchés |
| `GET /api/provenance` | Traçabilité des tables locales (source, date, licence) |
| `GET /api/bareme` | Méthodologie du score (barème versionné) |
| `GET /api/sante` | Healthcheck |

Mode démo sans réseau : `VIGIE_OFFLINE=1` sert les analyses enregistrées des 3 cas de démo
(régénérables via `python scripts/generer_fixtures.py`).

## Moteur d'analyse (Run 1)

```powershell
.\.venv\Scripts\python -m vigie.cli 552032534          # Danone : VERT, signal HATVP informatif
.\.venv\Scripts\python -m vigie.cli 75058171200015     # NEOLEDGE : track-record DECP (74 marchés)
.\.venv\Scripts\python -m vigie.cli 827879610          # DAVEO : ROUGE rédhibitoire (liquidation BODACC)
.\.venv\Scripts\python -m vigie.cli 552032534 --json   # contrat JSON complet (API/front/MCP)
.\.venv\Scripts\python -m pytest tests/ -q             # tests de la partie pure
```

Principes : score **déterministe et explicable** (aucune IA dans le calcul), barème versionné aligné
sur les interdictions de soumissionner (art. L2141 CCP), **aucun signal sans preuve** (source, URL,
date, licence), correspondances sanctions toujours « à vérifier » (jamais de rouge automatique sur
un matching de nom). Cas de démo documentés dans [data/fixtures/cas_demo.md](data/fixtures/cas_demo.md).

## Ingestion des données

```powershell
python -m venv .venv
.\.venv\Scripts\pip install -r requirements.txt

# Tout ingérer (DECP en vue distante = démarrage rapide, rien à télécharger)
.\.venv\Scripts\python -m ingestion.ingest_all --decp-remote

# Ou en matérialisant les 3,1M de marchés DECP en local (~200 Mo, requêtes instantanées)
.\.venv\Scripts\python -m ingestion.ingest_all

# À la carte
.\.venv\Scripts\python -m ingestion.ingest_all --only gels_avoirs edes
```

Résultat : une base **`data/vigie.duckdb`** avec :

| Table / vue | Contenu | Lignes (03/07/2026) |
|---|---|---|
| `gels_avoirs` | Registre national des gels des avoirs (DG Trésor) | 6 292 |
| `eu_fsf` | Sanctions financières UE (liste consolidée) | 42 347 |
| `edes` + `os_eu_edes` | Exclusions du budget UE | 3 |
| `os_worldbank_debarred` | Exclusions Banque mondiale (+ cross-debarment) | 1 415 |
| `hatvp_representants` / `v_lobbying` | Répertoire HATVP des représentants d'intérêts (3 718 SIREN joignables) | 4 038 |
| `acheteurs_locaux` / `v_acheteurs` | Annuaire des acheteurs publics locaux (SIREN/SIRET, géoloc) | 37 400 |
| `communes` | Communes (référentiel partiel Canutes) | 7 504 |
| `decp` + `v_decp_stats_titulaire` | 3,1M de marchés publics, agrégés par titulaire | 3 101 841 |
| `_provenance` | **Traçabilité** : source, URL, date de collecte, licence de chaque table | — |

Les fichiers bruts téléchargés sont conservés dans `data/raw/` (auditabilité).
Les APIs à interroger **par candidat** au moment de l'analyse (recherche-entreprises, BODACC,
DECP tabulaire, BOAMP, TED) sont disponibles dans [ingestion/clients.py](ingestion/clients.py).

## Serveurs MCP configurés (aucune clé requise)

Le fichier [.mcp.json](.mcp.json) est chargé automatiquement par Claude Code à l'ouverture du projet
(approuver les serveurs à la première utilisation) :

| Serveur | Rôle dans le projet |
|---|---|
| `parlement` (tricoteuses.fr) | HATVP : registre des représentants d'intérêts (avec SIREN), déclarations d'intérêts → détection de liens/conflits d'intérêts |
| `datagouv` (officiel) | Recherche de datasets + requêtage direct du contenu (DECP 3,1M de marchés par SIRET via l'API tabulaire) |
| `justicelibre` | ~3M décisions de justice + textes consolidés (Code de la commande publique) sans clé |
| `service-public` | Avis BOAMP, annuaire des administrations |

Vérifier la connexion : `claude mcp list` (ou `/mcp` dans une session Claude Code ouverte dans ce dossier).

## Stack de données du prototype (100 % sans authentification)

1. **Identité & finances du candidat** — API Recherche d'entreprises (`recherche-entreprises.api.gouv.fr`)
2. **Procédures collectives, radiations, dépôts de comptes** — BODACC (Opendatasoft DILA)
3. **Track-record marchés publics par SIRET** — DECP via API tabulaire data.gouv.fr (+ Parquet quotidien pour le batch)
4. **Avis et attributions** — BOAMP ; marchés européens — TED (POST sans clé)
5. **Sanctions & intégrité** — Gels des avoirs (DG Trésor), EU FSF, EDES, miroirs OpenSanctions (Banque mondiale…)
6. **Liens d'intérêts** — HATVP via l'API Tricoteuses Parlement
7. **Acheteurs locaux (SIREN/SIRET, contacts)** — Canutes PostgREST (`db.code4code.eu/canutes`)

Comptes gratuits à créer en avance (facultatif mais recommandé) : INPI RNE (comptes annuels PDF),
INSEE Sirene (source certifiée), Pappers (100 jetons), PISTE (Légifrance officiel — activation en plusieurs jours).

Détails complets, exemples de requêtes testées, limites, licences et pièges : **[docs/SOURCES.md](docs/SOURCES.md)**.

## Tester les sources

```powershell
./scripts/test-sources.ps1
```

Le script vérifie en ~30 s que les 4 serveurs MCP et les principales APIs répondent.
