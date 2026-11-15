/* Moon Analog Finder. All scoring runs in the browser on precomputed NASA/ESA-derived data. */
const $ = id => document.getElementById(id), f1 = v => v.toFixed(1), f2 = v => v.toFixed(2), pc = v => Math.round(v * 100) + "%";
const BINS = 46, T_RANGE = 200, DARK_H = 120, H_RANGE = 0.4, RET_RANGE = 0.5;
const FACT = {slope: "Slope match", classes: "Steep ground share (10 and 20 deg)", scale: "Roughness across scales", lowsun: "Low sun angle", dark: "Long darkness", t_cold: "Cold", t_peak: "Peak temperature", bare: "Bare surface"};
const PURPOSES = {
  mobility: {name: "Rover driving", desc: "Same steepness and same kind of terrain, on bare ground", gate: true, w: {slope: .5, scale: .5}},
  shadow: {name: "Shadow work and crater access", desc: "Steep access, low sun and cold", gate: true, w: {classes: .35, lowsun: .35, t_cold: .30}},
  darkness: {name: "Power and darkness survival", desc: "120+ hours of darkness, cold, low sun", gate: false, w: {dark: .45, t_cold: .35, lowsun: .20}}
};
const S = {purpose: "mobility", spot: null, site: null, col: "slope", rot: {x: -1.05, z: 0.6}};
let MAN, E, M, DEM, moonMap, earthMap, spotRect, earthMarkers = [], scores = null, topSites = [];

const DATA_V = "6";  // bump whenever files in data/ or layers/ change, so browsers do not reuse old copies
async function bin(u, T) { return new T(await (await fetch(u + "?v=" + DATA_V)).arrayBuffer()); }
async function init() {
  MAN = await (await fetch("data/manifest.json?v=" + DATA_V, {cache: "no-cache"})).json();
  const [eh, em, mh, mm, dem] = await Promise.all([bin("data/earth_hist.bin", Uint8Array), bin("data/earth_meta.bin", Float32Array),
    bin("data/moon_hist.bin", Uint8Array), bin("data/moon_meta.bin", Float32Array), bin("data/moon_dem400.bin", Int16Array)]);
  E = {n: MAN.earth.n, hist: eh, meta: em, nc: MAN.earth.cols.length, c: Object.fromEntries(MAN.earth.cols.map((k, i) => [k, i]))};
  M = {n: MAN.moon.n, hist: mh, meta: mm, nc: MAN.moon.cols.length, c: Object.fromEntries(MAN.moon.cols.map((k, i) => [k, i])), idx: new Map()};
  for (let i = 0; i < M.n; i++) M.idx.set(mv(i, "x") + "," + mv(i, "y"), i);
  DEM = dem;
  $("libinfo").textContent = `${E.n.toLocaleString()} Earth windows from ${MAN.squares_scanned.toLocaleString()} map squares · ${M.n.toLocaleString()} lunar spots`;
  buildMoonMap(); buildEarthMap(); buildPurposes(); init3d();
  document.querySelectorAll("input[name=col]").forEach(r => r.onchange = () => { S.col = r.value; draw3d(); });
  const h = location.hash.slice(1).split(",");
  if (h.length >= 3) { S.purpose = PURPOSES[h[2]] ? h[2] : "mobility"; buildPurposes(); selectSpot(+h[0], +h[1]); }
}
const mv = (i, k) => M.meta[i * M.nc + M.c[k]], ev = (i, k) => E.meta[i * E.nc + E.c[k]];

