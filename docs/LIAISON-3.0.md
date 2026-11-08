# Liaison SquidBot 3.0 → SquidBots Dashboard (proposition CoA Dashboard, 08/11)

Réponse à VISION-3.0 §4 bis. Le Builder code le côté module.

**Statut (08/11)** : principe accepté par le Builder, avec les modifications du §6 (elles priment sur le reste du document). Il lancera le module après le banc CPU A/B (chantier 0), sur l'ordre du Pilote. Non surveillé, le module doit rester dans le bruit de mesure. Les champs de `groups.json` et `runs.jsonl` restent à arrêter avec CoA Dungeon Clear.

## 1. Choix : des fichiers JSON écrits par le module, pas d'API HTTP

On prolonge ce qui marche déjà : `bot-status.json`, écrit par `CoaStatusFile.cpp`. Le monde construit le snapshot (moins de 1 ms pour 1000 bots), un thread à part écrit `.tmp` puis renomme, et le dashboard met la lecture en cache selon (mtime, taille).

| | Fichiers JSON | API HTTP dans le worldserver |
|---|---|---|
| Coût CPU | construction sur le thread monde, à intervalle fixe, à partir de compteurs déjà tenus ; écriture hors du thread monde | chaque requête lit les objets du monde : il faut un verrou ou une copie, avec le même coût en plus de la pile HTTP |
| Lecteurs multiples | gratuits (le cache du dashboard, le Manager, les scripts du banc, `jq`) | une requête par lecteur |
| Sécurité | aucun port, aucune popup du pare-feu ; la lecture suit les droits du dossier logs | un port à ouvrir, à lier sur 127.0.0.1 et à authentifier |
| Fraîcheur | l'intervalle de chaque sujet, de 5 à 60 s : assez pour un tableau de bord | immédiate (inutile ici) |
| Code module | on étend un écrivain qui existe déjà | un serveur HTTP à embarquer et à maintenir |

Les **actions** (commandes aux bots) ne passent pas par un fichier. Elles passent par la console RA, que le dashboard utilise déjà (`webapp/ra.py`, authentifiée, réservée aux comptes GM), avec des commandes `.squidbot …` du module. Il n'y a ni nouveau port ni boîte aux lettres écrivable.

## 2. Rien ne coûte quand personne ne regarde

- Le dashboard écrit `squidbot/watch.json` toutes les 30 s pendant qu'une page qui en a besoin est ouverte, par exemple `{"at": 1762600000, "topics": ["world", "economy"]}`.
- Le module ne lit que la date de ce fichier (un `stat`), toutes les 5 s. Il ne construit un sujet que si on l'a demandé il y a moins de 90 s. Sans lecteur, le coût se réduit à ce `stat`.
- `runs.jsonl` est la seule exception : une ligne par run DC terminé, toujours écrite, pour garder un historique complet (le coût est négligeable).
- `CoaStatusFile`, la règle existante, reste valable : `""` coupe tout. Le dossier vient de `AiPlayerbot.CoaDataDir` (par défaut, `squidbot/` à côté de `bot-status.json`).

## 3. Les fichiers

Toujours dans `<logs>/squidbot/`. Chaque fichier a la même enveloppe :

```json
{ "schema": "squidbot.world/1", "at": 1762600000, "every": 10, "build_us": 420, "data": { … } }
```

- `schema` : sujet et version majeure. Le dashboard accepte une version mineure plus récente et ignore les champs qu'il ne connaît pas. Il refuse une version majeure qu'il ne connaît pas et le dit.
- `at` : epoch du snapshot ; un fichier plus vieux que 3 × `every` est périmé.
- `build_us` : coût sur le thread monde, pour le suivi pmon.

| Fichier | `every` | Contenu de `data` |
|---|---|---|
| `bot-status.json` | 5 s | existant, inchangé (un bot par entrée) |
| `world.json` | 10 s | population et santé |
| `economy.json` | 60 s | marché, crafts, commandes |
| `groups.json` | 15 s | runs en cours et cumul du jour |
| `runs.jsonl` | à chaque fin de run | une ligne par run terminé |
| `events.jsonl` | au fil de l'eau | journal en direct : erreurs, bots coincés, boss, wipes. Rotation à 5 Mo, en gardant le `.1` |

### world.json
```json
{ "online": 487, "players": 2,
  "zones":  [{"map": 0, "zone": 1519, "bots": 61, "capital": true}],
  "activities": {"quest": 212, "grind": 64, "city": 88, "travel": 41, "fish": 9, "pvp": 23, "dungeon": 35, "idle": 15},
  "personalities": {"merchant": 74, "crafter": 51, "adventurer": 190, "explorer": 62, "duelist": 40, "homebody": 70},
  "health": { "tick_ms": {"avg": 38, "p95": 61, "max": 140},
              "bots_us_per_tick": {"avg": 9200, "p95": 15800},
              "by_strategy_us": [{"name": "rpg", "us": 3100}, {"name": "travel", "us": 1900}],
              "stuck": [{"guid": 1234, "name": "Arwen", "map": 1, "x": 0, "y": 0, "z": 0, "since": 1762599700, "why": "no path"}],
              "errors_10m": 3 } }
```
Les activités viennent de la stratégie active (même table que `ActionTasks`). Les personnalités sont les caractères 3.0 (patience, épargne…), regroupés en profils.

