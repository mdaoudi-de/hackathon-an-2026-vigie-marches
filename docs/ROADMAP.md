# Vigie Marchés — Plan de travail par runs (hackathon AN 2026, remise < 1 semaine)

## Contexte

Le socle données est terminé et vérifié : inventaire de ~30 sources (docs/SOURCES.md), 4 serveurs MCP (.mcp.json), ingestion testée → `data/vigie.duckdb` (921 Mo : 3,1 M marchés DECP, sanctions, HATVP, acheteurs, table `_provenance`), 5 clients API (ingestion/clients.py), dossier hackathon-an-2026/ conforme.

Reste à construire le prototype : **moteur de score explicable → API FastAPI → front React → rapport IA → serveur MCP maison → finitions**. Choix actés : échéance < 1 semaine ; FastAPI + React/Next ; IA « les deux » (API Claude pour le rapport + MCP maison pour la démo agentique) ; PDF de candidature en optionnel.

Principe : **1 run = 1 session Claude Code = 1 livrable démontrable + intitulé de commit** (l'utilisateur committe lui-même). Demo-first, chemin critique d'abord.

Cas de démo : Danone `552032534` (sain + registre HATVP), NEOLEDGE SIRET `75058171200015` (74 marchés DECP, 43 % offre unique), + 1 SIREN en liquidation à identifier au Run 1 (cas ROUGE).

## Calendrier et architecture cible

| Jour | Run |
|---|---|
| J1 | **Run 1** — Moteur de score + CLI |
| J2 | **Run 2** — API FastAPI (contrat gelé ensuite) |
| J2–J3 | **Run 3** — Front Next.js |
| J4 | **Run 4** — Rapport Claude ∥ **Run 5** — MCP maison (parallélisables) |
| J5 | **Run 6** — Polish + livrables hackathon |
| J6 | Tampon + optionnels (O1 PDF, O2 déploiement) |

```
vigie/            # cœur partagé, AUCUNE dépendance web — écrit 1 fois, démontré 3 fois (CLI, API, MCP)
  modeles.py      # Pydantic : Preuve, Signal, Analyse (sert aussi de schémas FastAPI)
  bareme.py       # poids, seuils, stop-words formes juridiques, VERSION_BAREME="1.0"
  db.py           # DuckDB read_only + requêtes locales
  signaux/        # identite.py, financier.py, procedures.py, sanctions.py, track_record.py, lobbying.py
  moteur.py       # orchestre les 6 familles → Analyse
  cli.py          # python -m vigie.cli <siren> [--json]
api/              # FastAPI (Run 2)     front/    # Next.js (Run 3)
vigie_mcp/        # FastMCP (Run 5)     data/fixtures/  # réponses enregistrées → démo hors-ligne
```

---

## Run 1 — Moteur de score déterministe et explicable (le cœur)

**6 familles de signaux** :

| Famille | Source | Signaux clés |
|---|---|---|
| identite | `clients.recherche_entreprise` | introuvable, état cessé, ancienneté < 1 an |
| financier | idem (bloc finances) | comptes absents/anciens (`indisponible`, affiché), résultat négatif, CA en baisse |
| procedures_collectives | `clients.bodacc_annonces` | liquidation en cours (**rédhibitoire**), redressement (majeur), sauvegarde (mineur), radiation |
| sanctions_integrite | tables locales gels_avoirs, eu_fsf (`NameAlias_WholeName`), edes, os_worldbank_debarred, os_eu_edes | correspondance de nom → toujours `a_verifier`, jamais rouge automatique |
| track_record | `v_decp_stats_titulaire` + `decp` | volume/récence (info) ; anomalies avec garde-fou `nb_marches ≥ 5` : `part_offre_unique > 0,5`, 1er acheteur > 80 % (GROUP BY acheteur_id) |
| lobbying | `v_lobbying` (SIREN direct) | inscription HATVP = signal **informatif 0 pt** (« vigilance déontologique ») |

**Barème défendable (bareme.py)** : décalque des interdictions de soumissionner (art. L2141-1 s. CCP). Gravités info 0 / mineur 5-10 / majeur 15-25 pts, plafond 30 pts/famille, `redhibitoire` → ROUGE immédiat. Niveaux : VERT < 20, ORANGE 20-49 ou signaux `a_verifier`, ROUGE ≥ 50 ou rédhibitoire. Source indisponible = statut `indisponible` (0 pt mais visible).

**Sortie JSON 100 % traçable** (contrat pour API/front/rapport/MCP) : `candidat`, `score {niveau, points, version_bareme, redhibitoire}`, `familles[].signaux[]` avec chacun `{libelle, statut ok|declenche|a_verifier|indisponible, valeur, gravite, points, preuve {source, url, collecte_le, licence, detail}}`, `avertissements[]`. Règle absolue : **aucun signal sans preuve** — `collecte_le`/`licence` viennent de `_provenance` (tables locales) ou de `source_url` (clients.py) ; les deux existent déjà, il suffit de propager.

**Matching sanctions (homonymies)** : normalisation (majuscules, accents via `unicodedata`, formes juridiques en stop-words) ; `rapidfuzz.fuzz.token_sort_ratio` (à ajouter à requirements.txt) ; 3 zones : ≥ 95 `a_verifier` majeur, 88-94 `a_verifier` mineur, < 88 ignoré mais affiché (« aucune correspondance ≥ 88 % sur N entrées ») ; modérateur pays (worldbank `countries`) ; personnes physiques des gels comparées aux **dirigeants** (recherche-entreprises), pas à la raison sociale. Message pitch : « l'outil ne condamne pas, il signale quoi vérifier ».

**Vérification** : trouver le cas ROUGE en début de run (BODACC ODSQL `familleavis_lib="Procédures collectives"` + jugement liquidation, récent ; candidats à confirmer : Camaïeu 345086177…) et le consigner dans `data/fixtures/cas_demo.md`. Puis :
`python -m vigie.cli 552032534` (VERT + lobbying info), `75058171200015` (track-record non vide), `<SIREN_ROUGE>` (ROUGE rédhibitoire), `--json | python -m json.tool`. 4-5 tests pytest sur la partie pure (barème, matching homonymies, agrégation) — pas de réseau.

**Commit** : `feat(moteur): moteur de score explicable — 6 familles de signaux, barème v1.0 aligné L2141, sortie JSON traçable, CLI`

## Run 2 — API REST FastAPI documentée

Endpoints : `GET /api/sante`, `/api/candidats?q=` (autocomplete), **`/api/analyses/{siren_ou_siret}`** (JSON du moteur tel quel), `/api/screening/sanctions?nom=`, `/api/track-record/{siret}`, `/api/provenance`, `/api/bareme` (méthodologie servie au front sans duplication).

Points techniques : schémas = `vigie/modeles.py` (Pydantic dès Run 1) ; DuckDB `read_only=True`, une connexion par requête ; **cache TTL 15 min** en mémoire (quota 7 req/s + démo instantanée) ; CORS localhost:3000 ; **mode `VIGIE_OFFLINE=1`** servant `data/fixtures/` (assurance démo jury). Fin de run : **contrat gelé**, le front avance en parallèle.

**Vérification** : uvicorn + curl des 3 cas + `/docs` en français ; enregistrer les 3 réponses dans `data/fixtures/`.
**Commit** : `feat(api): API REST FastAPI documentée (analyse, screening sanctions, track-record, provenance, barème)`

## Run 3 — Front Next.js (3 écrans, pas d'auth)

1. **Accueil/recherche** : autocomplete + **3 boutons « cas de démo »** (pitch fluide).
2. **Fiche d'analyse** `/analyse/[siren]` : bandeau identité, pastille VERT/ORANGE/ROUGE, carte par famille, tableau des signaux avec **lien « preuve » (URL source + date)** — l'écran que le jury retiendra.
3. **Méthodologie** : barème via `/api/bareme` + tableau `_provenance`.

Next.js App Router + Tailwind, fetch server-side, jauge en SVG/CSS (pas de lib de charts). Repli si retard : fusionner écrans 1 et 2.
**Vérification** : dérouler les 3 cas au clic ; chaque signal a un lien preuve ; captures → `hackathon-an-2026/images/`.
**Commit** : `feat(front): interface Next.js — recherche, fiche d'analyse avec preuves, page méthodologie`

## Run 4 — Rapport d'aide à la décision par Claude (∥ Run 5)

`vigie/rapport.py` + `GET /api/analyses/{siren}/rapport` : note 1-2 pages Markdown. **Garde-fou : l'IA ne reçoit QUE le JSON du moteur et ne calcule rien** — plan imposé (synthèse → décision proposée → détail → points à vérifier → limites), citation de source obligatoire après chaque fait, rappel « la décision reste humaine ». SDK `anthropic`, streaming, prompt système stable avec cache ; clé via `ANTHROPIC_API_KEY` (.env ignoré par git) ; ~0,08 $/rapport, mis en cache TTL. ⚠️ **Lire la skill `claude-api` au début de ce run** pour valider modèle et paramètres à jour. Front : bouton « Générer le rapport », rendu Markdown, téléchargement `.md`.

**Vérification** : rapports NEOLEDGE + cas rouge, relecture anti-hallucination croisée (chaque affirmation traçable au JSON) ; comportement propre sans clé API.
**Commit** : `feat(rapport): rédaction du rapport d'aide à la décision par Claude à partir des seuls signaux calculés`

## Run 5 — Serveur MCP « vigie-mcp » (∥ Run 4) — le différenciant

Aucun MCP DECP/BODACC n'existe : `vigie_mcp/serveur.py` (FastMCP, stdio) expose le même moteur en outils : `analyser_candidat(siren_ou_siret)`, `screening_sanctions(nom)`, `track_record_marches(siret, limite)`, `rechercher_entreprise(q)`, `sources_donnees()`. Docstrings soignées (c'est ce que voit le modèle), DuckDB read-only, ajout dans `.mcp.json` (command = .venv/Scripts/python -m vigie_mcp.serveur).

