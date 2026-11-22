import os
"""Build atlas-data.json: 194 systems traced from the 2235.12.10 reference map,
their ownership through time, settled worlds and dated events.

Positions: the map is 7000 px wide at 35 px per light year. Sol is the origin.
Heights above the plane are invented and kept small (seeded, so stable).
Ownership is reconstructed from the Expanded Edition. Anything the book does not
fix (claim years of minor systems, which Voor and Thaali systems the Khanate held)
is derived by rule and flagged with "derived": true.
"""
import json, math, random, re
from pathlib import Path

HERE = Path(__file__).parent
RAW = json.load(open(HERE / 'trace' / 'systems_named.json'))
PX_PER_LY = 35.0

def slug(t):
    t = t.lower().replace("'", '')
    return re.sub(r'[^a-z0-9]+', '-', t).strip('-')

def ym(y, m=6, d=15):
    return round(y + (m - 1) / 12 + (d - 1) / 365, 3)

# ------------------------------------------------------------------ polities
POLITIES = {
    'earth':    {'name': 'Earth', 'color': '#5B9BE0'},
    'une':      {'name': 'United Nations of Earth', 'color': '#5B9BE0', 'slug': 'united-nations-of-earth'},
    'usr':      {'name': 'Unified Solar Republic', 'color': '#5B9BE0', 'slug': 'unified-solar-republic'},
    'voor':     {'name': 'Voor Confederacy', 'color': '#3FB3A6', 'slug': 'voor-confederacy'},
    'voorsix':  {'name': 'Voor worlds', 'color': '#3FB3A6', 'slug': 'early-history-of-the-voor'},
    'maweer':   {'name': 'Long Garden', 'color': '#62BF6E', 'slug': 'thaali'},
    'freehold': {'name': 'Northern Fevarian Freeholds', 'color': '#A57BD6', 'slug': 'northern-fevarian-freeholds'},
    'fevclans': {'name': 'Southern Fevarian Freeholds', 'color': '#8E5E78', 'slug': 'southern-fevarian-freeholds'},
    'khanate':  {'name': 'Red Khanate', 'color': '#D2493E', 'slug': 'red-khanate'},
    'eight':    {'name': 'Council of the Eight Khans', 'color': '#E2733C', 'slug': 'council-of-the-eight-khans'},
    'remnant':  {'name': 'Khanate remnants', 'color': '#A44F48', 'slug': 'khanate-remnants'},
    'word':     {'name': 'Khanate of the Word', 'color': '#B24C8F', 'slug': 'khanate-of-the-word'},
    'dashan':   {'name': 'Khanate of D\'Ashan', 'color': '#B93838', 'slug': 'khanate-of-dashan'},
    'veilclans': {'name': 'The Veil Clans', 'color': '#9A6650', 'slug': 'the-veil-clans'},
    'dtarik':   {'name': 'Khanate of D\'Tarik', 'color': '#D9667A', 'slug': 'khanate-of-dtarik'},
    'dsethen':  {'name': 'Khanate of D\'Sethen', 'color': '#C9643C', 'slug': 'khanate-of-dsethen'},
    'dhovar':   {'name': 'Khanate of D\'Hovar', 'color': '#D19A4A', 'slug': 'khanate-of-dhovar'},
    'dmareth':  {'name': 'Khanate of D\'Mareth', 'color': '#5D6B76', 'slug': 'khanate-of-dmareth'},
    'dwaii':    {'name': 'Dwaii', 'color': '#E2C65C', 'slug': 'dwaii'},
    'kadur':    {'name': 'Ka-Dur League', 'color': '#E58CC2', 'slug': 'ka-dur'},
    'ossathi':  {'name': 'Ossathi', 'color': '#7FCF9A', 'slug': 'ossathi'},
    'veren':    {'name': 'Veren', 'color': '#D8B46A', 'slug': 'veren'},
    'kaltam':   {'name': 'Kal-Tam', 'color': '#C9825A', 'slug': 'kal-tam'},
    'duresh':   {'name': 'Dur-Esh', 'color': '#5FB8C8', 'slug': 'dur-esh'},
    'raidzone': {'name': 'Fevarian raiding grounds', 'color': '#7A4E66', 'slug': 'fevarian-clans'},
}

def human_polity(y):
    if y < 2283.42:
        return 'earth'
    if y < 2341:
        return 'une'
    return 'usr'

# ------------------------------------------------------------------ systems
sol = next(s for s in RAW if s['name'] == 'Sol')
rng = random.Random(2235)
systems = []
for s in RAW:
    x = (s['x'] - sol['x']) / PX_PER_LY
    y = (s['y'] - sol['y']) / PX_PER_LY
    z = 0.0 if s['name'] == 'Sol' else round(rng.uniform(-3.5, 3.5), 2)
    systems.append({
        # The Thaali home system keeps its old internal id after the rename of 22 November 2026.
        'id': 'maweer' if s['name'] == 'Thaali' else slug(s['name']), 'name': s['name'],
        'x': round(x, 2), 'y': round(-y, 2), 'z': z,   # map y grows downward; flip so north is +y
        'stars': max(1, min(3, len(s['pts']))),
        'region2235': s['region2235'],
    })
by = {s['id']: s for s in systems}

# ------------------------------------------------------------------ beyond the 2235 map
# The Veil (the Fevarians' own space), the Dwaii and the Ka-Dur lie south and south-west
# of the reference map. The book fixes only their relations: the Veil south of the
# Confederacy, its western edge on the Thaali's marches; the Dwaii and Ka-Dur on the
# Veil's far side, 60 to 100 ly from Haedius, the Dwaii reached first by the marches'
# far road and the Ka-Dur furthest (the book's distances changed to 60 to 100 ly to fit). Positions and every name but Ossath are invented.
EXTRA = {
    'veil': [('Dhen Ossa', -74, -80), ('Rhen Tal', -66, -86), ('Vesh Mar', -80, -72), ('Kasht', -60, -77),
             ('Tor Dhaan', -86, -84), ('Ashan Dur', -71, -92), ('Mareth Vel', -56, -88), ('Ul Sethen', -92, -76),
             ('Vharr', -63, -95), ('Drek Hul', -78, -97), ('Thul Ashra', -89, -91), ('Ossek', -54, -70),
             ('Varn Khet', -68, -70), ('Sel Tarik', -84, -101), ('Ushar\'s Well', -76, -66), ('Dhenmar', -62, -64)],
    'dwaii': [('Hwen', -106, -72), ('Ellui', -111, -78), ('Dwaimar', -103, -79)],
    # The Ka-Dur League lies west of the Dwaii, south of the Nythran Void. Ossath stands where
    # the map once had "Sethen's March". The Ka-Dur reach the Thaali by going round the
    # void's western edge, Dothom to Ellamir.
    'kadur': [('Ossath', -112, -58), ('Kadris', -117, -64), ('Tamuur', -123, -62),
              ('Dhur Ka', -129, -62), ('Sarrek', -120, -70), ('Imbal', -127, -69)],
    # The Rubin Void, east of the Republic, named for the astronomer Vera Rubin. Low density.
    'rubin': [('Kessavar', 22, 31), ('Oru Tenna', 31, 18), ('Halvek', 30, 3), ('Imrith', 16, -5),
              ('Selund', 36, -14), ('Aqqar', 34, -24), ('Morrow\'s Light', 41, 9), ('Teshun', 11, -18),
              ('Vane', 18, -25)],
    # The Mardak Cluster, on the far side of the Rubin Void: the ancients' eleven ruined worlds
    # and the star the Gagarin's road comes in by. Names are the Office's charts'.
    'mardak': [('Ithren', 50, 14), ('Varrow', 57, 18), ("Calder's Reach", 63, 10), ('Ommen', 52, 4),
               ('Teluvar', 60, 1), ('Saskel', 66, -5), ('Nadir', 49, -6), ('Halloran', 56, -10),
               ('Wend', 63, -17), ('Isolde', 51, -19), ('Peregrine', 58, -24), ('Lastlight', 66, -26)],
    # The four far peoples beyond the Ka-Dur, met by the Repatriation Authority in the 2460s
    # (book 15.x): the Ossathi, the Veren, the Kal-Tam and the Dur-Esh. Star names invented.
    # Lewis's placement (18 November 2026): three south of the Dwaii, Dur Eshen east by Mareth Vel.
    'far': [('Ossa Theran', -109, -103), ('Verentis', -100, -109), ('Kal Tamar', -112, -112), ('Dur Eshen', -47, -97)],
}
for region, lst in EXTRA.items():
    if region == 'rubin':
        rng.random(); rng.random()    # the retired Sethen's March's draws, so later stars keep their depth
    for name, x, y in lst:
        s = {'id': slug(name), 'name': name, 'x': float(x), 'y': float(y), 'z': round(rng.uniform(-3.5, 3.5), 2),
             'stars': 1 + (1 if rng.random() < 0.2 else 0), 'region2235': 'none' if region == 'far' else region, 'invented': True}
        systems.append(s); by[s['id']] = s

# Filler stars (Lewis, 18 November 2026): named and mostly unclaimed, in the southern band below the
# Ka-Dur, the Dwaii and the Veil, east of Ushar's Well, along the Nythran Void's western edge, and in
# the Veil's empty patches (those join the Veil). Drawn from their own generator so the stars above
# keep their depths. All names invented.
frng = random.Random(9071)
FILL_SYL = {
    'south': (['Ae', 'Bri', 'Cael', 'Dun', 'Esk', 'Fal', 'Gor', 'Hal', 'Ith', 'Kel', 'Lum', 'Mor', 'Nis', 'Orr', 'Pel', 'Ruv', 'Syl', 'Tav', 'Ur', 'Vey', 'Wyn', 'Yss'],
              ['ane', 'eth', 'ion', 'ara', 'ok', 'is', 'enn', 'avar', 'ul', 'ira', 'osk', 'eda']),
    'veil': (['Vesh', 'Dhar', 'Kol', 'Ash', 'Mar', 'Thul', 'Rhen', 'Kesh', 'Drath', 'Ul', 'Var', 'Hask', 'Zhar', 'Tor', 'Orr', 'Sev'],
             ['Tal', 'Khet', 'Dur', 'Vel', 'Mar', 'Ossa', 'Hul', 'Ash', 'Dhaan', 'Rek', 'Thar', 'Mol']),
    'east': (['Tey', 'Fol', 'Um', 'Ban', 'Ija', 'Kum', 'Nith', 'Bet', 'Ceye', 'Om', 'Vor', 'Ak'],
             ['tera', 'ingar', 'ik', 'agho', 'agin', 'asca', 'arro', 'aggus', 'eth', 'ul', 'ani']),
    'nythran': (['Dho', 'Ka', 'Sar', 'Im', 'Kod', 'Ell', 'Gal', 'Bral', 'Pon', 'Thom', 'Ur'],
                ['thom', 'rek', 'bal', 'uus', 'ith', 'ok', 'el', 'amir', 'urum', 'ix', 'ell']),
}
FILL_AREAS = [   # (style, x0, x1, y0, y1, count, region, keep out of the void)
    ('south', -165, -15, -128, -100, 18, 'none'),
    ('east', -48, -5, -92, -52, 9, 'none'),
    ('nythran', -168, -140, -56, -22, 7, 'none'),
    ('veil', -96, -50, -104, -60, 6, 'veil'),
]
VOID = (-115.0, -38.0, 15.0)
names_taken = {s['name'] for s in systems}
FILLED = []
for style, x0, x1, y0, y1, n, region in FILL_AREAS:
    pre, suf = FILL_SYL[style]
    got = 0
    for attempt in range(4000):
        if got >= n: break
        x, y = frng.uniform(x0, x1), frng.uniform(y0, y1)
        if math.hypot(x - VOID[0], y - VOID[1]) < VOID[2]: continue
        gap = 7.0 if region == 'veil' else 5.5
        if min(math.hypot(o['x'] - x, o['y'] - y) for o in systems) < gap: continue
        if style in ('veil',):
            nm = frng.choice(pre) + ' ' + frng.choice(suf)
        else:
            nm = frng.choice(pre) + frng.choice(suf)
        nm = {'Aeeth': 'Aeline', 'Ceyearro': 'Ceyarro', 'Dhoith': 'Dhorith'}.get(nm, nm)
        if nm in names_taken or slug(nm) in by: continue
        names_taken.add(nm)
        s = {'id': slug(nm), 'name': nm, 'x': round(x, 1), 'y': round(y, 1), 'z': round(frng.uniform(-3.5, 3.5), 2),
             'stars': 1 + (1 if frng.random() < 0.2 else 0), 'region2235': region, 'invented': True, 'fill': True}
        systems.append(s); by[s['id']] = s; FILLED.append(s); got += 1
        if region == 'veil': EXTRA['veil'].append((nm, s['x'], s['y']))

# ------------------------------------------------------------------ Lewis's colony sheet
# atlas/trace/colonies.tsv: sectors, claim years and the settled worlds. The book is canon;
# the sheet fills what the book leaves out. Its system-only rows use the old timeline
# (22xx), a century earlier, and are shifted forward.
import csv
SHEET_ALIAS = {'Derelis': 'derellis', 'Taggallion': 'taggalion', 'Bashpat': 'bashpit', 'Lytirin': 'lytirim',
               'Wanambis': 'wanambus', 'Tuiz': 'tiuz', 'Figzar/Gagarin': 'figzar', 'Acramalo': 'acramato',
               "Barnard's Star": 'barnards-star'}
def sheet_id(name):
    return SHEET_ALIAS.get(name, slug(name))
sheet = list(csv.reader(open(HERE / 'trace' / 'colonies.tsv'), delimiter='\t'))[1:]
SHEET_SECTOR, SHEET_CLAIM, SHEET_SYSNAME = {}, {}, {}
for r in sheet:
    sec, sysname, claim = r[1].replace('Gagarin Section', 'Gagarin Sector'), r[3].strip(), r[4].strip()
    if not sysname: continue
    sid = sheet_id(sysname)
    SHEET_SYSNAME[sid] = sysname.split('/')[0]
    SHEET_SECTOR.setdefault(sid, sec)
    if sid != 'sol' and claim.isdigit():
        y = int(claim)
        if 2150 < y < 2300: y += 100
        SHEET_CLAIM[sid] = min(SHEET_CLAIM.get(sid, 9999), y)
# Book canon over the sheet: Ladiom and Swur stay Voor; Derellis sits in the Geronth Sector.
for sid in ('ladiom', 'swur'):
    SHEET_SECTOR.pop(sid, None); SHEET_CLAIM.pop(sid, None)
SHEET_SECTOR['derellis'] = 'Geronth Sector'
SHEET_SECTOR['brink'] = 'Sol Sector'      # so the sectors do not overlap
SHEET_SECTOR['hadriccus'] = 'Gagarin Sector'
SHEET_SECTOR['zarqon'] = 'Geronth Sector'
SHEET_SECTOR['trab'] = 'Binami Sector'
SHEET_SECTOR['esmyke'] = 'Saolea Sector'
SHEET_SECTOR['golba'] = 'Saolea Sector'
SHEET_SECTOR['talandra'] = 'Binami Sector'   # book 8.3: the Binami sector runs through Talandra

# Systems on the sheet but not on the 2235 map get invented positions inside their sector,
# at the emptiest spot among its other members.
placed = []
for sid, sec in SHEET_SECTOR.items():
    if sid in by: continue
    mem = [by[m] for m, s in SHEET_SECTOR.items() if s == sec and m in by]
    xs, ys = [m['x'] for m in mem], [m['y'] for m in mem]
    best, bscore = None, -1
    prng = random.Random(sid)                                   # stable per system
    rubin = [s for s in systems if s['region2235'] == 'rubin']
    for _ in range(4000):
        x, y = prng.uniform(min(xs) - 3, max(xs) + 3), prng.uniform(min(ys) - 3, max(ys) + 3)
        dmem = min(math.hypot(x - m['x'], y - m['y']) for m in mem)
        if dmem > 7: continue                                   # stay near the sector
        if any(math.hypot(x - r['x'], y - r['y']) < 10 for r in rubin): continue   # not in the void
        score = min(math.hypot(x - s['x'], y - s['y']) for s in systems)
        if score > bscore: best, bscore = (x, y), score
    s = {'id': sid, 'name': SHEET_SYSNAME[sid], 'x': round(best[0], 2), 'y': round(best[1], 2),
         'z': round(prng.uniform(-3.5, 3.5), 2), 'stars': 1, 'region2235': 'usr', 'invented': True, 'sheet': True}
    systems.append(s); by[sid] = s; placed.append(sid)
