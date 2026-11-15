const assert = require("node:assert/strict");
const {readFileSync} = require("node:fs");
const {join} = require("node:path");
const {runInContext, createContext} = require("node:vm");
const {test} = require("node:test");

const app = readFileSync(join(__dirname, "..", "app", "app.js"), "utf8");
const startup = app.lastIndexOf("\ninit().catch(");
assert.notEqual(startup, -1, "app startup call should be present");

function setup() {
  const layers = new Set();
  const flyTos = [];
  const map = {
    removeLayer(marker) { layers.delete(marker); },
    getZoom() { return 2; },
    flyTo(...args) { flyTos.push(args); }
  };
  const elements = new Map();
  const document = {
    getElementById(id) {
      if (!elements.has(id)) elements.set(id, {});
      return elements.get(id);
    },
    querySelectorAll() { return []; }
  };
  class Marker {
    constructor(latlng, options) { this.latlng = latlng; this.options = options; }
    addTo(target) { target.layers.add(this); return this; }
    setLatLng(latlng) { this.latlng = latlng; return this; }
  }
  map.layers = layers;
  const L = {
    marker: (latlng, options) => new Marker(latlng, options),
    divIcon: options => options
  };
  const mockE = {
    nc: 7,
    c: {lat: 0, lon: 1, dark_h: 2, t_night_min: 3, slope_p50: 4, slope320_p50: 5, hurst: 6},
    meta: new Float32Array([12, 34, 10, 5, 2, 3, 1, -20, 45, 20, 6, 4, 5, 2])
  };
  const mockM = {nc: 2, c: {slope_p50: 0, slope320_p50: 1}, meta: new Float32Array([1, 2])};
  const context = createContext({L, document, mockE, mockM, mockEarthMap: map});
  runInContext(app.slice(0, startup), context);
  runInContext("earthMap = mockEarthMap; E = mockE; M = mockM; S.spot = {i: 0}; scores = new Float32Array([0.95, 0.9]); moonRef = () => ({H: 1, tavg: 1}); foms = () => ({slope: 0, classes: 0, scale: 0, bare: 1, lowsun: 0, dark: 0, t_cold: 0, t_peak: 0}); loadEarthPatch = () => {}; draw3d = () => {}", context);
  return {context, elements, flyTos, layers};
}

test("Earth selection outline follows the active selection and clears cleanly", () => {
  const {context, elements, flyTos, layers} = setup();
  assert.equal(layers.size, 0);
  assert.equal(runInContext("earthSelection", context), null);

  runInContext("selectSite(0)", context);
  const outline = runInContext("earthSelection", context);
  assert.equal(layers.size, 1);
  assert.deepEqual(Array.from(outline.latlng), [12, 34]);
  assert.equal(outline.options.interactive, false);
  assert.equal(elements.get("capE").textContent, "Earth: 12.00° N, 34.00° E");
  assert.deepEqual(Array.from(flyTos[0][0]), [12, 34]);

  runInContext("selectSite(1)", context);
  assert.equal(layers.size, 1);
  assert.equal(runInContext("earthSelection", context), outline);
  assert.deepEqual(Array.from(outline.latlng), [-20, 45]);

  runInContext("updateEarthSelection(null)", context);
  assert.equal(layers.size, 0);
  assert.equal(runInContext("earthSelection", context), null);
});