/* ---------- Moon map ---------- */
function buildMoonMap() {
  const B = [[-304, -304], [304, 304]];
  moonMap = L.map("moonmap", {crs: L.CRS.Simple, minZoom: -0.5, maxZoom: 4, zoomSnap: 0.5, attributionControl: false, maxBounds: [[-340, -340], [340, 340]]});
  L.imageOverlay("layers/base.png?v=" + DATA_V, B).addTo(moonMap); moonMap.fitBounds([[-160, -160], [160, 160]]);
  const defs = [["slope", "Slope"], ["sunlight", "Average sunlight"], ["shadow", "Permanent shadow"], ["temperature", "Peak temperature"]], lay = {};
  defs.forEach(([k, label]) => {
    lay[k] = L.imageOverlay(`layers/${k}.png?v=${DATA_V}`, B, {opacity: 0.85});
    const b = document.createElement("button"); b.className = "chip"; b.textContent = label;
    b.onclick = () => { const on = moonMap.hasLayer(lay[k]); on ? moonMap.removeLayer(lay[k]) : lay[k].addTo(moonMap); b.classList.toggle("on", !on); if (spotRect) spotRect.bringToFront(); };
    $("layers").appendChild(b);
  });
  L.circleMarker([0, 0], {radius: 3, color: "#fff"}).addTo(moonMap).bindTooltip("South Pole");
  MAN.regions.forEach(r => {
    L.circleMarker([r.y / 1000, r.x / 1000], {radius: 5, color: "#5cc8ff"}).addTo(moonMap).bindTooltip(r.name + " (approx.)").on("click", e => { L.DomEvent.stop(e); selectSpot(r.x, r.y, r.name); });
    const b = document.createElement("button"); b.className = "chip"; b.textContent = r.name; b.onclick = () => selectSpot(r.x, r.y, r.name); $("regions").appendChild(b);
  });
  $("regions").className = "reg";
  moonMap.on("click", e => selectSpot(e.latlng.lng * 1000, e.latlng.lat * 1000));
}
function selectSpot(x, y, name) {
  const gx = Math.round(x / 5000) * 5000, gy = Math.round(y / 5000) * 5000, i = M.idx.get(gx + "," + gy);
  if (i === undefined) { document.querySelectorAll("#spot .nodata").forEach(e => e.remove()); $("spot").insertAdjacentHTML("afterbegin", '<div class="flag bad nodata">No data at that point. The map covers 80 to 90 degrees south; pick a spot inside that circle.</div>'); return; }
  S.spot = {i, x: gx, y: gy, name: name || null}; S.site = null;
  if (spotRect) moonMap.removeLayer(spotRect);
  spotRect = L.rectangle([[gy / 1000 - 5, gx / 1000 - 5], [gy / 1000 + 5, gx / 1000 + 5]], {color: "#4ade80", weight: 2, fill: false}).addTo(moonMap);
  renderSpot(); run();
}
function lonTxt(l) { return Math.abs(l).toFixed(1) + "° " + (l >= 0 ? "E" : "W"); }
function renderSpot() {
  const i = S.spot.i, g = k => mv(i, k), psr = g("psr_share");
  const near = MAN.regions.map(r => ({r, d: Math.hypot(r.x - S.spot.x, r.y - S.spot.y) / 1000})).sort((a, b) => a.d - b.d)[0];
  const title = S.spot.name || (near.d < 12 ? `Near ${near.r.name}` : "Unnamed spot");
  let flags = "";
  if (psr > 0.5) flags += `<div class="flag">Mostly permanent shadow (${pc(psr)}). Not a landing spot; relevant for shadow work and ice prospecting.</div>`;
  else if (g("illum_max") > 0.6) flags += `<div class="flag ok">Has well-lit ground: best point is sunlit ${pc(g("illum_max"))} of the time.</div>`;
  if (!S.spot.name && near.d >= 12) flags += `<div class="flag ok">Not a named Artemis III region. Scored from the same data as the named ones. Nearest: ${near.r.name}, ${near.d.toFixed(0)} km away.</div>`;
  const h = histOf(M.hist, i), c = classes(h);
  $("spot").innerHTML = `<h3 style="margin-topSites:0;color:var(--tx);font-size:16px">${title}</h3>
   <div class="mut">${Math.abs(g("lat")).toFixed(2)}° S, ${lonTxt(g("lon"))} · 10 km window${S.spot.name ? " · centre approximate" : ""}</div>${flags}
   <div class="kv"><span>Median slope</span><span>${f1(g("slope_p50"))}°</span><span>Steepest tenth of ground</span><span>over ${f1(g("slope_p90"))}°</span>
   <span>Ground under 5° / 5 to 10°</span><span>${pc(c[0])} / ${pc(c[1])}</span><span>Ground 10 to 20° / over 20°</span><span>${pc(c[2])} / ${pc(c[3])}</span>
   <span>Slope at 320 m / scaling number</span><span>${f1(g("slope320_p50"))}° / ${f2(g("hurst"))}</span><span>Height range</span><span>${g("relief_m").toFixed(0)} m</span><span>Average sunlight</span><span>${pc(g("illum_mean"))}</span>
   <span>Permanent shadow</span><span>${pc(psr)}</span><span>Average temperature</span><span>${isNaN(g("t_avg")) ? "no data" : g("t_avg").toFixed(0) + " K"}</span>
   <span>Peak temperature</span><span>${isNaN(g("t_max")) ? "no data" : g("t_max").toFixed(0) + " K"}</span><span>Highest sun angle</span><span>${f1(90 - Math.abs(g("lat")) + 1.54)}°</span></div>
   <p class="mut" style="margin-bottom:4px">Other regions:</p><div class="reg" id="regions2"></div>`;
  MAN.regions.forEach(r => { const b = document.createElement("button"); b.className = "chip"; b.textContent = r.name; b.onclick = () => selectSpot(r.x, r.y, r.name); $("regions2").appendChild(b); });
  $("capM").textContent = `Moon: ${title}`;
}

