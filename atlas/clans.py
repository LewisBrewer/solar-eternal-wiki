"""The Fevarian clans and their monoliths, spread across the northern freeholds and the Veil
(Lewis, 18 November 2026). A clan may hold several monoliths; some have lost theirs and live on
their hulks and stations. Every monolith has a home system, sails with the Khanate's fleets from
its departure, and is destroyed in a battle the book describes, fails as a hulk in the Veil's
wells, or survives with the successor khanates. A clan's hulks and stations never leave home.

The book's figures drive the losses: 32 before 2428 (Maweer marches 20, Vur Duri 12), 100 by 2440,
Talandra 33, Procyon 19, Sol 73, Alpha Centauri 18, Second Talandra 43, the Scouring 81, and in 2460
twelve mobile monoliths and forty hulks. The total follows from them (about 465 monoliths in
about 300 clans). Clan names other than the book's nine are invented."""
import math, random, re

CANON = {  # name: (home system, monoliths, notes)
    "D'Rhen": ('rhen-tal', 2), "D'Dhen": ('dhen-ossa', 1), "D'Vesh": ('vesh-mar', 3), "D'Ashan": ('ashan-dur', 5),
    "D'Kasht": ('kasht', 2), "D'Mareth": ('mareth-vel', 2), "D'Hovar": ('vharr', 2), "D'Tarik": ('sel-tarik', 7),
    "D'Sethen": ('ul-sethen', 2),
}
DESIGNED = ["D'Ossar", "D'Varek", "D'Thulen", "D'Kharim", "D'Morrek", "D'Selvar", "D'Unnar", "D'Zhaal", "D'Rasken",
            "D'Volun", "D'Ashtor", "D'Garron", "D'Ishul", "D'Keleth", "D'Yeshar", "D'Nemar", "D'Akhul", "D'Sorrah",
            "D'Thurr", "D'Orsh", "D'Brahn", "D'Vahrel", "D'Esken"]
ON = ['Rh', 'Dh', 'V', 'K', 'M', 'H', 'T', 'S', 'Th', 'Kh', 'Z', 'Zh', 'Sh', 'N', 'B', 'G', 'Y', 'R', 'L', 'Dr', 'Gh', 'Q', 'Br', 'Kr', 'Ul', 'Or', 'Esk', 'Ash', 'Ish', 'Ak', 'Ir', 'Os', 'Ar']
VO = ['a', 'e', 'o', 'u', 'i', 'aa', 'ae', 'ei', 'au']
EN = ['n', 'sh', 'r', 'k', 'l', 'th', 'm', 'rn', 'sk', 'rk', 'v', 'x', 'kh', 'ss', 'd', 'rr', 'ht']
EN2 = ['', 'an', 'en', 'esh', 'ar', 'ek', 'ul', 'oth', 'ash', 'ir', 'or', 'eth', 'un', 'al', 'ik', 'ath', 'uun', 'iel']

def slug(s): return re.sub(r'[^a-z0-9]+', '-', s.lower().replace("'", '')).strip('-')

