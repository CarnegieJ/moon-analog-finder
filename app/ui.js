/* Moon Analog Finder: one window. Map is the stage, the left rail lists choices, the right panel opens on selection,
   popovers hold options. Layout, navigation and focus only; every number on screen is produced by app.js. */
const UI = {
  step: 1, mode: "moon", tab: "match", ready: false, open: null, opener: null, popTrig: null, picking: false, cmpOpen: false, toastT: 0,
  init() {
    document.querySelectorAll("[data-step]").forEach(b => b.onclick = () => UI.go(+b.dataset.step));
    document.querySelectorAll("[data-pop]").forEach(b => b.onclick = e => { e.stopPropagation(); UI.pop($(b.dataset.pop).hidden ? b.dataset.pop : null, b); });
    document.querySelectorAll("[data-close]").forEach(b => b.onclick = () => UI.close());
    document.querySelectorAll("[data-sheet]").forEach(b => b.onclick = () => { $("app").classList.toggle("tall"); requestAnimationFrame(() => UI.fit()); });
    document.querySelectorAll(".pop").forEach(p => p.addEventListener("focusout", e => { const t = e.relatedTarget; if (t && !p.contains(t) && t !== UI.popTrig && !p.hidden) UI.pop(null); }));
    /* tabs: click, and arrow keys between them (ARIA tabs pattern) */
    const tabs = [...document.querySelectorAll(".tabs [role=tab]")];
    tabs.forEach((b, i) => { b.onclick = () => UI.tabTo(b.dataset.tab); b.onkeydown = e => { const d = {ArrowRight: 1, ArrowLeft: -1}[e.key]; if (e.key == "Home" || e.key == "End" || d) { e.preventDefault(); const n = e.key == "Home" ? 0 : e.key == "End" ? tabs.length - 1 : (i + d + tabs.length) % tabs.length; UI.tabTo(tabs[n].dataset.tab); tabs[n].focus(); } }; });
    /* lists: arrow keys move between rows (listbox pattern); the container says which children are rows */
    document.addEventListener("keydown", e => { const c = e.target.closest && e.target.closest("[data-roving]"); if (!c || !["ArrowDown", "ArrowUp", "Home", "End"].includes(e.key)) return;
      const rows = [...c.querySelectorAll(c.dataset.roving)].filter(r => r.offsetParent), i = rows.indexOf(e.target.closest(c.dataset.roving)); if (i < 0) return; e.preventDefault();
      const n = e.key == "Home" ? 0 : e.key == "End" ? rows.length - 1 : Math.max(0, Math.min(rows.length - 1, i + (e.key == "ArrowDown" ? 1 : -1)));
      rows.forEach(r => r.tabIndex = -1); rows[n].tabIndex = 0; rows[n].focus(); });
    document.addEventListener("click", e => { if (!e.target.closest(".pop") && !UI.picking) UI.pop(null); });
    $("ctaEarth").onclick = () => UI.go(3);
    $("howBtn").onclick = () => UI.help(true);
    $("closeHow").onclick = $("scrim").onclick = () => UI.help(false);
    $("drawer").addEventListener("keydown", e => { if (e.key != "Tab") return; const f = [...$("drawer").querySelectorAll("button,a[href],summary,[tabindex='0']")]; if (!f.length) return;
      const a = f[0], z = f[f.length - 1]; if (e.shiftKey && document.activeElement === a) { e.preventDefault(); z.focus(); } else if (!e.shiftKey && document.activeElement === z) { e.preventDefault(); a.focus(); } });
    $("cmp").addEventListener("keydown", e => { if (e.key != "Tab") return; const f = [...$("cmp").querySelectorAll("button,input")].filter(x => x.offsetParent), a = f[0], z = f[f.length - 1];
      if (e.shiftKey && document.activeElement === a) { e.preventDefault(); z.focus(); } else if (!e.shiftKey && document.activeElement === z) { e.preventDefault(); a.focus(); } });
    $("expandBtn").onclick = () => UI.compare(true); $("cmpClose").onclick = () => UI.compare(false);
    document.addEventListener("keydown", e => { if (e.key != "Escape") return;
      if ($("app").classList.contains("help")) UI.help(false); else if (UI.cmpOpen) UI.compare(false); else if (UI.picking) UI.pick(false);
      else if (!UI.pop(null) && UI.open) UI.close(); });
    window.addEventListener("resize", () => UI.fit());
    UI.ready = true; UI.go(1);
  },
  /* 1 Moon map with the spot panel, 2 test menu, 3 Earth map and list, 4 Earth map with the site panel */
  go(n, shut, focus) {
    if (n == 2) { UI.pop("testPop", $("lnk2")); return; }
    if (n == 4 && focus) UI.opener = document.activeElement;
    UI.step = n; UI.mode = n == 1 ? "moon" : "earth"; UI.pop(null); if (n != 1) UI.hint(false);
    UI.panel(shut ? null : n == 1 ? (S.spot ? "spot" : null) : n == 4 ? "site" : null);
    $("app").dataset.mode = UI.mode;
    document.querySelectorAll(".chain [data-step]").forEach(b => { const on = (+b.dataset.step == 1) == (UI.mode == "moon"); b.classList.toggle("on", on); on ? b.setAttribute("aria-current", "page") : b.removeAttribute("aria-current"); });
    requestAnimationFrame(() => { UI.fit(); if (n == 4 && focus) $("siteTitle").focus({preventScroll: true}); });
  },
  close() { const back = UI.opener; UI.go(UI.mode == "moon" ? 1 : 3, true); if (back && document.contains(back) && back.offsetParent) back.focus(); else $(UI.mode == "moon" ? "lnk1" : "lnk3").focus(); UI.opener = null; },
  panel(which) { UI.open = which; $("app").dataset.panel = which || ""; $("pSpot").inert = which != "spot"; $("pSite").inert = which != "site"; markPins(); writeHash(); requestAnimationFrame(() => UI.fit()); },
  pop(id, trig) {
    let was = false;
    document.querySelectorAll(".pop").forEach(p => { if (!p.hidden) was = true; p.hidden = p.id != id; });
    document.querySelectorAll("[data-pop]").forEach(b => b.setAttribute("aria-expanded", b.dataset.pop == id));
    if (id) { UI.popTrig = trig || document.querySelector(`[data-pop=${id}]`); const p = $(id), f = p.querySelector("button.p.on,.lrow.on,input:not(:disabled),select,button:not(:disabled)"); if (f) requestAnimationFrame(() => f.focus({preventScroll: true})); }
    else if (was && UI.popTrig && document.activeElement && (document.activeElement === document.body || document.activeElement.closest(".pop"))) UI.popTrig.focus();
    return was && !id;
  },
  help(on) {
    UI.pop(null); $("app").classList.toggle("help", on);
    for (const el of [document.querySelector(".top"), document.querySelector(".work"), $("testPop")]) el.inert = on;
    (on ? $("closeHow") : $("howBtn")).focus();
  },
  /* Maps and 3D views are measured by their libraries, so re-measure whenever the layout changes. */
  fit() {
    if (!UI.ready) return;
    if (moonMap) moonMap.invalidateSize();
    if (earthMap) { earthMap.invalidateSize(); if (UI.mode == "earth" && !UI.seen3) { UI.seen3 = true; earthMap.fitBounds([[-60, -170], [84, 175]]); } }
    if (UI.open == "site" || UI.cmpOpen) { render3d(); if (satMap) satMap.invalidateSize(); }
    if (UI.open == "site" && UI.mode == "earth") showPin();
  },
  tabTo(t) {
    UI.tab = t;
    document.querySelectorAll(".tabs button").forEach(b => { const on = b.dataset.tab == t; b.classList.toggle("on", on); b.setAttribute("aria-selected", on); b.tabIndex = on ? 0 : -1; });
    document.querySelectorAll(".tab").forEach(p => p.classList.toggle("on", p.id == "tab-" + t));
    if (t == "sat" && S.site != null) showSat(S.site);
    requestAnimationFrame(() => UI.fit());
  },
  busy(on) { $("progress").hidden = !on; $("leftEarth").setAttribute("aria-busy", on); },
  toast(msg, ms = 3200) { const t = $("toast"); clearTimeout(UI.toastT); t.textContent = msg; t.hidden = !msg; if (msg && ms) UI.toastT = setTimeout(() => t.hidden = true, ms); },
  hint(on) { $("hint").hidden = !on; },
  /* Pick a point on the Earth map for the distance filter. */
  pick(on) {
    UI.picking = on; $("app").classList.toggle("picking", on);
    if (on) { UI.pop(null); UI.toast("Click a point on the map for the search circle. Esc cancels.", 0); earthMap.once("click", e => { if (!UI.picking) return; const ll = e.latlng.wrap(); $("fLat").value = ll.lat.toFixed(2); $("fLon").value = ll.lng.toFixed(2); UI.pick(false); setTimeout(() => { UI.pop("filterPop", $("filterBtn")); $("fKm").focus(); }, 0); }); }
    else { UI.toast(""); earthMap.off("click"); }
  },
  /* Compare overlay: the same two canvases move into a full-stage view, side by side, and move back on close. */
  compare(on) {
    if (on == UI.cmpOpen) return; UI.cmpOpen = on; $("cmp").hidden = !on;
    const move = (id, to) => { to.appendChild($(id)); };
    if (on) { move("c3m", $("cmpM")); move("cvsM", $("cmpM")); move("c3e", $("cmpE")); move("cvsE", $("cmpE")); syncCmp(); for (const el of [document.querySelector(".top"), document.querySelector(".work")]) el.inert = true; $("cmpClose").focus(); }
    else { move("c3m", $("slotM")); move("cvsM", $("slotM")); move("c3e", $("slotE")); move("cvsE", $("slotE")); for (const el of [document.querySelector(".top"), document.querySelector(".work")]) el.inert = false; $("expandBtn").focus(); }
    requestAnimationFrame(() => render3d());
  },
  onSpot(title) { $("st1").textContent = title; if (UI.ready && UI.mode == "moon") UI.panel("spot"); },
  onPurpose() { $("st2").textContent = PURPOSES[S.purpose].name; $("customTag").hidden = !isCustom(S.purpose); },
  onLayers() { const n = document.querySelectorAll("#layers .on").length; $("layN").textContent = n || ""; },
  afterRun() {
    $("st3").textContent = topSites.length ? `${topSites.length} sites` : "no sites";
    document.querySelectorAll("#ranked tr.site:not(.probe)").forEach((tr, r) => { const mk = earthMarkers[r]; if (!mk) return;
      tr.onmouseenter = tr.onfocus = () => { if (topSites[r] === S.site && UI.open == "site") return; mk.setStyle({weight: 4, fillOpacity: .95}); mk.bringToFront(); }; tr.onmouseleave = tr.onblur = () => markPins();
      mk.on("mouseover", () => tr.classList.add("hot")); mk.on("mouseout", () => tr.classList.remove("hot")); });
  }
};