/* ---------- scoring ---------- */
function histOf(H, i) { const o = new Float32Array(BINS); for (let b = 0; b < BINS; b++) o[b] = H[i * BINS + b] / 255; return o; }
function classes(h) { const c = [0, 0, 0, 0]; for (let b = 0; b < BINS; b++) c[b < 5 ? 0 : b < 10 ? 1 : b < 20 ? 2 : 3] += h[b]; return c; }
const clip = v => v < 0 ? 0 : v > 1 ? 1 : v, rat = (a, b) => 1 - Math.abs(a - b) / Math.max(a, b, 1e-9);
function foms(j, m) {
  let d = 0, c = [0, 0, 0, 0];
  for (let b = 0; b < BINS; b++) { const v = E.hist[j * BINS + b] / 255; d += Math.abs(v - m.h[b]); c[b < 5 ? 0 : b < 10 ? 1 : b < 20 ? 2 : 3] += v; }
  const dc = Math.abs(c[0] - m.c[0]) + Math.abs(c[1] - m.c[1]) + Math.abs(c[2] - m.c[2]) + Math.abs(c[3] - m.c[3]);
  const nd = ev(j, "ndvi"), tn = ev(j, "t_night_min"), td = ev(j, "t_day_max");
  return {slope: clip(1 - 0.5 * d), classes: clip(1 - 0.5 * dc), scale: 0.5 * (clip(1 - Math.abs(ev(j, "hurst") - m.H) / H_RANGE) + clip(1 - Math.abs(ev(j, "slope320_p50") / Math.max(ev(j, "slope_p50"), 1e-6) - m.ret) / RET_RANGE)),
    bare: isNaN(nd) ? 1 : clip(1 - (nd - 0.2) / 0.4), lowsun: clip(ev(j, "lowsun")), dark: clip(ev(j, "dark_h") / DARK_H),
    t_cold: isNaN(tn) || isNaN(m.tavg) ? 0 : clip(1 - Math.abs(tn - m.tavg) / T_RANGE), t_peak: isNaN(td) || isNaN(m.tmax) ? 0 : clip(1 - Math.abs(td - m.tmax) / T_RANGE)};
}
function afom(f, p) { let s = 0; for (const k in p.w) s += f[k] * p.w[k]; return p.gate ? s * f.bare : s; }
function moonRef() { const i = S.spot.i, h = histOf(M.hist, i); return {h, c: classes(h), H: mv(i, "hurst"), ret: mv(i, "slope320_p50") / Math.max(mv(i, "slope_p50"), 1e-6), tavg: mv(i, "t_avg"), tmax: mv(i, "t_max")}; }
function nearKnown(lat, lon) { for (const k of MAN.known) if (Math.abs(lat - k.lat) < 0.5 && Math.abs(lon - k.lon) * Math.cos(lat * Math.PI / 180) < 0.5) return k.name; return null; }
function run() {
  if (!S.spot) return;
  const m = moonRef(), p = PURPOSES[S.purpose]; scores = new Float32Array(E.n);
  for (let j = 0; j < E.n; j++) scores[j] = afom(foms(j, m), p);
  let bestS = 0; for (let j = 0; j < E.n; j++) if (scores[j] > bestS) bestS = scores[j];
  let ties = 0; for (let j = 0; j < E.n; j++) if (scores[j] >= bestS - 0.01) ties++;
  const tied = ties > 50, terr = j => { const f = foms(j, m); return 0.5 * f.slope + 0.5 * f.scale; };
  let order;
  if (tied) { const set = []; for (let j = 0; j < E.n; j++) if (scores[j] >= bestS - 0.01) set.push([terr(j), j]); set.sort((a, b) => b[0] - a[0]); order = set.map(x => x[1]); }
  else order = Array.from(scores.keys()).sort((a, b) => scores[b] - scores[a]);
  const seen = new Set(); topSites = [];
  for (const j of order) { const key = Math.floor(ev(j, "lat") / 2) + "," + Math.floor(ev(j, "lon") / 2); if (seen.has(key)) continue; seen.add(key); topSites.push(j); if (topSites.length == 15) break; }
  let strong = 0, part = 0; for (let j = 0; j < E.n; j++) { if (scores[j] >= 0.8) strong++; else if (scores[j] >= 0.5) part++; }
  const best = scores[topSites[0]];
  $("verdict").innerHTML = best >= 0.8 ? `<div class="flag ok">Strong matches exist: ${strong.toLocaleString()} of ${E.n.toLocaleString()} Earth windows score 0.8 or higher. Showing the best one per region.</div>`
    : best >= 0.5 ? `<div class="flag">No strong match on Earth for this spot and purpose. Best is a partial match (${f2(best)}). ${part.toLocaleString()} windows score 0.5 or higher. See which factor holds it back in step 4.</div>`
    : `<div class="flag bad">No useful Earth match found in the library for this spot and purpose (best ${f2(best)}).</div>`;
  if (tied) $("verdict").innerHTML += `<div class="flag">${ties.toLocaleString()} Earth windows tie within 0.01 of the top score, so their order by score is not meaningful. The list shows the tied sites whose terrain is most like this lunar spot.</div>`;
  $("ranked").innerHTML = `<table><tr><th>#</th><th>Earth site (lat, lon)</th><th>Score</th></tr>` + topSites.map((j, r) => { const k = nearKnown(ev(j, "lat"), ev(j, "lon"));
    return `<tr class="site" data-j="${j}"><td>${r + 1}</td><td>${coord(j)}${k ? `<span class="tag k">near ${k.split(" (")[0]}</span>` : `<span class="tag new">candidate</span>`}${ev(j, "nomask") ? `<span class="tag">Antarctic, ice not filtered</span>` : ""}</td><td class="n"><b>${f2(scores[j])}</b></td></tr>`; }).join("") + "</table>";
  document.querySelectorAll("#ranked tr.site").forEach(tr => tr.onclick = () => selectSite(+tr.dataset.j));
  earthMarkers.forEach(mk => earthMap.removeLayer(mk)); earthMarkers = [];
  topSites.forEach((j, r) => { const mk = L.circleMarker([ev(j, "lat"), ev(j, "lon")], {radius: 7, color: nearKnown(ev(j, "lat"), ev(j, "lon")) ? "#fbbf24" : "#4ade80", weight: 2, fillOpacity: .5}).addTo(earthMap).bindTooltip(`#${r + 1} · ${f2(scores[j])}`); mk.on("click", () => selectSite(j)); earthMarkers.push(mk); });
  // known analog sites benchmark: best window within ~0.3 degrees of each
  $("known").innerHTML = "<table><tr><th>Known analog site</th><th>Best nearby window</th><th>Score</th></tr>" + MAN.known.map(k => { let bj = -1, bs = -1;
    for (let j = 0; j < E.n; j++) { if (Math.abs(ev(j, "lat") - k.lat) < 0.3 && Math.abs(ev(j, "lon") - k.lon) * Math.cos(k.lat * Math.PI / 180) < 0.3 && scores[j] > bs) { bs = scores[j]; bj = j; } }
    return bj < 0 ? `<tr><td>${k.name}</td><td class="mut">not in library (not bare land in our mask)</td><td></td></tr>` : `<tr class="site" data-j="${bj}"><td>${k.name}</td><td>${coord(bj)}</td><td class="n"><b>${f2(bs)}</b></td></tr>`; }).join("") + "</table>";
  document.querySelectorAll("#known tr.site").forEach(tr => tr.onclick = () => selectSite(+tr.dataset.j));
  location.hash = `${S.spot.x},${S.spot.y},${S.purpose}`;
  selectSite(topSites[0]);
}
function coord(j) { const la = ev(j, "lat"), lo = ev(j, "lon"); return `${Math.abs(la).toFixed(2)}° ${la >= 0 ? "N" : "S"}, ${Math.abs(lo).toFixed(2)}° ${lo >= 0 ? "E" : "W"}`; }