# Lewis's moves: Cygni sits between Ijax and Bashpit.
MOVED = {'cygni': (-30.7, -10.4, -2.5), 'daranma': (17.5, 6.5, None)}   # Daranma sits at the Rubin Void's edge
for sid, (x, y, z) in MOVED.items():
    by[sid].update(x=x, y=y, z=by[sid]['z'] if z is None else z)
import heights as HT
HT.apply(systems)   # heights above the plane: real stars' galactic latitudes, the rest smoothed between them
# catalogue names from the sheet's designations (Teegarden for Targon and so on)
CATALOGUE = {}
for r in sheet:
    if r[2] and r[8] and r[3]:
        cat = re.sub(r'\s*\d+[a-z]?(/.*)?$', '', r[8]).strip()
        sid = sheet_id(r[3])
        if cat and not cat.lower().startswith(r[3].lower()) and cat not in ('Ciriban',): CATALOGUE[sid] = cat
for sid, cat in CATALOGUE.items():
    if sid in by: by[sid]['catalogue'] = cat

# corrections from the book's canon to the map's colour sampling
FREEHOLDS = ['churassix', 'barban', 'matar', 'fevallion', 'daarasta', 'mecura', 'japhon', 'maasym']
for f in FREEHOLDS:
    by[f]['region2235'] = 'fevarian'
for k, v in {'zosma': 'maweer', 'furud': 'usr', 'barnards-star': 'usr'}.items():
    by[k]['region2235'] = v
# The Thaali reach west across the Nythran Void's northern rim to Ellamir and Saonus.
WEST_M = ['ellamir', 'guhur', 'osellus', 'hocry', 'kastra', 'saonus', 'howoz', 'polaris', 'rovannic',
          'tethell', 'duhr', 'fir-mathrioz', 'halax', 'eriga', 'kazoo']
for k in WEST_M:
    by[k]['region2235'] = 'maweer'

def dist(a, b):
    return math.dist((a['x'], a['y'], a['z']), (b['x'], b['y'], b['z']))

# ------------------------------------------------------------------ ownership
own = {s['id']: [] for s in systems}   # list of [from, polity, note]

def set_owner(sid, year, polity, note=None, derived=False, vs=None):
    e = {'from': year, 'p': polity}
    if note: e['note'] = note
    if vs: e['vs'] = vs
    if derived: e['derived'] = True
    own[sid].append(e)

# Human claims. Explicit dates from Part Seven and Eight.
# Claim years the book states; the sheet supplies the rest.
BOOK_CLAIMS = {
    'sol': 1900, 'procyon': ym(2302, 3, 3), 'torovil': 2302, 'barnards-star': 2303, 'talandra': 2308,
    'yildun': 2307, 'sirius': 2312, 'daranma': 2313, 'saolea': 2316, 'ciriban': 2317, 'nomotar': 2317,
    'derellis': 2331,
}
CLAIMS = dict(SHEET_CLAIM); CLAIMS.update(BOOK_CLAIMS)
human_sys = [s for s in systems if s['region2235'] == 'usr' or (s['id'] in CLAIMS and s['region2235'] == 'none')]
dmax = max(dist(s, by['sol']) for s in human_sys)
for s in human_sys:
    if s['id'] in CLAIMS:
        y = CLAIMS[s['id']]; der = False
    else:
        y = round(2300 + 31 * dist(s, by['sol']) / dmax); der = True
    set_owner(s['id'], y, 'human', derived=der)

# The other powers hold their 2333 regions from before the map's range.
for s in systems:
    r = s['region2235']
    if r == 'voor': set_owner(s['id'], 1900, 'voor')
    elif r == 'maweer': set_owner(s['id'], 1900, 'maweer')
    elif r == 'fevarian': set_owner(s['id'], 1900, 'freehold')

# The Ciriban Gulf War (Part Nine)
for sid, y in [('myrum', ym(2333, 9, 12)), ('kastaba', ym(2335, 2, 3)), ('swur', ym(2335, 4, 20)),
               ('achernar', ym(2333, 12)), ('haedus', ym(2334, 9, 12)), ('leesak', ym(2337, 6, 24)), ('ximpok', ym(2339, 8, 17)),
               ('exedor', ym(2338, 5, 3))]:
    set_owner(sid, y, 'human', 'occupied')
for sid in ['swur', 'achernar', 'leesak', 'exedor', 'ximpok']:
    set_owner(sid, 2341.0, 'voor')
for sid in ['myrum', 'kastaba', 'haedus']:
    set_owner(sid, 2341.0, 'human', 'Voor territory')

# The Red Khanate (unified 2405). The northern freeholds join it at unification and
# the Khanate expands from two fronts: up from the Veil in the south and down from the
# freeholds in the north. The Confederacy falls between 2415 and 2427.
for f in FREEHOLDS:
    set_owner(f, 2405.0, 'khanate', 'northern clans')
fx = sum(by[f]['x'] for f in FREEHOLDS) / len(FREEHOLDS)
fy = sum(by[f]['y'] for f in FREEHOLDS) / len(FREEHOLDS)
voor_now = [s for s in systems if s['region2235'] == 'voor' and s['id'] not in ('myrum', 'kastaba', 'haedus')]
south_edge = min(s['y'] for s in voor_now)
def front(s):
    dn = math.hypot(s['x'] - fx, s['y'] - fy)       # from the freeholds
    ds = s['y'] - south_edge                          # from the Veil
    return ('north', dn) if dn < ds else ('south', ds)
VOOR_FIXED = {'aethos': ym(2422, 6, 14), 'exedor': ym(2427, 8, 16), 'ximpok': ym(2424, 6),
              'romston': ym(2417, 5), 'cazzabius': ym(2419, 9), 'wicklar': ym(2420, 3)}
north_v = sorted([s for s in voor_now if front(s)[0] == 'north'], key=lambda s: front(s)[1])
south_v = sorted([s for s in voor_now if front(s)[0] == 'south'], key=lambda s: front(s)[1])
south = south_v   # D'Hovar's far southern worlds are taken from this list
for lst, y0 in ((south_v, 2415.0), (north_v, 2416.0)):
    for i, s in enumerate(lst):
        y = VOOR_FIXED.get(s['id'], round(y0 + 11 * i / max(1, len(lst) - 1), 1))
        set_owner(s['id'], y, 'khanate', derived=s['id'] not in VOOR_FIXED)
dhovar = [s['id'] for s in south_v[:3]]
# The Thaali campaign, 2413 to 2417: the eleven marches on the Veil's approaches, and the
# northern Thaali systems nearest the freeholds. The Thaali retake them 2447 to 2449.
# The Khan came at them on two fronts: up from the Veil, and from the Ka-Dur round the
# Nythran Void by Dothom to Ellamir. Six marches on the Veil's side and five in the west make
# the book's eleven. The Thaali retake the southern six 2447 to 2449; the western five are
# still the Khan's when he dies and become the Khanate of D'Sethen.
maweer = [s for s in systems if s['region2235'] == 'maweer']
core = ('maweer', 'fejantris')
marches = sorted([m for m in maweer if m['id'] not in core and m['id'] not in WEST_M], key=lambda s: s['y'])[:6]
west_marches = [by[k] for k in ('ellamir', 'guhur', 'osellus', 'hocry', 'kastra')]
north_m = [m for m in maweer if m['id'] not in core and m not in marches and m['id'] not in WEST_M
           and math.hypot(m['x'] - fx, m['y'] - fy) < 30]
north_m.sort(key=lambda m: math.hypot(m['x'] - fx, m['y'] - fy))
# The front moves march by march (Lewis, 18 November 2026): each march is besieged before it falls (shown as
# contested), the Thaali retake them one by one from March 2447, and the Khanate's counterattacks take some back.
# (system order in each list: nearest the Veil or the freeholds first)
def front(sid, siege, fall, note):
    set_owner(sid, siege, 'maweer', 'besieged', derived=True, vs='khanate')
    set_owner(sid, fall, 'khanate', note, derived=True)
def retake(sid, attack, back, vs='khanate'):
    set_owner(sid, attack, vs, 'contested', derived=True, vs='maweer')
    set_owner(sid, back, 'maweer', derived=True)
SOUTH_FALL = [(2413.25, 2413.6), (2413.4, 2414.3), (2413.8, 2414.8), (2414.5, 2415.9), (2415.2, 2416.6), (2416.1, 2417.0)]
NORTH_FALL = [(2414.25, 2414.6), (2414.3, 2414.9), (2414.6, 2415.3), (2415.0, 2415.8), (2415.5, 2416.1), (2415.9, 2416.5), (2416.3, 2416.9)]
WEST_FALL = [(2413.3, 2413.7), (2413.6, 2414.3), (2414.1, 2414.9), (2414.7, 2415.6), (2415.4, 2416.3)]
for (sg, fl), s_ in zip(SOUTH_FALL, marches): front(s_['id'], sg, fl, 'the marches')
for (sg, fl), s_ in zip(NORTH_FALL, north_m): front(s_['id'], sg, fl, 'northern conquest')
for (sg, fl), s_ in zip(WEST_FALL, west_marches): front(s_['id'], sg, fl, 'the western marches')
# the Thaali offensive, 2447 to 2449: the southern six from the far end inward, two lost again to counterattacks
SOUTH_BACK = {5: (2447.17, 2447.5), 4: (2447.4, 2447.8), 3: (2447.7, 2448.1), 2: (2448.0, 2448.4), 1: (2448.3, 2448.7), 0: (2448.8, 2449.2)}
for i, (a, b) in SOUTH_BACK.items(): retake(marches[i]['id'], a, b)
for i, (lost, again, back) in {4: (2447.95, 2448.15, 2448.9), 2: (2448.55, 2448.7, 2449.3)}.items():
    set_owner(marches[i]['id'], lost, 'maweer', 'besieged', derived=True, vs='khanate')
    set_owner(marches[i]['id'], again, 'khanate', 'retaken by the Khanate', derived=True)
    retake(marches[i]['id'], again + 0.4, back)
# the north: five of seven retaken 2447 to 2449, the last two given up by the Word in July 2449
NORTH_BACK = [(2448.6, 2449.0), (2448.2, 2448.6), (2447.9, 2448.3), (2447.5, 2447.9), (2447.3, 2447.7)]
for (a, b), s_ in zip(NORTH_BACK, north_m[:5]): retake(s_['id'], a, b)
for s_ in north_m[5:]:
    set_owner(s_['id'], 2448.8, 'khanate', 'contested', derived=True, vs='maweer')
    set_owner(s_['id'], ym(2449, 7, 15), 'maweer', derived=True)
WEST_MARCH_IDS = {s['id'] for s in west_marches}

# Part Twelve and Thirteen: the Khan in human space.
KHAN_TAKES = [
    ('myrum', ym(2428, 7, 9)), ('haedus', ym(2428, 9, 5)), ('kastaba', ym(2428, 9)),
    ('ciriban', ym(2429, 1, 20)), ('media', ym(2430, 8)), ('uthan', ym(2430, 10)), ('hhabban', ym(2430, 10)),
    ('bashpit', ym(2430, 12)), ('izar', ym(2431, 4)), ('taggalion', ym(2432, 6)), ('trab', ym(2432, 9)),
    ('ijax', ym(2433, 6)), ('saolea', ym(2436, 9, 12)), ('stiridon', ym(2436, 12)), ('ajam', ym(2436, 12)),
    ('veyer', ym(2437, 3)), ('golba', ym(2437, 6)), ('esmyke', ym(2437, 6)), ('feonus', ym(2437, 6)),
    ('nomotar', ym(2438, 8, 20)), ('binami', ym(2440, 4, 14)), ('talandra', ym(2441, 5, 6)),
    ('procyon', ym(2441, 11, 19)), ('alpha-centauri', ym(2442, 4, 20)), ('yildun', ym(2444, 6)),
    ('brink', ym(2444, 10)),
]
SUBMITTED = {'uthan', 'hhabban', 'trab', 'golba', 'esmyke', 'feonus', 'alpha-centauri', 'brink'}
for sid, y in KHAN_TAKES:
    set_owner(sid, y, 'khanate', 'tributary' if sid in SUBMITTED else None)

RETAKES = [
    ('alpha-centauri', ym(2447, 10, 21)), ('yildun', ym(2448, 1)), ('brink', ym(2448, 1)),
    ('procyon', ym(2448, 5, 14)), ('talandra', ym(2449, 6, 20)), ('nomotar', ym(2449, 8, 12)),
    ('bashpit', ym(2449, 11)), ('izar', ym(2449, 12)), ('ijax', ym(2449, 12)), ('binami', ym(2450, 1, 20)),
    ('ciriban', ym(2450, 5, 16)), ('saolea', ym(2450, 6, 22)), ('stiridon', ym(2450, 10)),
    ('ajam', ym(2450, 10)), ('trab', ym(2450, 10)), ('taggalion', ym(2450, 11)), ('veyer', ym(2450, 12)),
    ('golba', ym(2451, 1)), ('esmyke', ym(2451, 1)), ('feonus', ym(2451, 2)), ('media', ym(2451, 2)),
    ('uthan', ym(2451, 3)), ('hhabban', ym(2451, 4)), ('haedus', ym(2451, 5, 12)),
    ('kastaba', ym(2451, 6)), ('myrum', ym(2451, 7)),
]
for sid, y in RETAKES:
    set_owner(sid, y, 'human')

# The Voor worlds, 2451 to 2460: a grind, world by world. Hiverion's orbitals hold for
# fourteen months after the Battle of Exedor and the Confederacy is restored on 1 January
# 2453. D'Ashan comes out of the Veil in August 2453 and retakes Aethos, Ksora and
# Banagho; D'Hovar strikes in February 2456 and retakes Omaggus. The main fleet goes north
# in 2454 and west in 2455, and the Southern Command and the Legion fight on alone. Kuma
# and Ijaagin are still under siege when the conference opens, and the Peace returns them.
VOOR_BACK = {
    'ladiom': ym(2451, 8), 'ximpok': ym(2451, 12, 4), 'leesak': ym(2451, 12), 'aethos': ym(2452, 1, 20),
    'swur': ym(2452, 2), 'faenov': ym(2452, 5), 'hoeddim': ym(2452, 8), 'batraq': ym(2452, 11),
    'exedor': ym(2452, 11, 30), 'azak': ym(2452, 10), 'ksora': ym(2452, 12), 'roschon': ym(2453, 1),
    'banagho': ym(2453, 3), 'achernar': ym(2455, 11), 'omaggus': ym(2455, 7), 'ceyecarro': ym(2456, 9),
    'nithascal': ym(2456, 12), 'umik': ym(2457, 3), 'beta-aquilae': ym(2457, 7),
    'kuma': ym(2460, 4), 'ijaagin': ym(2460, 4),
}
COUNTER = [   # (system, date, holder, retaken)
    ('aethos', ym(2453, 8, 9), 'dashan', ym(2453, 10, 18)),
    ('ksora', ym(2453, 8, 20), 'dashan', ym(2455, 9)),
    ('banagho', ym(2453, 9), 'dashan', ym(2456, 6)),
    ('omaggus', ym(2456, 2, 11), 'dhovar', ym(2457, 9)),
]
for s in south_v + north_v:
    sid = s['id']
    if sid in dhovar:
        set_owner(sid, 2449.47, 'dhovar', derived=True)
    elif sid in ('kuma', 'ijaagin'):
        set_owner(sid, ym(2453, 6), 'dhovar', 'under siege from 2458', derived=True)
        set_owner(sid, VOOR_BACK[sid], 'voor', 'returned by the Fejantris Peace')
    elif sid in VOOR_BACK:
        set_owner(sid, VOOR_BACK[sid], 'voor')
    else:                                   # the north, given up by the Word, reoccupied by the Legion
        set_owner(sid, ym(2453, 4), 'voor', derived=True)
