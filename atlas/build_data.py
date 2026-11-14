import os
"""Build atlas-data.json: 194 systems traced from the 2235.12.10 reference map,
their ownership through time, settled worlds and dated events.

Positions: the map is 7000 px wide at 35 px per light year. Sol is the origin.
Heights above the plane are invented and kept small (seeded, so stable).
Ownership is reconstructed from the Expanded Edition. Anything the book does not
fix (claim years of minor systems, which Voor and Maweer systems the Khanate held)
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
    'maweer':   {'name': 'Maweer Caretakers', 'color': '#62BF6E', 'slug': 'maweer'},
    'freehold': {'name': 'Northern Fevarian Freeholds', 'color': '#A57BD6'},
    'fevclans': {'name': 'Southern Fevarian Freeholds', 'color': '#8E5E78'},
    'khanate':  {'name': 'Red Khanate', 'color': '#D2493E', 'slug': 'red-khanate'},
    'eight':    {'name': 'Council of the Eight Khans', 'color': '#E2733C'},
    'remnant':  {'name': 'Khanate remnants', 'color': '#A44F48'},
    'word':     {'name': 'Khanate of the Word', 'color': '#B24C8F'},
    'dashan':   {'name': 'Khanate of D\'Ashan', 'color': '#B93838'},
    'veilclans': {'name': 'The Veil Clans', 'color': '#9A6650'},
    'dtarik':   {'name': 'Khanate of D\'Tarik', 'color': '#D9667A'},
    'dsethen':  {'name': 'Khanate of D\'Sethen', 'color': '#C9643C'},
    'dhovar':   {'name': 'Khanate of D\'Hovar', 'color': '#D19A4A'},
    'dwaii':    {'name': 'Dwaii', 'color': '#E2C65C', 'slug': 'dwaii'},
    'kadur':    {'name': 'Ka-Dur League', 'color': '#E58CC2', 'slug': 'ka-dur'},
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
        'id': slug(s['name']), 'name': s['name'],
        'x': round(x, 2), 'y': round(-y, 2), 'z': z,   # map y grows downward; flip so north is +y
        'stars': max(1, min(3, len(s['pts']))),
        'region2235': s['region2235'],
    })
by = {s['id']: s for s in systems}

# ------------------------------------------------------------------ beyond the 2235 map
# The Veil (the Fevarians' own space), the Dwaii and the Ka-Dur lie south and south-west
# of the reference map. The book fixes only their relations: the Veil south of the
# Confederacy, its western edge on the Maweer's marches; the Dwaii and Ka-Dur on the
# Veil's far side, 60 to 100 ly from Haedius, the Dwaii reached first by the marches'
# far road and the Ka-Dur furthest (the book's distances changed to 60 to 100 ly to fit). Positions and every name but Ossath are invented.
EXTRA = {
    'veil': [('Dhen Ossa', -74, -80), ('Rhen Tal', -66, -86), ('Vesh Mar', -80, -72), ('Kasht', -60, -77),
             ('Tor Dhaan', -86, -84), ('Ashan Dur', -71, -92), ('Mareth Vel', -56, -88), ('Ul Sethen', -92, -76),
             ('Vharr', -63, -95), ('Drek Hul', -78, -97), ('Thul Ashra', -89, -91), ('Ossek', -54, -70),
             ('Varn Khet', -68, -70), ('Sel Tarik', -84, -101), ('Ushar\'s Well', -76, -66), ('Dhenmar', -62, -64)],
    'dwaii': [('Hwen', -106, -72), ('Ellui', -111, -78), ('Dwaimar', -103, -79)],
    # The Ka-Dur League lies west of the Dwaii, south of the Nythran Void. Ossath stands where
    # the map once had "Sethen's March". The Ka-Dur reach the Maweer by going round the
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
}
for region, lst in EXTRA.items():
    if region == 'rubin':
        rng.random(); rng.random()    # the retired Sethen's March's draws, so later stars keep their depth
    for name, x, y in lst:
        s = {'id': slug(name), 'name': name, 'x': float(x), 'y': float(y), 'z': round(rng.uniform(-3.5, 3.5), 2),
             'stars': 1 + (1 if rng.random() < 0.2 else 0), 'region2235': region, 'invented': True}
        systems.append(s); by[s['id']] = s

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
SHEET_SECTOR['yildun'] = 'Saolea Sector'
SHEET_SECTOR['hadriccus'] = 'Gagarin Sector'
SHEET_SECTOR['zarqon'] = 'Geronth Sector'
SHEET_SECTOR['trab'] = 'Binami Sector'
SHEET_SECTOR['esmyke'] = 'Saolea Sector'
SHEET_SECTOR['golba'] = 'Saolea Sector'

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
# The Maweer reach west across the Nythran Void's northern rim to Ellamir and Saonus.
WEST_M = ['ellamir', 'guhur', 'osellus', 'hocry', 'kastra', 'saonus', 'howoz', 'polaris', 'rovannic',
          'tethell', 'duhr', 'fir-mathrioz', 'halax', 'eriga', 'kazoo']
for k in WEST_M:
    by[k]['region2235'] = 'maweer'

def dist(a, b):
    return math.dist((a['x'], a['y'], a['z']), (b['x'], b['y'], b['z']))

# ------------------------------------------------------------------ ownership
own = {s['id']: [] for s in systems}   # list of [from, polity, note]

def set_owner(sid, year, polity, note=None, derived=False):
    e = {'from': year, 'p': polity}
    if note: e['note'] = note
    if derived: e['derived'] = True
    own[sid].append(e)

# Human claims. Explicit dates from Part Seven and Eight.
# Claim years the book states; the sheet supplies the rest.
BOOK_CLAIMS = {
    'sol': 1900, 'procyon': ym(2302, 3, 3), 'torovil': 2302, 'barnards-star': 2303, 'talandra': 2308,
    'yildun': 2307, 'sirius': 2312, 'daranma': 2313, 'saolea': 2316, 'cirban': 2317, 'nomotar': 2317,
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
for sid, y in [('myrum', ym(2333, 9, 12)), ('kastaba', ym(2333, 9, 12)), ('swur', ym(2333, 11)),
               ('achernar', ym(2333, 12)), ('haedus', ym(2334, 9, 12)), ('leesak', ym(2337, 4)),
               ('exedor', ym(2338, 5, 3))]:
    set_owner(sid, y, 'human', 'occupied')
for sid in ['swur', 'achernar', 'leesak', 'exedor']:
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
# The Maweer campaign, 2413 to 2417: the eleven marches on the Veil's approaches, and the
# northern Maweer systems nearest the freeholds. The Maweer retake them 2447 to 2449.
# The Khan came at them on two fronts: up from the Veil, and from the Ka-Dur round the
# Nythran Void by Dothom to Ellamir. Six marches on the Veil's side and five in the west make
# the book's eleven. The Maweer retake the southern six 2447 to 2449; the western five are
# still the Khan's when he dies and become the Khanate of D'Sethen.
maweer = [s for s in systems if s['region2235'] == 'maweer']
core = ('maweer', 'fejantris')
marches = sorted([m for m in maweer if m['id'] not in core and m['id'] not in WEST_M], key=lambda s: s['y'])[:6]
west_marches = [by[k] for k in ('ellamir', 'guhur', 'osellus', 'hocry', 'kastra')]
north_m = [m for m in maweer if m['id'] not in core and m not in marches and m['id'] not in WEST_M
           and math.hypot(m['x'] - fx, m['y'] - fy) < 30]
north_m.sort(key=lambda m: math.hypot(m['x'] - fx, m['y'] - fy))
for lst, note in ((marches, 'the marches'), (north_m, 'northern conquest')):
    for i, s in enumerate(lst):
        set_owner(s['id'], round(2413 + 4 * i / max(1, len(lst) - 1), 1), 'khanate', note, derived=True)
        back = round(2447.2 + 2 * i / max(1, len(lst) - 1), 1)
        if note == 'northern conquest' and i >= len(lst) - 2:
            back = ym(2449, 7, 15)      # the Word withdraws from the last two in July 2449
        set_owner(s['id'], back, 'maweer', derived=True)
for i, s in enumerate(west_marches):
    set_owner(s['id'], round(2413.3 + 3 * i / max(1, len(west_marches) - 1), 1), 'khanate', 'the western marches', derived=True)
WEST_MARCH_IDS = {s['id'] for s in west_marches}

# Part Twelve and Thirteen: the Khan in human space.
KHAN_TAKES = [
    ('myrum', ym(2428, 7, 9)), ('haedus', ym(2428, 9, 5)), ('kastaba', ym(2428, 9)),
    ('cirban', ym(2429, 1, 20)), ('media', ym(2430, 8)), ('uthan', ym(2430, 10)), ('hhabban', ym(2430, 10)),
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
    ('cirban', ym(2450, 5, 16)), ('saolea', ym(2450, 6, 22)), ('stiridon', ym(2450, 10)),
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

for sid in own:
    own[sid].sort(key=lambda e: e['from'])

# ------------------------------------------------------------------ worlds
# Worlds: the sheet's settled worlds, with the book's dates where they differ, plus the
# non-human worlds known from contact and the book's later settlements.
BOOK_DATES = {'Mars': ym(2076, 7, 27), 'Luna': ym(2063, 3, 21), 'Io': ym(2114, 3, 1), 'Europa': ym(2116), 'Ganymede': ym(2118), 'Callisto': ym(2120),
              'Côte d\'Azur': ym(2342, 4, 21)}
SPELL = {"Cote d'Azure": "Côte d'Azur", 'Nouveau Montreal': 'Nouveau Montréal', 'New Indata Mog': None, 'Earth': 'Earth'}
SLUGS = {'Dauntless': 'dauntless', 'Mardak Vol': 'mardak-vol-planet', 'Theia': 'theia', 'Bounty': 'bounty'}
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
        ('aethos', 'Vur Duri', 2318.3, None, None), ('ximpok', 'Vi Simni', 2318.3, None, None),
        ('binami', 'Binami II (Inari)', ym(2315, 6, 3), 'inari', (2, 0)),
        ('nomotar', 'Nomotar', ym(2320), None, (3, 0)), ('feonus', "Vel's Rest", ym(2467), None, (4, 0))]:
    d = {'sys': sid, 'name': w, 'settled': y}
    if sl: d['slug'] = sl
    if pl: d['pl'], d['moon'] = pl[0], bool(pl[1])
    if w in ('Hiverion', 'Indata Mog', 'Vur Duri', 'Vi Simni', 'Binami II (Inari)'): d['native'] = True
    if w == 'Indata Mog': d['biome'] = 'Steppe world'
    if w == 'Nomotar': d['biome'] = 'Barren world'
    worlds.append(d)
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
PLANET_NAMES = {'saolea': {2: 'Okeanos'}, 'cirban': {3: 'Marigot', 5: 'Grand Anse'}, 'procyon': {2: 'Phoenicia'}}
BURNED = [('procyon', 'Landfall', ym(2441, 11, 26)), ('yildun', 'Dauntless', ym(2444, 12, 3)),
          ('saolea', 'Theia', ym(2436, 9, 12)), ('veyer', 'Hualapai', ym(2437, 3)),
          ('nomotar', 'Nomotar', ym(2438, 8, 20)), ('talandra', 'Talandra', ym(2441, 5, 10)),
          ('haedus', 'Indata Mog', ym(2428, 11, 6)), ('ijax', 'Ijax', ym(2433, 6)),
          ('cirban', 'Bounty', ym(2430, 5, 18))]

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
    ev(ym(2334, 8, 20), 'Fall of New Indata Mog', 'haedus', 'battle', 'fall-of-new-indata-mog'),
    ev(ym(2336, 3, 10), 'Battle of Exedor', 'exedor', 'battle', 'battle-of-exedor-2336'),
    ev(ym(2337, 4), 'Leesak', 'leesak', 'battle', 'siege-of-hiverion'),
    ev(ym(2338, 5, 3), 'Fall of the Krakre', 'exedor', 'battle', 'siege-of-hiverion'),
    ev(ym(2341, 1, 21), 'Treaty of Ximpok', 'ximpok', 'treaty', 'treaty-of-ximpok'),
    ev(ym(2341, 1, 1), 'Unified Solar Republic proclaimed', 'sol', 'polity', 'unified-solar-republic'),
    ev(ym(2388), 'Thurva named the Red Khan', 'dhen-ossa', 'polity'),
    ev(ym(2405), 'Assembly of the Veil', 'dhen-ossa', 'polity'),
    ev(ym(2408), 'The Dwaii fleet destroyed', 'hwen', 'battle'),
    ev(ym(2413), 'The Ka-Dur fall', 'ossath', 'battle'),
    ev(ym(2417, 5), 'Romston submits', 'romston', 'battle'),
    ev(ym(2419, 9), 'Cazzabius burned', 'cazzabius', 'burning'),
    ev(ym(2422, 6, 14), 'Fall of Vur Duri', 'aethos', 'battle'),
    ev(ym(2424, 6), 'Vi Simni submits', 'ximpok', 'battle'),
    ev(ym(2427, 8, 16), 'Fall of Hiverion', 'exedor', 'battle', 'hiverion'),
    ev(ym(2428, 7, 9), 'Fall of Myrum', 'myrum', 'battle'),
    ev(ym(2428, 8, 6), 'First Battle of Haedius', 'haedus', 'battle'),
    ev(ym(2428, 9, 3), 'Second Battle of Haedius', 'haedus', 'battle'),
    ev(ym(2428, 11, 6), 'Indata Mog burned', 'haedus', 'burning'),
    ev(ym(2429, 1, 22), 'Siege of Bounty', 'cirban', 'battle', 'siege-of-bounty'),
    ev(ym(2430, 5, 17), "Last stand at Roric's Plaza", 'cirban', 'battle', 'siege-of-bounty'),
    ev(ym(2433, 6), 'Ijax burned', 'ijax', 'burning'),
    ev(ym(2434, 3, 12), 'Battle of Saolea', 'saolea', 'battle', 'saolea'),
    ev(ym(2436, 9, 12), 'Theia burned', 'saolea', 'burning', 'theia'),
    ev(ym(2437, 3), 'Hualapai burned', 'veyer', 'burning'),
    ev(ym(2438, 1), 'Siege of Nomotar', 'nomotar', 'battle'),
    ev(ym(2440, 4, 14), 'Fall of Binami', 'binami', 'battle'),
    ev(ym(2441, 5, 2), 'First Battle of Talandra', 'talandra', 'battle'),
    ev(ym(2441, 11, 14), 'Battle of Procyon', 'procyon', 'battle'),
    ev(ym(2441, 11, 26), 'Landfall burned', 'procyon', 'burning'),
    ev(ym(2442, 4, 20), 'Circumstance submits', 'alpha-centauri', 'battle'),
    ev(ym(2444, 6, 8), 'Battle of Yildun', 'yildun', 'battle', 'yildun'),
    ev(ym(2444, 12, 3), 'Dauntless burned', 'yildun', 'burning', 'dauntless'),
    ev(ym(2446, 4, 2), 'Battle of Jupiter', 'sol', 'battle'),
    ev(ym(2446, 12, 5), 'Battle of Earth', 'sol', 'battle'),
    ev(ym(2447, 10, 14), 'Battle of Alpha Centauri', 'alpha-centauri', 'battle'),
    ev(ym(2448, 5, 4), 'Second Battle of Procyon', 'procyon', 'battle'),
    ev(ym(2449, 6, 14), 'Second Battle of Talandra', 'talandra', 'battle'),
    ev(ym(2450, 5, 11), 'The eight khans disperse', 'cirban', 'polity'),
    ev(ym(2449, 11), 'Bashpit, the Scouring begins', 'bashpit', 'battle'),
    ev(ym(2450, 5, 16), 'Bounty retaken', 'cirban', 'battle', 'bounty'),
    ev(ym(2451, 5, 9), 'Third Battle of Haedius', 'haedus', 'battle'),
    ev(ym(2451, 9, 24), 'Battle of Exedor', 'exedor', 'battle', 'battle-of-exedor-2451'),
    ev(ym(2452, 11, 30), "Hiverion's orbitals fall", 'exedor', 'battle'),
    ev(ym(2453, 1, 1), 'Voor Confederacy restored', 'exedor', 'polity'),
    ev(ym(2453, 8, 9), "D'Ashan's counterattack", 'aethos', 'battle'),
    ev(ym(2453, 10, 18), 'Second Battle of Aethos', 'aethos', 'battle'),
    ev(ym(2456, 2, 11), "D'Hovar's counterattack", 'omaggus', 'battle'),
    ev(ym(2460, 4, 1), 'Kuma and Ijaagin returned', 'kuma', 'treaty'),
    ev(ym(2454, 4), 'Churassix', 'churassix', 'battle'),
    ev(ym(2454, 10, 20), 'Battle of Fevallion', 'fevallion', 'battle'),
    ev(ym(2455, 6, 2), 'Fleets meet at Fejantris', 'fejantris', 'treaty'),
    ev(ym(2456, 4), 'The Dwaii freed', 'hwen', 'battle'),
    ev(ym(2457, 2, 20), 'Battle of Ossath', 'ossath', 'battle'),
    ev(ym(2460, 1, 1), 'Fejantris Peace', 'fejantris', 'treaty'),
    ev(ym(2466, 6, 20), 'Fevarian Accords signed', 'exedor', 'treaty'),
]

# ------------------------------------------------------------------ captions
CAPTIONS = [
    (2050, 2100, 'The Sun\'s planets are settled. Luna and Mars become the first worlds beyond Earth.'),
    (2100, 2220, 'Humanity spreads through the Sun\'s system. No ship has yet crossed to another star.'),
    (2220, 2255, 'The Solar War divides the Sun\'s worlds.'),
    (2255, 2283, 'Unification. The Sun\'s worlds move toward a single government.'),
    (2283, 2300, 'The United Nations of Earth is founded and commits to the stars.'),
    (2300, 2318, 'The Expansion Era. Four survey ships chart 800 stars; the core worlds are founded.'),
    (2318, 2333, 'Contact with the Voor. The Ciriban Gulf becomes a border of trade and forts.'),
    (2333, 2341, 'The Voor War. The Republic\'s fleets drive into the Confederacy.'),
    (2341, 2405, 'The First Republic. Second and Third Waves settle the frontier; the Voor Territories join.'),
    (2405, 2428, 'The Red Khan unites the Veil and conquers the Dwaii, the Ka-Dur and the Confederacy.'),
    (2428, 2441, 'The Fevarian Crisis. The Khan takes the Gulf and both Sectors.'),
    (2441, 2449, 'The Darkest Decade. The Khanate strikes into the core and reaches the Sun.'),
    (2449, 2460, 'The Scouring. The Retribution Fleet destroys the monoliths outside the Veil.'),
    (2460, 2510, 'Reconstruction. The Second Republic rebuilds the burned worlds.'),
    (2510, 2516, 'The Apportionment Crisis. Chamber seats are recalculated for the first time since 2420.'),
]

data = {
    'meta': {
        'source': 'Traced from Lewis Brewer\'s reference map 2235.12.10; 1 unit = 1 light year; Sol at origin.',
        'range': [2050, 2515], 'start': 2510,
    },
    'polities': POLITIES,
    # Powers fade in when humanity learns of them: the Voor at contact in 1 October 2317's
    # approach, the Maweer and (through the Voor) the Fevarians by 2320.
    'contact': {'voor': 2317.75, 'maweer': 2320.5, 'freehold': 2320.5, 'fevclans': 2320.5, 'dwaii': 2320.5, 'kadur': 2320.5},
    'systems': [{**s, 'own': own[s['id']]} for s in systems],
    'worlds': worlds,
    'planetNames': PLANET_NAMES,
    'burned': [{'sys': a, 'name': b, 'y': c} for a, b, c in BURNED],
    'events': sorted(EVENTS, key=lambda e: e['y']),
    'captions': [{'from': a, 'to': b, 'text': t} for a, b, t in CAPTIONS],
    'regions': [
        {'name': 'Ciriban Gulf', 'near': ['golba', 'media', 'swur', 'cirban']},
        {'name': 'Ibannic Veil', 'near': ['kuma', 'banagho', 'omaggus', 'ijaagin'], 'toward': 'ushars-well'},
        {'name': 'Zadanis Void', 'near': ['lishval', 'okul', 'gorim', 'targon']},
        {'name': 'Shadow Nebula', 'near': ['asmore', 'sorcimax', 'uldor', 'quannaga']},
        {'name': 'Nythran Void', 'near': ['ponnell', 'brallix', 'ellamir', 'galurum']},
        # on the far side of the Rubin Void (book 7.2 and 15.9)
        {'name': 'Mardak Cluster', 'near': [slug(n) for n, *_ in EXTRA['mardak']], 'stack': True},
        {'name': 'Rubin Void', 'near': ['halvek', 'imrith', 'oru-tenna', 'selund']},
    ],
    # The Republic's administrative sectors, from the colony sheet
    'sectors': [{'name': n, 'members': sorted(m for m, s in SHEET_SECTOR.items() if s == n)}
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
#    Cirban to Haedus and Swur to Media at the centre, the core worlds to the Sectors, the
#    Voor worlds from Exedor south to the Veil.
LANES = """sol-procyon sol-alpha-centauri procyon-binami procyon-talandra talandra-nomotar nomotar-myrum
talandra-binami binami-ijax ijax-cirban binami-yildun yildun-saolea cirban-izar izar-bashpit bashpit-ijax
cirban-ajam ajam-stiridon cirban-haedus haedus-kastaba kastaba-myrum haedus-faenov haedus-exedor
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
NO_LANES = "emim-maasym lytirim-dastamon cygni-myrum cygni-ross-alpha".split()
for lane in NO_LANES:
    i_, j_ = pair(lane); seen.add((min(i_, j_), max(i_, j_)))