/* ---------- purposes + weights ---------- */
function buildPurposes() {
  $("purposes").innerHTML = ""; for (const k in PURPOSES) { const b = document.createElement("button"); b.className = "p" + (k == S.purpose ? " on" : ""); b.innerHTML = `${PURPOSES[k].name}<small>${PURPOSES[k].desc}</small>`; b.onclick = () => { S.purpose = k; buildPurposes(); run(); }; $("purposes").appendChild(b); }
  const p = PURPOSES[S.purpose]; $("weights").innerHTML = "<span>Weights (set by our team, adjust to test):</span>";
  for (const k in p.w) { const l = document.createElement("label"); l.innerHTML = `${FACT[k]} <input type="range" min="0" max="100" value="${Math.round(p.w[k] * 100)}"> <b>${Math.round(p.w[k] * 100)}</b>`;
    l.querySelector("input").onchange = e => { p.w[k] = e.target.value / 100; const t = Object.values(p.w).reduce((a, b) => a + b, 0) || 1; for (const q in p.w) p.w[q] /= t; buildPurposes(); run(); }; $("weights").appendChild(l); }
  if (p.gate) $("weights").insertAdjacentHTML("beforeend", "<span>Vegetated ground is scored zero.</span>");
}

/* ---------- Earth map ---------- */
function buildEarthMap() {
  earthMap = L.map("earthmap", {worldCopyJump: true, minZoom: 1}).setView([25, 10], 1.5);
  const gibs = L.tileLayer("https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/BlueMarble_ShadedRelief_Bathymetry/default/GoogleMapsCompatible_Level8/{z}/{y}/{x}.jpeg", {maxNativeZoom: 8, maxZoom: 12, attribution: "Imagery: NASA GIBS Blue Marble"});
  const osm = L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {maxZoom: 12, attribution: "© OpenStreetMap contributors"});
  let swapped = false; gibs.on("tileerror", () => { if (!swapped) { swapped = true; earthMap.removeLayer(gibs); osm.addTo(earthMap); } }); gibs.addTo(earthMap);
  L.control.layers({"NASA Blue Marble": gibs, "Street map (place names)": osm}).addTo(earthMap);
  MAN.known.forEach(k => L.circleMarker([k.lat, k.lon], {radius: 3, color: "#fbbf24", weight: 1}).addTo(earthMap).bindTooltip("Known analog: " + k.name));
}

