/* The living world (CoA Bots 3.0): what the bots do, from the files SquidBot writes (docs: LIAISON-3.0.md).
   Private page, on this PC only. Reads /api/vivant (webapp/vivant.py), which answers with made-up figures,
   marked "demo", for each topic the module does not write yet. Uses server.js (SW, coins, ago, getJson). */

const VIVANT_WORDS = {
  en: {
    tabs: { population: "Population", economy: "Economy", groups: "Groups & dungeons", health: "Health", events: "Journal" },
    allKinds: "All", noEvent: "Nothing in the journal yet.", eventsHelp: "The newest 200 lines of events.jsonl, written by the server as things happen.",
    kind: { invasion: "Invasion", rush: "Rush", server_first: "Server first", guild: "Guild", stuck: "Stuck", unstuck: "Unstuck", boss: "Boss", wipe: "Wipe", order: "Order", error: "Error" },
    demo: t => "Made-up figures for " + t + ": the server does not write these files yet (CoA Bots 3.0).",
    stale: t => "Not updated for a while: " + t + ". The module has stopped writing, or the realm is down.",
    online: "Bots online", players: "Players", inCapitals: "In capitals", busy: "In a dungeon", stuck: "Stuck", zonesUsed: "Zones with bots", soon: "comes with CoA Bots 3.0", perfOff: "PerfMon is off on this realm: no cost by strategy.",
    zones: "Where they are", capital: "capital", activities: "What they do", souls: "Souls", surnames: "Surnames", soonL1: "comes with CoA Bots 3.0 (L1)", soulsOff: "Souls are off on this realm (AiPlayerbot.CoaSoul.Enable = 0).",
    surnameMode: ["None", "“Bot”", "From the list"], surnameHelp: ["Bots show their first name only.", "Every bot is named “First Bot” (as in 2.x).", n => "A family name per bot, drawn once from a list of " + n + "."],
    mostWorn: "Most worn",
    act: { quest: "Questing", grind: "Grinding", city: "In town", travel: "Travelling", fish: "Fishing", pvp: "PvP", dungeon: "Dungeon", idle: "Idle" },
    soul: { lazy: "Lazy", quester: "Quester", wanderer: "Wanderer", trader: "Trader", pvp: "PvP" },
    auctions: "Auctions", goldAll: "Gold in circulation", goldBots: "Held by bots", sold24: "Sold, 24 h", crafted24: "Crafted, 24 h", ordersTile: "Orders (last 50)", refusedN: n => n + " refused", goldWait: "first count within 10 min", needs: what => "Nothing yet: needs " + what + " in the module settings.", noAuction: "No auction right now.",
    categories: "Prices by category", cat: "Category", avg: "Average", band: "Low · usual · high", volume: "Sold 24 h",
    topSales: "Best sellers, 24 h", crafts: "Crafts, 24 h", orders: "Orders to crafting bots", item: "Item", qty: "Qty", gold: "Gold",
    orderState: { mailed: "mailed", refused: "refused", busy: "busy" },
    by: "by", forWhom: "for", profit: "profit", auctionsWeek: "Auctions, 48 h",
    runsToday: "Runs today", cleared: "Cleared", wipes: "Wipes", bossKills: "Bosses killed", running: "Running now",
    noRun: "No group in a dungeon right now.", dungeon: "Dungeon", runs: "Runs", median: "Median", best: "Best", started: "started",
    bosses: "bosses", lastRuns: "Last runs", result: { clear: "cleared", wipe: "wiped", aborted: "aborted", setup_failed: "failed to start" }, difficulty: ["", "heroic", "mythic"], perDungeon: "By dungeon",
    tick: "World tick", tickFoot: (p, m) => (p === null ? "" : "p95 " + p + " ms · ") + (m === null ? "" : "max " + m + " ms"), botsCpu: "Bots per tick", botsCpuFoot: p => "p95 " + p + " ms",
    build: "Snapshot cost", buildFoot: "on the world thread, all files", strategies: "Cost by strategy, microseconds per tick",
    stuckList: "Stuck bots", noStuck: "No bot is stuck.", since: "since", tickChart: "Tick (ms), 6 h", botsChart: "Bots online, 6 h", curveWait: "The curve draws itself as readings come in: a point every 5 minutes while this page is open.",
    actionsSoon: "Commands to the bots (stop, resume, summon, unstuck) arrive with the module, through the world console.",
  },
  fr: {
    tabs: { population: "Population", economy: "Économie", groups: "Groupes et donjons", health: "Santé", events: "Journal" },
    allKinds: "Tout", noEvent: "Rien dans le journal pour l’instant.", eventsHelp: "Les 200 dernières lignes d’events.jsonl, écrites par le serveur au fil de l’eau.",
    kind: { invasion: "Invasion", rush: "Ruée", server_first: "Premier du serveur", guild: "Guilde", stuck: "Coincé", unstuck: "Décoincé", boss: "Boss", wipe: "Wipe", order: "Commande", error: "Erreur" },
    demo: t => "Données factices pour " + t + " : le serveur n'écrit pas encore ces fichiers (CoA Bots 3.0).",
    stale: t => "Pas de mise à jour depuis un moment : " + t + ". Le module n'écrit plus, ou le royaume est arrêté.",
    online: "Bots en ligne", players: "Joueurs", inCapitals: "En capitale", busy: "En donjon", stuck: "Coincés", zonesUsed: "Zones occupées", soon: "arrive avec CoA Bots 3.0", perfOff: "PerfMon est coupé sur ce royaume : pas de coût par stratégie.",
    zones: "Où ils sont", capital: "capitale", activities: "Ce qu'ils font", souls: "Âmes", surnames: "Surnoms", soonL1: "arrive avec CoA Bots 3.0 (L1)", soulsOff: "Les âmes sont coupées sur ce royaume (AiPlayerbot.CoaSoul.Enable = 0).",
    surnameMode: ["Aucun", "« Bot »", "Liste"], surnameHelp: ["Les bots ne montrent que leur prénom.", "Chaque bot s'appelle « Prénom Bot » (comme en 2.x).", n => "Un nom de famille par bot, tiré une fois pour toutes d'une liste de " + n + "."],
    mostWorn: "Les plus portés",
    act: { quest: "En quête", grind: "Farm", city: "En ville", travel: "En voyage", fish: "Pêche", pvp: "JcJ", dungeon: "Donjon", idle: "Inactifs" },
    soul: { lazy: "Paresseux", quester: "Quêteur", wanderer: "Flâneur", trader: "Commerçant", pvp: "JcJ" },
    auctions: "Enchères", goldAll: "Or en circulation", goldBots: "Détenu par les bots", sold24: "Vendus, 24 h", crafted24: "Fabriqués, 24 h", ordersTile: "Commandes (50 dernières)", refusedN: n => n + " refusée(s)", goldWait: "premier compte sous 10 min", needs: what => "Rien pour l’instant : il faut " + what + " dans les réglages du module.", noAuction: "Aucune enchère pour l’instant.",
    categories: "Prix par catégorie", cat: "Catégorie", avg: "Moyen", band: "Bas · usuel · haut", volume: "Vendus 24 h",
    topSales: "Meilleures ventes, 24 h", crafts: "Artisanat, 24 h", orders: "Commandes aux bots artisans", item: "Objet", qty: "Qté", gold: "Or",
    orderState: { mailed: "envoyée", refused: "refusée", busy: "artisan occupé" },
    by: "par", forWhom: "pour", profit: "bénéfice", auctionsWeek: "Enchères, 48 h",
    runsToday: "Runs du jour", cleared: "Terminés", wipes: "Wipes", bossKills: "Boss tués", running: "En cours",
    noRun: "Aucun groupe en donjon pour l'instant.", dungeon: "Donjon", runs: "Runs", median: "Médiane", best: "Record", started: "commencé",
    bosses: "boss", lastRuns: "Derniers runs", result: { clear: "terminé", wipe: "wipe", aborted: "abandonné", setup_failed: "échec au départ" }, difficulty: ["", "héroïque", "mythique"], perDungeon: "Par donjon",
    tick: "Tick du monde", tickFoot: (p, m) => (p === null ? "" : "p95 " + p + " ms · ") + (m === null ? "" : "max " + m + " ms"), botsCpu: "Bots par tick", botsCpuFoot: p => "p95 " + p + " ms",
    build: "Coût des snapshots", buildFoot: "sur le thread monde, tous fichiers", strategies: "Coût par stratégie, microsecondes par tick",
    stuckList: "Bots coincés", noStuck: "Aucun bot coincé.", since: "depuis", tickChart: "Tick (ms), 6 h", botsChart: "Bots en ligne, 6 h", curveWait: "La courbe se dessine au fil des relevés : un point toutes les 5 minutes tant que cette page est ouverte.",
    actionsSoon: "Les commandes aux bots (arrêt, reprise, invocation, décoincer) arriveront avec le module, par la console du monde.",
  },
};
const VW = () => VIVANT_WORDS[lang] || VIVANT_WORDS.en;
let VIVANT = null, VIVANT_TAB = "population", vivantTimer = null;
const SOUL_COLORS = { lazy: "var(--text-muted)", quester: "var(--gold)", wanderer: "#7d9cc4", trader: "var(--accent)", pvp: "var(--horde)" };
const ACT_COLORS = { quest: "var(--gold)", grind: "#c96b3a", city: "var(--accent)", travel: "#7d9cc4", fish: "#3fa7d6",
  pvp: "var(--horde)", dungeon: "#b36df2", idle: "var(--text-muted)" };

