import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { mountGlobe, makeGlobe, statesAt, latLon, stateAt as planetState } from './planet.js';

const $ = (s) => document.querySelector(s);
const esc = (s) => String(s).replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
const MONTHS = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'];
const ROMAN = ['I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX', 'X', 'XI', 'XII'];
const ERAS = [
  [900, 1108, 'The Six Worlds'], [1108, 1438, 'The Fevarian Wars'], [1438, 1945, 'The Voor Expansion'],
  [1945, 2220, 'The Early Solar Era'], [2220, 2255, 'The Solar War'], [2255, 2289, 'Unification'],
  [2289, 2318, 'The Expansion Era'], [2318, 2333, 'The Ring of Iron'], [2333, 2341, 'The Ciriban Gulf Conflict'],
  [2341, 2405, 'The First Republic'], [2405, 2441, 'The Fevarian Crisis'], [2441, 2449, 'The Darkest Decade'],
  [2449, 2460, 'The Scouring'], [2460, 2510, 'Reconstruction'], [2510, 2600, 'The Apportionment Crisis'],
];

const [data, articles, PLANETS] = await Promise.all([
  fetch('assets/atlas-data.json').then((r) => r.json()),
  fetch('assets/articles.json').then((r) => r.json()).catch(() => ({})),
  fetch('assets/planets/planets.json').then((r) => r.json()).catch(() => ({})),
]);
// generated surfaces for planets nobody has mapped, by type
const GENLIB = await fetch('assets/planets/_gen/index.json').then((r) => r.json()).catch(() => ({}));
// generated planet maps, found by world name
const planetByName = Object.fromEntries(Object.entries(PLANETS).map(([slug, p]) => [p.name, Object.assign({ slug }, p)]));
const SOL_BODIES = { Mercury: 'mercury', Venus: 'venus', Jupiter: 'jupiter', Saturn: 'saturn', Uranus: 'uranus', Neptune: 'neptune', Titan: 'titan' };
function spriteFor(name, t) {
  const p = planetByName[name];
  if (p) return 'assets/planets/' + p.slug + '/' + planetState(p, t).k + '-sprite.webp';
  if (SOL_BODIES[name]) return 'assets/planets/_sol/' + SOL_BODIES[name] + '-sprite.webp';
  return null;
}
// a sprite lit from its left, turned so its lit side faces the star
function spriteSVG(href, x, y, r, sx, sy) {
  const a = Math.atan2(sy - y, sx - x) * 180 / Math.PI - 180;
  return '<image href="' + href + '" x="' + (x - r) + '" y="' + (y - r) + '" width="' + (2 * r) + '" height="' + (2 * r) + '" transform="rotate(' + a.toFixed(1) + ' ' + x + ' ' + y + ')"/>';
}
const SYS = data.systems;
const byId = Object.fromEntries(SYS.map((s) => [s.id, s]));
const P = data.polities;
const hasArticle = (slug) => slug && Object.prototype.hasOwnProperty.call(articles, slug);
const wikiHref = (slug) => 'wiki/' + slug + '.html';

// ------------------------------------------------------------------ time
const RANGE = data.meta.range;
let year = data.meta.start;
const fromHash = new URLSearchParams(location.hash.slice(1));
if (fromHash.get('year')) year = Math.min(RANGE[1], Math.max(RANGE[0], parseInt(fromHash.get('year'), 10) || year));

const humanName = (t) => (t < 2283.42 ? 'earth' : t < 2341 ? 'une' : 'usr');
const CONTACT = data.contact || {};
function ownerAt(s, t) {
  let cur = null;
  for (const e of s.own) { if (e.from <= t) cur = e; else break; }
  if (!cur || !cur.p) return null;
  const p = cur.p === 'human' ? humanName(t) : cur.p;
  if (CONTACT[p] && t < CONTACT[p]) return null;   // hidden until humanity meets it (Lewis); its earlier history lives in the wiki
  return { p, note: cur.note, derived: !!cur.derived, from: cur.from, vs: cur.vs };
}
// a world shows its found biome until its terraforming is complete
const biomeAt = (w, t) => (w && w.becomes && w.terraformed && t >= w.terraformed ? w.becomes : w && w.biome);
const worldByName = (sid, name) => data.worlds.find((w) => w.sys === sid && w.name === name);
// a world is shown from its settlement, except a world humanity had not yet heard of, which is hidden from 2050 until then
const seenAt = (o, t) => o.settled === undefined || (o.settled <= t && !(o.known && t >= 2050 && t < o.known));
const worldsAt = (sid, t) => data.worlds.filter((w) => w.sys === sid && seenAt(w, t));
const burnedAt = (sid, t) => data.burned.filter((b) => b.sys === sid && b.y <= t && t < b.y + 30);
const eraOf = (y) => (ERAS.find((e) => y >= e[0] && y < e[1]) || ERAS[ERAS.length - 1])[2];
const captionOf = (y) => (data.captions.find((c) => y >= c.from && y < c.to) || data.captions[data.captions.length - 1]).text;
const fmtDate = (y) => {
  const yr = Math.floor(y), f = y - yr, m = Math.min(11, Math.floor(f * 12 + 1e-6));
  return f < 0.001 ? String(yr) : MONTHS[m] + ' ' + yr;
};
const polName = (p) => (!p ? 'Unclaimed' : P[p] ? P[p].name : p);
const polColor = (p) => (P[p] ? P[p].color : '#888');

// ------------------------------------------------------------------ three.js scene
const canvas = $('#gl');
const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true });
renderer.setPixelRatio(Math.min(2, window.devicePixelRatio || 1));
const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(45, 1, 0.5, 3000);
const controls = new OrbitControls(camera, canvas);
controls.mouseButtons = { LEFT: THREE.MOUSE.PAN, MIDDLE: THREE.MOUSE.DOLLY, RIGHT: THREE.MOUSE.ROTATE };
controls.touches = { ONE: THREE.TOUCH.PAN, TWO: THREE.TOUCH.DOLLY_ROTATE };
controls.screenSpacePanning = false;
controls.zoomToCursor = true;
controls.enableDamping = true;
controls.dampingFactor = 0.12;
controls.minDistance = 8;
controls.maxDistance = 420;
controls.maxPolarAngle = Math.PI * 0.47;

const W3 = (s) => new THREE.Vector3(s.x, s.z, -s.y); // map plane (x, y) -> three (x, -z); height is three's y
const EXT = { x0: -175, x1: 75, y0: -140, y1: 90 };   // 250 x 230 ly, about 10 px to the light year
const HOME = { target: new THREE.Vector3(-64, 0, 18), pos: new THREE.Vector3(-64, 160, 140) };
camera.position.copy(HOME.pos); controls.target.copy(HOME.target);

// plane grid
const grid = new THREE.Group();
{
  const pts = [];
  for (let x = Math.ceil(EXT.x0 / 10) * 10; x <= EXT.x1; x += 10) pts.push(x, 0, -EXT.y0, x, 0, -EXT.y1);
  for (let y = Math.ceil(EXT.y0 / 10) * 10; y <= EXT.y1; y += 10) pts.push(EXT.x0, 0, -y, EXT.x1, 0, -y);
  const g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.Float32BufferAttribute(pts, 3));
  grid.add(new THREE.LineSegments(g, new THREE.LineBasicMaterial({ color: 0xffffff, transparent: true, opacity: 0.05 })));
  const rings = [];
  for (let r = 10; r <= 160; r += 10) {
    for (let i = 0; i < 128; i++) {
      const a0 = (i / 128) * Math.PI * 2, a1 = ((i + 1) / 128) * Math.PI * 2;
      rings.push(Math.cos(a0) * r, 0, Math.sin(a0) * r, Math.cos(a1) * r, 0, Math.sin(a1) * r);
    }
  }
  const rg = new THREE.BufferGeometry(); rg.setAttribute('position', new THREE.Float32BufferAttribute(rings, 3));
  grid.add(new THREE.LineSegments(rg, new THREE.LineBasicMaterial({ color: 0xffffff, transparent: true, opacity: 0.045 })));
}
scene.add(grid);

// territory canvas texture on the plane
const TPX = 2300 / 230;
const terrCanvas = document.createElement('canvas');
terrCanvas.width = Math.round((EXT.x1 - EXT.x0) * TPX);
terrCanvas.height = Math.round((EXT.y1 - EXT.y0) * TPX);
const terrTex = new THREE.CanvasTexture(terrCanvas);
terrTex.colorSpace = THREE.SRGBColorSpace;
terrTex.anisotropy = 4;
const terrMesh = new THREE.Mesh(
  new THREE.PlaneGeometry(EXT.x1 - EXT.x0, EXT.y1 - EXT.y0, 48, 48),
  new THREE.MeshBasicMaterial({ map: terrTex, transparent: true, depthWrite: false }),
);
terrMesh.rotation.x = -Math.PI / 2;
terrMesh.position.set((EXT.x0 + EXT.x1) / 2, -0.05, -(EXT.y0 + EXT.y1) / 2);
scene.add(terrMesh);
const cx = (x) => (x - EXT.x0) * TPX, cy = (y) => (EXT.y1 - y) * TPX;

// cloud noise, generated once
const noise = (() => {
  const n = 512, c = document.createElement('canvas'); c.width = c.height = n;
  const g = c.getContext('2d'), img = g.createImageData(n, n);
  let seed = 2235; const rnd = () => ((seed = (seed * 16807) % 2147483647) / 2147483647);
  const oct = [6, 12, 24, 48, 96].map((s) => { const a = new Float32Array(s * s); for (let i = 0; i < a.length; i++) a[i] = rnd(); return [s, a]; });
  const smooth = (t) => t * t * (3 - 2 * t);
  for (let y = 0; y < n; y++) for (let x = 0; x < n; x++) {
    let v = 0, amp = 0.55, tot = 0;
    for (const [s, a] of oct) {
      const fx = (x / n) * s, fy = (y / n) * s, x0 = Math.floor(fx) % s, y0 = Math.floor(fy) % s, x1 = (x0 + 1) % s, y1 = (y0 + 1) % s;
      const tx = smooth(fx % 1), ty = smooth(fy % 1);
      const top = a[y0 * s + x0] * (1 - tx) + a[y0 * s + x1] * tx, bot = a[y1 * s + x0] * (1 - tx) + a[y1 * s + x1] * tx;
      v += (top * (1 - ty) + bot * ty) * amp; tot += amp; amp *= 0.55;
    }
    v /= tot; const i = (y * n + x) * 4;
    img.data[i] = img.data[i + 1] = img.data[i + 2] = 255; img.data[i + 3] = Math.max(0, Math.min(255, (0.35 + (v - 0.5) * 1.6 + 0.4) * 255));
  }
  g.putImageData(img, 0, 0);
  return c;
})();

const STRIPES = (() => {
  const c = document.createElement('canvas'); c.width = c.height = 24; const g = c.getContext('2d');
  g.strokeStyle = '#000'; g.lineWidth = 7;
  for (const o of [-24, 0, 24]) { g.beginPath(); g.moveTo(o, 24); g.lineTo(o + 24, 0); g.stroke(); }
  return c;
})();
const blobR = Object.fromEntries(SYS.map((s, i) => [s.id, 6.2 + ((i * 7919) % 100) / 100 * 2.6]));
const layer = document.createElement('canvas'); layer.width = terrCanvas.width; layer.height = terrCanvas.height;
function paintTerritory(t) {
  const g = terrCanvas.getContext('2d');
  g.clearRect(0, 0, terrCanvas.width, terrCanvas.height);
  const groups = {};
  for (const s of SYS) {
    const o = ownerAt(s, t); if (!o) continue;
    (groups[o.p] = groups[o.p] || []).push([s, o]);
  }
  if (layers.ter) {
    const lg = layer.getContext('2d');
    for (const p of Object.keys(groups)) {
      lg.globalCompositeOperation = 'source-over';
      lg.clearRect(0, 0, layer.width, layer.height);
      for (const [s, o] of groups[p]) {
        const r = blobR[s.id] * TPX * (o.note === 'occupied' || o.note === 'tributary' || o.note === 'occupation zone' ? 0.8 : 1);
        const x = cx(s.x), y = cy(s.y);
        const gr = lg.createRadialGradient(x, y, 0, x, y, r);
        gr.addColorStop(0, 'rgba(0,0,0,1)'); gr.addColorStop(0.45, 'rgba(0,0,0,.85)'); gr.addColorStop(1, 'rgba(0,0,0,0)');
        lg.fillStyle = gr; lg.beginPath(); lg.arc(x, y, r, 0, Math.PI * 2); lg.fill();
      }
      lg.globalCompositeOperation = 'destination-in';
      const pat = lg.createPattern(noise, 'repeat'); pat.setTransform(new DOMMatrix().scale(2.2)); lg.fillStyle = pat; lg.fillRect(0, 0, layer.width, layer.height);
      lg.globalCompositeOperation = 'source-in';
      lg.fillStyle = polColor(p); lg.fillRect(0, 0, layer.width, layer.height);
      const fade = CONTACT[p] ? Math.min(1, Math.max(0, (t - CONTACT[p]) / 3)) : 1;   // fade in over three years after contact
      g.globalAlpha = 0.62 * fade; g.drawImage(layer, 0, 0); g.globalAlpha = 1;
    }
    // a besieged or contested system: the attacker's colour in diagonal stripes over the holder's
    for (const p of Object.keys(groups)) for (const [s, o] of groups[p]) {
      if (!o.vs) continue;
      lg.globalCompositeOperation = 'source-over'; lg.clearRect(0, 0, layer.width, layer.height);
      const r = blobR[s.id] * TPX * 0.95, x = cx(s.x), y = cy(s.y);
      const gr = lg.createRadialGradient(x, y, 0, x, y, r);
      gr.addColorStop(0, 'rgba(0,0,0,1)'); gr.addColorStop(0.5, 'rgba(0,0,0,.85)'); gr.addColorStop(1, 'rgba(0,0,0,0)');
      lg.fillStyle = gr; lg.beginPath(); lg.arc(x, y, r, 0, Math.PI * 2); lg.fill();
      lg.globalCompositeOperation = 'destination-in'; lg.fillStyle = lg.createPattern(STRIPES, 'repeat'); lg.fillRect(x - r, y - r, r * 2, r * 2);
      lg.globalCompositeOperation = 'source-in'; lg.fillStyle = polColor(o.vs); lg.fillRect(x - r, y - r, r * 2, r * 2);
      g.globalAlpha = 0.75; g.drawImage(layer, 0, 0); g.globalAlpha = 1;
    }
    // polity names at the centre of their holdings
    g.textAlign = 'center'; g.textBaseline = 'middle';
    for (const p of Object.keys(groups)) {
      const list = groups[p]; if (list.length < 3 || p === 'raidzone') continue;
      const mx = list.reduce((a, [s]) => a + s.x, 0) / list.length, my = list.reduce((a, [s]) => a + s.y, 0) / list.length;
      const words = polName(p).toUpperCase().split(' ');
      const lines = words.length > 2 ? [words.slice(0, Math.ceil(words.length / 2)).join(' '), words.slice(Math.ceil(words.length / 2)).join(' ')] : [words.join(' ')];
      const size = Math.min(120, 26 + list.length * 1.6);
      g.font = '300 ' + size + "px 'Jost', sans-serif";
      g.fillStyle = 'rgba(255,255,255,0.2)';
      if ('letterSpacing' in g) g.letterSpacing = size * 0.12 + 'px';
      lines.forEach((ln, i) => g.fillText(ln, cx(mx), cy(my) + (i - (lines.length - 1) / 2) * size * 1.05));
    }
  }
  if (layers.reg) {
    // regions: natural features, in large thin capitals
    g.textAlign = 'center'; g.textBaseline = 'middle';
    g.font = "300 46px 'Jost', sans-serif"; g.fillStyle = 'rgba(255,255,255,0.14)';
    if ('letterSpacing' in g) g.letterSpacing = '9px';
    for (const r of data.regions) {
      // a label near the map's edge can be stacked one word to a line
      const words = r.stack ? r.name.toUpperCase().split(' ') : [r.name.toUpperCase()];
      words.forEach((w, i) => g.fillText(w, cx(r.x), cy(r.y) + (i - (words.length - 1) / 2) * 50));
    }
    // sectors: the Republic's administrative divisions, drawn as straight-edged outlines
    for (const sh of sectorShapes(t)) {
      g.save(); g.setLineDash([14, 12]); g.lineWidth = 3; g.strokeStyle = 'rgba(242,213,154,0.45)'; g.lineJoin = 'miter';
      for (const line of sh.lines) { g.beginPath(); line.forEach(([x, y], i) => (i ? g.lineTo(cx(x), cy(y)) : g.moveTo(cx(x), cy(y)))); g.stroke(); }
      g.restore();
      g.font = "500 19px 'Jost', sans-serif"; g.fillStyle = 'rgba(242,213,154,0.75)';
      if ('letterSpacing' in g) g.letterSpacing = '4px';
      sh.words.forEach((w, i) => g.fillText(w.toUpperCase(), cx(sh.lx), cy(sh.ly) + (i - 0.5) * 21));
    }
  }
  if ('letterSpacing' in g) g.letterSpacing = '0px';
  terrTex.needsUpdate = true;
}