/* ---------- site scorecard ---------- */
function selectSite(j) {
  S.site = j; document.querySelectorAll("tr.site").forEach(tr => tr.classList.toggle("sel", +tr.dataset.j == j));
  const m = moonRef(), f = foms(j, m), p = PURPOSES[S.purpose], la = ev(j, "lat"), dh = ev(j, "dark_h");
  const bars = Object.keys(FACT).map(k => `<div class="bar${f[k] < 0.15 ? " zero" : ""}"><span>${FACT[k]} ${k in p.w ? `<span class="w">weight ${Math.round(p.w[k] * 100)}</span>` : (k == "bare" && p.gate ? '<span class="w">gate</span>' : "")}</span><i><b style="width:${f[k] * 100}%"></b></i><span>${f2(f[k])}</span></div>`).join("");
  const weak = Object.keys(p.w).filter(k => f[k] < 0.5).map(k => FACT[k].toLowerCase());
  const season = dh > 48 ? `Continuous darkness for about ${Math.round(dh / 24)} days each winter. ` : `Longest night about ${Math.round(dh)} hours. `;
  $("card").innerHTML = `<div class="cap">Scorecard · ${coord(j)}</div><div style="font-size:26px;font-weight:700">${f2(scores[j])} <span class="mut" style="font-size:13px;font-weight:400">for ${p.name.toLowerCase()}</span></div>${bars}
   <div class="bar zero"><span>Gravity, vacuum, radiation</span><i><b style="width:0"></b></i><span>0.00</span></div>
   <div class="kv" style="margin-topSites:8px"><span>Median slope (Moon / Earth)</span><span>${f1(mv(S.spot.i, "slope_p50"))}° / ${f1(ev(j, "slope_p50"))}°</span><span>Slope at 320 m (Moon / Earth)</span><span>${f1(mv(S.spot.i, "slope320_p50"))}° / ${f1(ev(j, "slope320_p50"))}°</span><span>Scaling number (Moon / Earth)</span><span>${f2(m.H)} / ${f2(ev(j, "hurst"))}</span>
   <span>Earth site: coldest month, average night</span><span>${isNaN(ev(j, "t_night_min")) ? "no data" : ev(j, "t_night_min").toFixed(0) + " K"}</span><span>Moon spot average</span><span>${isNaN(m.tavg) ? "no data" : m.tavg.toFixed(0) + " K"}</span></div>
   <p class="mut" style="margin:8px 0 0"><b>Where it breaks:</b> ${weak.length ? "weak on " + weak.join(", ") + ". " : "no weak factor for this purpose. "}${season}Lunar gravity (one sixth of Earth's), vacuum and radiation cannot be reproduced at any Earth site.
   <a target="_blank" href="https://worldview.earthdata.nasa.gov/?v=${(ev(j, "lon") - 1).toFixed(2)},${(la - 0.6).toFixed(2)},${(ev(j, "lon") + 1).toFixed(2)},${(la + 0.6).toFixed(2)}">Open in NASA Worldview</a></p>`;
  $("capE").textContent = `Earth: ${coord(j)}`; earthMap.flyTo([la, ev(j, "lon")], Math.max(earthMap.getZoom(), 4), {duration: 0.6});
  loadEarthPatch(j); draw3d();
}

