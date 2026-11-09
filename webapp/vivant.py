"""The living world of CoA Bots 3.0: what the bots do, read from the files SquidBot writes (docs: LIAISON-3.0.md).

SquidBot writes world.json, economy.json, groups.json and monde.json (CoA Monde) in <logs>/squidbot/, each wrapped as
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

TOPICS = ("world", "economy", "groups", "monde")
MAJOR = 1           # schema version this page understands: squidbot.<topic>/1
WATCH_EVERY = 30    # seconds between two writes of watch.json
HISTORY_EVERY = 15 * 60
HISTORY_KEEP = 48 * 3600
WORLD_EVERY = 5 * 60
WORLD_KEEP = 6 * 3600


class Vivant:
    def __init__(self, ctx, query=None, squidbot_dir=None):
        self.ctx, self.query = ctx, query
        self.items = {}     # item entry -> (name, quality), read once from item_template
        # The module sends the auction count of the moment: the dashboard keeps the curve (a point per 15 min, 48 h).
        self.history_file = ctx.file("vivant-history.json")
        try:
            self.history = json.load(open(self.history_file, encoding="utf-8"))
        except (OSError, ValueError):
            self.history = []
        self.world_history = []     # tick and bots online, a point per 5 min over 6 h (memory only)
        # The module's AiPlayerbot.CoaDataDir, by default <LogsDir>/squidbot: the folder of the realm's CoaBots.log.
        self.dir = (ctx.realm.key == "coa" and squidbot_dir) or os.path.join(os.path.dirname(ctx.coa_log), "squidbot")
        self.lock = threading.Lock()
        self.cache = {}
        self.watched = 0.0

    def _watch(self, topics):
        """Tell the module someone looks. The module makes its folder only when it writes, and writes only once watched:
        so the folder is made here, but only inside a logs folder that exists (never a stray path)."""
        now = time.time()
        if now - self.watched < WATCH_EVERY or not os.path.isdir(os.path.dirname(self.dir)):
            return
        self.watched = now
        try:
            os.makedirs(self.dir, exist_ok=True)
        except OSError:
            return
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
            if "economy" not in out["demo"] and not out["economy"].get("error"):
                self._name_items(out["economy"], ("top_sales_24h", "crafts_24h", "orders", "smelt_24h", "disenchant_24h"))
                out["economy"] = dict(out["economy"], categories=by_class(out["economy"].get("categories") or []))
                out["economy"] = dict(out["economy"], history=self._remember(out["economy"]))
            if "monde" not in out["demo"] and not out["monde"].get("error"):
                self._name_items(out["monde"], ("guild_orders",))
            if "world" not in out["demo"] and not out["world"].get("error"):
                world = out["world"]
                health = dict(world.get("health") or {})
                health.setdefault("history", self._remember_world(world))
                out["world"] = dict(world, health=health)
            events = self._events()
            if events is None:
                events = _demo_events(now)
                out["demo"].append("events")
            out["events"] = events
            out["log"] = tail_text(self.ctx.coa_log, 120)
            last = self._last_runs()
            if last is not None:
                out["groups"] = dict(out["groups"], last=last)
            return out

    def _remember(self, economy):
        at, auctions = economy.get("at"), economy.get("auctions")
        if at and auctions is not None and (not self.history or at - self.history[-1]["ts"] >= HISTORY_EVERY):
            self.history = [p for p in self.history if at - p["ts"] < HISTORY_KEEP] + [{"ts": int(at), "auctions": int(auctions)}]
            try:
                tmp = self.history_file + ".tmp"
                with open(tmp, "w", encoding="utf-8") as handle:
                    json.dump(self.history, handle)
                os.replace(tmp, self.history_file)
            except OSError:
                pass
        return self.history

    def _remember_world(self, world):
        at = world.get("at")
        tick = ((world.get("health") or {}).get("tick_ms") or {}).get("avg")
        if at and (not self.world_history or at - self.world_history[-1]["ts"] >= WORLD_EVERY):
            self.world_history = [p for p in self.world_history if at - p["ts"] < WORLD_KEEP] +                 [{"ts": int(at), "tick": tick, "online": world.get("online")}]
        return self.world_history

    def _name_items(self, doc, keys):
        """The modules give item entries only: add their name and quality (one query for the entries not seen yet)."""
        rows = [r for key in keys for r in doc.get(key) or [] if isinstance(r, dict) and r.get("item")]
        wanted = sorted({int(r["item"]) for r in rows} - set(self.items))
        if wanted and self.query:
            try:
                for entry, name, quality in self.query("SELECT entry, name, Quality FROM %s.item_template WHERE entry IN (%s)"
                                                      % (self.ctx.db["world"], ",".join(map(str, wanted)))):
                    self.items[int(entry)] = (name, int(quality))
            except Exception:  # noqa: BLE001  names are a comfort: the page shows the entry instead
                pass
        for r in rows:
            name, quality = self.items.get(int(r["item"]), (None, None))
            r.setdefault("name", name)
            if r.get("quality") is None:
                r["quality"] = quality

    def _last_runs(self, keep=8):
        """The newest lines of runs.jsonl (one per finished run, Dungeon Clear's record), newest first; None without it."""
        return tail_jsonl(os.path.join(self.dir, "runs.jsonl"), keep)

    def _events(self, keep=200):
        """The newest lines of events.jsonl, newest first, topped up from events.jsonl.1 just after a rotation;
        None when the module writes none (AiPlayerbot.CoaWorld.Events.Enable off)."""
        path = os.path.join(self.dir, "events.jsonl")
        rows = tail_jsonl(path, keep)
        if rows is not None and len(rows) < keep:
            rows += tail_jsonl(path + ".1", keep - len(rows)) or []
        return rows


def tail_jsonl(path, keep, span=256 * 1024):
    """The last `keep` well-formed lines of a JSON-lines journal, newest first, reading only its last `span` bytes."""
    try:
        with open(path, "rb") as handle:
            handle.seek(0, os.SEEK_END)
            start = max(0, handle.tell() - span)
            handle.seek(start)
            lines = handle.read().decode("utf-8", errors="replace").splitlines()
    except OSError:
        return None
    if start:
        lines = lines[1:]   # cut in the middle of a line
    rows = []
    for line in reversed(lines):
        try:
            row = json.loads(line)
        except ValueError:
            continue
        if isinstance(row, dict):
            rows.append(row)
            if len(rows) == keep:
                break
    return rows


def tail_text(path, keep, span=64 * 1024):
    """The last `keep` lines of a text log (CoaBots.log), oldest first, reading only its last `span` bytes; None without it."""
    try:
        with open(path, "rb") as handle:
            handle.seek(0, os.SEEK_END)
            start = max(0, handle.tell() - span)
            handle.seek(start)
            lines = handle.read().decode("utf-8", errors="replace").splitlines()
    except OSError:
        return None
    if start:
        lines = lines[1:]
    return [line for line in lines if line.strip()][-keep:]


def by_class(categories):
    """The module counts per item class and subclass (Armor/Cloth, Armor/Plate…): one row per class here, prices
    weighted by auctions, a null price staying null when no subclass of the class has one."""
    rows = {}
    for c in categories:
        if not isinstance(c, dict) or "class" not in c:
            continue
        row = rows.setdefault(c["class"], {"class": c["class"], "subs": 0, "auctions": 0, "volume_24h": 0, "_w": {}})
        row["subs"] += 1
        n = int(c.get("auctions") or 0)
        row["auctions"] += n
        row["volume_24h"] += int(c.get("volume_24h") or 0)
        for key in ("avg", "low", "usual", "high"):
            if c.get(key) is not None:
                total, weight = row["_w"].get(key, (0, 0))
                row["_w"][key] = (total + c[key] * max(n, 1), weight + max(n, 1))
    out = []
    for row in rows.values():
        weights = row.pop("_w")
        for key in ("avg", "low", "usual", "high"):
            total, weight = weights.get(key, (0, 0))
            row[key] = round(total / weight) if weight else None
        out.append(row)
    return sorted(out, key=lambda r: -r["auctions"])


# ------------------------------------------------------------------ made-up figures ----
# Stable within a minute so the page does not jump at every refresh, moving slowly over the day.
def _rng(now, salt):
    return random.Random(int(now // 60) * 7 + salt)


ZONES = [(1519, "Stormwind City", True), (1637, "Orgrimmar", True), (1537, "Ironforge", True), (1638, "Thunder Bluff", True),
         (1657, "Darnassus", True), (1497, "Undercity", True), (12, "Elwynn Forest", False), (14, "Durotar", False),
         (40, "Westfall", False), (17, "The Barrens", False), (11, "Wetlands", False), (33, "Stranglethorn Vale", False),
         (45, "Arathi Highlands", False), (440, "Tanaris", False), (361, "Felwood", False), (139, "Eastern Plaguelands", False)]
DUNGEONS = [("dm", 36, "The Deadmines", 5), ("wc", 43, "Wailing Caverns", 8), ("rfk", 47, "Razorfen Kraul", 6), ("sm-cath", 189, "Scarlet Monastery", 4),
            ("zf", 209, "Zul'Farrak", 8), ("mara", 349, "Maraudon", 7), ("brd", 230, "Blackrock Depths", 15), ("strat", 329, "Stratholme", 10)]
NAMES = ["Arwen", "Thorgal", "Brienne", "Kaelis", "Morwen", "Drakkar", "Ysolde", "Grimbald", "Lyria", "Barok", "Seraphine", "Torvald"]


def _demo_world(now):
    r = _rng(now, 1)
    online = 480 + int(20 * math.sin(now / 3600)) + r.randint(-5, 5)
    weights = [r.uniform(.4, 1.6) * (3 if cap else 1) for _, _, cap in ZONES]
    total = sum(weights)
    zones = [{"zone": z, "name": n, "capital": cap, "bots": max(1, round(online * w / total))} for (z, n, cap), w in zip(ZONES, weights)]
    for z in zones:
        horde = z["zone"] in (1637, 1638, 1497, 14, 17) and .9 or z["zone"] in (1519, 1537, 1657, 12, 40) and .05 or r.uniform(.3, .7)
        z["faction"] = {"alliance": z["bots"] - round(z["bots"] * horde), "horde": round(z["bots"] * horde)}
    zones.sort(key=lambda z: -z["bots"])
    acts = {"quest": .36, "grind": .1, "camp": .03, "city": .15, "wander_random": .04, "wander_npc": .03, "flight": .05, "rest": .03,
            "fish": .02, "gather": .04, "pvp": .05, "dungeon": .07, "idle": .03}
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
                                    "online": round(online * (1 + .05 * math.sin((now - i * 300) / 3000)))} for i in range(72, -1, -1)]},
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
            "crafts_24h": [{"skill": 197, "name": "Runecloth Bag", "quality": 1, "count": 31, "profit": 52000},
                           {"skill": 171, "name": "Major Healing Potion", "quality": 1, "count": 64, "profit": 38000},
                           {"skill": 164, "name": "Thorium Belt", "quality": 2, "count": 6, "profit": 27000},
                           {"skill": 333, "name": "Large Brilliant Shard", "quality": 3, "count": 18, "profit": 21000}],
            "orders": [{"id": 77, "buyer": "Squid", "bot": "Thorgal", "name": "Arcanite Reaper", "quality": 4, "price": 1250000, "state": "mailed", "at": int(now - 1800)},
                       {"id": 78, "buyer": "Squid", "bot": "Lyria", "name": "Robe of the Void", "quality": 4, "price": 640000, "state": "busy", "at": int(now - 5400)},
                       {"id": 74, "buyer": "Nimue", "bot": "Grimbald", "name": "Thorium Shield Spike", "quality": 2, "price": 85000, "state": "refused", "at": int(now - 86000)}],
            "smelt_24h": [{"item": 12359, "name": "Thorium Bar", "quality": 1, "count": 140}, {"item": 6037, "name": "Truesilver Bar", "quality": 2, "count": 22},
                          {"item": 3860, "name": "Mithril Bar", "quality": 1, "count": 61}],
            "disenchant_24h": [{"item": 14344, "name": "Large Brilliant Shard", "quality": 3, "count": 18, "from": 18},
                               {"item": 16204, "name": "Illusion Dust", "quality": 1, "count": 96, "from": 41},
                               {"item": 16203, "name": "Greater Eternal Essence", "quality": 2, "count": 12, "from": 30}],
            "clock": {"enabled": 1, "offline_added_s": 7200, "expired_24h": r.randint(300, 420), "sold_24h": r.randint(800, 1100), "relisted_24h": r.randint(150, 260)},
            "ahbot_24h": {"listed": r.randint(2400, 2800), "bought": r.randint(500, 700), "gold_in": 4100000, "gold_out": 3650000},
            "history": [{"ts": int(now - i * 3600), "auctions": 3000 + 300 * math.sin((now - i * 3600) / 20000)} for i in range(48, -1, -1)],
            "at": int(now), "every": 60, "buildUs": 1250}


