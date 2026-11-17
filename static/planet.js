// Planet globes for the Archive and the Atlas.
// Each world state has two maps: <year>-day.webp (colour) and <year>-data.webp
// (R lights, G clouds, B water, A height). makeGlobe builds a lit sphere from them.
export function stateAt(p, t) {
  let s = p.states[0];
  for (const x of p.states) if (x.y <= t) s = x;
  return s;
}

export function makeGlobe(THREE, o) {
  const L = new THREE.TextureLoader();
  const tex = (u, srgb) => { const t = L.load(u, o.onload); if (srgb) t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = 8; return t; };
  const sun = new THREE.Vector3(...(o.sun || [1, 0.25, 0.6])).normalize();
  const g = new THREE.Group();
  const day = tex(o.day, true), data = o.data ? tex(o.data, false) : null;
  const glow = new THREE.Color(o.glow || '#ffc27a');
  const mat = new THREE.ShaderMaterial({
    uniforms: { day: { value: day }, data: { value: data }, hasData: { value: data ? 1 : 0 }, sunDir: { value: sun }, glowCol: { value: glow }, relief: { value: o.relief ?? 2.2 }, texel: { value: new THREE.Vector2(1 / 512, 1 / 256) } },
    vertexShader: `varying vec2 vUv; varying vec3 vN; varying vec3 vW; varying vec3 vT; varying vec3 vB;
      void main(){ vUv=uv; vN=normalize(mat3(modelMatrix)*normal);
        vec3 t=cross(vec3(0.,1.,0.),normal); t=length(t)<1e-4?vec3(1.,0.,0.):normalize(t);
        vT=normalize(mat3(modelMatrix)*t); vB=normalize(cross(vN,vT));
        vec4 w=modelMatrix*vec4(position,1.); vW=w.xyz; gl_Position=projectionMatrix*viewMatrix*w; }`,
    fragmentShader: `uniform sampler2D day,data; uniform float hasData,relief; uniform vec3 sunDir,glowCol; uniform vec2 texel;
      varying vec2 vUv; varying vec3 vN; varying vec3 vW; varying vec3 vT; varying vec3 vB;
      void main(){
        vec4 d=hasData>0.5?texture2D(data,vUv):vec4(0.,0.,0.,.5);
        vec3 n=normalize(vN);
        if(hasData>0.5){
          float hx=texture2D(data,vUv+vec2(texel.x,0.)).a-texture2D(data,vUv-vec2(texel.x,0.)).a;
          float hy=texture2D(data,vUv+vec2(0.,texel.y)).a-texture2D(data,vUv-vec2(0.,texel.y)).a;
          n=normalize(vN+(vT*hx-vB*hy)*relief*(1.-d.b));
        }
        float dg=dot(normalize(vN),sunDir), lit=smoothstep(-0.03,0.3,dot(n,sunDir));
        vec3 c=texture2D(day,vUv).rgb;
        float cs=hasData>0.5?texture2D(data,vUv+vec2(-0.004,0.002)).g:0.;
        c*=1.-cs*0.35*smoothstep(0.,0.3,dg);
        vec3 v=normalize(cameraPosition-vW), h=normalize(sunDir+v);
        float spec=pow(max(dot(normalize(vN),h),0.),140.)*d.b*0.12;
        vec3 col=c*(0.01+lit*1.05)+vec3(1.,.95,.85)*spec*smoothstep(0.,0.2,dg);
        col+=glowCol*d.r*((1.-smoothstep(-0.15,0.1,dg))*1.7+0.03);
        gl_FragColor=vec4(col,1.);
        #include <colorspace_fragment>
      }`,
  });
  g.add(new THREE.Mesh(new THREE.SphereGeometry(1, 96, 72), mat));
  if (data && o.clouds !== false) {
    const cm = new THREE.ShaderMaterial({
      uniforms: { data: { value: data }, sunDir: { value: sun } }, transparent: true, depthWrite: false,
      vertexShader: `varying vec2 vUv; varying vec3 vN; void main(){ vUv=uv; vN=normalize(mat3(modelMatrix)*normal); gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.);} `,
      fragmentShader: `uniform sampler2D data; uniform vec3 sunDir; varying vec2 vUv; varying vec3 vN;
        void main(){ float a=texture2D(data,vUv).g; float lit=smoothstep(-0.1,0.3,dot(normalize(vN),sunDir)); gl_FragColor=vec4(vec3(.97)*(.03+lit),a*.92); }`,
    });
    const cl = new THREE.Mesh(new THREE.SphereGeometry(1.008, 96, 72), cm); g.add(cl); g.userData.clouds = cl;
  }
  if (o.atmo) {
    const am = new THREE.ShaderMaterial({
      uniforms: { sunDir: { value: sun }, tint: { value: new THREE.Color(o.atmo) } },
      transparent: true, depthWrite: false, side: THREE.BackSide, blending: THREE.AdditiveBlending,
      vertexShader: `varying vec3 vN; varying vec3 vW; void main(){ vN=normalize(mat3(modelMatrix)*normal); vec4 w=modelMatrix*vec4(position,1.); vW=w.xyz; gl_Position=projectionMatrix*viewMatrix*w; }`,
      fragmentShader: `uniform vec3 sunDir,tint; varying vec3 vN; varying vec3 vW;
        void main(){ vec3 v=normalize(cameraPosition-vW); float f=pow(1.-abs(dot(v,vN)),1.6); float l=smoothstep(-0.35,0.5,dot(vN,sunDir)); gl_FragColor=vec4(tint*f*l*.55,1.); }`,
    });
    g.add(new THREE.Mesh(new THREE.SphereGeometry(1.035, 96, 64), am));
  }
  return g;
}