/* ---------- 3D patches ---------- */
const V = {};
function init3d() {
  for (const id of ["c3m", "c3e"]) { const cv = $(id), r = new THREE.WebGLRenderer({canvas: cv, antialias: true}); const sc = new THREE.Scene(), cam = new THREE.PerspectiveCamera(35, 1, 0.1, 100);
    cam.position.set(0, -17, 9.5); cam.lookAt(0, 0, 0.5); sc.add(new THREE.AmbientLight(0xffffff, 0.55)); const dl = new THREE.DirectionalLight(0xffffff, 0.9); dl.position.set(-6, -4, 8); sc.add(dl);
    const grp = new THREE.Group(); sc.add(grp); V[id] = {r, sc, cam, grp, z: null, cv};
    let drag = null; cv.onpointerdown = e => { drag = [e.clientX, e.clientY]; cv.setPointerCapture(e.pointerId); };
    cv.onpointermove = e => { if (!drag) return; S.rot.z += (e.clientX - drag[0]) * 0.01; S.rot.x = Math.max(-1.5, Math.min(-0.2, S.rot.x + (e.clientY - drag[1]) * 0.006)); drag = [e.clientX, e.clientY]; render3d(); };
    cv.onpointerup = () => drag = null; }
  window.addEventListener("resize", render3d);
}
function moonPatch() { const n = 26, z = new Float32Array(n * n), D = MAN.moon.dem, c0 = Math.round((S.spot.x - 5000 + D.half_m) / D.res_m), r0 = Math.round((D.half_m - (S.spot.y + 5000)) / D.res_m);
  for (let r = 0; r < n; r++) for (let c = 0; c < n; c++) { const rr = Math.min(D.n - 1, Math.max(0, r0 + r)), cc = Math.min(D.n - 1, Math.max(0, c0 + c)); z[r * n + c] = DEM[rr * D.n + cc]; } return {z, n}; }