**Vérification** : `claude mcp list` ; démo réelle : « Analyse la candidature de NEOLEDGE (75058171200015), sanctions + historique, compare avec Danone » → enchaînement d'outils observé ; **GIF/captures enregistrés** pour la galerie (assurance si la démo live échoue).
**Commit** : `feat(mcp): serveur MCP vigie-mcp (FastMCP) — l'analyse de candidats exposée en outils agentiques`

## Run 6 — Polish et livrables hackathon

`LICENSE` MIT (+ mention CC-BY-NC des miroirs OpenSanctions dans le README) ; README refondu (schéma d'architecture, quickstart 5 commandes, tableau des familles, limites) ; **DEFI.md complété** (galerie captures + GIF MCP, URL démo, diapositives) ; diapositives PDF ~8 slides dans `hackathon-an-2026/docs/` ; script de pitch 3 min sur les 3 cas ; répétition en `VIGIE_OFFLINE=1`.

**Vérification** : « test du clone » — suivre le README de zéro sur poste propre (venv → `ingest_all --decp-remote` → uvicorn → npm run dev) ; checklist du template DEFI.md 100 % cochée.
**Commit** : `docs: finalisation des livrables hackathon (README, LICENSE, DEFI.md, galerie, diapositives)`

## Runs optionnels (si J6 disponible)

- **O1 — PDF DC1/DC2/DUME** : `POST /api/documents` → Claude (bloc document PDF) extrait SIREN/mandataire/sous-traitants → chaque SIREN passe au moteur. Vérif : un DC1 avec le SIREN rouge lève l'alerte. Commit : `feat(documents): extraction DC1/DC2 par Claude et contrôle croisé des SIREN déclarés (optionnel)`
- **O2 — Déploiement démo** : `scripts/build_db_demo.py` (matérialise v_decp_stats_titulaire, droppe `decp` → ~60-80 Mo), API Fly.io/Railway + front Vercel ; repli : vidéo + démo locale. Commit : `chore(deploy): base allégée et déploiement de démonstration (optionnel)`

## Risques → mitigations

| Risque | Mitigation |
|---|---|
| Front sous-estimé | Contrat gelé fin Run 2 + fixtures dès Run 1 (dev front sur mocks) ; scope 3 écrans ; repli page unique |
| Quotas API (7 req/s…) | Cache TTL, retries existants, `VIGIE_OFFLINE` pour le jury |
| Homonymies sanctions | `a_verifier` jamais bloquant, 3 zones de seuil, similarité affichée — assumé dans le pitch |
| Qualité DECP | Garde-fous `nb_marches ≥ 5`, avertissement « données déclaratives » |
| Hallucination rapport | IA = mise en forme du JSON uniquement, citations obligatoires, relecture croisée |
| Démo MCP live | GIF enregistré au Run 5 |
| DuckDB single-writer | `read_only=True` partout hors ingestion ; pas d'ingestion pendant la démo |

## Fichiers existants à réutiliser (ne pas réécrire)

- `ingestion/clients.py` — 5 clients avec `source_url` (traçabilité prête)
- `ingestion/common.py` — session retries + `_provenance` (ajouter l'ouverture read-only)
- `ingestion/ingest_decp.py` — colonnes exactes de `v_decp_stats_titulaire`
- `ingestion/config.py` — DB_PATH et URLs vérifiées à citer dans les preuves
- `hackathon-an-2026/DEFI.md` — à compléter au Run 6
