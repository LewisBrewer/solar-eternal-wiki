"""Flags for infobox entries: which polity a commander, unit, ship or belligerent belongs to.

Order of decision for one entry:
  1. a tag at the start of the entry in the doc, e.g. "{us} Frank Fletcher" (the tag is not shown)
  2. a [[link]] to a polity that has a flag
  3. a [[link]] to a person whose infobox Allegiance names a polity
  4. data/flagnames.tsv, a table of names the build cannot work out
  5. the name patterns below (ship prefixes, formation names, adjectives)
  6. the side's own flag, when that side of the infobox has a single belligerent
Members of a bloc carry the bloc's flag (a Japanese division flies the Pacific Union's).
United Nations bodies fly the UN flag to 2283, the UNE's to 2341 and the Republic's after.
"""
import os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FLAGDIR = os.path.join(ROOT, 'static', 'flags')

# short tags usable in the docs, and the polity each stands for
TAGS = {
    'us': 'united-states-of-america', 'usa': 'united-states-of-america',
    'ef': 'european-federation', 'eu': 'european-federation',
    'cn': 'peoples-republic-of-china', 'china': 'peoples-republic-of-china',
    'in': 'republic-of-india', 'india': 'republic-of-india',
    'pu': 'pacific-union', 'al': 'arabic-league', 'cac': 'central-african-confederation',
    'br': 'federative-republic-of-brazil', 'ar': 'argentine-republic', 'ca': 'canada',
    'kr': 'korean-republic', 'ru': 'russian-federation', 'jp': 'japan', 'my': 'malaysia',
    'sg': 'singapore', 'ph': 'philippines', 'vn': 'vietnam', 'id': 'indonesia',
    'mjc': 'martian-jovian-confederation', 'voor': 'voor-confederacy',
    'un': 'un', 'une': 'united-nations-of-earth', 'usr': 'unified-solar-republic',
    'none': '',
}

# polities whose units fly a bloc's flag
BLOC = {
    'japan': 'pacific-union', 'malaysia': 'pacific-union', 'singapore': 'pacific-union',
    'hellenic-free-state': 'martian-jovian-confederation',
    'confederation-of-jovian-free-colonies': 'martian-jovian-confederation',
    'marineris-coalition': 'martian-jovian-confederation',
    'league-for-jovian-rule': 'martian-jovian-confederation',
    'united-nations': 'un', 'united-nations-high-command': 'un',
    'united-nations-enforcement-directorate': 'un', 'unified-solar-marine-corps': 'un',
    'terrestrial-coalition': '', 'non-aligned-pact': '',
}

U = 'un'
PATTERNS = [
    (r'Rapid Orbital Deployment|\bROD\b|Enforcement Directorate|United Nations|High Command|Unified Solar|Combined Chiefs|Grand Armada|\bUNS\b', U),
    (r'Central African|\bCADF\b|Great Lakes|Congolese|Kenyan', 'central-african-confederation'),
    (r'Voor\b|\bhearths?\b|Kor-class', 'voor-confederacy'),
    (r'Martian-Jovian|Confederation|Jovian Militia|\bSpark\b|Io Divisions?|Europa Divisions?|Valles (Command|Militia|Division)'
     r'|Tharsis (Command|Hover|Division)|Elysium Command|Copernicus Division|Hellenic|Free State|Red Hand|Robespierre|Daxian'
     r'|Yugantar|\bJCV\b|\bMRNS\b|Europan Strike|Tunnel Brigade|Shipwrights|Caspari Fleet|militia', 'martian-jovian-confederation'),
    (r'Brazil', 'federative-republic-of-brazil'),
    (r'Argentin', 'argentine-republic'),
    (r'Canad', 'canada'),
    (r'Korea', 'korean-republic'),
    (r'Russia', 'russian-federation'),
    (r'Philippin|Filipino', 'philippines'),
    (r'Vietnam', 'vietnam'),
    (r'Indonesia', 'indonesia'),
    (r'United States|American|\bUSS\b|\bUS\b|Space Force|Marine Division|Infinity', 'united-states-of-america'),
    (r'European Federation|Federal|\bEFS\b|Panzer|French|German|Italian|Spanish|Polish|Dutch|British|Royal Marines|\bSAS\b'
     r'|Brunete|Ariete|Charlemagne|Maréchal|Lynx|Theseus|Walker Regiment', 'european-federation'),
    (r'Chin(a|ese)|\bPLAN?\b|People\'s Republic|Kunlun|Group Army|Theatre Command|Mongolian|Siberian|Far East|Ural', 'peoples-republic-of-china'),
    (r'India|Gurkha|Gorkha|Anant|Trishakti|Southern Army Group|Bharat|Mysore|Trishul|Nepal|Sri Lank|Bangladesh|Pakistan', 'republic-of-india'),
    (r'Pacific Union|Pacific Corps|\bUnion\b|ANZAC|Australia|New Zealand|Japan|Malaysia|Singapore|Fiji|Hellrider|Andean|Chilean|Peruvian|Ecuador', 'pacific-union'),
    (r'Arabic League|\bLeague\b(?! for)|Iraqi|Kuwaiti|Emirati|Sudanese|Iranian|Egyptian|Saudi', 'arabic-league'),
]
PATTERNS = [(re.compile(p), k) for p, k in PATTERNS]


def load_names():
    p = os.path.join(ROOT, 'data', 'flagnames.tsv')
    out = {}
    if os.path.exists(p):
        for line in open(p, encoding='utf-8'):
            line = line.rstrip('\n')
            if not line or line.startswith('#') or '\t' not in line:
                continue
            name, tag = line.split('\t', 1)
            out[name.strip().lower()] = TAGS.get(tag.strip().lower(), tag.strip())
    return out


NAMES = load_names()


def flag_file(key):
    for ext in ('svg', 'png'):
        if os.path.exists(os.path.join(FLAGDIR, '%s.%s' % (key, ext))):
            return '%s.%s' % (key, ext)
    return None


def settle(key, year):
    """Apply the bloc and UN rules, then return a key that has a flag file, or ''."""
    if key is None:
        return None
    key = BLOC.get(key, key)
    if key == 'philippines' and year and year >= 2232:
        key = 'pacific-union'
    if key in ('un', 'united-nations-of-earth', 'unified-solar-republic'):
        if key == 'un' or year:
            y = year or 2250
            key = 'united-nations' if y < 2283 else ('united-nations-of-earth' if y < 2341 else 'unified-solar-republic')
    return key if (key and flag_file(key)) else ''


def by_pattern(text):
    for rx, k in PATTERNS:
        if rx.search(text):
            return k
    return None