// ------------------------------------------------------------------ sector outlines
// A sector is its padded hull, less any ground nearer to another sector's star. The hull is
// straight-edged and the dividing lines between sectors are straight, so after tracing the
// boundary and dropping the points that sit on a straight run, the outline is all straight
// lines and no two sectors overlap.
const SECTOR_PAD = 3, SECTOR_GAP = 0.8, SECTOR_STEP = 0.25;
let sectorCache = { key: null, shapes: [] };
function sectorShapes(t) {
  const held = (data.sectors || []).map((s) => ({ name: s.name, pts: s.members.map((id) => byId[id]).filter((p) => { const o = p && ownerAt(p, t); return o && ['earth', 'une', 'usr'].includes(o.p); }) })).filter((h) => h.pts.length >= 2);
  const key = held.map((h) => h.pts.map((p) => p.id).join(',')).join('|');
  if (key === sectorCache.key) return sectorCache.shapes;
  const shapes = [];
  const all = held.flatMap((h) => h.pts);
  if (all.length) {
    const M = SECTOR_PAD + 1;
    const x0 = Math.min(...all.map((p) => p.x)) - M, x1 = Math.max(...all.map((p) => p.x)) + M;
    const y0 = Math.min(...all.map((p) => p.y)) - M, y1 = Math.max(...all.map((p) => p.y)) + M;
    const nx = Math.ceil((x1 - x0) / SECTOR_STEP) + 1, ny = Math.ceil((y1 - y0) / SECTOR_STEP) + 1;
    const near = held.map(() => new Float32Array(nx * ny));
    for (let j = 0; j < ny; j++) for (let i = 0; i < nx; i++) {
      const x = x0 + i * SECTOR_STEP, y = y0 + j * SECTOR_STEP;
      held.forEach((h, k) => { let m = 1e9; for (const p of h.pts) { const d = (p.x - x) ** 2 + (p.y - y) ** 2; if (d < m) m = d; } near[k][j * nx + i] = Math.sqrt(m); });
    }
    held.forEach((h, k) => {
      // the padded hull, as half-planes: inside where every edge function is negative
      const ring = [];
      for (const p of h.pts) for (let q = 0; q < 8; q++) { const a = (q + 0.5) * Math.PI / 4; ring.push([p.x + Math.cos(a) * SECTOR_PAD, p.y + Math.sin(a) * SECTOR_PAD]); }
      const hull = convexHull(ring);
      const edges = hull.map((a, i) => { const b = hull[(i + 1) % hull.length], ex = b[0] - a[0], ey = b[1] - a[1], l = Math.hypot(ex, ey) || 1; return [ey / l, -ex / l, (ey * a[0] - ex * a[1]) / l]; });
      const f = new Float32Array(nx * ny);
      for (let j = 0; j < ny; j++) for (let i = 0; i < nx; i++) {
        const q = j * nx + i, x = x0 + i * SECTOR_STEP, y = y0 + j * SECTOR_STEP;
        let g = -1e9; for (const [ex, ey, c] of edges) { const v = ex * x + ey * y - c; if (v > g) g = v; }
        let other = 1e9; for (let kk = 0; kk < held.length; kk++) if (kk !== k && near[kk][q] < other) other = near[kk][q];
        f[q] = Math.min(-g, (other - near[k][q]) / 2 - SECTOR_GAP / 2);
      }
      const lines = marching(f, nx, ny, x0, y0).map((ln) => simplify(ln, 0.12)).filter((ln) => ln.length > 2);
      if (!lines.length) return;
      // the name goes on two lines ("BINAMI" / "SECTOR") at the spot deepest inside the outline
      // where the whole label fits, preferring spots near the middle of the sector's stars
      const words = [h.name.replace(/ Sector$/i, ''), 'Sector'];
      const lw = Math.max(...words.map((w) => w.length)) * 1.55, lh = 4.2;
      const cxm = h.pts.reduce((a, p) => a + p.x, 0) / h.pts.length, cym = h.pts.reduce((a, p) => a + p.y, 0) / h.pts.length;
      const at = (x, y) => { const i = Math.round((x - x0) / SECTOR_STEP), j = Math.round((y - y0) / SECTOR_STEP); return i < 0 || j < 0 || i >= nx || j >= ny ? -1 : f[j * nx + i]; };
      let best = null;
      for (let j = 0; j < ny; j += 2) for (let i = 0; i < nx; i += 2) {
        if (f[j * nx + i] <= 0) continue;
        const x = x0 + i * SECTOR_STEP, y = y0 + j * SECTOR_STEP;
        let m = 1e9;
        for (const dx of [-0.5, -0.25, 0, 0.25, 0.5]) for (const dy of [-0.5, 0, 0.5]) m = Math.min(m, at(x + dx * lw, y + dy * lh));
        const score = Math.min(m, 1.5) - 0.03 * Math.hypot(x - cxm, y - cym);
        if (!best || score > best.score) best = { score, x, y };
      }
      shapes.push({ name: h.name, words, lines, lx: best ? best.x : cxm, ly: best ? best.y : cym });
    });
  }
  sectorCache = { key, shapes };
  return shapes;
}
function marching(f, nx, ny, x0, y0) {
  const segs = [];
  const P = (i, j) => [x0 + i * SECTOR_STEP, y0 + j * SECTOR_STEP];
  const lerp = (a, b, va, vb) => { const k = va / (va - vb); return [a[0] + (b[0] - a[0]) * k, a[1] + (b[1] - a[1]) * k]; };
  for (let j = 0; j < ny - 1; j++) for (let i = 0; i < nx - 1; i++) {
    const v = [f[j * nx + i], f[j * nx + i + 1], f[(j + 1) * nx + i + 1], f[(j + 1) * nx + i]];
    const c = [P(i, j), P(i + 1, j), P(i + 1, j + 1), P(i, j + 1)];
    const e = [];
    for (let k = 0; k < 4; k++) { const a = v[k], b = v[(k + 1) % 4]; if ((a > 0) !== (b > 0)) e.push(lerp(c[k], c[(k + 1) % 4], a, b)); }
    if (e.length === 2) segs.push([e[0], e[1]]);
    else if (e.length === 4) { segs.push([e[0], e[1]]); segs.push([e[2], e[3]]); }
  }
  const k = (p) => p[0].toFixed(4) + ',' + p[1].toFixed(4);
  const ends = new Map();
  segs.forEach((s, i) => { for (const p of s) { const kk = k(p); if (!ends.has(kk)) ends.set(kk, []); ends.get(kk).push(i); } });
  const used = new Uint8Array(segs.length), lines = [];
  for (let i = 0; i < segs.length; i++) {
    if (used[i]) continue; used[i] = 1;
    const line = [segs[i][0], segs[i][1]];
    for (const dir of [1, 0]) {
      for (;;) {
        const tip = dir ? line[line.length - 1] : line[0];
        const nxt = (ends.get(k(tip)) || []).find((s) => !used[s]);
        if (nxt === undefined) break;
        used[nxt] = 1;
        const [a, b] = segs[nxt], q = k(a) === k(tip) ? b : a;
        if (dir) line.push(q); else line.unshift(q);
      }
    }
    lines.push(line);
  }
  return lines;
}
// Douglas-Peucker: keep only the corners of a traced line
function simplify(pts, tol) {
  if (pts.length < 3) return pts;
  const closed = Math.hypot(pts[0][0] - pts[pts.length - 1][0], pts[0][1] - pts[pts.length - 1][1]) < 1e-6;
  const dp = (a, b) => {
    const [ax, ay] = pts[a], [bx, by] = pts[b], dx = bx - ax, dy = by - ay, L = Math.hypot(dx, dy);
    let m = -1, at = -1;
    for (let i = a + 1; i < b; i++) { const d = L ? Math.abs(dx * (pts[i][1] - ay) - dy * (pts[i][0] - ax)) / L : Math.hypot(pts[i][0] - ax, pts[i][1] - ay); if (d > m) { m = d; at = i; } }
    return m > tol ? dp(a, at).concat(dp(at, b).slice(1)) : [pts[a], pts[b]];
  };
  if (!closed) return dp(0, pts.length - 1);
  // split a closed ring at its farthest point so both halves simplify cleanly
  let far = 1, fd = 0;
  for (let i = 1; i < pts.length - 1; i++) { const d = Math.hypot(pts[i][0] - pts[0][0], pts[i][1] - pts[0][1]); if (d > fd) { fd = d; far = i; } }
  return dp(0, far).concat(dp(far, pts.length - 1).slice(1));
}

function convexHull(p) {
  p = p.slice().sort((a, b) => a[0] - b[0] || a[1] - b[1]);
  const cr = (o, a, b) => (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0]);
  const lo = [], up = [];
  for (const q of p) { while (lo.length >= 2 && cr(lo[lo.length - 2], lo[lo.length - 1], q) <= 0) lo.pop(); lo.push(q); }
  for (const q of p.slice().reverse()) { while (up.length >= 2 && cr(up[up.length - 2], up[up.length - 1], q) <= 0) up.pop(); up.push(q); }
  return lo.slice(0, -1).concat(up.slice(0, -1));
}

// stars
const N = SYS.length;
const starPos = new Float32Array(N * 3), starSize = new Float32Array(N), starBright = new Float32Array(N);
SYS.forEach((s, i) => { const v = W3(s); starPos.set([v.x, v.y, v.z], i * 3); });
const starGeo = new THREE.BufferGeometry();
starGeo.setAttribute('position', new THREE.BufferAttribute(starPos, 3));
starGeo.setAttribute('size', new THREE.BufferAttribute(starSize, 1));
starGeo.setAttribute('bright', new THREE.BufferAttribute(starBright, 1));
const starMat = new THREE.ShaderMaterial({
  transparent: true, depthWrite: false,
  uniforms: { uScale: { value: 1 } },
  vertexShader: `attribute float size; attribute float bright; varying float vB; uniform float uScale;
    void main(){ vB = bright; vec4 mv = modelViewMatrix * vec4(position,1.0); gl_PointSize = size * uScale; gl_Position = projectionMatrix * mv; }`,
  fragmentShader: `varying float vB; void main(){ vec2 p = gl_PointCoord*2.0-1.0; float d = length(p);
    float core = smoothstep(0.42,0.30,d); float halo = smoothstep(1.0,0.2,d)*0.35;
    float a = (core + halo) * vB; if(a<0.01) discard; gl_FragColor = vec4(1.0,1.0,1.0,a); }`,
});
const stars = new THREE.Points(starGeo, starMat);
scene.add(stars);
// black holes: a dark core inside a bright accretion ring
{
  const bh = []; SYS.forEach((s) => { if (s.blackhole) { const v = W3(s); bh.push(v.x, v.y, v.z); } });
  if (bh.length) {
    const g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.Float32BufferAttribute(bh, 3));
    const m = new THREE.ShaderMaterial({
      transparent: true, depthWrite: false, uniforms: { uScale: { value: 1 } },
      vertexShader: `uniform float uScale; void main(){ vec4 mv = modelViewMatrix * vec4(position,1.0); gl_PointSize = 30.0 * uScale; gl_Position = projectionMatrix * mv; }`,
      fragmentShader: `void main(){ vec2 p = gl_PointCoord*2.0-1.0; float d = length(vec2(p.x, p.y*2.2));
        float r = length(p);
        float disk = smoothstep(0.95,0.55,d) * smoothstep(0.30,0.42,d);
        float ring = smoothstep(0.48,0.40,r) * smoothstep(0.30,0.36,r);
        float glow = smoothstep(1.0,0.3,r)*0.18;
        vec3 col = mix(vec3(1.0,0.55,0.18), vec3(1.0,0.92,0.75), ring);
        float a = max(max(disk*0.9, ring), glow);
        if (r < 0.31) { gl_FragColor = vec4(0.0,0.0,0.0,1.0); return; }
        if (a < 0.01) discard; gl_FragColor = vec4(col, a); }`,
    });
    const pts = new THREE.Points(g, m); scene.add(pts); window.__bhMat = m;
  }
}
// companions of binary and trinary systems
{
  const cp = [];
  SYS.forEach((s) => { for (let k = 1; k < s.stars; k++) { const a = k * 2.3 + s.x; cp.push(s.x + Math.cos(a) * 0.55, s.z + 0.05, -(s.y + Math.sin(a) * 0.55)); } });
  const g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.Float32BufferAttribute(cp, 3));
  scene.add(new THREE.Points(g, new THREE.PointsMaterial({ color: 0xffffff, size: 3, sizeAttenuation: false, transparent: true, opacity: 0.7 })));
}
// drop lines to the plane
{
  const dl = [];
  SYS.forEach((s) => { if (Math.abs(s.z) > 0.1) dl.push(s.x, s.z, -s.y, s.x, 0, -s.y); });
  const g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.Float32BufferAttribute(dl, 3));
  scene.add(new THREE.LineSegments(g, new THREE.LineBasicMaterial({ color: 0xffffff, transparent: true, opacity: 0.22 })));
  const ft = []; SYS.forEach((s) => ft.push(s.x, 0, -s.y));
  const fg = new THREE.BufferGeometry(); fg.setAttribute('position', new THREE.Float32BufferAttribute(ft, 3));
  scene.add(new THREE.Points(fg, new THREE.PointsMaterial({ color: 0xffffff, size: 2, sizeAttenuation: false, transparent: true, opacity: 0.3 })));
}
// jump routes: every pair within a Pillai drive's 8 ly, plus the longer links that join the
// rest, so every star can be reached (built in build_data.py). Long links are dashed.
const routes = (() => {
  // lanes are straight lines, all in one style; the Rubin Void's charted routes are
  // gold and its uncharted approaches red
  const buckets = { lane: [], charted: [], hazard: [] };
  for (const [a, b, , kind] of data.routes) {
    const A = byId[a], B = byId[b];
    buckets[kind || 'lane'].push(A.x, A.z, -A.y, B.x, B.z, -B.y);
  }
  const grp = new THREE.Group();
  const add = (pts, mat) => {
    const g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.Float32BufferAttribute(pts, 3));
    const l = new THREE.LineSegments(g, mat); if (mat.isLineDashedMaterial) l.computeLineDistances(); grp.add(l);
  };
  add(buckets.lane, new THREE.LineBasicMaterial({ color: 0xe8b4a8, transparent: true, opacity: 0.42 }));
  add(buckets.charted, new THREE.LineDashedMaterial({ color: 0xf2c14e, transparent: true, opacity: 0.6, dashSize: 1.2, gapSize: 0.8 }));
  add(buckets.hazard, new THREE.LineDashedMaterial({ color: 0xe07a5f, transparent: true, opacity: 0.4, dashSize: 0.3, gapSize: 0.9 }));
  grp.visible = false; scene.add(grp); return grp;
})();

// ------------------------------------------------------------------ labels and markers (DOM)
const labelBox = $('#labels');
const labels = SYS.map((s) => { const d = document.createElement('div'); d.className = 'lb'; d.textContent = s.name; labelBox.appendChild(d); return d; });
const ring = document.createElement('div'); ring.className = 'sel-ring'; ring.hidden = true; labelBox.appendChild(ring);
let markers = [];
const layers = { ter: true, nam: true, reg: true, bat: true, rou: false, gri: true };

function buildMarkers() {
  markers.forEach((m) => m.el.remove()); markers = [];
  if (!layers.bat) return;
  const t = year + 0.999;
  const shown = new Set();
  for (const e of data.events.slice().reverse()) {
    if (e.y > t || e.y < year - 4) continue;
    const key = e.sys + (e.y >= year ? 'n' : 'o'); if (shown.has(e.sys)) continue; shown.add(e.sys);
    const el = document.createElement(hasArticle(e.slug) ? 'a' : 'button');
    el.className = 'mk ' + e.kind + (e.y < year ? ' old' : '');
    if (el.tagName === 'A') el.href = wikiHref(e.slug); else { el.type = 'button'; el.style.cssText = 'background:none;border:0;padding:0;font:inherit'; el.addEventListener('click', () => select(e.sys, true)); }
    el.innerHTML = '<i></i><span>' + esc(e.label) + '</span>';
    el.title = e.label + ', ' + fmtDate(e.y);
    labelBox.appendChild(el);
    markers.push({ el, s: byId[e.sys], key });
  }
}

