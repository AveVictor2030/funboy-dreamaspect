/* Stage 1 placeholder data. Replace this file in Stage 2. */
(function (root) {
  "use strict";

  var INTENSITY = {
    light: { id: "light", label: "Light", mult: 1, tokens: 1 },
    standard: { id: "standard", label: "Standard", mult: 2, tokens: 2 },
    push: { id: "push", label: "Push", mult: 3, tokens: 3 },
    allout: { id: "allout", label: "All-out", mult: 4, tokens: 4 },
  };

  var MIX = [
    { id: "daShoot", label: "DA shoot", hint: "Social-first production day" },
    { id: "inhouse", label: "In-house", hint: "Founder / office capture" },
    { id: "sourcing", label: "Sourcing", hint: "Brief creators / UGC" },
    { id: "recut", label: "Recut", hint: "Cut from the library" },
    { id: "stories", label: "Stories", hint: "Extra pipeline — not in contract" },
  ];

  var FORMULA = {
    postsPerDay: 0.4,
    originalsPerShoot: 8,
    recutShare: 0.5,
    sourcingShare: 0.3,
    inhouseShare: 0.4,
    storiesRatio: 0.4,
  };

  var PACE_OPTIONS = [2.5, 3, 4];
  var PACE_STEPS = [2.5, 3, 4, 5];
  var WEEKS = 4;
  var BAR_MAX = 12;
  var DA_MAX = 12;
  var IDEAS_PER_SHOOT = 5;
  var IDEAS_PER_OPP = 2;
  var MAX_SHOOTS = 2;
  var PACE_MIX = {
    2.5: { da: 10, f: 0, plus: 0 },
    3: { da: 12, f: 1, plus: 2 },
    4: { da: 12, f: 3, plus: 3 },
    5: { da: 12, f: 12, plus: 12 },
  };

  function monthlyNeed(pace) {
    return (pace || 2.5) * WEEKS;
  }

  function daRoom(mix) {
    return Math.max(0, DA_MAX - (mix.da || 0));
  }

  function mixFromPace(pace) {
    return copyMix(PACE_MIX[pace] || PACE_MIX[2.5]);
  }

  function paceFromMix(mix) {
    mix = mix || { da: 0, f: 0, plus: 0 };
    var da = mix.da || 0;
    var f = mix.f || 0;
    var plus = mix.plus || 0;
    for (var i = 0; i < PACE_STEPS.length; i++) {
      var pace = PACE_STEPS[i];
      var cap = PACE_MIX[pace];
      if (da <= cap.da && f <= cap.f && plus <= cap.plus) return pace;
    }
    return 5;
  }

  function clampBars(mix) {
    mix = mix || { da: 0, f: 0, plus: 0 };
    mix.da = Math.max(0, Math.min(DA_MAX, mix.da || 0));
    mix.f = Math.max(0, Math.min(BAR_MAX, mix.f || 0));
    mix.plus = Math.max(0, Math.min(BAR_MAX, mix.plus || 0));
    return mix;
  }

  function fitMixToTotal(mix, total) {
    mix = clampBars(mix);
    total = Math.max(0, total || 0);
    var sum = mixTotal(mix);
    if (sum >= total) return mix;
    var extra = total - sum;
    var toDA = Math.min(extra, daRoom(mix));
    mix.da += toDA;
    extra -= toDA;
    mix.f = Math.min(BAR_MAX, mix.f + extra);
    return clampBars(mix);
  }

  function shiftPlus(mix, next) {
    next = Math.max(0, Math.min(BAR_MAX, next));
    if (next === mix.plus) return;
    if (next > mix.plus) {
      mix.plus = next;
      return;
    }
    var give = mix.plus - next;
    mix.plus = next;
    var toDA = Math.min(give, daRoom(mix));
    mix.da += toDA;
    mix.f = Math.min(BAR_MAX, mix.f + (give - toDA));
  }

  function shiftFunboy(mix, next) {
    next = Math.max(0, Math.min(BAR_MAX, next));
    if (next === mix.f) return;
    if (next > mix.f) {
      mix.f = next;
      return;
    }
    var give = mix.f - next;
    mix.f = next;
    mix.da += Math.min(give, daRoom(mix));
  }

  function shiftDA(mix, next) {
    mix.da = Math.max(0, Math.min(DA_MAX, next));
  }

  function nudgeMix(mix, key, next) {
    mix = copyMix(mix);
    clampBars(mix);
    next = Math.max(0, Math.round(Number(next) || 0));
    if (key === "plus") shiftPlus(mix, next);
    else if (key === "f") shiftFunboy(mix, next);
    else if (key === "da") shiftDA(mix, next);
    return clampBars(mix);
  }

  function recommendedShoots(pace) {
    return recommendedShootsFromMix(mixFromPace(pace));
  }

  function recommendedShootsFromMix(mix) {
    var da = mix && mix.da ? mix.da : 0;
    if (da <= 0) return 0;
    if (da <= 8) return 1;
    return Math.min(MAX_SHOOTS, 2);
  }

  function defaultPace() {
    return { sep: 2.5, oct: 2.5 };
  }

  var PILLARS = [
    { id: "brand", name: "Brand and lifestyle", short: "Brand", bg: "#4a2c6a", fg: "#f4eef8" },
    { id: "product", name: "Product education and problem-solving", short: "Product", bg: "#f0d4a0", fg: "#3a2a14" },
    { id: "entertain", name: "Entertainment and trends", short: "Entertainment", bg: "#d8e9fb", fg: "#000000" },
    { id: "founder", name: "Founder and BTS", short: "Founder", bg: "#b7d0e6", fg: "#1c3a58" },
    { id: "promo", name: "Promotional", short: "Promo", bg: "#8b2a22", fg: "#f4e6d4" },
    { id: "community", name: "Community and creators", short: "Community", bg: "#d4c2e4", fg: "#3a2458" },
    { id: "retailer", name: "Retailer", short: "Retailer", bg: "#9dc9f5", fg: "#000000" },
  ];

  var GROUPS = [
    { id: "people", name: "Fun People", hue: "#e8b84a" },
    { id: "product", name: "How it works", hue: "#4a7c6a" },
    { id: "season", name: "Season", hue: "#c45c2a" },
    { id: "drop", name: "Drop / sale", hue: "#8b3a2a" },
    { id: "house", name: "The house", hue: "#6b8ab4" },
  ];

  var SHEET_IDEAS = [
    { id: "idea-don-t-distract-me-i-m-shopping", title: "don't distract me i'm shopping", pillar: "promo", season: "Labor Day Sale", owner: "FUNBOY", series: "Single Post", platform: "Instagram + TikTok", months: ["sep"] },
    { id: "idea-scrabble-announcement", title: "Scrabble Announcement", pillar: "promo", season: "Labor Day Sale", owner: "Dream Aspect", series: "Single Post", platform: "Instagram", months: ["sep"] },
    { id: "idea-mail-delivery", title: "Mail Delivery", pillar: "promo", season: "Labor Day Sale", owner: "Dream Aspect", series: "Single Post", platform: "Instagram + TikTok", months: ["sep"] },
    { id: "idea-pool-graphic-post", title: "Pool Graphic Post", pillar: "promo", season: "Labor Day Sale", owner: "Dream Aspect", series: "Single Post", platform: "Instagram", months: ["sep"] },
    { id: "idea-calling-a-customer", title: "Calling A Customer", pillar: "founder", season: "Evergreen", owner: "Dream Aspect", series: "Series", platform: "Instagram + TikTok", months: ["sep", "oct"] },
    { id: "idea-fall-movie-night", title: "Fall Movie Night", pillar: "brand", season: "Halloween", owner: "Dream Aspect", series: "Series", platform: "Instagram + TikTok", months: ["sep", "oct"] },
    { id: "idea-halloween-to-holiday-transition", title: "Halloween to Holiday transition", pillar: "entertain", season: "Holiday", owner: "Dream Aspect", series: "Single Post", platform: "Instagram + TikTok", months: ["oct"] },
    { id: "idea-you-found-perfect-halloween-decor", title: "you found perfect halloween decor", pillar: "brand", season: "Halloween", owner: "Dream Aspect", series: "", platform: "Instagram + TikTok", months: ["sep", "oct"] },
    { id: "idea-retailer-shopping", title: "Retailer Shopping", pillar: "retailer", season: "Evergreen", owner: "Dream Aspect", series: "", platform: "Instagram + TikTok", months: ["sep", "oct"] },
    { id: "idea-halloween-decor-ugc", title: "Halloween Decor UGC", pillar: "product", season: "Halloween", owner: "UGC", series: "", platform: "Instagram + TikTok", months: ["sep", "oct"] },
    { id: "idea-halloween-finds", title: "Halloween Finds", pillar: "product", season: "Halloween", owner: "UGC", series: "Series", platform: "Instagram + TikTok", months: ["sep", "oct"] },
    { id: "idea-halloween-find-talking", title: "Halloween Find: Talking", pillar: "product", season: "Halloween", owner: "UGC", series: "", platform: "Instagram + TikTok", months: ["sep", "oct"] },
    { id: "idea-this-or-that", title: "This or That", pillar: "founder", season: "Halloween, Holiday", owner: "Dream Aspect", series: "Series", platform: "Instagram + TikTok", months: ["sep", "oct"] },
    { id: "idea-halloween-sale", title: "Halloween Sale", pillar: "promo", season: "Halloween", owner: "Dream Aspect", series: "", platform: "Instagram + TikTok", months: ["sep", "oct"] },
    { id: "idea-how-to-decor-like-a-pro-expert", title: "How to Decor like a pro (Expert)", pillar: "product", season: "Halloween", owner: "UGC", series: "Series", platform: "Instagram + TikTok", months: ["sep", "oct"] },
    { id: "idea-how-to-decor", title: "How to Decor", pillar: "product", season: "Halloween", owner: "UGC", series: "", platform: "Instagram + TikTok", months: ["sep", "oct"] },
    { id: "idea-kids-movie-night", title: "Kids Movie Night", pillar: "brand", season: "Halloween", owner: "UGC", series: "Series", platform: "Instagram + TikTok", months: ["sep", "oct"] },
    { id: "idea-we-re-here-to-tell-you", title: "We're here to tell you", pillar: "promo", season: "Halloween Sale", owner: "Dream Aspect", series: "", platform: "Instagram + TikTok", months: ["oct"] },
    { id: "idea-coffee-reveal", title: "Coffee Reveal", pillar: "promo", season: "Halloween Sale", owner: "Dream Aspect", series: "Single Post", platform: "Instagram + TikTok", months: ["oct"] },
    { id: "idea-walmart-find-unpacking", title: "Walmart Find Unpacking", pillar: "retailer", season: "Halloween", owner: "UGC", series: "", platform: "Instagram + TikTok", months: ["sep", "oct"] },
    { id: "idea-spooky-holiday-season-is-calling", title: "Spooky/Holiday Season is calling", pillar: "entertain", season: "Halloween, Holiday", owner: "Dream Aspect", series: "", platform: "Instagram", months: ["sep", "oct"] },
    { id: "idea-pathway-lawn-snakes", title: "Pathway Lawn Snakes", pillar: "product", season: "Halloween", owner: "Dream Aspect", series: "Single Post", platform: "Instagram + TikTok", months: ["sep", "oct"] },
    { id: "idea-my-brain-right-now", title: "My brain right now", pillar: "entertain", season: "Halloween, Holiday", owner: "Dream Aspect", series: "", platform: "Instagram + TikTok", months: ["sep", "oct"] },
    { id: "idea-best-holiday-purchase-i-ever-made", title: "Best Holiday Purchase I Ever Made", pillar: "product", season: "Holiday", owner: "UGC", series: "", platform: "Instagram + TikTok", months: ["oct"] },
    { id: "idea-decor-for-christmas", title: "Decor for Christmas", pillar: "product", season: "Holiday", owner: "UGC", series: "", platform: "Instagram + TikTok", months: ["oct"] },
    { id: "idea-funboy-christmas-porch", title: "Funboy Christmas Porch", pillar: "product", season: "Holiday", owner: "Dream Aspect", series: "Single Post", platform: "Instagram + TikTok", months: ["oct"] },
    { id: "idea-pool-holiday-decor", title: "Pool Holiday Decor", pillar: "product", season: "Holiday", owner: "Dream Aspect", series: "", platform: "Instagram + TikTok", months: ["oct"] },
    { id: "idea-in-charge-for-memories", title: "In Charge for Memories", pillar: "product", season: "Holiday", owner: "UGC", series: "Series", platform: "Instagram + TikTok", months: ["oct"] },
    { id: "idea-swipe-to-open-santa-s-letter", title: "Swipe to Open Santa's Letter", pillar: "promo", season: "Holiday Sale", owner: "Dream Aspect", series: "Single Post", platform: "Instagram + TikTok", months: ["oct"] },
    { id: "idea-halloween-bucket-list", title: "Halloween Bucket List", pillar: "brand", season: "Halloween", owner: "Dream Aspect", series: "Single Post", platform: "Instagram + TikTok", months: ["sep", "oct"] },
    { id: "idea-pumpkin-photos-to-recreate-this-fall-funboy-pumpkins", title: "Pumpkin Photos to recreate this fall (Funboy Pumpkins)", pillar: "entertain", season: "Halloween", owner: "Dream Aspect", series: "Single Post", platform: "Instagram + TikTok", months: ["sep", "oct"] },
    { id: "idea-halloween-movie-night", title: "Halloween Movie Night", pillar: "brand", season: "Halloween", owner: "UGC", series: "Series", platform: "Instagram + TikTok", months: ["sep", "oct"] },
    { id: "idea-before-after", title: "Before / After", pillar: "brand", season: "Halloween", owner: "Dream Aspect", series: "Single Post", platform: "Instagram + TikTok", months: ["sep", "oct"] },
    { id: "idea-halloween-decor-doesn-t-have-to-be-high-effort", title: "Halloween Decor doesn't have to be high-effort", pillar: "product", season: "Halloween", owner: "Dream Aspect", series: "Series", platform: "Instagram + TikTok", months: ["sep", "oct"] },
    { id: "idea-funboy-story", title: "Funboy Story", pillar: "founder", season: "Evergreen", owner: "Dream Aspect", series: "Series", platform: "Instagram + TikTok", months: ["sep", "oct"] },
    { id: "idea-proof-that-halloween-decor-can-be-easy", title: "Proof that Halloween decor can be easy", pillar: "product", season: "Halloween", owner: "Dream Aspect", series: "Series", platform: "Instagram + TikTok", months: ["sep", "oct"] },
    { id: "idea-new-collection-moodboard", title: "New Collection Moodboard", pillar: "brand", season: "Holiday", owner: "Dream Aspect", series: "Series", platform: "Instagram + TikTok", months: ["oct"] }
  ];

  function groupById(id) {
    for (var i = 0; i < GROUPS.length; i++) {
      if (GROUPS[i].id === id) return GROUPS[i];
    }
    return GROUPS[0];
  }

  function eventsForMonth(monthId) {
    return EVENTS.filter(function (ev) {
      return ev.month === monthId;
    }).map(function (ev) {
      var h = seed(ev.id);
      return {
        id: ev.id,
        monthId: monthId,
        title: ev.name,
        when: ev.when,
        type: ev.type,
        typeName: ev.type === "sales" ? "Sale" : ev.type === "shoot" ? "Shoot" : ev.type === "event" ? "Event" : "Calendar",
        hue: ev.type === "sales" ? "#d4a017" : ev.type === "shoot" ? "#8b2a22" : "#e8b84a",
        blurb: ev.blurb,
        start: ev.start || "",
        end: ev.end || "",
        needsDelivery: ev.needsDelivery !== false && ev.type !== "shoot",
        a: 1 + (h % 4),
        b: 1 + ((h * 5) % 4),
      };
    });
  }

  function seed(str) {
    var n = 7;
    for (var i = 0; i < str.length; i++) n = (n * 31 + str.charCodeAt(i)) % 97;
    return n;
  }

  var SHEET_ID = "1upwkNcf6WXyY9Azwy5IJlw-PBcSjRrOW7DEYu64PGmY";
  var PILLAR_FROM_SHEET = {
    "brand and lifestyle": "brand",
    "product education and problem-solving": "product",
    "entertainment and trends": "entertain",
    "founder and bts": "founder",
    "promotional": "promo",
    "community and creators": "community",
    "retailer": "retailer",
  };
  var sheetIdeas = SHEET_IDEAS.slice();

  function slugIdea(title) {
    var s = String(title || "")
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, "-")
      .replace(/^-+|-+$/g, "");
    return (s || "idea").slice(0, 60);
  }

  function monthsFromSeason(event, section) {
    var t = String(event || "").toLowerCase();
    if (t.indexOf("labor") !== -1) return ["sep"];
    if (t.indexOf("halloween sale") !== -1) return ["oct"];
    if (t.indexOf("holiday sale") !== -1) return ["oct"];
    if (t.indexOf("halloween") !== -1 && t.indexOf("holiday") !== -1) return ["sep", "oct"];
    if (t.indexOf("halloween") !== -1) return ["sep", "oct"];
    if (t.indexOf("holiday") !== -1) return ["oct"];
    if (t.indexOf("evergreen") !== -1) return ["sep", "oct"];
    if (section === "oct") return ["oct"];
    if (section === "aug" || section === "sep") return ["sep"];
    return ["sep", "oct"];
  }

  function applySheetRows(rows) {
    var out = [];
    var seen = {};
    var section = "";
    (rows || []).forEach(function (row) {
      var title = String(row.title || "").replace(/^\s+|\s+$/g, "");
      if (!title) return;
      var low = title.toLowerCase();
      if (
        low === "august" ||
        low === "september" ||
        low === "october" ||
        low.indexOf("september") === 0 ||
        low.indexOf("october") === 0
      ) {
        section = low.indexOf("oct") !== -1 ? "oct" : low.indexOf("sep") !== -1 ? "sep" : "aug";
        return;
      }
      title = title.split("\n")[0].replace(/^\s+|\s+$/g, "");
      var pillar =
        PILLAR_FROM_SHEET[String(row.pillarName || "").toLowerCase().replace(/^\s+|\s+$/g, "")] ||
        "brand";
      var base = "idea-" + slugIdea(title);
      var id = base;
      var n = 2;
      while (seen[id]) {
        id = base + "-" + n;
        n += 1;
      }
      seen[id] = true;
      out.push({
        id: id,
        title: title,
        pillar: pillar,
        season: String(row.season || "").replace(/^\s+|\s+$/g, ""),
        owner: String(row.owner || "").replace(/^\s+|\s+$/g, ""),
        series: String(row.series || "").replace(/^\s+|\s+$/g, ""),
        platform: String(row.platform || "").replace(/^\s+|\s+$/g, ""),
        link: String(row.link || "").replace(/^\s+|\s+$/g, ""),
        months: monthsFromSeason(row.season, section),
      });
    });
    if (out.length) sheetIdeas = out;
  }

  function parseGviz(res) {
    var table = res && res.table;
    if (!table || !table.rows) return [];
    var idx = {};
    (table.cols || []).forEach(function (col, i) {
      var name = String(col.label || "").replace(/^\s+|\s+$/g, "");
      if (name) idx[name] = i;
    });
    function cell(row, name) {
      var i = idx[name];
      if (i == null || !row.c || !row.c[i]) return null;
      return row.c[i];
    }
    function isHttp(s) {
      return /^https?:\/\//i.test(String(s || "").replace(/^\s+|\s+$/g, ""));
    }
    function strip(s) {
      return String(s || "").replace(/^\s+|\s+$/g, "");
    }
    function urlFromCell(c) {
      if (!c) return "";
      if (c.p) {
        var u = c.p.url || c.p.hyperlink || c.p.uri || c.p.link;
        if (u && isHttp(u)) return strip(u);
      }
      var v = c.v != null ? strip(String(c.v)) : "";
      if (isHttp(v)) return v;
      var f = c.f != null ? String(c.f) : "";
      var m =
        f.match(/HYPERLINK\s*\(\s*"([^"]+)"/i) ||
        f.match(/HYPERLINK\s*\(\s*'([^']+)'/i) ||
        f.match(/href\s*=\s*["']([^"']+)["']/i);
      if (m && isHttp(m[1])) return m[1];
      if (isHttp(f)) return strip(f);
      return "";
    }
    function titleFromCell(c) {
      if (!c) return "";
      var f = c.f != null ? String(c.f) : "";
      var html = f.match(/<a[^>]*>([\s\S]*?)<\/a>/i);
      if (html) {
        var t = strip(html[1].replace(/<[^>]+>/g, ""));
        if (t && !isHttp(t)) return t;
      }
      var hyp = f.match(/HYPERLINK\s*\(\s*["'][^"']+["']\s*,\s*["']([^"']+)["']/i);
      if (hyp && strip(hyp[1])) return strip(hyp[1]);
      var v = c.v != null ? strip(String(c.v)) : "";
      if (v && !isHttp(v)) return v;
      var plainF = strip(f.replace(/<[^>]+>/g, ""));
      if (plainF && !isHttp(plainF) && plainF.toLowerCase().indexOf("hyperlink") === -1) {
        return plainF;
      }
      return v;
    }
    function val(row, name) {
      var c = cell(row, name);
      if (!c || c.v == null) return "";
      return String(c.v);
    }
    return table.rows.map(function (row) {
      var ref = cell(row, "Reference");
      var linkCell = cell(row, "Link") || cell(row, "URL");
      return {
        title: titleFromCell(ref) || val(row, "Reference"),
        link: urlFromCell(ref) || urlFromCell(linkCell),
        pillarName: val(row, "Content Pillar"),
        season: val(row, "Event/Season"),
        owner: val(row, "Asset Owner"),
        series: val(row, "Series?") || val(row, "Series"),
        platform: val(row, "Platform"),
      };
    });
  }

  function decodeXml(s) {
    return String(s || "")
      .replace(/&amp;/g, "&")
      .replace(/&lt;/g, "<")
      .replace(/&gt;/g, ">")
      .replace(/&quot;/g, '"')
      .replace(/&#39;/g, "'");
  }

  function zipCentralEntries(buf) {
    var u8 = new Uint8Array(buf);
    var view = new DataView(buf);
    var eocd = -1;
    var start = Math.max(0, u8.length - 65557);
    for (var i = u8.length - 22; i >= start; i--) {
      if (view.getUint32(i, true) === 0x06054b50) {
        eocd = i;
        break;
      }
    }
    if (eocd < 0) return {};
    var cdOff = view.getUint32(eocd + 16, true);
    var cdSize = view.getUint32(eocd + 12, true);
    var entries = {};
    var p = cdOff;
    var decoder = new TextDecoder();
    while (p < cdOff + cdSize) {
      if (view.getUint32(p, true) !== 0x02014b50) break;
      var method = view.getUint16(p + 10, true);
      var compSize = view.getUint32(p + 20, true);
      var nameLen = view.getUint16(p + 28, true);
      var extraLen = view.getUint16(p + 30, true);
      var commentLen = view.getUint16(p + 32, true);
      var localOff = view.getUint32(p + 42, true);
      var name = decoder.decode(u8.subarray(p + 46, p + 46 + nameLen));
      entries[name] = { method: method, compSize: compSize, localOff: localOff };
      p += 46 + nameLen + extraLen + commentLen;
    }
    return entries;
  }

  function zipReadFile(buf, entry, done) {
    if (!entry) {
      done("");
      return;
    }
    var view = new DataView(buf);
    var u8 = new Uint8Array(buf);
    var nameLen = view.getUint16(entry.localOff + 26, true);
    var extraLen = view.getUint16(entry.localOff + 28, true);
    var dataStart = entry.localOff + 30 + nameLen + extraLen;
    var compressed = u8.subarray(dataStart, dataStart + entry.compSize);
    if (entry.method === 0) {
      done(new TextDecoder().decode(compressed));
      return;
    }
    if (typeof DecompressionStream === "undefined") {
      done("");
      return;
    }
    var ds = new DecompressionStream("deflate-raw");
    new Response(new Blob([compressed]).stream().pipeThrough(ds))
      .text()
      .then(function (text) {
        done(text);
      })
      .catch(function () {
        done("");
      });
  }

  function parseSharedStrings(xml) {
    var out = [];
    var blocks = xml.match(/<si[\s\S]*?<\/si>/g) || [];
    blocks.forEach(function (block) {
      var parts = [];
      var re = /<t[^>]*>([\s\S]*?)<\/t>/g;
      var m;
      while ((m = re.exec(block))) parts.push(decodeXml(m[1]));
      out.push(parts.join(""));
    });
    return out;
  }

  function parseXlsxReferenceLinks(sheetXml, relsXml, strings) {
    var idToUrl = {};
    var relRe = /<Relationship\b([^>]*)\/?>/g;
    var rel;
    while ((rel = relRe.exec(relsXml))) {
      var attrs = rel[1];
      var idm = attrs.match(/\bId="([^"]+)"/);
      var tm = attrs.match(/\bTarget="(https?:[^"]+)"/);
      if (idm && tm) idToUrl[idm[1]] = decodeXml(tm[1]);
    }
    var cellText = {};
    var cellRe = /<c r="(E\d+)"([^>]*)>([\s\S]*?)<\/c>/g;
    var cell;
    while ((cell = cellRe.exec(sheetXml))) {
      var ref = cell[1];
      var attrs = cell[2] || "";
      var inner = cell[3] || "";
      var vm = inner.match(/<v>([^<]*)<\/v>/);
      if (!vm) continue;
      if (/\bt="s"/.test(attrs)) {
        var idx = parseInt(vm[1], 10);
        cellText[ref] = strings[idx] || "";
      } else {
        cellText[ref] = decodeXml(vm[1]);
      }
    }
    var map = {};
    var linkRe = /<hyperlink r:id="([^"]+)" ref="(E\d+)"/g;
    var link;
    while ((link = linkRe.exec(sheetXml))) {
      var title = String(cellText[link[2]] || "").replace(/^\s+|\s+$/g, "");
      var url = idToUrl[link[1]] || "";
      if (title && url) map[title] = url;
    }
    return map;
  }

  function applyLinksByTitle(map) {
    if (!map) return;
    sheetIdeas.forEach(function (idea) {
      if (idea.link) return;
      var url = map[idea.title] || map[String(idea.title || "").split("\n")[0]];
      if (url) idea.link = url;
    });
  }

  function loadSheet(done) {
    var gvizDone = false;
    var xlsxDone = false;
    var finished = false;
    var linkMap = {};
    function finish() {
      if (!gvizDone || !xlsxDone || finished) return;
      finished = true;
      applyLinksByTitle(linkMap);
      if (done) done();
    }
    window.__funboySheet = function (res) {
      try {
        applySheetRows(parseGviz(res));
      } catch (err) {}
      gvizDone = true;
      finish();
    };
    var s = document.createElement("script");
    s.src =
      "https://docs.google.com/spreadsheets/d/" +
      SHEET_ID +
      "/gviz/tq?tqx=out:json;responseHandler:__funboySheet&headers=1&gid=0&tq=limit+1000&t=" +
      Date.now();
    s.onerror = function () {
      gvizDone = true;
      finish();
    };
    document.head.appendChild(s);
    var xlsxUrl =
      "https://docs.google.com/spreadsheets/d/" + SHEET_ID + "/export?format=xlsx&t=" + Date.now();
    fetch(xlsxUrl)
      .then(function (res) {
        if (!res.ok) throw new Error("xlsx");
        return res.arrayBuffer();
      })
      .then(function (buf) {
        var entries = zipCentralEntries(buf);
        var sheetName = "xl/worksheets/sheet1.xml";
        var relsName = "xl/worksheets/_rels/sheet1.xml.rels";
        var stringsName = "xl/sharedStrings.xml";
        var left = 3;
        var files = {};
        function got() {
          left -= 1;
          if (left) return;
          linkMap = parseXlsxReferenceLinks(
            files[sheetName] || "",
            files[relsName] || "",
            parseSharedStrings(files[stringsName] || "")
          );
          xlsxDone = true;
          finish();
        }
        function read(name) {
          zipReadFile(buf, entries[name], function (text) {
            files[name] = text;
            got();
          });
        }
        read(sheetName);
        read(relsName);
        read(stringsName);
      })
      .catch(function () {
        xlsxDone = true;
        finish();
      });
  }

  function ideasForMonth(monthId) {
    var list = sheetIdeas.filter(function (idea) {
      return idea.months.indexOf(monthId) !== -1;
    });
    if (list.length) return list;
    return sheetIdeas;
  }

  function pillarById(id) {
    for (var i = 0; i < PILLARS.length; i++) {
      if (PILLARS[i].id === id) return PILLARS[i];
    }
    return PILLARS[0];
  }

  function contentForMonth(monthId) {
    return ideasForMonth(monthId).map(function (idea) {
      return {
        id: idea.id,
        monthId: monthId,
        title: idea.title,
        pillar: idea.pillar,
        season: idea.season,
        owner: idea.owner,
        series: idea.series,
        platform: idea.platform,
        link: idea.link || "",
        eventId: null,
      };
    });
  }

  function allSheetIdeas() {
    return sheetIdeas.slice();
  }

  function mixTotal(mix) {
    mix = mix || { da: 0, f: 0, plus: 0 };
    return (mix.da || 0) + (mix.f || 0) + (mix.plus || 0);
  }

  function copyMix(mix) {
    return { da: mix.da || 0, f: mix.f || 0, plus: mix.plus || 0 };
  }

  function defaultMix() {
    return {
      sep: mixFromPace(2.5),
      oct: mixFromPace(2.5),
    };
  }

  function chipMeters(count, salt) {
    var n = count || 0;
    var intensity = Math.min(4, n);
    var novelty = Math.max(0, 4 - n);
    var tilt = ((salt || 0) % 5) / 20;
    var red = n === 0 ? 0.18 + tilt : intensity / 4 + tilt * 0.35;
    return { intensity: intensity, novelty: novelty, redShare: Math.min(0.92, Math.max(0.08, red)) };
  }

  var PRODUCTIONS = {
    sep: [{ title: "September shoot 1" }, { title: "September shoot 2" }, { title: "September shoot 3" }],
    oct: [{ title: "October shoot 1" }, { title: "October shoot 2" }, { title: "October shoot 3" }],
  };

  function productionsForMonth(monthId) {
    return (PRODUCTIONS[monthId] || []).map(function (idea, i) {
      return {
        id: monthId + "-p" + i,
        n: i + 1,
        monthId: monthId,
        title: idea.title,
        blurb: idea.blurb || "",
        hue: "#8b2a22",
        salt: seed(monthId + ":prod:" + i),
      };
    });
  }

  function eventChipsForMonth(monthId) {
    return eventsForMonth(monthId)
      .slice(0, 5)
      .map(function (ev, i) {
        ev.kind = ev.type === "sales" ? "sale" : "week";
        ev.salt = seed(ev.id + ":chip");
        ev.n = i + 1;
        return ev;
      });
  }

  function isoDate(y, m, d) {
    var mm = m < 10 ? "0" + m : String(m);
    var dd = d < 10 ? "0" + d : String(d);
    return y + "-" + mm + "-" + dd;
  }

  function monthRange(month) {
    var min = isoDate(month.year, month.month, 1);
    var max = isoDate(month.year, month.month, month.days);
    if (month.id === "sep") {
      min = isoDate(month.year, 8, 24);
      var now = new Date();
      if (now.getFullYear() === month.year && now.getMonth() + 1 === 8 && now.getDate() > 24) {
        min = isoDate(month.year, 8, now.getDate());
      }
    }
    return { min: min, max: max };
  }

  function defaultShootDate(month, index) {
    var days = [8, 15, 22];
    var mm = month.month < 10 ? "0" + month.month : String(month.month);
    var d = days[index] || 15;
    return month.year + "-" + mm + "-" + (d < 10 ? "0" + d : String(d));
  }

  var MONTHS = [
    { id: "sep", label: "September", short: "Sep", mark: "leaf", year: 2026, month: 9, days: 30 },
    { id: "oct", label: "October", short: "Oct", mark: "pumpkin", year: 2026, month: 10, days: 31 },
  ];

  var EVENTS = [
    {
      id: "hw-live",
      name: "Halloween live",
      type: "sales",
      month: "aug",
      when: "Aug 18",
      windowDays: 5,
      slot: 1,
      blurb: "Collection goes live. This window is the first public look — teasers, drop-day posts, and the first read on whether people actually want it.",
    },
    {
      id: "meltdown",
      name: "Summer Meltdown",
      type: "sales",
      month: "aug",
      when: "late Aug",
      windowDays: 7,
      slot: 2,
      blurb: "Last summer sale before the season turns. Daily deals, story cards, and leftover summer footage. Easy to under-plan because Halloween is already in the room.",
    },
    {
      id: "labor-sale",
      name: "Labor Day Sale",
      type: "sales",
      month: "sep",
      when: "Sep 3–7",
      start: "2026-09-03",
      end: "2026-09-07",
      windowDays: 5,
      slot: 1,
      blurb: "Product focus: summer collection.",
    },
    {
      id: "holiday-coll-shoot",
      name: "Holiday Collection Shoot",
      type: "shoot",
      month: "sep",
      when: "Sep 21",
      start: "2026-09-21",
      windowDays: 1,
      slot: 2,
      blurb: "Production day. See products.",
      needsDelivery: false,
    },
    {
      id: "calamigos",
      name: "Calamigos Movie Night",
      type: "event",
      month: "sep",
      when: "Sep 26",
      start: "2026-09-26",
      windowDays: 1,
      slot: 3,
      blurb: "TBD whether we need to be there. Event shoot?",
    },
    {
      id: "hw-sale",
      name: "Halloween Sale",
      type: "sales",
      month: "oct",
      when: "Oct 1–4",
      start: "2026-10-01",
      end: "2026-10-04",
      windowDays: 4,
      slot: 1,
      blurb: "30% off all Halloween decor.",
    },
    {
      id: "holiday-launch",
      name: "Holiday Collection Launch",
      type: "sales",
      month: "oct",
      when: "Oct 13",
      start: "2026-10-13",
      windowDays: 1,
      slot: 2,
      blurb: "Holiday collection goes live.",
    },
    {
      id: "thanks",
      name: "Thanksgiving",
      type: "calendar",
      month: "nov",
      when: "Nov 26",
      windowDays: 5,
      slot: 1,
      blurb: "A calendar beat, not a catalog dump. Hosting, gathering, the house filling up. Easy to skip if BFCM takes every slot.",
    },
    {
      id: "bfcm",
      name: "BFCM",
      type: "sales",
      month: "nov",
      when: "Nov 27",
      windowDays: 5,
      slot: 2,
      blurb: "Placeholder sales window. Volume here is a choice: conversion content, or you spend the days on holiday storytelling instead.",
    },
    {
      id: "christmas",
      name: "Christmas",
      type: "calendar",
      month: "dec",
      when: "Dec 25",
      windowDays: 10,
      slot: 1,
      blurb: "The holiday season, not a single day. Sundays-until-Christmas energy. This is what the mid-September holiday shoot has to feed.",
    },
  ];

  var EMPTY_MIX = {
    daShoot: false,
    inhouse: false,
    sourcing: false,
    recut: false,
    stories: false,
  };

  function cloneMix(mix) {
    return {
      daShoot: !!mix.daShoot,
      inhouse: !!mix.inhouse,
      sourcing: !!mix.sourcing,
      recut: !!mix.recut,
      stories: !!mix.stories,
    };
  }

  function defaultPiece() {
    return { intensity: null, mix: cloneMix({}), placed: false };
  }

  function blankBoard() {
    return allPieces(function () {
      return defaultPiece();
    });
  }

  function markPlaced(pieces) {
    Object.keys(pieces).forEach(function (id) {
      pieces[id].placed = true;
    });
    return pieces;
  }

  function allPieces(makePiece) {
    var pieces = {};
    EVENTS.forEach(function (ev) {
      pieces[ev.id] = makePiece(ev);
    });
    return pieces;
  }

  function holdTheLine() {
    return markPlaced(
      allPieces(function () {
        return { intensity: "light", mix: cloneMix({ recut: true }) };
      })
    );
  }

  function seasonalPush() {
    var hot = {
      "hw-live": true,
      "peak-hw": true,
      halloween: true,
      "holiday-launch": true,
      bfcm: true,
    };
    return markPlaced(
      allPieces(function (ev) {
        if (hot[ev.id]) {
          return {
            intensity: ev.id === "peak-hw" || ev.id === "holiday-launch" ? "push" : "standard",
            mix: cloneMix({ daShoot: true, recut: true }),
          };
        }
        return { intensity: "light", mix: cloneMix({ recut: true }) };
      })
    );
  }

  function allOutQ4() {
    return markPlaced(
      allPieces(function (ev) {
        var q4 = ev.month === "oct" || ev.month === "nov" || ev.month === "dec";
        var sales = ev.type === "sales";
        return {
          intensity: q4 && sales ? "allout" : q4 ? "push" : "standard",
          mix: cloneMix({
            daShoot: sales && q4,
            inhouse: ev.type === "calendar",
            sourcing: sales,
            recut: true,
            stories: sales,
          }),
        };
      })
    );
  }

  var GROUP_LINES = {
    people: "A Fun People beat. Faces, hanging out, the inflatable as the reason they’re together.",
    product: "How it works. Setup, pack-down, why this isn’t a costume.",
    season: "A calendar beat. The month should feel like this, not like a catalog.",
    drop: "A drop / sale beat. Conversion without turning the whole grid into a flyer.",
    house: "The house filling up. Rooms, yards, the set becoming furniture.",
  };

  function starterPlan(mode) {
    var mix = defaultMix();
    var prod = {};
    var posted = {};
    if (mode === "season") {
      mix.sep = copyMix(STRATEGIES.ii.owner);
      mix.oct = copyMix(STRATEGIES.ii.owner);
    }
    if (mode === "full") {
      mix.sep = copyMix(STRATEGIES.ii.owner);
      mix.oct = copyMix(STRATEGIES.iii.owner);
    }
    MONTHS.forEach(function (m) {
      var shoots = productionsForMonth(m.id);
      var events = eventChipsForMonth(m.id);
      var ideas = contentForMonth(m.id);
      var take = mode === "thin" ? 2 : mode === "season" ? 4 : 6;
      var i;
      for (i = 0; i < take && i < ideas.length; i++) {
        var shoot = shoots[i < 3 ? 0 : 1];
        if (!shoot) continue;
        if (!prod[shoot.id]) prod[shoot.id] = { ideas: [], eventId: events[0] ? events[0].id : null };
        if (i < Math.ceil(take / 2)) {
          prod[shoot.id].ideas.push(ideas[i].id);
        } else if (events[0]) {
          if (!posted[events[0].id]) posted[events[0].id] = [];
          posted[events[0].id].push(ideas[i].id);
          prod[shoot.id].eventId = events[0].id;
        }
      }
    });
    return { mix: mix, prod: prod, posted: posted };
  }

  var TIMELINE_STEPS = [
    { id: "concept", label: "Concept revision", at: -3, note: "3 working days before shoot" },
    { id: "prepro", label: "Pre-pro", at: -1, note: "1 working day before shoot" },
    { id: "shoot", label: "Shoot", at: 0, note: "Day 0" },
    { id: "edit1", label: "Editing round 1", at: 3, note: "3 working days" },
    { id: "revise1", label: "Round 1 revisions", at: 5, atNoRound2: 4, note: "1–2 working days", noteNoRound2: "1 working day" },
    { id: "edit2", label: "Editing round 2", at: 7, note: "1–2 working days", round2: true },
    { id: "revise2", label: "Round 2 revisions", at: 8, note: "1 working day · 2 working days before delivery", round2: true },
    {
      id: "deliver",
      label: "Final delivery",
      at: 10,
      atNoRound2: 5,
      note: "2 working days after round 2 revisions",
      noteNoRound2: "5 working days after shoot",
    },
  ];

  function timelineSteps(round2) {
    var out = [];
    for (var i = 0; i < TIMELINE_STEPS.length; i++) {
      var step = TIMELINE_STEPS[i];
      if (step.round2 && !round2) continue;
      out.push({
        id: step.id,
        label: step.label,
        at: !round2 && step.atNoRound2 != null ? step.atNoRound2 : step.at,
        note: !round2 && step.noteNoRound2 ? step.noteNoRound2 : step.note,
      });
    }
    return out;
  }

  var DEAL_MODELS = [
    {
      id: "you-ideas",
      guarantee: false,
      title: "You suggest concepts → we produce",
    },
    {
      id: "we-ideas-you-revise",
      guarantee: false,
      title: "We suggest concepts → we produce → concept is revised afterwards",
    },
    {
      id: "we-own",
      guarantee: true,
      title: "We suggest concepts → we produce them → we take responsibility for how it performs",
    },
  ];

  var PRODUCTION_LISTS = [
    {
      id: "location",
      label: "Location",
      items: [
        { id: "loc-porch", title: "House with a nice porch" },
        { id: "loc-lawn", title: "Large lawn with healthy green grass" },
        { id: "loc-yard", title: "Backyard with room for the movie screen" },
      ],
    },
    {
      id: "wardrobe",
      label: "Wardrobe",
      items: [
        { id: "ward-steamer", title: "Clothes steamer" },
        { id: "ward-looks", title: "Casual looks and Halloween outfits" },
      ],
    },
    {
      id: "talent",
      label: "Talent",
      items: [
        {
          id: "talent-model",
          title: "One model booked",
          note: "Enough for a social shoot — no extra photographers or videographers on set.",
        },
        {
          id: "talent-founders",
          title: "Founders available for founder content",
          note: "Optional.",
        },
      ],
    },
    {
      id: "crew",
      label: "Crew",
      items: [
        { id: "crew-assistant", title: "Funboy assistant to inflate products and decorate" },
      ],
    },
    {
      id: "props",
      label: "Props",
      items: [
        { id: "props-halloween", title: "Halloween props", note: "TBD." },
      ],
    },
  ];

  var REPORTS = [
    {
      id: "2026-09",
      label: "September 2026",
      sub: "Visual recap — Instagram and TikTok",
      file: "september-2026-recap.html",
    },
    {
      id: "2026-08",
      label: "August 2026",
      sub: "Visual recap — Instagram and TikTok",
      file: "august-2026-recap.html",
    },
  ];

  root.CAMPAIGN = {
    REPORTS: REPORTS,
    PACE_OPTIONS: PACE_OPTIONS,
    WEEKS: WEEKS,
    mixFromPace: mixFromPace,
    paceFromMix: paceFromMix,
    monthlyNeed: monthlyNeed,
    fitMixToTotal: fitMixToTotal,
    clampBars: clampBars,
    nudgeMix: nudgeMix,
    recommendedShoots: recommendedShoots,
    recommendedShootsFromMix: recommendedShootsFromMix,
    IDEAS_PER_SHOOT: IDEAS_PER_SHOOT,
    IDEAS_PER_OPP: IDEAS_PER_OPP,
    BAR_MAX: BAR_MAX,
    DA_MAX: DA_MAX,
    PILLARS: PILLARS,
    pillarById: pillarById,
    defaultPace: defaultPace,
    defaultMix: defaultMix,
    copyMix: copyMix,
    mixTotal: mixTotal,
    chipMeters: chipMeters,
    MONTHS: MONTHS,
    monthRange: monthRange,
    defaultShootDate: defaultShootDate,
    eventsForMonth: eventChipsForMonth,
    contentForMonth: contentForMonth,
    allSheetIdeas: allSheetIdeas,
    loadSheet: loadSheet,
    productionsForMonth: productionsForMonth,
    TIMELINE_STEPS: TIMELINE_STEPS,
    timelineSteps: timelineSteps,
    deliveryOffset: function (round2) {
      var steps = timelineSteps(round2);
      for (var i = 0; i < steps.length; i++) {
        if (steps[i].id === "deliver") return steps[i].at;
      }
      return round2 ? 10 : 5;
    },
    DEAL_MODELS: DEAL_MODELS,
    PRODUCTION_LISTS: PRODUCTION_LISTS,
  };
})(window);
