import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';

const $ = (s) => document.querySelector(s);
const esc = (s) => String(s).replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
const MONTHS = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'];
const ROMAN = ['I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX', 'X', 'XI', 'XII'];
const ERAS = [
  [1945, 2220, 'The Early Solar Era'], [2220, 2255, 'The Solar War'], [2255, 2289, 'Unification'],
  [2289, 2318, 'The Expansion Era'], [2318, 2333, 'The Ring of Iron'], [2333, 2341, 'The Voor War'],
  [2341, 2405, 'The First Republic'], [2405, 2441, 'The Fevarian Crisis'], [2441, 2449, 'The Darkest Decade'],
  [2449, 2460, 'The Scouring'], [2460, 2510, 'Reconstruction'], [2510, 2600, 'The Apportionment Crisis'],
];

const [data, articles] = await Promise.all([
  fetch('assets/atlas-data.json').then((r) => r.json()),
  fetch('assets/articles.json').then((r) => r.json()).catch(() => ({})),
]);
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
  if (!cur) return null;
  const p = cur.p === 'human' ? humanName(t) : cur.p;
  if (CONTACT[p] && t < CONTACT[p]) return null;   // not yet known to humanity
  return { p, note: cur.note, derived: !!cur.derived, from: cur.from };
}
// a world shows its found biome until its terraforming is complete
const biomeAt = (w, t) => (w && w.becomes && w.terraformed && t >= w.terraformed ? w.becomes : w && w.biome);
const worldByName = (sid, name) => data.worlds.find((w) => w.sys === sid && w.name === name);
const worldsAt = (sid, t) => data.worlds.filter((w) => w.sys === sid && w.settled <= t);
const burnedAt = (sid, t) => data.burned.filter((b) => b.sys === sid && b.y <= t && t < b.y + 30);
const eraOf = (y) => (ERAS.find((e) => y >= e[0] && y < e[1]) || ERAS[ERAS.length - 1])[2];
const captionOf = (y) => (data.captions.find((c) => y >= c.from && y < c.to) || data.captions[data.captions.length - 1]).text;
const fmtDate = (y) => {
  const yr = Math.floor(y), f = y - yr, m = Math.min(11, Math.floor(f * 12 + 1e-6));
  return f < 0.001 ? String(yr) : MONTHS[m] + ' ' + yr;
};
const polName = (p) => (P[p] ? P[p].name : p);
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
const EXT = { x0: -160, x1: 45, y0: -115, y1: 90 };   // 205 x 205 ly on a 2048 texture
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
const TPX = 2048 / 205;
const terrCanvas = document.createElement('canvas');
terrCanvas.width = 2048;
terrCanvas.height = 2048;
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
    // polity names at the centre of their holdings
    g.textAlign = 'center'; g.textBaseline = 'middle';
    for (const p of Object.keys(groups)) {
      const list = groups[p]; if (list.length < 3) continue;
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
    for (const r of data.regions) g.fillText(r.name.toUpperCase(), cx(r.x), cy(r.y));
    // sectors: the Republic's administrative divisions. Each sector's boundary is a contour of
    // a distance field that stops short of the bisector with its neighbours, so sectors never overlap.
    for (const sh of sectorShapes(t)) {
      g.save(); g.setLineDash([14, 12]); g.lineWidth = 3; g.strokeStyle = 'rgba(242,213,154,0.45)'; g.lineJoin = 'round';
      for (const line of sh.lines) { g.beginPath(); line.forEach(([x, y], i) => (i ? g.lineTo(cx(x), cy(y)) : g.moveTo(cx(x), cy(y)))); g.stroke(); }
      g.restore();
      g.font = "500 26px 'Jost', sans-serif"; g.fillStyle = 'rgba(242,213,154,0.7)';
      if ('letterSpacing' in g) g.letterSpacing = '6px';
      g.fillText(sh.name.toUpperCase(), cx(sh.lx), cy(sh.ly));
    }
  }
  if ('letterSpacing' in g) g.letterSpacing = '0px';
  terrTex.needsUpdate = true;
}


