"""The living world of CoA Bots 3.0: what the bots do, read from the files SquidBot writes (docs: LIAISON-3.0.md).

SquidBot writes world.json, economy.json and groups.json in <logs>/squidbot/, each wrapped as
{schema, at, every, build_us, data}, and only while someone looks: the dashboard rewrites watch.json there
every half minute while this page is open. Until the module writes them, each missing topic is answered with
made-up figures marked "demo", so the page can be built and shown before the module exists.
"""
import json
import math
import os
import random
import threading
import time

TOPICS = ("world", "economy", "groups")
MAJOR = 1           # schema version this page understands: squidbot.<topic>/1
WATCH_EVERY = 30    # seconds between two writes of watch.json


class Vivant:
    def __init__(self, ctx):
        self.dir = os.path.join(os.path.dirname(ctx.status_file), "squidbot")
        self.lock = threading.Lock()
        self.cache = {}
        self.watched = 0.0

    def _watch(self, topics):
        """Tell the module someone looks. Only where the module made its folder: nothing is created otherwise."""
        now = time.time()
        if now - self.watched < WATCH_EVERY or not os.path.isdir(self.dir):
            return
        self.watched = now
        tmp = os.path.join(self.dir, "watch.json.tmp")
        try:
            with open(tmp, "w", encoding="utf-8") as handle:
                json.dump({"at": int(now), "topics": list(topics)}, handle)
            os.replace(tmp, os.path.join(self.dir, "watch.json"))
        except OSError:
            pass

    def _read(self, topic):
        path = os.path.join(self.dir, topic + ".json")
        try:
            stat = os.stat(path)
        except OSError:
            return None
        key = (stat.st_mtime_ns, stat.st_size)
        hit = self.cache.get(topic)
        if hit and hit[0] == key:
            return hit[1]
        # The module renames a new copy over the file; on Windows an open landing in that swap is refused: once more.
        for attempt in (0, 1):
            try:
                with open(path, "rb") as handle:
                    doc = json.loads(handle.read().decode("utf-8", errors="replace"))
                break
            except PermissionError as error:
                if attempt:
                    return {"error": "%s.json unreadable: %s" % (topic, error)}
                time.sleep(0.1)
            except (OSError, ValueError) as error:
                return {"error": "%s.json unreadable: %s" % (topic, error)}
        schema = str(doc.get("schema", ""))
        try:
            major = int(schema.rsplit("/", 1)[1].split(".")[0])
        except (IndexError, ValueError):
            major = -1
        if major != MAJOR:
            answer = {"error": "%s.json: schema %r is not one this dashboard reads (squidbot.%s/%d)" % (topic, schema, topic, MAJOR)}
        else:
            every = float(doc.get("every") or 10)
            answer = dict(doc.get("data") or {}, at=doc.get("at"), every=every, buildUs=doc.get("build_us"),
                          serverStart=doc.get("server_start"), module=doc.get("module"))
        self.cache[topic] = (key, answer)
        return answer

    def get(self):
        with self.lock:
            self._watch(TOPICS)
            now = time.time()
            out = {"demo": [], "stale": []}
            for topic in TOPICS:
                data = self._read(topic)
                if data is None:
                    data = DEMO[topic](now)
                    out["demo"].append(topic)
                elif data.get("at") and now - float(data["at"]) > 3 * data.get("every", 10):
                    out["stale"].append(topic)
                out[topic] = data
            return out