async function loadVivant() {
  VIVANT = await getJson("/api/vivant").catch(error => ({ error: String(error) }));
  renderVivant();
}

function vivantFigures(tiles) {
  return '<div class="figures">' + tiles.map(f => '<div class="figure"><div class="label">' + esc(f[0]) + '</div><div class="value num">' +
    f[1] + '</div><div class="foot">' + esc(f[2] || "") + "</div></div>").join("") + "</div>";
}

const qualityName = (name, quality) => '<span style="color:' + (QUALITY_COLORS[quality] || "#eee") + '">[' + esc(name) + "]</span>";
const duration = s => Math.floor(s / 60) + ":" + String(Math.round(s % 60)).padStart(2, "0");

function renderVivant() {
  const host = document.getElementById("vivantPage");
  if (!host || !VIVANT) return;
  const w = VW();
  if (VIVANT.error && !VIVANT.world) { host.innerHTML = '<div class="banner">' + esc(VIVANT.error) + "</div>"; return; }
  const tabs = Object.keys(w.tabs).map(k => '<button type="button" role="tab" data-vivant="' + k + '" aria-selected="' + (k === VIVANT_TAB) + '">' +
    esc(w.tabs[k]) + "</button>").join("");
  const banners = (VIVANT.demo && VIVANT.demo.length ? '<div class="banner">' + esc(w.demo(VIVANT.demo.join(", "))) + "</div>" : "") +
    (VIVANT.stale && VIVANT.stale.length ? '<div class="banner">' + esc(w.stale(VIVANT.stale.join(", "))) + "</div>" : "");
  host.innerHTML = banners + '<div class="tabs" role="tablist">' + tabs + '</div><div id="vivantBody"></div>';
  ({ population: vivantPopulation, economy: vivantEconomy, groups: vivantGroups, health: vivantHealth, events: vivantEvents })[VIVANT_TAB](document.getElementById("vivantBody"), w);
}