// ------------------------------------------------------------------ year state
let selected = null;
function applyYear() {
  const t = year + 0.999;
  SYS.forEach((s, i) => {
    const o = ownerAt(s, t), w = worldsAt(s.id, t).length, burned = burnedAt(s.id, t).length;
    starSize[i] = w ? 13 : o ? 9 : 7.5;
    starBright[i] = s.blackhole ? 0 : w ? 1 : o ? 0.85 : 0.55;
    const l = labels[i];
    l.classList.toggle('on', !!w);
    l.classList.toggle('big', s.id === 'sol' || (w && worldsAt(s.id, t).length >= 2));
    l.classList.toggle('burn', !!burned);
    l.dataset.rank = s.id === 'sol' ? 3 : w ? 2 : o ? 1 : 0;
    l._w = 0;
  });
  starGeo.attributes.size.needsUpdate = true; starGeo.attributes.bright.needsUpdate = true;
  paintTerritory(t);
  buildMarkers();
  // panel
  $('#year-big').textContent = year;
  $('#year-era').textContent = eraOf(year);
  $('#year-cap').textContent = captionOf(year);
  const evs = data.events.filter((e) => Math.floor(e.y) === year);
  $('#thisyear').innerHTML = evs.length ? '<p class="k">This year</p><ol>' + evs.map((e) => {
    const m = Math.floor((e.y - year) * 12 + 1e-6);
    const lbl = hasArticle(e.slug) ? '<a href="' + wikiHref(e.slug) + '">' + esc(e.label) + '</a>' : esc(e.label);
    return '<li><time>' + MONTHS[m].slice(0, 3).toUpperCase() + '</time><span>' + lbl + ' · <button type="button" class="go" data-sys="' + e.sys + '" style="background:none;border:0;padding:0;color:var(--muted);font:inherit;cursor:pointer;text-decoration:underline;text-underline-offset:3px">' + esc(byId[e.sys].name) + '</button></span></li>';
  }).join('') + '</ol>' : '';
  $('#foot-title').textContent = 'Known space - ' + year;
  $('#foot-sub').textContent = evs.length ? evs[evs.length - 1].label : eraOf(year);
  // legend: polities present this year
  const present = new Set(SYS.map((s) => ownerAt(s, t)).filter(Boolean).map((o) => o.p));
  const legend = Object.keys(P).filter((k) => present.has(k)).map((k) => '<span>' + polKey(k) + esc(P[k].name) + '</span>').join('');
  $('#legend').innerHTML = legend + (layers.reg && year >= 2302 ? '<span><i class="sec"></i>Republic sector</span>' : '') + (layers.bat ? '<span><i class="bt"></i>Battle or event</span>' : '');
  if (selected) renderSelected();
  if (!$('#sysview').hidden && sv.sys) renderSystemInfo();
  const tl = $('#timeline'); tl.setAttribute('aria-valuenow', year); tl.setAttribute('aria-valuetext', year + ', ' + eraOf(year));
  writeHash();
}
$('#thisyear').addEventListener('click', (e) => { const b = e.target.closest('.go'); if (b) select(b.dataset.sys, true); });

// ------------------------------------------------------------------ selection panel
function sectorFlag(name) {
  const sec = (data.sectors || []).find((x) => x.name === name);
  return sec && sec.flag ? '<img class="flagkey secflag" src="assets/flags/' + sec.flag + '" alt=""> ' : '';
}
function secLink(name) {
  const slug = name.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');
  return hasArticle(slug) ? '<a href="' + wikiHref(slug) + '">' + esc(name) + '</a>' : esc(name);
}
function regionOf(s) {
  const sec = (data.sectors || []).find((x) => x.members.includes(s.id));
  if (sec) return sec.name;
  if (s.region2235 === 'rubin') return 'Rubin Void';
  let best = null, bd = 1e9;
  for (const r of data.regions) { const d = Math.hypot(r.x - s.x, r.y - s.y); if (d < bd) { bd = d; best = r; } }
  return bd < 22 ? best.name : null;
}
function ownHistory(s) {
  const out = []; let last = null;
  for (const e of s.own) {
    const p = e.p === 'human' ? humanName(e.from) : e.p;
    const key = p + (e.note || '');
    if (key === last) continue; last = key;
    out.push({ y: e.from, p, note: e.note, derived: e.derived });
  }
  return out;
}
function renderSelected() {
  const s = selected, t = year + 0.999, o = ownerAt(s, t);
  const ws = worldsAt(s.id, t), burned = burnedAt(s.id, t), reg = regionOf(s);
  const evs = data.events.filter((e) => e.sys === s.id);
  const dist = Math.hypot(s.x, s.y, s.z);
  const slug = s.id;
  let desc;
  if (ws.length) desc = ws.length === 1 ? ws[0].name + ' is its settled world.' : ws.map((w) => w.name).join(', ').replace(/, ([^,]*)$/, ' and $1') + ' are its settled worlds.';
  else if (o) desc = 'Held by the ' + polName(o.p) + '. No settled world is charted here.';
  else desc = 'Unclaimed. Charted, but held by no known power.';
  if (burned.length) desc += ' ' + burned.map((b) => b.name).join(' and ') + ' burned in ' + Math.floor(burned[0].y) + '.';
  const held = o ? (P[o.p] && P[o.p].flag ? '<img class="sw flagkey" src="assets/flags/' + P[o.p].flag + '" alt="">' : '<span class="sw" style="background:' + polColor(o.p) + '"></span>') + esc(polName(o.p)) + (o.note ? ' <span style="color:var(--muted)">(' + esc(o.note) + ')</span>' : '') + (o.derived ? '<sup class="drv" title="Date reconstructed, not stated in the book">†</sup>' : '') : 'Unclaimed';
  const evHtml = evs.length ? '<ul>' + evs.map((e) => '<li>' + (hasArticle(e.slug) ? '<a href="' + wikiHref(e.slug) + '">' + esc(e.label) + '</a>' : esc(e.label)) + ', ' + Math.floor(e.y) + '</li>').join('') + '</ul>' : '';
  const wHtml = ws.length ? '<ul>' + ws.map((w) => '<li>' + (hasArticle(w.slug) ? '<a href="' + wikiHref(w.slug) + '">' + esc(w.name) + '</a>' : esc(w.name)) + (w.native ? '' : ', ' + Math.floor(w.settled)) + '</li>').join('') + '</ul>' : '';
  $('#selected').innerHTML =
    '<div class="hd"><button type="button" class="x" aria-label="Close">×</button>' +
    '<span class="k">' + (reg ? sectorFlag(reg) + secLink(reg) + ' // ' : '') + esc(o ? polName(o.p) : 'Unclaimed') + '</span>' +
    '<h1>' + esc(s.name) + '</h1><span class="ds">' + esc(desc) + '</span></div>' +
    '<dl><dt>Held by</dt><dd>' + held + '</dd>' +
    (wHtml ? '<dt>Worlds</dt><dd>' + wHtml + '</dd>' : '') +
    (s.catalogue ? '<dt>Catalogue</dt><dd>' + esc(s.catalogue) + '</dd>' : '') +
    (s.hazard ? '<dt>Hazard</dt><dd style="color:#F0B6A8">' + esc(s.hazard) + '</dd>' : '') +
    '<dt>From Sol</dt><dd>' + (s.id === 'sol' ? '—' : dist.toFixed(1) + ' light years') + '</dd>' +
    '<dt>Stars</dt><dd>' + (s.blackhole ? 'Black hole' : ['Single', 'Binary', 'Trinary'][s.stars - 1]) + '</dd>' +
    (evHtml ? '<dt>Events</dt><dd>' + evHtml + '</dd>' : '') + '</dl>' +
    (hasArticle(slug) ? '<a class="open" href="' + wikiHref(slug) + '">Read the article<span aria-hidden="true">→</span></a>' : '') +
    '<button type="button" class="open" id="open-sys">Open system view<span aria-hidden="true">→</span></button>' +
    '<p class="note">Or double-click any star.</p>';
  $('#selected').hidden = false;
  $('#selected .x').onclick = () => select(null);
  $('#open-sys').onclick = () => openSystem(s.id);
}
function select(id, fly) {
  selected = id ? byId[id] : null;
  ring.hidden = !selected;
  if (!selected) { $('#selected').hidden = true; writeHash(); return; }
  renderSelected();
  if (fly) flyTo(selected);
  writeHash();
}

// ------------------------------------------------------------------ camera moves
let anim = null;
function flyTo(s, dist = 70) {
  const tgt = W3(s); tgt.y = 0;
  const off = camera.position.clone().sub(controls.target);
  off.setLength(Math.min(off.length(), dist));
  anim = { t0: performance.now(), d: 700, fromT: controls.target.clone(), toT: tgt, fromP: camera.position.clone(), toP: tgt.clone().add(off) };
}
function goHome() { anim = { t0: performance.now(), d: 700, fromT: controls.target.clone(), toT: HOME.target.clone(), fromP: camera.position.clone(), toP: HOME.pos.clone() }; }
function zoomBy(f) {
  const off = camera.position.clone().sub(controls.target);
  const len = Math.max(controls.minDistance, Math.min(controls.maxDistance, off.length() * f));
  anim = { t0: performance.now(), d: 300, fromT: controls.target.clone(), toT: controls.target.clone(), fromP: camera.position.clone(), toP: controls.target.clone().add(off.setLength(len)) };
}
$('#zoom-in').onclick = () => zoomBy(0.7);
$('#zoom-out').onclick = () => zoomBy(1.4);
$('#reset').onclick = goHome;

// ------------------------------------------------------------------ picking
const proj = new Array(N);
const v3 = new THREE.Vector3();
function project() {
  const w = canvas.clientWidth, h = canvas.clientHeight;
  for (let i = 0; i < N; i++) {
    v3.set(starPos[i * 3], starPos[i * 3 + 1], starPos[i * 3 + 2]).project(camera);
    proj[i] = { x: (v3.x + 1) / 2 * w, y: (1 - v3.y) / 2 * h, vis: v3.z < 1 && v3.z > -1 };
  }
}
function pick(ev) {
  const r = canvas.getBoundingClientRect(), x = ev.clientX - r.left, y = ev.clientY - r.top;
  let best = -1, bd = 16;
  for (let i = 0; i < N; i++) { const p = proj[i]; if (!p || !p.vis) continue; const d = Math.hypot(p.x - x, p.y - y); if (d < bd) { bd = d; best = i; } }
  return best;
}
let down = null, hover = -1;
canvas.addEventListener('pointerdown', (e) => { down = { x: e.clientX, y: e.clientY, t: performance.now() }; });
canvas.addEventListener('pointerup', (e) => {
  if (!down) return;
  const moved = Math.hypot(e.clientX - down.x, e.clientY - down.y);
  if (moved < 5 && e.button === 0) { const i = pick(e); if (i >= 0) select(SYS[i].id); }
  down = null;
});
canvas.addEventListener('dblclick', (e) => { const i = pick(e); if (i >= 0) { select(SYS[i].id); openSystem(SYS[i].id); } });
canvas.addEventListener('pointermove', (e) => {
  if (e.buttons) return;
  const i = pick(e);
  if (i !== hover) { if (hover >= 0) labels[hover].classList.remove('hov'); hover = i; if (i >= 0) labels[i].classList.add('hov'); canvas.style.cursor = i >= 0 ? 'pointer' : ''; }
});
canvas.addEventListener('contextmenu', (e) => e.preventDefault());

// ------------------------------------------------------------------ layers
for (const k of Object.keys(layers)) {
  const el = $('#l-' + k); if (!el) continue;
  el.addEventListener('change', () => {
    layers[k] = el.checked;
    grid.visible = layers.gri; routes.visible = layers.rou;
    if (k === 'ter' || k === 'reg') paintTerritory(year + 0.999);
    if (k === 'bat') { buildMarkers(); applyYear(); }
  });
}
$('#toggle-controls').addEventListener('click', (e) => {
  const c = $('#controls'), open = c.classList.toggle('closed');
  e.currentTarget.setAttribute('aria-expanded', String(!open));
});
if (window.innerWidth < 900) { $('#controls').classList.add('closed'); $('#toggle-controls').setAttribute('aria-expanded', 'false'); }

// ------------------------------------------------------------------ search
const find = $('#find'), results = $('#find-results');
let hits = [], hitIx = 0;
function showHits() {
  results.innerHTML = hits.map((s, i) => {
    const o = ownerAt(s, year + 0.999);
    return '<li role="option" data-id="' + s.id + '" aria-selected="' + (i === hitIx) + '">' + esc(s.name) + '<small>' + esc(o ? polName(o.p) : 'Unclaimed') + '</small></li>';
  }).join('');
  results.classList.toggle('open', hits.length > 0);
}
find.addEventListener('input', () => {
  const q = find.value.trim().toLowerCase();
  const worldHit = (s) => data.worlds.some((w) => w.sys === s.id && w.name.toLowerCase().includes(q));
  hits = q ? SYS.filter((s) => s.name.toLowerCase().includes(q) || worldHit(s)).sort((a, b) => a.name.toLowerCase().indexOf(q) - b.name.toLowerCase().indexOf(q)).slice(0, 8) : [];
  hitIx = 0; showHits();
});
find.addEventListener('keydown', (e) => {
  if (e.key === 'ArrowDown') { hitIx = Math.min(hits.length - 1, hitIx + 1); showHits(); e.preventDefault(); }
  else if (e.key === 'ArrowUp') { hitIx = Math.max(0, hitIx - 1); showHits(); e.preventDefault(); }
  else if (e.key === 'Enter' && hits[hitIx]) { select(hits[hitIx].id, true); hits = []; showHits(); find.blur(); }
  else if (e.key === 'Escape') { hits = []; showHits(); }
});
results.addEventListener('mousedown', (e) => { const li = e.target.closest('li'); if (li) { select(li.dataset.id, true); hits = []; showHits(); find.value = ''; } });
find.addEventListener('blur', () => setTimeout(() => { hits = []; showHits(); }, 150));

// ------------------------------------------------------------------ timeline
const tlBox = $('#timeline'), tl = $('#tl'), tlg = tl.getContext('2d');
let tlPos = year;               // fractional, follows drags
let VISIBLE_YEARS = window.innerWidth < 700 ? 30 : 60;
window.addEventListener('resize', () => { VISIBLE_YEARS = window.innerWidth < 700 ? 30 : 60; });
// before 2040 the strip shows more years at once, up to ten times as many, so the deep past is quick to cross
const spanAt = (p) => (p >= 2040 ? VISIBLE_YEARS : VISIBLE_YEARS * Math.min(10, 1 + (2040 - p) / 30));
const tickStep = (span) => (span <= 90 ? 1 : span <= 200 ? 5 : span <= 400 ? 10 : 25);
const EV_Y = data.events.map((e) => e.y);
function drawTimeline() {
  const dpr = Math.min(2, window.devicePixelRatio || 1);
  const w = tlBox.clientWidth, h = tlBox.clientHeight;
  if (tl.width !== Math.round(w * dpr) || tl.height !== Math.round(h * dpr)) { tl.width = Math.round(w * dpr); tl.height = Math.round(h * dpr); }
  tlg.setTransform(dpr, 0, 0, dpr, 0, 0);
  tlg.clearRect(0, 0, w, h);
  const span = spanAt(tlPos), st = tickStep(span);
  const ppy = w / span, mid = w / 2, cyy = h / 2 - 4;
  const y0 = Math.floor((tlPos - span / 2 - 1) / st) * st, y1 = Math.ceil(tlPos + span / 2 + 1);
  tlg.font = "500 9px 'Jost', sans-serif"; tlg.textAlign = 'center'; tlg.textBaseline = 'alphabetic';
  for (let y = y0; y <= y1; y += st) {
    if (y < RANGE[0] || y > RANGE[1]) continue;
    const x = mid + (y - tlPos) * ppy;
    if (x < -2 || x > w + 2) continue;
    const d = Math.min(1, Math.abs(x - mid) / mid);
    const grow = 1 + 0.75 * Math.pow(1 - d, 2);
    const decade = y % (10 * st) === 0;
    const isCur = st === 1 ? y === year : false;
    let bh = (decade ? 22 : 13) * grow;
    if (isCur) bh = 34;
    const lw = isCur ? 3 : decade ? 1.4 : 1;
    const a = isCur ? 1 : (0.35 + 0.55 * (1 - d)) * (decade ? 1 : 0.8);
    tlg.fillStyle = 'rgba(255,255,255,' + a + ')';
    tlg.fillRect(Math.round(x - lw / 2), cyy - bh / 2, lw, bh);
    if (!isCur && EV_Y.some((ey) => ey >= y && ey < y + st)) { tlg.fillStyle = 'rgba(242,193,78,' + (0.35 + 0.5 * (1 - d)) + ')'; tlg.fillRect(Math.round(x) - 1.5, cyy - bh / 2 - 6, 3, 3); }
    if (decade && !isCur && Math.abs(x - mid) > 34) { tlg.fillStyle = 'rgba(169,187,208,' + (0.25 + 0.5 * (1 - d)) + ')'; tlg.fillText(String(y), x, h - 6); }
  }
  if (st > 1) { tlg.fillStyle = '#fff'; tlg.fillRect(Math.round(mid + (year - tlPos) * ppy - 1.5), cyy - 17, 3, 34); }
  // current year readout under the bold bar
  tlg.font = "600 11px 'Jost', sans-serif"; tlg.fillStyle = '#fff';
  if ('letterSpacing' in tlg) tlg.letterSpacing = '1.5px';
  tlg.fillText(String(year), mid, h - 5);
  if ('letterSpacing' in tlg) tlg.letterSpacing = '0px';
}
function setPos(p, snap) {
  tlPos = Math.max(RANGE[0], Math.min(RANGE[1], p));
  const y = Math.round(tlPos);
  if (y !== year) { year = y; applyYear(); }
  if (snap) tlPos = year;
  drawTimeline();
}
let drag = null, glide = null;
tlBox.addEventListener('pointerdown', (e) => {
  tlBox.setPointerCapture(e.pointerId); tlBox.classList.add('drag');
  drag = { x: e.clientX, pos: tlPos, lastX: e.clientX, lastT: performance.now(), v: 0, moved: 0 }; glide = null;
});
tlBox.addEventListener('pointermove', (e) => {
  if (!drag) return;
  const ppy = tlBox.clientWidth / spanAt(tlPos), now = performance.now();
  const dx = e.clientX - drag.lastX, dt = Math.max(1, now - drag.lastT);
  drag.v = 0.8 * (-dx / ppy / dt) + 0.2 * drag.v; drag.lastX = e.clientX; drag.lastT = now; drag.moved += Math.abs(dx);
  setPos(drag.pos - (e.clientX - drag.x) / ppy);
});
const endDrag = (e) => {
  if (!drag) return;
  tlBox.classList.remove('drag');
  if (drag.moved < 4) { // a click jumps to the year under the pointer
    const r = tlBox.getBoundingClientRect(), ppy = r.width / spanAt(tlPos);
    glide = { target: Math.round(tlPos + (e.clientX - r.left - r.width / 2) / ppy) };
  } else glide = { v: drag.v };
  drag = null;
};
tlBox.addEventListener('pointerup', endDrag); tlBox.addEventListener('pointercancel', endDrag);
tlBox.addEventListener('wheel', (e) => { e.preventDefault(); glide = null; setPos(tlPos + (Math.abs(e.deltaX) > Math.abs(e.deltaY) ? e.deltaX : e.deltaY) / 40 * spanAt(tlPos) / VISIBLE_YEARS); clearTimeout(tlBox._t); tlBox._t = setTimeout(() => { glide = { target: Math.round(tlPos) }; }, 160); }, { passive: false });
tlBox.addEventListener('keydown', (e) => {
  const step = { ArrowLeft: -1, ArrowRight: 1, ArrowDown: -1, ArrowUp: 1, PageDown: -10, PageUp: 10 }[e.key];
  if (step) { e.preventDefault(); glide = { target: Math.round(tlPos) + step }; }
  if (e.key === 'Home') glide = { target: RANGE[0] };
  if (e.key === 'End') glide = { target: RANGE[1] };
});
function stepGlide(dt) {
  if (!glide || drag) return;
  if (glide.v !== undefined) {
    setPos(tlPos + glide.v * dt);
    glide.v *= Math.pow(0.004, dt / 1000);
    if (Math.abs(glide.v) < 0.002) glide = { target: Math.round(tlPos) };
  } else {
    const d = glide.target - tlPos;
    if (Math.abs(d) < 0.01) { setPos(glide.target, true); glide = null; }
    else setPos(tlPos + d * Math.min(1, dt / 90));
  }
}