for sid, y, p, back in COUNTER:
    set_owner(sid, y, p, 'counterattack from the Veil')
    set_owner(sid, back, 'voor')

# The northern freeholds: destroyed 2454, then the Republic's occupation zone.
FREEHOLD_END = {'churassix': ym(2454, 4), 'barban': ym(2454, 6), 'matar': ym(2454, 6),
                'daarasta': ym(2454, 8), 'fevallion': ym(2454, 11, 14), 'mecura': ym(2454, 12),
                'japhon': ym(2455, 1), 'maasym': ym(2455, 1)}
for sid, y in FREEHOLD_END.items():
    set_owner(sid, y, 'human', 'occupation zone')
    set_owner(sid, 2468.0, 'human', derived=True)

# The Veil, the Dwaii and the Ka-Dur
for name, *_ in EXTRA['veil']:
    set_owner(slug(name), 1900, 'fevclans')
    set_owner(slug(name), 2405.0, 'khanate')
for i, (name, *_) in enumerate(EXTRA['dwaii']):
    set_owner(slug(name), 1900, 'dwaii')
    set_owner(slug(name), round(2407.5 + i * 0.6, 1), 'khanate', 'tributary', derived=True)
    set_owner(slug(name), ym(2456, 4) + i * 0.1, 'dwaii')
for i, (name, *_) in enumerate(EXTRA['kadur']):
    set_owner(slug(name), 1900, 'kadur')
    set_owner(slug(name), round(2410.3 + i * 0.5, 1), 'khanate', 'tributary', derived=True)
KADUR_FREED = {'ossath': ym(2457, 3, 4), 'kadris': ym(2457, 7), 'tamuur': ym(2457, 10)}
# The four far peoples (Lewis, 18 November 2026): the clans' raiding grounds for centuries, the Red Khan's first and
# easiest conquest straight after the Assembly of the Veil, and subject worlds of the khanates ever after.
FAR_TAKEN = {'dur-eshen': 2405.6, 'kal-tamar': 2406.2, 'verentis': 2406.6, 'ossa-theran': 2407.0}
for sid, y in FAR_TAKEN.items():
    set_owner(sid, 1900, 'raidzone', 'raided by the clans')
    set_owner(sid, y, 'khanate', 'tributary')

# The sheet's new systems share the wartime fate of their nearest charted neighbour.
for sid in placed:
    s = by[sid]
    near = min((o for o in systems if o['id'] not in placed and o['region2235'] == 'usr'),
               key=lambda o: dist(o, s))
    for e in own[near['id']]:
        if e['from'] >= 2400:
            own[sid].append(dict(e, derived=True))

# After Thurva's death (19 June 2449) the Khanate splits. The eight khans' council holds
# the Gulf, the Sectors and the Voor worlds until it disperses on 11 May 2450; what is
# still held after that is "Khanate remnants". The northern clans become the Khanate of
# the Word. D'Tarik governs the Ka-Dur. The Veil divides among D'Ashan, the Veil Clans and,
# from late 2454, the Word's two dark stars on its northern edge.
DEATH, DISPERSAL = ym(2449, 6, 19), ym(2450, 5, 11)
NORTH = set(FREEHOLDS) | {s['id'] for s in north_v} | {s['id'] for s in north_m}
VEIL_IDS = [slug(n) for n, *_ in EXTRA['veil']]
veil_west = {slug(n) for n, x, y in EXTRA['veil'] if x <= -84}
veil_north = {'ushars-well', 'dhenmar'}
def holder(sid, t):
    cur = None
    for e in sorted(own[sid], key=lambda e: e['from']):
        if e['from'] <= t: cur = e
    return cur
for s in systems:
    sid = s['id']
    h = holder(sid, DEATH)
    if not h or h['p'] != 'khanate':
        continue
    if sid in NORTH:
        set_owner(sid, DEATH, 'word', derived=True)
    elif sid in VEIL_IDS:
        set_owner(sid, DEATH, 'veilclans' if sid in veil_west else 'dashan', derived=True)
        if sid in veil_north:
            set_owner(sid, ym(2454, 10), 'word', 'after Fevallion', derived=True)
    elif s['region2235'] == 'kadur':
        set_owner(sid, DEATH, 'dtarik')
        if sid in KADUR_FREED: set_owner(sid, KADUR_FREED[sid], 'kadur')
    elif s['region2235'] == 'dwaii':
        set_owner(sid, DEATH, 'remnant', derived=True)
    elif sid in WEST_MARCH_IDS:
        set_owner(sid, DEATH, 'dsethen')
    else:
        set_owner(sid, DEATH, 'eight')
        nxt = [e for e in own[sid] if e['from'] > DEATH]
        if not nxt or min(e['from'] for e in nxt) > DISPERSAL:
            set_owner(sid, DISPERSAL, 'remnant', derived=True)

# Folingar opens the southern road into the Dwaii and Ka-Dur holdings: the Legion takes it in late 2455, D'Hovar's raid of
# February 2456 takes it back, and the Southern Command takes it again with Omaggus in September 2457
set_owner('folingar', 2455.6, 'dhovar', 'besieged', vs='voor')
set_owner('folingar', 2455.85, 'voor', 'taken by the Legion')
set_owner('folingar', ym(2456, 2, 8), 'dhovar', 'retaken by D\'Hovar')
set_owner('folingar', 2457.45, 'dhovar', 'besieged', vs='voor')
set_owner('folingar', 2457.7, 'voor')
# the far peoples stay under the khanates: D'Tarik's three, D'Mareth's Dur Eshen
for sid in FAR_TAKEN:
    own[sid] = [e for e in own[sid] if not (e['from'] >= DEATH - 0.01 and e['p'] in ('eight', 'remnant'))]
    set_owner(sid, DEATH, 'dmareth' if sid == 'dur-eshen' else 'dtarik', 'subject world')
# the clan D'Mareth keeps its home dust east of the Veil as its own khanate (book: one of the eight by 2455)
set_owner('mareth-vel', ym(2449, 7), 'dmareth')
# the clans D'Tarik and D'Sethen keep their home stars in the Veil; D'Tarik's khan withdraws into the
# Veil's far reaches in the winter of 2457 (Syleth, where his last three monoliths settle)
set_owner('sel-tarik', DEATH, 'dtarik', derived=True)
set_owner('ul-sethen', DEATH, 'dsethen', derived=True)
if 'syleth' in own: set_owner('syleth', ym(2457, 12), 'dtarik', 'the Veil\'s far reaches', derived=True)

for sid in own:
    own[sid].sort(key=lambda e: e['from'])
    # a later decision for the same moment replaces the earlier one
    own[sid] = [e for i, e in enumerate(own[sid]) if not (i + 1 < len(own[sid]) and own[sid][i + 1]['from'] - e['from'] < 0.1)]

# ------------------------------------------------------------------ worlds
# Worlds: the sheet's settled worlds, with the book's dates where they differ, plus the
# non-human worlds known from contact and the book's later settlements.
BOOK_DATES = {'Mars': ym(2076, 7, 27), 'Luna': ym(2063, 3, 21), 'Io': ym(2114, 3, 1), 'Europa': ym(2116), 'Ganymede': ym(2118), 'Callisto': ym(2120),
              'Côte d\'Azur': ym(2342, 4, 21)}
SPELL = {"Cote d'Azure": "Côte d'Azur", 'New Caracas': 'Caldera', 'Nouveau Montreal': 'Nouveau Montréal', 'New Indata Mog': None, 'Earth': 'Earth'}
SLUGS = {'Dauntless': 'dauntless', 'Mardak Vol': 'mardak-vol-planet', 'Theia': 'theia', 'Bounty': 'bounty',
         'Landfall': 'landfall', 'Circumstance': 'circumstance', 'Serenity': 'serenity', 'Hualapai': 'hualapai'}
def biome_label(b):
    b = b.strip()
    if not b: return None
    b = re.sub(r'\s*world$', '', b, flags=re.I)
    return b + ' world'
worlds = []
for r in sheet:
    if not r[2]: continue
    name = SPELL.get(r[2], r[2])
    if name is None: continue                      # Indata Mog is a native Voor world in the book
    sid = sheet_id(r[3])
    d = {'sys': sid, 'name': name}
    if name == 'Earth':
        d['settled'] = 1900; d['native'] = True
    else:
        yy, mm, dd = (r[7].strip().split('.') + ['1', '1'])[:3]
        d['settled'] = BOOK_DATES.get(name, ym(int(yy), int(mm), int(dd)))
    m = re.search(r'(\d+)([a-z]?)(?:/.*)?$', r[8].strip())
    if m: d['pl'], d['moon'] = int(m.group(1)), bool(m.group(2))
    d['biome'] = biome_label(r[5])
    later = biome_label(r[6])
    if later and later != d['biome']: d['becomes'] = later
    if name == 'Mars': d['becomes'] = 'Continental world'
    if r[10].strip() and r[10].strip() != '-': d['capital'] = r[10].strip()
    if r[9].strip() and r[9].strip() != '-': d['ship'] = r[9].strip()
    if r[0].strip(): d['by'] = r[0].strip()
    if name in SLUGS: d['slug'] = SLUGS[name]
    worlds.append(d)
for sid, w, y, sl, pl in [
        ('exedor', 'Hiverion', 2318.3, 'hiverion', (2, 0)), ('haedus', 'Indata Mog', 2318.3, 'indata-mog', (3, 0)),
        ('aethos', 'Vur Duri', 2318.3, None, (2, 0)), ('ximpok', 'Vi Simni', 2318.3, None, (2, 0)),
        ('binami', 'Binami II (Inari)', ym(2315, 6, 3), 'inari', (2, 0)),
        ('nomotar', 'Nomotar', ym(2320), 'nomotar', (3, 0)), ('feonus', "Vel's Rest", ym(2467), None, (4, 0)),
        ('talandra', 'Talandra', ym(2345), 'talandra', (2, 0))]:
    d = {'sys': sid, 'name': w, 'settled': y}
    if sl: d['slug'] = sl
    if pl: d['pl'], d['moon'] = pl[0], bool(pl[1])
    if w in ('Hiverion', 'Indata Mog', 'Vur Duri', 'Vi Simni', 'Binami II (Inari)'): d['native'] = True
    if w in ('Indata Mog', 'Hiverion', 'Vur Duri'): d['biome'] = 'Steppe world'
    if w == 'Vi Simni': d['biome'] = 'Mediterranean world'
    if w == 'Binami II (Inari)': d['biome'] = 'Flood world'
    if w == "Vel's Rest": d['biome'] = 'Tundra world'
    if w == 'Nomotar': d['biome'] = 'Barren world'
    if w == 'Talandra': d['biome'] = 'Dry temperate world'
    worlds.append(d)
# ------------------------------------------------------------------ the other peoples' worlds
# The book gives the Thaali "perhaps forty systems" of tended worlds, the Dwaii three worlds and
# the Ka-Dur six systems, and names none of their worlds but Ossath. Everything here is invented
# (Lewis's choices, 18 November 2026): Thaali core systems hold one to four tended worlds and the
# frontier one or two, some visibly engineered, some kept wild, the frontier ones still being
# made; the Dwaii's are cold mountain worlds; the Ka-Dur's are varied round a sakura homeworld.
# 'gen' tells the planet generator what to draw.
arng = random.Random(1857)
MW_ON = ['Th', 'S', 'V', 'M', 'L', 'R', 'N', 'Qu', 'Ph', 'H', 'Sh', 'T', 'K', 'Ael', 'Or', 'Il']
MW_NU = ['aa', 'a', 'e', 'i', 'o', 'u', 'ae', 'ue', 'ou', 'ia', 'ee']
MW_MID = ['l', 'r', 'n', 'v', 'th', 'm', 's', 'ss', 'll', 'rr']
MW_CO = ['n', 'r', 'th', 'l', 's', '', '', 'm']
MW_USED = set()
def maweer_name():
    while True:
        on = arng.choice(MW_ON)
        nu = arng.choice(MW_NU) if on[-1] not in 'aeiou' and on not in ('Ael', 'Or', 'Il') else arng.choice(['a', 'e', 'i', 'o'])
        n = on + nu + arng.choice(MW_MID) + arng.choice(['a', 'e', 'i', 'o', 'u', 'aa', 'ue', 'ia'])
        if arng.random() < 0.35: n += arng.choice(MW_MID[:7]) + arng.choice(['a', 'e', 'i', 'o', 'u'])
        n += arng.choice(MW_CO)
        if 5 <= len(n) <= 10 and n not in MW_USED and not re.search(r'([aeiou])\1\1|[aeiou]{3}', n):
            MW_USED.add(n); return n
MW_FOREST = ['forest', 'megaflora', 'boreal', 'lake', 'cascadian', 'verdant', 'taiga', 'thunderstorm']
MW_BARE = ['ochre', 'colddesert', 'regolith', 'ironsand', 'basalt']
maweer_sys = [x for x in systems if x['region2235'] == 'maweer']
march_ids = {sid for sid in own if any(e['p'] == 'khanate' for e in own[sid])}
MAWEER_BURNED = 'ovastiuum'
# Lewis's choices (18 November 2026): five garden arcologies, Thaaluun, the Fejantris world and three
# spread through the core; every other Thaali world a forest world with two or three small ring-cities;
# two march worlds, one north and one west, still being made in 2510.
note = lambda sid: ([e.get('note') or '' for e in own[sid] if e['p'] == 'khanate'] or [''])[0]
core = sorted([x for x in maweer_sys if x['id'] not in march_ids], key=lambda x: x['id'])
pick = ['maweer', 'fejantris']
while len(pick) < 5:
    far = max((x for x in core if x['id'] not in pick), key=lambda x: min(math.dist((x['x'], x['y']), (by[p]['x'], by[p]['y'])) for p in pick))
    pick.append(far['id'])
ARC_SYS = set(pick)
north = sorted(x['id'] for x in maweer_sys if x['id'] in march_ids and 'northern' in note(x['id']))
west = sorted(x['id'] for x in maweer_sys if x['id'] in march_ids and 'western' in note(x['id']))
MAKING = {north[0], west[0]}
srng = random.Random(4417)   # styles drawn apart from names, so the names stay put
for x in sorted(maweer_sys, key=lambda x: x['id']):
    frontier = x['id'] in march_ids
    n = arng.randint(1, 2) if frontier else arng.randint(1, 4)
    pls = sorted(arng.sample(range(2, 7), n))
    for k, pl in enumerate(pls):
        home = x['id'] == 'maweer' and k == 0
        name = 'Thaaluun' if home else maweer_name()
        if home: MW_USED.add(name)
        d = {'sys': x['id'], 'name': name, 'settled': 1800, 'native': True, 'pl': pl, 'moon': False, 'people': 'Thaali', 'invented': True}
        forest = srng.choice(MW_FOREST); bare = srng.choice(MW_BARE)
        if x['id'] in ARC_SYS and k == 0:
            d['biome'] = 'Garden city-world' if x['id'] in ('maweer', 'fejantris') else 'Garden arcology'
            d['gen'] = {'now': 'verdant' if home else forest, 'after': None, 'cls': 'maweer', 'style': 'arcology'}
        elif x['id'] in MAKING and k == 0:
            d['biome'] = 'Forest world in the making'
            d['gen'] = {'now': bare, 'after': forest, 'cls': 'maweer', 'style': 'frontier', 'start': srng.randint(2300, 2400), 'ty': srng.randint(2540, 2580)}
        else:
            d['biome'] = 'Forest world'
            d['gen'] = {'now': forest, 'after': None, 'cls': 'maweer', 'style': 'forest'}
        if home: d['capital'] = 'Ouvenarth'; d['homeworld'] = True; d['slug'] = 'thaaluun'
        worlds.append(d)