function topicError(data) { return data && data.error ? '<div class="banner">' + esc(data.error) + "</div>" : ""; }

function vivantPopulation(body, w) {
  const d = VIVANT.world || {};
  const zones = d.zones || [], acts = d.activities || {}, h = d.health || {};
  const capitals = zones.filter(z => z.capital).reduce((s, z) => s + z.bots, 0);
  body.innerHTML = topicError(d) + vivantFigures([[w.online, num(d.online), ""], [w.players, num(d.players), ""],
    [w.inCapitals, num(capitals), Math.round(capitals / Math.max(1, d.online) * 100) + " %"], [w.busy, num(acts.dungeon), ""],
    [w.stuck, h.stuck ? num(h.stuck.length) : "–", h.stuck ? "" : w.soon], [w.zonesUsed, num(zones.length), ""]]) +
    '<div class="grid two"><section class="card"><h2>' + esc(w.zones) + '</h2><div id="vvZones"></div></section>' +
    '<section class="card"><h2>' + esc(w.activities) + '</h2><div class="splits" id="vvActs"></div>' +
    '<h2 class="later">' + esc(w.souls) + '</h2><div class="splits" id="vvSouls"></div>' +
    '<h2 class="later">' + esc(w.surnames) + '</h2><div id="vvSurname"></div></section></div>';
  rankedList(document.getElementById("vvZones"), zones.map(z => ({ name: z.name || "#" + z.zone, bots: z.bots, capital: z.capital })),
    { value: r => r.bots, unit: "bots", line2: r => (r.capital ? w.capital : "") });
  splitBar(document.getElementById("vvActs"), Object.keys(acts).map(k => ({ label: w.act[k] || k, count: acts[k], color: ACT_COLORS[k] || "var(--gold)" })));
  const souls = d.souls, soulHost = document.getElementById("vvSouls");
  if (!souls) soulHost.innerHTML = '<p class="empty">' + esc((VIVANT.demo || []).includes("world") ? w.soonL1 : w.soulsOff) + "</p>";
  else splitBar(soulHost, Object.keys(SOUL_COLORS).map(k => ({ label: w.soul[k], count: souls[k] || 0, color: SOUL_COLORS[k] })));
  const sn = d.surname, snHost = document.getElementById("vvSurname");
  if (!sn) { snHost.innerHTML = '<p class="empty">' + esc(w.soonL1) + "</p>"; return; }
  const help = w.surnameHelp[sn.mode];
  snHost.innerHTML = '<div class="tabs" aria-label="' + esc(w.surnames) + '">' + w.surnameMode.map((label, mode) =>
    '<button type="button" disabled aria-selected="' + (mode === sn.mode) + '">' + esc(label) + "</button>").join("") + "</div>" +
    '<p class="meta">' + esc(typeof help === "function" ? help(sn.list_size || 0) : help) + "</p>" +
    (sn.mode === 2 && sn.top && sn.top.length ? '<p class="meta"><strong>' + esc(w.mostWorn) + '</strong></p><div id="vvSurnameTop"></div>' : "");
  if (sn.mode === 2 && sn.top && sn.top.length) rankedList(document.getElementById("vvSurnameTop"), sn.top.slice().sort((a, b) => b.bots - a.bots),
    { value: r => r.bots, unit: "bots", line2: () => "" });
}