// ------------------------------------------------------------------ system view
const sv = { sys: null, speed: 0.25, t: 0, planets: [], zoom: 1, pick: null };
function rngFor(id) { let h = 2166136261; for (const c of id) h = Math.imul(h ^ c.charCodeAt(0), 16777619); return () => ((h = Math.imul(h ^ (h >>> 15), 2246822507) ^ Math.imul(h ^ (h >>> 13), 3266489909)) >>> 0) / 4294967296; }
const TYPES_IN = ['Molten world', 'Tidally locked rock', 'Hot cloud world', 'Barren rock'];
const TYPES_MID = ['Barren world', 'Frozen desert', 'Ocean world', 'Steppe world', 'Barren world'];
const TYPES_OUT = ['Gas giant', 'Ringed gas giant', 'Ice giant', 'Frozen dwarf'];
const TYPES_DEAD = ['Barren world', 'Frozen world', 'Molten world', 'Irradiated rock', 'Barren world'];
// flags flown on a world in a given year; Earth before 1 June 2283 flies its states' flags
// a world without its own flag flies its owner's banner, if that power has one (the Voor roundel)
function flagsAt(name, t) {
  const tl = (data.flags || {})[sv.sys.id + ':' + name]; let f = [];
  if (tl) { for (const [y, fs] of tl) if (y <= t) f = fs; return f; }
  const o = ownerAt(sv.sys, t), pol = o && P[o.p];
  return pol && pol.flag ? [pol.flag] : [];
}
const isRound = (f) => (data.roundFlags || []).includes(f);
function flagRow(fs, x, y, h) {
  const per = 6; let out = '', fx = x;
  fs.forEach((f, k) => {
    if (k && k % per === 0) fx = x;
    const fy = y + Math.floor(k / per) * (h + 3);
    if ((data.squareFlags || []).includes(f)) {
      out += '<image href="assets/flags/' + f + '" x="' + fx + '" y="' + fy + '" width="' + h + '" height="' + h + '"/>';
      fx += h + 3;
    } else if (isRound(f)) {
      const d = h * 1.35, cy = fy + h / 2;
      out += '<image href="assets/flags/' + f + '" x="' + fx + '" y="' + (cy - d / 2) + '" width="' + d + '" height="' + d + '"/>';
      fx += d + 3;
    } else {
      const w = h * 1.5;
      out += '<image href="assets/flags/' + f + '" x="' + fx + '" y="' + fy + '" width="' + w + '" height="' + h + '" preserveAspectRatio="xMidYMid slice"/>' +
        '<rect x="' + fx + '" y="' + fy + '" width="' + w + '" height="' + h + '" fill="none" stroke="#fff" stroke-opacity=".5" stroke-width=".75"/>';
      fx += w + 3;
    }
  });
  return out;
}
// a polity's key in a legend: its banner where it has one, else its colour
function polKey(k) {
  const pol = P[k];
  return pol && pol.flag ? '<img class="flagkey" src="assets/flags/' + pol.flag + '" alt="">' : '<i style="background:' + (pol ? pol.color : polColor(k)) + '"></i>';
}
function makePlanets(s) {
  const r = rngFor(s.id);
  if (s.id === 'sol') {
    const solW = data.worlds.filter((w) => w.sys === 'sol');
    const moonsOf = (n) => solW.filter((w) => w.moon && w.pl === n).map((w) => ({ name: w.name, slug: w.slug, settled: w.settled, known: w.known, world: true, ph: r() * 6.28 }));
    return ['Mercury', 'Venus', 'Earth', 'Mars', 'Jupiter', 'Saturn', 'Uranus', 'Neptune'].map((n, i) => {
      const w = solW.find((x) => x.name === n);
      const moons = moonsOf(i + 1);
      if (n === 'Saturn') moons.push({ name: 'Titan', settled: 2150, world: true, ph: r() * 6.28 });
      return { name: n, a: [0.39, 0.72, 1, 1.52, 5.2, 9.5, 19.2, 30][i], size: [3, 5, 5.5, 4, 11, 10, 7, 7][i],
        type: ['Rock', 'Cloud world', 'Homeworld of humanity', 'Terraformed world', 'Gas giant', 'Ringed gas giant', 'Ice giant', 'Ice giant'][i],
        ring: i === 5, world: w ? n : null, slug: w && w.slug, settled: w ? w.settled : undefined, known: w && w.known, biome: w && w.biome, ph: r() * 6.28, moons, giant: i >= 4 };
    });
  }
  const known = data.worlds.filter((w) => w.sys === s.id);
  const names = (data.planetNames || {})[s.id] || {};
  const maxPl = Math.max(0, ...known.map((w) => w.pl || 0), ...Object.keys(names).map(Number));
  const n = Math.max(maxPl + 1 + Math.floor(r() * 2), known.length + 2, 3 + Math.floor(r() * 6));
  const hz = 1 + Math.floor(r() * 2);
  const out = []; let a = 0.25 + r() * 0.25;
  for (let i = 0; i < n; i++) {
    const MID = (s.region2235 === 'rubin' || s.blackhole) ? TYPES_DEAD : TYPES_MID;   // nothing habitable in the Rubin Void or round a black hole
    const type = i < hz ? TYPES_IN[Math.floor(r() * TYPES_IN.length)] : i < hz + 2 ? MID[Math.floor(r() * MID.length)] : TYPES_OUT[Math.floor(r() * TYPES_OUT.length)];
    out.push({ name: names[i + 1] || s.name + ' ' + ROMAN[i], a, type, ph: r() * 6.28, world: null, moons: [] });
    a *= 1.5 + r() * 0.6;
  }
  const free = [];
  for (const w of known) {
    if (!w.pl) { free.push(w); continue; }
    const p = out[w.pl - 1];
    if (w.moon) p.moons.push({ name: w.name, slug: w.slug, settled: w.settled, known: w.known, world: true, ph: r() * 6.28 });
    else { p.world = w.name; p.slug = w.slug; p.settled = w.settled; p.known = w.known; p.biome = w.biome; }
  }
  for (const b of (data.bodies || {})[s.id] || []) {
    const p = out[b.pl - 1]; if (!p) continue;
    p.name = b.name; p.type = b.type; p.body = b;
  }
  const order = out.map((p, i) => i).filter((i) => !out[i].world && !out[i].body).sort((x, y) => Math.abs(x - hz - 0.5) - Math.abs(y - hz - 0.5));
  free.forEach((w, k) => { const p = out[order[k]]; if (p) { p.world = w.name; p.slug = w.slug; p.settled = w.settled; p.known = w.known; p.biome = w.biome; } });
  for (const p of out) {
    if (p.moons.length && !p.world && !/giant/.test(p.type)) p.type = 'Gas giant';
    if (p.world && /giant/.test(p.type)) p.type = 'Barren world';
    p.giant = /giant/.test(p.type);
    p.size = p.giant ? 8 + r() * 4 : 3 + r() * 3;
    p.ring = /Ringed/.test(p.type);
  }
  return out;
}
function openSystem(id) {
  const s = byId[id]; sv.sys = s; sv.planets = makePlanets(s); sv.zoom = 1; sv.pick = null;
  $('#sysview').hidden = false;
  svBuild(true);
  renderSystemInfo();
  writeHash();
}
function closeSystem() { $('#sysview').hidden = true; sv.sys = null; writeHash(); }
$('#sv-back').onclick = closeSystem;
document.addEventListener('keydown', (e) => { if (e.key === 'Escape' && !$('#sysview').hidden) closeSystem(); });
$('#sv-names').addEventListener('change', (e) => $('#sv-map').classList.toggle('nonames', !e.target.checked));
$('#sv-home').onclick = () => { sv.pick = null; svFocus(null); renderSystemInfo(); };
sv.hits = [];
$('#sv-info').addEventListener('click', (e) => { const b = e.target.closest('[data-b]'); if (b) { sv.pick = b.dataset.b; svFocus(sv.pick); renderSystemInfo(); } });

const chev = '<svg width="14" height="14" viewBox="0 0 16 16" fill="none" stroke="#A9BBD0" stroke-width="1.6" aria-hidden="true"><path d="M4 6l4 4 4-4"/></svg>';
// a clan's monoliths in year t: at anchor, away with the fleets, failed into hulks, or lost (and where)
const clanName = (id) => ((data.clans || []).find((c) => c.id === id) || { name: id }).name;
function clanStatus(c, t) {
  let home = 0, away = 0, hulks = 0; const lost = [];
  for (const m of c.mon) {
    if (m.fate && m.fate.y <= t) { lost.push(m); continue; }
    const gone = m.depart && t >= m.depart && !(m.back && t >= m.back);
    if (gone) away++;
    else if (m.end && m.end !== c.home && m.back && t >= m.back) away++;
    else if (m.hulk && t >= m.hulk) hulks++;
    else home++;
  }
  const parts = [];
  if (home) parts.push(home + (home > 1 ? ' monoliths' : ' monolith') + ' at anchor');
  if (away) parts.push(away + ' with the fleets');
  if (hulks) parts.push(hulks + (hulks > 1 ? ' hulks' : ' hulk'));
  const lostAt = new Map();
  lost.sort((a, b) => a.fate.y - b.fate.y);
  for (const m of lost) {
    if (m.name) { parts.push(m.name + ' lost at ' + m.fate.label + ', ' + Math.floor(m.fate.y)); continue; }
    const k = m.fate.label + ', ' + Math.floor(m.fate.y);
    lostAt.set(k, (lostAt.get(k) || 0) + 1);
  }
  for (const [k, n] of lostAt) parts.push((n > 1 ? n + ' ' : '') + 'lost at ' + k);
  if (!home && !away && !hulks) parts.push(c.gone && t >= c.gone ? 'hulks and stations taken, ' + Math.floor(c.gone) : 'hulks and stations');
  return '<img class="sw flagkey" src="assets/flags/clans/' + c.id + '.png" alt=""> ' + esc(parts.join('; ') || 'stations');
}
// Fevarian features the system view lets you pick, and the card each one opens in the panel
const PICKABLE = new Set(['navy', 'fleet', 'clanfleet', 'clanhulk', 'clanbase', 'orbital', 'hulk', 'wreck', 'hedge']);
const FEAT_KIND = { navy: 'Fleet', fleet: 'Monolith fleet', clanfleet: 'Clan anchorage', clanhulk: 'Clan hulks', clanbase: 'Clan hulks and stations', orbital: 'Fevarian orbital settlement', hulk: 'Hulk anchorage', wreck: 'Monolith wrecks', hedge: 'Thaali march hedge' };
const clanLink = (id) => hasArticle(id) ? '<a href="' + wikiHref(id) + '">' + esc(clanName(id)) + '</a>' : esc(clanName(id));
const clanHead = (id, sz = 14) => '<img class="sw flagkey" src="assets/flags/clans/' + id + '.png" alt="" style="width:' + sz + 'px;height:' + sz + 'px">';
function featInfo(f, t) {
  if (f.kind === 'navy') {
    const rows = [['Side', esc(f.side)], ['Strength', esc(f.strength)], ['Here', (f.from < RANGE[0] ? 'Since before ' + RANGE[0] : fmtDate(f.from)) + (f.to && f.to < RANGE[1] ? ' to ' + fmtDate(f.to) : ' onward')]];
    if (hasArticle(f.slug)) rows.push(['Article', '<a href="' + wikiHref(f.slug) + '">' + esc(typeof articles[f.slug] === 'string' ? articles[f.slug] : (articles[f.slug].title || f.slug)) + '</a>']);
    return '<div class="sv-feat"><span class="k">Fleet</span><h2>' + esc(f.name) + '</h2></div>' + sec('Fleet', rows);
  }
  if (f.kind === 'wreck') {
    const rows = [['Date', fmtDate(f.from)]];
    if (hasArticle(f.slug)) rows.push(['Article', '<a href="' + wikiHref(f.slug) + '">' + esc(f.title) + '</a>']);
    const lost = (f.sides || []).map((sd) => [sd.name, esc(sd.lost)]);
    let html = '<div class="sv-feat"><span class="k">Wreckage</span><h2>' + esc(f.title) + '</h2></div>' + sec('Battle', rows) + sec('Ships lost', lost);
    if (hasArticle(f.slug)) html += '<a class="art" href="' + wikiHref(f.slug) + '">Read the article →</a>';
    return html;
  }
  const c = f.clan ? (data.clans || []).find((x) => x.id === f.clan) : null;
  const head = c ? '<img src="assets/flags/clans/' + c.id + '-banner.png" alt="" style="height:150px;display:block;margin:6px auto 2px" onerror="this.src=\'assets/flags/clans/' + c.id + '.png\';this.style.height=\'64px\'">' : '';
  const rows = [['Kind', FEAT_KIND[f.kind] || f.kind]];
  if (c) {
    rows.push(['Clan', clanHead(c.id) + ' ' + clanLink(c.id)]);
    rows.push(['This year', clanStatus(c, t)]);
  }
  if (f.kind === 'hedge') rows.push(['State', f.broken ? 'Stripped of its generators by the Khanate' : 'A world field over the march world, raised by generator rings in three orbits']);
  if (f.n && f.kind !== 'clanbase') rows.push([f.kind === 'clanhulk' || f.kind === 'hulk' ? 'Hulks' : f.kind === 'orbital' ? 'Rings' : 'Monoliths', String(f.n)]);
  if (f.hearths) rows.push(['Captured hearths', String(f.hearths)]);
  rows.push(['Here', (f.from < 1900 ? (f.kind === 'hedge' ? 'Kept for centuries' : 'Since before the Khanate') : 'From ' + fmtDate(f.from)) + (f.to ? ' to ' + fmtDate(f.to) : '')]);
  if (f.clans && f.clans.length) rows.push(['Clans', f.clans.map((id) => clanHead(id) + ' ' + clanLink(id)).join('<br>')]);
  if (c && hasArticle(c.id)) rows.push(['Article', '<a href="' + wikiHref(c.id) + '">' + esc(c.name) + '</a>']);
  else if (f.slug && hasArticle(f.slug)) rows.push(['Article', '<a href="' + wikiHref(f.slug) + '">' + esc(typeof articles[f.slug] === 'string' ? articles[f.slug] : (articles[f.slug].title || f.slug)) + '</a>']);
  else if (f.kind !== 'hedge' && hasArticle('fevarian-clans')) rows.push(['Article', '<a href="' + wikiHref('fevarian-clans') + '">Fevarian clans</a>']);
  return '<div class="sv-feat">' + head + '<h2>' + esc(f.name) + '</h2></div>' + sec('Feature', rows);
}
function sec(title, rows) {
  return '<button type="button" class="sv-sec" aria-expanded="true">' + esc(title) + chev + '</button><table>' + rows.map(([k, v, later, rawKey]) => '<tr' + (later ? ' class="later"' : '') + '><th scope="row">' + (rawKey ? k : esc(k)) + '</th><td>' + v + '</td></tr>').join('') + '</table>';
}