def _demo_groups(now):
    """Field names follow Dungeon Clear's run records (bin/dc_testruns.jsonl): camelCase, times in ms."""
    r = _rng(now, 3)
    ms = int(now * 1000)
    running = []
    for key, map_id, name, bosses in r.sample(DUNGEONS, 3):
        running.append({"runId": r.randint(9000, 9999), "dungeon": key, "dungeonName": name, "mapId": map_id, "difficulty": r.choice([0, 0, 1]),
                        "bots": 5, "players": r.choice([0, 0, 1]), "startedAtMs": ms - r.randint(300, 2400) * 1000,
                        "bossesKilled": r.randint(0, bosses - 1), "bossesTotal": bosses, "wipes": r.choice([0, 0, 1, 2])})
    by = [{"dungeon": key, "dungeonName": n, "runs": r.randint(2, 11), "medianS": b * 240 + r.randint(-120, 300), "bestS": b * 200, "wipes": r.randint(0, 4)}
          for key, _, n, b in DUNGEONS]
    for row in by:
        row["cleared"] = max(0, row["runs"] - r.randint(0, 2))
    last = []
    for i in range(8):
        key, map_id, name, bosses = r.choice(DUNGEONS)
        end = ms - (i * 700 + r.randint(0, 600)) * 1000
        took = r.randint(900, 2600)
        result = r.choice(["clear", "clear", "clear", "wipe", "aborted"])
        killed = bosses if result == "clear" else r.randint(0, bosses - 1)
        last.append({"runId": 9000 - i, "dungeon": key, "dungeonName": name, "difficulty": r.choice([0, 0, 1]), "startedAtMs": end - took * 1000,
                     "endedAtMs": end, "durationS": took, "result": result, "bossesKilled": killed, "bossesTotal": bosses, "wipes": r.randint(0, 2),
                     "comp": [{"name": n, "class": c, "role": role} for n, c, role in
                              zip(r.sample(NAMES, 5), ("Warrior", "Priest", "Mage", "Rogue", "Hunter"), ("tank", "heal", "dps", "dps", "dps"))],
                     "players": r.choice([[], [], ["Squid"]])})
    return {"running": running, "byDungeon": by, "last": last,
            "today": {"runs": sum(b["runs"] for b in by), "cleared": sum(b["cleared"] for b in by),
                      "wipes": sum(b["wipes"] for b in by), "bossKills": sum(b["cleared"] for b in by) * 6},
            "at": int(now), "every": 15, "buildUs": 90}


