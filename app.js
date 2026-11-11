(function () {
  "use strict";

  var C = window.CAMPAIGN;
  var STORE = "funboy-campaign-map-v12";
  var OWNER_NAME = { da: "DA", plus: "Sourcing", f: "Funboy internal" };
  var OWNER_ORDER = ["da", "plus", "f"];

  var state = {
    month: "oct",
    screen: "board",
    selected: null,
    pace: C.defaultPace(),
    mix: C.defaultMix(),
    shoots: {},
    prod: {},
    posted: {},
    origin: {},
    owners: {},
    opps: {},
    focusShoot: null,
    focusKind: null,
    focusOpp: null,
    filterPillar: null,
    foldOpps: true,
    deal: "you-ideas",
    lastDeal: "you-ideas",
    round2: true,
    productionChecks: {},
    popup: null,
  };

  function monthById(id) {
    for (var i = 0; i < C.MONTHS.length; i++) {
      if (C.MONTHS[i].id === id) return C.MONTHS[i];
    }
    return C.MONTHS[0];
  }

  function monthNow() {
    return monthById(state.month);
  }

  function paceNow() {
    return state.pace[state.month] || 2.5;
  }

  function mixNow() {
    return state.mix[state.month] || C.mixFromPace(paceNow());
  }

  function eventsNow() {
    return C.eventsForMonth(state.month);
  }

  function allProds() {
    return C.productionsForMonth("sep").concat(C.productionsForMonth("oct"));
  }

  function allEvents() {
    return C.eventsForMonth("sep").concat(C.eventsForMonth("oct"));
  }

  function allIdeas() {
    var seen = {};
    var out = [];
    ["sep", "oct"].forEach(function (monthId) {
      C.contentForMonth(monthId).forEach(function (idea) {
        if (seen[idea.id]) return;
        seen[idea.id] = true;
        out.push(idea);
      });
    });
    return out;
  }

  function findById(list, id) {
    for (var i = 0; i < list.length; i++) if (list[i].id === id) return list[i];
    return null;
  }

  function findEvent(id) {
    return findById(allEvents(), id);
  }

  function findProd(id) {
    return findById(allProds(), id);
  }

  function findIdea(id) {
    return findById(allIdeas(), id);
  }

  function shootRec(id) {
    if (!state.shoots[id]) state.shoots[id] = { approved: false, date: "", title: "" };
    if (state.shoots[id].title == null) state.shoots[id].title = "";
    return state.shoots[id];
  }

  function shootTitle(prod) {
    if (!prod) return "";
    var custom = shootRec(prod.id).title;
    custom = custom && String(custom).replace(/^\s+|\s+$/g, "");
    return custom || prod.title;
  }

  function approvedProds() {
    return neededProds().filter(function (p) {
      return shootRec(p.id).approved;
    });
  }

  function prodRec(id) {
    if (!state.prod[id]) state.prod[id] = { ideas: [], eventId: null };
    if (!state.prod[id].ideas) state.prod[id].ideas = [];
    return state.prod[id];
  }

  function postedFor(eventId) {
    if (!state.posted[eventId]) state.posted[eventId] = [];
    return state.posted[eventId];
  }

  function removeIdeaFromProds(id) {
    Object.keys(state.prod).forEach(function (pid) {
      state.prod[pid].ideas = (state.prod[pid].ideas || []).filter(function (x) {
        return x !== id;
      });
    });
  }

  function removeIdeaFromEvents(id) {
    Object.keys(state.posted).forEach(function (eid) {
      state.posted[eid] = (state.posted[eid] || []).filter(function (x) {
        return x !== id;
      });
    });
  }

  function stripIdea(id) {
    removeIdeaFromProds(id);
    removeIdeaFromEvents(id);
  }

  function ideaShootId(id) {
    var found = "";
    Object.keys(state.prod).forEach(function (pid) {
      if ((state.prod[pid].ideas || []).indexOf(id) !== -1) found = pid;
    });
    return found;
  }

  function ideaHome(id) {
    var eventId = null;
    var prodId = null;
    Object.keys(state.posted).forEach(function (eid) {
      if ((state.posted[eid] || []).indexOf(id) !== -1) eventId = eid;
    });
    Object.keys(state.prod).forEach(function (pid) {
      if ((state.prod[pid].ideas || []).indexOf(id) !== -1) prodId = pid;
    });
    if (eventId) return { kind: "event", id: eventId };
    if (prodId) return { kind: "prod", id: prodId };
    return { kind: "pool" };
  }

  function rememberOrigin(ideaId, prodId) {
    if (!state.origin) state.origin = {};
    if (prodId) state.origin[ideaId] = prodId;
    else delete state.origin[ideaId];
  }

  function moveToProd(ideaId, prodId) {
    var rec = prodRec(prodId);
    if ((rec.ideas || []).indexOf(ideaId) !== -1) {
      rememberOrigin(ideaId, prodId);
      return true;
    }
    if (rec.ideas.length >= C.IDEAS_PER_SHOOT) return false;
    removeIdeaFromProds(ideaId);
    rec.ideas.push(ideaId);
    rememberOrigin(ideaId, prodId);
    return true;
  }

  function ownerOf(ideaId) {
    return (state.owners && state.owners[ideaId]) || "da";
  }

  function setOwner(ideaId, owner) {
    if (!state.owners) state.owners = {};
    state.owners[ideaId] = owner;
  }

  function cycleOwner(ideaId) {
    var cur = ownerOf(ideaId);
    var i = OWNER_ORDER.indexOf(cur);
    setOwner(ideaId, OWNER_ORDER[(i + 1) % OWNER_ORDER.length]);
  }

  function nextOwner() {
    var mix = mixNow();
    var used = { da: 0, f: 0, plus: 0 };
    eventsNow().forEach(function (ev) {
      (state.posted[ev.id] || []).forEach(function (id) {
        var o = ownerOf(id);
        if (used[o] != null) used[o] += 1;
      });
    });
    if (used.da < (mix.da || 0)) return "da";
    if (used.f < (mix.f || 0)) return "f";
    return "plus";
  }

  function moveToEvent(ideaId, eventId) {
    if (!oppRec(eventId).available) return false;
    if ((postedFor(eventId) || []).indexOf(ideaId) !== -1) return true;
    if (postedFor(eventId).length >= C.IDEAS_PER_OPP) return false;
    var shootId = ideaShootId(ideaId);
    if (shootId) rememberOrigin(ideaId, shootId);
    removeIdeaFromEvents(ideaId);
    postedFor(eventId).push(ideaId);
    if (!state.owners || !state.owners[ideaId]) setOwner(ideaId, nextOwner());
    return true;
  }

  function returnToPool(ideaId) {
    stripIdea(ideaId);
    rememberOrigin(ideaId, null);
  }

  function shootForReturn(ideaId) {
    var originId = state.origin && state.origin[ideaId];
    if (originId && findProd(originId) && shootRec(originId).approved) return originId;
    var first = approvedProds()[0];
    return first ? first.id : null;
  }

  function ideasNow() {
    return C.contentForMonth(state.month);
  }

  function poolIdeas() {
    return ideasNow().filter(function (idea) {
      return ideaHome(idea.id).kind === "pool";
    });
  }

  function unlockedIdeas() {
    var out = [];
    approvedProds().forEach(function (p) {
      ((state.prod[p.id] && state.prod[p.id].ideas) || []).forEach(function (id) {
        var idea = findIdea(id);
        if (idea) out.push(idea);
      });
    });
    return out;
  }

  function postedCount(monthId) {
    var n = 0;
    C.eventsForMonth(monthId).forEach(function (ev) {
      n += (state.posted[ev.id] || []).length;
    });
    return n;
  }

  function setPace(pace) {
    state.pace[state.month] = pace;
    state.mix[state.month] = C.mixFromPace(pace);
    syncShootsToPace();
  }

  function neededProds() {
    return C.productionsForMonth(state.month).slice(0, C.recommendedShootsFromMix(mixNow()));
  }

  function setMixPart(key, value) {
    state.mix[state.month] = C.nudgeMix(mixNow(), key, value);
    var next = C.paceFromMix(mixNow());
    if (next > paceNow()) state.pace[state.month] = next;
    syncShootsToPace();
  }

  function syncShootsToPace() {
    var need = C.recommendedShootsFromMix(mixNow());
    C.productionsForMonth(state.month).forEach(function (prod, i) {
      if (i >= need) toggleShoot(prod, false);
      else if (!shootRec(prod.id).approved) toggleShoot(prod, true);
    });
    if (!state.focusKind && need) {
      var first = C.productionsForMonth(state.month)[0];
      if (first) focusShoot(first);
    }
  }

  function toggleShoot(prod, on) {
    var rec = shootRec(prod.id);
    rec.approved = on;
    if (!on) {
      (prodRec(prod.id).ideas || []).slice().forEach(function (id) {
        removeIdeaFromProds(id);
        if (state.origin && state.origin[id] === prod.id) rememberOrigin(id, null);
      });
      prodRec(prod.id).ideas = [];
      if (state.focusShoot === prod.id) {
        state.focusShoot = null;
        if (state.focusKind === "shoot") state.focusKind = null;
      }
    }
  }

  function oppRec(id) {
    if (!state.opps) state.opps = {};
    if (!state.opps[id]) state.opps[id] = { available: true };
    return state.opps[id];
  }

  function availableOpps() {
    return eventsNow().filter(function (ev) {
      return oppRec(ev.id).available;
    });
  }

  function toggleOpp(ev, on) {
    var rec = oppRec(ev.id);
    rec.available = on;
    if (!on) {
      state.posted[ev.id] = [];
      if (state.focusOpp === ev.id) {
        state.focusOpp = null;
        if (state.focusKind === "opp") state.focusKind = null;
      }
    }
  }

  function focusShoot(prod) {
    if (!shootRec(prod.id).approved) return;
    state.focusKind = "shoot";
    state.focusShoot = prod.id;
    state.focusOpp = null;
  }

  function focusOpp(ev) {
    if (!oppRec(ev.id).available) return;
    state.focusKind = "opp";
    state.focusOpp = ev.id;
    state.focusShoot = null;
  }

  function focusedTarget() {
    if (state.focusKind === "opp" && state.focusOpp) {
      var ev = findEvent(state.focusOpp);
      if (ev && oppRec(ev.id).available) return { kind: "opp", item: ev };
    }
    var shoot = focusedProd();
    if (state.focusKind === "shoot" && shoot) return { kind: "shoot", item: shoot };
    if (shoot) return { kind: "shoot", item: shoot };
    var first = availableOpps()[0];
    if (first) return { kind: "opp", item: first };
    return null;
  }

  function focusedProd() {
    var approved = approvedProds();
    if (!approved.length) return null;
    if (state.focusShoot) {
      for (var i = 0; i < approved.length; i++) {
        if (approved[i].id === state.focusShoot) return approved[i];
      }
    }
    return approved[0];
  }

  function pillarCounts() {
    var counts = {};
    C.PILLARS.forEach(function (p) {
      counts[p.id] = 0;
    });
    approvedProds().forEach(function (p) {
      (prodRec(p.id).ideas || []).forEach(function (id) {
        var idea = findIdea(id);
        if (idea && counts[idea.pillar] != null) counts[idea.pillar] += 1;
      });
    });
    availableOpps().forEach(function (ev) {
      postedFor(ev.id).forEach(function (id) {
        var idea = findIdea(id);
        if (idea && counts[idea.pillar] != null) counts[idea.pillar] += 1;
      });
    });
    return counts;
  }

  function clampMix(mix) {
    return C.clampBars(mix || { da: 0, f: 0, plus: 0 });
  }

  function snapshot() {
    return {
      month: state.month,
      pace: state.pace,
      mix: state.mix,
      shoots: state.shoots,
      prod: state.prod,
      posted: state.posted,
      origin: state.origin || {},
      owners: state.owners || {},
      opps: state.opps || {},
      deal: state.deal || "you-ideas",
      lastDeal: state.lastDeal || "you-ideas",
      foldOpps: state.foldOpps !== false,
      round2: state.round2 !== false,
      productionChecks: state.productionChecks || {},
    };
  }

  function applySnapshot(parsed) {
    if (!parsed) return;
    state.month = "oct";
    state.pace = parsed.pace || C.defaultPace();
    state.mix = parsed.mix || C.defaultMix();
    if (state.mix.sep) clampMix(state.mix.sep);
    if (state.mix.oct) clampMix(state.mix.oct);
    ["sep", "oct"].forEach(function (id) {
      if (state.pace[id] !== 5 && C.PACE_OPTIONS.indexOf(state.pace[id]) === -1) {
        state.pace[id] = 2.5;
        state.mix[id] = C.mixFromPace(2.5);
      }
    });
    state.shoots = parsed.shoots || {};
    state.prod = parsed.prod || {};
    state.posted = parsed.posted || {};
    state.origin = parsed.origin || {};
    state.owners = parsed.owners || {};
    state.opps = parsed.opps || {};
    state.deal = parsed.deal || "you-ideas";
    state.lastDeal = parsed.lastDeal || "you-ideas";
    state.foldOpps = parsed.foldOpps !== false;
    state.round2 = parsed.round2 !== false;
    state.productionChecks = parsed.productionChecks || {};
    clearDefaultShootDates();
  }

  function load() {
    try {
      var raw = localStorage.getItem(STORE);
      if (!raw) {
        state.pace = C.defaultPace();
        state.mix = C.defaultMix();
        save();
      } else {
        applySnapshot(JSON.parse(raw));
      }
    } catch (err) {
      state.pace = C.defaultPace();
      state.mix = C.defaultMix();
    }
  }

  function clearDefaultShootDates() {
    C.MONTHS.forEach(function (month) {
      C.productionsForMonth(month.id).forEach(function (prod, i) {
        var rec = state.shoots[prod.id];
        if (rec && rec.date === C.defaultShootDate(month, i)) rec.date = "";
      });
    });
  }

  function save() {
    localStorage.setItem(STORE, JSON.stringify(snapshot()));
  }

  function el(tag, cls, text) {
    var node = document.createElement(tag);
    if (cls) node.className = cls;
    if (text != null) node.textContent = text;
    return node;
  }

  function ownershipPie(owner, extra) {
    owner = owner || { da: 0, f: 0, plus: 0 };
    var total = C.mixTotal(owner);
    var wrap = el("div", "own" + (total === 0 ? " is-empty" : "") + (extra ? " " + extra : ""));
    wrap.setAttribute("aria-label", "DA " + owner.da + ", Sourcing " + owner.plus + ", Funboy internal " + owner.f);
    var pie = el("div", "own-pie");
    if (!total) pie.style.background = "#d8cba8";
    else {
      var daDeg = (owner.da / total) * 360;
      var plusDeg = (owner.plus / total) * 360;
      pie.style.background =
        "conic-gradient(#9dc9f5 0 " +
        daDeg +
        "deg, #3d6e9a " +
        daDeg +
        "deg " +
        (daDeg + plusDeg) +
        "deg, #c45c2a " +
        (daDeg + plusDeg) +
        "deg 360deg)";
    }
    wrap.appendChild(pie);
    var labeled = extra && extra.indexOf("is-labeled") !== -1;
    if (total && labeled) {
      function sliceN(n, start, span) {
        if (!n || span < 14) return;
        var mid = ((start + span / 2) * Math.PI) / 180;
        var lab = el("span", "pie-n");
        lab.textContent = String(n);
        lab.style.left = 50 + Math.sin(mid) * 28 + "%";
        lab.style.top = 50 - Math.cos(mid) * 28 + "%";
        pie.appendChild(lab);
      }
      var daDeg = (owner.da / total) * 360;
      var plusDeg = (owner.plus / total) * 360;
      sliceN(owner.da, 0, daDeg);
      sliceN(owner.plus, daDeg, plusDeg);
      sliceN(owner.f, daDeg + plusDeg, 360 - daDeg - plusDeg);
    }
    if (!labeled) {
      var legend = el("div", "own-legend");
      function key(cls, label, n) {
        var item = el("span", "own-key own-" + cls);
        item.appendChild(el("i"));
        item.appendChild(document.createTextNode(label + " " + n));
        return item;
      }
      legend.appendChild(key("da", "DA", owner.da));
      legend.appendChild(key("plus", "Sourcing", owner.plus));
      legend.appendChild(key("f", "Funboy internal", owner.f));
      wrap.appendChild(legend);
    }
    return wrap;
  }

  function goBoard() {
    state.screen = "board";
    state.selected = null;
    state.popup = null;
    persistAndPaint();
  }

  function goIdeas() {
    state.screen = "ideas";
    state.popup = null;
    persistAndPaint();
  }

  function goProduction() {
    state.screen = "production";
    state.popup = null;
    persistAndPaint();
  }

  function goObjective() {
    state.screen = "objective";
    state.popup = null;
    persistAndPaint();
  }

  function goReports() {
    state.screen = "reports";
    state.popup = null;
    persistAndPaint();
  }

  function paceButtons() {
    var paceRow = el("div", "pace-row");
    C.PACE_OPTIONS.forEach(function (n) {
      var shown = n === 4 && paceNow() >= 5 ? 5 : n;
      var btn = el("button", "pace-btn");
      btn.type = "button";
      btn.setAttribute("aria-pressed", n === 4 ? (paceNow() >= 4 ? "true" : "false") : paceNow() === n ? "true" : "false");
      btn.textContent = shown === 2.5 ? "2.5" : String(shown);
      btn.addEventListener("click", function () {
        setPace(n);
        persistAndPaint();
      });
      paceRow.appendChild(btn);
    });
    return paceRow;
  }

  function mixHead() {
    var mix = mixNow();
    var total = C.mixTotal(mix);
    var head = el("div", "map-head");
    head.appendChild(el("h2", "map-title", monthNow().label));
    head.appendChild(el("p", "label", "Posts per week"));
    head.appendChild(paceButtons());
    var hero = el("div", "mix-hero");
    hero.appendChild(ownershipPie(mix, "is-hero is-labeled"));
    hero.appendChild(
      mixBars(mix, total, function (key, value) {
        setMixPart(key, value);
        persistAndPaint();
      })
    );
    var num = el("div", "hero-num map-num");
    num.appendChild(el("b", "", String(total)));
    num.appendChild(el("span", "", "this month"));
    hero.appendChild(num);
    head.appendChild(hero);
    return head;
  }

  function renderMonths() {
    var board = state.screen === "board";
    document.getElementById("viewShoots").setAttribute("aria-pressed", board && state.month === "oct" ? "true" : "false");
    document.getElementById("viewIdeas").setAttribute("aria-pressed", state.screen === "ideas" ? "true" : "false");
    document.getElementById("viewProduction").setAttribute("aria-pressed", state.screen === "production" ? "true" : "false");
    document.getElementById("viewObjective").setAttribute("aria-pressed", state.screen === "objective" ? "true" : "false");
    document.getElementById("viewReports").setAttribute("aria-pressed", state.screen === "reports" ? "true" : "false");
  }

  function renderLegend() {
    document.getElementById("groupLegend").innerHTML = "";
  }

  function renderPlanCount() {
    document.getElementById("planCount").textContent = "content strategy";
  }

  function backBar() {
    var row = el("div", "page-bar");
    var btn = el("button", "btn-back", "Back");
    btn.type = "button";
    btn.addEventListener("click", goBoard);
    row.appendChild(btn);
    return row;
  }

  function pillarChip(id) {
    var p = C.pillarById(id);
    if (!p) return null;
    var node = el("span", "pillar-chip");
    node.textContent = p.short;
    node.title = p.name;
    node.style.background = p.bg;
    node.style.color = p.fg;
    return node;
  }

  function oppChip(eventId) {
    var ev = findEvent(eventId);
    if (!ev) return null;
    var node = el("span", "opp-chip");
    node.textContent = ev.title;
    return node;
  }

  function eventPills(mode) {
    var wrap = el("div", "event-pills");
    C.eventsForMonth(state.month).forEach(function (ev) {
      var on = mode === "filter" && state.filterEvent === ev.id;
      var btn = el(
        "button",
        "event-pill" + (ev.kind === "sale" ? " is-sale" : "") + (on ? " is-on" : "")
      );
      btn.type = "button";
      btn.textContent = ev.title;
      if (ev.when) btn.title = ev.when;
      btn.addEventListener("click", function () {
        if (mode === "filter") {
          state.filterEvent = state.filterEvent === ev.id ? null : ev.id;
          persistAndPaint();
          return;
        }
        state.screen = "event";
        state.selected = ev.id;
        persistAndPaint();
      });
      wrap.appendChild(btn);
    });
    return wrap;
  }

  function pillarPlan() {
    var wrap = el("div", "pillar-row");
    var counts = pillarCounts();
    C.PILLARS.forEach(function (p) {
      var chip = pillarChip(p.id);
      chip.textContent = p.short + " " + (counts[p.id] || 0);
      wrap.appendChild(chip);
    });
    return wrap;
  }

  function contentFilters() {
    var wrap = el("div", "filter-row");
    var all = el("button", "filter-chip" + (!state.filterPillar ? " is-on" : ""));
    all.type = "button";
    all.textContent = "All";
    all.addEventListener("click", function () {
      state.filterPillar = null;
      persistAndPaint();
    });
    wrap.appendChild(all);
    C.PILLARS.forEach(function (p) {
      var on = state.filterPillar === p.id;
      var chip = el("button", "filter-chip" + (on ? " is-on" : ""));
      chip.type = "button";
      chip.textContent = p.short;
      chip.title = p.name;
      chip.style.background = on ? p.bg : "transparent";
      chip.style.color = on ? p.fg : "var(--ink)";
      chip.style.boxShadow = "inset 0 0 0 1px " + p.bg;
      chip.addEventListener("click", function () {
        state.filterPillar = p.id;
        persistAndPaint();
      });
      wrap.appendChild(chip);
    });
    return wrap;
  }

  function oppsFold() {
    var wrap = el("div", "fold" + (state.foldOpps ? " is-open" : ""));
    var btn = el("button", "fold-btn" + (state.foldOpps ? " is-open" : ""));
    btn.type = "button";
    btn.appendChild(el("span", "", "Opportunities"));
    btn.appendChild(el("span", "fold-caret", state.foldOpps ? "▾" : "▸"));
    btn.addEventListener("click", function () {
      state.foldOpps = !state.foldOpps;
      persistAndPaint();
    });
    wrap.appendChild(btn);
    if (state.foldOpps) {
      eventsNow().forEach(function (ev) {
        wrap.appendChild(oppRow(ev));
      });
    }
    return wrap;
  }

  function shootBlock(mix) {
    var wrap = el("div", "shoot-block");
    wrap.appendChild(el("p", "map-label", "Select shoots"));
    var need = C.recommendedShootsFromMix(mix);
    if (!need) {
      wrap.appendChild(el("p", "map-note", "No DA shoot."));
      return wrap;
    }
    wrap.appendChild(el("p", "map-note", "Name each shoot and pick a date."));
    neededProds().forEach(function (prod, i) {
      wrap.appendChild(shootRow(prod, { focus: true, index: i }));
    });
    return wrap;
  }

  function shootRow(prod, opts) {
    opts = opts || {};
    var recs = shootRec(prod.id);
    var focus = focusedProd();
    var index = opts.index || 0;
    var guard = opts.dates !== false ? shootGuard(index, recs.date) : null;
    var row = el(
      "div",
      "shoot-row" +
        (recs.approved ? " is-on" : "") +
        (opts.focus && state.focusKind === "shoot" && focus && focus.id === prod.id ? " is-focus" : "") +
        (guard && guard.late ? " is-late" : "")
    );
    var check = el("button", "shoot-check");
    check.type = "button";
    check.setAttribute("aria-pressed", recs.approved ? "true" : "false");
    check.textContent = recs.approved ? "✓" : "";
    check.addEventListener("click", function (e) {
      e.stopPropagation();
      var next = !recs.approved;
      toggleShoot(prod, next);
      if (next) focusShoot(prod);
      persistAndPaint();
    });
    row.appendChild(check);
    var nameWrap = el("span", "shoot-name");
    var name = document.createElement("input");
    name.type = "text";
    name.placeholder = prod.title;
    name.value = recs.title || "";
    name.setAttribute("aria-label", "Shoot name");
    name.addEventListener("click", function (e) {
      e.stopPropagation();
    });
    name.addEventListener("input", function () {
      recs.title = name.value;
      save();
    });
    name.addEventListener("change", function () {
      recs.title = name.value.replace(/^\s+|\s+$/g, "");
      persistAndPaint();
    });
    nameWrap.appendChild(name);
    if (recs.approved) {
      var n = (prodRec(prod.id).ideas || []).length;
      nameWrap.appendChild(el("span", "shoot-count", n + "/" + C.IDEAS_PER_SHOOT));
    }
    row.appendChild(nameWrap);
    if (opts.dates !== false) {
      var range = C.monthRange(monthNow());
      var date = document.createElement("input");
      date.type = "date";
      date.min = range.min;
      date.max = range.max;
      if (guard && guard.latest && guard.latest >= range.min && guard.latest < range.max) {
        date.max = guard.latest;
      }
      date.value = recs.date || "";
      if (!recs.date) date.className = "is-empty";
      date.addEventListener("click", function (e) {
        e.stopPropagation();
      });
      date.addEventListener("change", function () {
        recs.date = date.value;
        if (date.value) recs.approved = true;
        persistAndPaint();
      });
      row.appendChild(date);
    }
    if (opts.focus) {
      row.addEventListener("click", function () {
        focusShoot(prod);
        persistAndPaint();
      });
    }
    var summary = recs.approved ? assignedNote((prodRec(prod.id).ideas || [])) : null;
    if (!guard && !summary) return row;
    var slot = el("div", "shoot-slot");
    slot.appendChild(row);
    if (guard) {
      slot.appendChild(
        el(
          "p",
          "shoot-guard" + (guard.late ? " is-late" : ""),
          guard.late
            ? "This date delivers after " + guard.event.title + " starts."
            : "Not later than " + formatWorkDate(guard.latest) + " so " + guard.event.title + " is delivered."
        )
      );
    }
    if (summary) slot.appendChild(summary);
    return slot;
  }

  function assignedNote(ids) {
    var titles = (ids || [])
      .map(findIdea)
      .filter(Boolean)
      .map(function (idea) {
        return idea.title;
      });
    if (!titles.length) return null;
    return el("p", "assign-summary", titles.join(" · "));
  }

  function homeNote(home) {
    if (home.kind === "prod") {
      var prod = findProd(home.id);
      return prod ? shootTitle(prod) : "";
    }
    if (home.kind === "event") {
      var ev = findEvent(home.id);
      return ev ? ev.title : "";
    }
    return "";
  }

  function oppRow(ev) {
    var rec = oppRec(ev.id);
    var target = focusedTarget();
    var row = el(
      "div",
      "opp-row" +
        (rec.available ? " is-on" : "") +
        (target && target.kind === "opp" && target.item.id === ev.id ? " is-focus" : "")
    );
    var check = el("button", "opp-check");
    check.type = "button";
    check.setAttribute("aria-pressed", rec.available ? "true" : "false");
    check.textContent = rec.available ? "✓" : "";
    check.addEventListener("click", function (e) {
      e.stopPropagation();
      var next = !rec.available;
      toggleOpp(ev, next);
      if (next) focusOpp(ev);
      persistAndPaint();
    });
    row.appendChild(check);
    var body = el("span", "opp-body");
    var name = el("strong", "", ev.title);
    body.appendChild(name);
    if (ev.blurb) body.appendChild(el("small", "opp-blurb", ev.blurb));
    row.appendChild(body);
    row.appendChild(el("span", "opp-when", ev.when || ""));
    row.addEventListener("click", function () {
      if (!oppRec(ev.id).available) toggleOpp(ev, true);
      focusOpp(ev);
      persistAndPaint();
    });
    var summary = rec.available ? assignedNote(postedFor(ev.id)) : null;
    if (!summary) return row;
    var wrap = el("div", "opp-slot");
    wrap.appendChild(row);
    wrap.appendChild(summary);
    return wrap;
  }

  function monthIdeaList() {
    var list = el("div", "checks");
    var ideas = ideasNow().filter(function (idea) {
      return !state.filterPillar || idea.pillar === state.filterPillar;
    });
    if (!ideas.length) list.appendChild(el("p", "empty", "No ideas for this filter."));
    ideas.forEach(function (idea) {
      list.appendChild(ideaCard(idea));
    });
    return list;
  }

  function ideaCard(idea) {
    var card = el("div", "idea-card");
    var body = el("span", "check-body");
    body.appendChild(el("strong", "", idea.title));
    var chips = el("span", "chip-line");
    if (idea.pillar) {
      var chip = pillarChip(idea.pillar);
      if (chip) chips.appendChild(chip);
    }
    if (idea.season) chips.appendChild(el("span", "season-chip", idea.season));
    if (idea.owner) chips.appendChild(el("span", "owner-chip", idea.owner));
    if (idea.series) chips.appendChild(el("span", "tag-chip", idea.series));
    if (idea.platform) chips.appendChild(el("span", "tag-chip", idea.platform));
    if (chips.childNodes.length) body.appendChild(chips);
    if (idea.link) {
      var a = el("a", "ref-link", "Open reference");
      a.href = idea.link;
      a.target = "_blank";
      a.rel = "noopener noreferrer";
      a.addEventListener("click", function (e) {
        e.preventDefault();
        e.stopPropagation();
        window.open(idea.link, "_blank", "noopener,noreferrer");
      });
      body.appendChild(a);
    }
    card.appendChild(body);
    return card;
  }

  function ideaTicketFields(idea) {
    if (!idea) return {};
    return {
      pillar: idea.pillar,
      season: idea.season,
      ownerLabel: idea.owner,
      series: idea.series,
      platform: idea.platform,
      link: idea.link,
    };
  }

  function checkList(rows, tone) {
    var list = el("div", "checks checks-" + (tone || "ink"));
    if (!rows.length) list.appendChild(el("p", "empty", "Empty"));
    rows.forEach(function (row) {
      var btn = el("button", "check-row" + (row.on ? " is-on" : ""));
      btn.type = "button";
      btn.appendChild(el("span", "check-mark", row.on ? "✓" : ""));
      var body = el("span", "check-body");
      body.appendChild(el("strong", "", row.title));
      var chips = el("span", "chip-line");
      if (row.pillar) {
        var chip = pillarChip(row.pillar);
        if (chip) chips.appendChild(chip);
      }
      if (row.eventId) {
        var opp = oppChip(row.eventId);
        if (opp) chips.appendChild(opp);
      }
      if (row.season) chips.appendChild(el("span", "season-chip", row.season));
      if (row.ownerLabel) chips.appendChild(el("span", "owner-chip", row.ownerLabel));
      if (row.series) chips.appendChild(el("span", "tag-chip", row.series));
      if (row.platform) chips.appendChild(el("span", "tag-chip", row.platform));
      if (chips.childNodes.length) body.appendChild(chips);
      if (row.note) body.appendChild(el("small", "", row.note));
      if (row.link) {
        var a = el("a", "ref-link", "Open reference");
        a.href = row.link;
        a.target = "_blank";
        a.rel = "noopener noreferrer";
        a.addEventListener("click", function (e) {
          e.preventDefault();
          e.stopPropagation();
          window.open(row.link, "_blank", "noopener,noreferrer");
        });
        body.appendChild(a);
      }
      btn.appendChild(body);
      if (row.owner) {
        var who = el("span", "check-owner owner-" + row.owner, OWNER_NAME[row.owner] || row.owner);
        btn.appendChild(who);
      }
      btn.addEventListener("click", function (e) {
        if (e.target.closest && e.target.closest("a.ref-link")) return;
        if (e.target.classList.contains("check-owner")) {
          cycleOwner(row.id);
          persistAndPaint();
          return;
        }
        row.onToggle();
        persistAndPaint();
      });
      list.appendChild(btn);
    });
    return list;
  }

  function mixBars(mix, total, onChange) {
    var wrap = el("div", "mix-stack" + (onChange ? " is-edit" : ""));
    wrap.appendChild(mixBar("da", "DA", mix.da, onChange));
    wrap.appendChild(mixBar("plus", "Sourcing", mix.plus, onChange));
    wrap.appendChild(mixBar("f", "Funboy internal", mix.f, onChange));
    return wrap;
  }

  function mixBar(key, label, value, onChange) {
    var max = key === "da" ? C.DA_MAX : C.BAR_MAX;
    var row = el("div", "mix-row mix-" + key + (onChange ? " is-edit" : ""));
    row.appendChild(el("span", "", label));
    var track = el("span", "mix-track");
    var fill = el("span", "mix-fill");
    fill.style.width = Math.round((value / max) * 100) + "%";
    track.appendChild(fill);
    if (onChange) {
      track.addEventListener("click", function (e) {
        e.stopPropagation();
        var rect = track.getBoundingClientRect();
        var t = (e.clientX - rect.left) / Math.max(1, rect.width);
        onChange(key, Math.round(t * max));
      });
    }
    row.appendChild(track);
    row.appendChild(el("b", "", String(value)));
    if (onChange) {
      var less = el("button", "mix-step", "−");
      less.type = "button";
      less.addEventListener("click", function (e) {
        e.stopPropagation();
        onChange(key, value - 1);
      });
      var more = el("button", "mix-step", "+");
      more.type = "button";
      more.addEventListener("click", function (e) {
        e.stopPropagation();
        onChange(key, value + 1);
      });
      row.appendChild(less);
      row.appendChild(more);
    }
    return row;
  }

  var WEEKDAYS = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
  var MONTHS_SHORT = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

  function parseISODate(iso) {
    var parts = (iso || "").split("-");
    if (parts.length < 3) return null;
    return new Date(Number(parts[0]), Number(parts[1]) - 1, Number(parts[2]));
  }

  function todayIso() {
    var d = new Date();
    var m = d.getMonth() + 1;
    var dayNum = d.getDate();
    return (
      d.getFullYear() +
      "-" +
      (m < 10 ? "0" : "") +
      m +
      "-" +
      (dayNum < 10 ? "0" : "") +
      dayNum
    );
  }

  function addWorkDays(iso, delta) {
    var d = parseISODate(iso);
    if (!d) return "";
    if (!delta) return iso;
    var step = delta > 0 ? 1 : -1;
    var left = Math.abs(delta);
    while (left) {
      d.setDate(d.getDate() + step);
      var day = d.getDay();
      if (day !== 0 && day !== 6) left -= 1;
    }
    var m = d.getMonth() + 1;
    var dayNum = d.getDate();
    return (
      d.getFullYear() +
      "-" +
      (m < 10 ? "0" : "") +
      m +
      "-" +
      (dayNum < 10 ? "0" : "") +
      dayNum
    );
  }

  function formatWorkDate(iso) {
    var d = parseISODate(iso);
    if (!d) return "";
    return WEEKDAYS[d.getDay()] + " " + MONTHS_SHORT[d.getMonth()] + " " + d.getDate();
  }

  function deliveryEvents() {
    return eventsNow().filter(function (ev) {
      return ev.needsDelivery && ev.start;
    });
  }

  function deliveryOffset() {
    return C.deliveryOffset(state.round2 !== false);
  }

  function latestShootForEvent(ev) {
    if (!ev || !ev.start) return "";
    return addWorkDays(ev.start, -deliveryOffset());
  }

  function eventForShootIndex(index) {
    var today = todayIso();
    var events = deliveryEvents().filter(function (ev) {
      var latest = latestShootForEvent(ev);
      return latest && latest >= today;
    });
    if (!events.length) return null;
    if (index >= events.length) return events[events.length - 1];
    return events[index];
  }

  function shootGuard(index, shootDate) {
    var ev = eventForShootIndex(index);
    if (!ev) return null;
    var latest = latestShootForEvent(ev);
    var late = !!(shootDate && latest && shootDate > latest);
    return { event: ev, latest: latest, late: late };
  }

  function relativeWhen(at) {
    if (at === 0) return "Shoot day";
    var abs = Math.abs(at);
    var unit = abs === 1 ? " working day " : " working days ";
    return abs + unit + (at < 0 ? "before" : "after");
  }

  function timelineList(iso) {
    var list = el("div", "time-list");
    C.timelineSteps(state.round2 !== false).forEach(function (step) {
      var row = el("div", "time-row" + (step.at === 0 ? " is-shoot" : ""));
      var when = iso ? formatWorkDate(addWorkDays(iso, step.at)) : relativeWhen(step.at);
      row.appendChild(el("span", "time-when", when));
      var body = el("span", "time-body");
      body.appendChild(el("strong", "", step.label));
      body.appendChild(el("small", "", step.note));
      row.appendChild(body);
      list.appendChild(row);
    });
    return list;
  }

  function timelineBlock() {
    var wrap = el("div", "timeline-block");
    wrap.appendChild(el("p", "map-label", "Delivery timeline"));
    var dated = neededProds().filter(function (prod) {
      return shootRec(prod.id).date;
    });
    if (!dated.length) {
      wrap.appendChild(el("p", "map-note", "Set a shoot date."));
      wrap.appendChild(timelineList(""));
    } else {
      dated.forEach(function (prod) {
        wrap.appendChild(el("p", "time-shoot", shootTitle(prod)));
        wrap.appendChild(timelineList(shootRec(prod.id).date));
      });
    }
    var on = state.round2 !== false;
    var toggle = el("button", "round2-toggle" + (on ? " is-on" : ""));
    toggle.type = "button";
    toggle.setAttribute("aria-pressed", on ? "true" : "false");
    var knob = el("span", "guarantee-knob");
    knob.appendChild(el("b", "", on ? "ON" : "OFF"));
    toggle.appendChild(knob);
    toggle.appendChild(
      el("strong", "", on ? "Round 2 revisions included. +2 working days." : "Round 2 revisions skipped.")
    );
    toggle.addEventListener("click", function () {
      state.round2 = !on;
      persistAndPaint();
    });
    wrap.appendChild(toggle);
    return wrap;
  }

  function dealById(id) {
    for (var i = 0; i < C.DEAL_MODELS.length; i++) {
      if (C.DEAL_MODELS[i].id === id) return C.DEAL_MODELS[i];
    }
    return C.DEAL_MODELS[0];
  }

  function setDeal(id) {
    var model = dealById(id);
    state.deal = model.id;
    if (!model.guarantee) state.lastDeal = model.id;
  }

  function dealBlock() {
    var wrap = el("div", "deal-block");
    wrap.appendChild(el("p", "map-label", "Disclaimer"));
    C.DEAL_MODELS.forEach(function (model) {
      var btn = el("button", "deal-card" + (state.deal === model.id ? " is-on" : ""));
      btn.type = "button";
      btn.appendChild(el("strong", "", model.title));
      btn.addEventListener("click", function () {
        setDeal(model.id);
        persistAndPaint();
      });
      wrap.appendChild(btn);
    });
    var on = dealById(state.deal).guarantee;
    var toggle = el("button", "guarantee-toggle" + (on ? " is-on" : ""));
    toggle.type = "button";
    toggle.setAttribute("aria-pressed", on ? "true" : "false");
    var knob = el("span", "guarantee-knob");
    knob.appendChild(el("b", "", on ? "ON" : "OFF"));
    toggle.appendChild(knob);
    toggle.appendChild(el("strong", "", on ? "We guarantee results." : "No result guarantee."));
    toggle.addEventListener("click", function () {
      setDeal(on ? state.lastDeal || "you-ideas" : "we-own");
      persistAndPaint();
    });
    wrap.appendChild(toggle);
    return wrap;
  }

  function renderBoard() {
    var row = document.getElementById("hexRow");
    row.innerHTML = "";
    row.className = "lands is-single";
    if (state.screen === "ideas") {
      row.appendChild(ideasPage());
      return;
    }
    if (state.screen === "production") {
      row.appendChild(productionPage());
      return;
    }
    if (state.screen === "objective") {
      row.appendChild(objectivePage());
      return;
    }
    if (state.screen === "reports") {
      row.appendChild(reportsPage());
      return;
    }
    var month = monthNow();
    var mix = mixNow();
    var land = el("article", "month month-" + month.id + " is-solo is-map");
    land.appendChild(mixHead());
    var body = el("div", "map-body");
    body.appendChild(shootBlock(mix));
    body.appendChild(oppsFold());
    body.appendChild(timelineBlock());
    body.appendChild(dealBlock());
    land.appendChild(body);
    row.appendChild(land);
  }

  function formatDate(iso) {
    if (!iso) return "";
    var parts = iso.split("-");
    if (parts.length < 3) return iso;
    return monthNow().short + " " + Number(parts[2]);
  }

  function dotChip(kind, item) {
    var n =
      kind === "prod"
        ? ((state.prod[item.id] && state.prod[item.id].ideas) || []).length
        : (state.posted[item.id] || []).length;
    var open = n > 0;
    var btn = el("button", "dot-chip dot-" + kind + (open ? " is-open" : " is-mystery"));
    btn.type = "button";
    var pog = el("span", "dot-pog");
    pog.appendChild(el("span", open ? "dot-ok" : "dot-q", open ? (n > 1 ? String(n) : "✓") : "?"));
    btn.appendChild(pog);
    var side = el("span", "dot-side");
    side.appendChild(el("strong", "", kind === "prod" ? shootTitle(item) : item.title));
    var sub =
        kind === "prod"
          ? (formatDate(shootRec(item.id).date) || "Shoot") +
            " · " +
            n +
            "/" +
            C.IDEAS_PER_SHOOT
          : item.kind === "sale"
            ? "Sale"
            : "Week";
    if (open) sub += " · " + n;
    side.appendChild(el("small", "", sub));
    btn.appendChild(side);
    btn.addEventListener("click", function () {
      state.screen = kind === "prod" ? "prod" : "event";
      state.selected = item.id;
      persistAndPaint();
    });
    return btn;
  }

  function ideasPage() {
    var month = monthNow();
    var page = el("article", "page page-ideas");
    page.appendChild(backBar());
    page.appendChild(el("h2", "", "Content ideas"));
    page.appendChild(el("p", "label", month.label + " · " + ideasNow().length + " from the sheet"));
    page.appendChild(el("p", "map-label", "Content"));
    page.appendChild(contentFilters());
    page.appendChild(monthIdeaList());
    return page;
  }

  function productionChecked(id) {
    return !!(state.productionChecks && state.productionChecks[id]);
  }

  function toggleProductionCheck(id) {
    if (!state.productionChecks) state.productionChecks = {};
    state.productionChecks[id] = !state.productionChecks[id];
  }

  function productionPage() {
    var page = el("article", "page page-production");
    page.appendChild(backBar());
    page.appendChild(el("h2", "", "Production"));
    page.appendChild(el("p", "label", "Halloween social shoot"));
    page.appendChild(
      el("p", "map-note", "What we need on set. Check each item off as it is locked.")
    );
    (C.PRODUCTION_LISTS || []).forEach(function (group) {
      page.appendChild(el("p", "map-label", group.label));
      var rows = (group.items || []).map(function (item) {
        return {
          id: item.id,
          title: item.title,
          note: item.note,
          on: productionChecked(item.id),
          onToggle: function () {
            toggleProductionCheck(item.id);
          },
        };
      });
      page.appendChild(checkList(rows, "prod"));
    });
    return page;
  }

  function objectivePage() {
    var page = el("article", "page page-objective");
    page.appendChild(backBar());
    page.appendChild(el("h2", "", "Objective"));
    page.appendChild(
      el(
        "p",
        "objective-statement",
        "We can't reach a massive non-follower audience if we don't produce content worth commenting or sharing."
      )
    );
    var shot = el("img", "objective-shot");
    shot.src = "objective-comments.png?v=75";
    shot.alt =
      "Why no one writes comments versus why everyone writes in comments: targeting, community, and identity.";
    page.appendChild(shot);
    return page;
  }

  function reportsPage() {
    var page = el("article", "page page-reports");
    page.appendChild(backBar());
    page.appendChild(el("h2", "", "Social reports"));

    var reports = C.REPORTS || [];
    var main = reports[0];
    var earlier = reports.slice(1);

    if (main) {
      page.appendChild(el("p", "map-label", main.label));
      page.appendChild(el("p", "label", main.sub || ""));
      var openMain = el("a", "ref-link ref-link-main", "Open " + main.label + " Recap");
      openMain.href = main.file;
      openMain.target = "_blank";
      openMain.rel = "noopener noreferrer";
      page.appendChild(openMain);
    }

    if (earlier.length) {
      page.appendChild(el("p", "label report-prev-label", "Previous months"));
      var row = el("div", "report-btn-row");
      earlier.forEach(function (r) {
        var btn = el("a", "report-btn-sm", r.label.replace(" 2026", ""));
        btn.href = r.file;
        btn.target = "_blank";
        btn.rel = "noopener noreferrer";
        row.appendChild(btn);
      });
      page.appendChild(row);
    }

    return page;
  }

  function prodPage() {
    var prod = findProd(state.selected);
    var page = el("article", "page page-prod");
    page.appendChild(backBar());
    if (!prod) {
      page.appendChild(el("p", "", "No shoot."));
      return page;
    }
    var rec = prodRec(prod.id);
    page.appendChild(el("h2", "", shootTitle(prod)));
    var when = formatDate(shootRec(prod.id).date);
    if (when) page.appendChild(el("p", "label", when + " · " + rec.ideas.length + "/" + C.IDEAS_PER_SHOOT));
    var legend = el("div", "pillar-row");
    C.PILLARS.forEach(function (p) {
      var chip = pillarChip(p.id);
      chip.textContent = p.name;
      legend.appendChild(chip);
    });
    page.appendChild(legend);
    var rows = [];
    rec.ideas.map(findIdea).filter(Boolean).forEach(function (idea) {
      rows.push(
        Object.assign(ideaTicketFields(idea), {
          id: idea.id,
          title: idea.title,
          on: true,
          onToggle: function () {
            returnToPool(idea.id);
          },
        })
      );
    });
    poolIdeas().forEach(function (idea) {
      rows.push(
        Object.assign(ideaTicketFields(idea), {
          id: idea.id,
          title: idea.title,
          on: false,
          onToggle: function () {
            moveToProd(idea.id, prod.id);
          },
        })
      );
    });
    page.appendChild(checkList(rows, "prod"));
    return page;
  }

  function eventPage() {
    var ev = findEvent(state.selected);
    var page = el("article", "page page-post");
    page.appendChild(backBar());
    if (!ev) {
      goBoard();
      return page;
    }
    var list = postedFor(ev.id);
    page.appendChild(el("h2", "", ev.title));
    if (ev.when) page.appendChild(el("p", "label", ev.when));
    var rows = [];
    list.map(findIdea).filter(Boolean).forEach(function (idea) {
      rows.push(
        Object.assign(ideaTicketFields(idea), {
          id: idea.id,
          title: idea.title,
          on: true,
          owner: ownerOf(idea.id),
          onToggle: function () {
            var shootId = shootForReturn(idea.id);
            if (shootId) moveToProd(idea.id, shootId);
            else returnToPool(idea.id);
          },
        })
      );
    });
    unlockedIdeas().forEach(function (idea) {
      rows.push(
        Object.assign(ideaTicketFields(idea), {
          id: idea.id,
          title: idea.title,
          note: "From shoot",
          on: false,
          onToggle: function () {
            moveToEvent(idea.id, ev.id);
          },
        })
      );
    });
    page.appendChild(checkList(rows, "post"));
    return page;
  }

  function persistAndPaint() {
    save();
    paint();
  }

  function paint() {
    var leftover = document.getElementById("mixPop");
    if (leftover) leftover.remove();
    renderMonths();
    renderLegend();
    renderPlanCount();
    renderBoard();
  }

  function setMonth(id) {
    state.month = id;
    state.screen = "board";
    state.selected = null;
    state.filterPillar = null;
    state.focusShoot = null;
    state.focusOpp = null;
    state.focusKind = null;
    state.popup = null;
    syncShootsToPace();
    persistAndPaint();
  }

  document.getElementById("viewShoots").addEventListener("click", function () {
    setMonth("oct");
  });
  document.getElementById("viewIdeas").addEventListener("click", function () {
    goIdeas();
  });
  document.getElementById("viewProduction").addEventListener("click", function () {
    goProduction();
  });
  document.getElementById("viewObjective").addEventListener("click", function () {
    goObjective();
  });
  document.getElementById("viewReports").addEventListener("click", function () {
    goReports();
  });
  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape" && state.screen !== "board") goBoard();
  });

  load();
  syncShootsToPace();
  paint();
  if (C.loadSheet) {
    C.loadSheet(function () {
      paint();
    });
  }
})();
