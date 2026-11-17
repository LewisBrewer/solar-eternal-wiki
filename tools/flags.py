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
    'mars': 'mars', 'io': 'free-io', 'europa': 'free-europa', 'ganymede': 'free-ganymede',
    'callisto': 'free-callisto', 'luna': 'free-luna', 'league': 'league-for-jovian-rule',
}

# polities whose units fly a bloc's flag
BLOC = {
    'japan': 'pacific-union', 'malaysia': 'pacific-union', 'singapore': 'pacific-union',
    'hellenic-free-state': 'mars',
    'confederation-of-jovian-free-colonies': 'league-for-jovian-rule',
    'marineris-coalition': 'mars',
    'united-nations': 'un', 'united-nations-high-command': 'un',
    'united-nations-enforcement-directorate': 'un', 'unified-solar-marine-corps': 'un',
    'terrestrial-coalition': '', 'non-aligned-pact': '',
}

U = 'un'
PATTERNS = [
    (r'Rapid Orbital Deployment|\bROD\b|Enforcement Directorate|United Nations|High Command\b|Unified Solar|Combined Chiefs|Grand Armada|\bUNS\b', U),
    (r'Central African|\bCADF\b|Great Lakes|Congolese|Kenyan', 'central-african-confederation'),
    (r'Voor\b|\bhearths?\b|Kor-class', 'voor-confederacy'),
    (r'Jovian Free Colonies|League for Jovian Rule', 'league-for-jovian-rule'),
    (r'Caños|Guardia del Delta|outer delta|Moriche', 'dauntless'),
    (r'Verhoeven|Triumph Squadron', 'circumstance'),
    (r"Landfall's home guard", 'landfall'),
    (r'Marineris Coalition', 'mars'),
    (r'Martian-Jovian|Confederation|Jovian Militia|Jovian League|League for Jovian|\bSpark\b|Io Divisions?|Europa Divisions?|Valles (Command|Militia|Division)'
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


# after unification (1 June 2283) every human formation is the federation's, whatever a name suggests
NATIONAL = {'united-states-of-america', 'european-federation', 'peoples-republic-of-china', 'republic-of-india',
            'pacific-union', 'arabic-league', 'central-african-confederation', 'federative-republic-of-brazil',
            'argentine-republic', 'canada', 'korean-republic', 'russian-federation', 'japan', 'malaysia',
            'singapore', 'philippines', 'vietnam', 'indonesia', 'martian-jovian-confederation'}


def by_pattern(text):
    for rx, k in PATTERNS:
        if rx.search(text):
            return k
    return None


# The Confederation's forces fly the flag of their home area: Mars, the revolutionary moon flags,
# or the Jovian League's for Jovian-wide bodies. The fleet and the council fly the Confederation's.
CONFED = 'martian-jovian-confederation'
AREAS = [
    (r'[Ff]leet|Robespierre|Daxian|Yugantar|Red Hand|Trojan|\bJCV\b|\bMRNS\b|[Ss]quadron|[Tt]ask force|council', CONFED),
    (r'Jovian Militia|Jovian Free Colonies|\bLeague\b', 'league-for-jovian-rule'),
    (r'\bIo\b|Spark|Tunnel Brigade|Chasma|Gandhi|Van Maanush|Loki|Pele\b|Mahajan', 'free-io'),
    (r'Europa|Europan|New Rhine|Da Gama|Tycho City|West Rhine|Magellan|Shipwrights', 'free-europa'),
    (r'Ganymede|Zhang|Pauldron|Xi He', 'free-ganymede'),
    (r'Callisto|Sabre|Big River', 'free-callisto'),
    (r'Mars|Martian|Valles|Tharsis|Elysium|Hellas|Hellenic|Free State|Marineris|Liberté|Bartolomeu|Redoubt|Ionia|'
     r'Oberstdorf|New Corinth|Albany|Coleridge|Phobos|Deimos|Hesperus|Daxia|Ophir|Port Argo', 'mars'),
    (r'\bLuna\b|Lunar|Copernicus|Zheng He|Crisium|Delambre|Farside|Hangzhou One|Yorktown|Dongsuo|Procellarum', 'free-luna'),
]
AREAS = [(re.compile(p), k) for p, k in AREAS]
AREA_KEYS = set(k for _, k in AREAS) | {CONFED}


def area_for(text):
    for rx, k in AREAS:
        if rx.search(text or ''):
            return k
    return None


# the article a flag links to, where it is not the flag's own name
LINK = {
    'free-io': 'swaraj of io', 'free-europa': 'free hanse of europa', 'free-ganymede': "ganymede people's commune",
    'free-callisto': 'free port of callisto', 'free-luna': 'lunar revolutionary administration', 'united-nations': 'united nations',
}