# ------------------------------------------------------------------ made-up figures ----
# Stable within a minute so the page does not jump at every refresh, moving slowly over the day.
def _rng(now, salt):
    return random.Random(int(now // 60) * 7 + salt)


ZONES = [(1519, "Stormwind City", True), (1637, "Orgrimmar", True), (1537, "Ironforge", True), (1638, "Thunder Bluff", True),
         (1657, "Darnassus", True), (1497, "Undercity", True), (12, "Elwynn Forest", False), (14, "Durotar", False),
         (40, "Westfall", False), (17, "The Barrens", False), (11, "Wetlands", False), (33, "Stranglethorn Vale", False),
         (45, "Arathi Highlands", False), (440, "Tanaris", False), (361, "Felwood", False), (139, "Eastern Plaguelands", False)]
DUNGEONS = [(36, "The Deadmines", 5), (43, "Wailing Caverns", 8), (47, "Razorfen Kraul", 6), (189, "Scarlet Monastery", 4),
            (209, "Zul'Farrak", 8), (349, "Maraudon", 7), (230, "Blackrock Depths", 15), (329, "Stratholme", 10)]
NAMES = ["Arwen", "Thorgal", "Brienne", "Kaelis", "Morwen", "Drakkar", "Ysolde", "Grimbald", "Lyria", "Barok", "Seraphine", "Torvald"]


def _demo_world(now):
    r = _rng(now, 1)
    online = 480 + int(20 * math.sin(now / 3600)) + r.randint(-5, 5)
    weights = [r.uniform(.4, 1.6) * (3 if cap else 1) for _, _, cap in ZONES]
    total = sum(weights)
    zones = [{"zone": z, "name": n, "capital": cap, "bots": max(1, round(online * w / total))} for (z, n, cap), w in zip(ZONES, weights)]
    zones.sort(key=lambda z: -z["bots"])
    acts = {"quest": .42, "grind": .12, "city": .18, "travel": .08, "fish": .02, "pvp": .05, "dungeon": .08, "idle": .05}
    stuck = [{"name": r.choice(NAMES), "zone": r.choice(ZONES)[1], "since": int(now - r.randint(60, 900)),
              "why": r.choice(["no path", "falling", "loop on a quest giver", "inside a wall"])} for _ in range(r.randint(0, 3))]
    tick = r.randint(32, 48)
    return {"online": online, "players": r.randint(0, 3), "zones": zones,
            "activities": {k: round(online * v * r.uniform(.85, 1.15)) for k, v in acts.items()},
            "souls": {"lazy": round(online * .18), "quester": round(online * .34), "wanderer": round(online * .2),
                      "trader": round(online * .16), "pvp": round(online * .12)},
            "surname": {"mode": 2, "list_size": 64, "top": [{"name": n, "bots": r.randint(6, 14)} for n in
                        ("Stormhand", "Ashvale", "Ironbrook", "Duskmantle", "Emberfall", "Greywater", "Thornfield", "Brightwood")]},
            "health": {"tick_ms": {"avg": tick, "p95": tick + r.randint(15, 30), "max": tick + r.randint(60, 120)},
                       "bots_us_per_tick": {"avg": online * 19, "p95": online * 32},
                       "by_strategy_us": [{"name": n, "us": u} for n, u in
                                          [("rpg", 3100), ("travel", 1900), ("combat", 1700), ("city life", 900), ("loot", 600), ("economy", 400)]],
                       "stuck": stuck,
                       "history": [{"ts": int(now - i * 300), "tick": 36 + 8 * math.sin((now - i * 300) / 2400) + _rng(now - i * 300, 9).uniform(-3, 3),
                                    "bots": online * 19 / 1000 * (1 + .1 * math.sin((now - i * 300) / 3000))} for i in range(72, -1, -1)]},
            "at": int(now), "every": 10, "buildUs": 410}


ITEMS = [(14047, "Runecloth", 1, 640000), (12359, "Thorium Bar", 1, 410000), (13444, "Major Mana Potion", 1, 380000),
         (8836, "Arthas' Tears", 1, 205000), (14344, "Large Brilliant Shard", 3, 190000), (12804, "Powerful Mojo", 2, 150000),
         (4338, "Mageweave Cloth", 1, 120000), (13464, "Golden Sansam", 1, 95000)]
CATEGORIES = [("Trade goods", 7, 1200, 2350), ("Consumables", 0, 820, 1800), ("Armor", 4, 640, 14500), ("Weapons", 2, 210, 22800),
              ("Recipes", 9, 120, 6400), ("Gems", 3, 75, 9800), ("Containers", 1, 64, 12000)]


def _demo_economy(now):
    r = _rng(now, 2)
    cats = []
    for name, cls, auctions, avg in CATEGORIES:
        a = round(avg * r.uniform(.9, 1.1))
        cats.append({"name": name, "class": cls, "auctions": round(auctions * r.uniform(.9, 1.1)), "avg": a,
                     "low": round(a * .45), "usual": round(a * .9), "high": round(a * 2.1), "volume_24h": round(auctions * r.uniform(.6, 1.2))})
    return {"auctions": sum(c["auctions"] for c in cats), "gold_circulating": 18450000 + r.randint(-90000, 90000),
            "gold_bots": 16200000 + r.randint(-90000, 90000), "categories": cats,
            "top_sales_24h": [{"item": i, "name": n, "quality": q, "count": r.randint(20, 220), "gold": round(g * r.uniform(.8, 1.2))} for i, n, q, g in ITEMS],
            "crafts_24h": [{"skill": "Tailoring", "name": "Runecloth Bag", "quality": 1, "count": 31, "profit": 52000},
                           {"skill": "Alchemy", "name": "Major Healing Potion", "quality": 1, "count": 64, "profit": 38000},
                           {"skill": "Blacksmithing", "name": "Thorium Belt", "quality": 2, "count": 6, "profit": 27000},
                           {"skill": "Enchanting", "name": "Large Brilliant Shard", "quality": 3, "count": 18, "profit": 21000}],
            "orders": [{"id": 77, "buyer": "Squid", "bot": "Thorgal", "name": "Arcanite Reaper", "quality": 4, "price": 1250000, "state": "crafting", "at": int(now - 1800)},
                       {"id": 78, "buyer": "Squid", "bot": "Lyria", "name": "Robe of the Void", "quality": 4, "price": 640000, "state": "waiting materials", "at": int(now - 5400)},
                       {"id": 74, "buyer": "Nimue", "bot": "Grimbald", "name": "Thorium Shield Spike", "quality": 2, "price": 85000, "state": "delivered", "at": int(now - 86000)}],
            "history": [{"ts": int(now - i * 3600), "auctions": 3000 + 300 * math.sin((now - i * 3600) / 20000)} for i in range(48, -1, -1)],
            "at": int(now), "every": 60, "buildUs": 1250}


def _demo_groups(now):
    r = _rng(now, 3)
    running = []
    for d, name, bosses in r.sample(DUNGEONS, 3):
        done = r.randint(0, bosses - 1)
        running.append({"run": r.randint(9000, 9999), "dungeon": d, "name": name, "bots": 5, "players": r.choice([0, 0, 1]),
                        "started": int(now - r.randint(300, 2400)), "boss_done": done, "boss_total": bosses, "wipes": r.choice([0, 0, 1, 2])})
    by = [{"dungeon": d, "name": n, "runs": r.randint(2, 11), "median_s": b * 240 + r.randint(-120, 300), "best_s": b * 200, "wipes": r.randint(0, 4)}
          for d, n, b in DUNGEONS]
    for row in by:
        row["cleared"] = max(0, row["runs"] - r.randint(0, 2))
    last = [{"name": r.choice(DUNGEONS)[1], "end": int(now - i * 700 - r.randint(0, 600)), "result": r.choice(["clear", "clear", "clear", "wipe", "abandon"]),
             "time_s": r.randint(900, 2600), "wipes": r.randint(0, 2), "group": r.sample(NAMES, 5)} for i in range(8)]
    return {"running": running, "by_dungeon": by, "last": last,
            "today": {"runs": sum(b["runs"] for b in by), "cleared": sum(b["cleared"] for b in by),
                      "wipes": sum(b["wipes"] for b in by), "boss_kills": sum(b["cleared"] for b in by) * 6},
            "at": int(now), "every": 15, "buildUs": 90}


DEMO = {"world": _demo_world, "economy": _demo_economy, "groups": _demo_groups}
