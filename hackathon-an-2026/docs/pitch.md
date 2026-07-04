# Pitch — Vigie Marchés (3 minutes)

> Support : les diapositives ([diapositives.pdf](diapositives.pdf)) et une démo live du front.
> Filet de sécurité : lancer l'API avec `VIGIE_OFFLINE=1` → la démo des 3 cas fonctionne sans réseau.

## 0:00 — Le problème (30 s)
« Chaque année, les collectivités analysent des milliers de candidatures aux marchés publics.
Pour vérifier un seul candidat, un acheteur doit consulter à la main l'INPI, le BODACC,
data.gouv, les listes de sanctions… C'est long, fastidieux, et difficile à maintenir.
Pire : **il n'existe aucun registre public des interdictions de soumissionner**. Aujourd'hui,
l'acheteur fait largement confiance à la déclaration sur l'honneur du candidat. »

## 0:30 — La solution (20 s)
« Vigie Marchés croise automatiquement les données ouvertes et produit un **score de risque
explicable et traçable**. Un identifiant SIREN, deux secondes, et l'acheteur voit tout —
avec, derrière chaque signal, sa source et sa date. »

## 0:50 — Démo, cas 1 : DANONE (30 s) — écran d'accueil → fiche VERT
« Je cherche Danone. Niveau **VERT** : entreprise saine. Mais regardez : l'outil signale qu'elle
est inscrite au **répertoire HATVP des représentants d'intérêts** — un point de vigilance
déontologique, pas un risque en soi. On ne cache rien, on contextualise. »

## 1:20 — Démo, cas 2 : DAVEO, le cas qui fait mouche (45 s) — fiche ROUGE
« Deuxième candidat, DAVEO. Dans l'annuaire officiel, l'entreprise apparaît **encore active** —
un acheteur pressé la retiendrait. Vigie Marchés, lui, a croisé le BODACC : **liquidation
judiciaire**. Niveau **ROUGE**, signal rédhibitoire, avec le motif d'interdiction de soumissionner
(article L2141-3 du Code de la commande publique) et **le lien vers la preuve, daté**.
C'est exactement l'angle mort que l'outil comble. »

## 2:05 — Ce qui nous différencie (35 s)
« Trois choses. Un : le score est **déterministe** — aucune IA dans le calcul, un barème public
et versionné ; l'IA ne sert qu'à **rédiger le rapport** d'aide à la décision, à partir des seuls
signaux calculés. Deux : une **API réutilisable** par n'importe quelle collectivité. Trois, et
c'est unique : un **serveur MCP** qui permet à un agent IA d'instruire un dossier en langage
naturel — aucun serveur MCP sur les marchés publics n'existait avant nous. »

## 2:40 — Conclusion (20 s)
« Vigie Marchés fait gagner un temps considérable à l'acheteur, objective le risque et trace
chaque signal — **sans jamais se substituer à son jugement**. L'outil signale et source ;
la décision reste humaine. Le tout, open source. Merci. »

---

### Réponses aux questions probables
- **« Et les faux positifs sur les sanctions ? »** Une correspondance de nom est toujours
  « à vérifier », jamais une condamnation : matching flou à 3 zones, similarité et source
  affichées. C'est un choix de conception assumé.
- **« La fiabilité des données ? »** Chaque table est datée et sourcée (page Méthodologie).
  On affiche aussi les *trous* : un compte non publié devient « indisponible », pas « OK ».
- **« En production ? »** Un acheteur habilité brancherait l'API Entreprise (attestations
  fiscales/sociales certifiées) ; les sources de sanctions primaires (DG Trésor, UE) sont
  libres. La seule dépendance non commerciale (OpenSanctions) est substituable.
- **« Combien de temps par candidat ? »** ~1,5 seconde d'analyse, contre plusieurs dizaines
  de minutes de consultations manuelles.