def _demo_monde(now):
    """CoA Monde's state of the moment (proposed 09/11): invasions, rushes, guilds and their orders, server firsts."""
    r = _rng(now, 5)
    return {"invasions": [{"zone": 42, "name": "Duskwood", "kind": "Scourge", "since": int(now - 1500), "ends": int(now + 2100), "bots": r.randint(12, 30)}],
            "rushes": [{"what": "Zul'Farrak", "zone": 1176, "name": "Zul'Farrak", "since": int(now - 900), "bots": 20}],
            "guilds": [{"id": 1, "name": "Iron Tide", "members": 48, "bots": 46, "online": r.randint(18, 30), "bank_gold": 12500000, "orders_open": 2},
                       {"id": 2, "name": "Moonwhisper", "members": 37, "bots": 37, "online": r.randint(10, 22), "bank_gold": 8400000, "orders_open": 1},
                       {"id": 3, "name": "Blood of Ashenvale", "members": 29, "bots": 28, "online": r.randint(8, 16), "bank_gold": None, "orders_open": 0}],
            "guild_orders": [{"id": 12, "guild": "Iron Tide", "item": 13444, "name": "Major Mana Potion", "quality": 1, "count": 20, "state": "open", "at": int(now - 3000)},
                             {"id": 11, "guild": "Moonwhisper", "item": 14047, "name": "Runecloth", "quality": 1, "count": 60, "state": "done", "at": int(now - 9000)}],
            "server_firsts": [{"what": "level 60", "by": "Kaelis", "at": int(now - 20000)}, {"what": "Onyxia", "by": "<Iron Tide>", "at": int(now - 50000)}],
            "recovery_24h": {"stuck": r.randint(8, 20), "unstuck": r.randint(6, 18)},
            "at": int(now), "every": 30, "buildUs": 60}