const PROFESSIONS = { 164: "Blacksmithing", 165: "Leatherworking", 171: "Alchemy", 182: "Herbalism", 185: "Cooking", 186: "Mining",
  197: "Tailoring", 202: "Engineering", 333: "Enchanting", 356: "Fishing", 393: "Skinning", 755: "Jewelcrafting", 773: "Inscription", 129: "First Aid" };
const money = v => (v === null || v === undefined ? "–" : coins(v));
const count = v => (v === null || v === undefined ? "–" : num(v));

function vivantEconomy(body, w) {
  // Nulls are real (LIAISON-3.0 §6): gold before the first query, prices without buyouts, bands without Market.Enable.
  const d = VIVANT.economy || {};
  const cats = d.categories || [], orders = d.orders || [], crafts = d.crafts_24h || [], sales = d.top_sales_24h || [];
  const known = cats.filter(c => c.volume_24h !== null && c.volume_24h !== undefined);
  const sold = known.length ? known.reduce((s, c) => s + c.volume_24h, 0) : null, crafted = crafts.reduce((s, c) => s + (c.count || 0), 0);
  const className = c => c.name || (SW().mkClass[c.class] || "#" + c.class);
  const band = c => (c.low === null && c.usual === null && c.high === null) || c.low === undefined ? "–" : money(c.low) + " · " + money(c.usual) + " · " + money(c.high);
  const catRows = cats.map(c => "<tr><td>" + esc(className(c)) + '</td><td class="r">' + count(c.auctions) + '</td><td class="r">' + money(c.avg) +
    '</td><td class="r meta">' + band(c) + '</td><td class="r">' + count(c.volume_24h) + "</td></tr>").join("");
  const salesRows = sales.map(s => "<tr><td>" + qualityName(s.name || "#" + s.item, s.quality) + '</td><td class="r">' + num(s.count) +
    '</td><td class="r">' + money(s.gold) + "</td></tr>").join("");
  const craftRows = crafts.map(c => "<tr><td>" + qualityName(c.name || "#" + c.item, c.quality) + '<div class="meta">' + esc(PROFESSIONS[c.skill] || c.skill) +
    '</div></td><td class="r">' + num(c.count) + '</td><td class="r">' + money(c.profit) + "</td></tr>").join("");
  const orderRows = orders.map(o => "<tr><td>" + qualityName(o.name || "#" + o.item, o.quality) + '<div class="meta">' + esc(w.by) + " " + esc(o.bot) + " · " +
    esc(w.forWhom) + " " + esc(o.buyer) + '</div></td><td class="r">' + (o.state === "refused" && !o.price ? "–" : money(o.price)) + '</td><td class="order-' + esc(o.state) + '">' + esc(w.orderState[o.state] || o.state) +
    '</td><td class="r meta">' + esc(ago(o.at)) + "</td></tr>").join("");
  const refused = orders.filter(o => o.state === "refused").length;
  const table = (head, rows, why) => rows ? '<div class="scroll"><table><thead><tr>' + head + "</tr></thead><tbody>" + rows + "</tbody></table></div>"
    : '<p class="empty">' + esc(why) + "</p>";
  const share = d.gold_bots !== null && d.gold_bots !== undefined && d.gold_circulating ? Math.round(d.gold_bots / d.gold_circulating * 100) + " %" : "";
  body.innerHTML = topicError(d) + vivantFigures([[w.auctions, count(d.auctions), ""],
    [w.goldAll, money(d.gold_circulating), d.gold_circulating === null ? w.goldWait : ""], [w.goldBots, money(d.gold_bots), share],
    [w.sold24, count(sold), sold === null ? w.needs("Market.Enable") : ""], [w.crafted24, num(crafted), ""],
    [w.ordersTile, num(orders.length), refused ? w.refusedN(refused) : ""]]) +
    '<section class="card"><h2>' + esc(w.categories) + "</h2>" + table("<th>" + esc(w.cat) + '</th><th class="r">' + esc(w.auctions) + '</th><th class="r">' +
      esc(w.avg) + '</th><th class="r">' + esc(w.band) + '</th><th class="r">' + esc(w.volume) + "</th>", catRows, w.noAuction) + "</section>" +
    '<div class="grid two"><section class="card"><h2>' + esc(w.topSales) + "</h2>" + table("<th>" + esc(w.item) + '</th><th class="r">' + esc(w.qty) +
      '</th><th class="r">' + esc(w.gold) + "</th>", salesRows, w.needs("Market.Enable")) + "</section>" +
    '<section class="card"><h2>' + esc(w.crafts) + "</h2>" + table("<th>" + esc(w.item) + '</th><th class="r">' + esc(w.qty) + '</th><th class="r">' +
      esc(w.profit) + "</th>", craftRows, w.needs("Artisans")) + "</section></div>" +
    '<div class="grid two"><section class="card"><h2>' + esc(w.orders) + "</h2>" + table("<th>" + esc(w.item) + '</th><th class="r">' + esc(w.gold) +
      "</th><th></th><th></th>", orderRows, w.needs("CraftOrders")) + "</section>" +
    '<section class="card"><h2>' + esc(w.auctionsWeek) + '</h2><div class="chart" id="vvAh"></div></section></div>';
  lineChart(document.getElementById("vvAh"), d.history || [], { value: p => p.auctions, label: w.auctionsWeek, unit: "" });
}