for lane in LANES + EXTRA_LANES:
    link(*pair(lane))
# The Iron Gulf map's own area follows its lanes only; elsewhere the network is a relative
# neighbourhood graph (two stars are linked when no third star lies closer to both), which
# gives the same sparse, lane-like structure across the rest of the map.
GULF = set("""sol procyon alpha-centauri tem torovil talandra brink binami bashpit izar ijax cirban haedus ajam
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
    'sol:Luna': [[2063, ['peoples-republic-of-china.svg', 'european-federation.svg', 'united-states-of-america.svg']], [UNIFY, ['luna.png']]],
    'sol:Mars': [[2076, ['european-federation.svg']], [2079.7, ['european-federation.svg', 'united-states-of-america.svg']], [UNIFY, ['mars.png']]],
    'sol:Io': [[2100, ['republic-of-india.svg']], [UNIFY, ['io.png']]],
    'sol:Europa': [[2100, ['european-federation.svg']], [UNIFY, ['europa.png']]],
    'sol:Ganymede': [[2100, ['peoples-republic-of-china.svg']], [UNIFY, ['ganymede.png']]],
    'sol:Callisto': [[2100, ['united-states-of-america.svg']], [UNIFY, ['callisto.png']]],
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

out = HERE / 'atlas-data.json'
json.dump(data, open(out, 'w'), separators=(',', ':'))
print('systems', len(systems), 'worlds', len(worlds), 'events', len(EVENTS), '->', out, out.stat().st_size, 'bytes')
print('D\'Hovar worlds:', dhovar)
print('marches:', [s['id'] for s in marches])
print('north Voor:', [s['id'] for s in north_v])
print('north Maweer:', [s['id'] for s in north_m])
print('extent x', min(s['x'] for s in systems), max(s['x'] for s in systems), 'y', min(s['y'] for s in systems), max(s['y'] for s in systems))
