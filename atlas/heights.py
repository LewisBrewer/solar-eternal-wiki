"""Heights above the plane (Lewis, 19 November 2026: real where known).
Real stars take their true galactic latitude b; height = map distance x sin(b) x K, capped.
Invented and unidentified systems are smoothed between the real ones by inverse-distance weighting,
falling back toward the plane far from any real star, with a little of their old scatter kept."""
import math
# RA (h, m, s), Dec (deg, min) J2000, for the systems that are real stars
RADEC = {
    'alpha-centauri': ((14, 39, 36), (-60, 50)), 'sirius': ((6, 45, 9), (-16, 43)), 'procyon': ((7, 39, 18), (5, 13)),
    'epsilon-eridani': ((3, 32, 56), (-9, 27)), 'tau-ceti': ((1, 44, 4), (-15, 56)), 'epsilon-indi': ((22, 3, 22), (-56, 47)),
    'barnards-star': ((17, 57, 48), (4, 41)), 'kapteyn': ((5, 11, 41), (-45, 1)), 'kruger': ((22, 28, 0), (57, 42)),
    'luyten-major': ((7, 27, 24), (5, 14)), 'groombridge': ((0, 18, 23), (44, 1)), 'lacaille': ((23, 5, 52), (-35, 51)),
    'wolf': ((10, 56, 29), (7, 1)), 'van-maanen': ((0, 49, 10), (5, 23)), 'lalande': ((11, 3, 20), (35, 58)),
    'struve-alpha': ((18, 42, 47), (59, 38)), 'cygni': ((21, 6, 54), (38, 45)), 'polaris': ((2, 31, 49), (89, 16)),
    'yildun': ((17, 32, 13), (86, 35)), 'zosma': ((11, 14, 6), (20, 31)), 'wezen': ((7, 8, 23), (-26, 24)),
    'furud': ((6, 20, 19), (-30, 4)), 'gamma-draconis': ((17, 56, 36), (51, 29)), 'sigma-draconis': ((19, 32, 22), (69, 40)),
    'achernar': ((1, 37, 43), (-57, 14)), 'spica': ((13, 25, 12), (-11, 10)), 'sabik': ((17, 10, 23), (-15, 43)),
    'izar': ((14, 44, 59), (27, 4)), 'cheleb': ((17, 43, 28), (4, 34)), 'beid': ((4, 11, 52), (-6, 50)),
    'matar': ((22, 43, 0), (30, 13)), 'beta-aquilae': ((19, 55, 19), (6, 24)), 'luhman': ((10, 49, 19), (-53, 19)),
}
K, CAP = 0.25, 8.0
AG, DG = math.radians(192.85948), math.radians(27.12825)
def gal_b(ra, dec):
    a = math.radians((ra[0] + ra[1] / 60 + ra[2] / 3600) * 15)
    d = math.radians(dec[0] + math.copysign(dec[1] / 60, dec[0] if dec[0] else 1))
    return math.asin(math.sin(d) * math.sin(DG) + math.cos(d) * math.cos(DG) * math.cos(a - AG))

def apply(systems):
    by = {s['id']: s for s in systems}
    real = {}
    for sid, (ra, dec) in RADEC.items():
        s = by.get(sid)
        if not s: continue
        dmap = math.hypot(s['x'], s['y'])
        z = max(-CAP, min(CAP, dmap * math.sin(gal_b(ra, dec)) * K))
        real[sid] = z; s['z'] = round(z, 2); s['zReal'] = True
    for s in systems:
        if s['id'] in real or s['id'] == 'sol': continue
        num = den = 0.0
        for sid, z in list(real.items()) + [('sol', 0.0)]:
            r = by[sid]; d = math.hypot(s['x'] - r['x'], s['y'] - r['y'])
            w = 1 / max(d, 1.0) ** 2
            num += w * z; den += w
        near = min(math.hypot(s['x'] - by[k]['x'], s['y'] - by[k]['y']) for k in real)
        fall = math.exp(-max(0.0, near - 15) / 25)       # far from any real star the field relaxes toward the plane
        s['z'] = round(num / den * fall + 0.3 * s['z'], 2)
    by['sol']['z'] = 0.0
    return real