function vivantGroups(body, w) {
  // Field names are Dungeon Clear's (runId, dungeonName, startedAtMs, bossesKilled…): see LIAISON-3.0.md.
  const d = VIVANT.groups || {};
  const t = d.today || {};
  const sec = msTime => msTime / 1000;
  const label = r => esc(r.dungeonName || r.dungeon) + (r.difficulty ? ' <span class="meta">' + esc(w.difficulty[r.difficulty] || "") + "</span>" : "");
  const running = (d.running || []).map(r => '<div class="zone-row"><div><strong>' + label(r) + '</strong><div class="meta">' +
    r.bots + " bots" + (r.players ? " + " + r.players + " " + esc(w.players.toLowerCase()).replace(/s$/, r.players > 1 ? "s" : "") : "") + " · " +
    esc(w.started) + " " + esc(ago(sec(r.startedAtMs))) + (r.wipes ? " · " + r.wipes + " " + esc(w.wipes.toLowerCase()) : "") +
    '</div></div><div class="bar" title="' + r.bossesKilled + "/" + r.bossesTotal + '"><i style="width:' + (r.bossesKilled / Math.max(1, r.bossesTotal) * 100) +
    '%"></i></div><div class="meta">' + r.bossesKilled + "/" + r.bossesTotal + " " + esc(w.bosses) + "</div></div>").join("");
  const dungeons = (d.byDungeon || []).map(b => "<tr><td>" + esc(b.dungeonName || b.dungeon) + '</td><td class="r">' + b.runs + '</td><td class="r">' + b.cleared +
    '</td><td class="r">' + b.wipes + '</td><td class="r">' + duration(b.medianS) + '</td><td class="r">' + duration(b.bestS) + "</td></tr>").join("");
  const last = (d.last || []).map(r => "<tr><td>" + label(r) + '<div class="meta">' + esc((r.comp || []).map(c => c.name).concat(r.players || []).join(", ")) +
    "</div></td><td>" + esc(w.result[r.result] || r.result) + ' <span class="meta">' + r.bossesKilled + "/" + r.bossesTotal + '</span></td><td class="r">' +
    duration(r.durationS) + '</td><td class="r">' + (r.wipes || 0) + '</td><td class="r meta">' + esc(ago(sec(r.endedAtMs))) + "</td></tr>").join("");
  body.innerHTML = topicError(d) + vivantFigures([[w.runsToday, num(t.runs), ""], [w.cleared, num(t.cleared), Math.round(t.cleared / Math.max(1, t.runs) * 100) + " %"],
    [w.wipes, num(t.wipes), ""], [w.bossKills, num(t.bossKills), ""], [w.running, num((d.running || []).length), ""], [w.busy, num((d.running || []).reduce((s, r) => s + r.bots, 0)), "bots"]]) +
    '<section class="card"><h2>' + esc(w.running) + "</h2>" + (running || '<p class="empty">' + esc(w.noRun) + "</p>") + "</section>" +
    '<section class="card"><h2>' + esc(w.perDungeon) + '</h2><div class="scroll"><table><thead><tr><th>' + esc(w.dungeon) + '</th><th class="r">' +
      esc(w.runs) + '</th><th class="r">' + esc(w.cleared) + '</th><th class="r">' + esc(w.wipes) + '</th><th class="r">' + esc(w.median) + '</th><th class="r">' +
      esc(w.best) + "</th></tr></thead><tbody>" + dungeons + "</tbody></table></div></section>" +
    '<section class="card"><h2>' + esc(w.lastRuns) + '</h2><div class="scroll"><table><tbody>' + last + "</tbody></table></div></section>";
}

