# Hackathon 2026 — Transparence des marchés publics par l'IA et l'Open Data

Prototype **open source** d'aide aux acheteurs publics pour l'analyse des candidatures aux marchés publics :
agrégation automatique de sources Open Data, vérification de conformité administrative, analyse de documents,
**score de risque explicable**, tableaux de bord et **rapport d'aide à la décision** — avec transparence et traçabilité.

## État du projet

- [x] Recensement et **vérification en conditions réelles** de ~80 endpoints / 30 sources (03/07/2026) → [docs/SOURCES.md](docs/SOURCES.md)
- [x] Initialisation des serveurs MCP du projet → [.mcp.json](.mcp.json)
- [ ] Architecture du prototype (pipeline d'analyse, score, dashboard, rapport)
- [ ] Implémentation

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
