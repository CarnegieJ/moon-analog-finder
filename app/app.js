/* Moon Analog Finder. Scores come from the server (3.8 million overlapping Earth squares) or, if it cannot be reached, from the built-in
   library scored in the browser. All numbers on screen come from the data files and the code below. */
const $ = id => document.getElementById(id), f1 = v => v.toFixed(1), f2 = v => v.toFixed(2), pc = v => Math.round(v * 100) + "%";
const esc = s => String(s).replace(/[&<>"]/g, c => ({"&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;"}[c]));
const BINS = 46, T_RANGE = 200, DARK_H = 120, H_RANGE = 0.4, RET_RANGE = 0.5;
const FACT = {slope: "Slope match", classes: "Steep ground share (10 and 20 deg)", scale: "Roughness across scales", lowsun: "Low sun angle", dark: "Long darkness", t_cold: "Cold", t_peak: "Peak temperature", frozen: "Frozen ground", bare: "Bare surface"};
const PURPOSES = {
  mobility: {name: "Rover driving", desc: "Same steepness and same kind of terrain, on bare ground", gate: true, w: {slope: .5, scale: .5}},
  shadow: {name: "Shadow work and crater access", desc: "Steep access, low sun and cold. Mostly set by Earth latitude", gate: true, w: {classes: .35, lowsun: .35, t_cold: .30}},
  darkness: {name: "Power and darkness survival", desc: "Long darkness and cold on Earth. Does not depend on the lunar spot", gate: false, w: {dark: .45, t_cold: .35, lowsun: .20}},
  ice: {name: "Ice drilling and digging", desc: "Ground frozen all year, cold, and similar slopes. An analog for digging frozen ground, not for lunar ice itself", gate: "bare", w: {frozen: .5, t_cold: .3, slope: .2}}
};
const W0 = JSON.parse(JSON.stringify(Object.fromEntries(Object.entries(PURPOSES).map(([k, v]) => [k, v.w]))));
const PUI = {
  mobility: {cmp: "Spread of slopes and roughness from 80 m to 320 m, on bare ground", cant: "Rocks, soil strength and dust. Nothing smaller than 80 m"},
  shadow: {cmp: "Share of steep ground, low sun angle and cold", cant: "Real permanent shadow or lunar cold. Earth is far warmer, and the ranking mostly follows latitude"},
  darkness: {cmp: "Length of darkness, cold and low sun on Earth", cant: "Anything about the lunar spot you picked. The ranking follows Earth latitude"},
  ice: {cmp: "Ground frozen all year, cold and similar slopes", cant: "Lunar ice itself. Earth permafrost is frozen soil near 260 K. No permafrost data south of 60° S"}
};
const S = {purpose: "mobility", spot: null, site: null, col: "slope", rot: {x: -1.05, z: 0.6}, flt: {country: "", near: null, alt: null, newOnly: false}, probe: null, probeNew: false, keep: null};
let PL = null, PN = null, satMap = null, satRect = null, satErr = false;
const WELD = "https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/Landsat_WELD_CorrectedReflectance_TrueColor_Global_Annual/default/2000-12-01/GoogleMapsCompatible_Level12/{z}/{y}/{x}.jpeg";
const earthLabel = j => `${place(j) && place(j).country ? place(j).country + ", " : ""}${coord(j)}`;
let MAN, E, M, DEM, moonMap, earthMap, spotRect, earthMarkers = [], probeMk = null, nearCircle = null, knownLayer = null, scores = null, topSites = [], INF = null, regionMk = {};

const DATA_V = "16";  // bump whenever files in data/ or layers/ change, so browsers do not reuse old copies
async function bin(u, T) { const r = await fetch(u + "?v=" + DATA_V); if (!r.ok) throw new Error(u + " " + r.status); return new T(await r.arrayBuffer()); }
async function init() {
  MAN = await (await fetch("data/manifest.json?v=" + DATA_V, {cache: "no-cache"})).json();
  const [eh, em, mh, mm, dem] = await Promise.all([bin("data/earth_hist16.bin", Uint16Array), bin("data/earth_meta.bin", Float32Array),
    bin("data/moon_hist16.bin", Uint16Array), bin("data/moon_meta.bin", Float32Array), bin("data/moon_dem400.bin", Int16Array)]);
  E = {n: MAN.earth.n, hs: 10000, hist: eh, meta: em, nc: MAN.earth.cols.length, c: Object.fromEntries(MAN.earth.cols.map((k, i) => [k, i]))};
  M = {n: MAN.moon.n, hist: mh, meta: mm, nc: MAN.moon.cols.length, c: Object.fromEntries(MAN.moon.cols.map((k, i) => [k, i])), idx: new Map()};
  for (let i = 0; i < M.n; i++) M.idx.set(mv(i, "x") + "," + mv(i, "y"), i);
  DEM = dem;
  try { PL = await bin("data/earth_place.bin", Uint16Array); PN = await (await fetch("data/places.json?v=" + DATA_V)).json(); } catch (e) { PL = null; }
  EL = E; PLL = PL; PNL = PN;
  MAN.regions.forEach(r => { r.kind = r.kind || (/lander/i.test(r.name) ? "lander" : "artemis"); });
  libInfo(null);
  buildMoonMap(); buildEarthMap(); init3d(); initSun(); initForms(); UI.init(); fillCountries(null);
  const h = readHash();
  if (h) applyHash(h);
  else { const d = MAN.regions.find(r => r.name == "Malapert Massif") || MAN.regions[0]; selectSpot(d.x, d.y, d.name); UI.hint(true); }
}
const mv = (i, k) => M.meta[i * M.nc + M.c[k]], ev = (i, k) => E.meta[i * E.nc + E.c[k]];
const regionAt = (gx, gy) => { const r = MAN.regions.find(r => Math.round(r.x / 5000) * 5000 == gx && Math.round(r.y / 5000) * 5000 == gy); return r ? r.name : null; };

/* ---------- Moon map ---------- */
const LEG = {slope: ["0°", "35°", "#000004,#51127c,#b73779,#fc8961,#fcfdbf"], sunlight: ["never lit", "lit 60% of the time", "#000004,#56106e,#bb3754,#f98c0a,#fcffa4"], shadow: ["", "permanently shadowed", "#c6dbef,#2171b5"], temperature: ["40 K", "320 K", "#30123b,#28bbec,#a4fc3c,#fb7e21,#7a0403"], testability: ["0.5", "0.95 best Earth terrain match", "#a50026,#fdae61,#ffffbf,#a6d96a,#006837"]};
function buildMoonMap() {
  const B = [[-304, -304], [304, 304]];
  moonMap = L.map("moonmap", {crs: L.CRS.Simple, minZoom: -0.5, maxZoom: 4, zoomSnap: 0.5, attributionControl: false, maxBounds: [[-340, -340], [340, 340]]});
  L.imageOverlay("layers/base.png?v=" + DATA_V, B).addTo(moonMap); moonMap.fitBounds([[-160, -160], [160, 160]]);
  const legend = () => { $("legend").innerHTML = Object.keys(lay).filter(k => moonMap.hasLayer(lay[k])).map(k => `<span class="leg"><span>${LEG[k][0]}</span><i style="background:linear-gradient(90deg,${LEG[k][2]})"></i><span>${LEG[k][1]}</span></span>`).join(""); };
  const defs = [["slope", "Slope"], ["sunlight", "Average sunlight"], ["shadow", "Permanent shadow"], ["temperature", "Peak temperature"], ["testability", "Earth match (rover terrain)"]], lay = {};
  defs.forEach(([k, label]) => {
    lay[k] = L.imageOverlay(`layers/${k}.png?v=${DATA_V}`, k == "testability" ? [[-305, -305], [305, 305]] : B, {opacity: 0.85});
    const b = document.createElement("button"); b.className = "lrow"; b.setAttribute("aria-pressed", "false");
    b.innerHTML = `<i style="background:linear-gradient(90deg,${LEG[k][2]})"></i><span>${label}<small>${[LEG[k][0], LEG[k][1]].filter(Boolean).join(" to ")}</small></span>`;
    b.onclick = () => { const on = moonMap.hasLayer(lay[k]); on ? moonMap.removeLayer(lay[k]) : lay[k].addTo(moonMap); b.classList.toggle("on", !on); b.setAttribute("aria-pressed", !on); if (spotRect) spotRect.bringToFront(); legend(); UI.onLayers(); };
    $("layers").appendChild(b);
  });
  L.circleMarker([0, 0], {radius: 3, color: "#fff"}).addTo(moonMap).bindTooltip("South Pole");
  MAN.regions.forEach(r => {
    const tip = r.name + (r.cited ? "" : " (approx.)"), go = e => { L.DomEvent.stop(e); selectSpot(r.x, r.y, r.name, {user: true}); };
    regionMk[r.name] = (r.kind == "lander" ? L.marker([r.y / 1000, r.x / 1000], {icon: L.divIcon({className: "", html: '<div class="lander"></div>', iconSize: [14, 12], iconAnchor: [7, 6]}), keyboard: false})
      : L.circleMarker([r.y / 1000, r.x / 1000], {radius: 6, color: "#8CC8F5", weight: 2, fillOpacity: .2})).addTo(moonMap).bindTooltip(tip).on("click", go);
  });
  moonMap.on("click", e => selectSpot(e.latlng.lng * 1000, e.latlng.lat * 1000, null, {user: true}));
}
function selectSpot(x, y, name, o = {}) {
  const gx = Math.round(x / 5000) * 5000, gy = Math.round(y / 5000) * 5000, i = M.idx.get(gx + "," + gy);
  if (i === undefined) { if (o.user) UI.toast("No data here. The map covers 80 to 90° S."); else $("coordMsg").textContent = "No data at that point. The map covers 80 to 90 degrees south."; return false; }
  $("coordMsg").textContent = ""; if (o.user) UI.hint(false);
  const changed = !S.spot || S.spot.i !== i;
  S.spot = {i, x: gx, y: gy, name: name || regionAt(gx, gy)};
  if (changed) { S.site = null; if (!o.keep) S.keep = null; if (UI.open == "site") UI.panel(UI.mode == "moon" ? "spot" : null); }
  if (spotRect) moonMap.removeLayer(spotRect);
  spotRect = L.rectangle([[gy / 1000 - 5, gx / 1000 - 5], [gy / 1000 + 5, gx / 1000 + 5]], {color: "#ffffff", weight: 2, fill: false, interactive: false}).addTo(moonMap);
  renderSpot(); if (changed) { OUT = null; buildPurposes(); scheduleOutlook(); run(); sunMoon(); }
  return true;
}
function goCoord() {
  const la = parseFloat($("inLat").value), lo = parseFloat($("inLon").value);
  if (!(la <= -80 && la >= -90) || isNaN(lo)) { $("coordMsg").textContent = "Enter a latitude from -90 to -80 and a longitude in degrees east."; return; }
  const r = 2 * 1737400 * Math.tan((90 + la) * Math.PI / 360), x = r * Math.sin(lo * Math.PI / 180), y = r * Math.cos(lo * Math.PI / 180);
  if (selectSpot(x, y, null, {user: true})) moonMap.panTo([y / 1000, x / 1000]);
}
function lonTxt(l) { return Math.abs(l).toFixed(1) + "° " + (l >= 0 ? "E" : "W"); }
function renderRegions() {
  const tk = (v, u) => isNaN(v) ? "no data" : v.toFixed(0) + u;
  const rowOf = (r, q) => { const ri = M.idx.get(Math.round(r.x / 5000) * 5000 + "," + Math.round(r.y / 5000) * 5000); if (ri === undefined) return ""; const v = k => mv(ri, k), on = S.spot && S.spot.i === ri;
    return `<button class="row${on ? " on" : ""}" data-r="${q}" aria-pressed="${on}" tabindex="-1"><span class="rn">${esc(r.name)}${v("psr_share") > 0.5 ? '<i class="tag possible">permanent shadow</i>' : ""}</span><span class="rm">${f1(v("slope_p50"))}° slope · ${pc(v("illum_mean"))} sunlit · ${tk(v("t_avg"), " K")}</span></button>`; };
  const art = MAN.regions.map((r, q) => r.kind == "artemis" ? rowOf(r, q) : "").join(""), land = MAN.regions.map((r, q) => r.kind == "lander" ? rowOf(r, q) : "").join("");
  $("regions").innerHTML = art; $("landers").innerHTML = land; $("landWrap").hidden = !land;
  for (const box of [$("regions"), $("landers")]) { const rows = box.querySelectorAll(".row"); if (rows.length) (box.querySelector(".row.on") || rows[0]).tabIndex = 0;
    rows.forEach(b => b.onclick = () => { const r = MAN.regions[+b.dataset.r]; if (selectSpot(r.x, r.y, r.name, {user: true})) { moonMap.panTo([r.y / 1000, r.x / 1000]); UI.panel("spot"); } }); }
  for (const r of MAN.regions) { const mk = regionMk[r.name], on = S.spot && S.spot.name == r.name; if (!mk) continue;
    if (mk.setStyle) mk.setStyle({fillOpacity: on ? .9 : .2, weight: on ? 3 : 2}); else if (mk.getElement()) mk.getElement().firstChild.classList.toggle("on", !!on); }
}
function renderSpot() {
  const i = S.spot.i, g = k => mv(i, k), psr = g("psr_share"), tk = (v, u) => isNaN(v) ? "no data" : v.toFixed(0) + u;
  const near = MAN.regions.map(r => ({r, d: Math.hypot(r.x - S.spot.x, r.y - S.spot.y) / 1000})).sort((a, b) => a.d - b.d)[0];
  const art = MAN.regions.filter(r => r.kind == "artemis"), nearA = art.map(r => ({r, d: Math.hypot(r.x - S.spot.x, r.y - S.spot.y) / 1000})).sort((a, b) => a.d - b.d)[0];
  const title = S.spot.name || (near.d < 12 ? `Near ${near.r.name}` : "Unnamed spot");
  let flags = "";
  if (psr > 0.5) flags += `<div class="flag">Mostly permanent shadow (${pc(psr)}). Not a landing spot; relevant for shadow work and ice prospecting.</div>`;
  else if (g("illum_max") > 0.6) flags += `<div class="flag ok">Has well-lit ground: best point is sunlit ${pc(g("illum_max"))} of the time.</div>`;
  if (!S.spot.name && nearA && nearA.d >= 12) flags += `<div class="flag ok">${art.length >= 9 ? "Not one of the nine candidate landing regions NASA named in 2024." : "Not within 12 km of a named region on this map."} Scored from the same data as the named ones. Nearest named region: ${esc(nearA.r.name)}, ${nearA.d.toFixed(0)} km away.</div>`;
  const h = histOf(M.hist, i), c = classes(h);
  renderRegions();
  $("spot").innerHTML = `<div class="eyebrow">Lunar spot</div><h2 tabindex="-1">${esc(title)}</h2>
   <div class="mut small">${Math.abs(g("lat")).toFixed(2)}° S, ${lonTxt(g("lon"))} · 10 km window${S.spot.name ? (MAN.regions.find(r => r.name == S.spot.name && r.cited) ? " · coordinates from NASA" : " · centre approximate") : ""}</div>
   <div class="stats"><div><b>${f1(g("slope_p50"))}°</b><span>median slope</span></div><div><b>${pc(g("illum_mean"))}</b><span>average sunlight</span></div><div><b>${pc(psr)}</b><span>permanent shadow</span></div><div><b>${tk(g("t_avg"), " K")}</b><span>average temperature</span></div></div>${flags}
   <details class="more"><summary>All numbers</summary><div class="kv"><span>Steepest tenth of ground</span><span>over ${f1(g("slope_p90"))}°</span>
   <span>Ground under 5° / 5 to 10°</span><span>${pc(c[0])} / ${pc(c[1])}</span><span>Ground 10 to 20° / over 20°</span><span>${pc(c[2])} / ${pc(c[3])}</span>
   <span>Slope at 320 m / scaling number</span><span>${f1(g("slope320_p50"))}° / ${f2(g("hurst"))}</span><span>Height range</span><span>${g("relief_m").toFixed(0)} m</span>
   <span>Ground with stable ice (Diviner model)</span><span>${pc(g("ice_share") || 0)}</span>
   <span>Peak temperature</span><span>${tk(g("t_max"), " K")}</span><span>Highest sun angle</span><span>${f1(90 - Math.abs(g("lat")) + 1.54)}°</span></div></details>`;
  $("capM").innerHTML = `<i class="mdot"></i>Moon: ${esc(title)}`;
  UI.onSpot(title);
}

/* ---------- scoring ---------- */
function histOf(H, i) { const o = new Float32Array(BINS); for (let b = 0; b < BINS; b++) o[b] = H[i * BINS + b] / 10000; return o; }   // lunar slope charts are stored at full precision
function classes(h) { const c = [0, 0, 0, 0]; for (let b = 0; b < BINS; b++) c[b < 5 ? 0 : b < 10 ? 1 : b < 20 ? 2 : 3] += h[b]; return c; }
const clip = v => v < 0 ? 0 : v > 1 ? 1 : v, rat = (a, b) => 1 - Math.abs(a - b) / Math.max(a, b, 1e-9);
function foms(j, m) {
  let d = 0, c = [0, 0, 0, 0];
  for (let b = 0; b < BINS; b++) { const v = E.hist[j * BINS + b] / (E.hs || 255); d += Math.abs(v - m.h[b]); c[b < 5 ? 0 : b < 10 ? 1 : b < 20 ? 2 : 3] += v; }
  const dc = Math.abs(c[0] - m.c[0]) + Math.abs(c[1] - m.c[1]) + Math.abs(c[2] - m.c[2]) + Math.abs(c[3] - m.c[3]);
  const nd = ev(j, "ndvi"), tn = ev(j, "t_night_min"), td = ev(j, "t_day_max"), pz = ev(j, "pzi") || 0, ic = m.ice || 0;
  return {slope: clip(1 - 0.5 * d), classes: clip(1 - 0.5 * dc), scale: 0.5 * (clip(1 - Math.abs(ev(j, "hurst") - m.H) / H_RANGE) + clip(1 - Math.abs(ev(j, "slope320_p50") / Math.max(ev(j, "slope_p50"), 1e-6) - m.ret) / RET_RANGE)),
    bare: isNaN(nd) ? 1 : clip(1 - (nd - 0.2) / 0.4), reliable: ev(j, "slope_p50") >= 1 ? 1 : 0, lowsun: clip(ev(j, "lowsun")), frozen: Math.max(pz, ic) > 0 ? Math.min(pz, ic) / Math.max(pz, ic) : 0, dark: clip(ev(j, "dark_h") / DARK_H),
    t_cold: isNaN(tn) || isNaN(m.tavg) ? 0 : clip(1 - Math.abs(tn - m.tavg) / T_RANGE), t_peak: isNaN(td) || isNaN(m.tmax) ? 0 : clip(1 - Math.abs(td - m.tmax) / T_RANGE)};
}
function afom(f, p) { let s = 0; for (const k in p.w) s += f[k] * p.w[k]; return p.gate == "bare" ? s * f.bare : p.gate ? s * f.bare * f.reliable : s; }
/* Lunar side of the placement question: the 8 lunar grid squares around the chosen one (5 km away, half overlapping). */
function moonNear() { const out = []; for (let dx = -1; dx <= 1; dx++) for (let dy = -1; dy <= 1; dy++) { if (!dx && !dy) continue; const i = M.idx.get((S.spot.x + dx * 5000) + "," + (S.spot.y + dy * 5000)); if (i !== undefined) out.push(moonRef(i)); } return out; }
function nearRange(j, near) { let lo = 1, hi = 0; for (const mm of near) { const f = foms(j, mm), t = (0.5 * f.slope + 0.5 * f.scale) * f.bare * f.reliable; if (t < lo) lo = t; if (t > hi) hi = t; } return near.length ? [lo, hi] : null; }
function moonRef(i = S.spot.i) { const h = histOf(M.hist, i); return {h, c: classes(h), H: mv(i, "hurst"), ret: mv(i, "slope320_p50") / Math.max(mv(i, "slope_p50"), 1e-6), tavg: mv(i, "t_avg"), tmax: mv(i, "t_max"), ice: mv(i, "ice_share")}; }
/* Reading a terrain score, from the identity test on 2,629 lunar squares (pipeline/identity_test.py, docs/BENCHMARK.md):
   two halves of the same lunar terrain score 0.91 (median); two unrelated lunar squares score 0.74 (median); 9% of unrelated pairs reach 0.87 and 31% reach 0.80.
   Uncertainty of one score: square placement 0.06, which pixels are sampled 0.03, elevation data source 0.02; combined about 0.07. */
const CAL = {strong: 0.87, possible: 0.80, same: 0.91, unrelated: 0.74, err: 0.07};
const level = t => t >= CAL.strong ? {k: "strong", name: "same kind of terrain", cls: "ok"} : t >= CAL.possible ? {k: "possible", name: "possible match", cls: ""} : {k: "none", name: "no match", cls: "bad"};
const terrOf = (j, m) => { if (RS) return RS.terr[j]; const f = foms(j, m); return (0.5 * f.slope + 0.5 * f.scale) * f.bare * f.reliable; };
function calBar(t, er = CAL.err) { const x = v => ((v - 0.5) / 0.5 * 100).toFixed(1), c = Math.max(0.5, Math.min(1, t));
  return `<div class="cal"><i style="left:0;width:${x(CAL.possible)}%;background:#3b1d1d"></i><i style="left:${x(CAL.possible)}%;width:${(x(CAL.strong) - x(CAL.possible)).toFixed(1)}%;background:#3a3312"></i><i style="left:${x(CAL.strong)}%;right:0;background:#143524"></i>
    <b style="left:${x(Math.max(0.5, c - er))}%;width:${(x(Math.min(1, c + er)) - x(Math.max(0.5, c - er))).toFixed(1)}%"></b><u style="left:${x(c)}%"></u><s style="left:${x(CAL.unrelated)}%">unrelated terrain 0.74</s><s style="left:${x(CAL.same)}%">same terrain 0.91</s></div>`; }
function nearKnown(lat, lon) { let best = null, bd = 55; for (const k of MAN.known) { const d = kmBetween(lat, lon, k.lat, k.lon); if (d < bd) { bd = d; best = k.name; } } return best; }   // nearest known analog site within 55 km

/* Outlook per test for the chosen lunar spot, counted on the built-in library with the same foms and afom as the ranking. */
let OUT = null, outTok = 0;
function scheduleOutlook() { const tok = ++outTok; (window.requestIdleCallback || (f => setTimeout(f, 60)))(() => { if (tok !== outTok || !S.spot) return; OUT = computeOutlook(); buildPurposes(); }, {timeout: 1000}); }
function computeOutlook() {
  const m = moonRef(), keep = E, keys = Object.keys(PURPOSES), o = {lib: EL.n}; keys.forEach(k => o[k] = {best: 0, n: 0, poss: 0});
  E = EL;
  try { for (let j = 0; j < E.n; j++) { const f = foms(j, m); for (const k of keys) { const s = afom(f, PURPOSES[k]), q = o[k]; if (s > q.best) q.best = s;
    if (k == "mobility") { if (s >= CAL.strong) q.n++; else if (s >= CAL.possible) q.poss++; } else if (s >= CAL.possible) q.n++; } } }
  finally { E = keep; }
  return o;
}

/* Scoring service: the hosted app scores all 3.8 million overlapping Earth squares on the server (pipeline/score_service.py) and returns the
   best square per region. If the service is not there (local copy, GitHub Pages) or fails, the app scores the built-in library in the browser. */
let EL = null, PLL = null, PNL = null, RS = null, runTok = 0, svcOK = location.protocol != "file:", svcFailed = false, lastReq = "", lastR = null, runT = 0;
const unb = (b, T) => { const s = atob(b), u = new Uint8Array(s.length); for (let i = 0; i < s.length; i++) u[i] = s.charCodeAt(i); return new T(u.buffer); };
async function remoteScore(m, p) {
  const body = JSON.stringify({moon: {hist: Array.from(m.h), hurst: m.H, ret: m.ret, t_avg: isNaN(m.tavg) ? null : m.tavg, t_max: isNaN(m.tmax) ? null : m.tmax, ice: m.ice || 0}, w: p.w, gate: p.gate, flt: {countries: S.flt.country ? [S.flt.country] : null, near: S.flt.near, max_alt: S.flt.alt, probe: S.probe}});
  if (body === lastReq && lastR) return lastR;                         // same question as last time (e.g. only "hide near known" changed)
  const ac = new AbortController(), to = setTimeout(() => ac.abort(), 90000);
  try {
    const r = await fetch("api/score", {method: "POST", headers: {"Content-Type": "application/json"}, body, signal: ac.signal});
    if (!r.ok) throw new Error("service " + r.status); const d = await r.json(); let out;
    if (d.empty) out = {empty: d.empty}; else { if (!d.k) throw new Error("empty");
      out = {E: {n: d.k, hs: d.hist_scale, hist: unb(d.hist, d.hist_scale == 10000 ? Uint16Array : Uint8Array), meta: unb(d.meta, Float32Array), nc: d.cols.length, c: Object.fromEntries(d.cols.map((k, i) => [k, i]))}, PL: d.place ? unb(d.place, Uint16Array) : null, PN: d.place_names || null,
        scores: unb(d.scores, Float32Array), terr: unb(d.terr, Float32Array), spread: unb(d.spread, Float32Array), stats: d.stats, nTop: d.n_top, known: d.known, probe: d.probe}; }
    lastReq = body; lastR = out; return out;
  } finally { clearTimeout(to); }
}
function libInfo(R) {
  $("libinfo").innerHTML = R ? `${R.stats.n.toLocaleString()} Earth squares scored on the server · ${M.n.toLocaleString()} lunar spots`
    : `${EL.n.toLocaleString()} Earth windows (built-in library, scored in your browser) · ${M.n.toLocaleString()} lunar spots` + (svcFailed ? ` · <span class="fb">scoring server unreachable</span> <button class="linkbtn" id="retrySvc">Retry server</button>` : "");
  const b = $("retrySvc"); if (b) b.onclick = () => { svcOK = true; svcFailed = false; countriesDone = null; run(); };
  $("fAlt").disabled = !R && !svcOK; $("altNote").textContent = !R && !svcOK ? "needs the scoring server" : "";
}
const skeleton = () => `<table>${Array.from({length: 6}, () => `<tr class="skel"><td></td><td><i style="width:60%"></i><i style="width:40%"></i></td><td><i style="width:40px;margin-left:auto"></i></td></tr>`).join("")}</table>`;
function runSoon() { clearTimeout(runT); runT = setTimeout(run, 300); }
async function run() {
  if (!S.spot) return;
  const tok = ++runTok, m = moonRef(), p = PURPOSES[S.purpose];
  if (!S.keep && S.site != null && UI.open == "site" && E && S.site < E.n) S.keep = {lat: ev(S.site, "lat"), lon: ev(S.site, "lon")};   // keep the open site if it survives
  let R = null, failed = false;
  if (svcOK) {
    UI.busy(true); $("st3").textContent = "scoring…";
    if (!(lastR && lastReq)) { $("ranked").innerHTML = skeleton(); }
    $("verdict").innerHTML = `<div class="flag info">Scoring every Earth square on the server…</div>`;
    const slow = setTimeout(() => { if (tok === runTok) $("verdict").innerHTML = `<div class="flag info">Waking the scoring server. The first request can take up to a minute.</div>`; }, 3000);
    try { R = await remoteScore(m, p); } catch (e) { failed = true; }
    clearTimeout(slow); if (tok !== runTok) return; UI.busy(false);
    if (failed) { svcOK = false; svcFailed = true; UI.toast("Scoring server unreachable. Showing the built-in library."); }
  }
  if (R && R.empty) { RS = null; topSites = []; scores = null; clearPins(); drawNear(); UI.chips();
    $("verdict").innerHTML = `<div class="flag bad">${esc(R.empty)} Widen the search area.<br><button class="chip" id="vClear">Clear filters</button></div>`; $("vClear").onclick = clearFilter;
    $("ranked").innerHTML = ""; $("known").innerHTML = ""; UI.afterRun(); siteGone(); writeHash(); return; }
  fillCountries(R);
  RS = R; if (R) { E = R.E; PL = R.PL; PN = R.PN; scores = R.scores; } else { E = EL; PL = PLL; PN = PNL; scores = new Float32Array(E.n); for (let j = 0; j < E.n; j++) scores[j] = afom(foms(j, m), p); }
  libInfo(R);
  // search area (browser library only; the server applies it itself)
  const inF = new Uint8Array(E.n).fill(1), F = S.flt, filtered = !!(F.country || F.near || F.alt != null); let probeJ = -2, probeKm = null;
  if (!R && filtered) { const ci = F.country && PN ? PN.countries.indexOf(F.country) : -1; for (let j = 0; j < E.n; j++) { if (F.country && (!PL || PL[j * 4] !== ci)) inF[j] = 0; else if (F.near && kmBetween(ev(j, "lat"), ev(j, "lon"), F.near[0], F.near[1]) > F.near[2]) inF[j] = 0; } }
  INF = R ? null : inF;
  if (R) { if (R.probe) { probeJ = R.probe.idx; probeKm = R.probe.km; } } else if (S.probe) { let bd = 6; probeJ = -1; for (let j = 0; j < E.n; j++) { if (Math.abs(ev(j, "lat") - S.probe[0]) > 0.1) continue; const d = kmBetween(ev(j, "lat"), ev(j, "lon"), S.probe[0], S.probe[1]); if (d < bd) { bd = d; probeJ = j; probeKm = d; } } }
  let NT = 0; if (R) NT = R.stats.n; else for (let j = 0; j < E.n; j++) NT += inF[j];
  UI.chips();
  if (!NT) { topSites = []; clearPins(); drawNear(); $("verdict").innerHTML = `<div class="flag bad">No library squares inside this search area. Widen it.<br><button class="chip" id="vClear">Clear filters</button></div>`; $("vClear").onclick = clearFilter; $("ranked").innerHTML = ""; UI.afterRun(); siteGone(); writeHash(); return; }
  let bestS = 0; for (let j = 0; j < E.n; j++) if (inF[j] && scores[j] > bestS) bestS = scores[j];
  let ties = 0; if (R) ties = R.stats.ties; else for (let j = 0; j < E.n; j++) if (inF[j] && scores[j] >= bestS - 0.01) ties++;
  const tied = ties > 50, terr = j => { const f = foms(j, m); return 0.5 * f.slope + 0.5 * f.scale; };
  let order;
  if (R) order = Array.from({length: R.nTop}, (_, i) => i);
  else if (tied) { const set = []; for (let j = 0; j < E.n; j++) if (inF[j] && scores[j] >= bestS - 0.01) set.push([terr(j), j]); set.sort((a, b) => b[0] - a[0]); order = set.map(x => x[1]); }
  else order = Array.from(scores.keys()).filter(j => inF[j]).sort((a, b) => scores[b] - scores[a]);
  const seen = new Set(); topSites = [];
  for (const j of order) { const key = Math.floor(ev(j, "lat") / 2) + "," + Math.floor(ev(j, "lon") / 2); if (seen.has(key)) continue; if (F.newOnly && nearKnown(ev(j, "lat"), ev(j, "lon"))) continue; seen.add(key); topSites.push(j); if (topSites.length == 15) break; }
  if (!topSites.length) { clearPins(); drawNear(); $("verdict").innerHTML = `<div class="flag bad">Every site in this search area is near a known analog.<br><button class="chip" id="vClear">Show them</button></div>`; $("vClear").onclick = () => { S.flt.newOnly = false; $("newOnly").checked = false; run(); }; $("ranked").innerHTML = ""; UI.afterRun(); siteGone(); writeHash(); return; }
  const best = scores[topSites[0]], isT = S.purpose == "mobility", tTop = terrOf(topSites[0], m);
  if (isT) { let strong = 0, poss = 0; if (R) { strong = R.stats.strong; poss = R.stats.possible; } else for (let j = 0; j < E.n; j++) { if (!inF[j]) continue; if (scores[j] >= CAL.strong) strong++; else if (scores[j] >= CAL.possible) poss++; }
    $("verdict").innerHTML = best >= CAL.strong ? `<div class="flag ok">${strong.toLocaleString()} of ${NT.toLocaleString()} Earth windows score ${CAL.strong} or higher: as alike to this lunar spot as two halves of the same lunar terrain are to each other. A further ${poss.toLocaleString()} are possible matches (${CAL.possible} to ${CAL.strong}). These are candidates to check, not confirmed analogs. Showing the best one per region.</div>`
      : best >= CAL.possible ? `<div class="flag">No Earth window reaches ${CAL.strong} for this spot. ${poss.toLocaleString()} are possible matches (${CAL.possible} to ${CAL.strong}); nearly one in three pairs of unrelated lunar squares also score in or above that range, so treat these as leads only.</div>`
      : `<div class="flag bad">No terrain match on Earth for this spot (best ${f2(best)}). Unrelated lunar squares score about ${CAL.unrelated} against each other, so scores below ${CAL.possible} carry no evidence of similarity.</div>`; }
  else $("verdict").innerHTML = `<div class="flag${best >= 0.8 ? " ok" : best >= 0.5 ? "" : " bad"}">Best score for this purpose: ${f2(best)}. This purpose mixes terrain with light, cold or frozen ground, and only the terrain part has been tested for reliability. Terrain of the top site: ${f2(tTop)}, ${level(tTop).name}.</div>`;
  if (tied) $("verdict").innerHTML += `<div class="flag">${ties.toLocaleString()} Earth windows tie within 0.01 of the top score, so their order by score is not meaningful. The list shows the tied sites whose terrain is most like this lunar spot.</div>`;
  if (!R && svcFailed) $("verdict").innerHTML += `<div class="flag info">Scoring server unreachable, so this is the built-in library (${EL.n.toLocaleString()} windows).${F.alt != null ? " The altitude limit is not applied." : ""}</div>`;
  const near = moonNear(), pj = probeJ, lvp = pj >= 0 ? level(terrOf(pj, m)) : null;
  const probeHtml = pj == -2 ? "" : pj < 0 ? `<div class="flag" style="margin:0 12px 10px">No library square within 6 km of ${S.probe[0]}, ${S.probe[1]}. That place is not bare land in our mask, is nearly all sea, or lies outside the coverage. <button class="linkbtn" data-unprobe>Remove</button></div>`
    : `<table><tr class="site probe" data-j="${pj}" tabindex="-1"><td>★</td><td><button class="x2" data-unprobe aria-label="Remove your place">×</button><span class="pl">Your place: ${esc((place(pj) || {}).country || "unnamed land")}</span><span class="co">${coord(pj)}${probeKm != null ? ` · nearest library square ${probeKm.toFixed(1)} km away` : ""}</span></td><td class="n"><b>${f2(scores[pj])}</b><br><span class="tag ${lvp.k}">${isT ? "" : "terrain: "}${lvp.name}</span></td></tr></table>`;
  $("ranked").innerHTML = probeHtml + `<table>` + topSites.map((j, r) => { const k = nearKnown(ev(j, "lat"), ev(j, "lon")), lv = level(terrOf(j, m)), tie = r > 0 && scores[j] >= best - CAL.err;
    return `<tr class="site" data-j="${j}" tabindex="-1"><td>${r + 1}</td><td><span class="pl">${esc((place(j) || {}).country || "Unnamed land")}</span><span class="co">${coord(j)}</span>${k ? `<span class="tag k">near ${esc(k.split(" (")[0])}</span>` : ""}${ev(j, "nomask") ? `<span class="tag">Antarctic, ice not filtered</span>` : ""}</td><td class="n"><b>${f2(scores[j])}</b><br><span class="tag ${lv.k}">${isT ? "" : "terrain: "}${lv.name}</span>${tie ? `<br><span class="mut" style="font-size:11.5px">level with #1</span>` : ""}</td></tr>`; }).join("") + "</table>";
  $("ranked").insertAdjacentHTML("beforeend", `<p class="mut" style="margin:8px 12px 0">One score is uncertain by about ${CAL.err}, so sites marked "level with #1" cannot be ranked against it.</p><div class="acts2"><button class="chip" id="csvBtn">Download CSV</button></div>`);
  $("ranked").dataset.roving = "tr.site"; $("csvBtn").onclick = downloadCsv;
  $("ranked").querySelectorAll("[data-unprobe]").forEach(b => b.onclick = e => { e.stopPropagation(); clearProbe(); });
  bindRows($("ranked"));
  clearPins();
  topSites.forEach((j, r) => { const k = !!nearKnown(ev(j, "lat"), ev(j, "lon")), mk = L.circleMarker([ev(j, "lat"), ev(j, "lon")], {radius: 11, color: k ? "#c9d1dc" : "#F2B04C", fillColor: k ? "#c9d1dc" : "#F2B04C", weight: 2, fillOpacity: .5}).addTo(earthMap).bindTooltip(String(r + 1), {permanent: true, direction: "center", className: "pinnum"});
    mk.base = k ? "#c9d1dc" : "#F2B04C"; mk.on("click", () => { selectSite(j); UI.opener = rowFor(j); UI.go(4); }); earthMarkers.push(mk); });
  if (pj >= 0) { probeMk = L.marker([ev(pj, "lat"), ev(pj, "lon")], {icon: L.divIcon({className: "", html: '<div class="probepin"><span>★</span></div>', iconSize: [18, 18], iconAnchor: [9, 9]}), zIndexOffset: 1000, keyboard: false}).addTo(earthMap).bindTooltip("Your place");
    probeMk.on("click", () => { selectSite(pj); UI.opener = rowFor(pj); UI.go(4); }); }
  $("legProbe").hidden = pj < 0; drawNear();
  UI.afterRun();
  // known analog sites benchmark: best window within ~0.3 degrees of each
  $("known").innerHTML = "<table><tr><th>Known analog site</th><th>Best nearby window</th><th>Score</th></tr>" + MAN.known.map((k, q) => { let bj = -1, bs = -1;
    if (R) { const kk = R.known.find(x => x.name == k.name); if (kk && kk.idx >= 0) { bj = kk.idx; bs = scores[bj]; } }
    else for (let j = 0; j < E.n; j++) { if (Math.abs(ev(j, "lat") - k.lat) < 0.3 && Math.abs(ev(j, "lon") - k.lon) * Math.cos(k.lat * Math.PI / 180) < 0.3 && scores[j] > bs) { bs = scores[j]; bj = j; } }
    return bj < 0 ? `<tr><td>${esc(k.name)}</td><td class="mut">not in library (not bare land in our mask)</td><td></td></tr>` : `<tr class="site" data-j="${bj}" tabindex="-1"><td>${esc(k.name)}</td><td>${placeShort(bj)}${coord(bj)}</td><td class="n"><b>${f2(bs)}</b></td></tr>`; }).join("") + "</table>";
  $("known").dataset.roving = "tr.site"; bindRows($("known"));
  // which site to show: your new place, else the site that was open (if it is still in the results), else #1
  let target = topSites[0], note = "", open = false;
  if (S.probeNew && pj >= 0) { target = pj; open = true; }
  else if (S.keep) { const k = findNear(S.keep.lat, S.keep.lon, 1); if (k >= 0) target = k; else if (UI.open == "site" || S.keep.open) note = "The site you had open is not in the new results, so this is #1."; open = !!S.keep.open; }
  S.probeNew = false; S.keep = null;
  selectSite(target, {note});
  if (open) UI.go(4);
}
function bindRows(box) {
  const rows = box.querySelectorAll("tr.site"); if (rows.length) rows[0].tabIndex = 0;
  rows.forEach(tr => { tr.onclick = () => { selectSite(+tr.dataset.j); UI.go(4, false, true); }; tr.onkeydown = e => { if (e.key == "Enter" || e.key == " ") { e.preventDefault(); tr.onclick(); } }; });
}
const rowFor = j => document.querySelector(`#ranked tr.site[data-j="${j}"]`) || document.querySelector(`#known tr.site[data-j="${j}"]`);
function findNear(lat, lon, km) { let bj = -1, bd = km; for (let j = 0; j < E.n; j++) { if ((INF && !INF[j]) || Math.abs(ev(j, "lat") - lat) > 0.02) continue; const d = kmBetween(ev(j, "lat"), ev(j, "lon"), lat, lon); if (d <= bd) { bd = d; bj = j; } } return bj; }
function clearPins() { earthMarkers.forEach(mk => earthMap.removeLayer(mk)); earthMarkers = []; if (probeMk) { earthMap.removeLayer(probeMk); probeMk = null; } $("legProbe").hidden = true; }
function drawNear() { if (nearCircle) { earthMap.removeLayer(nearCircle); nearCircle = null; } const n = S.flt.near; if (n) nearCircle = L.circle([n[0], n[1]], {radius: n[2] * 1000, color: "#F2B04C", weight: 1.5, dashArray: "6 6", fill: false, interactive: false}).addTo(earthMap); }
function siteGone() { S.site = null; if (UI.open == "site") UI.panel(null); $("siteTitle").textContent = ""; $("card").innerHTML = ""; }
/* The selected site keeps a bigger pin with a white ring while its panel is open. */
function markPins() { earthMarkers.forEach((mk, r) => { const on = UI.open == "site" && topSites[r] === S.site;
  mk.setStyle(on ? {radius: 14, weight: 3, color: "#ffffff", fillColor: mk.base, fillOpacity: .95} : {radius: 11, weight: 2, color: mk.base, fillColor: mk.base, fillOpacity: .5}); if (on) mk.bringToFront(); });
  if (probeMk && probeMk.getElement()) probeMk.getElement().firstChild.style.boxShadow = UI.open == "site" && S.site === probeJOf() ? "0 0 0 3px #fff" : ""; }
const probeJOf = () => { const tr = document.querySelector("#ranked tr.probe"); return tr ? +tr.dataset.j : -9; };
/* When the panel narrows the map, move the map so the selected pin stays in view. */
function showPin() { if (S.site == null || !E || S.site >= E.n) return; earthMap.panInside([ev(S.site, "lat"), ev(S.site, "lon")], {padding: [60, 60], animate: true}); }
const altOf = j => E.c.alt !== undefined && !isNaN(ev(j, "alt")) ? Math.round(ev(j, "alt") / 10) * 10 : null;   // altitude from the scoring data (hosted version)
const altAny = j => altOf(j) != null ? altOf(j) : V.c3e && V.c3e.j === j && V.c3e.alt != null ? Math.round(V.c3e.alt / 10) * 10 : null;
function kmBetween(a, b, c, d) { const r = Math.PI / 180, x = Math.sin((a - c) * r / 2), y = Math.sin((b - d) * r / 2); return 12742 * Math.asin(Math.sqrt(x * x + Math.cos(a * r) * Math.cos(c * r) * y * y)); }

/* ---------- filters, your place, chips ---------- */
let countriesDone = null;
async function fillCountries(R) { const mode = R ? "svc" : "local"; if (countriesDone === mode) return; countriesDone = mode; let list = [];
  if (R) { try { list = (await (await fetch("api/status")).json()).countries || []; } catch (e) {} if (!list.length) countriesDone = null; }
  else if (PLL && PNL) { const seen = new Set(); for (let j = 0; j < EL.n; j++) seen.add(PLL[j * 4]); list = PNL.countries.filter((c, i) => seen.has(i)); }
  list = [...list].sort(); if (S.flt.country && !list.includes(S.flt.country)) list.unshift(S.flt.country);
  $("fCountry").innerHTML = `<option value="">the whole world</option>` + list.map(c => `<option${c == S.flt.country ? " selected" : ""}>${esc(c)}</option>`).join(""); }
function num(id, lo, hi) { const v = parseFloat($(id).value); return isNaN(v) || v < lo || v > hi ? null : v; }
function bad(ids, msg, out = "fMsg") { document.querySelectorAll(".fbar input").forEach(i => i.removeAttribute("aria-invalid")); ids.forEach(id => $(id).setAttribute("aria-invalid", "true")); $(out).textContent = msg; if (ids[0]) $(ids[0]).focus(); return false; }
function applyFilter() {
  const la = num("fLat", -90, 90), lo = num("fLon", -180, 180), km = num("fKm", 1, 20000), F = {country: $("fCountry").value, near: null, alt: null, newOnly: $("newOnly").checked};
  if ($("fLat").value.trim() || $("fLon").value.trim()) { if (la === null || lo === null || km === null) return bad([la === null ? "fLat" : lo === null ? "fLon" : "fKm"], "Enter latitude (-90 to 90), longitude (-180 to 180, west negative) and a distance in km."); F.near = [la, lo, km]; }
  if ($("fAlt").value.trim() && !$("fAlt").disabled) { F.alt = num("fAlt", -500, 9000); if (F.alt === null) return bad(["fAlt"], "Enter the altitude limit in metres (-500 to 9,000)."); }
  bad([], ""); S.flt = F; UI.pop(null); run(); return true;
}
function fillFilterForm() { const F = S.flt; $("fCountry").value = F.country || ""; $("newOnly").checked = !!F.newOnly; $("fLat").value = F.near ? F.near[0] : ""; $("fLon").value = F.near ? F.near[1] : ""; $("fKm").value = F.near ? F.near[2] : 200; $("fAlt").value = F.alt != null ? F.alt : ""; }
function clearFilter() { S.flt = {country: "", near: null, alt: null, newOnly: false}; fillFilterForm(); bad([], ""); run(); }
function applyProbe() { const la = num("pLat", -90, 90), lo = num("pLon", -180, 180); if (la === null || lo === null) return bad([la === null ? "pLat" : "pLon"], "Enter the latitude and longitude of the Earth place (west and south negative).", "pMsg");
  bad([], "", "pMsg"); S.probe = [la, lo]; S.probeNew = true; UI.pop(null); run(); }
function clearProbe() { S.probe = null; $("pLat").value = $("pLon").value = ""; if (S.site === probeJOf() && UI.open == "site") UI.panel(null); run(); }
UI.chips = () => { const F = S.flt, c = [];
  if (F.country) c.push([esc(F.country), () => { S.flt.country = ""; }]);
  if (F.near) c.push([`within ${F.near[2].toLocaleString()} km of ${F.near[0]}, ${F.near[1]}`, () => { S.flt.near = null; }]);
  if (F.alt != null) c.push([`below ${F.alt.toLocaleString()} m${!svcOK ? " (not applied)" : ""}`, () => { S.flt.alt = null; }]);
  if (F.newOnly) c.push(["new sites only", () => { S.flt.newOnly = false; }]);
  if (S.probe) c.push([`your place ${S.probe[0]}, ${S.probe[1]}`, () => { S.probe = null; $("pLat").value = $("pLon").value = ""; }]);
  $("fchips").innerHTML = c.map(([t], i) => `<span class="fchip">${t}<button data-i="${i}" aria-label="Remove filter: ${t.replace(/<[^>]*>/g, "")}">×</button></span>`).join("");
  $("fchips").querySelectorAll("button").forEach(b => b.onclick = () => { c[+b.dataset.i][1](); fillFilterForm(); run(); });
  $("fN").textContent = c.length || ""; };
function initForms() {
  $("coordForm").onsubmit = e => { e.preventDefault(); goCoord(); };
  $("filterForm").onsubmit = e => { e.preventDefault(); applyFilter(); };
  $("probeForm").onsubmit = e => { e.preventDefault(); applyProbe(); };
  $("clearBtn").onclick = () => { clearFilter(); };
  $("newOnly").onchange = () => { S.flt.newOnly = $("newOnly").checked; run(); };
  $("pickBtn").onclick = e => { e.stopPropagation(); UI.pick(true); };
  document.addEventListener("click", e => { const b = e.target.closest("[data-retry-sun]"); if (b && S.site != null) sunEarth(S.site); const t = e.target.closest("[data-retry-3d]"); if (t && S.site != null) loadEarthPatch(S.site); });
}

/* ---------- link state: spot, test, weights, filters, your place and the open site ---------- */
function writeHash() {
  if (!S.spot || !UI.ready) return; const F = S.flt, q = [`spot=${S.spot.x},${S.spot.y}`, `test=${S.purpose}`];
  if (isCustom(S.purpose)) q.push("w=" + Object.entries(PURPOSES[S.purpose].w).map(([k, v]) => k + ":" + Math.round(v * 100)).join(","));
  if (F.country) q.push("c=" + encodeURIComponent(F.country)); if (F.near) q.push("near=" + F.near.join(",")); if (F.alt != null) q.push("alt=" + F.alt); if (F.newOnly) q.push("new=1");
  if (S.probe) q.push("probe=" + S.probe.join(","));
  if (UI.open == "site" && S.site != null && E && S.site < E.n) q.push(`site=${ev(S.site, "lat").toFixed(3)},${ev(S.site, "lon").toFixed(3)}`);
  history.replaceState(null, "", "#" + q.join("&"));
}
function readHash() {
  const h = decodeURIComponent(location.hash.slice(1)); if (!h) return null;
  if (/^-?\d/.test(h)) { const a = h.split(","); return a.length >= 3 && isFinite(+a[0]) && isFinite(+a[1]) ? {x: +a[0], y: +a[1], test: a[2]} : null; }   // old links: x,y,purpose
  const q = new URLSearchParams(h), nums = (k, n) => { const v = (q.get(k) || "").split(",").map(Number); return v.length == n && v.every(isFinite) ? v : null; };
  const sp = nums("spot", 2); if (!sp) return null;
  return {x: sp[0], y: sp[1], test: q.get("test"), w: q.get("w"), c: q.get("c") || "", near: nums("near", 3), alt: q.get("alt") != null && isFinite(+q.get("alt")) ? +q.get("alt") : null, newOnly: q.get("new") == "1", probe: nums("probe", 2), site: nums("site", 2)};
}
function applyHash(o) {
  if (PURPOSES[o.test]) S.purpose = o.test;
  if (o.w) { const p = PURPOSES[S.purpose], w = {}; let t = 0; for (const part of o.w.split(",")) { const [k, v] = part.split(":"); if (k in W0[S.purpose] && isFinite(+v) && +v >= 0) { w[k] = +v; t += +v; } }
    if (t > 0 && Object.keys(w).length == Object.keys(W0[S.purpose]).length) { for (const k in w) w[k] /= t; p.w = w; } }
  S.flt = {country: o.c || "", near: o.near, alt: o.alt, newOnly: !!o.newOnly}; S.probe = o.probe || null; fillFilterForm();
  if (S.probe) { $("pLat").value = S.probe[0]; $("pLon").value = S.probe[1]; }
  if (o.site) S.keep = {lat: o.site[0], lon: o.site[1], open: true};
  UI.onPurpose(); if (o.site) UI.go(3);
  if (!selectSpot(o.x, o.y, null, {keep: true})) { const d = MAN.regions[0]; selectSpot(d.x, d.y, d.name); }
  else moonMap.panTo([S.spot.y / 1000, S.spot.x / 1000]);
}

/* ---------- copy, CSV, print ---------- */
/* Plain-text summary of one site, built only from numbers the tool computed. */
function lowSunHours(lat, maxEl) { const r = Math.PI / 180, out = []; for (let mth = 0; mth < 12; mth++) { const doy = 15 + mth * 30.4, dec = -23.44 * Math.cos(2 * Math.PI * (doy + 10) / 365) * r; let n = 0;
    for (let h = 0; h < 24; h += 0.1) { const el = Math.asin(Math.sin(lat * r) * Math.sin(dec) + Math.cos(lat * r) * Math.cos(dec) * Math.cos(15 * (h - 12) * r)) / r; if (el > 0 && el <= maxEl) n++; } out.push(n / 10); } return out; }
const MON = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
function siteSummary(j = S.site) { const m = moonRef(), f = foms(j, m), p = PURPOSES[S.purpose], pl = place(j) || {}, tm = (0.5 * f.slope + 0.5 * f.scale) * f.bare * f.reliable, nr = nearRange(j, moonNear()), i = S.spot.i, L = [];
  const mx = 90 - Math.abs(mv(i, "lat")) + 1.54, hrs = lowSunHours(ev(j, "lat"), mx), e = SUN.earth && SUN.earth.j === j && SUN.earth.curve ? SUN.earth : null, mo = SUN.moon && SUN.moon.curve ? SUN.moon : null;
  L.push(`Lunar spot: ${S.spot.name || "unnamed"} (${Math.abs(mv(i, "lat")).toFixed(2)} S, ${lonTxt(mv(i, "lon"))}), 10 km square. Purpose: ${p.name}${isCustom(S.purpose) ? " (custom weights)" : ""}.`);
  L.push(`Earth site: ${pl.country || "country not found"}, ${coord(j)}${pl.town ? `; nearest town over 1,000 people ${pl.town}, about ${pl.km} km` : ""}${pl.border < 60000 ? `; land border ${pl.border} km` : ""}${altOf(j) != null ? `; about ${altOf(j)} m above sea level` : V.c3e.alt != null && V.c3e.j === j ? `; about ${Math.round(V.c3e.alt / 10) * 10} m above sea level (display tiles)` : ""}.`);
  L.push(`Terrain match ${f2(RS ? RS.terr[j] : tm)} (${level(RS ? RS.terr[j] : tm).name}); uncertainty about ${f2(RS ? Math.hypot(RS.spread[j], 0.03, 0.02) : CAL.err)}. Slope chart match ${f2(f.slope)}, roughness across scales ${f2(f.scale)}.`);
  L.push(`Median slope Moon ${f1(mv(i, "slope_p50"))} deg, Earth ${f1(ev(j, "slope_p50"))} deg. Scaling number Moon ${f2(m.H)}, Earth ${f2(ev(j, "hurst"))}.`);
  if (nr) L.push(`Against the 8 neighbouring lunar squares (5 km away): ${f2(nr[0])} to ${f2(nr[1])}.`);
  if (RS) L.push(`Moving the Earth square 2.5 km changes the score by ${f2(RS.spread[j])} on average.`);
  if (e && mo) { let s = 0, k = 0; ELS.forEach((el, q) => { if (el <= mo.maxEl) { s += Math.abs(mo.curve[q] - e.curve[q]); k++; } }); L.push(`Sun and shadow: over sun heights up to ${mo.maxEl.toFixed(1)} deg, shadowed share differs by ${Math.round(s / k * 100)} percentage points on average.`);
    const a = reach(mo.T.slope, SUN.lim), b = reach(e.T.slope, SUN.lim); L.push(`Ground under ${SUN.lim} deg: Moon ${pc(a.under)}, Earth ${pc(b.under)}; largest joined-up area: Moon ${pc(a.joined)}, Earth ${pc(b.joined)}. Patch seen from a typical point: Moon ${pc(mo.T.visMean)}, Earth ${pc(e.T.visMean)}.`); }
  L.push(`Frozen ground: Moon ice-stable share ${pc(m.ice || 0)}, Earth permafrost index ${isNaN(ev(j, "pzi")) ? "no data" : pc(ev(j, "pzi"))}. Coldest-month night ${isNaN(ev(j, "t_night_min")) ? "no data" : ev(j, "t_night_min").toFixed(0) + " K"}. Longest darkness ${Math.round(ev(j, "dark_h"))} h.`);
  const best = hrs.map((h, q) => [h, q]).sort((a, b) => b[0] - a[0]).slice(0, 3); L.push(`Natural sun between the horizon and ${mx.toFixed(1)} deg (the lunar range): most in ${best.map(b => `${MON[b[1]]} (${b[0].toFixed(1)} h/day)`).join(", ")}.`);
  L.push(`Not tested by this tool: rock and soil type, dust, access and permits. Gravity, vacuum and radiation cannot be matched on Earth. Weights set by the team, not NASA. Terrain screen, not a validated analog finder. Candidate only; not field-checked.`);
  L.push(`Link: ${location.href}`);
  return L.join("\n"); }
function copyText(t, msgId, ok) {
  const done = () => { $(msgId).textContent = ok; setTimeout(() => { if ($(msgId)) $(msgId).textContent = ""; }, 2500); };
  const fallback = () => { const a = document.createElement("textarea"); a.value = t; a.style.position = "fixed"; a.style.opacity = "0"; document.body.appendChild(a); a.select(); let k = false; try { k = document.execCommand("copy"); } catch (e) {} a.remove();
    if (k) done(); else { const w = window.open("", "_blank"); if (w) w.document.write("<pre>" + esc(t) + "</pre>"); } };
  (navigator.clipboard && window.isSecureContext ? navigator.clipboard.writeText(t) : Promise.reject()).then(done, fallback);
}
function downloadCsv() {
  if (!scores) return; const m = moonRef(), cols = Object.keys(FACT), order = Array.from(scores.keys()).filter(j => !INF || INF[j]).sort((x, y) => scores[y] - scores[x]).slice(0, 500);
  const rows = [["rank", "country", "nearest_town", "town_km", "border_km", "lat", "lon", "score", ...cols, "median_slope_deg", "known_site_within_55km"].join(",")];
  const q = s => /[",\n]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s;
  order.forEach((j, r) => { const f = foms(j, m); const pl = place(j) || {}; rows.push([r + 1, q(pl.country || ""), q(pl.town || ""), pl.town ? pl.km : "", pl.border > 60000 || pl.border == null ? "" : pl.border, ev(j, "lat").toFixed(3), ev(j, "lon").toFixed(3), scores[j].toFixed(3), ...cols.map(k => f[k].toFixed(3)), ev(j, "slope_p50").toFixed(2), q(nearKnown(ev(j, "lat"), ev(j, "lon")) || "")].join(",")); });
  const F = S.flt, area = [F.country, F.near ? `within ${F.near[2]} km of ${F.near[0]} ${F.near[1]}` : "", F.alt != null && RS ? `below ${F.alt} m` : ""].filter(Boolean).join("; ");
  const head = `# Moon Analog Finder. Lunar spot ${S.spot.name || "unnamed"} ${mv(S.spot.i, "lat").toFixed(2)} ${mv(S.spot.i, "lon").toFixed(2)}; purpose ${PURPOSES[S.purpose].name}${isCustom(S.purpose) ? " (custom weights " + Object.entries(PURPOSES[S.purpose].w).map(([k, v]) => k + " " + Math.round(v * 100)).join(" ") + ")" : ""}; ${RS ? "best Earth squares per 2-degree region scored on the server, plus known sites" : "built-in library scored in the browser, top 500"}${area ? "; search limited to " + area : ""}. Terrain screen with modest measured skill; candidates only, not field-checked.\n`;
  const slug = (S.spot.name || `${Math.abs(mv(S.spot.i, "lat")).toFixed(1)}S_${mv(S.spot.i, "lon").toFixed(1)}E`).replace(/[^A-Za-z0-9.]+/g, "-");
  const u = URL.createObjectURL(new Blob([head + rows.join("\n")], {type: "text/csv"})), l = document.createElement("a"); l.href = u; l.download = `moon-analog_${slug}_${S.purpose}.csv`; document.body.appendChild(l); l.click(); l.remove(); setTimeout(() => URL.revokeObjectURL(u), 1000);
}
function snapshot(v) { if (!v.z || !v.r) return ""; v.r.setPixelRatio(2); v.r.setSize(640, 400, false); v.cam.aspect = 1.6; v.cam.updateProjectionMatrix(); v.grp.rotation.set(0, 0, S.rot.z);
  const span = Math.max(V.c3m.span || 0, V.c3e.span || 0), dist = 19 * Math.max(1, (10 + span * 1.6) / 12), el = -S.rot.x - 0.5; v.cam.position.set(0, -dist * Math.cos(el), dist * Math.sin(el)); v.cam.lookAt(0, 0, 0); v.r.render(v.sc, v.cam); return v.cv.toDataURL("image/png"); }
function printSite() {
  if (S.site == null) return; const j = S.site, iM = snapshot(V.c3m), iE = snapshot(V.c3e); render3d();
  const card = $("card").cloneNode(true); card.querySelectorAll("details").forEach(d => d.open = true);
  $("printSheet").innerHTML = `<div class="mut">${$("siteEyebrow").textContent}</div><h1>${esc($("siteTitle").textContent)}</h1><div class="mut">${esc($("siteSub").textContent)}</div><div>${$("siteChips").innerHTML}</div>
    <h2>Match</h2>${card.innerHTML}
    <h2>Terrain, 10 km patches (heights x2)</h2><div class="imgs"><div>${iM ? `<img src="${iM}" alt="">` : "no data"}<div class="mut">${esc($("capM").textContent)}</div></div><div>${iE ? `<img src="${iE}" alt="">` : "no data"}<div class="mut">${esc($("capE").textContent)}</div></div></div>
    <h2>Sun and shadow</h2><p>${$("sunLab").innerHTML}</p>${$("sunChart").innerHTML}<div>${$("sunTxt").innerHTML}</div>
    <h2>Reach and line of sight</h2><div class="reach">${$("reachTxt").innerHTML}</div>
    <h2>How far to trust this</h2><div class="mut">${$("trust").innerHTML}</div><p class="mut">Link: ${esc(location.href)}</p>`;
  window.print();
}
window.addEventListener("afterprint", () => { $("printSheet").innerHTML = ""; });
/* Place context: country from Natural Earth 1:50m boundaries; nearest town of over 1,000 people in that country from GeoNames. */
function place(j) { if (!PL) return null; const c = PL[j * 4], t = PL[j * 4 + 1]; return {country: c == 65535 ? null : PN.countries[c], town: t == 65535 ? null : PN.towns[t], km: PL[j * 4 + 2], border: PL[j * 4 + 3]}; }
function placeShort(j) { const p = place(j); return p && p.country ? `<b>${esc(p.country)}</b> · ` : ""; }
function placeLong(j) { const p = place(j); if (!p || !p.country) return "";
  return `<span>Country (approx.)</span><span>${esc(p.country)}</span>` + (p.town ? `<span>Nearest town over 1,000 people</span><span>${esc(p.town)}, about ${p.km.toLocaleString()} km</span>` : "") +
    (p.border <= 15 ? `<span style="color:var(--warn)">Border</span><span style="color:var(--warn)">about ${p.border} km from a land border; country not certain at this map scale</span>` : ""); }
function coord(j) { const la = ev(j, "lat"), lo = ev(j, "lon"); return `${Math.abs(la).toFixed(2)}° ${la >= 0 ? "N" : "S"}, ${Math.abs(lo).toFixed(2)}° ${lo >= 0 ? "E" : "W"}`; }

/* ---------- tests and weights ---------- */
const isCustom = k => Object.keys(W0[k]).some(q => Math.abs((PURPOSES[k].w[q] || 0) - W0[k][q]) > 0.005);
function buildPurposes() {
  const o = OUT, noIce = S.spot && (mv(S.spot.i, "ice_share") || 0) < 0.05;
  const chip = k => { if (!S.spot) return ""; if (!o) return `<span class="tag">counting…</span>`; const q = o[k];
    if (k == "ice" && noIce) return `<span class="tag none">almost no stable ice at this lunar spot</span>`;
    if (k == "mobility") return q.n ? `<span class="tag strong">${q.n.toLocaleString()} windows with the same kind of terrain</span>` : q.poss ? `<span class="tag possible">possible matches only · best ${f2(q.best)}</span>` : `<span class="tag none">no terrain match · best ${f2(q.best)}</span>`;
    return q.n ? `<span class="tag strong">${q.n.toLocaleString()} windows score 0.80 or higher</span>` : `<span class="tag possible">partial matches only · best ${f2(q.best)}</span>`; };
  const hadFocus = $("purposes").contains(document.activeElement);
  $("purposes").innerHTML = ""; for (const k in PURPOSES) { const b = document.createElement("button"); b.className = "p" + (k == S.purpose ? " on" : ""); b.setAttribute("aria-pressed", k == S.purpose);
    b.innerHTML = `<span class="pn">${PURPOSES[k].name}${isCustom(k) ? ' <span class="tag">custom weights</span>' : ""}</span><small>${PURPOSES[k].desc}</small><span class="pk">Compares</span><span class="pv">${PUI[k].cmp}</span><span class="pk">Cannot judge</span><span class="pv">${PUI[k].cant}</span><span class="po">${chip(k)}</span>`;
    b.onclick = () => { if (S.purpose != k) { S.purpose = k; buildPurposes(); run(); } UI.onPurpose(); UI.pop(null); }; $("purposes").appendChild(b); }
  $("outNote").textContent = o ? `Outlook counted on the built-in library of ${o.lib.toLocaleString()} Earth windows for the lunar spot you picked, with the weights shown. The list itself comes from ${RS ? "the server's 3.8 million squares" : "the same built-in library"}.` : "";
  buildWeights(); UI.onPurpose(); if (hadFocus) $("purposes").querySelector("button.p.on").focus();
}
function buildWeights(focusKey) {
  const p = PURPOSES[S.purpose], custom = Object.keys(PURPOSES).some(isCustom);
  $("weights").innerHTML = `<div class="whead"><span>Weights for ${p.name.toLowerCase()} (set by our team, not by NASA). They are scaled to add up to 100.</span><button class="chip" id="wReset"${custom ? "" : " disabled"}>Reset weights</button></div>`;
  for (const k in p.w) { const l = document.createElement("label"), v = Math.round(p.w[k] * 100); l.innerHTML = `${FACT[k]} <input type="range" min="0" max="100" value="${v}" data-k="${k}" aria-label="${FACT[k]} weight"> <b>${v}</b>`;
    const inp = l.querySelector("input"), out = l.querySelector("b");
    inp.oninput = () => { out.textContent = inp.value; };
    inp.onchange = () => { const old = {...p.w}; p.w[k] = inp.value / 100; const t = Object.values(p.w).reduce((a, b) => a + b, 0);
      if (t <= 0) { p.w = old; buildWeights(k); return; } for (const q in p.w) p.w[q] /= t;
      buildWeights(k); UI.onPurpose(); refreshCards(); scheduleOutlook(); runSoon(); };
    $("weights").appendChild(l); }
  if (p.gate) $("weights").insertAdjacentHTML("beforeend", `<span class="pnote">Vegetated ground is scored zero for this test.</span>`);
  $("wReset").onclick = () => { for (const k in PURPOSES) PURPOSES[k].w = {...W0[k]}; buildWeights(); UI.onPurpose(); refreshCards(); scheduleOutlook(); runSoon(); };
  if (focusKey) { const f = $("weights").querySelector(`input[data-k="${focusKey}"]`); if (f) f.focus(); }
}
function refreshCards() { document.querySelectorAll("#purposes button.p").forEach((b, i) => { const k = Object.keys(PURPOSES)[i], pn = b.querySelector(".pn"); pn.innerHTML = PURPOSES[k].name + (isCustom(k) ? ' <span class="tag">custom weights</span>' : ""); }); }

/* ---------- Earth map ---------- */
let BASE = {}, baseKey = "gibs";
function buildEarthMap() {
  earthMap = L.map("earthmap", {worldCopyJump: true, minZoom: 1}).setView([25, 10], 1.5);
  BASE = {
    gibs: {name: "NASA Blue Marble", sub: "Shaded relief and sea floor (NASA GIBS)", sw: "linear-gradient(135deg,#123257,#3c6b3a 50%,#c9b98a)", layer: L.tileLayer("https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/BlueMarble_ShadedRelief_Bathymetry/default/GoogleMapsCompatible_Level8/{z}/{y}/{x}.jpeg", {maxNativeZoom: 8, maxZoom: 12, attribution: "Imagery: NASA GIBS Blue Marble"})},
    weld: {name: "Landsat close-up, 2000", sub: "NASA GIBS, 30 m; no Antarctica", sw: "linear-gradient(135deg,#6b5a3d,#a08c62 50%,#4d5b3a)", layer: L.tileLayer(WELD, {maxNativeZoom: 12, maxZoom: 14, attribution: "Imagery: NASA GIBS, Landsat WELD (2000)"})},
    osm: {name: "Street map", sub: "Place names (OpenStreetMap)", sw: "linear-gradient(135deg,#e9e5dc,#f6f3ee 50%,#aad3df)", layer: L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {maxZoom: 12, attribution: "© OpenStreetMap contributors"})},
    land: {name: "Land outlines", sub: "Natural Earth; works without map tiles", sw: "linear-gradient(135deg,#1b2433,#2a3548)", layer: null}};
  for (const k of ["gibs", "weld", "osm"]) { let n = 0; BASE[k].layer.on("tileerror", () => { if (baseKey != k || ++n < (k == "gibs" ? 1 : 3)) return; n = 0;
    if (k == "osm") setBase("land", "Map tiles unreachable, so this shows land outlines."); else setBase("osm", `${BASE[k].name} did not load, so this shows the street map.`); }); }
  knownLayer = L.layerGroup(MAN.known.map(k => L.circleMarker([k.lat, k.lon], {radius: 3, color: "#c9d1dc", weight: 1}).bindTooltip("Known analog: " + k.name))).addTo(earthMap);
  $("elayers").innerHTML = Object.entries(BASE).map(([k, b]) => `<button class="lrow" role="radio" data-b="${k}"><i style="background:${b.sw}"></i><span>${b.name}<small>${b.sub}</small></span></button>`).join("");
  $("elayers").querySelectorAll(".lrow").forEach(b => b.onclick = () => setBase(b.dataset.b));
  $("eover").innerHTML = `<button class="lrow chk2 on" id="knownTog" aria-pressed="true"><i style="background:radial-gradient(circle,#c9d1dc 0 3px,transparent 4px)"></i><span>Known analog sites<small>${MAN.known.length} established lunar analogs</small></span></button>`;
  $("knownTog").onclick = () => { const on = earthMap.hasLayer(knownLayer); on ? earthMap.removeLayer(knownLayer) : knownLayer.addTo(earthMap); $("knownTog").classList.toggle("on", !on); $("knownTog").setAttribute("aria-pressed", !on); };
  setBase("gibs");
}
async function setBase(k, note) {
  if (k == "land" && !BASE.land.layer) { try { const g = await (await fetch("data/land.json?v=" + DATA_V)).json(); BASE.land.layer = L.geoJSON(g, {interactive: false, style: {color: "#44506a", weight: 0.7, fillColor: "#1b2433", fillOpacity: 1}, attribution: "Land outlines: Natural Earth"}); } catch (e) { $("elayNote").textContent = "Land outlines could not be loaded."; return; } }
  for (const b of Object.values(BASE)) if (b.layer && earthMap.hasLayer(b.layer)) earthMap.removeLayer(b.layer);
  baseKey = k; BASE[k].layer.addTo(earthMap); BASE[k].layer.bringToBack && BASE[k].layer.bringToBack();
  $("earthmap").style.background = k == "osm" ? "#aad3df" : "#0b1119";
  $("elayers").querySelectorAll(".lrow").forEach(b => { const on = b.dataset.b == k; b.classList.toggle("on", on); b.setAttribute("aria-checked", on); });
  $("elayNote").textContent = note || ""; if (note) UI.toast(note);
}

/* ---------- satellite close-up (NASA GIBS, Landsat WELD annual composite, 30 m) ---------- */
function showSat(j) {
  if (UI.tab != "sat" || UI.open != "site") return;
  const la = ev(j, "lat"), lo = ev(j, "lon"), dy = 5 / 111.32, dx = 5 / (111.32 * Math.cos(la * Math.PI / 180));
  $("wvLink").href = `https://worldview.earthdata.nasa.gov/?v=${(lo - 1).toFixed(2)},${(la - 0.6).toFixed(2)},${(lo + 1).toFixed(2)},${(la + 0.6).toFixed(2)}`;
  if (la < -60) { $("satMsg").innerHTML = `<div>No Landsat coverage in Antarctica.<br><a target="_blank" rel="noopener" href="${$("wvLink").href}">Open this site in NASA Worldview</a></div>`; }
  else $("satMsg").innerHTML = "";
  if (!satMap) { satMap = L.map("sat", {zoomControl: true, attributionControl: true, scrollWheelZoom: false}); const t = L.tileLayer(WELD, {maxNativeZoom: 12, maxZoom: 14, attribution: "Imagery: NASA GIBS, Landsat WELD (2000)"}).addTo(satMap);
    let n = 0; t.on("tileerror", () => { if (++n == 4 && !$("satMsg").innerHTML) $("satMsg").innerHTML = `<div>Landsat tiles did not load (tile service unreachable).<br><a target="_blank" rel="noopener" href="${$("wvLink").href}">Open in NASA Worldview</a></div>`; }); t.on("load", () => { n = 0; }); }
  if (satRect) satMap.removeLayer(satRect);
  satRect = L.rectangle([[la - dy, lo - dx], [la + dy, lo + dx]], {color: "#fff", weight: 1.5, fill: false}).addTo(satMap);
  satMap.invalidateSize(); satMap.fitBounds([[la - 2.2 * dy, lo - 2.2 * dx], [la + 2.2 * dy, lo + 2.2 * dx]]);
}
/* ---------- site panel ---------- */
function histSvg(mh, j) {
  const W = 300, H = 86, n = 40, bw = W / n; let mx = 0; const eh = []; for (let b = 0; b < n; b++) { eh.push(E.hist[j * BINS + b] / (E.hs || 255)); mx = Math.max(mx, eh[b], mh[b]); }
  const y = v => H - 14 - (v / mx) * (H - 20);
  const bars = eh.map((v, b) => `<rect x="${(b * bw + 1).toFixed(1)}" y="${y(v).toFixed(1)}" width="${(bw - 2).toFixed(1)}" height="${(H - 14 - y(v)).toFixed(1)}" fill="#F2B04C" opacity=".55"/>`).join("");
  const line = Array.from({length: n}, (_, b) => `${(b * bw + bw / 2).toFixed(1)},${y(mh[b]).toFixed(1)}`).join(" ");
  const ticks = [0, 10, 20, 30, 40].map(t => `<text x="${t * bw}" y="${H - 2}" font-size="9" fill="#9aa4b2">${t}°</text>`).join("");
  return `<div class="cap" style="margin:10px 0 2px">Share of ground at each slope: <span style="color:#8CC8F5">Moon (line)</span>, <span style="color:#F2B04C">Earth (bars)</span></div><svg viewBox="0 0 ${W} ${H}" style="width:100%;height:auto">${bars}<polyline points="${line}" fill="none" stroke="#8CC8F5" stroke-width="1.6"/><line x1="${10 * bw}" x2="${10 * bw}" y1="4" y2="${H - 14}" stroke="#4b5563" stroke-dasharray="3 3"/><line x1="${20 * bw}" x2="${20 * bw}" y1="4" y2="${H - 14}" stroke="#4b5563" stroke-dasharray="3 3"/>${ticks}</svg>`;
}
function siteChips(j) {
  const k = nearKnown(ev(j, "lat"), ev(j, "lon")), lv = level(terrOf(j, moonRef())), a = altAny(j);
  $("siteChips").innerHTML = (k ? `<span class="tag k">near known analog ${esc(k.split(" (")[0])}</span>` : `<span class="tag new">candidate</span>`) + `<span class="tag ${lv.k}">${S.purpose == "mobility" ? "" : "terrain: "}${lv.name}</span><span class="tag">not field-checked</span>`
    + (ev(j, "nomask") ? `<span class="tag">Antarctic, ice not filtered</span>` : "") + (a != null && a > 3500 ? `<span class="tag possible">${a.toLocaleString()} m · crews need to acclimatise</span>` : "");
}
function selectSite(j, o = {}) {
  S.site = j; document.querySelectorAll("tr.site").forEach(tr => { const on = +tr.dataset.j == j; tr.classList.toggle("sel", on); tr.setAttribute("aria-selected", on); });
  const m = moonRef(), f = foms(j, m), p = PURPOSES[S.purpose], la = ev(j, "lat"), dh = ev(j, "dark_h"), pl = place(j) || {};
  const bar = k => `<div class="bar${f[k] < 0.15 ? " zero" : ""}"><span>${FACT[k]} ${k in p.w ? `<span class="w">weight ${Math.round(p.w[k] * 100)}</span>` : (k == "bare" && p.gate ? '<span class="w">gate</span>' : "")}</span><i><b style="width:${f[k] * 100}%"></b></i><span>${f2(f[k])}</span></div>`;
  const used = Object.keys(p.w).concat(p.gate ? ["bare"] : []), good = used.filter(k => f[k] >= 0.5), poor = used.filter(k => f[k] < 0.5), rest = Object.keys(FACT).filter(k => !used.includes(k));
  const weak = Object.keys(p.w).filter(k => f[k] < 0.5).map(k => FACT[k].toLowerCase()), tm = (0.5 * f.slope + 0.5 * f.scale) * f.bare * f.reliable, perr = RS ? Math.hypot(RS.spread[j], 0.03, 0.02) : CAL.err;
  const season = dh > 48 ? `Continuous darkness for about ${Math.round(dh / 24)} days each winter. ` : `Longest night about ${Math.round(dh)} hours. `;
  const breaks = `<b>Where it breaks:</b> ${S.purpose == "ice" ? ((m.ice || 0) < 0.05 ? "NASA's Diviner model finds almost no stable ground ice at this lunar spot, so ice drilling is not a sensible test purpose here. " : "") + (isNaN(ev(j, "pzi")) ? "No permafrost data for this site (the map stops at 60 degrees south). " : "") + "Earth permafrost is frozen soil near 260 K; lunar ice sits far colder and in vacuum, so this tests digging frozen ground only. " : ""}${p.gate === true && !f.reliable ? "this Earth window is nearly flat (median slope under 1 degree), where radar elevation noise is as large as the terrain, so it is not scored for terrain. " : ""}${weak.length ? "weak on " + weak.join(", ") + ". " : "no weak factor for this purpose. "}${season}Lunar gravity (one sixth of Earth's), vacuum and radiation cannot be reproduced at any Earth site.`;
  const nr = nearRange(j, moonNear());
  $("card").innerHTML = `<div class="scorehead"><div class="big">${f2(scores[j])}</div><div><div class="mut">for ${p.name.toLowerCase()}${isCustom(S.purpose) ? " (custom weights)" : ""}</div><div>Terrain match ${f2(tm)} ± ${f2(perr)}: <b>${level(tm).name}</b></div></div></div>
   ${calBar(tm, perr)}<div class="mut small">${RS ? `Moving this square 2.5 km changes the score by ${f2(RS.spread[j])} on average. ` : ""}${nr ? `Against the 8 neighbouring lunar squares (5 km away) this site scores ${f2(nr[0])} to ${f2(nr[1])}${nr[0] < CAL.possible && tm >= CAL.possible ? ". The match depends on the exact lunar position" : ""}.` : ""}</div>
   <div class="cards2"><div class="mini"><h4 class="okc">What matches</h4>${good.map(bar).join("") || '<p class="mut small">No factor used for this purpose scores 0.50 or higher.</p>'}</div>
   <div class="mini"><h4 class="badc">What differs</h4>${poor.map(bar).join("")}<div class="bar zero"><span>Gravity, vacuum, radiation</span><i><b style="width:0"></b></i><span>0.00</span></div></div></div>
   <p class="mut small" style="margin:10px 0 0">${breaks}</p>
   <details class="more"><summary>All numbers</summary>${rest.map(bar).join("")}${histSvg(m.h, j)}<div class="kv" style="margin-top:8px">${placeLong(j)}<span>Median slope (Moon / Earth)</span><span>${f1(mv(S.spot.i, "slope_p50"))}° / ${f1(ev(j, "slope_p50"))}°</span><span>Slope at 320 m (Moon / Earth)</span><span>${f1(mv(S.spot.i, "slope320_p50"))}° / ${f1(ev(j, "slope320_p50"))}°</span><span>Scaling number (Moon / Earth)</span><span>${f2(m.H)} / ${f2(ev(j, "hurst"))}</span>
   <span>Ground frozen all year (Moon ice-stable share / Earth permafrost index)</span><span>${pc(m.ice || 0)} / ${isNaN(ev(j, "pzi")) ? "no data" : pc(ev(j, "pzi"))}</span>
   <span>Earth site: coldest month, average night</span><span>${isNaN(ev(j, "t_night_min")) ? "no data" : ev(j, "t_night_min").toFixed(0) + " K"}</span><span>Moon spot average</span><span>${isNaN(m.tavg) ? "no data" : m.tavg.toFixed(0) + " K"}</span>
   <span>Score uncertainty: placement / pixels / elevation source</span><span>${RS ? f2(RS.spread[j]) : "no data"} / 0.03 / 0.02</span></div></details>
   <p class="acts"><button class="chip" id="copyBtn">Copy site summary</button><button class="chip" id="linkBtn">Copy link</button><button class="chip" id="printBtn">Print</button><a target="_blank" rel="noopener" href="https://worldview.earthdata.nasa.gov/?v=${(ev(j, "lon") - 1).toFixed(2)},${(la - 0.6).toFixed(2)},${(ev(j, "lon") + 1).toFixed(2)},${(la + 0.6).toFixed(2)}">Open in NASA Worldview</a> <span id="copyMsg" class="mut" role="status"></span></p>`;
  $("copyBtn").onclick = () => copyText(siteSummary(), "copyMsg", "Summary copied."); $("printBtn").onclick = printSite;
  $("linkBtn").onclick = () => { writeHash(); copyText(location.href, "copyMsg", "Link copied."); };
  $("siteEyebrow").innerHTML = `${PURPOSES[S.purpose].name} · for <span class="mc">${esc($("st1").textContent)}</span>`;
  $("siteTitle").textContent = (S.probe && j === probeJOf() ? "Your place: " : "") + (pl.country || "Unnamed land");
  $("siteSub").textContent = [coord(j), pl.town ? `nearest town ${pl.town}, about ${pl.km.toLocaleString()} km` : "", altOf(j) != null ? `${altOf(j).toLocaleString()} m` : ""].filter(Boolean).join(" · ");
  $("siteNote").textContent = o.note || ""; siteChips(j);
  $("capE").innerHTML = `<i class="edot"></i>Earth: ${esc(earthLabel(j))}`;
  markPins(); writeHash();
  loadEarthPatch(j); sunEarth(j); draw3d(); showSat(j);
  if (UI.open == "site") requestAnimationFrame(() => UI.fit());
}

/* ---------- 3D patches ---------- */
const V = {};
function init3d() {
  for (const id of ["c3m", "c3e"]) { const cv = $(id); let r; try { r = new THREE.WebGLRenderer({canvas: cv, antialias: true}); } catch (e) { $(id == "c3m" ? "cvsM" : "cvsE").textContent = "3D view not available in this browser (WebGL is off)."; continue; }
    const sc = new THREE.Scene(), cam = new THREE.PerspectiveCamera(35, 1, 0.1, 200); cam.up.set(0, 0, 1);
    cam.position.set(0, -17, 9.5); cam.lookAt(0, 0, 0.5); sc.add(new THREE.AmbientLight(0xffffff, 0.55)); const dl = new THREE.DirectionalLight(0xffffff, 0.9); dl.position.set(-6, -4, 8); sc.add(dl);
    const grp = new THREE.Group(); sc.add(grp); V[id] = {r, sc, cam, grp, z: null, cv};
    let drag = null; cv.onpointerdown = e => { drag = [e.clientX, e.clientY]; cv.setPointerCapture(e.pointerId); };
    cv.onpointermove = e => { if (!drag) return; S.rot.z += (e.clientX - drag[0]) * 0.01; S.rot.x = Math.max(-1.75, Math.min(-0.64, S.rot.x + (e.clientY - drag[1]) * 0.006)); drag = [e.clientX, e.clientY]; render3d(); };
    cv.onpointerup = () => drag = null; }
  if (!V.c3m) V.c3m = {z: null}; if (!V.c3e) V.c3e = {z: null};
  const setCol = v => { S.col = v; document.querySelectorAll("input[name=col],input[name=col2]").forEach(r => r.checked = r.value == v); draw3d(); syncCmp(); };
  document.querySelectorAll("input[name=col],input[name=col2]").forEach(r => r.onchange = () => setCol(r.value));
}
function moonPatch() { const n = 26, z = new Float32Array(n * n), D = MAN.moon.dem, c0 = Math.round((S.spot.x - 5000 + D.half_m) / D.res_m), r0 = Math.round((D.half_m - (S.spot.y + 5000)) / D.res_m);
  for (let r = 0; r < n; r++) for (let c = 0; c < n; c++) { const rr = Math.min(D.n - 1, Math.max(0, r0 + r)), cc = Math.min(D.n - 1, Math.max(0, c0 + c)); z[r * n + c] = DEM[rr * D.n + cc]; } return {z, n}; }
const ramp = t => { t = clip(t); const s = [[13, 8, 135], [126, 3, 168], [204, 71, 120], [248, 149, 64], [240, 249, 33]], x = t * 4, i = Math.min(3, Math.floor(x)), f = x - i; return s[i].map((v, k) => (v + (s[i + 1][k] - v) * f) / 255); };
function buildMesh(v) {
  if (!v.grp) return; v.grp.clear(); v.span = 0; if (!v.z) return; const {z, n} = v.z, g = new THREE.PlaneGeometry(10, 10, n - 1, n - 1), pos = g.attributes.position, col = new Float32Array(n * n * 3), cell = 10000 / (n - 1);
  let mn = Infinity, mx = -Infinity; for (const h of z) { if (h < mn) mn = h; if (h > mx) mx = h; }
  for (let r = 0; r < n; r++) for (let c = 0; c < n; c++) { const i = r * n + c; pos.setZ(i, (z[i] - (mn + mx) / 2) / 1000 * 2);
    let t; if (S.col == "sun" && v.H) { const q = (SUN.a * 51 + Math.round(r * 50 / (n - 1))) * 51 + Math.round(c * 50 / (n - 1)), lit = Math.tan(SUN.el * Math.PI / 180) > v.H[q]; col[i * 3] = lit ? 0.93 : 0.07; col[i * 3 + 1] = lit ? 0.88 : 0.09; col[i * 3 + 2] = lit ? 0.74 : 0.16; continue; }
    if (S.col == "height") t = (z[i] - mn) / Math.max(mx - mn, 1); else { const dx = (z[r * n + Math.min(n - 1, c + 1)] - z[r * n + Math.max(0, c - 1)]) / (2 * cell), dy = (z[Math.min(n - 1, r + 1) * n + c] - z[Math.max(0, r - 1) * n + c]) / (2 * cell); t = Math.atan(Math.hypot(dx, dy)) * 180 / Math.PI / 30; }
    const k = ramp(t); col[i * 3] = k[0]; col[i * 3 + 1] = k[1]; col[i * 3 + 2] = k[2]; }
  g.setAttribute("color", new THREE.BufferAttribute(col, 3)); g.computeVertexNormals(); v.span = (mx - mn) / 1000 * 2;
  v.grp.add(new THREE.Mesh(g, new THREE.MeshLambertMaterial({vertexColors: true, side: THREE.DoubleSide})));
  const zb = -(mx - mn) / 1000 - 0.15, fr = new THREE.BufferGeometry().setFromPoints([[-5, -5], [5, -5], [5, 5], [-5, 5], [-5, -5]].map(p => new THREE.Vector3(p[0], p[1], zb)));
  v.grp.add(new THREE.Line(fr, new THREE.LineBasicMaterial({color: 0x4b5563})));
  const na = new THREE.BufferGeometry().setFromPoints([new THREE.Vector3(0, 5, zb), new THREE.Vector3(0, 6.2, zb), new THREE.Vector3(-0.35, 5.7, zb), new THREE.Vector3(0, 6.2, zb), new THREE.Vector3(0.35, 5.7, zb)]);
  v.grp.add(new THREE.Line(na, new THREE.LineBasicMaterial({color: 0x9aa4b2})));
  if (S.col == "sun" && v.H) { const az = SUN.a * 2 * Math.PI / NAZ, e = SUN.el * Math.PI / 180, zt = (mx - mn) / 1000 + 0.3, d = [Math.sin(az) * Math.cos(e), Math.cos(az) * Math.cos(e), Math.sin(e) * 2];
    v.grp.add(new THREE.Line(new THREE.BufferGeometry().setFromPoints([new THREE.Vector3(0, 0, zt), new THREE.Vector3(d[0] * 6, d[1] * 6, zt + d[2] * 6)]), new THREE.LineBasicMaterial({color: 0xF2B04C}))); }
}
function draw3d() { if (S.spot) V.c3m.z = moonPatch(); V.c3m.H = SUN.moon && SUN.moon.H; V.c3e.H = SUN.earth && SUN.earth.j === S.site ? SUN.earth.H : null; buildMesh(V.c3m); buildMesh(V.c3e); render3d(); }
function render3d() { for (const id in V) { const v = V[id]; if (!v.r) continue; const w = v.cv.clientWidth, h = v.cv.clientHeight; if (!w || !h) continue; v.r.setPixelRatio(window.devicePixelRatio); v.r.setSize(w, h, false); v.cam.aspect = w / h; v.cam.updateProjectionMatrix(); v.grp.rotation.set(0, 0, S.rot.z); const span = Math.max(V.c3m.span || 0, V.c3e.span || 0), dist = 19 * Math.max(1, 1.45 / (w / h)) * Math.max(1, (10 + span * 1.6) / 12), el = -S.rot.x - 0.5; v.cam.position.set(0, -dist * Math.cos(el), dist * Math.sin(el)); v.cam.lookAt(0, 0, 0); v.r.render(v.sc, v.cam); } }
/* Compare overlay captions and controls follow the same sun and colour state as the panel. */
function syncCmp() {
  if (!UI.cmpOpen) return; const m = SUN.moon, e = SUN.earth && SUN.earth.j === S.site ? SUN.earth : null, sun = S.col == "sun";
  $("cmpCapM").innerHTML = $("capM").innerHTML + (sun && m && m.H ? ` · <b>${pc(shadeAt(m.H))}</b> in shadow` : "");
  $("cmpCapE").innerHTML = $("capE").innerHTML + (sun && e && e.H ? ` · <b>${pc(shadeAt(e.H))}</b> in shadow` : "");
  document.querySelectorAll("input[name=col2]").forEach(r => r.checked = r.value == S.col);
  $("cSunEl").value = SUN.el; $("cSunAz").value = SUN.a; $("cSunElV").textContent = SUN.el.toFixed(1) + "°";
}
/* ---------- Sun and shadow simulation ----------
   For every 200 m cell of the 10 km window, find the horizon in 16 directions by walking outwards over the elevation data, allowing for the
   curvature of the body. A cell is in shadow when the centre of the Sun is below its horizon. Same code for Moon and Earth. */
const NAZ = 16, SUN = {el: 3, a: 0, lim: 15, moon: null, earth: null, demP: null}, ELS = Array.from({length: 40}, (_, i) => (i + 1) * 0.5);
const STEPS = (() => { const s = new Set(); for (let i = 1; i < 40; i++) s.add(i); for (let k = 0; k < 45; k++) s.add(Math.round(40 * Math.pow(750 / 40, k / 44))); return [...s].sort((a, b) => a - b); })();
function horizons(D, N, r0, c0, n, res, radius, maxStep) {
  const out = new Float32Array(NAZ * n * n).fill(-9);
  for (let a = 0; a < NAZ; a++) { const az = 2 * Math.PI * a / NAZ, dc = Math.sin(az), dr = -Math.cos(az);
    for (const s of STEPS) { if (s > maxStep) break; const dist = s * res, drop = dist * dist / (2 * radius);
      for (let r = 0; r < n; r++) for (let c = 0; c < n; c++) { const R = Math.round(r0 + r + dr * s), C = Math.round(c0 + c + dc * s); if (R < 0 || R >= N || C < 0 || C >= N) continue;
        const t = (D[R * N + C] - D[(r0 + r) * N + c0 + c] - drop) / dist, o = (a * n + r) * n + c; if (t > out[o]) out[o] = t; } } }
  return out;
}
function shadeCurve(H) { const m = H.length; return ELS.map(e => { const t = Math.tan(e * Math.PI / 180); let k = 0; for (let i = 0; i < m; i++) if (H[i] >= t) k++; return k / m; }); }
function shadeAt(H) { const t = Math.tan(SUN.el * Math.PI / 180), n = 2601; let k = 0; for (let i = 0; i < n; i++) if (H[SUN.a * n + i] >= t) k++; return k / n; }
async function sunMoon() {
  const sp = S.spot, d = MAN.moon.dem200; SUN.moon = null; renderSun(); if (!d) return;
  try { SUN.demP = SUN.demP || bin("data/moon_dem200.bin", Int16Array); const D = await SUN.demP; if (S.spot !== sp) return;
    const r0 = Math.floor((d.half_m - sp.y) / d.res_m) - 25, c0 = Math.floor((sp.x + d.half_m) / d.res_m) - 25;
    if (r0 < 0 || c0 < 0 || r0 + 51 > d.n || c0 + 51 > d.n) { SUN.moon = {err: "This spot is at the edge of the elevation map, so the sun test is not available here."}; renderSun(); return; }
    const H = horizons(D, d.n, r0, c0, 51, d.res_m, 1737400, 750);
    SUN.moon = {H, T: tests(cut(D, d.n, r0, c0), 1737400), curve: shadeCurve(H), maxEl: 90 - Math.abs(mv(sp.i, "lat")) + 1.54, far: Math.hypot(sp.x, sp.y) > 200000};
  } catch (e) { SUN.demP = null; SUN.moon = {err: "Could not load the lunar elevation file for the sun test."}; }
  renderSun(); if (S.col == "sun") draw3d();
}
async function sunEarth(j) {
  SUN.earth = {j, loading: true}; renderSun();
  try { const lat = ev(j, "lat"), lon = ev(j, "lon"), N = 601, res = 200, zoom = Math.max(5, Math.min(11, Math.round(Math.log2(156543 * Math.cos(lat * Math.PI / 180) / res)))), T = 2 ** zoom, D = new Float32Array(N * N), px = new Float64Array(N * N * 2), need = new Set();
    for (let r = 0; r < N; r++) { const la = lat + (300 - r) * res / 111320, s = Math.sin(la * Math.PI / 180), Y = (0.5 - Math.log((1 + s) / (1 - s)) / (4 * Math.PI)) * T, k = res / (111320 * Math.cos(la * Math.PI / 180));
      for (let c = 0; c < N; c++) { const X = (lon + (c - 300) * k + 180) / 360 * T, o = (r * N + c) * 2; px[o] = X; px[o + 1] = Y; need.add(Math.floor(X) + "/" + Math.floor(Y)); } }
    const data = {}; await Promise.all([...need].map(async k => { const [x, y] = k.split("/").map(Number); data[k] = await tile(zoom, ((x % T) + T) % T, y); }));
    if (S.site !== j) return;
    for (let i = 0; i < N * N; i++) { const X = px[i * 2], Y = px[i * 2 + 1], d = data[Math.floor(X) + "/" + Math.floor(Y)], u = Math.min(255, Math.floor((X - Math.floor(X)) * 256)), v = Math.min(255, Math.floor((Y - Math.floor(Y)) * 256)), o = (v * 256 + u) * 4; D[i] = d[o] * 256 + d[o + 1] + d[o + 2] / 256 - 32768; }
    if (zoom < 11) { const T2 = 2048, need2 = new Set(), q = [];      // the middle 30 km again from zoom 11: coarser zooms are smoothed and would hide the local hills
      for (let r = 225; r <= 375; r++) { const la = lat + (300 - r) * res / 111320, sn = Math.sin(la * Math.PI / 180), Y = (0.5 - Math.log((1 + sn) / (1 - sn)) / (4 * Math.PI)) * T2, k = res / (111320 * Math.cos(la * Math.PI / 180));
        for (let c = 225; c <= 375; c++) { const X = (lon + (c - 300) * k + 180) / 360 * T2; q.push([r * N + c, X, Y]); need2.add(Math.floor(X) + "/" + Math.floor(Y)); } }
      const d2 = {}; await Promise.all([...need2].map(async k => { const [x, y] = k.split("/").map(Number); d2[k] = await tile(11, ((x % T2) + T2) % T2, y); })); if (S.site !== j) return;
      for (const [i, X, Y] of q) { const d = d2[Math.floor(X) + "/" + Math.floor(Y)], u = Math.min(255, Math.floor((X - Math.floor(X)) * 256)), v = Math.min(255, Math.floor((Y - Math.floor(Y)) * 256)), o = (v * 256 + u) * 4; D[i] = d[o] * 256 + d[o + 1] + d[o + 2] / 256 - 32768; } }
    const H = horizons(D, N, 275, 275, 51, res, 6371000, 275); SUN.earth = {j, H, T: tests(cut(D, N, 275, 275), 6371000), curve: shadeCurve(H)};
  } catch (e) { if (S.site !== j) return; SUN.earth = {j, err: "Earth terrain tiles are unreachable (or there is no coverage here), so the Earth side of this test is not available."}; }
  renderSun(); if (S.col == "sun") draw3d();
}
const DIRS = ["north", "north-north-east", "north-east", "east-north-east", "east", "east-south-east", "south-east", "south-south-east", "south", "south-south-west", "south-west", "west-south-west", "west", "west-north-west", "north-west", "north-north-west"];
function initSun() {
  $("slopeLim").oninput = e => { SUN.lim = +e.target.value; renderSun(); };
  const setSun = (el, a) => { if (el != null) SUN.el = el; if (a != null) SUN.a = a; $("sunEl").value = SUN.el; $("sunAz").value = SUN.a; renderSun(); if (S.col == "sun") draw3d(); syncCmp(); };
  $("sunEl").oninput = e => setSun(+e.target.value, null); $("sunAz").oninput = e => setSun(null, +e.target.value);
  $("cSunEl").oninput = e => setSun(+e.target.value, null); $("cSunAz").oninput = e => setSun(null, +e.target.value);
}
function renderSun() {
  const m = SUN.moon, e = SUN.earth && SUN.earth.j === S.site ? SUN.earth : null, W = 520, Hh = 190, L = 34, B = 24, x = v => L + v / 20 * (W - L - 6), y = v => 6 + (1 - v) * (Hh - B - 6);
  $("sunLab").innerHTML = `Sun <b>${SUN.el.toFixed(1)}°</b> above the horizon, shining from the <b>${DIRS[SUN.a]}</b> side of the patch`;
  const line = (c, col) => `<polyline points="${ELS.map((el, i) => x(el).toFixed(1) + "," + y(c[i]).toFixed(1)).join(" ")}" fill="none" stroke="${col}" stroke-width="2"/>`;
  let g = ""; for (const t of [0, 5, 10, 15, 20]) g += `<text x="${x(t) - (t == 20 ? 18 : 6)}" y="${Hh - 6}" font-size="11" fill="#9aa4b2">${t}°</text>`; for (const t of [0, 0.5, 1]) g += `<text x="2" y="${y(t) + 4}" font-size="11" fill="#9aa4b2">${t * 100}%</text><line x1="${L}" x2="${W - 6}" y1="${y(t)}" y2="${y(t)}" stroke="#2b3340"/>`;
  if (m && m.curve) g += `<rect x="${x(0)}" y="6" width="${x(Math.min(20, m.maxEl)) - x(0)}" height="${Hh - B - 6}" fill="#8CC8F5" opacity=".08"/>` + line(m.curve, "#8CC8F5");
  if (e && e.curve) g += line(e.curve, "#F2B04C");
  else if (e && e.loading) g += `<text x="${x(10)}" y="${y(0.5)}" font-size="12" fill="#F2B04C" text-anchor="middle">Earth: loading terrain…</text>`;
  g += `<line x1="${x(SUN.el)}" x2="${x(SUN.el)}" y1="6" y2="${Hh - B}" stroke="#e6e9ee" stroke-dasharray="3 3"/>`;
  $("sunChart").innerHTML = `<svg viewBox="0 0 ${W} ${Hh}" style="width:100%;height:auto" role="img" aria-label="Share of each patch in shadow against sun height">${g}</svg>`;
  let t = "";
  if (!m) t += "Moon: calculating…<br>"; else if (m.err) t += m.err + "<br>"; else t += `<span class="mc">Moon spot</span>: <b>${pc(shadeAt(m.H))}</b> of the patch in shadow with this sun. The Sun never rises above about ${m.maxEl.toFixed(1)}° here (shaded band).${m.far ? " This spot is more than 200 km from the pole, where part of the far horizon lies outside our elevation map, so shadow may be under-estimated." : ""}<br>`;
  if (S.site == null) t += "Earth: select a site in the list."; else if (!e || e.loading) t += `<span class="ec">Earth</span>: loading terrain (open elevation tiles)…`; else if (e.err) t += `${e.err} <button class="linkbtn" data-retry-sun>Retry</button>`; else { t += `<span class="ec">Earth site</span>: <b>${pc(shadeAt(e.H))}</b> in shadow with the same sun.`;
    if (m && m.curve) { let s = 0, k = 0; ELS.forEach((el, i) => { if (el <= m.maxEl) { s += Math.abs(m.curve[i] - e.curve[i]); k++; } }); t += `<br>Over the sun heights that occur at this lunar spot, the shadowed share of the two patches differs by <b>${Math.round(s / k * 100)} percentage points</b> on average (all sun directions).`; } }
  if (m && m.maxEl && S.site != null && E && S.site < E.n) { const hrs = lowSunHours(ev(S.site, "lat"), m.maxEl), mxh = Math.max(...hrs, 0.1), a = altAny(S.site);
    t += `<br><br>When to go for natural light: hours per day the real Sun at this Earth site is between the horizon and ${m.maxEl.toFixed(1)}° (the range at this lunar spot).<span class="months">${hrs.map((h, q) => `<span><i style="height:${Math.round(h / mxh * 26) + 1}px"></i>${MON[q]}<br>${h.toFixed(1)}</span>`).join("")}</span>${a != null && a > 3500 ? `This site is about ${(Math.round(a / 100) * 100).toLocaleString()} m above sea level; crews would need to acclimatise.` : ""}`; }
  $("sunTxt").innerHTML = t;
  const row = (nm, col, T) => { const q = reach(T.slope, SUN.lim); return `<span style="color:${col}">${nm}</span><span>${pc(q.under)}</span><span>${pc(q.joined)}</span><span>${pc(T.visMean)}</span><span>${pc(T.visBest)}</span>`; };
  const pend = (nm, col, s) => `<span style="color:${col}">${nm}</span>` + `<span class="nd">${s}</span>`.repeat(4);
  $("reachTxt").innerHTML = `<span></span><span>ground under ${SUN.lim}°</span><span>largest joined-up area under ${SUN.lim}°</span><span>patch seen from a typical point</span><span>patch seen from the best point</span>`
    + (m && m.T ? row("Moon spot", "#8CC8F5", m.T) : pend("Moon spot", "#8CC8F5", m && m.err ? "no data" : "loading…"))
    + (S.site == null ? "" : e && e.T ? row("Earth site", "#F2B04C", e.T) : pend("Earth site", "#F2B04C", e && e.err ? "no data" : "loading…"));
  $("reachNote").innerHTML = e && e.err ? `${e.err} <button class="linkbtn" data-retry-sun>Retry</button>` : "";
  syncCmp();
}
/* Reach and line of sight on the same 51 x 51 grid of 200 m cells. */
function cut(D, N, r0, c0) { const z = new Float32Array(2601); for (let r = 0; r < 51; r++) for (let c = 0; c < 51; c++) z[r * 51 + c] = D[(r0 + r) * N + c0 + c]; return z; }
function tests(z, radius) { const n = 51, slope = new Float32Array(n * n), cl = v => Math.max(0, Math.min(n - 1, v));
  for (let r = 0; r < n; r++) for (let c = 0; c < n; c++) { const dx = (z[r * n + cl(c + 1)] - z[r * n + cl(c - 1)]) / ((cl(c + 1) - cl(c - 1)) * 200), dy = (z[cl(r + 1) * n + c] - z[cl(r - 1) * n + c]) / ((cl(r + 1) - cl(r - 1)) * 200); slope[r * n + c] = Math.atan(Math.hypot(dx, dy)) * 180 / Math.PI; }
  const vis = []; for (let a = 0; a < 5; a++) for (let b = 0; b < 5; b++) { const r0 = 5 + a * 10, c0 = 5 + b * 10, zo = z[r0 * n + c0] + 2; let k = 0;      // observer 2 m above the ground at 25 evenly spaced points
    for (let r = 0; r < n; r++) for (let c = 0; c < n; c++) { const dr = r - r0, dc = c - c0, m = Math.max(Math.abs(dr), Math.abs(dc)); if (!m) { k++; continue; }
      const dt = Math.hypot(dr, dc) * 200, zt = z[r * n + c] - dt * dt / (2 * radius); let ok = true;
      for (let q = 1; q < m; q++) { const f = q / m, d = dt * f, zp = z[Math.round(r0 + dr * f) * n + Math.round(c0 + dc * f)] - d * d / (2 * radius); if (zp > zo + (zt - zo) * f) { ok = false; break; } }
      if (ok) k++; } vis.push(k / (n * n)); }
  vis.sort((a, b) => a - b); return {slope, visMean: vis[12], visBest: vis[24]};
}
function reach(slope, lim) { const n = 51, lab = new Int8Array(n * n); let under = 0, best = 0;
  for (let i = 0; i < n * n; i++) { if (slope[i] > lim) continue; under++; if (lab[i]) continue; let size = 0; const st = [i]; lab[i] = 1;
    while (st.length) { const p = st.pop(), r = (p / n) | 0, c = p % n; size++; for (const [a, b] of [[r - 1, c], [r + 1, c], [r, c - 1], [r, c + 1]]) { if (a < 0 || b < 0 || a >= n || b >= n) continue; const q = a * n + b; if (!lab[q] && slope[q] <= lim) { lab[q] = 1; st.push(q); } } }
    if (size > best) best = size; }
  return {under: under / (n * n), joined: best / (n * n)};
}
/* Earth display patch from open Terrarium elevation tiles (AWS Open Data). Display only. A failed tile is forgotten so Retry can fetch it again. */
const tileCache = new Map();
function tile(z, x, y) { const k = `${z}/${x}/${y}`; if (!tileCache.has(k)) { const p = new Promise((res, rej) => { const im = new Image(); im.crossOrigin = "anonymous"; im.onload = () => { const c = document.createElement("canvas"); c.width = c.height = 256; const cx = c.getContext("2d", {willReadFrequently: true}); cx.drawImage(im, 0, 0); res(cx.getImageData(0, 0, 256, 256).data); }; im.onerror = rej; im.src = `https://s3.amazonaws.com/elevation-tiles-prod/terrarium/${k}.png`; });
  p.catch(() => tileCache.delete(k)); tileCache.set(k, p); } return tileCache.get(k); }
async function loadEarthPatch(j) {
  const lat = ev(j, "lat"), lon = ev(j, "lon"), n = 26, z = new Float32Array(n * n), zoom = 11, N = 2 ** zoom;   // below zoom 10 these tiles come from a much coarser, smoothed elevation source
  const dLat = 10 / 111.32, dLon = 10 / (111.32 * Math.cos(lat * Math.PI / 180)), px = [];
  for (let r = 0; r < n; r++) for (let c = 0; c < n; c++) { const la = lat + dLat / 2 - dLat * r / (n - 1), lo = lon - dLon / 2 + dLon * c / (n - 1), X = (lo + 180) / 360 * N, s = Math.sin(la * Math.PI / 180), Y = (0.5 - Math.log((1 + s) / (1 - s)) / (4 * Math.PI)) * N; px.push([X, Y]); }
  V.c3e.z = null; V.c3e.alt = null; V.c3e.j = j; buildMesh(V.c3e); render3d(); $("cvsE").textContent = "Loading terrain…";
  try { const need = new Map(); px.forEach(([X, Y]) => need.set(Math.floor(X) + "/" + Math.floor(Y), 1)); const data = {};
    await Promise.all([...need.keys()].map(async k => { const [x, y] = k.split("/").map(Number); data[k] = await tile(zoom, ((x % N) + N) % N, y); }));
    if (S.site !== j) return;
    px.forEach(([X, Y], i) => { const d = data[Math.floor(X) + "/" + Math.floor(Y)], u = Math.min(255, Math.floor((X % 1) * 256)), v = Math.min(255, Math.floor((Y % 1) * 256)), o = (v * 256 + u) * 4; z[i] = d[o] * 256 + d[o + 1] + d[o + 2] / 256 - 32768; });
    let sum = 0; for (const h of z) sum += h; V.c3e.alt = sum / z.length; V.c3e.z = {z, n}; $("cvsE").textContent = "";
    $("capE").innerHTML = `<i class="edot"></i>Earth: ${esc(earthLabel(j))} · about ${(Math.round(V.c3e.alt / 10) * 10).toLocaleString()} m`; buildMesh(V.c3e); render3d(); renderSun(); siteChips(j);
  } catch (e) { if (S.site === j) $("cvsE").innerHTML = `<div>3D terrain not available (tile service unreachable).<br><button class="linkbtn" data-retry-3d>Retry</button></div>`; }
}
init().catch(e => { document.body.insertAdjacentHTML("beforeend", `<div class="fatal" role="alert"><div><h2>Could not load the data</h2><p class="mut">${esc(e && e.message || e)}</p><p class="mut">Reload the page. If you opened the file directly from disk, open it through the local server instead (scripts\\open_app.bat).</p></div></div>`); });