def _demo_events(now):
    r = _rng(now, 4)
    lines = [("invasion", "", "The Scourge invades Darkshire: guards and bots rally at the town hall."),
             ("rush", "", "Rush on Zul'Farrak: 4 groups of bots heading there."),
             ("server_first", "Kaelis", "Server first: Kaelis reaches level 60."),
             ("guild", "Grimbald", "<Iron Tide> Grimbald dings 42."),
             ("guild", "Lyria", "<Moonwhisper> Lyria loots [Robe of the Archmage]."),
             ("stuck", "Arwen", "Stuck in Westfall (no path) for 3 min."),
             ("unstuck", "Arwen", "Freed: teleported to the nearest graveyard."),
             ("boss", "Thorgal", "Group of Thorgal kills Edwin VanCleef (The Deadmines)."),
             ("wipe", "Brienne", "Group of Brienne wipes on Gahz'rilla (Zul'Farrak)."),
             ("order", "Thorgal", "Thorgal mails [Arcanite Reaper] to Squid."),
             ("error", "", "CoA Economy: cannot write economy.json.tmp")]
    out, at = [], now
    for _ in range(40):
        kind, bot, text = r.choice(lines)
        at -= r.randint(20, 400)
        out.append({"at": int(at), "kind": kind, "bot": bot, "text": text})
    return out


DEMO = {"world": _demo_world, "economy": _demo_economy, "groups": _demo_groups, "monde": _demo_monde}
