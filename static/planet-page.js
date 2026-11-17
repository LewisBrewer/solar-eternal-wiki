// Article pages: a turning globe in the infobox and a labelled flat map under Geography.
import * as THREE from 'three';
import { mountGlobe, flatMap, stateAt } from './planet.js';
const fig = document.querySelector('.ib-globe');
if (fig) {
  const slug = fig.dataset.planet, base = '../assets/planets/' + slug + '/';
  const all = await (await fetch('../assets/planets/planets.json')).json();
  const p = all[slug];
  if (p) {
    const cap = (p.cities || [])[0] || { lon: 0 };
    let cur = p.states[p.states.length - 1];
    const g = mountGlobe(THREE, fig.querySelector('.pg'), { base, cities: p.cities, lon: cap.lon });
    g.set(cur);
    const yrs = fig.querySelector('.pg-years');
    const map = document.createElement('figure'); map.className = 'planet-map';
    const draw = () => { flatMap(map, { base, state: cur, year: cur.y, cities: p.cities, name: p.name }); map.insertAdjacentHTML('beforeend', '<figcaption>' + p.name + ' in ' + cur.y + '</figcaption>'); };
    p.states.forEach((s) => {
      const b = document.createElement('button'); b.type = 'button'; b.textContent = s.y; if (s === cur) b.className = 'on';
      b.onclick = () => { cur = s; g.set(s); draw(); yrs.querySelectorAll('button').forEach((x) => x.classList.toggle('on', x === b)); };
      yrs.appendChild(b);
    });
    const h = [...document.querySelectorAll('.prose h2, .prose h3')].find((x) => /^(geography|description)$/i.test(x.textContent.trim()));
    if (h) { draw(); h.after(map); }
  }
}