const ramp = t => { t = clip(t); const s = [[13, 8, 135], [126, 3, 168], [204, 71, 120], [248, 149, 64], [240, 249, 33]], x = t * 4, i = Math.min(3, Math.floor(x)), f = x - i; return s[i].map((v, k) => (v + (s[i + 1][k] - v) * f) / 255); };
function buildMesh(v) {
  v.grp.clear(); v.span = 0; if (!v.z) return; const {z, n} = v.z, g = new THREE.PlaneGeometry(10, 10, n - 1, n - 1), pos = g.attributes.position, col = new Float32Array(n * n * 3), cell = 10000 / (n - 1);
  let mn = Infinity, mx = -Infinity; for (const h of z) { if (h < mn) mn = h; if (h > mx) mx = h; }
  for (let r = 0; r < n; r++) for (let c = 0; c < n; c++) { const i = r * n + c; pos.setZ(i, (z[i] - (mn + mx) / 2) / 1000 * 2);
    let t; if (S.col == "height") t = (z[i] - mn) / Math.max(mx - mn, 1); else { const dx = (z[r * n + Math.min(n - 1, c + 1)] - z[r * n + Math.max(0, c - 1)]) / (2 * cell), dy = (z[Math.min(n - 1, r + 1) * n + c] - z[Math.max(0, r - 1) * n + c]) / (2 * cell); t = Math.atan(Math.hypot(dx, dy)) * 180 / Math.PI / 30; }
    const k = ramp(t); col[i * 3] = k[0]; col[i * 3 + 1] = k[1]; col[i * 3 + 2] = k[2]; }
  g.setAttribute("color", new THREE.BufferAttribute(col, 3)); g.computeVertexNormals(); v.span = (mx - mn) / 1000 * 2;
  v.grp.add(new THREE.Mesh(g, new THREE.MeshLambertMaterial({vertexColors: true, side: THREE.DoubleSide})));
}
function draw3d() { if (S.spot) V.c3m.z = moonPatch(); buildMesh(V.c3m); buildMesh(V.c3e); render3d(); }
function render3d() { for (const id in V) { const v = V[id], w = v.cv.clientWidth, h = v.cv.clientHeight; if (!w) continue; v.r.setPixelRatio(window.devicePixelRatio); v.r.setSize(w, h, false); v.cam.aspect = w / h; v.cam.updateProjectionMatrix(); v.grp.rotation.set(0, 0, S.rot.z); const span = Math.max(V.c3m.span || 0, V.c3e.span || 0), dist = 19 * Math.max(1, 1.45 / (w / h)) * Math.max(1, (10 + span * 1.6) / 12), el = -S.rot.x - 0.5; v.cam.position.set(0, -dist * Math.cos(el), dist * Math.sin(el)); v.cam.lookAt(0, 0, 0); v.r.render(v.sc, v.cam); } }
/* Earth display patch from open Terrarium elevation tiles (AWS Open Data). Display only. */
const tileCache = new Map();
function tile(z, x, y) { const k = `${z}/${x}/${y}`; if (!tileCache.has(k)) tileCache.set(k, new Promise((res, rej) => { const im = new Image(); im.crossOrigin = "anonymous"; im.onload = () => { const c = document.createElement("canvas"); c.width = c.height = 256; const cx = c.getContext("2d", {willReadFrequently: true}); cx.drawImage(im, 0, 0); res(cx.getImageData(0, 0, 256, 256).data); }; im.onerror = rej; im.src = `https://s3.amazonaws.com/elevation-tiles-prod/terrarium/${k}.png`; })); return tileCache.get(k); }
async function loadEarthPatch(j) {
  const lat = ev(j, "lat"), lon = ev(j, "lon"), n = 26, z = new Float32Array(n * n), zoom = Math.max(6, Math.min(12, Math.round(Math.log2(156543 * Math.cos(lat * Math.PI / 180) / 150)))), N = 2 ** zoom;
  const dLat = 10 / 111.32, dLon = 10 / (111.32 * Math.cos(lat * Math.PI / 180)), px = [];
  for (let r = 0; r < n; r++) for (let c = 0; c < n; c++) { const la = lat + dLat / 2 - dLat * r / (n - 1), lo = lon - dLon / 2 + dLon * c / (n - 1), X = (lo + 180) / 360 * N, s = Math.sin(la * Math.PI / 180), Y = (0.5 - Math.log((1 + s) / (1 - s)) / (4 * Math.PI)) * N; px.push([X, Y]); }
  V.c3e.z = null; buildMesh(V.c3e); render3d(); $("capE").textContent = `Earth: ${coord(j)} · loading terrain…`;
  try { const need = new Map(); px.forEach(([X, Y]) => need.set(Math.floor(X) + "/" + Math.floor(Y), 1)); const data = {};
    await Promise.all([...need.keys()].map(async k => { const [x, y] = k.split("/").map(Number); data[k] = await tile(zoom, ((x % N) + N) % N, y); }));
    if (S.site !== j) return;
    px.forEach(([X, Y], i) => { const d = data[Math.floor(X) + "/" + Math.floor(Y)], u = Math.min(255, Math.floor((X % 1) * 256)), v = Math.min(255, Math.floor((Y % 1) * 256)), o = (v * 256 + u) * 4; z[i] = d[o] * 256 + d[o + 1] + d[o + 2] / 256 - 32768; });
    V.c3e.z = {z, n}; $("capE").textContent = `Earth: ${coord(j)}`; buildMesh(V.c3e); render3d();
  } catch (e) { if (S.site === j) $("capE").textContent = `Earth: ${coord(j)} · 3D terrain not available (tile service unreachable)`; }
}
init().catch(e => { document.body.insertAdjacentHTML("afterbegin", `<div class="flag bad" style="margin:12px">Could not load data: ${e}. Open this page through the local server (scripts\\open_app.bat), not by double-clicking the file.</div>`); });