def build(systems, by, FEATURES, marches, north_m, west_marches, FREEHOLDS, VEIL_IDS):
    rng = random.Random(4471)
    north_homes = list(FREEHOLDS)
    veil_homes = list(VEIL_IDS)
    # ---------------------------------------------------------------- the clans
    taken = set(CANON) | set(DESIGNED)
    names = []
    while len(names) < 300 - len(CANON) - len(DESIGNED):
        n = "D'" + rng.choice(ON) + rng.choice(VO) + rng.choice(EN) + rng.choice(EN2)
        if len(n) > 11 or n in taken: continue
        taken.add(n); names.append(n)
    clans = []
    for n, (home, m) in CANON.items():
        clans.append({'name': n, 'home': home, 'm': m, 'canon': True})
    pool = DESIGNED + names
    # north: 34 clans, 40 monoliths; the rest in the Veil, 425 monoliths
    north_names = pool[:34]; veil_names = pool[34:]
    def counts(k, total):
        out = []
        for _ in range(k):
            r = rng.random()
            out.append(0 if r < 0.14 else 1 if r < 0.68 else 2 if r < 0.88 else 3 if r < 0.96 else 4)
        while sum(out) > total:
            i = rng.randrange(k)
            if out[i] > 0: out[i] -= 1
        while sum(out) < total:
            out[rng.randrange(k)] += 1
        return out
    for n, m in zip(north_names, counts(len(north_names), 40)):
        clans.append({'name': n, 'home': north_homes[len([c for c in clans if c['home'] in north_homes]) % len(north_homes)], 'm': m})
    canon_m = sum(c['m'] for c in clans if c.get('canon'))
    for i, (n, m) in enumerate(zip(veil_names, counts(len(veil_names), 425 - canon_m))):
        clans.append({'name': n, 'home': veil_homes[i % len(veil_homes)], 'm': m})
    for c in clans:
        c['id'] = slug(c['name']); c['north'] = c['home'] in north_homes
        c['inv'] = not c.get('canon')
    # ---------------------------------------------------------------- the monoliths
    mons = []
    for c in clans:
        for k in range(c['m']):
            mons.append({'clan': c['id'], 'north': c['north'], 'home': c['home'], 'k': k})
    rng.shuffle(mons)
    byclan = {}
    for m in mons: byclan.setdefault(m['clan'], []).append(m)
    # canon monoliths: the Returning and Ushar's Word (D'Rhen); Orun D'Vesh's at Saolea; D'Kasht's at Alpha Centauri
    fixed = {}
    r = byclan["drhen"]; r[0]['name'] = 'the Returning'; r[1]['name'] = "Ushar's Word"
    fixed[id(r[0])] = ('sol', 2446.93, 'the Battle of Earth'); fixed[id(r[1])] = ('talandra', 2449.47, 'Second Talandra')
    fixed[id(byclan['dvesh'][0])] = ('saolea', 2434.2, 'Saolea')
    fixed[id(byclan['dkasht'][0])] = ('alpha-centauri', 2447.8, 'Alpha Centauri')
    fixed[id(byclan['dhovar'][0])] = ('kuma', 2455.5, 'the Long Siege')
    fixed[id(byclan['dhovar'][1])] = ('far-south', 2458.79, 'the last monolith outside the Veil')
    # ---------------------------------------------------------------- the losses, battle by battle
    m6 = [s['id'] for s in marches]; wm = [s['id'] for s in west_marches]; nm = [s['id'] for s in north_m]
    EVENTS = [  # (system, year, count, pool, label)
        (nm[0] if nm else 'arausnyria', 2414.6, 4, 'north', 'the northern Maweer campaign'),
        (nm[1] if len(nm) > 1 else 'thaaram', 2415.3, 3, 'north', 'the northern Maweer campaign'),
        (nm[2] if len(nm) > 2 else 'aphris', 2416.8, 3, 'north', 'the northern Maweer campaign'),
        (m6[0], 2413.6, 4, 'veil', 'the Maweer marches'), (m6[2], 2414.8, 3, 'veil', 'the Maweer marches'), (wm[0], 2415.5, 3, 'veil', 'the western marches'),
        ('aethos', 2422.45, 12, 'veil', 'Vur Duri'),
        ('myrum', 2428.5, 4, 'war', 'Myrum'), ('haedus', 2428.62, 41, 'war', 'First Haedius'),
        ('ciriban', 2429.3, 6, 'war', 'Bijou Nan Syèl La and Bounty'), ('saolea', 2434.2, 28, 'war', 'Saolea'),
        ('saolea', 2436.7, 4, 'war', 'Theia'), ('veyer', 2437.5, 3, 'war', 'Hualapai'), ('nomotar', 2438.6, 9, 'war', 'Nomotar'),
        ('binami', 2440.28, 5, 'war', 'Binami'),
        ('talandra', 2441.35, 33, 'war', 'First Talandra'), ('procyon', 2441.87, 19, 'war', 'Procyon'),
        ('sirius', 2444.45, 4, 'war', 'Sirius'), ('yildun', 2444.93, 3, 'war', 'Dauntless'),
        ('sol', 2446.27, 40, 'war', 'Jupiter'), ('sol', 2446.9, 33, 'war', 'the Battle of Earth'),
        ('alpha-centauri', 2447.8, 18, 'war', 'Alpha Centauri'), ('procyon', 2448.2, 4, 'war', 'Procyon'),
        ('daranma', 2448.7, 3, 'war', 'Mardak Vol'), ('talandra', 2449.47, 43, 'war', 'Second Talandra'),
        ('bashpit', 2449.87, 3, 'war', 'Bashpit'), ('haedus', 2451.36, 5, 'war', 'Third Haedius'), ('exedor', 2451.73, 9, 'war', 'Exedor'),
        ('faenov', 2452.4, 3, 'war', 'Faenov'), ('hoeddim', 2452.7, 2, 'war', 'Hoeddim'), ('azak', 2453.1, 3, 'war', 'Azak'),
        ('aethos', 2453.79, 2, 'war', 'Second Aethos'), ('kuma', 2455.5, 3, 'war', 'the Long Siege'), ('omaggus', 2456.2, 4, 'war', 'Omaggus'),
        ('ijaagin', 2457.6, 3, 'war', 'the Long Siege'),
        ('churassix', 2454.3, 2, 'home', 'the freeholds'), ('barban', 2454.45, 2, 'home', 'the freeholds'), ('matar', 2454.45, 2, 'home', 'the freeholds'),
        ('daarasta', 2454.6, 3, 'home', 'the freeholds'), ('fevallion', 2454.85, 6, 'home', 'Fevallion'), ('mecura', 2454.95, 1, 'home', 'the freeholds'),
        ('japhon', 2455.05, 1, 'home', 'the freeholds'), ('maasym', 2455.05, 1, 'home', 'the freeholds'),
        (m6[1], 2455.4, 3, 'war', 'the marches'), (m6[3], 2455.8, 3, 'war', 'the marches'), (m6[4], 2456.0, 4, 'war', 'the marches'),
        ('hwen', 2456.2, 2, 'war', 'the Dwaii'), ('ellui', 2456.3, 2, 'war', 'the Dwaii'), ('dwaimar', 2456.4, 2, 'war', 'the Dwaii'),
        ('ossath', 2457.17, 5, 'war', 'Ossath'), ('kadris', 2457.5, 2, 'war', 'Kadris'), ('tamuur', 2457.8, 2, 'war', 'Tamuur'),
        ('far-south', 2458.79, 1, 'war', 'the last monolith outside the Veil'),
    ]
    far_south = min((s for s in systems if s.get('fill') and s['y'] < -95), key=lambda s: math.hypot(s['x'] + 75, s['y'] + 112))['id']
    EVENTS = [((far_south if e[0] == 'far-south' else e[0]),) + e[1:] for e in EVENTS]
    for k, v in list(fixed.items()):
        if v[0] == 'far-south': fixed[k] = (far_south,) + v[1:]
    # who is where: north monoliths stay home (18), go to the Maweer north (10) or join the war (12)
    north = [m for m in mons if m['north']]
    rng.shuffle(north)
    for i, m in enumerate(north):
        m['role'] = 'maweer-north' if i < 10 else 'home' if i < 28 else 'war'
    veil = [m for m in mons if not m['north']]
    rng.shuffle(veil)
    # 40 Veil monoliths fail and become hulks in the wells; 30 of them never left; 12 survive mobile
    for i, m in enumerate(veil):
        m['role'] = 'hulk-stay' if i < 30 else 'hulk-return' if i < 40 else 'mobile' if i < 52 else 'war'
    for m in byclan['drhen'] + byclan['dvesh'][:1] + byclan['dkasht'][:1] + byclan['dhovar']:
        m['role'] = 'war'
    # the successors' twelve: D'Tarik 6 into the Veil's far reaches, D'Ashan 2, D'Mareth 1, D'Sethen 1, the Word 1, the Veil Clans 1
    mob = [m for m in veil if m['role'] == 'mobile']
    want = [('dtarik', 6), ('dashan', 2), ('dmareth', 1), ('dsethen', 1)]
    for cid, k in want:
        for m in byclan[cid][:k]:
            if m['role'] != 'mobile':
                swap = next((x for x in mob if x['clan'] not in dict(want)), None)
                if swap: swap['role'] = 'war'; mob.remove(swap)
                m['role'] = 'mobile'; mob.append(m)
    for m in mons:
        m['depart'] = (2414.0 if m['role'] == 'maweer-north' else 2416.0 if m['north'] else round(rng.uniform(2405.0, 2413.0), 2)) if m['role'] not in ('home', 'hulk-stay') else None
    # assign deaths
    for m in mons:
        if id(m) in fixed:
            s, y, lbl = fixed[id(m)]; m['fate'] = {'y': y, 'sys': s, 'label': lbl}
    for s, y, n, poolk, lbl in EVENTS:
        n -= sum(1 for m in mons if m.get('fate') and m['fate']['sys'] == s and abs(m['fate']['y'] - y) < 0.01)
        if poolk == 'north': cand = [m for m in mons if m['role'] == 'maweer-north' and not m.get('fate')]
        elif poolk == 'home': cand = [m for m in mons if m['role'] == 'home' and not m.get('fate') and m['home'] == s]
        elif poolk == 'veil': cand = [m for m in mons if m['role'] == 'war' and not m['north'] and not m.get('fate') and m['depart'] < y]
        else: cand = [m for m in mons if m['role'] == 'war' and not m.get('fate') and (m['depart'] or 9999) < y]
        if poolk == 'home' and len(cand) < n:
            cand += [m for m in mons if m['role'] == 'home' and not m.get('fate') and m['home'] in north_homes]
        rng.shuffle(cand)
        for m in cand[:max(0, n)]:
            m['fate'] = {'y': y, 'sys': s, 'label': lbl}
    # whatever is left of the war's monoliths fell in the Scouring's smaller fights or joined the hulks
    for m in mons:
        if m['role'] == 'war' and not m.get('fate'):
            m['role'] = 'hulk-return'
        if m['role'] == 'home' and not m.get('fate'):
            m['fate'] = {'y': 2454.9, 'sys': m['home'], 'label': 'the freeholds'}
        if m['role'] in ('hulk-stay', 'hulk-return'):
            m['hulk'] = round(rng.uniform(2450.0, 2459.5), 1)
        if m['role'] in ('hulk-return', 'mobile'):
            m['back'] = round(rng.uniform(2449.6, 2451.0), 2)
    # where the mobile twelve end up
    succ = {'dtarik': far_south, 'dsethen': wm[1] if len(wm) > 1 else wm[0], 'dmareth': 'mareth-vel', 'dashan': 'ashan-dur'}
    for m in mons:
        if m['role'] == 'mobile':
            m['end'] = succ.get(m['clan'], m['home'])
    # ---------------------------------------------------------------- the war's anchorages take named clans
    def alive(m, a, b):
        if m['depart'] is None or m['depart'] > a: return False
        if m.get('fate') and m['fate']['y'] < b - 0.01 and m['fate']['sys'] != None: return m['fate']['y'] > a
        return True
    booked = {id(m): [] for m in mons}
    for sid, fs in FEATURES.items():
        for f in fs:
            if f['kind'] != 'fleet' or f['name'] in ('Monoliths', 'Freehold anchorage', 'Garrison monoliths') and sid in VEIL_IDS + north_homes: continue
            a, b = f['from'], f.get('to', 2510)
            if a < 2405: continue
            cand = [m for m in mons if m['role'] == 'war' and alive(m, a, b) and not any(x < b and a < y for x, y in booked[id(m)])]
            cand.sort(key=lambda m: (0 if m.get('fate') and m['fate']['sys'] == sid else 1, rng.random()))
            pick = cand[:min(f.get('n', 4), 60)]
            for m in pick:
                end = min(b, m['fate']['y']) if m.get('fate') else b
                booked[id(m)].append((a, end)); m.setdefault('segs', []).append([a, end, sid])
            f['clans'] = sorted({m['clan'] for m in pick})
    # ---------------------------------------------------------------- features
    clan_by = {c['id']: c for c in clans}
    for c in clans:
        ms = byclan.get(c['id'], [])
        # the clan's hulks and stations, which never leave home (the freeholds' are taken in the Scouring)
        base = {'name': c['name'], 'kind': 'clanbase', 'at': 'pillai', 'from': 1300, 'clan': c['id'], 'n': 3 + (2 if c['m'] == 0 else 0) + min(c['m'], 3)}
        if c['north']: base['to'] = 2454.9
        FEATURES.setdefault(c['home'], []).append(base)
    for c in clans:
        ms = byclan.get(c['id'], [])
        def at_home(m, t, c=c):
            if m.get('fate') and m['fate']['y'] <= t: return False
            if m['depart'] is None: return True
            if t < m['depart']: return True
            return bool(m.get('back') and t >= m['back'] and m.get('end', c['home']) == c['home'])
        marks = sorted({1300, 2511} | {m['depart'] for m in ms if m['depart']} | {m['fate']['y'] for m in ms if m.get('fate')}
                       | {m['back'] for m in ms if m.get('back')} | {m['hulk'] for m in ms if m.get('hulk')})
        for a, b in zip(marks, marks[1:]):
            t = (a + b) / 2
            here = [m for m in ms if at_home(m, t)]
            hulks = sum(1 for m in here if m.get('hulk') and m['hulk'] <= a)
            live = len(here) - hulks
            if live: FEATURES[c['home']].append({'name': c['name'], 'kind': 'clanfleet', 'at': 'pillai', 'from': a, 'to': b, 'n': live, 'clan': c['id']})
            if hulks: FEATURES[c['home']].append({'name': c['name'], 'kind': 'clanhulk', 'at': 'pillai', 'from': a, 'to': b, 'n': hulks, 'clan': c['id']})
        # mobile monoliths that settle away from home
        for m in ms:
            if m['role'] == 'mobile' and m.get('end') and m['end'] != c['home']:
                FEATURES.setdefault(m['end'], []).append({'name': c['name'], 'kind': 'clanfleet', 'at': 'pillai', 'from': m['back'], 'n': 1, 'clan': c['id']})
    # the battles where monoliths fell, each with the clans that lost them
    seen = {}
    for m in mons:
        f = m.get('fate')
        if not f or f['sys'] == m['home']: continue
        seen.setdefault((f['sys'], f['y'], f['label']), []).append(m)
    for (s, y, lbl), ms in seen.items():
        FEATURES.setdefault(s, []).append({'name': 'Monoliths at ' + lbl, 'kind': 'fleet', 'at': 'pillai', 'from': round(y - 0.08, 3), 'to': y,
                                           'n': len(ms), 'clans': sorted({m['clan'] for m in ms})})
    # ---------------------------------------------------------------- the roll for the panel and the article
    out = []
    for c in clans:
        ms = byclan.get(c['id'], [])
        out.append({'id': c['id'], 'name': c['name'], 'home': c['home'], 'inv': c['inv'],
                    **({'gone': 2454.9} if c['north'] else {}),
                    'mon': [{k: v for k, v in {'name': m.get('name'), 'depart': m['depart'], 'fate': m.get('fate'), 'hulk': m.get('hulk'),
                                                'back': m.get('back'), 'end': m.get('end')}.items() if v is not None} for m in ms]})
    return out
