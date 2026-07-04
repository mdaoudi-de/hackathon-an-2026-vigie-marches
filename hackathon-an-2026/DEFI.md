### Nom du défi
Vigie Marchés — IA et Open Data pour la transparence des marchés publics

### Description courte
Un outil open source qui assiste les acheteurs publics dans l'analyse des candidatures aux marchés publics : agrégation automatique de sources Open Data, vérification de la conformité administrative, score de risque explicable et rapport d'aide à la décision — avec transparence et traçabilité de chaque signal.

### Porteur
Vigie Marchés

### Description longue
**Contexte.** Chaque année, les collectivités et administrations analysent des milliers de candidatures aux marchés publics. Ces vérifications (situation administrative, financière et juridique des candidats) exigent de consulter manuellement de nombreuses sources : INPI, data.gouv.fr, BODACC, BOAMP, listes de sanctions… Un travail chronophage, difficile à maintenir, et sans registre centralisé : il n'existe aujourd'hui **aucun registre public français des interdictions de soumissionner** (art. L.2141-1 s. du Code de la commande publique) — la vérification repose sur la déclaration sur l'honneur du candidat.

**Objectif.** Vigie Marchés croise automatiquement les données ouvertes pour objectiver le risque d'une candidature et produire un **score de risque explicable** : chaque signal est tracé jusqu'à sa source (URL, date de consultation, base légale citée), afin que l'acheteur décide en connaissance de cause.

**Ce que fait l'outil :**
- **Identité et santé financière** du candidat : API Recherche d'entreprises (dirigeants, finances), BODACC (procédures collectives, radiations, dépôts de comptes) ;
- **Track-record réel** : historique des marchés remportés par SIRET dans les DECP (3,1 millions de marchés requêtables) et les avis BOAMP/TED ;
- **Intégrité** : screening contre le registre des gels des avoirs (DG Trésor), les sanctions financières de l'UE, les exclusions EDES et Banque mondiale ;
- **Liens d'intérêts** : croisement du SIREN candidat avec le répertoire HATVP des représentants d'intérêts et détection de proximités acheteur/candidat, via l'API et le serveur MCP Parlement (LegiWatch/Tricoteuses) ;
- **Restitution** : tableau de bord des risques et génération automatique d'un rapport d'aide à la décision, sourcé et horodaté.

**Approche technique.** Prototype open source construit sur une architecture « MCP-first » : l'agent IA interroge les données via des serveurs MCP (Parlement, data.gouv.fr, jurisprudence, service-public) et des APIs ouvertes vérifiées — l'inventaire complet des sources testées est publié dans les documents ci-dessous. Aucun scraping : uniquement des accès documentés et reproductibles.

**Déroulé.** 1) Dépôt d'une candidature (SIREN/SIRET + documents) → 2) collecte parallèle sur toutes les sources → 3) calcul des signaux et du score explicable → 4) dashboard + rapport exportable.

### Image principale
![Image principale](images/cover.png)

### Contributeurs
- Mohamed (@mdaoudi-de)

### Ressources utilisées
Cochez les ressources utilisées en remplaçant `[ ]` par `[x]`.

- [ ] `openfisca-france-parameters` — Base de données de paramètres ✺ OpenFisca
- [ ] `an-dossiers-legislatifs` — Dossiers législatifs de l'Assemblée nationale (législature courante) ✺ Assemblée nationale
- [ ] `an-amendements-xvii` — Amendements déposés à l'Assemblée nationale (législature actuelle) ✺ Assemblée nationale
- [ ] `an-comptes-rendus` — Comptes rendus de la séance publique à l'Assemblée nationale (législature actuelle) ✺ Assemblée nationale
- [ ] `an-votes-xvii` — Votes des députés (législature actuelle) ✺ Assemblée nationale
- [ ] `an-deputes-en-exercice` — Députés en exercice ✺ Assemblée nationale
- [ ] `an-deputes-historique` — Historique des députés ✺ Assemblée nationale
- [ ] `an-deputes-senateurs-ministres-par-legislature` — Députés, sénateurs et ministres d'une législature ✺ Assemblée nationale
- [ ] `an-agenda-reunions` — Agenda des réunions à l'Assemblée nationale (législature courante) ✺ Assemblée nationale
- [ ] `an-questions-gouvernement` — Questions de l'Assemblée nationale au Gouvernement ✺ Assemblée nationale
- [ ] `an-questions-gouvernement-ecrites` — Questions écrites de l'Assemblée nationale au Gouvernement ✺ Assemblée nationale
- [ ] `an-questions-gouvernement-orales` — Questions orales de l'Assemblée nationale au Gouvernement ✺ Assemblée nationale
- [ ] `premier-ministre-legi` — Codes, lois et règlements consolidés ✺ Premier ministre
- [ ] `premier-ministre-dole` — Dossiers législatifs Légifrance ✺ Premier ministre
- [ ] `premier-ministre-jorf` — Édition ''Lois et décrets'' du Journal officiel ✺ Premier ministre
- [ ] `senat-dispositifs-textes` — Dispositifs des textes déposés ou adoptés au Sénat ✺ Sénat
- [ ] `senat-dossiers-legislatifs` — Dossiers législatifs du Sénat ✺ Sénat
- [ ] `senat-amendements` — Amendements déposés au Sénat ✺ Sénat
- [ ] `senat-senateurs` — Sénateurs ✺ Sénat
- [ ] `senat-questions-gouvernement` — Questions orales et écrites du Sénat au Gouvernement ✺ Sénat
- [ ] `senat-comptes-rendus` — Comptes rendus de la séance publique au Sénat ✺ Sénat
- [x] `an-et-co-database-regroupement-toutes-donnees` — Base de données unifiée Parlement / Législation / Service Public ✺ Assemblée nationale & communauté
- [ ] `an-et-co-serveur-mcp-regroupement-toutes-donnees` — Serveur MCP  - Accès unifié Parlement / Législation / Service Public ✺ Assemblée nationale & communauté
- [x] `an-et-co-api-regroupement-toutes-donnees` — API - Accès unifié Parlement / Législation / Service Public ✺ Assemblée nationale & communauté
- [x] `legiwatch-api-parlement` — API Parlement ✺ LegiWatch
- [ ] `legiwatch-database-parlement` — Base de données Parlement ✺ LegiWatch
- [x] `legiwatch-serveur-mcp-parlement` — Serveur MCP Parlement ✺ LegiWatch

### Galerie
- [Écran d'accueil — recherche et cas de démonstration](images/ecran-accueil.png)
- [Fiche d'analyse — cas ROUGE (DAVEO en liquidation), chaque signal sourcé](images/ecran-analyse-rouge.png)
- [Page méthodologie — barème public et provenance des données](images/ecran-methodologie.png)
- [Serveur MCP « vigie-marches » — l'analyse exposée en outils agentiques](images/ecran-mcp.png)

### Documents
- [Inventaire des sources Open Data vérifiées](docs/sources-verifiees.md)
- [Script de présentation (pitch 3 minutes)](docs/pitch.md)

### URL de démonstration
Démonstration locale (le dépôt est autonome) — voir le démarrage rapide du README.
Le jeu de démonstration hors-ligne (`VIGIE_OFFLINE=1`) permet de présenter les 3 cas sans réseau.

### Diapositives de présentation
[Diapositives de présentation](docs/diapositives.pdf)
