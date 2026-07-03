# Inventaire des sources — APIs Open Data & serveurs MCP

> Toutes les URLs marquées ✅ ont été **testées par requête réelle le 03/07/2026** (statut HTTP + échantillon de réponse vérifiés).
> Contexte : outil open source IA + Open Data d'aide à l'analyse des candidatures aux marchés publics
> (vérification administrative/financière/juridique, score de risque explicable, rapport d'aide à la décision).

---

## 1. Serveurs MCP actifs dans le projet (`.mcp.json`)

Ces 4 serveurs distants fonctionnent **sans clé API** (transport MCP Streamable HTTP, testés) :

| Nom | URL | Contenu | Outils clés |
|---|---|---|---|
| `parlement` | `https://parlement.tricoteuses.fr/mcp` ✅ | Parlement FR (AN + Sénat) + **HATVP** | 17 outils : `search_global`, `search_acteurs`, `search_dossiers`, `get_details`, `summarize`… |
| `datagouv` | `https://mcp.data.gouv.fr/mcp` ✅ | Catalogue data.gouv.fr + **contenu des CSV** (API tabulaire) | `search_datasets`, `query_resource_data`, `search_dataservices`, `get_metrics` |
| `justicelibre` | `https://justicelibre.org/mcp` ✅ | ~3M décisions de justice (Cass, CE, CAA/TA, CEDH, CJUE) + LEGI/JORF/KALI | 24-29 outils, entrée : `search_all` (recherche fédérée BM25) |
| `service-public` | `https://mcp-service-public.nhaultcoeur.workers.dev/mcp` ✅ | service-public.fr, annuaire administrations, **BOAMP**, DVF | 38 outils dont `rechercher_marche_public` |

Notes :
- Ces serveurs exigent le transport **Streamable HTTP** : un GET simple renvoie 404/405/406, c'est normal — le client MCP fait des POST JSON-RPC.
- `justicelibre` et `service-public` sont communautaires (pas de SLA) mais open source et auto-hébergeables — plan B si indisponibles le jour J.
- Ajout manuel possible : `claude mcp add --transport http datagouv https://mcp.data.gouv.fr/mcp`

---

## 2. Ressources imposées par le hackathon

### 2.1 API Tricoteuses Parlement — `https://parlement.tricoteuses.fr`
- **Spec complète** : `https://parlement.tricoteuses.fr/openapi.json` ✅ (OpenAPI 3.1, 76 endpoints — la doc Scalar `/docs` tronque à l'affichage)
- **Auth** : aucune. Formats : `json` | `csv` | `rss` dans le chemin. Params : `page`, `perPage`, `search`, `select`, `sort`, `include`…
- **Le filon pour notre sujet — les endpoints HATVP** :
  - `GET /representantsInterets/json?page=1&perPage=5` ✅ → répertoire des représentants d'intérêts **avec SIREN** (`typeIdentifiantNational=SIREN`, `denomination`) → croiser le SIREN d'un candidat avec le registre lobbying.
  - `/declarants`, `/declarations` → déclarations d'intérêts des responsables publics (détection conflits d'intérêts acheteur ↔ candidat).
  - `/personnes_auditionnees_reunions` → candidat auditionné au Parlement ?
- Exemples testés : `/acteurs/json?chambre=AN&actif=true` ✅, `/dossiers/json?search=commande%20publique` ✅
- Licence ODbL-1.0 (à créditer). Les endpoints `/{uid}/resume` sont des résumés générés par IA (à sourcer comme tels).

### 2.2 Serveur MCP Parlement — `https://parlement.tricoteuses.fr/mcp` ✅
- La page de doc `tricoteuses.fr/services/mcp-parlement` est derrière l'anti-bot Anubis (OK en navigateur), mais **l'endpoint MCP lui-même est libre** (v0.4.0, testé sans auth).
- Test manuel : `curl -X POST https://parlement.tricoteuses.fr/mcp -H "Content-Type: application/json" -H "Accept: application/json, text/event-stream" -d '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}'`
- Code source AGPL-3.0 : `https://git.tricoteuses.fr/logiciels/tricoteuses-api-parlement` (le même logiciel génère l'API REST et le MCP).

### 2.3 Canutes — annuaire des services publics locaux (PostgREST) — `https://db.code4code.eu/canutes/`
- **Auth** : aucune en lecture. Racine = spec OpenAPI auto-générée ✅. Tables : `services` (37 400 lignes), `communes` (7 504), `version`.
- Données DILA (mairies & services locaux) : `nom`, `siren`, `siret`, `pivot[]` (type + code INSEE commune), `adresse[]` (avec lat/lon), `telephone[]`, `adresse_courriel`, `plage_ouverture[]`…
- **Syntaxe PostgREST testée** (encoder `->>` en `-%3E%3E` dans l'URL) :
  - Par SIREN : `services?data-%3E%3Esiren=eq.216500470&select=id,data-%3E%3Enom` ✅
  - Plein texte français : `services?text_search=wfts(french).mairie%20aureilhan&limit=3` ✅
  - Commune par code INSEE : `communes?id=eq.04145` ✅
  - Comptage : header `Prefer: count=exact` → `Content-Range`. Toujours paginer (`limit`/`offset`).
- **Usage** : valider l'identité SIREN/SIRET de l'acheteur, coordonnées officielles, géoloc (proximité candidat/acheteur).
- Limite : table `communes` partielle (~7 500 / 35 000 communes).

---

## 3. Vérifier une entreprise candidate

### 3.1 API Recherche d'entreprises (DINUM) — **la brique de base, sans clé**
- `https://recherche-entreprises.api.gouv.fr/search?q=<nom|siren|siret>` ✅ — spec : `/openapi.json` ✅
- Retourne : identité, `etat_administratif` (A/F), **dirigeants** (nom, prénoms, date naissance → croisement conflits d'intérêts), **finances par année** (`ca`, `resultat_net`), effectifs, catégorie (PME/ETI/GE), conventions collectives, labels (RGE, Qualiopi, ESS).
- Recherche par dirigeant : `?nom_personne=X&type_personne=dirigeant` ✅
- Limites : **7 req/s/IP**, 25 résultats/page max, ⚠️ **PAS de procédures collectives** (vérifié) → compléter avec BODACC.

### 3.2 BODACC (Opendatasoft DILA) — **le signal de risque juridique, sans clé**
- Base : `https://bodacc-datadila.opendatasoft.com/api/explore/v2.1/catalog/datasets/annonces-commerciales/records`
- Annonces d'un SIREN : `?where=registre like "552032534"&limit=10` ✅ (106 annonces pour Danone)
- **Procédures collectives** : `?where=registre like "<siren>" and familleavis_lib="Procédures collectives"&order_by=dateparution desc` ✅
- 11 familles d'avis ✅ : Procédures collectives, Radiations, Dépôts des comptes (le non-dépôt récurrent = red flag), Ventes et cessions…
- Champ `jugement` : nature ("Jugement d'ouverture de liquidation judiciaire"), date, complément.

### 3.3 Avec compte gratuit (à créer AVANT le hackathon)
| API | Auth | Apport |
|---|---|---|
| **INSEE Sirene** `https://api.insee.fr/api-sirene/3.11/siren/{siren}` | Clé sur portail-api.insee.fr, header `X-INSEE-Api-Key-Integration`, 30 req/min | Source certifiée qui fait foi (à citer dans le rapport) |
| **INPI RNE** `https://registre-national-entreprises.inpi.fr/api/companies/{siren}` | Compte data.inpi.fr → `POST /api/sso/login` → Bearer, ~15 000 req/j | **Comptes annuels PDF déposés**, actes, statuts — la source amont des données financières |
| **Pappers** `https://api.pappers.fr/v2/entreprise?siren=…&api_token=…` | 100 jetons gratuits (email pro) | Tout-en-un : finances + dirigeants + bénéficiaires effectifs + procédures collectives |

### 3.4 API Entreprise (`entreprise.api.gouv.fr`) — argument production du dossier
Réservée aux administrations habilitées (DataPass) : **attestations fiscales DGFIP et de vigilance URSSAF** certifiées (exigées des attributaires, art. R. 2143-6 CCP), liasses fiscales, Kbis, certifications Qualibat/Qualifelec/OPQIBI. Le prototype simule ces contrôles avec les sources ouvertes ; en prod chez un acheteur public, ils deviennent certifiés à la source.

---

## 4. Historique des marchés publics (le « track-record » du candidat)

### 4.1 DECP via l'API tabulaire data.gouv.fr — **le cœur du réacteur**
- Ressource `decp.csv` consolidée (rid `22847056-61df-452d-837d-8b8ceadbfc52`) : **3 101 841 marchés requêtables sans télécharger les 2,2 Go** :
  - `https://tabular-api.data.gouv.fr/api/resources/22847056-61df-452d-837d-8b8ceadbfc52/data/?montant__greater=1000000&columns=acheteur_nom,titulaire_nom,titulaire_id,montant,objet,codeCPV` ✅
  - Filtres : `__exact`, `__contains`, `__greater`… ; tri `col__sort=asc` ; **par SIRET titulaire : `titulaire_id__exact=<siret>`**
  - Swagger par ressource : `…/swagger/` ✅. Limites : page_size max 50, 100 req/s.
- Même donnée via Opendatasoft MEF : `https://data.economie.gouv.fr/api/explore/v2.1/catalog/datasets/decp-2022-marches-valides/records?where=titulaire_id_1="<siret>"` ✅ (656 837 marchés format 2022 ; ⚠️ titulaires aplatis en 3 colonnes max, valeurs manquantes = `"CDL"`)
- **Pour l'analyse batch / features du score** : Parquet quotidien (202 Mo) → `https://www.data.gouv.fr/api/1/datasets/r/11cea8e8-df3e-4ed1-932b-781e2635e432` ✅ → DuckDB (une ligne par couple marché-titulaire, dédupliquer par `id`).
- Signaux de risque calculables : concentration sur un acheteur, `offresRecues=1` récurrent, montants vs pairs du CPV, sous-traitance déclarée.

### 4.2 BOAMP (avis de marchés) — sans clé
- `https://boamp-datadila.opendatasoft.com/api/explore/v2.1/catalog/datasets/boamp/records` ✅ — 1 683 847 annonces, données du jour même.
- Attributions : `?where=nature="ATTRIBUTION" and dateparution>="2026-01-01"` ✅ (champ `titulaire` seulement sur les attributions).
- Champ `donnees` = JSON imbriqué (contenu complet de l'annonce) à parser.

### 4.3 TED (marchés européens) — recherche sans clé
- `POST https://api.ted.europa.eu/v3/notices/search` avec body `{"query":"buyer-country=FRA AND publication-date>20260601","fields":[…],"limit":2}` ✅ (POST uniquement)
- XML eForms d'un avis : `https://ted.europa.eu/en/notice/{num}/xml` ✅. Clé API seulement pour publication/validation.

### 4.4 APProch (projets d'achats à venir)
- `https://data.economie.gouv.fr/api/explore/v2.1/catalog/datasets/projets-dachats-publics/records` ✅ (11 793 projets)
- ⚠️ ODSQL : préfixe CPV avec joker `like "35*"` ou `startswith(code_s_cpv,"35")` — `like "35"` seul renvoie 0 ✅.

---

## 5. Sanctions & intégrité (sans clé sauf mention)

| Source | Accès testé | Contenu |
|---|---|---|
| **Gels des avoirs (DG Trésor)** — registre officiel FR | `https://gels-avoirs.dgtresor.gouv.fr/ApiPublic/api/v1/publication/derniere-publication-fichier-json` ✅ (~10 Mo, publié le jour même) | ONU + UE + gels nationaux ; champs `MOTIFS`, `FONDEMENT_JURIDIQUE` → parfait pour un rapport explicable |
| **EU FSF** — sanctions financières UE | `https://webgate.ec.europa.eu/fsd/fsf/public/files/csvFullSanctionsList_1_1/content?token=dG9rZW4tMjAxNw` ✅ (CSV 24 Mo ; token public générique) | Chaque entrée référence le règlement UE + URL EUR-Lex |
| **EDES** — exclusions budget UE | `POST https://ec.europa.eu/edes/api/cases/paginatedList` body `{"pageNumber":1,"pageSize":10,"sortColumn":"","sortOrder":""}` ✅ | ⚠️ GET → 500 ; réponse préfixée `)]}',` à retirer. Peu d'entrées mais signal très fort |
| **Banque mondiale (debarment)** | Miroir OpenSanctions : `https://data.opensanctions.org/datasets/latest/worldbank_debarred/targets.simple.csv` ✅ (l'API directe worldbank est 401/vide) | Exclusions pour fraude/corruption + cross-debarment BAD/BERD/BID |
| **OpenSanctions** | Bulk gratuit sans clé : `data.opensanctions.org/datasets/latest/{slug}/…` ✅ ; l'API `api.opensanctions.org` /search /match exige une clé (401 vérifié) | 320+ listes consolidées (sanctions, **PEP**, exclusions). Self-host possible : yente (Docker, MIT) |

⚠️ **Licence OpenSanctions : CC-BY-NC** — OK pour le prototype, mais un déploiement commercial/production nécessite une licence (le self-host yente ne lève pas cette contrainte). Les sources primaires (gels-avoirs, FSF, EDES) sont libres.

📌 **Constat juridique utile pour le pitch** : il n'existe AUCUN registre public français des interdictions de soumissionner (art. L.2141-1 s. CCP — le B2 n'est pas public ; vérification = déclaration sur l'honneur DUME). C'est exactement la lacune que l'outil comble en croisant les signaux ouverts. L'outil produit des **signaux de risque**, pas des preuves d'exclusion.

---

## 6. Juridique (Code de la commande publique, jurisprudence)

- **JusticeLibre** (déjà dans `.mcp.json`) : zéro clé, ~3M décisions + textes consolidés. Alternative sans friction aux MCP Légifrance.
- **droit-francais-mcp** (jmtanguy, GitHub) : Légifrance + Judilibre officiels via **PISTE** — identifiants gratuits sur piste.gouv.fr mais **activation en plusieurs jours → à demander tout de suite si on en veut**.
- **mcp-server-legifrance** (pylegifrance) : passe par une API tierce (lab.dassignies.law), clé à demander à l'auteur.

---

## 7. Serveurs MCP optionnels (clé/compte requis) — configs prêtes

```jsonc
// À fusionner dans .mcp.json si les clés sont obtenues :
{
  "mcpServers": {
    // Screening sanctions/PEP (6 outils dont investigate_entity).
    // Option 100% gratuite : pointer OPENSANCTIONS_API_URL vers un yente Docker local.
    "opensanctions": {
      "command": "npx",
      "args": ["-y", "opensanctions-mcp"],
      "env": {
        "OPENSANCTIONS_API_KEY": "VOTRE_CLE",
        "OPENSANCTIONS_API_URL": "https://api.opensanctions.org"
      }
    },
    // Pappers officiel : 35+ outils (finances, procédures collectives, BE, justice).
    // Clé API Pappers en Bearer ; 100 crédits gratuits (email pro).
    "pappers": { "type": "http", "url": "https://mcp.pappers.fr" },
    // BOAMP + TED unifiés + "winner intelligence" (stats par attributaire).
    // Clé gratuite sur tenderapi.fr (100 req/j).
    "tenderapi": { "command": "tenderapi-mcp", "env": { "TENDERAPI_KEY": "ta_votre_cle" } }
  }
}
```

Autres recensés : `ted-mcp` (fbuchner, TED sans clé, clone+uv), `boamp-server` (stefw, build manuel), `mcp-insee-entreprises` (DavidScanu, clé INSEE), MCP Factory/juri-mcp (commercial 40€/mois — écarté), `french-admin-mcp` (hors sujet — écarté), `mcp-recherche-entreprises` (ARCHIVÉ, remplacé par datagouv-mcp).

💡 **Aucun MCP dédié DECP/BODACC n'existe** : un serveur MCP maison `recherche_marches_par_siret` / `screening_candidat` au-dessus des APIs ci-dessus est un **livrable différenciant** du hackathon.

---

## 8. Pièges techniques vérifiés (à ne pas redécouvrir le jour J)

1. **EDES** : POST obligatoire (GET = 500) ; retirer le préfixe anti-XSSI `)]}',` avant `JSON.parse`.
2. **ODSQL (Opendatasoft)** : `like "35"` ne matche pas un préfixe → `like "35*"` ou `startswith()`.
3. **DECP MEF** : valeurs manquantes = chaîne `"CDL"` ; titulaires limités à `titulaire_id_1..3`.
4. **PostgREST Canutes** : encoder `->>` en `-%3E%3E` ; toujours `limit`/`offset`.
5. **Serveurs MCP Streamable HTTP** : GET simple → 404/405/406 (normal) ; tester avec POST JSON-RPC + header `Accept: application/json, text/event-stream`.
6. **Anti-bots** : annuaire-entreprises (Incapsula), pappers.fr, data.inpi.fr, portail tricoteuses.fr (Anubis) bloquent les fetchs automatisés — **utiliser les APIs, pas le scraping**.
7. **API Recherche d'entreprises** : `include=` seulement avec `minimal=true` (400 sinon) ; 429 + `Retry-After` au-delà de 7 req/s.
8. **rid data.gouv.fr** : peuvent changer si le producteur recrée la ressource → les résoudre dynamiquement via l'API catalogue.
9. **data.gouv ressources** : les URLs `/api/1/datasets/r/{rid}` redirigent (302) vers static.data.gouv.fr → `curl -L`.

## 9. Licences à créditer
- Tricoteuses / Canutes Parlement : **ODbL-1.0** ; annuaire Canutes : © DILA.
- BOAMP/BODACC : etalab-2.0. DECP : Licence Ouverte 2.0.
- OpenSanctions : **CC-BY-NC 4.0** (⚠️ non commercial).