mb = [w for w in worlds if w['sys'] == MAWEER_BURNED][0]
BURNED_EXTRA = [(MAWEER_BURNED, mb['name'], ym(2416, 8))]
ALIEN = [
    ('dwaimar', 'Dwaimar', 3, 'Dwaii', 'Alpine tundra world', 'tundra-alpine', True),
    ('hwen', 'Hwen', 2, 'Dwaii', 'Fjord world', 'dwaii-fjord', False),
    ('ellui', 'Ellui', 3, 'Dwaii', 'Highland tundra world', 'dwaii-tundra', False),
    ('kadris', 'Kadris', 3, 'Ka-Dur', 'Sakura world', 'sakura', True),
    ('ossath', 'Ossath', 2, 'Ka-Dur', 'Archipelago world', 'archipelago', False),
    ('tamuur', 'Tamuur', 3, 'Ka-Dur', 'Prairie world', 'prairie', False),
    ('dhur-ka', 'Dhur Ka', 2, 'Ka-Dur', 'Mesa world', 'mesa', False),
    ('sarrek', 'Sarrek', 4, 'Ka-Dur', 'Swamp world', 'swamp', False),
    ('imbal', 'Imbal', 3, 'Ka-Dur', 'Mediterranean world', 'mediterranean', False),
    ('ossa-theran', 'Ossath Ul', 3, 'Ossathi', 'Jungle world', 'forest', True),
    ('verentis', 'Veren', 2, 'Veren', 'Savanna world', 'semiarid', True),
    ('kal-tamar', 'Kal-Tam', 3, 'Kal-Tam', 'Desert world', 'mesa-terra', True),
    ('dur-eshen', 'Dur-Esh', 2, 'Dur-Esh', 'Ocean world', 'reef', True),
]
for sid, name, pl, people, biome, gtype, home in ALIEN:
    d = {'sys': sid, 'name': name, 'settled': 1800, 'native': True, 'pl': pl, 'moon': False, 'people': people,
         'biome': biome, 'invented': True, 'gen': {'now': gtype, 'after': None, 'cls': 'alien' if people in ('Dwaii', 'Ka-Dur') else 'alien-minor'}}
    if home: d['homeworld'] = True
    if name in ('Dwaimar', 'Kadris'): d['slug'] = slug(name); d['capital'] = {'Dwaimar': 'Dwaithom', 'Kadris': 'Imaruk'}[name]
    FAR = {'Ossath Ul': ('ossathi', 'Theran Crown'), 'Veren': ('veren', 'Ammarel'), 'Kal-Tam': ('kal-tam', 'Tamar Deep'), 'Dur-Esh': ('dur-esh', 'Eshen Reef')}
    if name in FAR: d['slug'], d['capital'] = FAR[name]
    worlds.append(d)

# New Veren (Lewis, 18 November 2026): an empty plains world at Tem that the Veren in exile settle from 2468.
worlds.append({'sys': 'tem', 'name': 'New Veren', 'settled': 2468, 'native': False, 'pl': 3, 'moon': False, 'people': 'Veren',
               'biome': 'Savanna world', 'invented': True, 'slug': 'new-veren', 'capital': 'Ammarel Nova',
               'gen': {'now': 'semiarid', 'after': None, 'cls': 'alien-minor', 'style': 'farcolony', 'start': 2468}})

# Fevarian space has no living worlds of the clans' own: they live aboard the monoliths and hulks.
# What the Veil and the freeholds do have: worlds the clans have stripped for metal, dead worlds
# with golden-age ruins, and one shattered world the Voor take for the clans' lost homeworld.
# Bodies are planets of note, not settled worlds; unnamed ones carry the system's numeral.
ROMAN = ['', 'I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII']
BODIES = {}
def body(sid, pl, kind, now, note):
    nm = by[sid]['name'] + ' ' + ROMAN[pl]
    BODIES.setdefault(sid, []).append({'pl': pl, 'name': nm, 'kind': kind, 'type': {'stripped': 'Stripped world', 'ruins': 'Ruin world', 'shattered': 'Shattered world'}[kind],
                                       'note': note, 'gen': {'now': now, 'after': None, 'cls': 'dead', 'special': kind}, 'invented': True})
for sid, pl, now in [('kasht', 2, 'ironsand'), ('vharr', 3, 'basalt'), ('drek-hul', 2, 'ochre'), ('ossek', 4, 'ironsand'),
                     ('churassix', 3, 'basalt'), ('barban', 2, 'ochre'), ('maasym', 4, 'ironsand'), ('rhen-tal', 3, 'colddesert')]:
    body(sid, pl, 'stripped', now, 'Mined to the mantle by the clans for metal')
for sid, pl, now in [('ashan-dur', 3, 'ochre'), ('thul-ashra', 2, 'colddesert'), ('fevallion', 3, 'ochre')]:
    body(sid, pl, 'ruins', now, 'Dead world with ruins of the Fevarian golden age')
body('dhen-ossa', 4, 'shattered', 'obsidian', 'Shattered world; the Voor hold it to be the Fevarians\' lost homeworld')

# Planets of note in the explorers' systems. The book gives Procyon two planets in the habitable
# band and four gas giants (Moorthi's Book), and has the Tadasca colony ship orbiting a gas giant;
# Barnard's Star is a flare star with nothing living. PLANET_NAMES' Procyon VII holds Procyon at
# eight planets.
def note_body(sid, pl, typ, note):
    BODIES.setdefault(sid, []).append({'pl': pl, 'name': by[sid]['name'] + ' ' + ROMAN[pl], 'kind': 'noted', 'type': typ, 'note': note, 'invented': True})
note_body('procyon', 8, 'Ice giant', "The outermost of Procyon's four giants")
note_body('tadasca', 4, 'Gas giant', 'The Mardak Vol colony ship lies in a decaying orbit around it')
note_body('barnards-star', 3, 'Irradiated rock', "Scoured by the star's flares")
for sid, pl, n in [('ithren', 2, 'first'), ('ommen', 4, 'second'), ('nadir', 4, 'third'), ('varrow', 3, 'fourth'), ('teluvar', 3, 'fifth'),
                   ('calders-reach', 3, 'sixth'), ('halloran', 2, 'seventh'), ('saskel', 3, 'eighth'), ('isolde', 3, 'ninth'),
                   ('peregrine', 3, 'tenth'), ('lastlight', 2, 'eleventh')]:
    note_body(sid, pl, 'Ruin world', 'Mardak Vol ruins; the ' + n + ' world the expedition of 2502 to 2505 landed on' + ('; the vault of the end' if n == 'fourth' else ''))

# Terraforming. A world keeps its found biome until its remaking is complete. The book dates
# Mars (the Marineris Tent lifted, 14 April 2182); the rest are estimated: worlds that were
# already living take about 60 years, the Second Wave's century plans about 100, the Third
# Wave's and later worlds about 120, and the Jovian moons are taken as complete by 2290.
LIVING = {'Mangrove world', 'Mesa world', 'Savana world', 'Tropical world', 'Atoll world', 'Tepui world', 'Continental world', 'Verdant world', 'Steppe world', 'Alpine world'}
for w in worlds:
    assert w['sys'] in by, w
    if not w.get('becomes'): continue
    if w['name'] == 'Mars':
        w['terraformed'] = ym(2182, 4, 14); w['biome'] = 'Barren world'; continue
    if w['name'] in ('Io', 'Europa', 'Ganymede', 'Callisto'):
        w['terraformed'] = 2290.0
    elif w['biome'] in LIVING:
        w['terraformed'] = round(w['settled'] + 60, 1)
    elif w['settled'] < 2349:
        w['terraformed'] = round(w['settled'] + 100, 1)
    else:
        w['terraformed'] = round(w['settled'] + 120, 1)
    w['terraformedEstimated'] = True
# Names of planets that are not settled worlds themselves
PLANET_NAMES = {'saolea': {2: 'Okeanos'}, 'ciriban': {3: 'Marigot', 5: 'Grand Anse'}, 'procyon': {2: 'Phoenicia', 7: 'Procyon VII'}}
BURNED = [('procyon', 'Landfall', ym(2441, 11, 26)), ('yildun', 'Dauntless', ym(2444, 12, 3)),
          ('saolea', 'Theia', ym(2436, 9, 12)), ('veyer', 'Hualapai', ym(2437, 3)),
          ('nomotar', 'Nomotar', ym(2438, 8, 20)), ('talandra', 'Talandra', ym(2441, 5, 10)),
          ('haedus', 'Indata Mog', ym(2428, 11, 6)), ('ijax', 'Ijax', ym(2433, 6)), ('myrum', 'Myrum', ym(2428, 7, 4)),
          ('ciriban', 'Bounty', ym(2430, 5, 18)), ('aethos', 'Vur Duri', ym(2422, 6, 14))]


# ------------------------------------------------------------------ system view features
# Stations, yards, starforts, tethers, Mars's mirrors and Custos, and the Fevarian monoliths,
# by year, for the 3D system view. 'at' is a planet number (or [planet, moon]), 'pillai' for the
# system's jump limit, or 'l1' for a planet's sun-side Lagrange point. Dates from the book where
# it gives them; the rest are estimates.
FEATURES = {
    'sol': [
        {'name': 'Kitty Hawk Station', 'kind': 'station', 'at': 3, 'from': 2047},
        # six on Earth, two on Mars and three on Europa before the Solar War; four stood at its end
        # (Singapore, Melas, and Quito and Nairobi re-spun in 2231 and 2232). The Swarga's second cable
        # stood 2241 to 2244; the Unification Works Program re-spun the Swarga (2264), Fortaleza (2266)
        # and Libreville (2270). Opening years from the book (Accords tethers 2172 to 2178).
        {'name': 'Swarga tether', 'kind': 'tether', 'at': 3, 'lon': 73, 'from': 2078, 'gaps': [[2229.99, 2241], [2244, 2264]]},
        {'name': 'Quito tether', 'kind': 'tether', 'at': 3, 'lon': -78, 'from': 2172, 'gaps': [[2229.99, 2232], [2446.7, 2470]]},
        {'name': 'Nairobi tether', 'kind': 'tether', 'at': 3, 'lon': 37, 'from': 2174, 'gaps': [[2229.99, 2232]]},
        {'name': 'Fortaleza tether', 'kind': 'tether', 'at': 3, 'lon': -38, 'from': 2175, 'gaps': [[2229.99, 2266], [2446.7, 2470]]},
        {'name': 'Libreville tether', 'kind': 'tether', 'at': 3, 'lon': 9.5, 'from': 2176, 'gaps': [[2229.99, 2270]]},
        {'name': 'Singapore tether', 'kind': 'tether', 'at': 3, 'lon': 104, 'from': 2178, 'gaps': [[2446.7, 2470]]},
        {'name': 'Xi Lunar Yards', 'kind': 'yard', 'at': [3, 0], 'from': 2290, 'gap': [2446.8, 2474]},
        {'name': 'Helios array', 'kind': 'mirrors', 'at': 4, 'pole': 1, 'from': 2088, 'build': 2096, 'to': 2446.7},
        {'name': 'Lumen array', 'kind': 'mirrors', 'at': 4, 'pole': -1, 'from': 2100, 'build': 2104, 'to': 2446.7},
        {'name': 'Concordia array', 'kind': 'mirrors', 'at': 4, 'pole': 0, 'from': 2118, 'build': 2128, 'to': 2446.7},
        {'name': 'Mars mirror array', 'kind': 'mirrors', 'at': 4, 'pole': 0, 'from': 2465, 'build': 2485},
        {'name': 'Custos Station', 'kind': 'custos', 'at': 4, 'from': 2112, 'on': 2114},
        {'name': 'Melas tether', 'kind': 'tether', 'at': 4, 'lon': -71, 'from': 2160, 'gaps': [[2446.7, 2470]]},
        # the Pavonis tether on Tharsis: cut in the landings of 2246, re-spun 2272 to 2274, its anchor broken in September 2276
        {'name': 'Pavonis tether', 'kind': 'tether', 'at': 4, 'lon': -113.4, 'from': 2170, 'gaps': [[2246.0, 2274], [2276.7, 2300], [2446.7, 2470]]},
        # Europa's three, cut in the Jovian campaign; Da Gama 2262, Tycho City 2266, New Rhine 2276 (wiki: Tether re-spinning)
        {'name': 'New Rhine tether', 'kind': 'tether', 'at': [5, 1], 'lon': -94, 'from': 2144, 'gaps': [[2250, 2276]]},
        {'name': 'Da Gama tether', 'kind': 'tether', 'at': [5, 1], 'lon': -40, 'from': 2159, 'gaps': [[2250, 2262]]},
        {'name': 'Tycho City tether', 'kind': 'tether', 'at': [5, 1], 'lon': -125, 'from': 2167, 'gaps': [[2249.5, 2266]]},
        {'name': 'The Khan\'s fleet', 'kind': 'fleet', 'at': 5, 'from': 2446.25, 'to': 2446.6, 'n': 106},
        {'name': 'The Khan\'s fleet', 'kind': 'fleet', 'at': 3, 'from': 2446.6, 'to': 2447.03, 'n': 73},
    ],
    'ciriban': [
        {'name': 'The Exchange', 'kind': 'station', 'at': 'pillai', 'from': 2320, 'to': 2360},
        {'name': 'Delambre', 'kind': 'starfort', 'at': 'pillai', 'from': 2324, 'to': 2429},
        {'name': 'Hellas Gate', 'kind': 'starfort', 'at': 'pillai', 'from': 2324, 'to': 2429},
        {'name': 'Pauldron', 'kind': 'starfort', 'at': 'pillai', 'from': 2324, 'to': 2429},
        {'name': 'Bijou Nan Syèl La', 'kind': 'station', 'at': 4, 'from': 2352, 'to': 2429.27},
        {'name': 'Monolith anchorage', 'kind': 'fleet', 'at': 4, 'from': 2429.05, 'to': 2440.3, 'n': 40},
    ],
    'nomotar': [{'name': n, 'kind': 'starfort', 'at': 'pillai', 'from': 2322, 'to': 2438.6} for n in ('Tethers', 'Manila', 'Chasma')] +
               [{'name': 'Northern station', 'kind': 'station', 'at': 3, 'from': 2321, 'to': 2438.6}],
    'saolea': [{'name': 'Rhine', 'kind': 'starfort', 'at': 'pillai', 'from': 2327, 'to': 2436.7},
               {'name': 'Io', 'kind': 'starfort', 'at': 'pillai', 'from': 2329, 'to': 2436.7},
               {'name': 'Hoplonka orbital', 'kind': 'station', 'at': 1, 'from': 2331, 'to': 2436.7}],
    'haedus': [{'name': 'Naval Station Paldron', 'kind': 'starfort', 'at': 'pillai', 'from': 2424, 'to': 2428.68},
               {'name': 'Naval Station Paldron', 'kind': 'starfort', 'at': 'pillai', 'from': 2453},
               {'name': 'Monolith anchorage', 'kind': 'fleet', 'at': 3, 'from': 2428.6, 'to': 2451.4, 'n': 20},
               {'name': 'D\'Mareth hulk', 'kind': 'hulk', 'at': 'pillai', 'from': 2474}],
    'exedor': [{'name': 'Hiverion hearth yards', 'kind': 'yard', 'at': 2, 'from': 1327, 'to': 2427.6, 'gap': [2341.05, 2416.2], 'slug': 'hearth-yards'},
               {'name': 'Hiverion hearth yards (rebuilt)', 'kind': 'yard', 'at': 2, 'from': 2475, 'slug': 'hearth-yards'},
               {'name': 'Monolith anchorage', 'kind': 'fleet', 'at': 2, 'from': 2427.6, 'to': 2451.7, 'n': 30}],
    'talandra': [{'name': 'The Khan\'s fleet', 'kind': 'fleet', 'at': 2, 'from': 2441.3, 'to': 2441.5, 'n': 210},
                 {'name': 'The Khan\'s fleet', 'kind': 'fleet', 'at': 2, 'from': 2449.4, 'to': 2449.47, 'n': 61}],
    'alpha-centauri': [{'name': 'The Khan\'s seat', 'kind': 'fleet', 'at': 1, 'from': 2442.3, 'to': 2446.13, 'n': 51}],
    'procyon': [{'name': 'Monolith anchorage', 'kind': 'fleet', 'at': 2, 'from': 2441.9, 'to': 2448.2, 'n': 12}],
    'bashpit': [{'name': 'Monolith garrison', 'kind': 'fleet', 'at': 2, 'from': 2441, 'to': 2449.84, 'n': 3}],
}
for x in systems:
    # the Veil's and the freeholds' monoliths, hulks and stations are the clans' own (atlas/clans.py)
    if x['region2235'] in ('dwaii', 'kadur'):
        to = 2456.7 if x['region2235'] == 'dwaii' else (2457.5 if x['id'] in KADUR_FREED else None)
        f = {'name': 'Garrison monoliths', 'kind': 'fleet', 'at': 'pillai', 'from': 2408 if x['region2235'] == 'dwaii' else 2412, 'n': 2}
        if to: f['to'] = to
        FEATURES.setdefault(x['id'], []).append(f)