// a body key is "3" for planet III, or "3.1" for its second moon
function bodyFor(key) {
  if (!key || !sv.sys) return null;
  const [pi, mi] = key.split('.').map(Number), p = sv.planets[pi];
  if (!p) return null;
  if (mi === undefined || Number.isNaN(mi)) {
    const settled = p.world && seenAt(p, year + 0.999);
    return { key, kind: 'planet', p, pi, label: settled ? p.world : p.name, world: p.world, slug: p.slug, settled: p.settled, biome: p.biome, type: p.type };
  }
  const m = p.moons[mi]; if (!m) return null;
  const wd = data.worlds.find((w) => w.sys === sv.sys.id && w.name === m.name) || {};
  return { key, kind: 'moon', p, pi, m, label: m.name, world: m.world ? m.name : null, slug: m.slug, settled: m.settled, biome: wd.biome, type: 'Moon' };
}
function bodyInfo(b, t, o) {
  const live = b.world && seenAt(b, t);
  const burned = live && burnedAt(sv.sys.id, t).find((x) => x.name === b.world);
  const rows = [];
  const parentName = b.p.world && seenAt(b.p, t) ? b.p.world : b.p.name;
  rows.push(['Designation', esc(b.kind === 'moon' ? 'Moon of ' + parentName : sv.sys.name + ' ' + ROMAN[b.pi])]);
  const bw = b.world && worldByName(sv.sys.id, b.world);
  rows.push(['Type', esc(live && bw && biomeAt(bw, t) ? biomeAt(bw, t) : b.type)]);
  if (b.world) {
    const w = data.worlds.find((x) => x.sys === sv.sys.id && x.name === b.world);
    if (w && w.native) rows.push(['Inhabited', 'Native world']);
    else if (b.settled !== undefined) rows.push([b.settled <= t ? 'Settled' : 'To be settled', esc(fmtDate(b.settled)), b.settled > t]);
    if (w && w.capital) rows.push(['Capital', esc(w.capital)]);
    if (w && w.ship) rows.push(['Colony ship', esc(w.ship)]);
    if (w && w.by && !w.native && w.settled < 2283) rows.push(['Settled by', esc(w.by)]);
    if (w && w.becomes && w.terraformed) {
      const est = w.terraformedEstimated ? '<sup class="drv" title="Date estimated">†</sup>' : '';
      if (t >= w.terraformed) rows.push(['Terraformed', esc(String(Math.floor(w.terraformed))) + est + ', from ' + esc(w.biome.toLowerCase())]);
      else rows.push(['Being remade as', esc(w.becomes) + ', complete c. ' + esc(String(Math.floor(w.terraformed))) + est]);
    }
    if (live) rows.push(['Status', burned ? 'Burned, ' + esc(fmtDate(burned.y)) : o ? esc(polName(o.p)) + (o.note ? ', ' + esc(o.note) : '') : 'Unclaimed']);
  } else rows.push(['Settled', 'No settlement']);
  if (b.kind === 'planet' && b.p.moons.length) rows.push(['Moons', b.p.moons.map((m, k) => '<button type="button" class="lnk" data-b="' + b.pi + '.' + k + '">' + esc(m.name) + '</button>').join(', ')]);
  if (b.kind === 'moon') rows.push(['Orbits', '<button type="button" class="lnk" data-b="' + b.pi + '">' + esc(parentName) + '</button>']);
  let h = '';
  const pg = b.world && live && planetByName[b.world];
  const solName = !b.world || !live ? (b.kind === 'moon' ? b.m.name : b.p.name) : null;
  if (pg) h += '<div class="sv-globe" data-world="' + esc(b.world) + '"></div>';
  else if (solName && SOL_BODIES[solName] && sv.sys.id === 'sol') h += '<div class="sv-globe" data-sol="' + SOL_BODIES[solName] + '"></div>';
  h += sec('Selected · ' + b.label, rows);
  if (pg) {
    // the world's towns in the year shown, with the far peoples' cities and the resettlement quarters marked
    const QN = { ossathi: ['Ossathi', 'ossathi'], veren: ['Veren', 'veren'], kaltam: ['Kal-Tam', 'kal-tam'], duresh: ['Dur-Esh', 'dur-esh'], returnee: ['Returned refugees', null], voorret: ['Returned Voor', null] };
    const towns = (pg.cities || []).filter((c) => c.n && (!c.k || c.k === 'quarter') && (!c.f || c.f <= t) && !(c.t && t >= c.t) && !(c.gap && t >= c.gap[0] && t < c.gap[1]));
    if (towns.length) h += sec('Towns', towns.slice(0, 16).map((c) => {
      let what = c.w >= 1 ? 'Capital' : 'Town';
      if (c.q && QN[c.q]) {
        const [nm, sl] = QN[c.q], ppl = sl && hasArticle(sl) ? '<a href="' + wikiHref(sl) + '">' + nm + '</a>' : nm;
        what = c.k === 'quarter' ? ppl + (sl ? ' quarter in exile' : ' quarter') : ppl + (sl ? ' city' : ' town');
      }
      return [esc(c.n), what + (c.f && c.f > 1900 ? ', ' + Math.floor(c.f) : '')];
    }));
  }
  if (b.slug && hasArticle(b.slug) && live) h += '<a class="art" href="' + wikiHref(b.slug) + '">Read about ' + esc(b.label) + ' →</a>';
  return h;
}
function renderSystemInfo() {
  const s = sv.sys, t = year + 0.999, o = ownerAt(s, t), ws = worldsAt(s.id, t), reg = regionOf(s);
  const evs = data.events.filter((e) => e.sys === s.id);
  const hist = ownHistory(s).filter((h) => h.y > RANGE[0]);
  const dist = Math.hypot(s.x, s.y, s.z);
  let html = '<div class="hd"><span class="k">' + esc(o ? polName(o.p) : 'Unclaimed') + '</span><h1>' + esc(s.name) + '</h1><span>Star system' + (reg ? ' · ' + sectorFlag(reg) + secLink(reg) : '') + '</span></div>';
  const body = bodyFor(sv.pick);
  if (body) html += bodyInfo(body, t, o);
  const pickedF = String(sv.pick || '').startsWith('f:') ? ((data.features || {})[s.id] || [])[+sv.pick.slice(2)] : null;
  if (pickedF) html += featInfo(pickedF, t);
  html += sec('Observation data · epoch ' + year, [
    ['Stars', s.blackhole ? 'Black hole' : ['Single', 'Binary', 'Trinary'][s.stars - 1]],
    ...(s.catalogue ? [['Catalogue name', esc(s.catalogue)]] : []),
    ...(s.hazard ? [['Hazard', '<span style="color:#F0B6A8">' + esc(s.hazard) + '</span>']] : []),
    ['Distance from Sol', s.id === 'sol' ? '—' : dist.toFixed(1) + ' ly'],
    ['Map position', s.x.toFixed(1) + ', ' + s.y.toFixed(1) + ', ' + s.z.toFixed(1) + ' ly<sup class="drv" title="Height above the plane is reconstructed">†</sup>'],
    ['Planets', String(sv.planets.length)],
  ]);
  html += sec('Sovereignty', [['Held by', o ? (P[o.p] && P[o.p].flag ? '<img class="sw flagkey" src="assets/flags/' + P[o.p].flag + '" alt="">' : '<span class="sw" style="background:' + polColor(o.p) + '"></span>') + esc(polName(o.p)) + (o.note ? ', ' + esc(o.note) : '') : 'Unclaimed']]
    .concat(hist.map((h) => [String(Math.floor(h.y)), esc(polName(h.p)) + (h.note ? ', ' + esc(h.note) : '') + (h.derived ? '<sup class="drv" title="Date reconstructed">†</sup>' : ''), h.y > t])));
  const clansHere = (data.clans || []).filter((c) => c.home === s.id);
  if (clansHere.length) {
    const rows = clansHere.map((c) => hasArticle(c.id) ? ['<a href="' + wikiHref(c.id) + '">' + esc(c.name) + '</a>', clanStatus(c, t), false, true] : [c.name, clanStatus(c, t)]);
    if (hasArticle('fevarian-clans')) rows.push(['Article', '<a href="' + wikiHref('fevarian-clans') + '">Fevarian clans</a>']);
    html += sec('Clans', rows);
  }
  const visiting = [];
  for (const f of ((data.features || {})[s.id] || [])) if (f.clans && t >= f.from && !(f.to && t >= f.to)) for (const c of f.clans) if (!visiting.includes(c) && !clansHere.some((x) => x.id === c)) visiting.push(c);
  if (visiting.length) html += sec('Clans in the system', [[visiting.length + ' clans', visiting.slice(0, 40).map((c) => '<img class="sw flagkey" src="assets/flags/clans/' + c + '.png" alt="" title="' + esc(clanName(c)) + '">').join('')]]);
  ((data.features || {})[s.id] || []).forEach((f, i) => { f._i = i; });
  const wrecks = ((data.features || {})[s.id] || []).filter((f) => f.kind === 'wreck' && f.from <= t);
  if (wrecks.length) html += sec('Wreckage', wrecks.map((f) => [String(Math.floor(f.from)), (hasArticle(f.slug) ? '<a href="' + wikiHref(f.slug) + '">' + esc(f.title) + '</a>' : esc(f.title)) + ' · <a href="#" class="pickf" data-k="f:' + f._i + '">show</a>']));
  if (ws.length) html += sec('Settled worlds', ws.map((w) => [w.name, (hasArticle(w.slug) ? '<a href="' + wikiHref(w.slug) + '">Article</a> · ' : '') + (w.native ? 'Native world' : fmtDate(w.settled))]));
  if (evs.length) html += sec('History', evs.map((e) => [fmtDate(e.y), hasArticle(e.slug) ? '<a href="' + wikiHref(e.slug) + '">' + esc(e.label) + '</a>' : esc(e.label), e.y > t]));
  if (hasArticle(s.id)) html += '<a class="art" href="' + wikiHref(s.id) + '">Read the article →</a>';
  $('#sv-info').innerHTML = html;
  const gEl = $('#sv-info .sv-globe');
  if (gEl) {
    // one globe per world, kept across year changes: a new WebGL context on every tick of the year slider
    // ran the browser out of contexts and it dropped the Atlas's own
    const key = gEl.dataset.world || ('sol:' + gEl.dataset.sol);
    const keep = PANEL_GLOBE.key === key ? PANEL_GLOBE : null;
    if (keep) {
      gEl.replaceWith(keep.el);
      if (gEl.dataset.world) keep.g.setYear(planetByName[gEl.dataset.world], t);
    } else {
      if (PANEL_GLOBE.g) PANEL_GLOBE.g.destroy();
      let g;
      if (gEl.dataset.world) {
        const p = planetByName[gEl.dataset.world];
        g = mountGlobe(THREE, gEl, { base: 'assets/planets/' + p.slug + '/', cities: p.cities, lon: (p.cities[0] || { lon: 0 }).lon, height: gEl.clientWidth });
        g.setYear(p, t);
      } else {
        g = mountGlobe(THREE, gEl, { base: 'assets/planets/_sol/', cities: [], height: gEl.clientWidth });
        g.set({ k: gEl.dataset.sol, atmo: null, glow: '#000000', noData: true });
      }
      PANEL_GLOBE = { key, el: gEl, g };
    }
  } else if (PANEL_GLOBE.g) { PANEL_GLOBE.g.destroy(); PANEL_GLOBE = {}; }
  $('#sv-info').querySelectorAll('.pickf').forEach((a) => a.addEventListener('click', (e) => { e.preventDefault(); sv.pick = a.dataset.k; svFocus(sv.pick); renderSystemInfo(); writeHash(); }));
  $('#sv-info').querySelectorAll('.sv-sec').forEach((b) => b.addEventListener('click', () => { const open = b.getAttribute('aria-expanded') === 'true'; b.setAttribute('aria-expanded', String(!open)); b.nextElementSibling.hidden = open; }));
  $('#sv-title').textContent = (body ? body.label : pickedF ? (pickedF.title || pickedF.name) : s.name) + ' - ' + year;
  const last = evs.filter((e) => e.y <= t).pop();
  $('#sv-sub').textContent = last ? last.label + ', ' + fmtDate(last.y) : (o ? polName(o.p) : 'Unclaimed');
  $('#sv-legend').innerHTML = o ? '<span>' + polKey(o.p) + esc(polName(o.p)) + '</span>' : '';
}
let PANEL_GLOBE = {};
// ------------------------------------------------------------------ system view, in 3D
// Drag to orbit and tilt, wheel or pinch to zoom, right-drag to pan. Clicking a planet or moon
// selects it and flies the camera to it; the camera then follows it round its orbit. Orbits use a
// log scale so inner and outer planets both fit; bodies are drawn far larger than to scale.
const S3 = { r: null, scene: null, cam: null, ctl: null, root: null, feat: null, bodies: [], globes: [], focus: null, fly: null, featYear: null, down: null };
const SVW = 10, PILLAI = 1.18;
const svR = (a) => { const amax = sv.planets[sv.planets.length - 1].a; return Math.log(1 + a * 4) / Math.log(1 + amax * 4) * SVW; };
const bodyR = (p) => 0.07 + p.size * 0.021;
const TEXC = new Map();
function canvasTex(key, draw, w = 256, h = 128) {
  if (TEXC.has(key)) return TEXC.get(key);
  const c = document.createElement('canvas'); c.width = w; c.height = h; draw(c.getContext('2d'), w, h);
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; TEXC.set(key, t); return t;
}
function seeded(str) { let h = 2166136261; for (const ch of str) h = Math.imul(h ^ ch.charCodeAt(0), 16777619); return () => ((h = Math.imul(h ^ (h >>> 15), 2246822507) ^ Math.imul(h ^ (h >>> 13), 3266489909)) >>> 0) / 4294967296; }
// a plain procedural surface for planets nobody has mapped, by type
function typeTex(type, name) {
  const pal = {
    'Gas giant': ['#c9a27a', '#e4cfa8', '#a7764f', '#efe2c6'], 'Ringed gas giant': ['#d9c08e', '#efe0b8', '#b89a6a', '#f6ecd0'],
    'Ice giant': ['#7fb4c9', '#a6d3e0', '#5d97b0', '#c2e6ee'], 'Frozen dwarf': ['#cfd6dc', '#aab4bd', '#e9eef2'],
    'Molten world': ['#3a1f17', '#7a2c12', '#e0581c', '#2a1712'], 'Tidally locked rock': ['#7d6e62', '#a49384', '#4e443d'],
    'Hot cloud world': ['#e8d39c', '#f3e5bd', '#cdb57b'], 'Barren rock': ['#8a7f75', '#6c635b', '#a59a8f'],
    'Barren world': ['#9a8a78', '#7b6d60', '#b5a693'], 'Frozen desert': ['#d8d2c8', '#b9b0a2', '#efebe4'],
    'Ocean world': ['#1d4f7a', '#2f6d9a', '#16395a'], 'Steppe world': ['#9e9a62', '#7f7f4d', '#b5ad78'],
    'Frozen world': ['#dfe7ee', '#c3cfd9', '#f5f8fa'], 'Irradiated rock': ['#6f6a5c', '#8f8a72', '#4d4a41'],
  }[type] || ['#8f8a84', '#6f6a64', '#aaa49d'];
  const banded = /giant/.test(type);
  return canvasTex('t:' + type + ':' + name, (g, w, h) => {
    const r = seeded(name);
    g.fillStyle = pal[0]; g.fillRect(0, 0, w, h);
    if (banded) {
      for (let y = 0; y < h; y += 2 + r() * 6) { g.fillStyle = pal[Math.floor(r() * pal.length)]; g.globalAlpha = 0.5 + r() * 0.5; g.fillRect(0, y, w, 1 + r() * 7); }
    } else {
      for (let k = 0; k < 260; k++) { g.fillStyle = pal[Math.floor(r() * pal.length)]; g.globalAlpha = 0.25 + r() * 0.4; g.beginPath(); g.arc(r() * w, r() * h, 2 + r() * 14, 0, 7); g.fill(); }
    }
    g.globalAlpha = 1;
  });
}
const glowTex = () => canvasTex('glow', (g, w, h) => {
  const gr = g.createRadialGradient(w / 2, h / 2, 0, w / 2, h / 2, w / 2);
  gr.addColorStop(0, 'rgba(255,255,255,1)'); gr.addColorStop(0.18, 'rgba(255,244,214,.85)'); gr.addColorStop(0.45, 'rgba(255,214,150,.18)'); gr.addColorStop(1, 'rgba(255,200,140,0)');
  g.fillStyle = gr; g.fillRect(0, 0, w, h);
}, 256, 256);
function svInit() {
  if (S3.r) return;
  const wrap = $('#sv-map');
  S3.r = new THREE.WebGLRenderer({ canvas: $('#sv-gl'), antialias: true, alpha: true });
  S3.r.setPixelRatio(Math.min(2, window.devicePixelRatio || 1));
  S3.scene = new THREE.Scene();
  S3.cam = new THREE.PerspectiveCamera(40, 1, 0.005, 400);
  S3.ctl = new OrbitControls(S3.cam, wrap);
  Object.assign(S3.ctl, { enableDamping: true, dampingFactor: 0.08, minDistance: 0.12, maxDistance: 60, rotateSpeed: 0.6, zoomSpeed: 1.1 });
  S3.ctl.addEventListener('start', () => { S3.fly = null; });
  S3.scene.add(new THREE.AmbientLight(0xffffff, 0.05));
  S3.light = new THREE.PointLight(0xfff4e6, 3.2, 0, 0); S3.scene.add(S3.light);
  wrap.addEventListener('pointerdown', (e) => { S3.down = { x: e.clientX, y: e.clientY }; });
  wrap.addEventListener('pointerup', (e) => {
    if (!S3.down || Math.hypot(e.clientX - S3.down.x, e.clientY - S3.down.y) > 6) { S3.down = null; return; }
    S3.down = null;
    const r = wrap.getBoundingClientRect(), x = e.clientX - r.left, y = e.clientY - r.top;
    let best = null, bd = Infinity;
    for (const h of sv.hits) {
      const d = h.box ? (x >= h.box[0] && x <= h.box[2] && y >= h.box[1] && y <= h.box[3] ? -1 : Infinity) : Math.hypot(h.x - x, h.y - y) - h.r;
      if (d <= 0 && d < bd) { bd = d; best = h; }
    }
    sv.pick = best ? best.key : null;
    svFocus(sv.pick);
    renderSystemInfo(); writeHash();
    if (sv.pick) $('#sv-info').scrollTop = 0;
  });
  wrap.addEventListener('pointermove', (e) => {
    const r = wrap.getBoundingClientRect(), x = e.clientX - r.left, y = e.clientY - r.top;
    const over = sv.hits.some((h) => h.box ? x >= h.box[0] && x <= h.box[2] && y >= h.box[1] && y <= h.box[3] : Math.hypot(h.x - x, h.y - y) <= h.r);
    wrap.style.cursor = over ? 'pointer' : '';
  });
}
function disposeTree(o) {
  o.traverse((m) => { if (m.geometry) m.geometry.dispose(); if (m.material) [].concat(m.material).forEach((x) => { if (x.map && !TEXC.has(x.map.name)) {} x.dispose(); }); });
}
function lineCircle(r, op, dashed) {
  const pts = []; for (let i = 0; i <= 160; i++) { const a = i / 160 * Math.PI * 2; pts.push(new THREE.Vector3(Math.cos(a) * r, 0, Math.sin(a) * r)); }
  const g = new THREE.BufferGeometry().setFromPoints(pts);
  const m = dashed ? new THREE.LineDashedMaterial({ color: 0xffffff, transparent: true, opacity: op, dashSize: 0.08, gapSize: 0.22 }) : new THREE.LineBasicMaterial({ color: 0xffffff, transparent: true, opacity: op });
  const l = new THREE.Line(g, m); if (dashed) l.computeLineDistances(); return l;
}
// a body's surface: a generated globe where one exists, a real map for the Sun's planets, otherwise a plain type texture
function svSurface(name, type, rad, t) {
  const pg = planetByName[name];
  if (pg) {
    const { a, b, k } = statesAt(pg, t), base = 'assets/planets/' + pg.slug + '/';
    const g = makeGlobe(THREE, { day: base + a.k + '-day.webp', data: a.noData ? null : base + a.k + '-data.webp', day2: base + b.k + '-day.webp', data2: (a.noData || b.noData) ? null : base + b.k + '-data.webp', atmo: a.atmo, atmo2: b.atmo, k, glow: a.glow, clouds: true });
    g.scale.setScalar(rad); S3.globes.push({ g, pg, name }); return g;
  }
  const lib = GENLIB[type];
  if (lib && lib.length && !SOL_BODIES[name]) {
    const r = seeded(name), key = lib[Math.floor(r() * lib.length)], base = 'assets/planets/_gen/' + key;
    const g = makeGlobe(THREE, { day: base + '-day.webp', data: base + '-data.webp', clouds: false, relief: 3,
      atmo: /Ocean|Steppe/.test(type) ? '#8fb8ff' : /Hot cloud/.test(type) ? '#f0d9a0' : /giant/.test(type) ? '#c8d8f0' : null,
      glow: /Molten/.test(type) ? '#ff7a2a' : '#000000' });
    g.scale.setScalar(rad); S3.globes.push({ g, name }); return g;
  }
  const sk = SOL_BODIES[name] || (sv.sys.id === 'sol' && { Earth: null }[name]);
  const mat = new THREE.MeshStandardMaterial({ roughness: 0.95, metalness: 0 });
  if (sk) { const tx = new THREE.TextureLoader().load('assets/planets/_sol/' + sk + '-day.webp'); tx.colorSpace = THREE.SRGBColorSpace; mat.map = tx; }
  else mat.map = typeTex(type, name);
  const m = new THREE.Mesh(new THREE.SphereGeometry(1, 48, 32), mat); m.scale.setScalar(rad); return m;
}
function ringMesh(p, rad) {
  const inner = rad * 1.35, outer = rad * 2.3, geo = new THREE.RingGeometry(inner, outer, 128, 1);
  const uv = geo.attributes.uv, pos = geo.attributes.position, v = new THREE.Vector3();
  for (let i = 0; i < uv.count; i++) { v.fromBufferAttribute(pos, i); uv.setXY(i, (v.length() - inner) / (outer - inner), 0.5); }
  let tex;
  if (p.name === 'Saturn') { tex = new THREE.TextureLoader().load('assets/planets/_sol/saturn-ring.png'); tex.colorSpace = THREE.SRGBColorSpace; }
  else tex = canvasTex('ring:' + p.name, (g, w, h) => { const r = seeded(p.name); for (let x = 0; x < w; x++) { const a = 0.15 + 0.6 * r(); g.fillStyle = 'rgba(230,214,186,' + a.toFixed(2) + ')'; g.fillRect(x, 0, 1, h); } }, 256, 4);
  const m = new THREE.Mesh(geo, new THREE.MeshBasicMaterial({ map: tex, transparent: true, side: THREE.DoubleSide, depthWrite: false }));
  m.rotation.x = -Math.PI / 2 + 0.35; return m;
}
// build the system: star, orbits, planets, moons, rings; features are rebuilt as the year changes
function svBuild(reset) {
  svInit(); S3.year = year;
  if (S3.root) { S3.scene.remove(S3.root); disposeTree(S3.root); }
  S3.root = new THREE.Group(); S3.scene.add(S3.root); S3.bodies = []; S3.globes = []; S3.feat = null; S3.featYear = null;
  const t = year + 0.999, sys = sv.sys;
  if (sys.blackhole) {
    S3.root.add(new THREE.Mesh(new THREE.SphereGeometry(0.22, 32, 24), new THREE.MeshBasicMaterial({ color: 0x000000 })));
    const disk = new THREE.Mesh(new THREE.RingGeometry(0.3, 1.1, 96), new THREE.MeshBasicMaterial({ map: canvasTex('bh', (g, w, h) => { const gr = g.createLinearGradient(0, 0, w, 0); gr.addColorStop(0, 'rgba(255,240,210,1)'); gr.addColorStop(0.4, 'rgba(242,140,56,.8)'); gr.addColorStop(1, 'rgba(242,140,56,0)'); g.fillStyle = gr; g.fillRect(0, 0, w, h); }, 256, 4), transparent: true, side: THREE.DoubleSide, blending: THREE.AdditiveBlending, depthWrite: false }));
    const uv = disk.geometry.attributes.uv, pos = disk.geometry.attributes.position, v = new THREE.Vector3();
    for (let i = 0; i < uv.count; i++) { v.fromBufferAttribute(pos, i); uv.setXY(i, (v.length() - 0.3) / 0.8, 0.5); }
    disk.rotation.x = -Math.PI / 2 + 0.25; S3.root.add(disk);
    S3.light.intensity = 0.6;
  } else {
    S3.root.add(new THREE.Mesh(new THREE.SphereGeometry(0.2, 32, 24), new THREE.MeshBasicMaterial({ color: 0xfff6e8 })));
    const gl = new THREE.Sprite(new THREE.SpriteMaterial({ map: glowTex(), blending: THREE.AdditiveBlending, depthWrite: false, transparent: true }));
    gl.scale.setScalar(2.4); S3.root.add(gl);
    S3.light.intensity = 3.2;
  }
  const pil = lineCircle(svR(sv.planets[sv.planets.length - 1].a) * PILLAI, 0.35, true); S3.root.add(pil);
  sv.planets.forEach((p, pi) => {
    S3.root.add(lineCircle(svR(p.a), p.world ? 0.5 : 0.2));
    const rad = bodyR(p), grp = new THREE.Group(); S3.root.add(grp);
    const settled = p.world && (p.settled === undefined || p.settled <= t);
    const spin = new THREE.Group(); grp.add(spin);
    spin.add(svSurface(settled ? p.world : p.name, p.type, rad, t));
    if (p.ring) grp.add(ringMesh(p, rad));
    if (p.body && p.body.kind === 'shattered') {
      const pts = [], r = seeded(p.name);
      for (let k = 0; k < 900; k++) { const a = r() * 6.283, d = rad * (1.6 + r() * 1.4); pts.push(Math.cos(a) * d, (r() - 0.5) * rad * 0.25, Math.sin(a) * d); }
      const g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.Float32BufferAttribute(pts, 3));
      const debris = new THREE.Points(g, new THREE.PointsMaterial({ color: 0x9a8f86, size: 0.012, sizeAttenuation: true }));
      debris.rotation.x = 0.3; grp.add(debris);
    }
    const moons = p.moons.map((m, k) => {
      const mr = rad * (0.24 + 0.04 * ((k * 7) % 3)), orbit = rad * (2.1 + k * 0.85);
      const mg = new THREE.Group(); grp.add(mg);
      const ol = lineCircle(orbit, 0.16); ol.rotation.x = 0.12; grp.add(ol);
      const live = m.settled === undefined || m.settled <= t;
      mg.add(svSurface(m.world && live ? m.name : m.name, 'Barren rock', mr, t));
      return { m, k, mg, mr, orbit };
    });
    S3.bodies.push({ p, pi, grp, spin, rad, moons });
  });
  svFeatures(true);
  if (reset) {
    S3.focus = null; S3.fly = null;
    const R = svR(sv.planets[sv.planets.length - 1].a) * PILLAI;
    S3.ctl.target.set(0, 0, 0); S3.cam.position.set(0, R * 0.62, R * 1.25); S3.ctl.update();
  }
}
// stations, yards, starforts, tethers, mirrors, Custos and monoliths for the year shown
function svFeatures(force) {
  const t = year + 0.999;
  if (!force && S3.featYear === year) return;
  S3.featYear = year;
  if (S3.feat) { for (const f of S3.feat) { f.obj.parent && f.obj.parent.remove(f.obj); disposeTree(f.obj); } }
  S3.feat = [];
  const all = (data.features || {})[sv.sys.id] || [];
  all.forEach((f, i) => { f._i = i; });
  const unmet = (() => { let c = null; for (const e of sv.sys.own) { if (e.from <= t) c = e; else break; } return !!(c && c.p && CONTACT[c.p] && t < CONTACT[c.p]); })();
  const list = unmet ? [] : all.filter((f) => t >= f.from && !(f.to && t >= f.to) && !(f.gap && t >= f.gap[0] && t < f.gap[1]) && !(f.gaps || []).some((g) => t >= g[0] && t < g[1]));
  const R = svR(sv.planets[sv.planets.length - 1].a) * PILLAI;
  let pillaiK = 0;
  const bodyAt = (at) => {
    if (Array.isArray(at)) { const b = S3.bodies[at[0] - 1]; const mo = b && b.moons[at[1]]; return mo ? { grp: mo.mg, rad: mo.mr, spin: mo.mg } : null; }
    const b = S3.bodies[at - 1]; return b ? { grp: b.grp, rad: b.rad, spin: b.spin, b } : null;
  };
  const dark = new THREE.MeshStandardMaterial({ color: 0x2a2526, emissive: 0x5a1010, emissiveIntensity: 0.6, roughness: 0.6, metalness: 0.4 });
  const steel = new THREE.MeshStandardMaterial({ color: 0xc9d2dc, roughness: 0.4, metalness: 0.6, emissive: 0x223344, emissiveIntensity: 0.4 });
  const hulkM = new THREE.MeshStandardMaterial({ color: 0x6d655f, roughness: 0.9, metalness: 0.2 });
  const monoM = new THREE.MeshStandardMaterial({ color: 0x0d0c0e, roughness: 0.75, metalness: 0.5, emissive: 0x140405, emissiveIntensity: 1 });
  const lanceM = new THREE.MeshBasicMaterial({ color: 0xc8322a });
  const ringM = new THREE.MeshStandardMaterial({ color: 0x3a3234, roughness: 0.85, metalness: 0.35, emissive: 0x2a0808, emissiveIntensity: 0.5 });
  const hearthM = new THREE.MeshStandardMaterial({ color: 0x5b3f7a, roughness: 0.6, metalness: 0.2, emissive: 0x2a1640, emissiveIntensity: 0.6 });
  const NAVY_MAT = {
    human: new THREE.MeshStandardMaterial({ color: 0xc9d2dc, roughness: 0.4, metalness: 0.6, emissive: 0x334455, emissiveIntensity: 0.6 }),
    conf: new THREE.MeshStandardMaterial({ color: 0xc0704e, roughness: 0.5, metalness: 0.5, emissive: 0x401a0e, emissiveIntensity: 0.7 }),
    thaali: new THREE.MeshStandardMaterial({ color: 0x8fd4a8, roughness: 0.4, metalness: 0.4, emissive: 0x2f7a52, emissiveIntensity: 0.9 }),
    voor: new THREE.MeshStandardMaterial({ color: 0x7a58a6, roughness: 0.6, metalness: 0.2, emissive: 0x2a1640, emissiveIntensity: 0.7 }),
  };
  const hedgeM = new THREE.MeshStandardMaterial({ color: 0x9fe0b8, roughness: 0.4, metalness: 0.5, emissive: 0x2f7a52, emissiveIntensity: 0.9 });
  const hedgeDeadM = new THREE.MeshStandardMaterial({ color: 0x4a4f4c, roughness: 0.9, metalness: 0.3 });
  const WRECK_MAT = {
    mono: new THREE.MeshStandardMaterial({ color: 0x2c2829, roughness: 0.95, metalness: 0.3 }),
    human: new THREE.MeshStandardMaterial({ color: 0x8d959e, roughness: 0.7, metalness: 0.5, emissive: 0x262b31, emissiveIntensity: 1 }),
    conf: new THREE.MeshStandardMaterial({ color: 0x9a6650, roughness: 0.75, metalness: 0.4, emissive: 0x2e1a12, emissiveIntensity: 1 }),
    voor: new THREE.MeshStandardMaterial({ color: 0x6a4a8c, roughness: 0.8, metalness: 0.2, emissive: 0x24163a, emissiveIntensity: 1 }),
    maweer: new THREE.MeshStandardMaterial({ color: 0x4f8a5c, roughness: 0.7, metalness: 0.3, emissive: 0x15301c, emissiveIntensity: 1 }),
    alien: new THREE.MeshStandardMaterial({ color: 0x9a9470, roughness: 0.8, metalness: 0.3, emissive: 0x2a2818, emissiveIntensity: 1 }),
    fev: new THREE.MeshStandardMaterial({ color: 0x5a4a40, roughness: 0.9, metalness: 0.3 }),
  };
  for (const f of list) {
    // freehold settlements ring the system's largest body; everything else at the jump limit stays there
    const big = () => { let bi = 0; S3.bodies.forEach((b, i) => { if (b.rad > S3.bodies[bi].rad) bi = i; }); return bodyAt(bi + 1); };
    const host = f.kind === 'orbital' && f.at === 'pillai' ? big() : f.at === 'pillai' ? null : bodyAt(f.at);
    let obj = new THREE.Group(), anchor = null;
    if (!host && f.clan) {
      // a clan's monoliths, hulks and stations keep one place on the jump limit, its home anchorage
      const cr = seeded('clan:' + f.clan), a = cr() * 6.283, rr = R * (0.8 + cr() * 0.45);
      obj.position.set(Math.cos(a) * rr, (cr() - 0.5) * R * 0.16, Math.sin(a) * rr); S3.root.add(obj); anchor = obj;
    } else if (!host && f.kind === 'wreck') {
      // a battle's wrecks drift where the fleets met at the edge
      const cr = seeded('wreck:' + f.name + f.from), a = cr() * 6.283, rr = R * (0.95 + cr() * 0.25);
      obj.position.set(Math.cos(a) * rr, (cr() - 0.5) * R * 0.08, Math.sin(a) * rr); S3.root.add(obj); anchor = obj;
    } else if (!host) {
      const a = 0.6 + pillaiK++ * 0.55; obj.position.set(Math.cos(a) * R, 0, Math.sin(a) * R); S3.root.add(obj); anchor = obj;
    } else (f.kind === 'tether' ? host.spin : host.grp).add(obj);
    const rad = host ? host.rad : 0.15;
    if (f.kind === 'tether') {
      const dir = latLon(THREE, 0, f.lon || 0, 1), len = rad * 0.75;
      const g = new THREE.BufferGeometry().setFromPoints([dir.clone().multiplyScalar(rad), dir.clone().multiplyScalar(rad + len)]);
      obj.add(new THREE.Line(g, new THREE.LineBasicMaterial({ color: 0xe8eef6, transparent: true, opacity: 0.85 })));
      const cw = new THREE.Mesh(new THREE.BoxGeometry(1, 1, 1), steel); cw.scale.setScalar(rad * 0.05); cw.position.copy(dir.clone().multiplyScalar(rad + len)); obj.add(cw);
      anchor = cw;
    } else if (f.kind === 'mirrors') {
      const m = new THREE.Mesh(new THREE.CircleGeometry(1, 24), new THREE.MeshBasicMaterial({ color: 0xffe9b8, transparent: true, opacity: 0.85, side: THREE.DoubleSide }));
      m.scale.setScalar(rad * 0.09);
      if (f.pole) { m.position.set(0, f.pole * rad * 1.45, 0); m.rotation.x = Math.PI / 2; }
      else m.position.set(0, rad * 0.3, rad * 1.5);
      obj.add(m); anchor = m;
    } else if (f.kind === 'custos') {
      const st = new THREE.Mesh(new THREE.OctahedronGeometry(rad * 0.12), steel); obj.add(st); obj.userData.custos = { st, rad, on: t >= (f.on || f.from) };
      anchor = st;
    } else if (f.kind === 'clanbase') {
      // the clan's hulks and stations, which never leave home
      const r = seeded('base:' + f.clan);
      for (let k = 0; k < (f.n || 4); k++) {
        const m = new THREE.Mesh(new THREE.DodecahedronGeometry(0.5, 0), hulkM);
        m.scale.set(0.022 * (1 + r()), 0.016 * (0.6 + r()), 0.02 * (0.6 + r()));
        const a = r() * 6.283, d = 0.05 + r() * 0.07; m.position.set(Math.cos(a) * d, (r() - 0.5) * 0.04, Math.sin(a) * d); m.rotation.set(r(), r() * 6, r());
        obj.add(m);
      }
      const st = new THREE.Mesh(new THREE.TorusGeometry(0.03, 0.007, 4, 10), ringM); st.position.set(0, 0.03, 0); st.rotation.x = 1.2; obj.add(st);
      anchor = obj;
    } else if (f.kind === 'clanfleet' || f.kind === 'clanhulk') {
      const r = seeded('mon:' + f.clan + f.from), dead = f.kind === 'clanhulk';
      for (let k = 0; k < Math.min(f.n || 1, 6); k++) {
        const grp = new THREE.Group();
        grp.add(new THREE.Mesh(new THREE.BoxGeometry(0.42, 1.6, 0.14), dead ? hulkM : monoM));
        if (!dead) { const seam = new THREE.Mesh(new THREE.BoxGeometry(0.05, 1.3, 0.15), lanceM); seam.position.x = 0.12; grp.add(seam); }
        for (let h = 0; h < 3; h++) {
          const hk = new THREE.Mesh(new THREE.DodecahedronGeometry(0.15 + r() * 0.1, 0), hulkM);
          const ha = r() * 6.283; hk.position.set(Math.cos(ha) * 0.5, (r() - 0.5) * 1.2, Math.sin(ha) * 0.5); grp.add(hk);
        }
        grp.scale.setScalar(0.07);
        grp.position.set((k - (Math.min(f.n, 6) - 1) / 2) * 0.05, 0, (r() - 0.5) * 0.04); grp.rotation.set((r() - 0.5) * 0.3, r() * 6, dead ? 0.6 : 0);
        obj.add(grp);
      }
      anchor = obj;
    } else if (f.kind === 'fleet') {
      // monoliths: tall black slabs, scarred, with a faint lance glow, each with its clan's hulks moored round it
      const n = Math.min(f.n || 4, 40), r = seeded(f.name + f.from), base = host ? rad * 2.6 : 0.35;
      const sz = host ? rad * 0.09 : 0.1;
      for (let k = 0; k < n; k++) {
        const grp = new THREE.Group();
        const slab = new THREE.Mesh(new THREE.BoxGeometry(0.42, 1.6, 0.14), monoM); grp.add(slab);
        const seam = new THREE.Mesh(new THREE.BoxGeometry(0.05, 1.3, 0.15), lanceM); seam.position.x = 0.12; grp.add(seam);
        for (let h = 0, nh = 2 + Math.floor(r() * 4); h < nh; h++) {
          const hk = new THREE.Mesh(new THREE.DodecahedronGeometry(0.16 + r() * 0.12, 0), hulkM);
          const ha = r() * 6.283; hk.position.set(Math.cos(ha) * (0.45 + r() * 0.35), (r() - 0.5) * 1.3, Math.sin(ha) * (0.45 + r() * 0.35));
          hk.scale.set(1 + r(), 0.6 + r() * 0.6, 0.8 + r()); hk.rotation.set(r() * 3, r() * 3, r() * 3); grp.add(hk);
        }
        grp.scale.setScalar(sz);
        const a = r() * 6.283, d = base * (0.7 + r() * 0.6);
        grp.position.set(Math.cos(a) * d, (r() - 0.5) * 0.12, Math.sin(a) * d); grp.rotation.set((r() - 0.5) * 0.4, r() * 6, (r() - 0.5) * 0.4);
        obj.add(grp);
      }
      // the Voor hearths the Khan took: long tapering grown hulls among the slabs
      for (let k = 0; k < (f.hearths || 0); k++) {
        const hm = new THREE.Mesh(new THREE.CylinderGeometry(0.06, 0.16, 1.9, 8), hearthM); hm.rotation.z = Math.PI / 2;
        const grp = new THREE.Group(); grp.add(hm); grp.scale.setScalar(sz * 1.3);
        const a = r() * 6.283, d = base * (0.6 + r() * 0.5); grp.position.set(Math.cos(a) * d, (r() - 0.5) * 0.08, Math.sin(a) * d); grp.rotation.y = r() * 6;
        obj.add(grp);
      }
      anchor = obj;
    } else if (f.kind === 'wreck') {
      // a battle's wreckage: each side's dead hulls in its own build, broken and cold, in one drifting field.
      // By a world the field sits off to one side in the world's orbit, so the camera can centre on it.
      const r = seeded('w' + f.name + f.from), span = host ? rad * 0.9 : 0.16;
      if (host) { const a = r() * 6.283, d = rad * 2.6; obj.position.set(Math.cos(a) * d, (r() - 0.5) * rad * 0.4, Math.sin(a) * d); }
      for (const side of f.sides || []) {
        const n = Math.min(side.n || 1, side.style === 'mono' ? 40 : 30), mat = WRECK_MAT[side.style] || WRECK_MAT.human;
        const sz = (host ? rad * 0.07 : 0.07) * (side.style === 'mono' ? 1 : side.style === 'voor' ? 0.9 : 0.55);
        for (let k = 0; k < n; k++) {
          const grp = new THREE.Group();
          if (side.style === 'mono') {
            for (const sgn of [-1, 1]) {
              const half = new THREE.Mesh(new THREE.BoxGeometry(0.42, 0.72 + r() * 0.2, 0.14), mat);
              half.position.set(sgn * (0.05 + r() * 0.12), sgn * (0.42 + r() * 0.2), (r() - 0.5) * 0.2);
              half.rotation.set((r() - 0.5) * 0.8, (r() - 0.5) * 0.8, sgn * (0.2 + r() * 0.5)); grp.add(half);
            }
          } else if (side.style === 'voor') {
            const hm = new THREE.Mesh(new THREE.CylinderGeometry(0.05, 0.13, 0.8 + r() * 0.5, 7), mat); hm.rotation.z = Math.PI / 2 + (r() - 0.5); grp.add(hm);
            const tail = new THREE.Mesh(new THREE.CylinderGeometry(0.03, 0.06, 0.5, 6), mat); tail.position.set(0.6 + r() * 0.3, (r() - 0.5) * 0.3, 0); tail.rotation.z = r() * 3; grp.add(tail);
          } else {
            const len = 0.5 + r() * 0.6;
            for (const sgn of [-1, 1]) {
              const part = new THREE.Mesh(new THREE.BoxGeometry(len * 0.5, 0.12, 0.16), mat);
              part.position.set(sgn * (len * 0.28 + r() * 0.1), (r() - 0.5) * 0.12, (r() - 0.5) * 0.12); part.rotation.set(r(), r(), (r() - 0.5) * 0.9); grp.add(part);
            }
          }
          for (let h = 0; h < 3; h++) {
            const d = new THREE.Mesh(new THREE.TetrahedronGeometry(0.04 + r() * 0.05, 0), mat);
            d.position.set((r() - 0.5) * 0.9, (r() - 0.5) * 0.9, (r() - 0.5) * 0.9); d.rotation.set(r() * 3, r() * 3, r() * 3); grp.add(d);
          }
          grp.scale.setScalar(sz);
          const a = r() * 6.283, d = span * Math.sqrt(r());
          grp.position.set(Math.cos(a) * d, (r() - 0.5) * span * 0.35, Math.sin(a) * d); grp.rotation.set(r() * 6, r() * 6, r() * 6);
          obj.add(grp);
        }
      }
      obj.userData.span = span;
      anchor = obj;
    } else if (f.kind === 'navy') {
      // a human fleet: wedge-hulled ships in loose formation, off to one side of the world it holds
      const r = seeded('n' + f.name + f.from), span = host ? rad * 0.8 : 0.14;
      if (host) { const a = r() * 6.283, d = rad * 2.2; obj.position.set(Math.cos(a) * d, (r() - 0.5) * rad * 0.3, Math.sin(a) * d); }
      else {
        // a fleet at the jump limit holds a place on its edge; the Thaali and the Voor face each other across the crossing
        const cr = seeded('navy:' + f.side), a = cr() * 6.283, rr = R * (0.9 + cr() * 0.2);
        obj.position.set(Math.cos(a) * rr, (cr() - 0.5) * R * 0.1, Math.sin(a) * rr);
      }
      const mat = NAVY_MAT[f.style] || NAVY_MAT.human, sz = host ? rad * 0.05 : 0.05;
      const nbig = f.style === 'thaali' ? Math.max(1, (f.n || 6) - 6) : Math.max(2, (f.n || 6) / 6);
      for (let k = 0; k < Math.min(f.n || 6, 40); k++) {
        const big = k < nbig;
        const grp = new THREE.Group();
        if (f.style === 'thaali') {
          // a Thaali hull: a chain of segments on its keel; the great ships long, on two keels
          const segs = big ? 9 : 4, keels = big ? 2 : 1;
          for (let q = 0; q < keels; q++) for (let j = 0; j < segs; j++) {
            const sgm = new THREE.Mesh(new THREE.BoxGeometry(0.11, 0.07, 0.08), mat);
            sgm.position.set((j - segs / 2) * 0.13, 0, (q - (keels - 1) / 2) * 0.1); grp.add(sgm);
          }
        } else if (f.style === 'voor') {
          // a hearth: a long tapering grown hull
          const hm = new THREE.Mesh(new THREE.CylinderGeometry(0.06, 0.16, 1.9, 8), mat); hm.rotation.z = Math.PI / 2; grp.add(hm);
        } else {
          const hull = new THREE.Mesh(new THREE.ConeGeometry(0.16, big ? 1.1 : 0.6, 4), mat); hull.rotation.z = -Math.PI / 2; grp.add(hull);
        }
        grp.scale.setScalar(sz * (big ? 1.4 : 1));
        const a = r() * 6.283, d = span * Math.sqrt(r());
        grp.position.set(Math.cos(a) * d, (r() - 0.5) * span * 0.25, Math.sin(a) * d); grp.rotation.y = 0.4 + (r() - 0.5) * 0.3;
        obj.add(grp);
      }
      obj.userData.span = span;
      anchor = obj;
    } else if (f.kind === 'hulk') {
      const n = Math.min(f.n || 4, 48), r = seeded(f.name + f.from);
      for (let k = 0; k < n; k++) {
        const m = new THREE.Mesh(new THREE.DodecahedronGeometry(0.5, 0), hulkM);
        m.scale.set(0.03 * (0.6 + r()) * (1 + r()), 0.03 * (0.6 + r()), 0.03 * (0.6 + r()));
        const a = r() * 6.283, d = (host ? rad * 2.6 : 0.35) * (0.7 + r() * 0.6);
        m.position.set(Math.cos(a) * d, (r() - 0.5) * 0.12, Math.sin(a) * d); m.rotation.set(r(), r() * 6, r());
        obj.add(m);
      }
      anchor = obj;
    } else if (f.kind === 'hedge') {
      // a Thaali march hedge: generator stations in three orbits round the world, whole or stripped
      const r = seeded(f.name + f.at + f.from);
      for (let j = 0; j < 3; j++) {
        const R0 = host ? rad * (1.3 + j * 0.22) : 0.14 + j * 0.05, n = 26 + j * 8, tilt = (j - 1) * 0.45;
        const ring = new THREE.Group();
        for (let k = 0; k < n; k++) {
          if (f.broken && r() < 0.7) continue;
          const st = new THREE.Mesh(new THREE.OctahedronGeometry(R0 * 0.02, 0), f.broken ? hedgeDeadM : hedgeM);
          const a0 = k / n * 6.283; st.position.set(Math.cos(a0) * R0, 0, Math.sin(a0) * R0); ring.add(st);
        }
        ring.rotation.x = tilt; ring.rotation.z = j * 0.6; obj.add(ring);
      }
      obj.userData.span = host ? rad * 6 : 0.5;
      anchor = obj;
    } else if (f.kind === 'orbital') {
      // Fevarian orbital settlements: a broken dark ring of hulls lashed together, hulks moored along it, faint red lights
      const r = seeded(f.name + f.from), nring = f.n || 1;
      for (let j = 0; j < nring; j++) {
        const R0 = host ? rad * (1.35 + j * 0.32) : 0.14 + j * 0.08;
        const segs = 18 + Math.floor(r() * 10);
        const ring = new THREE.Group();
        for (let k = 0; k < segs; k++) {
          if (r() < 0.18) continue;
          const a0 = k / segs * 6.283, w = 6.283 / segs * (0.55 + r() * 0.35);
          const seg = new THREE.Mesh(new THREE.TorusGeometry(R0, R0 * 0.016, 4, 6, w), ringM); seg.rotation.z = a0; ring.add(seg);
          if (r() < 0.45) {
            const hk = new THREE.Mesh(new THREE.DodecahedronGeometry(R0 * 0.026, 0), hulkM);
            hk.position.set(Math.cos(a0) * R0 * (1 + (r() - 0.5) * 0.1), Math.sin(a0) * R0 * (1 + (r() - 0.5) * 0.1), (r() - 0.5) * R0 * 0.05); ring.add(hk);
          }
          if (r() < 0.3) { const l = new THREE.Mesh(new THREE.SphereGeometry(R0 * 0.012, 4, 3), lanceM); l.position.set(Math.cos(a0) * R0, Math.sin(a0) * R0, 0); ring.add(l); }
        }
        ring.rotation.x = Math.PI / 2 + (r() - 0.5) * 0.3 + (j ? (j % 2 ? 0.35 : -0.35) : 0); ring.rotation.y = j * 0.9;
        obj.add(ring);
      }
      if (!host) obj.position.y += 0;
      anchor = obj;
    } else {
      const geo = f.kind === 'starfort' ? new THREE.OctahedronGeometry(1) : f.kind === 'yard' ? new THREE.BoxGeometry(1.6, 0.4, 0.8) : new THREE.TorusGeometry(1, 0.28, 8, 24);
      const m = new THREE.Mesh(geo, steel); m.scale.setScalar(host ? rad * 0.12 : 0.05);
      if (host) m.position.set(rad * 1.6, rad * 0.2, 0);
      obj.add(m); anchor = m;
    }
    S3.feat.push({ f, obj, anchor: anchor || obj, host });
  }
  // a feature picked from a link or the hash before its scene existed: fly to it now
  if (String(S3.focus || '').startsWith('f:') && S3.flownF !== S3.focus && bodyKeyRad(S3.focus)) { S3.flownF = S3.focus; svFocus(S3.focus); }
}
// fly the camera to a body (or back to the whole system)
function svFocus(key, instant) {
  if (!S3.ctl) return;
  S3.focus = key;
  const R = svR(sv.planets[sv.planets.length - 1].a) * PILLAI;
  const b = key ? bodyKeyRad(key) : null;
  const toDist = b ? Math.max(0.25, b.rad * 9) : R * 1.4;
  S3.fly = { t0: performance.now(), d: instant ? 1 : 1100, from: S3.cam.position.distanceTo(S3.ctl.target), to: toDist, fromT: S3.ctl.target.clone() };
}
function bodyKeyRad(key) {
  if (String(key).startsWith('f:')) {
    const e = (S3.feat || []).find((x) => 'f:' + x.f._i === key);
    return e ? { obj: e.anchor, rad: Math.max(0.03, (e.anchor.userData.span || 0.1) / 3) } : null;
  }
  const [pi, mi] = String(key).split('.').map(Number), b = S3.bodies[pi];
  if (!b) return null;
  if (mi === undefined || Number.isNaN(mi)) return { obj: b.grp, rad: b.rad };
  const m = b.moons[mi]; return m ? { obj: m.mg, rad: m.mr } : null;
}
const V3 = new THREE.Vector3(), V4 = new THREE.Vector3();
function drawSystem(dt) {
  if (!sv.sys || !S3.r) return;
  const wrap = $('#sv-map'), w = wrap.clientWidth, h = wrap.clientHeight; if (!w) return;
  if (S3.r.domElement.width !== Math.round(w * S3.r.getPixelRatio())) { S3.r.setSize(w, h, false); S3.cam.aspect = w / h; S3.cam.updateProjectionMatrix(); }
  if (S3.year !== year) { S3.year = year; svBuild(false); }
  svFeatures(false);
  sv.t += dt / 1000 * sv.speed;
  const t = year + 0.999;
  for (const b of S3.bodies) {
    const R = svR(b.p.a), ang = b.p.ph + sv.t * 0.6 / Math.pow(b.p.a, 1.5);
    b.grp.position.set(Math.cos(ang) * R, 0, Math.sin(ang) * R);
    b.spin.rotation.y += dt / 1000 * 0.15;
    for (const mo of b.moons) {
      const a2 = mo.m.ph + sv.t * 2.2 / (1 + mo.k * 0.6);
      mo.mg.position.set(Math.cos(a2) * mo.orbit, Math.sin(a2) * mo.orbit * 0.12, Math.sin(a2) * mo.orbit);
    }
  }
  S3.root.updateMatrixWorld(true);
  for (const g of S3.globes) {
    g.g.getWorldPosition(V3);
    if (g.g.userData.sun) g.g.userData.sun.copy(V3).negate().normalize();
  }
  for (const f of S3.feat || []) {
    if (f.f.kind === 'custos' && f.host) {
      f.host.grp.getWorldPosition(V3); const dir = V3.clone().negate().normalize();
      f.obj.position.copy(dir.clone().multiplyScalar(f.host.rad * 4.2));
    }
  }
  // follow the focused body, and ease the camera's distance when flying
  if (S3.focus) { const b = bodyKeyRad(S3.focus); if (b) { b.obj.getWorldPosition(V3); V4.copy(V3).sub(S3.ctl.target); S3.ctl.target.add(V4); S3.cam.position.add(V4); } }
  if (S3.fly) {
    const k = Math.min(1, (performance.now() - S3.fly.t0) / S3.fly.d), e = k < 0.5 ? 2 * k * k : 1 - Math.pow(-2 * k + 2, 2) / 2;
    if (!S3.focus) S3.ctl.target.lerpVectors(S3.fly.fromT, V4.set(0, 0, 0), e);
    const dir = V3.copy(S3.cam.position).sub(S3.ctl.target).normalize();
    S3.cam.position.copy(S3.ctl.target).addScaledVector(dir, S3.fly.from + (S3.fly.to - S3.fly.from) * e);
    if (k >= 1) S3.fly = null;
  }
  S3.ctl.update();
  S3.r.render(S3.scene, S3.cam);
  // labels, poster style, in the SVG over the canvas
  const svg = $('#sv-svg'), hits = [], burnedList = burnedAt(sv.sys.id, t), names = !wrap.classList.contains('nonames');
  const proj = (o) => { o.getWorldPosition(V3); const d = V3.distanceTo(S3.cam.position); V3.project(S3.cam); return { x: (V3.x + 1) / 2 * w, y: (1 - V3.y) / 2 * h, ok: V3.z < 1, d }; };
  const pxR = (rad, d) => rad / (d * Math.tan(S3.cam.fov * Math.PI / 360)) * h / 2;
  let out = '';
  const queue = [];
  const R0 = svR(sv.planets[sv.planets.length - 1].a) * PILLAI;
  { V3.set(0, 0, -R0); const d = V3.distanceTo(S3.cam.position); V3.project(S3.cam); if (V3.z < 1 && names && d < 60) out += '<text class="lbl sb" x="' + ((V3.x + 1) / 2 * w) + '" y="' + ((1 - V3.y) / 2 * h - 8) + '" text-anchor="middle" font-size="10" letter-spacing="2" fill="#C9D6E5">PILLAI RADIUS · JUMP LIMIT</text>'; }
  { V3.set(0, 0, 0); V3.project(S3.cam); if (V3.z < 1 && names) out += '<text class="lbl nm" x="' + ((V3.x + 1) / 2 * w + 14) + '" y="' + ((1 - V3.y) / 2 * h - 16) + '" font-size="15">' + esc(sv.sys.name) + '</text>'; }
  const order = S3.bodies.map((b) => ({ b, s: proj(b.grp) })).sort((a, c) => c.s.d - a.s.d);
  for (const { b, s } of order) {
    if (!s.ok) continue;
    const p = b.p, pi = b.pi, pr = Math.max(3, pxR(b.rad, s.d));
    const settled = p.world && (p.settled === undefined || p.settled <= t);
    const burnP = settled && burnedList.find((x) => x.name === p.world);
    hits.push({ key: String(pi), x: s.x, y: s.y, r: Math.max(14, pr + 6) });
    if (sv.pick === String(pi)) out += '<circle cx="' + s.x + '" cy="' + s.y + '" r="' + (pr + 9) + '" fill="none" stroke="#F2C14E" stroke-width="1.5" stroke-dasharray="3 3"/>';
    if (settled) out += '<circle cx="' + s.x + '" cy="' + s.y + '" r="' + (pr + 4) + '" fill="none" stroke="#fff" stroke-opacity=".7"/>';
    const near = s.d < b.rad * 40;
    b.moons.forEach((mo, k) => {
      const ms = proj(mo.mg); if (!ms.ok) return;
      const mr = Math.max(2.5, pxR(mo.mr, ms.d));
      hits.push({ key: pi + '.' + k, x: ms.x, y: ms.y, r: Math.max(8, mr + 4) });
      if (sv.pick === pi + '.' + k) out += '<circle cx="' + ms.x + '" cy="' + ms.y + '" r="' + (mr + 6) + '" fill="none" stroke="#F2C14E" stroke-width="1.5" stroke-dasharray="3 3"/>';
      const live = mo.m.world && (mo.m.settled === undefined || mo.m.settled <= t);
      if (names && (near || live) && (near || sv.pick === String(pi) || live)) {
        const burnM = live && burnedList.find((x) => x.name === mo.m.name);
        if (near || live) {
          const mf = live ? flagsAt(mo.m.name, t) : [];
          let html = '<g class="lbl"><text x="' + (ms.x + mr + 5) + '" y="' + (ms.y + 4) + '"><tspan class="nm" data-b="' + pi + '.' + k + '" style="cursor:pointer" font-size="11">' + esc(mo.m.name) + '</tspan>' + (burnM ? '<tspan class="sb" font-size="10"> · burned ' + Math.floor(burnM.y) + '</tspan>' : '') + '</text>';
          if (mf.length) html += flagRow(mf, ms.x + mr + 10 + mo.m.name.length * 7.6, ms.y - 5, 9);
          html += '</g>';
          const box = [ms.x + mr + 4, ms.y - 8, ms.x + mr + 8 + mo.m.name.length * 7.6 + mf.length * 16, ms.y + 6];
          queue.push({ pri: (sv.pick === pi + '.' + k ? 9 : 0) + (live ? 2 : 1), box, html, hit: { key: pi + '.' + k, box } });
        }
      }
    });
    if (!names) continue;
    const label = settled ? p.world : p.name;
    const bio = settled && biomeAt(worldByName(sv.sys.id, p.world), t);
    const sub = burnP ? 'Burned ' + Math.floor(burnP.y) : bio || p.type;
    const pf = settled ? flagsAt(p.world, t) : [];
    const subW = (ROMAN[pi] + ' · ' + sub).length * 6;
    const mk = (ly, below) => {
      const y0 = below ? s.y + pr + 2 : s.y - pr - 2, y1 = below ? ly - 15 : ly - 8;
      const box = [s.x + 4, ly - 16, s.x + 8 + Math.max(label.length * (settled ? 11 : 9) + pf.length * 20, subW), ly + 18];
      let html = '<g class="lbl"><line x1="' + s.x + '" y1="' + y0 + '" x2="' + s.x + '" y2="' + y1 + '" stroke="#fff" stroke-width="1"/>' +
        '<text class="nm" data-b="' + pi + '" style="cursor:pointer" x="' + (s.x + 6) + '" y="' + ly + '" font-size="' + (settled ? 17 : 13) + '">' + esc(label) + '</text>' +
        '<text class="sb" x="' + (s.x + 6) + '" y="' + (ly + 14) + '">' + esc(ROMAN[pi] + ' · ' + sub) + '</text></g>';
      if (pf.length) html += '<g class="lbl">' + flagRow(pf, s.x + 12 + label.length * 9.6, ly - 13 - (pf.length > 6 ? 15 : 0), 12) + '</g>';
      return { box, html, hit: { key: String(pi), box: [s.x + 4, ly - 16, s.x + 8 + label.length * (settled ? 11 : 9), ly + 2] } };
    };
    const up = s.y - pr - 22;
    queue.push({ pri: (sv.pick === String(pi) ? 9 : 0) + (settled ? 5 : 3), alts: [mk(up, false), mk(up - 34, false), mk(s.y + pr + 30, true), mk(up - 68, false)] });
  }
  // feature labels: always for the Pillai radius's starforts and fleets, near bodies when zoomed in
  if (names) for (const f of S3.feat || []) {
    const s = proj(f.anchor); if (!s.ok) continue;
    const close = !f.host || s.d < (f.host.rad || 0.2) * 30;
    if (!close) continue;
    const n = (f.f.n && (f.f.kind === 'fleet' || f.f.kind === 'hulk') ? ' · ' + f.f.n + (f.f.kind === 'fleet' ? ' monoliths' : ' hulks') : '') + (f.f.hearths ? ' · ' + f.f.hearths + ' captured hearths' : '');
    const fkey = 'f:' + f.f._i, pickable = PICKABLE.has(f.f.kind);
    if (pickable) hits.push({ key: fkey, x: s.x, y: s.y, r: 11 });
    if (f.f.kind === 'clanbase') continue;
    let txt = f.f.name + n;
    if (f.f.kind === 'wreck') txt = (f.f.title || f.f.name) + ' · ' + Math.floor(f.f.from);
    if (f.f.kind === 'clanfleet') txt = f.f.name + (f.f.n > 1 ? ' · ' + f.f.n + ' monoliths' : '');
    if (f.f.kind === 'clanhulk') txt = f.f.name + (f.f.n > 1 ? ' · ' + f.f.n + ' hulks' : ' hulk');
    let pre = '', dx = 0;
    if (f.f.clan) { pre = '<image href="assets/flags/clans/' + f.f.clan + '.png" x="' + (s.x + 6) + '" y="' + (s.y - 6) + '" width="12" height="12"/>'; dx = 15; }
    let post = '', tw = txt.length * 5.8;
    if (f.f.clans && f.f.clans.length && f.f.kind !== 'wreck') {
      const show = f.f.clans.slice(0, f.f.kind === 'wreck' ? 4 : 10);
      show.forEach((c, k) => { post += '<image href="assets/flags/clans/' + c + '.png" x="' + (s.x + 12 + tw + k * 12) + '" y="' + (s.y - 5) + '" width="11" height="11"/>'; });
      if (f.f.clans.length > show.length) post += '<text class="sb ft" x="' + (s.x + 14 + tw + show.length * 12) + '" y="' + (s.y + 4) + '" font-size="9.5">+' + (f.f.clans.length - show.length) + '</text>';
      tw += show.length * 12 + 18;
    }
    const box = [s.x + 6, s.y - 7, s.x + 8 + dx + tw, s.y + 6];
    queue.push({ pri: (sv.pick === fkey ? 9 : 0) + (f.f.kind === 'wreck' ? 0.3 : f.f.clan ? 0.35 : 0.5), box, hit: pickable ? { key: fkey, box } : null,
      html: '<g class="lbl"' + (pickable ? ' style="cursor:pointer"' : '') + '>' + pre + '<text class="sb ft ft-' + f.f.kind + (sv.pick === fkey ? ' on' : '') + '" x="' + (s.x + 7 + dx) + '" y="' + (s.y + 4) + '" font-size="10.5">' + esc(txt) + '</text>' + post + '</g>' });
  }
  // place labels by priority; a label that would overlap one already placed is left out
  const placed = [];
  queue.sort((a, b) => b.pri - a.pri);
  for (const q of queue) {
    const c = (q.alts || [q]).find((a) => !placed.some((b) => a.box[0] < b[2] && a.box[2] > b[0] && a.box[1] < b[3] && a.box[3] > b[1]));
    if (!c) continue;
    placed.push(c.box); out += c.html; if (c.hit) hits.push(c.hit);
  }
  svg.innerHTML = out;
  sv.hits = hits.reverse();
}