// ------------------------------------------------------------------ sector outlines
const SECTOR_R = 5, SECTOR_GAP = 0.6, SECTOR_STEP = 0.5;
let sectorCache = { key: null, shapes: [] };
function sectorShapes(t) {
  const held = (data.sectors || []).map((s) => ({ name: s.name, pts: s.members.map((id) => byId[id]).filter((p) => { const o = p && ownerAt(p, t); return o && ['earth', 'une', 'usr'].includes(o.p); }) }));
  const key = held.map((h) => h.pts.map((p) => p.id).join(',')).join('|');
  if (key === sectorCache.key) return sectorCache.shapes;
  const all = held.flatMap((h) => h.pts);
  const shapes = [];
  if (all.length) {
    const x0 = Math.min(...all.map((p) => p.x)) - SECTOR_R - 1, x1 = Math.max(...all.map((p) => p.x)) + SECTOR_R + 1;
    const y0 = Math.min(...all.map((p) => p.y)) - SECTOR_R - 1, y1 = Math.max(...all.map((p) => p.y)) + SECTOR_R + 1;
    const nx = Math.ceil((x1 - x0) / SECTOR_STEP) + 1, ny = Math.ceil((y1 - y0) / SECTOR_STEP) + 1;
    // nearest held member of each sector, per grid point
    const near = held.map(() => new Float32Array(nx * ny));
    for (let j = 0; j < ny; j++) for (let i = 0; i < nx; i++) {
      const x = x0 + i * SECTOR_STEP, y = y0 + j * SECTOR_STEP;
      held.forEach((h, k) => { let m = 1e9; for (const p of h.pts) { const d = Math.hypot(p.x - x, p.y - y); if (d < m) m = d; } near[k][j * nx + i] = m; });
    }
    held.forEach((h, k) => {
      if (h.pts.length < 2) return;
      const f = new Float32Array(nx * ny);
      for (let q = 0; q < nx * ny; q++) {
        let other = 1e9; held.forEach((_, kk) => { if (kk !== k && near[kk][q] < other) other = near[kk][q]; });
        const ds = near[k][q];
        f[q] = Math.min(SECTOR_R - ds, (other - ds) / 2 - SECTOR_GAP);
      }
      const lines = marching(f, nx, ny, x0, y0);
      const cxm = h.pts.reduce((a, p) => a + p.x, 0) / h.pts.length;
      shapes.push({ name: h.name, lines, lx: cxm, ly: Math.max(...h.pts.map((p) => p.y)) + SECTOR_R + 1.6 });
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
  // chain segments into polylines so the dash pattern runs continuously
  const k = (p) => p[0].toFixed(3) + ',' + p[1].toFixed(3);
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
    starBright[i] = w ? 1 : o ? 0.85 : 0.55;
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
  const legend = Object.keys(P).filter((k) => present.has(k)).map((k) => '<span><i style="background:' + P[k].color + '"></i>' + esc(P[k].name) + '</span>').join('');
  $('#legend').innerHTML = legend + (layers.reg && year >= 2302 ? '<span><i class="sec"></i>Republic sector</span>' : '') + (layers.bat ? '<span><i class="bt"></i>Battle or event</span>' : '');
  if (selected) renderSelected();
  if (!$('#sysview').hidden && sv.sys) renderSystemInfo();
  const tl = $('#timeline'); tl.setAttribute('aria-valuenow', year); tl.setAttribute('aria-valuetext', year + ', ' + eraOf(year));
  writeHash();
}
$('#thisyear').addEventListener('click', (e) => { const b = e.target.closest('.go'); if (b) select(b.dataset.sys, true); });

// ------------------------------------------------------------------ selection panel
function regionOf(s) {
  const sec = (data.sectors || []).find((x) => x.members.includes(s.id));
  if (sec) return sec.name;
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
  const held = o ? '<span class="sw" style="background:' + polColor(o.p) + '"></span>' + esc(polName(o.p)) + (o.note ? ' <span style="color:var(--muted)">(' + esc(o.note) + ')</span>' : '') + (o.derived ? '<sup class="drv" title="Date reconstructed, not stated in the book">†</sup>' : '') : 'Unclaimed';
  const evHtml = evs.length ? '<ul>' + evs.map((e) => '<li>' + (hasArticle(e.slug) ? '<a href="' + wikiHref(e.slug) + '">' + esc(e.label) + '</a>' : esc(e.label)) + ', ' + Math.floor(e.y) + '</li>').join('') + '</ul>' : '';
  const wHtml = ws.length ? '<ul>' + ws.map((w) => '<li>' + (hasArticle(w.slug) ? '<a href="' + wikiHref(w.slug) + '">' + esc(w.name) + '</a>' : esc(w.name)) + (w.native ? '' : ', ' + Math.floor(w.settled)) + '</li>').join('') + '</ul>' : '';
  $('#selected').innerHTML =
    '<div class="hd"><button type="button" class="x" aria-label="Close">×</button>' +
    '<span class="k">' + esc((reg ? reg + ' // ' : '') + (o ? polName(o.p) : 'Unclaimed')) + '</span>' +
    '<h1>' + esc(s.name) + '</h1><span class="ds">' + esc(desc) + '</span></div>' +
    '<dl><dt>Held by</dt><dd>' + held + '</dd>' +
    (wHtml ? '<dt>Worlds</dt><dd>' + wHtml + '</dd>' : '') +
    (s.catalogue ? '<dt>Catalogue</dt><dd>' + esc(s.catalogue) + '</dd>' : '') +
    (s.hazard ? '<dt>Hazard</dt><dd style="color:#F0B6A8">' + esc(s.hazard) + '</dd>' : '') +
    '<dt>From Sol</dt><dd>' + (s.id === 'sol' ? '—' : dist.toFixed(1) + ' light years') + '</dd>' +
    '<dt>Stars</dt><dd>' + ['Single', 'Binary', 'Trinary'][s.stars - 1] + '</dd>' +
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
const eventYears = new Set(data.events.map((e) => Math.floor(e.y)));
function drawTimeline() {
  const dpr = Math.min(2, window.devicePixelRatio || 1);
  const w = tlBox.clientWidth, h = tlBox.clientHeight;
  if (tl.width !== Math.round(w * dpr) || tl.height !== Math.round(h * dpr)) { tl.width = Math.round(w * dpr); tl.height = Math.round(h * dpr); }
  tlg.setTransform(dpr, 0, 0, dpr, 0, 0);
  tlg.clearRect(0, 0, w, h);
  const ppy = w / VISIBLE_YEARS, mid = w / 2, cyy = h / 2 - 4;
  const y0 = Math.floor(tlPos - VISIBLE_YEARS / 2 - 1), y1 = Math.ceil(tlPos + VISIBLE_YEARS / 2 + 1);
  tlg.font = "500 9px 'Jost', sans-serif"; tlg.textAlign = 'center'; tlg.textBaseline = 'alphabetic';
  for (let y = y0; y <= y1; y++) {
    if (y < RANGE[0] || y > RANGE[1]) continue;
    const x = mid + (y - tlPos) * ppy;
    if (x < -2 || x > w + 2) continue;
    const d = Math.min(1, Math.abs(x - mid) / mid);
    const grow = 1 + 0.75 * Math.pow(1 - d, 2);
    const decade = y % 10 === 0;
    const isCur = y === year;
    let bh = (decade ? 22 : 13) * grow;
    if (isCur) bh = 34;
    const lw = isCur ? 3 : decade ? 1.4 : 1;
    const a = isCur ? 1 : (0.35 + 0.55 * (1 - d)) * (decade ? 1 : 0.8);
    tlg.fillStyle = 'rgba(255,255,255,' + a + ')';
    tlg.fillRect(Math.round(x - lw / 2), cyy - bh / 2, lw, bh);
    if (eventYears.has(y) && !isCur) { tlg.fillStyle = 'rgba(242,193,78,' + (0.35 + 0.5 * (1 - d)) + ')'; tlg.fillRect(Math.round(x) - 1.5, cyy - bh / 2 - 6, 3, 3); }
    if (decade && !isCur && Math.abs(x - mid) > 34) { tlg.fillStyle = 'rgba(169,187,208,' + (0.25 + 0.5 * (1 - d)) + ')'; tlg.fillText(String(y), x, h - 6); }
  }
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
  const ppy = tlBox.clientWidth / VISIBLE_YEARS, now = performance.now();
  const dx = e.clientX - drag.lastX, dt = Math.max(1, now - drag.lastT);
  drag.v = 0.8 * (-dx / ppy / dt) + 0.2 * drag.v; drag.lastX = e.clientX; drag.lastT = now; drag.moved += Math.abs(dx);
  setPos(drag.pos - (e.clientX - drag.x) / ppy);
});
const endDrag = (e) => {
  if (!drag) return;
  tlBox.classList.remove('drag');
  if (drag.moved < 4) { // a click jumps to the year under the pointer
    const r = tlBox.getBoundingClientRect(), ppy = r.width / VISIBLE_YEARS;
    glide = { target: Math.round(tlPos + (e.clientX - r.left - r.width / 2) / ppy) };
  } else glide = { v: drag.v };
  drag = null;
};
tlBox.addEventListener('pointerup', endDrag); tlBox.addEventListener('pointercancel', endDrag);
tlBox.addEventListener('wheel', (e) => { e.preventDefault(); glide = null; setPos(tlPos + (Math.abs(e.deltaX) > Math.abs(e.deltaY) ? e.deltaX : e.deltaY) / 40); clearTimeout(tlBox._t); tlBox._t = setTimeout(() => { glide = { target: Math.round(tlPos) }; }, 160); }, { passive: false });
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
function makePlanets(s) {
  const r = rngFor(s.id);
  if (s.id === 'sol') {
    const solW = data.worlds.filter((w) => w.sys === 'sol');
    const moonsOf = (n) => solW.filter((w) => w.moon && w.pl === n).map((w) => ({ name: w.name, settled: w.settled, world: true, ph: r() * 6.28 }));
    return ['Mercury', 'Venus', 'Earth', 'Mars', 'Jupiter', 'Saturn', 'Uranus', 'Neptune'].map((n, i) => {
      const w = solW.find((x) => x.name === n);
      const moons = moonsOf(i + 1);
      if (n === 'Saturn') moons.push({ name: 'Titan', settled: 2150, world: true, ph: r() * 6.28 });
      return { name: n, a: [0.39, 0.72, 1, 1.52, 5.2, 9.5, 19.2, 30][i], size: [3, 5, 5.5, 4, 11, 10, 7, 7][i],
        type: ['Rock', 'Cloud world', 'Homeworld of humanity', 'Terraformed world', 'Gas giant', 'Ringed gas giant', 'Ice giant', 'Ice giant'][i],
        ring: i === 5, world: w ? n : null, settled: w ? w.settled : undefined, biome: w && w.biome, ph: r() * 6.28, moons, giant: i >= 4 };
    });
  }
  const known = data.worlds.filter((w) => w.sys === s.id);
  const names = (data.planetNames || {})[s.id] || {};
  const maxPl = Math.max(0, ...known.map((w) => w.pl || 0), ...Object.keys(names).map(Number));
  const n = Math.max(maxPl + 1 + Math.floor(r() * 2), known.length + 2, 3 + Math.floor(r() * 6));
  const hz = 1 + Math.floor(r() * 2);
  const out = []; let a = 0.25 + r() * 0.25;
  for (let i = 0; i < n; i++) {
    const MID = s.region2235 === 'rubin' ? TYPES_DEAD : TYPES_MID;   // nothing habitable in the Rubin Void
    const type = i < hz ? TYPES_IN[Math.floor(r() * TYPES_IN.length)] : i < hz + 2 ? MID[Math.floor(r() * MID.length)] : TYPES_OUT[Math.floor(r() * TYPES_OUT.length)];
    out.push({ name: names[i + 1] || s.name + ' ' + ROMAN[i], a, type, ph: r() * 6.28, world: null, moons: [] });
    a *= 1.5 + r() * 0.6;
  }
  const free = [];
  for (const w of known) {
    if (!w.pl) { free.push(w); continue; }
    const p = out[w.pl - 1];
    if (w.moon) p.moons.push({ name: w.name, slug: w.slug, settled: w.settled, world: true, ph: r() * 6.28 });
    else { p.world = w.name; p.slug = w.slug; p.settled = w.settled; p.biome = w.biome; }
  }
  const order = out.map((p, i) => i).filter((i) => !out[i].world).sort((x, y) => Math.abs(x - hz - 0.5) - Math.abs(y - hz - 0.5));
  free.forEach((w, k) => { const p = out[order[k]]; if (p) { p.world = w.name; p.slug = w.slug; p.settled = w.settled; p.biome = w.biome; } });
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
  renderSystemInfo();
  writeHash();
}
function closeSystem() { $('#sysview').hidden = true; sv.sys = null; writeHash(); }
$('#sv-back').onclick = closeSystem;
document.addEventListener('keydown', (e) => { if (e.key === 'Escape' && !$('#sysview').hidden) closeSystem(); });
$('#sv-names').addEventListener('change', (e) => $('#sv-map').classList.toggle('nonames', !e.target.checked));
// The orbit view is redrawn every frame, so bodies are picked by position, not by element.
sv.hits = [];
let svDown = null;
$('#sv-map').addEventListener('pointerdown', (e) => { svDown = { x: e.clientX, y: e.clientY }; });
$('#sv-map').addEventListener('pointerup', (e) => {
  if (!svDown || Math.hypot(e.clientX - svDown.x, e.clientY - svDown.y) > 6) { svDown = null; return; }
  svDown = null;
  const r = $('#sv-map').getBoundingClientRect(), x = e.clientX - r.left, y = e.clientY - r.top;
  let best = null, bd = Infinity;
  for (const h of sv.hits) {
    const d = h.box ? (x >= h.box[0] && x <= h.box[2] && y >= h.box[1] && y <= h.box[3] ? 0 : Infinity) : Math.hypot(h.x - x, h.y - y) - h.r;
    if (d <= 0 && d < bd) { bd = d; best = h; } else if (d <= 0 && best === null) best = h;
  }
  sv.pick = best ? best.key : null;
  renderSystemInfo();
  if (sv.pick) $('#sv-info').scrollTop = 0;
});
$('#sv-map').addEventListener('pointermove', (e) => {
  const r = $('#sv-map').getBoundingClientRect(), x = e.clientX - r.left, y = e.clientY - r.top;
  const over = sv.hits.some((h) => h.box ? x >= h.box[0] && x <= h.box[2] && y >= h.box[1] && y <= h.box[3] : Math.hypot(h.x - x, h.y - y) <= h.r);
  $('#sv-map').style.cursor = over ? 'pointer' : '';
});
$('#sv-info').addEventListener('click', (e) => { const b = e.target.closest('[data-b]'); if (b) { sv.pick = b.dataset.b; renderSystemInfo(); } });
$('#sv-map').addEventListener('wheel', (e) => { e.preventDefault(); sv.zoom = Math.max(0.4, Math.min(4, sv.zoom * (e.deltaY > 0 ? 0.9 : 1.1))); }, { passive: false });

const chev = '<svg width="14" height="14" viewBox="0 0 16 16" fill="none" stroke="#A9BBD0" stroke-width="1.6" aria-hidden="true"><path d="M4 6l4 4 4-4"/></svg>';
function sec(title, rows) {
  return '<button type="button" class="sv-sec" aria-expanded="true">' + esc(title) + chev + '</button><table>' + rows.map(([k, v, later]) => '<tr' + (later ? ' class="later"' : '') + '><th scope="row">' + esc(k) + '</th><td>' + v + '</td></tr>').join('') + '</table>';
}

// a body key is "3" for planet III, or "3.1" for its second moon
function bodyFor(key) {
  if (!key || !sv.sys) return null;
  const [pi, mi] = key.split('.').map(Number), p = sv.planets[pi];
  if (!p) return null;
  if (mi === undefined || Number.isNaN(mi)) {
    const settled = p.world && (p.settled === undefined || p.settled <= year + 0.999);
    return { key, kind: 'planet', p, pi, label: settled ? p.world : p.name, world: p.world, slug: p.slug, settled: p.settled, biome: p.biome, type: p.type };
  }
  const m = p.moons[mi]; if (!m) return null;
  const wd = data.worlds.find((w) => w.sys === sv.sys.id && w.name === m.name) || {};
  return { key, kind: 'moon', p, pi, m, label: m.name, world: m.world ? m.name : null, slug: m.slug, settled: m.settled, biome: wd.biome, type: 'Moon' };
}
function bodyInfo(b, t, o) {
  const live = b.world && (b.settled === undefined || b.settled <= t);
  const burned = live && burnedAt(sv.sys.id, t).find((x) => x.name === b.world);
  const rows = [];
  const parentName = b.p.world && (b.p.settled === undefined || b.p.settled <= t) ? b.p.world : b.p.name;
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
  let h = sec('Selected · ' + b.label, rows);
  if (b.slug && hasArticle(b.slug) && live) h += '<a class="art" href="' + wikiHref(b.slug) + '">Read about ' + esc(b.label) + ' →</a>';
  return h;
}
function renderSystemInfo() {
  const s = sv.sys, t = year + 0.999, o = ownerAt(s, t), ws = worldsAt(s.id, t), reg = regionOf(s);
  const evs = data.events.filter((e) => e.sys === s.id);
  const hist = ownHistory(s).filter((h) => h.y > 1950);
  const dist = Math.hypot(s.x, s.y, s.z);
  let html = '<div class="hd"><span class="k">' + esc(o ? polName(o.p) : 'Unclaimed') + '</span><h1>' + esc(s.name) + '</h1><span>Star system' + (reg ? ' · ' + esc(reg) : '') + '</span></div>';
  const body = bodyFor(sv.pick);
  if (body) html += bodyInfo(body, t, o);
  html += sec('Observation data · epoch ' + year, [
    ['Stars', ['Single', 'Binary', 'Trinary'][s.stars - 1]],
    ...(s.catalogue ? [['Catalogue name', esc(s.catalogue)]] : []),
    ...(s.hazard ? [['Hazard', '<span style="color:#F0B6A8">' + esc(s.hazard) + '</span>']] : []),
    ['Distance from Sol', s.id === 'sol' ? '—' : dist.toFixed(1) + ' ly'],
    ['Map position', s.x.toFixed(1) + ', ' + s.y.toFixed(1) + ', ' + s.z.toFixed(1) + ' ly<sup class="drv" title="Height above the plane is reconstructed">†</sup>'],
    ['Planets', String(sv.planets.length)],
  ]);
  html += sec('Sovereignty', [['Held by', o ? '<span class="sw" style="background:' + polColor(o.p) + '"></span>' + esc(polName(o.p)) + (o.note ? ', ' + esc(o.note) : '') : 'Unclaimed']]
    .concat(hist.map((h) => [String(Math.floor(h.y)), esc(polName(h.p)) + (h.note ? ', ' + esc(h.note) : '') + (h.derived ? '<sup class="drv" title="Date reconstructed">†</sup>' : ''), h.y > t])));
  if (ws.length) html += sec('Settled worlds', ws.map((w) => [w.name, (hasArticle(w.slug) ? '<a href="' + wikiHref(w.slug) + '">Article</a> · ' : '') + (w.native ? 'Native world' : fmtDate(w.settled))]));
  if (evs.length) html += sec('History', evs.map((e) => [fmtDate(e.y), hasArticle(e.slug) ? '<a href="' + wikiHref(e.slug) + '">' + esc(e.label) + '</a>' : esc(e.label), e.y > t]));
  if (hasArticle(s.id)) html += '<a class="art" href="' + wikiHref(s.id) + '">Read the article →</a>';
  $('#sv-info').innerHTML = html;
  $('#sv-info').querySelectorAll('.sv-sec').forEach((b) => b.addEventListener('click', () => { const open = b.getAttribute('aria-expanded') === 'true'; b.setAttribute('aria-expanded', String(!open)); b.nextElementSibling.hidden = open; }));
  $('#sv-title').textContent = (body ? body.label : s.name) + ' - ' + year;
  const last = evs.filter((e) => e.y <= t).pop();
  $('#sv-sub').textContent = last ? last.label + ', ' + fmtDate(last.y) : (o ? polName(o.p) : 'Unclaimed');
  $('#sv-legend').innerHTML = o ? '<span><i style="background:' + polColor(o.p) + '"></i>' + esc(polName(o.p)) + '</span>' : '';
}
function drawSystem(dt) {
  if (!sv.sys) return;
  sv.t += dt / 1000 * sv.speed;
  const svg = $('#sv-map'), w = svg.clientWidth, h = svg.clientHeight; if (!w) return;
  const cxs = w * 0.5, cys = h * 0.5, tilt = 0.42;
  const amax = sv.planets[sv.planets.length - 1].a;
  const scale = (Math.min(w, h / tilt) * 0.46) * sv.zoom;
  const R = (a) => (Math.log(1 + a * 4) / Math.log(1 + amax * 4)) * scale;
  const t = year + 0.999;
  let out = '<defs><radialGradient id="sv-star"><stop offset="0" stop-color="#FFFFFF"/><stop offset=".5" stop-color="#FFFFFF"/><stop offset="1" stop-color="#FFFFFF" stop-opacity="0"/></radialGradient></defs>';
  out += '<ellipse cx="' + cxs + '" cy="' + cys + '" rx="' + (R(amax) * 1.18) + '" ry="' + (R(amax) * 1.18 * tilt) + '" fill="none" stroke="#fff" stroke-opacity=".35" stroke-dasharray="2 6"/>';
  out += '<text class="lbl sb" x="' + cxs + '" y="' + (cys - R(amax) * 1.18 * tilt - 8) + '" text-anchor="middle" font-size="10" letter-spacing="2" fill="#C9D6E5">PILLAI RADIUS · JUMP LIMIT</text>';
  for (const p of sv.planets) out += '<ellipse cx="' + cxs + '" cy="' + cys + '" rx="' + R(p.a) + '" ry="' + R(p.a) * tilt + '" fill="none" stroke="#fff" stroke-opacity="' + (p.world ? 0.55 : 0.22) + '"/>';
  out += '<circle cx="' + cxs + '" cy="' + cys + '" r="22" fill="url(#sv-star)"/><circle cx="' + cxs + '" cy="' + cys + '" r="7" fill="#fff"/>';
  out += '<text class="lbl nm" x="' + (cxs + 14) + '" y="' + (cys - 16) + '" font-size="15">' + esc(sv.sys.name) + '</text>';
  const items = sv.planets.map((p) => {
    const ang = p.ph + sv.t * 0.6 / Math.pow(p.a, 1.5);
    return { p, x: cxs + Math.cos(ang) * R(p.a), y: cys + Math.sin(ang) * R(p.a) * tilt };
  }).sort((a, b) => a.y - b.y);
  const link = (slug, inner) => (slug && hasArticle(slug) ? '<a href="' + wikiHref(slug) + '">' + inner + '</a>' : inner);
  const burnedList = burnedAt(sv.sys.id, t);
  const hits = [];
  for (const { p, x, y } of items) {
    const settled = p.world && (p.settled === undefined || p.settled <= t);
    const burnP = settled && burnedList.find((b) => b.name === p.world);
    if (p.ring) out += '<ellipse cx="' + x + '" cy="' + y + '" rx="' + p.size * 2 + '" ry="' + p.size * 0.65 + '" transform="rotate(-14 ' + x + ' ' + y + ')" fill="none" stroke="#fff" stroke-opacity=".8" stroke-width="1.5"/>';
    const pi = sv.planets.indexOf(p);
    out += '<circle cx="' + x + '" cy="' + y + '" r="' + p.size + '" fill="' + (burnP ? '#E07A5F' : '#fff') + '"/>';
    if (sv.pick === String(pi)) out += '<circle cx="' + x + '" cy="' + y + '" r="' + (p.size + 10) + '" fill="none" stroke="#F2C14E" stroke-width="1.5" stroke-dasharray="3 3"/>';
    hits.push({ key: String(pi), x, y, r: Math.max(16, p.size + 8) });
    if (settled) out += '<circle cx="' + x + '" cy="' + y + '" r="' + (p.size + 4) + '" fill="none" stroke="#fff" stroke-opacity=".85"/>';
    // moons orbit the planet; their names are listed beside it
    const moonLines = [];
    p.moons.forEach((m, k) => {
      const mr = p.size + 12 + k * 7, ang = m.ph + sv.t * 2.2 / (1 + k * 0.6);
      const mx = x + Math.cos(ang) * mr, my = y + Math.sin(ang) * mr * 0.55;
      const live = m.settled <= t, burnM = live && burnedList.find((b) => b.name === m.name);
      out += '<ellipse cx="' + x + '" cy="' + y + '" rx="' + mr + '" ry="' + mr * 0.55 + '" fill="none" stroke="#fff" stroke-opacity=".18"/>';
      out += '<circle cx="' + mx + '" cy="' + my + '" r="2.6" fill="' + (burnM ? '#E07A5F' : '#fff') + '"/>';
      if (sv.pick === pi + '.' + k) out += '<circle cx="' + mx + '" cy="' + my + '" r="8" fill="none" stroke="#F2C14E" stroke-width="1.5" stroke-dasharray="3 3"/>';
      hits.push({ key: pi + '.' + k, x: mx, y: my, r: 9 });
      if (live) {
        out += '<circle cx="' + mx + '" cy="' + my + '" r="5.5" fill="none" stroke="#fff" stroke-opacity=".8"/>';
        moonLines.push('<tspan data-b="' + pi + '.' + k + '" style="cursor:pointer" class="nm" font-size="11">' + esc(m.name) + '</tspan>' + (burnM ? '<tspan class="sb" font-size="10"> · burned ' + Math.floor(burnM.y) + '</tspan>' : '<tspan class="sb" font-size="10"> · moon</tspan>'));
      }
    });
    moonLines.forEach((ln, k) => {
      const lx = x + p.size + 16 + p.moons.length * 7, ly = y + 4 + k * 15;
      out += '<text class="lbl" x="' + lx + '" y="' + ly + '">' + ln + '</text>';
      if (!$('#sv-map').classList.contains('nonames')) hits.push({ key: pi + '.' + k, box: [lx, ly - 12, lx + p.moons[k].name.length * 8.5, ly + 3] });
    });
    const label = settled ? p.world : p.name;
    const bio = settled && biomeAt(worldByName(sv.sys.id, p.world), t);
    const sub = burnP ? 'Burned ' + Math.floor(burnP.y) : bio || p.type;
    const lift = sv.planets.indexOf(p) % 2 ? 22 : 0;
    if (!$('#sv-map').classList.contains('nonames')) hits.push({ key: String(pi), box: [x + 4, y - p.size - 38 - lift, x + 8 + label.length * (settled ? 11 : 9), y - p.size - 4 - lift] });
    out += '<g class="lbl"><line x1="' + x + '" y1="' + (y - p.size - 2) + '" x2="' + x + '" y2="' + (y - p.size - 30 - lift) + '" stroke="#fff" stroke-width="1"/>' +
      '<text class="nm" data-b="' + pi + '" style="cursor:pointer" x="' + (x + 6) + '" y="' + (y - p.size - 22 - lift) + '" font-size="' + (settled ? 17 : 13) + '">' + esc(label) + '</text>' +
      '<text class="sb" x="' + (x + 6) + '" y="' + (y - p.size - 8 - lift) + '">' + esc(ROMAN[sv.planets.indexOf(p)] + ' · ' + sub) + '</text></g>';
  }
  svg.innerHTML = out;
  sv.hits = hits.reverse();   // labels and nearer bodies first
}

// ------------------------------------------------------------------ hash state
let hashT = null;
function writeHash() {
  clearTimeout(hashT);
  hashT = setTimeout(() => {
    const q = new URLSearchParams();
    q.set('year', year);
    if (selected) q.set('sys', selected.id);
    if (sv.sys && !$('#sysview').hidden) q.set('view', 'system');
    window.history.replaceState(null, '', '#' + q.toString());
  }, 250);
}

// ------------------------------------------------------------------ loop
function resize() {
  const w = canvas.clientWidth, h = canvas.clientHeight;
  renderer.setSize(w, h, false); camera.aspect = w / h; camera.updateProjectionMatrix();
  starMat.uniforms.uScale.value = Math.min(2, window.devicePixelRatio || 1);
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
  if (fromHash.get('view') === 'system') openSystem(fromHash.get('sys'));
}
requestAnimationFrame(frame);