# The Khanate's orbitals: 400 million Fevarians settled on the tributary worlds' orbitals from 2413, until each world
# was retaken. Hiverion's Ring held 6 million and fell section by section to 30 November 2452.
KHAN_RULE = {'khanate', 'eight', 'remnant', 'word', 'dashan', 'dtarik', 'dsethen', 'dhovar', 'dmareth'}
for x in systems:
    ws_ = sorted([w for w in worlds if w['sys'] == x['id'] and w.get('pl') and not w.get('moon')], key=lambda w: -(w.get('native') or 0))
    if not ws_: continue
    hist = sorted(own[x['id']], key=lambda e: e['from'])
    start = None
    for e in hist + [{'from': 9999, 'p': None}]:
        ruled = e['p'] in KHAN_RULE
        if ruled and start is None: start = e['from']
        elif not ruled and start is not None:
            w0 = ws_[0]; end = e['from'] if e['from'] < 9999 else None
            nm = 'Fevarian orbitals'
            if w0['name'] == 'Hiverion': nm, end = "Hiverion's Ring", 2452.92
            f = {'name': nm, 'kind': 'orbital', 'at': w0['pl'], 'from': max(start, 2413) + 0.3}
            if end: f['to'] = end
            if not end or end > f['from']: FEATURES.setdefault(x['id'], []).append(f)
            start = None
for x in systems:
    if x['region2235'] == 'fevarian':
        FEATURES.setdefault(x['id'], []).append({'name': 'Freehold settlement', 'kind': 'orbital', 'at': 'pillai', 'from': 1300,
                                                 'to': 2454.87 if x['id'] == 'fevallion' else 2454.6, 'n': 3 if x['id'] == 'fevallion' else 1})
# the clans: every monolith with a home, a war and a fate; their hulks and stations stay home
import clans as CL
CLANS = CL.build(systems, by, FEATURES, marches, north_m, west_marches, FREEHOLDS, VEIL_IDS)
# the six hearths the Khan took at Vi Simni and Hiverion sail with his fleet
for f in FEATURES.get('exedor', []):
    if f['name'] == 'Monolith anchorage': f['hearths'] = 6
for sid in ('talandra', 'alpha-centauri'):
    for f in FEATURES.get(sid, []):
        if f['kind'] == 'fleet': f['hearths'] = 2

# ------------------------------------------------------------------ events
def ev(y, label, sys, kind='battle', slug=None):
    assert sys in by, sys
    e = {'y': y, 'label': label, 'sys': sys, 'kind': kind}
    if slug: e['slug'] = slug
    return e

EVENTS = [
    ev(ym(2076, 7, 27), 'Bartolomeu founded on Mars', 'sol', 'world'), ev(ym(2063, 3, 21), 'Zheng He founded on Luna', 'sol', 'world'),
    ev(ym(2114, 3, 1), 'Van Maanush founded on Io', 'sol', 'world'), ev(ym(2116), 'New Rhine founded on Europa', 'sol', 'world'),
    ev(ym(2118), 'Xi He founded on Ganymede', 'sol', 'world'), ev(ym(2120), 'Sabre founded on Callisto', 'sol', 'world'),
    ev(ym(2283, 6, 1), 'United Nations of Earth founded', 'sol', 'polity', 'united-nations-of-earth'),
    # the Jovian and Martian revolts and the Solar War (2220 to 2252), from the wiki's articles
    ev(ym(2207, 11, 15), 'Jovian Intifada begins', 'sol', 'war', 'jovian-intifada'),
    ev(ym(2220, 1, 2), 'Gandhi Revolt; the Solar War begins', 'sol', 'war', 'gandhi-revolt'),
    ev(ym(2224, 7, 27), 'Martian Revolt', 'sol', 'war', 'martian-revolt'),
    ev(ym(2225, 7, 14), 'Battle of Hellas Gate', 'sol', 'battle', 'battle-of-hellas-gate'),
    ev(ym(2226, 5, 18), 'Battle of Eos Rift', 'sol', 'battle', 'battle-of-eos-rift'),
    ev(ym(2227, 9, 12), 'Raid on Delambre', 'sol', 'battle', 'raid-on-delambre'),
    ev(ym(2227, 10, 10), 'Battle of Procellarum', 'sol', 'battle', 'battle-of-procellarum'),
    ev(ym(2227, 11, 2), 'Siege of Zheng He', 'sol', 'battle', 'siege-of-zheng-he'),
    ev(ym(2227, 11, 20), 'Battle of Farside', 'sol', 'battle', 'battle-of-farside'),
    ev(ym(2228, 1, 15), 'Siege of Hangzhou One', 'sol', 'battle', 'siege-of-hangzhou-one'),
    ev(ym(2228, 10, 14), 'Siege of Copernicus', 'sol', 'battle', 'siege-of-copernicus'),
    ev(ym(2229, 12, 30), 'Battle of the Tethers', 'sol', 'battle', 'battle-of-the-tethers'),
    ev(ym(2230, 1, 6), 'First Battle of Sydney', 'sol', 'battle', 'first-battle-of-sydney'),
    ev(ym(2230, 2, 12), 'Battle of the Tasman', 'sol', 'battle', 'battle-of-the-tasman'),
    ev(ym(2230, 11, 3), 'Second Battle of Sydney', 'sol', 'battle', 'second-battle-of-sydney'),
    ev(ym(2231, 1, 14), 'Battle of Singapore', 'sol', 'battle', 'battle-of-singapore'),
    ev(ym(2232, 3, 2), 'Battle for Lunar Orbit', 'sol', 'battle', 'battle-for-lunar-orbit'),
    ev(ym(2232, 3, 6), 'Battle of Galileo Station', 'sol', 'battle', 'battle-of-galileo-station'),
    ev(ym(2232, 3, 20), 'Siege of Delambre', 'sol', 'battle', 'siege-of-delambre'),
    ev(ym(2233, 1, 14), 'Battle of Dongsuo', 'sol', 'battle', 'battle-of-dongsuo'),
    ev(ym(2239, 4, 12), 'Raid on Bartolomeu', 'sol', 'battle', 'raid-on-bartolomeu'),
    ev(ym(2246, 1, 2), 'Operation Blue Smoke', 'sol', 'battle', 'operation-blue-smoke'),
    ev(ym(2246, 5, 12), 'Hellas Basin Campaign', 'sol', 'battle', 'hellas-basin-campaign'),
    ev(ym(2246, 7, 20), 'Siege of Bartolomeu', 'sol', 'battle', 'siege-of-bartolomeu'),
    ev(ym(2246, 7, 25), 'Battle of Coleridge', 'sol', 'battle', 'battle-of-coleridge'),
    ev(ym(2246, 10, 5), 'Seismic campaign', 'sol', 'battle', 'seismic-campaign'),
    ev(ym(2248, 1), 'Himalia Raids', 'sol', 'battle', 'himalia-raids'),
    ev(ym(2249, 8, 12), 'Battle for Io', 'sol', 'battle', 'battle-for-io'),
    ev(ym(2249, 12, 20), 'Battle of Loki Mons', 'sol', 'battle', 'battle-of-loki-mons'),
    ev(ym(2250, 2, 14), 'Battle of New Rhine', 'sol', 'battle', 'battle-of-new-rhine'),
    ev(ym(2250, 3, 1), 'Battle for Magellan', 'sol', 'battle', 'battle-for-magellan'),
    ev(ym(2250, 3, 5), 'Battle of Da Gama', 'sol', 'battle', 'battle-of-da-gama'),
    ev(ym(2251, 3), 'Callisto Campaign', 'sol', 'battle', 'callisto-campaign'),
    ev(ym(2252, 4, 11), 'Operation Decapitation; the Solar War ends', 'sol', 'battle', 'operation-decapitation'),
    ev(ym(2300, 2, 25), 'Lief Ericson reaches Procyon', 'procyon', 'survey'),
    ev(ym(2303, 5), 'Mardak Vol colony ship found', 'tadasca', 'survey'),
    ev(ym(2305), 'First Sirius observation post found', 'sirius', 'survey'),
    ev(ym(2307, 12, 14), 'The Yildun capsule', 'yildun', 'survey'),
    ev(ym(2308, 11, 2), 'Gagarin reaches Daranma', 'daranma', 'survey', 'daranma'),
    ev(ym(2315, 6, 3), 'The Inari seen at Binami', 'binami', 'survey', 'inari'),
    ev(ym(2318, 4), 'First human visit to Exedor', 'exedor', 'survey', 'exedor'),
    ev(ym(2333, 7, 28), 'Ciriban Incident', 'nomotar', 'battle', 'ciriban-incident'),
    ev(ym(2333, 9, 12), 'Operation Mirage', 'myrum', 'battle', 'operation-mirage'),
    ev(ym(2333, 11, 6), 'First Battle of Media', 'media', 'battle', 'first-battle-of-media'),
    ev(ym(2334, 2, 2), 'Battle of the Mog', 'haedus', 'battle', 'battle-of-the-mog'),
    ev(ym(2334, 5, 14), 'Second Battle of Media', 'media', 'battle', 'second-battle-of-media'),
    ev(ym(2334, 9, 12), 'Fall of New Indata Mog', 'haedus', 'battle', 'fall-of-new-indata-mog'),
    ev(ym(2336, 3, 10), 'Battle of Exedor', 'exedor', 'battle', 'battle-of-exedor-2336'),
    ev(ym(2335, 2, 3), 'Fall of Kastaba', 'kastaba', 'battle', 'fall-of-kastaba-and-swur'),
    ev(ym(2335, 4, 5), 'Swur abandoned', 'swur', 'battle', 'fall-of-kastaba-and-swur'),
    ev(ym(2337, 6, 22), 'Battle of Leesak', 'leesak', 'battle', 'battle-of-leesak'),
    ev(ym(2338, 5, 3), 'Fall of the Krakre', 'exedor', 'battle', 'siege-of-hiverion'),
    ev(ym(2339, 8, 17), 'A hearth strikes at Ximpok', 'ximpok', 'battle', 'voolar-surrender'),
    ev(ym(2340, 12, 21), 'Voolar Surrender', 'exedor', 'treaty', 'voolar-surrender'),
    ev(ym(2341, 1, 21), 'Treaty of Ximpok', 'ximpok', 'treaty', 'treaty-of-ximpok'),
    ev(ym(2341, 1, 1), 'Unified Solar Republic proclaimed', 'sol', 'polity', 'unified-solar-republic'),
    ev(ym(2388), 'Thurva named the Red Khan', 'dhen-ossa', 'polity'),
    ev(ym(2405), 'Assembly of the Veil', 'dhen-ossa', 'polity'),
    ev(ym(2408), 'The Dwaii fleet destroyed', 'hwen', 'battle'),
    ev(ym(2413), 'The Ka-Dur fall', 'ossath', 'battle'),
    ev(ym(2417, 5), 'Romston submits', 'romston', 'battle'),
    # the Thaali front (wiki articles, 18 November 2026)
    ev(ym(2413, 4), 'The Khan strikes the Thaali marches', 'zosma', 'battle', 'fall-of-the-thaali-marches'),
    ev(ym(2417, 1), 'The Thaali seal their frontier', 'craxima', 'battle', 'fall-of-the-thaali-marches'),
    ev(ym(2447, 3, 2), 'The Thaali offensive', 'craxima', 'battle', 'thaali-offensive'),
    ev(ym(2456, 3, 9), 'Battle of Kaldreth', 'craxima', 'battle', 'battle-of-kaldreth'),
    ev(ym(2419, 9), 'Cazzabius burned', 'cazzabius', 'burning'),
    ev(ym(2422, 6, 14), 'Fall of Vur Duri', 'aethos', 'battle'),
    ev(ym(2424, 6), 'Vi Simni submits', 'ximpok', 'battle'),
    ev(ym(2427, 8, 16), 'Fall of Hiverion', 'exedor', 'battle', 'hiverion'),
    ev(ym(2428, 7, 4), 'Myrum burned', 'myrum', 'burning', 'myrum'),
    ev(ym(2428, 7, 9), 'Fall of Myrum', 'myrum', 'battle', 'myrum'),
    ev(ym(2428, 8, 6), 'First Battle of Haedius', 'haedus', 'battle', 'first-battle-of-haedius'),
    ev(ym(2428, 9, 3), 'Second Battle of Haedius', 'haedus', 'battle', 'second-battle-of-haedius'),
    ev(ym(2428, 11, 6), 'Indata Mog burned', 'haedus', 'burning', 'tunnel-war-on-indata-mog'),
    ev(ym(2429, 1, 22), 'Siege of Bounty', 'ciriban', 'battle', 'siege-of-bounty'),
    ev(ym(2430, 5, 17), "Last stand at Roric's Plaza", 'ciriban', 'battle', 'battle-of-rorics-plaza'),
    ev(ym(2433, 6), 'Ijax burned', 'ijax', 'burning'),
    ev(ym(2434, 3, 12), 'Battle of Saolea', 'saolea', 'battle', 'battle-of-saolea'),
    ev(ym(2436, 9, 12), 'Theia burned', 'saolea', 'burning', 'burning-of-theia'),
    ev(ym(2437, 3), 'Hualapai burned', 'veyer', 'burning'),
    ev(ym(2438, 1), 'Siege of Nomotar', 'nomotar', 'battle', 'siege-of-nomotar'),
    ev(ym(2440, 4, 14), 'Fall of Binami', 'binami', 'battle'),
    ev(ym(2441, 5, 2), 'First Battle of Talandra', 'talandra', 'battle', 'first-battle-of-talandra'),
    ev(ym(2441, 11, 14), 'Battle of Procyon', 'procyon', 'battle', 'battle-of-procyon-2441'),
    ev(ym(2441, 11, 26), 'Landfall burned', 'procyon', 'burning', 'burning-of-landfall'),
    ev(ym(2442, 4, 20), 'Circumstance submits', 'alpha-centauri', 'battle', 'submission-of-circumstance'),
    ev(ym(2444, 6, 8), 'Battle of Yildun', 'yildun', 'battle', 'yildun'),
    ev(ym(2444, 12, 3), 'Dauntless burned', 'yildun', 'burning', 'dauntless'),
    ev(ym(2446, 4, 2), 'Battle of Jupiter', 'sol', 'battle', 'battle-of-jupiter'),
    ev(ym(2446, 12, 5), 'Battle of Earth', 'sol', 'battle', 'battle-of-earth'),
    ev(ym(2447, 10, 14), 'Battle of Alpha Centauri', 'alpha-centauri', 'battle', 'counterattack-of-2447-to-2448'),
    ev(ym(2448, 5, 4), 'Second Battle of Procyon', 'procyon', 'battle', 'counterattack-of-2447-to-2448'),
    ev(ym(2449, 6, 14), 'Second Battle of Talandra', 'talandra', 'battle', 'second-battle-of-talandra'),
    ev(ym(2450, 5, 11), 'The eight khans disperse', 'ciriban', 'polity'),
    ev(ym(2449, 11), 'Bashpit, the Scouring begins', 'bashpit', 'battle', 'scouring'),
    ev(ym(2450, 5, 16), 'Bounty retaken', 'ciriban', 'battle', 'bounty'),
    ev(ym(2451, 5, 9), 'Third Battle of Haedius', 'haedus', 'battle', 'third-battle-of-haedius'),
    ev(ym(2451, 9, 24), 'Battle of Exedor', 'exedor', 'battle', 'battle-of-exedor-2451'),
    ev(ym(2452, 11, 30), "Hiverion's orbitals fall", 'exedor', 'battle', 'reclamation-of-the-voor-worlds'),
    ev(ym(2453, 1, 1), 'Voor Confederacy restored', 'exedor', 'polity', 'reclamation-of-the-voor-worlds'),
    ev(ym(2453, 8, 9), "D'Ashan's counterattack", 'aethos', 'battle', 'second-battle-of-aethos'),
    ev(ym(2453, 10, 18), 'Second Battle of Aethos', 'aethos', 'battle', 'second-battle-of-aethos'),
    ev(ym(2456, 2, 11), "D'Hovar's counterattack", 'omaggus', 'battle', 'reclamation-of-the-voor-worlds'),
    ev(ym(2460, 4, 1), 'Kuma and Ijaagin returned', 'kuma', 'treaty', 'fejantris-peace'),
    ev(ym(2454, 4), 'Churassix', 'churassix', 'battle', 'northern-reaches-campaign'),
    ev(ym(2454, 10, 20), 'Battle of Fevallion', 'fevallion', 'battle', 'northern-reaches-campaign'),
    ev(ym(2455, 6, 2), 'Fleets meet at Fejantris', 'fejantris', 'treaty', 'the-hunt-2455-to-2458'),
    ev(ym(2456, 4), 'The Dwaii freed', 'hwen', 'battle', 'the-hunt-2455-to-2458'),
    ev(ym(2457, 2, 20), 'Battle of Ossath', 'ossath', 'battle', 'battle-of-ossath'),
    ev(ym(2460, 1, 1), 'Fejantris Peace', 'fejantris', 'treaty', 'fejantris-peace'),
    ev(ym(2466, 6, 20), 'Fevarian Accords signed', 'exedor', 'treaty'),
]