const KIND_COLORS = { invasion: "var(--horde)", rush: "#c96b3a", server_first: "var(--gold-bright)", guild: "var(--accent)", stuck: "#d6a03f",
  unstuck: "#7d9cc4", boss: "#b36df2", wipe: "var(--horde)", order: "var(--gold)", error: "#ff5a5a" };
let VIVANT_KIND = "";

function vivantEvents(body, w) {
  const rows = VIVANT.events || [];
  const kinds = Array.from(new Set(rows.map(e => e.kind))).sort();
  const shown = VIVANT_KIND ? rows.filter(e => e.kind === VIVANT_KIND) : rows;
  const pills = '<div class="tabs" role="tablist">' + ["", ...kinds].map(k => '<button type="button" data-vkind="' + esc(k) + '" aria-selected="' +
    (k === VIVANT_KIND) + '">' + esc(k ? (w.kind[k] || k) : w.allKinds) + (k ? " · " + rows.filter(e => e.kind === k).length : "") + "</button>").join("") + "</div>";
  const lines = shown.map(e => '<tr><td class="meta">' + esc(ago(e.at)) + '</td><td><span style="color:' + (KIND_COLORS[e.kind] || "var(--text-muted)") + '">' +
    esc(w.kind[e.kind] || e.kind) + "</span></td><td>" + (e.bot ? "<strong>" + esc(e.bot) + "</strong> " : "") + esc(e.text) + "</td></tr>").join("");
  body.innerHTML = '<section class="card"><h2>' + esc(w.tabs.events) + '</h2><p class="meta">' + esc(w.eventsHelp) + "</p>" + pills +
    (lines ? '<div class="scroll"><table><tbody>' + lines + "</tbody></table></div>" : '<p class="empty">' + esc(w.noEvent) + "</p>") + "</section>";
}