// lat/lon (degrees) to a point on the unit sphere in the globe's own frame
export function latLon(THREE, lat, lon, r = 1) {
  const la = lat * Math.PI / 180, lo = lon * Math.PI / 180;
  return new THREE.Vector3(Math.cos(la) * Math.cos(lo) * r, Math.sin(la) * r, -Math.cos(la) * Math.sin(lo) * r);
}

// An interactive globe in a container: drag to turn, slow spin, city labels.
export function mountGlobe(THREE, el, o) {
  const W = el.clientWidth || 320, H = o.height || W;
  const r = new THREE.WebGLRenderer({ antialias: true, alpha: true });
  r.setPixelRatio(Math.min(2, window.devicePixelRatio || 1)); r.setSize(W, H);
  el.appendChild(r.domElement);
  const labels = document.createElement('div'); labels.className = 'pg-labels'; el.appendChild(labels);
  const sc = new THREE.Scene(); const cam = new THREE.PerspectiveCamera(30, W / H, 0.1, 100); cam.position.set(0, 0, o.dist || 4.1);
  let globe = null; const spin = new THREE.Group(); sc.add(spin);
  let rx = 0.25, ry = 0, drag = null, auto = true;
  const set = (s) => {
    if (globe) { spin.remove(globe); globe.traverse((m) => { if (m.material) { m.material.dispose(); m.geometry.dispose(); } }); }
    globe = makeGlobe(THREE, { day: o.base + s.k + '-day.webp', data: s.noData ? null : o.base + s.k + '-data.webp', atmo: s.atmo, glow: s.glow, sun: [0.8, 0.25, 0.55] });
    spin.add(globe);
    labels.innerHTML = '';
    (o.cities || []).forEach((c) => {
      if (!c.n) return;
      const d = document.createElement('span'); d.textContent = c.n; d.dataset.lat = c.lat; d.dataset.lon = c.lon; labels.appendChild(d);
    });
  };
  if (o.lon !== undefined) ry = -Math.PI / 2 - o.lon * Math.PI / 180;
  r.domElement.addEventListener('pointerdown', (e) => { drag = { x: e.clientX, y: e.clientY, rx, ry }; auto = false; r.domElement.setPointerCapture(e.pointerId); });
  r.domElement.addEventListener('pointermove', (e) => { if (!drag) return; ry = drag.ry + (e.clientX - drag.x) * 0.01; rx = Math.max(-1.2, Math.min(1.2, drag.rx + (e.clientY - drag.y) * 0.01)); });
  r.domElement.addEventListener('pointerup', () => { drag = null; });
  const v = new THREE.Vector3();
  let last = performance.now();
  const tick = (now) => {
    const dt = Math.min(0.1, (now - last) / 1000); last = now;
    if (auto) ry += dt * 0.08;
    spin.rotation.set(rx, ry, 0);
    if (globe && globe.userData.clouds) globe.userData.clouds.rotation.y += dt * 0.004;
    r.render(sc, cam);
    for (const s of labels.children) {
      v.copy(latLon(THREE, +s.dataset.lat, +s.dataset.lon, 1.01)).applyEuler(spin.rotation);
      const front = v.z > 0.15; const p = v.clone().project(cam);
      s.style.transform = 'translate(' + ((p.x + 1) / 2 * W) + 'px,' + ((1 - p.y) / 2 * H) + 'px)';
      s.style.opacity = front ? 1 : 0;
    }
    if (el.isConnected) requestAnimationFrame(tick); else r.dispose();
  };
  requestAnimationFrame(tick);
  return { set };
}

// A flat map with city labels, from the same day map.
export function flatMap(el, o) {
  const s = o.state;
  el.innerHTML = '<div class="pm-wrap"><img alt="Map of ' + o.name + '" src="' + o.base + s.k + '-day.webp"><svg viewBox="0 0 1024 512" preserveAspectRatio="none"></svg></div>';
  const svg = el.querySelector('svg');
  let out = '';
  for (let lat = -60; lat <= 60; lat += 30) out += '<line x1="0" x2="1024" y1="' + (256 - lat / 90 * 256) + '" y2="' + (256 - lat / 90 * 256) + '" class="pm-grid"/>';
  for (let lon = -150; lon <= 150; lon += 30) out += '<line y1="0" y2="512" x1="' + (512 + lon / 180 * 512) + '" x2="' + (512 + lon / 180 * 512) + '" class="pm-grid"/>';
  for (const c of o.cities || []) {
    if (!c.n) continue;
    const x = 512 + c.lon / 180 * 512, y = 256 - c.lat / 90 * 256;
    out += '<circle cx="' + x + '" cy="' + y + '" r="' + (c.w >= 1 ? 5 : 3.5) + '" class="pm-city' + (c.w >= 1 ? ' cap' : '') + '"/>';
    out += '<text x="' + (x + 8) + '" y="' + (y + 4) + '" class="pm-lbl' + (c.w >= 1 ? ' cap' : '') + '">' + c.n + '</text>';
  }
  svg.innerHTML = out;
}