# ------------------------------------------------------------------ captions
CAPTIONS = [
    (1000, 1108, 'Six Voor worlds with six navies and no common cause. The Fevarian clans have already taken the Ommath of the inner Gulf.'),
    (1108, 1438, 'The Fevarian wars. The clans burn two Voor worlds, and the four that survive found the Legion and drive the clans beyond the Veil.'),
    (1438, 2018, 'The Voor Confederacy settles the Gulf and the systems beyond it. Its history before contact comes from the Legion\'s sealed histories.'),
    (2018, 2050, 'The Voor meet the Thaali at Zom. Humanity has not yet settled beyond Earth.'),
    (2050, 2100, 'The Sun\'s planets are settled. Luna and Mars become the first worlds beyond Earth.'),
    (2100, 2220, 'Humanity spreads through the Sun\'s system. No ship has yet crossed to another star.'),
    (2220, 2255, 'The Solar War divides the Sun\'s worlds.'),
    (2255, 2283, 'Unification. The Sun\'s worlds move toward a single government.'),
    (2283, 2300, 'The United Nations of Earth is founded and commits to the stars.'),
    (2300, 2318, 'The Expansion Era. Four survey ships chart 800 stars; the core worlds are founded.'),
    (2318, 2333, 'Contact with the Voor. The Ciriban Gulf becomes a border of trade and forts.'),
    (2333, 2341, 'The Ciriban Gulf Conflict. The Republic\'s fleets drive into the Confederacy.'),
    (2341, 2405, 'The First Republic. Second and Third Waves settle the frontier; the Voor Territories join.'),
    (2405, 2428, 'The Red Khan unites the Veil and conquers the Dwaii, the Ka-Dur and the Confederacy.'),
    (2428, 2441, 'The Fevarian Crisis. The Khan takes the Gulf and both Sectors.'),
    (2441, 2449, 'The Darkest Decade. The Khanate strikes into the core and reaches the Sun.'),
    (2449, 2460, 'The Scouring. The Retribution Fleet destroys the monoliths outside the Veil.'),
    (2460, 2510, 'Reconstruction. The Second Republic rebuilds the burned worlds.'),
    (2510, 2516, 'The Apportionment Crisis. Chamber seats are recalculated for the first time since 2420.'),
]

# wrecks of the Republic's well battles (from the Miracle at Sol on) lie by the world fought over;
# the earlier battles at the edge leave theirs on the jump limit
WRECK_AT = {('sol', 'the Battle of Earth'): 3, ('sol', 'Jupiter'): 5}
for sid, fs in FEATURES.items():
    for f in fs:
        if f['kind'] != 'wreck': continue
        if (sid, f['battle']) in WRECK_AT: f['at'] = WRECK_AT[(sid, f['battle'])]; continue
        if f['from'] < 2446 or sid == 'sol': continue
        ws_ = sorted((w for w in worlds if w['sys'] == sid and w.get('pl') and w['settled'] < f['from']), key=lambda w: (not w.get('native'), w['settled']))
        if ws_: f['at'] = ws_[0]['pl']

# ---- the Thaali in the Atlas (Lewis, 22 November 2026): the great fleet at the three crossings of the Voor frontier,
# the Legion's frontier hearths opposite them, the Thaali fleets in the marches, the march hedges, yards and stations
GF = 'Thaali great fleet'
def _navy(sid, name, side, style, a, b, n, strength, slug_):
    FEATURES.setdefault(sid, []).append({'name': name, 'kind': 'navy', 'side': side, 'style': style, 'at': 'pillai',
                                         'from': a, 'to': b, 'n': n, 'strength': strength, 'slug': slug_})
# (crossing, Voor system opposite, great ships drawn: peace, the watch of 2334 to 2340, 2341 to 2447, 2447 to 2449, from 2449)
CROSSINGS = [('zom', 'faenov', 'the central crossing, opposite Faenov', (5, 10, 5, 2, 4), True),
             ('tirim', 'wicklar', 'the crossing opposite Wicklar', (4, 7, 4, 1, 3), False),
             ('cheleb', 'wuae', 'the crossing opposite Wuae', (4, 7, 4, 1, 3), False)]
for sid, vsid, where, (p0, p1, p2, p3, p4), centre in CROSSINGS:
    big = ' with the three ships of the Ocean Under the Ice class' if centre else ''
    for a, b, n, txt in ((2018, 2334.5, p0, 'the frontier keepers\' body at ' + where + big),
                         (2334.5, 2341.0, p1, 'the frontier watch: part of about twenty-four great ships at the crossings' + big),
                         (2341.0, 2447.17, p2, 'the body at ' + where + ' through the sealed years' + big),
                         (2447.17, 2449.6, p3, 'the body left at ' + where + ' while the great fleet fought in the marches'),
                         (2449.6, 2515, p4, 'the body at ' + where + ' under the Accords' + (' with two of the three greatest ships' if centre else ''))):
        _navy(sid, GF, 'Thaali', 'thaali', a, b, n + 6, '%d great ships of the Weight of the Sea class; %s' % (n, txt), 'great-fleet-thaali')
    _navy(vsid, 'The Legion\'s frontier hearths', 'Voor Legion', 'voor', 2018, 2334.5, 4,
          'Frontier hearths opposite the Thaali at ' + sid.title() + ', under one of the three frontier Generals', 'thaali-voor-frontier')
    _navy(vsid, 'The Legion\'s frontier hearths', 'Voor Legion', 'voor', 2334.5, 2343.0, 7,
          'Part of the twenty best hearths of the Legion, held on the Thaali frontier through the Ciriban Gulf Conflict; moved to the Veil frontier in the 2340s', 'thaali-voor-frontier')
_navy('faenov', 'The Legion\'s frontier hearths', 'Voor Legion', 'voor', 2454.1, 2515, 2,
      'The restored Legion\'s hearths on the Thaali frontier again', 'thaali-voor-frontier')
# the southern frontier fleets with eleven great ships, falling back march by march (2413 to 2417)
_lost_south = [11, 10, 8, 8, 7, 4]
for (sg, fl), s_, g in zip(SOUTH_FALL, marches, _lost_south):
    _navy(s_['id'], 'Thaali southern frontier fleet', 'Thaali', 'thaali', sg, fl, 14 + g,
          'The southern reaches and %d great ships, holding the march under its hedge' % g, 'fall-of-the-thaali-marches')
# the home fleets and the great fleet in the offensive (2447 to 2449), the march they took back in turn
_gs = {5: 9, 4: 9, 3: 8, 2: 8, 1: 7, 0: 7}
for i, (a, b) in SOUTH_BACK.items():
    _navy(marches[i]['id'], 'Thaali home fleets', 'Thaali', 'thaali', a, b, 16 + _gs[i],
          'The home fleets\' reaches led by %d great ships of the great fleet' % _gs[i], 'thaali-offensive')
_navy('fejantris', 'Thaali fleets at Fejantris', 'Thaali', 'thaali', 2455.40, 2455.48, 24,
      'About 400 hulls, eight great ships and the Sea Before the Land Was, met by the Retribution Fleet on 2 June 2455', 'nomotar-agreement')
# the march hedges: whole over each march world until it fell, broken under the Khanate, rebuilt after the offensive
def _first(sid, pred):
    for e in sorted(own[sid], key=lambda e: e['from']):
        if pred(e): return e['from']
_hr = random.Random(4471)
for s_ in marches + north_m + west_marches:
    ws_ = sorted([w for w in worlds if w['sys'] == s_['id'] and w.get('pl') and not w.get('moon')], key=lambda w: w['pl'])
    if not ws_: continue
    pl = ws_[0]['pl']; fall = _first(s_['id'], lambda e: e['p'] == 'khanate')
    back = None
    if fall:
        back = next((e['from'] for e in sorted(own[s_['id']], key=lambda e: e['from']) if e['from'] > fall and e['p'] == 'maweer' and not e.get('note')), None)
    fs = FEATURES.setdefault(s_['id'], [])
    h = {'name': 'March hedge', 'kind': 'hedge', 'at': pl, 'from': 1700, 'slug': 'thaali-march-fortifications'}
    if fall: h['to'] = fall
    fs.append(h)
    if fall:
        bh = {'name': 'March hedge (stripped)', 'kind': 'hedge', 'broken': True, 'at': pl, 'from': fall, 'slug': 'thaali-march-fortifications'}
        if back:
            done = round(min(2490.0, back + 3 + _hr.random() * 37), 1); bh['to'] = done
            fs.append(bh)
            fs.append({'name': 'March hedge (rebuilt)', 'kind': 'hedge', 'at': pl, 'from': done, 'slug': 'thaali-march-fortifications'})
        else:
            fs.append(bh)
# the great yards and the stations of the opening
FEATURES.setdefault('maweer', []).extend([
    {'name': 'Great yards of Thaaluun', 'kind': 'yard', 'at': 3, 'from': 1900},
    {'name': 'Great yards of Kouria', 'kind': 'yard', 'at': 4, 'from': 1900},
    {'name': 'Reception station', 'kind': 'station', 'at': 3, 'from': ym(2471, 11)}])
FEATURES.setdefault('fejantris', []).extend([
    {'name': 'Great yards of Vaamith', 'kind': 'yard', 'at': 2, 'from': 1900},
    {'name': 'Conference station', 'kind': 'station', 'at': 'pillai', 'from': ym(2459, 5)},
    {'name': 'Republic trade mission', 'kind': 'station', 'at': 2, 'from': ym(2468, 5)}])
FEATURES.setdefault('saonus', []).append({'name': 'Great yards of Haessaas', 'kind': 'yard', 'at': 2, 'from': 1900})
EVENTS.extend([
    ev(ym(2334, 7), 'The Thaali mass on the Voor frontier', 'zom', 'battle', 'thaali-voor-frontier'),
    ev(ym(2416, 8), 'Orerom burned', 'ovastiuum', 'burning', 'burning-of-orerom'),
    ev(ym(2455, 3, 14), 'Nomotar agreement', 'nomotar', 'treaty', 'nomotar-agreement'),
    ev(ym(2468, 5), 'Republic trade mission at Fejantris', 'fejantris', 'polity', 'thaali-opening'),
    ev(ym(2471, 11), 'Republic envoys received over Thaaluun', 'maweer', 'polity', 'thaali-opening'),
])
for e in EVENTS:
    if e['label'] == 'The Thaali seal their frontier': e['slug'] = 'sealing-of-the-thaali-frontier'

# ---- the Voor in the Atlas (Lewis, 22 November 2026): the hearth yards, the Legion's hearth groups by period (at home,
# on the Gulf line, on the frontiers, in exile and restored), the lost world, the dead world of the Ommath, and the
# Ximpok years and the restoration on the timeline. The Legion's grounds are globe sites (planets/places.py SITES).
def _hy(sid, name, at, a, b=None, gap=None):
    f = {'name': name, 'kind': 'yard', 'at': at, 'from': a, 'slug': 'hearth-yards'}
    if b: f['to'] = b
    if gap: f['gap'] = gap
    FEATURES.setdefault(sid, []).append(f)
_hy('ximpok', 'Vi Simni hearth yard', 2, 1350, ym(2339, 8, 14))
_hy('ximpok', 'Vi Simni hearth yard (rebuilt)', 2, 2475)
_hy('swur', 'Swur hearth yards', 2, 2326, ym(2335, 4, 20))
_hy('swur', 'Swur hearth yards (rebuilt)', 2, 2475)
_hy('kastaba', 'Kastaba yard', 2, 1745, ym(2335, 2, 3))
_hy('haedus', 'Legion Gulf repair yards', 3, 1382, ym(2334, 9, 12))
_hy('sol', 'Europa hearth yard (Voor licence)', [5, 1], 2451, 2475.5)
VH = 'Voor Legion'
def _hg(sid, name, a, b, n, strength, slug_='voor-legion'):
    _navy(sid, name, VH, 'voor', a, b, n, strength, slug_)