### economy.json
```json
{ "auctions": 3120, "gold_circulating": 18450000, "gold_bots": 16200000,
  "categories": [{"class": 7, "sub": 5, "auctions": 410, "avg": 2350, "low": 900, "usual": 2100, "high": 4800, "volume_24h": 380}],
  "top_sales_24h": [{"item": 14047, "count": 212, "gold": 640000}],
  "crafts_24h": [{"skill": 197, "item": 14048, "count": 31, "profit": 52000}],
  "orders": [{"id": 77, "buyer": "Squid", "bot": "Thorgal", "item": 14154, "price": 1250000, "state": "crafting", "at": 1762599000}] }
```
Les montants sont en cuivre. `low/usual/high` sont les bandes de prix du §2 de la vision.

### groups.json et runs.jsonl
```json
{ "running": [{"run": 9812, "dungeon": 36, "bots": 5, "players": 0, "started": 1762599100, "boss_done": 2, "boss_total": 5, "wipes": 0}],
  "today": {"runs": 42, "cleared": 37, "wipes": 11, "boss_kills": 168},
  "by_dungeon": [{"dungeon": 36, "runs": 9, "cleared": 9, "median_s": 1420, "best_s": 1180, "wipes": 1}] }
```
Une ligne de `runs.jsonl` : `{"run":9812,"dungeon":36,"start":…,"end":…,"result":"clear|wipe|abandon","bosses":[{"id":639,"t":312}],"wipes":1,"group":["Arwen",…]}`. C'est le format du banc DC, joué ici en jeu réel, pour que les deux se comparent.

### events.jsonl
`{"at":…,"kind":"error|stuck|unstuck|boss|wipe|order","bot":"…","text":"…"}`. Le dashboard le lit en `tail` (comme Chat.log aujourd'hui) et l'affiche en direct.

## 4. Actions (3.0, deuxième temps)
Les commandes RA du module sont `.squidbot bot <nom> stop|resume|summon|unstuck`, `.squidbot order cancel <id>` et `.squidbot reload`. Le dashboard n'envoie que des commandes d'une liste blanche, et seulement depuis ses pages privées. Le module vérifie le niveau GM du compte RA.

## 5. Côté dashboard
- `webapp/vivant.py` lit les fichiers, met chacun en cache selon (mtime, taille) et écrit `watch.json`. Quand un fichier manque, il sert des **données factices** marquées `"demo": true`, et la page affiche alors un bandeau.
- Une page privée « Monde vivant » (`#vivant`) a quatre onglets : Population, Économie, Groupes, Santé. Elle n'est jamais publiée dans la copie publique.

## 6. Décisions du Builder (08/11), qui priment sur ce qui précède
- L'enveloppe gagne `server_start` (epoch) et `module` (sha court), pour repérer un redémarrage ou un changement de version.
- L'écriture passe par `.tmp` puis `MoveFileEx(REPLACE_EXISTING)`. Si le dashboard tombe sur une violation de partage, il réessaie une fois après 100 ms (c'est fait dans `webapp/vivant.py`).
- `world.json` sort de la même passe que `bot-status.json`, sans scan en plus. `tick_ms` vient des statistiques du cœur.
  - `bots_us_per_tick` et `by_strategy_us` valent `null` sans PerfMon.
  - `stuck` vaut `null` jusqu'au détecteur 3.0, et `personalities` jusqu'à la fonction 3.0.
  - `errors_10m` est **retiré** : les entrées `error` de `events.jsonl` le remplacent.
- `economy.json` (60 s, seulement s'il est surveillé) fait une passe sur l'hôtel des ventes. `gold_*` vient d'une requête asynchrone mise en cache. Les bandes de prix, `crafts_24h` et `orders` restent des tableaux vides jusqu'à l'économie 3.0.
- `groups.json` et `runs.jsonl` : l'état des runs appartient à Dungeon Clear. Le module n'écrit que ce que DC expose, au format du banc DC.
- Réglages : `AiPlayerbot.CoaDataDir` (`""` = `<Logs>/squidbot`) et `AiPlayerbot.CoaDataFiles = 1` (`0` coupe tout, y compris `runs.jsonl`).

## 7. Maquette (branche `feature/vivant-3.0` du dépôt dashboard)
- `webapp/vivant.py` lit les fichiers et met en cache selon (mtime, taille). Il vérifie la version du schéma, signale un fichier périmé au-delà de 3 × `every`, et réécrit `watch.json` toutes les 30 s, mais seulement si le dossier `squidbot/` existe.
- Pour chaque sujet absent, il sert des données factices, signalées par un bandeau.
- `static/vivant.js` : la page privée `#vivant` (Population, Économie, Groupes et donjons, Santé). Les `null` du §6 s'affichent « – » ou « arrive avec CoA Bots 3.0 », jamais en faux chiffres.
- Elle est absente de la copie publique, car `public_files()` la refuse.