document.addEventListener("click", event => {
  const pill = event.target.closest("[data-vkind]");
  if (!pill) return;
  VIVANT_KIND = pill.dataset.vkind;
  renderVivant();
});

function vivantHealth(body, w) {
  const d = VIVANT.world || {};
  const h = d.health || {}, tick = h.tick_ms || {}, cpu = h.bots_us_per_tick || {};
  const real = ["world", "economy", "groups"].filter(k => !(VIVANT.demo || []).includes(k));
  const builds = real.reduce((s, k) => s + ((VIVANT[k] || {}).buildUs || 0), 0);
  const stuck = (h.stuck || []).map(s => "<tr><td>" + esc(s.name) + '</td><td class="meta">' + esc(s.zone || "") + "</td><td>" + esc(s.why) +
    '</td><td class="r meta">' + esc(w.since) + " " + esc(ago(s.since)) + "</td></tr>").join("");
  body.innerHTML = topicError(d) + vivantFigures([[w.tick, tick.avg === null || tick.avg === undefined ? "–" : num(tick.avg) + " ms", w.tickFoot(tick.p95 == null ? null : num(tick.p95), tick.max == null ? null : num(tick.max))],
    [w.botsCpu, h.bots_us_per_tick ? (cpu.avg / 1000).toFixed(1) + " ms" : "–", h.bots_us_per_tick ? w.botsCpuFoot((cpu.p95 / 1000).toFixed(1)) : "PerfMon off"], [w.build, num(builds) + " µs", w.buildFoot],
    [w.stuck, h.stuck ? num(h.stuck.length) : "–", h.stuck ? "" : w.soon], [w.players, num(d.players), ""], [w.online, num(d.online), ""]]) +
    '<div class="grid two"><section class="card"><h2>' + esc(w.tickChart) + '</h2><div class="chart" id="vvTick"></div></section>' +
    '<section class="card"><h2>' + esc(w.botsChart) + '</h2><div class="chart" id="vvBots"></div></section></div>' +
    '<div class="grid two"><section class="card"><h2>' + esc(w.strategies) + '</h2><div id="vvStrat"></div></section>' +
    '<section class="card"><h2>' + esc(w.stuckList) + "</h2>" + (!h.stuck ? '<p class="empty">' + esc(w.soon) + "</p>" : stuck ? '<div class="scroll"><table><tbody>' + stuck + "</tbody></table></div>"
      : '<p class="empty">' + esc(w.noStuck) + "</p>") + '<p class="meta">' + esc(w.actionsSoon) + "</p></section></div>";
  const points = h.history || [];
  lineChart(document.getElementById("vvTick"), points.filter(p => p.tick != null), { value: p => p.tick, label: w.tickChart, unit: " ms", waiting: w.curveWait });
  lineChart(document.getElementById("vvBots"), points.filter(p => p.online != null), { value: p => p.online, label: w.botsChart, unit: "", color: "var(--accent)", waiting: w.curveWait });
  if (!h.by_strategy_us) { document.getElementById("vvStrat").innerHTML = '<p class="empty">' + esc(w.perfOff) + "</p>"; return; }
  rankedList(document.getElementById("vvStrat"), h.by_strategy_us.map(s => ({ name: s.name, us: s.us })),
    { value: r => r.us, unit: "µs", line2: () => "" });
}

document.addEventListener("click", event => {
  const tab = event.target.closest("[data-vivant]");
  if (!tab) return;
  VIVANT_TAB = tab.dataset.vivant;
  renderVivant();
});

function showVivantPage(page) {
  clearInterval(vivantTimer);
  if (page !== "vivant") return;
  loadVivant();
  vivantTimer = setInterval(() => { if (!document.hidden) loadVivant(); }, 15000);
}

document.getElementById("langButton").addEventListener("click", () => { if (PAGE === "vivant") renderVivant(); });
showVivantPage(PAGE);