# at home: Exedor
_hg('exedor', 'Home formations', 1328, 2335.2, 5, 'The First of the Fires and the interior formation\'s hearths, under the High Command at Hiverion', 'high-command-voor-legion')
_hg('exedor', 'Defence of Exedor', 2335.2, 2336.2, 15, 'Fifteen hearths led by the First of the Fires, with the High Commander aboard', 'battle-of-exedor-2336')
_hg('exedor', 'Defence of Exedor', 2336.2, 2338.34, 9, 'The hearths left after the Battle of Exedor, sortieing in pairs from under the shield', 'siege-of-hiverion')
_hg('exedor', 'Hearths under the failing shield', 2338.34, 2341.05, 5, 'Five hearths under Hiverion\'s failing shield, without a High Command', 'voor-confederacy')
_hg('exedor', 'Defence of Hiverion', 2425.0, 2427.62, 7, 'Seven hearths and 3 million Legionaries behind a shield rebuilt with Republic generators', 'frontier-generals')
_hg('exedor', 'The restored Legion', 2460.0, 2476.0, 3, 'The restored Legion\'s home hearths at Hiverion', 'restored-voor-confederacy')
_hg('exedor', 'The restored Legion', 2476.0, 2490.0, 5, 'The home hearths, with the first Aquilifers from the rebuilt yards', 'restored-voor-confederacy')
_hg('exedor', 'The restored Legion', 2490.0, 2515, 8, 'The home hearths of a Legion of twenty under the Council', 'restored-voor-confederacy')
# the Gulf line, 2324 to 2335
_hg('haedus', 'Haedus group', 2324.0, 2327.0, 2, 'The Legion\'s Gulf formation at Haedus, moving into the Gulf from 2324', 'voor-legion')
_hg('haedus', 'Haedus group', 2327.0, 2334.09, 5, 'Five hearths under General Volar Vex, led by the Keeper of the Threshold', 'battle-of-the-mog')
_hg('swur', 'Swur group', 2330.0, 2334.38, 5, 'Five hearths under General Ahnar Varn', 'second-battle-of-media')
_hg('swur', 'Swur group', 2334.38, 2335.26, 4, 'The four hearths that came back from Media without a General', 'fall-of-kastaba-and-swur')
_hg('kastaba', 'Kastaba group', 2324.0, 2335.09, 2, 'The Legion\'s Gulf formation at Kastaba', 'fall-of-kastaba-and-swur')
_hg('ximpok', 'Ximpok hearths', 2338.3, 2339.63, 3, 'Three hearths at Vi Simni with the Council; two destroyed and one struck in August 2339', 'voolar-surrender')
_hg('aethos', 'Aethos hearths', 2337.5, 2341.05, 2, 'Two hearths blockaded at Aethos from October 2339', 'voor-confederacy')
# the Veil frontier
_hg('qad-vhi', 'Veil frontier hearths', 1438, 2335.2, 10, 'The Veil frontier\'s hearths under its two Generals, watching the clans beyond the Veil', 'frontier-generals')
_hg('qad-vhi', 'The frontier\'s twenty', 2344.0, 2415.8, 20, 'The twenty hearths of the treaty cap under the frontier Generals, the Legion\'s unofficial High Command, at their seat at Qad Vhi', 'frontier-generals')
_hg('qad-vhi', 'The frontier\'s twenty', 2415.8, 2416.4, 14, 'The fourteen hearths left after the first engagement with the Khan\'s monoliths', 'voor-campaign')
_hg('aethos', 'Defence of Vur Duri', 2420.2, 2422.44, 21, 'Twenty-one hearths, nine old and twelve of the Tribune class, under General Seren Vaadh', 'fall-of-vur-duri')
# exile and the restoration
_hg('haedus', 'The last hearth', 2427.65, 2428.6, 1, 'The one hearth that reached Haedus with its field gone, escorting the last refugee convoy', 'voor-worlds-under-the-red-khanate')
_hg('aethos', 'The Long Siege', 2455.4, 2460.0, 4, 'Four hearths and the Legion\'s ground forces with the Republic\'s Southern Command, siege by siege', 'reclamation-of-the-voor-worlds')
_hg('omaggus', 'Veil\'s eastern approaches', 2466.5, 2476.0, 2, 'The Legion\'s hearths on the Veil\'s eastern approaches under the Fevarian Accords', 'fevarian-accords')
_hg('omaggus', 'Veil\'s eastern approaches', 2476.0, 2490.0, 5, 'The Legion\'s hearths on the Veil\'s eastern approaches under the Fevarian Accords', 'fevarian-accords')
_hg('omaggus', 'Veil\'s eastern approaches', 2490.0, 2515, 10, 'Half the Legion of 2510 on the Veil\'s eastern approaches, its Commander in the Accords\' Joint Command', 'fevarian-accords')
# the lost world, the first colony and the dead world of the Ommath
note_body('batraq', 4, 'Dead world', 'Durnhaal, the Voor world burned in the Fevarian wars; its name laid down. Seal-stones of about 400 clans recovered in 2470')
note_body('ladiom', 2, 'Cold grassland world', 'Ladiom II, the first Voor colony beyond Exedor; burned in the Fevarian wars and resettled about 760 Voor years before contact')
note_body('izar', 3, 'Ruin world', 'Izar III, the burned world of the Ommath, the Fevarians\' prey before the Voor; a protected site from 2470')
for _sid, _pl in (('batraq', 4), ('ladiom', 2), ('izar', 3)):
    BODIES[_sid][-1]['slug'] = {'batraq': 'durnhaal', 'ladiom': 'ladiom', 'izar': 'ommath'}[_sid]
EVENTS.extend([
    ev(ym(2344), 'The frontier Generals make Qad Vhi their seat', 'qad-vhi', 'polity', 'frontier-generals'),
    ev(ym(2345, 12, 21), 'Military government of Hiverion ends', 'exedor', 'polity', 'voor-confederacy-under-the-treaty-of-ximpok'),
    ev(ym(2385), 'Clan raids on the Veil worlds resume', 'qad-vhi', 'battle', 'frontier-generals'),
    ev(ym(2391), 'The Council asks to lift the hearth cap', 'ximpok', 'polity', 'voor-confederacy-under-the-treaty-of-ximpok'),
    ev(ym(2392), 'Two frontier hearths lost to a clan fleet', 'qad-vhi', 'battle', 'frontier-generals'),
    ev(ym(2415, 10), 'The frontier hearths meet the Khan', 'qad-vhi', 'battle', 'voor-campaign'),
    ev(ym(2416, 3, 14), 'Fifteen Tribune hearths laid down at Hiverion', 'exedor', 'polity', 'hearth-yards'),
    ev(ym(2453, 12, 21), 'The Kindling relit', 'exedor', 'polity', 'voor-rites'),
    ev(ym(2455), 'The Legion\'s sealed histories opened', 'exedor', 'polity', 'early-history-of-the-voor'),
    ev(ym(2460), 'Legion service made voluntary', 'exedor', 'polity', 'legion-service'),
    ev(ym(2462, 3, 4), 'Voor Reconstruction Agreement', 'exedor', 'treaty', 'restored-voor-confederacy'),
    ev(ym(2464), 'Excavation of the Ommath world begins', 'izar', 'survey', 'ommath'),
    ev(ym(2470), 'The Legion lands on Durnhaal', 'batraq', 'survey', 'durnhaal'),
    ev(ym(2476), 'First Voor-grown hearths since 2420', 'swur', 'polity', 'hearth-yards'),
])
for e in EVENTS:
    if e['label'] in ('Fall of Vur Duri',): e['slug'] = 'fall-of-vur-duri'
    if e['label'] == 'Vi Simni submits': e['slug'] = 'voor-worlds-under-the-red-khanate'
    if e['label'] == 'Fevarian Accords signed': e['slug'] = 'fevarian-accords'

# every battle's wreckage, each side's losses, and the article it opens (atlas/battles.py)
import battles as BT
def _at(sid, where):
    if where == 'pillai' or isinstance(where, (int, list)): return where
    w = next((w for w in worlds if w['sys'] == sid and w['name'] == where and w.get('pl')), None)
    return w['pl'] if w else 'pillai'
_mw = {'m': marches, 'w': west_marches, 'n': north_m}
for key, y, title, lost, n in BT.MAWEER_BATTLES:
    sl = 'fall-of-the-thaali-marches' if title.startswith(('Fall of', 'Siege of')) else slug(title)
    BT.BATTLES.append((_mw[key[0]][int(key[1:])]['id'], y, 'pillai', sl, title, [(BT.MAWEER, 'maweer', n, lost)]))
for sid, y, where, slug_, title, sides in BT.BATTLES:
    fs = FEATURES.setdefault(sid, [])
    wr = next((f for f in fs if f['kind'] == 'wreck' and not f.get('title') and abs(f['from'] - y) < 0.15), None)
    if not slug_:
        ev = next((e for e in EVENTS if e["sys"] == sid and abs(e['y'] - y) < 0.5 and e.get('slug')), None)
        slug_ = ev['slug'] if ev else None
    out = []
    mono = None
    if wr:
        mono = {'name': BT.KH, 'style': 'mono', 'n': wr['n'], 'lost': '%d monolith%s' % (wr['n'], 's' if wr['n'] > 1 else '') +
                (' (%s)' % ', '.join(wr['named']) if wr.get('named') else ''), 'clans': wr['clans']}
    for nm, st, n, lost in sides:
        if st == 'fev' and mono:
            mono['lost'] += '; ' + lost; mono['n2'] = n
        else:
            out.append({'name': nm, 'style': st, 'n': n, 'lost': lost})
    if mono: out.append(mono)
    f = wr or {'kind': 'wreck', 'from': y, 'n': 0}
    if not wr: fs.append(f)
    f.update({'title': title, 'name': title, 'battle': title, 'at': _at(sid, where), 'sides': out})
    if slug_: f['slug'] = slug_
for nm, side, st, where, a, b, n, strength, slug_ in BT.FLEETS:
    FEATURES.setdefault('sol', []).append({'name': nm, 'kind': 'navy', 'side': side, 'style': st, 'at': where, 'from': a, 'to': b,
                                           'n': n, 'strength': strength, 'slug': slug_})
for sid, fs in FEATURES.items():
    for f in fs:
        if f['kind'] == 'wreck' and not f.get('sides'):
            f['title'] = 'Wrecks of ' + f['battle']
            WSLUG = {'the Thaali marches': 'fall-of-the-thaali-marches', 'the western marches': 'fall-of-the-thaali-marches',
                     'the northern Thaali campaign': 'fall-of-the-thaali-marches', 'the Thaali offensive': 'thaali-offensive', 'the Hunt': 'hunt-in-the-marches'}
            if f['battle'] in WSLUG: f['slug'] = WSLUG[f['battle']]
            f['sides'] = [{'name': BT.KH, 'style': 'mono', 'n': f['n'], 'lost': '%d monolith%s' % (f['n'], 's' if f['n'] > 1 else '') +
                           (' (%s)' % ', '.join(f['named']) if f.get('named') else ''), 'clans': f['clans']}]

# ---- deep time (Lewis, 22 November 2026): the timeline reaches back to 1000, the century before the Fevarian wars.
# Voor years before contact convert at 1.1 Earth years each from 2317.75. Every claim the sheet starts in 1900 reaches
# back to 1000; the Voor systems follow the Voor's own history: the six worlds (the Voor worlds) to the founding of the
# Confederacy in 1438, Ladiom's first colony and Durnhaal burned in the wars, then the expansion outward from Exedor.
DEEP = 1000
VOOR_DEEP = {'exedor': [(DEEP, 'voorsix')], 'ximpok': [(DEEP, 'voorsix')], 'aethos': [(DEEP, 'voorsix')], 'romston': [(DEEP, 'voorsix')],
             'ladiom': [(DEEP, 'voorsix'), (1108.4, None), (1482, 'voor')], 'batraq': [(DEEP, 'voorsix'), (1119.0, None), (1438.5, 'voor')],
             'haedus': [(1383, 'voorsix')], 'kastaba': [(1746, 'voor')], 'myrum': [(1790, 'voor')],
             # the expansion reached the Thaali frontier about 273 Voor years before contact
             'faenov': [(2008, 'voor')], 'wicklar': [(2010, 'voor')], 'wuae': [(2012, 'voor')]}
_ex = by['exedor']; _vs = [s for s in systems if s['region2235'] == 'voor']
_dist = {s['id']: math.dist((s['x'], s['y'], s['z']), (_ex['x'], _ex['y'], _ex['z'])) for s in _vs}
_d0, _d1 = min(_dist.values()), max(_dist.values())
for s in systems:
    o = own[s['id']]
    if s['region2235'] == 'voor':
        if o and o[0]['from'] == 1900 and o[0]['p'] == 'voor': o.pop(0)
        sched = VOOR_DEEP.get(s['id']) or [(round(1450 + (_dist[s['id']] - _d0) / (_d1 - _d0) * 560, 1), 'voor')]
        if any(p == 'voorsix' for _, p in sched) and not any(y == 1438.5 and p == 'voor' for y, p in sched) and s['id'] != 'ladiom':
            sched = sched + [(1438.5, 'voor')]
        o[:0] = [{'from': y, 'p': p} for y, p in sched]
    elif o and o[0]['from'] == 1900:
        o[0]['from'] = DEEP
    o.sort(key=lambda e: e['from'])
# native worlds stand from the start; the Voor's own worlds from their settlement
for w in worlds:
    if w.get('native') and w['settled'] <= 1900: w['settled'] = DEEP
    if w['sys'] in ('exedor', 'ximpok', 'aethos') and w.get('native'): w['settled'] = DEEP
    if w['name'] == 'Indata Mog': w['settled'] = 1383
    # humanity learned of the Voor worlds in 2318: they stay off the map from 2050 until then, as before
    if w['sys'] in ('exedor', 'ximpok', 'aethos', 'haedus') and w.get('native'): w['known'] = 2318.3
BURNED_EXTRA += [('izar', 'Izar III', 1000.5), ('ladiom', 'Ladiom II', 1108.4), ('batraq', 'Durnhaal', 1119.0)]
def _dev(y, label, sys, kind, slug):
    assert sys in by, sys
    return {'y': y, 'label': label, 'sys': sys, 'kind': kind, 'slug': slug}
EVENTS.extend([
    _dev(1000.5, 'The Fevarian clans take the Ommath', 'izar', 'burning', 'ommath'),
    _dev(1020.0, 'A survey ship of Vi Simni finds the Ommath dead', 'izar', 'survey', 'ommath'),
    _dev(1108.4, 'The clans burn Ladiom\'s first colony', 'ladiom', 'burning', 'ladiom'),
    _dev(1108.6, 'The four worlds found the Legion', 'exedor', 'polity', 'fevarian-wars'),
    _dev(1119.0, 'Durnhaal burned', 'batraq', 'burning', 'durnhaal'),
    _dev(1328.0, 'The First of the Fires grown at Hiverion', 'exedor', 'polity', 'hearth-yards'),
    _dev(1338.7, 'The nine-day hold at Ladiom', 'ladiom', 'battle', 'ladiom'),
    _dev(1383.0, 'The Keeper of the Threshold founds Indata Mog', 'haedus', 'world', 'indata-mog'),
    _dev(1432.2, 'The last clan fleet in the Gulf destroyed at Batraq', 'batraq', 'battle', 'fevarian-wars'),
    _dev(1438.5, 'The Voor Confederacy founded', 'exedor', 'polity', 'early-history-of-the-voor'),
    _dev(1482.0, 'Ladiom resettled', 'ladiom', 'world', 'ladiom'),
    _dev(1746.0, 'Kastaba settled', 'kastaba', 'world', 'voor-expansion'),
    _dev(1790.0, 'Myrum settled', 'myrum', 'world', 'voor-expansion'),
    _dev(1856.0, 'General summons against the clans of the Veil', 'qad-vhi', 'battle', 'legion-service'),
    _dev(2017.5, 'The Voor meet the Thaali at Zom', 'zom', 'survey', 'early-history-of-the-voor'),
    _dev(2019.7, 'The first Thaali envoy received at Hiverion', 'exedor', 'polity', 'high-council-voor'),
    _dev(2098.0, 'The last general summons before contact', 'qad-vhi', 'battle', 'legion-service'),
    _dev(2186.0, 'The second Thaali reception at Hiverion', 'exedor', 'polity', 'high-council-voor'),
])
EVENTS.sort(key=lambda e: e['y'])
# hidden on the Atlas until humanity meets them (Lewis, 22 November 2026): drop any event in a system held by a power
# humanity had not yet met; that history lives in the wiki's articles. The deep owners above stay in the data.
_CONTACT = {'voor': 2317.75, 'voorsix': 2317.75, 'maweer': 2320.5, 'freehold': 2320.5, 'fevclans': 2320.5, 'raidzone': 2320.5,
            'dwaii': 2320.5, 'kadur': 2320.5, 'ossathi': 2457.0, 'veren': 2457.0, 'kaltam': 2456.3, 'duresh': 2457.0}
