// Article pages: a turning globe in the infobox and a labelled flat map under Geography.
// A year slider crossfades the globe and the map between the generated keyframes.
import * as THREE from 'three';
import { mountGlobe, flatMap, statesAt } from './planet.js';
const fig = document.querySelector('.ib-globe');
if (fig) {
  const slug = fig.dataset.planet, base = '../assets/planets/' + slug + '/';
  const all = await (await fetch('../assets/planets/planets.json')).json();
  const p = all[slug];
  if (p) {
    const cap = (p.cities || [])[0] || { lon: 0 };
    const y0 = p.states[0].y, y1 = p.states[p.states.length - 1].y;
    let year = y1;
    const g = mountGlobe(THREE, fig.querySelector('.pg'), { base, cities: p.cities, lon: cap.lon });
    g.setYear(p, year);
    const yrs = fig.querySelector('.pg-years');
    const map = document.createElement('figure'); map.className = 'planet-map';
    const draw = () => {
      const { a, b, k } = statesAt(p, year);
      flatMap(map, { base, state: a, next: b, k, year, cities: p.cities, name: p.name });
      map.insertAdjacentHTML('beforeend', '<figcaption>' + p.name + ' in ' + Math.round(year) + '</figcaption>');
    };
    if (y1 > y0) {
      yrs.innerHTML = '<input type="range" min="' + y0 + '" max="' + y1 + '" step="1" value="' + y1 + '" aria-label="Year"><output>' + y1 + '</output>';
      const rng = yrs.querySelector('input'), out = yrs.querySelector('output');
      let pend = 0;
      rng.addEventListener('input', () => {
        year = +rng.value; out.textContent = year; g.setYear(p, year);
        cancelAnimationFrame(pend); pend = requestAnimationFrame(() => { if (map.isConnected) draw(); });
      });
    }
    const h = [...document.querySelectorAll('.prose h2, .prose h3')].find((x) => /^(geography|description)$/i.test(x.textContent.trim()));
    if (h) { draw(); h.after(map); }
  }
}