// ------------------------------------------------------------------ hash state
let hashT = null;
function writeHash() {
  clearTimeout(hashT);
  hashT = setTimeout(() => {
    const q = new URLSearchParams();
    q.set('year', year);
    if (selected) q.set('sys', selected.id);
    if (sv.sys && !$('#sysview').hidden) { q.set('view', 'system'); if (sv.pick) q.set('body', sv.pick); }
    window.history.replaceState(null, '', '#' + q.toString());
  }, 250);
}

// ------------------------------------------------------------------ loop
function resize() {
  const w = canvas.clientWidth, h = canvas.clientHeight;
  renderer.setSize(w, h, false); camera.aspect = w / h; camera.updateProjectionMatrix();
  starMat.uniforms.uScale.value = Math.min(2, window.devicePixelRatio || 1); if (window.__bhMat) window.__bhMat.uniforms.uScale.value = starMat.uniforms.uScale.value;
  drawTimeline();
}
window.addEventListener('resize', resize);
// keep the zoom buttons and panels clear of the footer as its legend wraps
new ResizeObserver(() => { document.getElementById('atlas').style.setProperty('--foot', $('#foot').offsetHeight + 'px'); }).observe($('#foot'));
let last = performance.now();
function frame(now) {
  const dt = Math.min(100, now - last); last = now;
  if (anim) {
    const k = Math.min(1, (now - anim.t0) / anim.d), e = k < 0.5 ? 2 * k * k : 1 - Math.pow(-2 * k + 2, 2) / 2;
    controls.target.lerpVectors(anim.fromT, anim.toT, e); camera.position.lerpVectors(anim.fromP, anim.toP, e);
    if (k >= 1) anim = null;
  }
  controls.update();
  renderer.render(scene, camera);
  project();
  // labels
  const camDist = camera.position.distanceTo(controls.target);
  const minRank = camDist > 260 ? 2 : camDist > 110 ? 1 : 0;
  const w = canvas.clientWidth, h = canvas.clientHeight;
  const placed = [];
  for (const i of labelOrder()) {
    const p = proj[i], l = labels[i];
    const pri = i === hover || (selected && SYS[i] === selected);
    let show = layers.nam && p.vis && p.x > -50 && p.x < w + 50 && p.y > 40 && p.y < h && (+l.dataset.rank >= minRank || pri);
    if (show) {
      const bw = l._w || (l._w = l.offsetWidth || SYS[i].name.length * 8), box = [p.x + 8, p.y - 8, p.x + 12 + bw, p.y + 8];
      if (!pri && placed.some((b) => box[0] < b[2] && box[2] > b[0] && box[1] < b[3] && box[3] > b[1])) show = false;
      else placed.push(box);
    }
    if (show) { l.style.display = ''; l.style.transform = 'translate(' + (p.x + 9).toFixed(1) + 'px,' + (p.y - 7).toFixed(1) + 'px)'; }
    else l.style.display = 'none';
  }
  for (const m of markers) {
    const i = SYS.indexOf(m.s), p = proj[i];
    if (!p.vis) { m.el.style.display = 'none'; continue; }
    m.el.style.display = ''; m.el.style.transform = 'translate(' + (p.x - 5).toFixed(1) + 'px,' + (p.y - 30).toFixed(1) + 'px)';
  }
  if (selected) { const p = proj[SYS.indexOf(selected)]; ring.hidden = !p.vis; ring.style.transform = 'translate(' + p.x.toFixed(1) + 'px,' + p.y.toFixed(1) + 'px)'; }
  stepGlide(dt);
  if (!$('#sysview').hidden) drawSystem(dt);
  requestAnimationFrame(frame);
}

function labelOrder() {
  const ix = [...Array(N).keys()];
  return ix.sort((a, b) => {
    const pa = (a === hover || (selected && SYS[a] === selected)) ? 9 : +labels[a].dataset.rank;
    const pb = (b === hover || (selected && SYS[b] === selected)) ? 9 : +labels[b].dataset.rank;
    return pb - pa;
  });
}

// ------------------------------------------------------------------ start
await document.fonts.ready.catch(() => {});
resize();
applyYear();
drawTimeline();
if (fromHash.get('sys') && byId[fromHash.get('sys')]) {
  select(fromHash.get('sys'), true);
  if (fromHash.get('view') === 'system') {
    openSystem(fromHash.get('sys'));
    if (fromHash.get('body')) { sv.pick = fromHash.get('body'); svFocus(sv.pick, true); renderSystemInfo(); }
  }
}
requestAnimationFrame(frame);