def _owner(sid, y):
    cur = None
    for e in own.get(sid, []):
        if e['from'] <= y: cur = e['p']
        else: break
    return cur
_n0 = len(EVENTS)
EVENTS[:] = [e for e in EVENTS if e['y'] >= 2050 and not (_owner(e['sys'], e['y']) in _CONTACT and e['y'] < _CONTACT[_owner(e['sys'], e['y'])])]
print('pre-contact events dropped:', _n0 - len(EVENTS))

data = {
    'meta': {
        'source': 'Traced from Lewis Brewer\'s reference map 2235.12.10; 1 unit = 1 light year; Sol at origin.',
        'range': [2050, 2515], 'start': 2510,
    },
    'polities': POLITIES,
    # Powers fade in when humanity learns of them: the Voor at contact in 1 October 2317's
    # approach, the Thaali and (through the Voor) the Fevarians by 2320.
    'contact': {'voor': 2317.75, 'voorsix': 2317.75, 'maweer': 2320.5, 'freehold': 2320.5, 'fevclans': 2320.5, 'raidzone': 2320.5, 'dwaii': 2320.5, 'kadur': 2320.5, 'ossathi': 2457.0, 'veren': 2457.0, 'kaltam': 2456.3, 'duresh': 2457.0},
    'systems': [{**s, 'own': own[s['id']]} for s in systems],
    'worlds': worlds,
    'planetNames': PLANET_NAMES,
    'burned': [{'sys': a, 'name': b, 'y': c} for a, b, c in BURNED + BURNED_EXTRA],
    'bodies': BODIES,
    'features': FEATURES,
    'clans': CLANS,
    'events': sorted(EVENTS, key=lambda e: e['y']),
    'captions': [{'from': a, 'to': b, 'text': t} for a, b, t in CAPTIONS],
    'regions': [
        {'name': 'Ciriban Gulf', 'near': ['golba', 'media', 'swur', 'ciriban']},
        {'name': 'Ibannic Veil', 'near': ['kuma', 'banagho', 'omaggus', 'ijaagin'], 'toward': 'ushars-well'},
        {'name': 'Zadanis Void', 'near': ['lishval', 'okul', 'gorim', 'targon']},
        {'name': 'Shadow Nebula', 'near': ['asmore', 'sorcimax', 'uldor', 'quannaga']},
        {'name': 'Nythran Void', 'near': ['ponnell', 'brallix', 'ellamir', 'galurum']},
        # on the far side of the Rubin Void (book 7.2 and 15.9)
        {'name': 'Mardak Cluster', 'near': [slug(n) for n, *_ in EXTRA['mardak']], 'stack': True},
        {'name': 'Rubin Void', 'near': ['halvek', 'imrith', 'oru-tenna', 'selund']},
    ],
    # The Republic's administrative sectors, from the colony sheet
    'sectors': [{'name': n, 'flag': slug(n) + '.png', 'members': sorted(m for m, s in SHEET_SECTOR.items() if s == n)}
                for n in ('Sol Sector', 'Binami Sector', 'Saolea Sector', 'Geronth Sector', 'Gagarin Sector')],
}
for r in data['regions']:
    if 'at' in r:
        r['x'], r['y'] = r.pop('at'); continue
    pts = [by[i] for i in r['near']]
    r['x'] = round(sum(p['x'] for p in pts) / len(pts), 2)
    r['y'] = round(sum(p['y'] for p in pts) / len(pts), 2)
    if r.get('toward'):          # move the label halfway toward a named system
        o = by[r.pop('toward')]
        r['x'] = round((r['x'] + o['x']) / 2, 2); r['y'] = round((r['y'] + o['y']) / 2, 2)
    del r['near']

# Jump routes: every pair within a Pillai drive's 8 ly, then the shortest links that join
# what is left, so that every star can be reached from every other. The Rubin Void is
# different: its gravity moves the Pillai radius, so only the routes charted in the
# Expansion Era count as routes (Imrith; Teshun and on to Vane), and they stay hazardous.
# Every other approach into the void is drawn as an uncharted hazard.
RUBIN = {slug(n) for n, *_ in EXTRA['rubin']}
for sid in RUBIN:
    by[sid]['hazard'] = 'Dark-matter masses move the Pillai radius. Jumps are unreliable.'
# Ushar's Well, in the Veil, is a black hole. Its name is the prophetess Ushar Vel's.
by['ushars-well']['blackhole'] = True
by['ushars-well']['stars'] = 1
by['ushars-well']['hazard'] = 'Black hole. Its well holds the Pillai radius far out, and no jump is charted inside it.'
N = len(systems)
parent = list(range(N))
def find(i):
    while parent[i] != i:
        parent[i] = parent[parent[i]]; i = parent[i]
    return i
ix = {s['id']: i for i, s in enumerate(systems)}
routes, seen = [], set()
def link(i, j, kind=None):
    key = (min(i, j), max(i, j))
    if key in seen: return
    seen.add(key)
    routes.append([systems[i]['id'], systems[j]['id'], round(dist(systems[i], systems[j]), 1)] + ([kind] if kind else []))
    parent[find(i)] = find(j)
outside = lambda i: systems[i]['id'] not in RUBIN

# 1. The Gulf's lanes, after Lewis's "Iron Gulf" map (2200 to 2233 in the old dating):
#    Ciriban to Haedus and Swur to Media at the centre, the core worlds to the Sectors, the
#    Voor worlds from Exedor south to the Veil.
LANES = """sol-procyon sol-alpha-centauri procyon-binami procyon-talandra talandra-nomotar nomotar-myrum
talandra-binami binami-ijax ijax-ciriban binami-yildun yildun-saolea brink-yildun ciriban-izar izar-bashpit bashpit-ijax
ciriban-ajam ajam-stiridon ciriban-haedus haedus-kastaba kastaba-myrum haedus-faenov haedus-exedor
exedor-faenov faenov-wuae wuae-cheleb faenov-hydrobius faenov-zom exedor-ximpok exedor-leesak leesak-swur
ximpok-aethos ximpok-roschon roschon-batraq batraq-swur swur-media media-uthan uthan-hhabban hhabban-feonus
feonus-achernar achernar-omaggus omaggus-batraq omaggus-banagho banagho-aethos aethos-ksora aethos-nithascal
aethos-ceyecarro saolea-taggalion taggalion-veyer veyer-hhabban ksora-umik umik-beta-aquilae umik-ijaagin""".split()
def pair(lane):
    parts = lane.split('-')
    for cut in range(1, len(parts)):                    # split "a-b" where both halves are system ids
        a_, b_ = '-'.join(parts[:cut]), '-'.join(parts[cut:])
        if a_ in ix and b_ in ix: return ix[a_], ix[b_]
    raise AssertionError(lane)
# Lewis's hand edits to the network: lanes he wants and lanes he does not.
EXTRA_LANES = """dhur-ka-dothom dothom-ellamir lytirim-grumium cygni-ijax wuae-wicklar wicklar-cazzabius azak-hoeddim ceyecarro-hoeddim
kuma-ijaagin qad-vhi-ijaagin""".split()
NO_LANES = "emim-maasym lalande-maasym lytirim-dastamon cygni-myrum cygni-ross-alpha".split()
for lane in NO_LANES:
    i_, j_ = pair(lane); seen.add((min(i_, j_), max(i_, j_)))
for lane in LANES + EXTRA_LANES:
    link(*pair(lane))
# The Iron Gulf map's own area follows its lanes only; elsewhere the network is a relative
# neighbourhood graph (two stars are linked when no third star lies closer to both), which
# gives the same sparse, lane-like structure across the rest of the map.
GULF = set("""sol procyon alpha-centauri tem torovil talandra brink binami bashpit izar ijax ciriban haedus ajam
stiridon trab yildun saolea ladiom golba esmyke hoeddim exedor azak leesak swur media taggalion uthan veyer
ximpok ceyecarro batraq roschon hhabban aethos ksora nithascal banagho umik feonus achernar omaggus
beta-aquilae kuma ijaagin qad-vhi kastaba myrum nomotar faenov wuae""".split())
import numpy as np
P = np.array([[s['x'], s['y'], s['z']] for s in systems])
D = np.sqrt(((P[:, None, :] - P[None, :, :]) ** 2).sum(-1))
for i in range(N):
    if not outside(i): continue
    for j in range(i + 1, N):
        if not outside(j) or D[i, j] > 13: continue
        if systems[i]['id'] in GULF and systems[j]['id'] in GULF: continue
        if np.any(np.maximum(D[i], D[j]) < D[i, j] - 1e-9): continue
        link(i, j)
# 2. Whatever is still cut off joins by its shortest link, so every star can be reached.
#    The Mardak Cluster lies across the void and is joined only by the void's own routes below.
MARDAK = {slug(n) for n, *_ in EXTRA['mardak']}
same_side = lambda i, j: (systems[i]['id'] in MARDAK) == (systems[j]['id'] in MARDAK)
pairs = sorted((D[i, j], i, j) for i in range(N) for j in range(i + 1, N) if outside(i) and outside(j) and same_side(i, j))
for d_, i, j in pairs:
    if find(i) != find(j): link(i, j)
# 3. The Rubin Void: the charted routes, then hazards for the rest.
def nearest_outside(sid):
    return min((k for k in range(N) if outside(k)), key=lambda k: D[k, ix[sid]])
link(ix['luhman'], ix['imrith'], 'charted')
# The Gagarin's road (2310), from the ancients' own lattice: Daranma, Halvek, Morrow's Light
# and on into the Cluster. Daranma also reaches Imrith.
link(ix['daranma'], ix['imrith'], 'charted')
link(ix['daranma'], ix['halvek'], 'charted')
link(ix['halvek'], ix['morrows-light'], 'charted')
link(ix['morrows-light'], min((ix[m] for m in MARDAK), key=lambda k: D[k, ix['morrows-light']]), 'charted')
link(nearest_outside('teshun'), ix['teshun'], 'charted')
link(ix['teshun'], ix['vane'], 'charted')
for d_, i, j in sorted((D[i, j], i, j) for i in range(N) for j in range(i + 1, N)):
    if find(i) != find(j): link(i, j, 'hazard')
assert len({find(i) for i in range(N)}) == 1
data['routes'] = routes
print('routes', len(routes), 'longest link', max(r[2] for r in routes))

# ---- flags shown beside worlds in the system viewer: [from-year, [flag files]] per world
SOL_SLUGS = {'Luna': 'luna', 'Mars': 'mars', 'Io': 'io', 'Europa': 'europa', 'Ganymede': 'ganymede', 'Callisto': 'callisto'}
for w in worlds:
    if w['sys'] == 'sol' and w['name'] in SOL_SLUGS: w['slug'] = SOL_SLUGS[w['name']]
UNIFY = 2283.416   # New Luxor, 1 June 2283
FED = 'united-nations-of-earth.png'
USR = 'unified-solar-republic.png'   # 1 January 2341
EARTH_STATES = ['united-states-of-america.svg', 'peoples-republic-of-china.svg', 'european-federation.svg',
                'republic-of-india.svg', 'pacific-union.svg', 'arabic-league.png', 'canada.svg',
                'federative-republic-of-brazil.svg', 'argentine-republic.svg', 'korean-republic.svg', 'russian-federation.svg']
CAC = 'central-african-confederation.svg'
FLAGS = {
    'sol:Earth': [[1900, EARTH_STATES], [2057.62, EARTH_STATES[:6] + [CAC] + EARTH_STATES[6:]], [UNIFY, [FED]], [2341.0, [USR]]],
    # the Solar War: who held each world (the wiki's articles). The Jovian Free Colonies from March 2220, the
    # Martian-Jovian Confederation from September 2224, the Lunar Revolutionary Administration on the far side 2227 to
    # 2233; the United Nations' provisional governments on the retaken worlds until the United Nations of Earth.
    'sol:Luna': [[2063, ['peoples-republic-of-china.svg', 'european-federation.svg', 'united-states-of-america.svg']],
                 [2227.84, ['peoples-republic-of-china.svg', 'european-federation.svg', 'united-states-of-america.svg', 'lunar-revolutionary-administration.svg']],
                 [2233.1, ['peoples-republic-of-china.svg', 'european-federation.svg', 'united-states-of-america.svg']], [UNIFY, ['luna.png']]],
    'sol:Mars': [[2076, ['european-federation.svg']], [2079.7, ['european-federation.svg', 'united-states-of-america.svg']],
                 [2224.71, ['european-federation.svg', 'united-states-of-america.svg', 'martian-jovian-confederation.svg']],
                 [2225.2, ['united-states-of-america.svg', 'martian-jovian-confederation.svg']],
                 [2226.88, ['martian-jovian-confederation.svg', 'mars.png']], [2246.84, ['united-nations.svg']], [UNIFY, ['mars.png']]],
    'sol:Io': [[2100, ['republic-of-india.svg']], [2220.17, ['free-io.svg', 'league-for-jovian-rule.png']],
               [2224.71, ['free-io.svg', 'martian-jovian-confederation.svg']], [2249.99, ['united-nations.svg']], [UNIFY, ['io.png']]],
    'sol:Europa': [[2100, ['european-federation.svg']], [2220.17, ['free-europa.svg', 'league-for-jovian-rule.png']],
                   [2224.71, ['free-europa.svg', 'martian-jovian-confederation.svg']], [2252.3, ['united-nations.svg']], [UNIFY, ['europa.png']]],
    'sol:Ganymede': [[2100, ['peoples-republic-of-china.svg']], [2220.17, ['free-ganymede.svg', 'league-for-jovian-rule.png']],
                     [2224.71, ['free-ganymede.svg', 'martian-jovian-confederation.svg']], [2252.3, ['united-nations.svg']], [UNIFY, ['ganymede.png']]],
    'sol:Callisto': [[2100, ['united-states-of-america.svg']], [2220.17, ['free-callisto.svg', 'league-for-jovian-rule.png']],
                     [2224.71, ['free-callisto.svg', 'martian-jovian-confederation.svg']], [2251.7, ['united-nations.svg']], [UNIFY, ['callisto.png']]],
}
# any other world with its own flag file shows it from settlement
FLAG_DIR = HERE.parent / 'static' / 'flags'
have = {f.rsplit('.', 1)[0]: f for f in os.listdir(FLAG_DIR)} if FLAG_DIR.exists() else {}
for w in worlds:
    k = w['sys'] + ':' + w['name']
    if k not in FLAGS and w.get('slug') in have: FLAGS[k] = [[w['settled'], [have[w['slug']]]]]
data['flags'] = FLAGS
# a non-human power with a banner file flies it over its worlds and keys it in the legends;
# the Voor banner is a roundel (the Hearth), drawn round rather than as a 3:2 flag
for k, pol in POLITIES.items():
    if k in ('earth', 'une', 'usr'): continue
    if pol.get('slug') in have: pol['flag'] = have[pol['slug']]
data['roundFlags'] = ['voor-confederacy.svg']
# the Fevarian powers fly tall hanging banners; their square heads stand in for them on the map and in legends
data['squareFlags'] = sorted(pol['flag'] for pol in POLITIES.values() if pol.get('flag') and os.path.exists(FLAG_DIR / (pol['flag'].rsplit('.', 1)[0] + '-banner.png')))

# refresh systems so later fields (hazards, black holes) reach the data
data['systems'] = [{**s, 'own': own[s['id']]} for s in systems]
out = HERE / 'atlas-data.json'
json.dump(data, open(out, 'w'), separators=(',', ':'))
print('systems', len(systems), 'worlds', len(worlds), 'events', len(EVENTS), '->', out, out.stat().st_size, 'bytes')
print('D\'Hovar worlds:', dhovar)
print('marches:', [s['id'] for s in marches])
print('north Voor:', [s['id'] for s in north_v])
print('north Thaali:', [s['id'] for s in north_m])
print('extent x', min(s['x'] for s in systems), max(s['x'] for s in systems), 'y', min(s['y'] for s in systems), max(s['y'] for s in systems))
