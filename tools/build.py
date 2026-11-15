#!/usr/bin/env python3
"""Build the Solar Eternal Archive from a folder of article HTML files.

Input: src/docs/*.html (Google Docs HTML exports, or plain HTML in the same shape:
an h1 title, an italic epigraph paragraph and its source line, an infobox table whose
first row is "Type", then the body, ending with a "Sources" heading and list).
Output: out/ (a static site for GitHub Pages).
"""
import html, json, os, re, shutil, sys, datetime
from bs4 import BeautifulSoup, NavigableString, Tag
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import flags as FL

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'src', 'docs')
OUT = os.path.join(ROOT, 'out')
STATIC = os.path.join(ROOT, 'static')

SECTION = '\x00section'   # infobox key for a section heading row
MONTHS = ['January','February','March','April','May','June','July','August','September','October','November','December']
MRX = '|'.join(MONTHS)

CATEGORIES = [
    ('battles', 'Battles and campaigns', 'Battles, sieges, campaigns and wars.'),
    ('people', 'People', 'Admirals, generals, presidents, explorers and envoys.'),
    ('polities', 'Polities', 'States, federations and confederacies.'),
    ('species', 'Species', 'The peoples of known space.'),
    ('worlds', 'Worlds and systems', 'Star systems, worlds and moons.'),
    ('ships', 'Ships and technology', 'Ships, classes and the drives that moved them.'),
    ('organisations', 'Organisations and places', 'Armed forces, offices and great buildings.'),
    ('treaties', 'Treaties, acts and plans', 'Treaties, pledges, protocols and war plans.'),
    ('other', 'Other articles', 'Everything else in the archive.'),
]

def _atlas_ids():
    p = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'atlas', 'atlas-data.json')
    try:
        return set(s['id'] for s in json.load(open(p))['systems'])
    except Exception:
        return set()


ATLAS_IDS = _atlas_ids()

ERAS = [
    ('PARTS I–II · 1945–2220', 'The Early Solar Era', 1945, 2220),
    ('PARTS III–V · 2220–2255', 'The Solar War', 2220, 2255),
    ('PART VI · 2255–2290', 'Unification', 2255, 2290),
    ('PART VII · 2289–2318', 'The Expansion Era', 2289, 2318),
    ('PART VIII · 2318–2333', 'The Ring of Iron', 2318, 2333),
    ('PART IX · 2333–2341', 'The Ciriban Gulf Conflict', 2333, 2341),
    ('PART X · 2341–2405', 'The First Republic', 2341, 2405),
    ('PARTS XI–XII · 2405–2441', 'The Fevarian Crisis', 2405, 2441),
    ('PART XIII · 2441–2449', 'The Darkest Decade', 2441, 2449),
    ('PART XIV · 2449–2460', 'The Scouring', 2449, 2460),
    ('PART XV · 2460–2510', 'Reconstruction', 2460, 2510),
]


def cut_sentences(s, n):
    if len(s) <= n:
        return s
    c = s[:n]
    i = c.rfind('. ')
    return c[:i + 1] if i > 0 else c.rsplit(' ', 1)[0] + '…'


def slugify(t):
    t = html.unescape(t).lower().replace('’', "'")
    t = re.sub(r"[']", '', t)
    t = re.sub(r'[^a-z0-9]+', '-', t).strip('-')
    return t or 'untitled'


def infer_type(art):
    """A type for an infobox that does not state one."""
    keys = set(k.lower() for k, v in art['infobox'] if k != SECTION)
    secs = set(v.lower() for k, v in art['infobox'] if k == SECTION)
    t = (art['title'] or '').lower()
    if not art['infobox']:
        return ''
    if 'born' in keys or ('rank' in keys and 'allegiance' in keys):
        return 'Person'
    if 'belligerents' in keys or 'belligerents' in secs or ('result' in keys and 'part of' in keys):
        for w, typ in (('siege', 'Siege'), ('campaign', 'Campaign'), ('operation', 'Military operation'), ('raid', 'Raid'),
                       ('landing', 'Landing'), ('front', 'Campaign'), ('war', 'War'), ('massacre', 'Battle'), ('capture', 'Battle')):
            if re.search(r'\b%s\b' % w, t):
                return typ
        return 'Battle'
    if any(k.startswith('signatories') for k in keys) or 'terms' in keys:
        return 'Surrender agreement'
    if 'called by' in keys or 'participants' in keys:
        return 'Conference'
    if 'branch' in keys or ('active' in keys and 'strength' in keys):
        return 'Military unit'
    return ''


def category_for(typ):
    t = (typ or '').lower()
    if any(k in t for k in ('battle', 'campaign', 'siege', 'war ', 'incident', 'assault', 'operation', 'raid', 'landing')) or t in ('war',):
        return 'battles'
    if 'person' in t:
        return 'people'
    if 'polity' in t or any(k in t for k in ('provisional state', 'alliance', 'political', 'mutual security')):
        return 'polities'
    if 'species' in t:
        return 'species'
    if any(k in t for k in ('world', 'star system', 'system', 'moon', 'planet')):
        return 'worlds'
    if any(k in t for k in ('ship', 'class', 'drive', 'technology', 'vessel', 'cruiser', 'battlecruiser', 'carrier', 'destroyer', 'frigate', 'corvette')):
        return 'ships'
    if any(k in t for k in ('treaty', 'plan', 'act', 'pledge', 'protocol', 'charter', 'agreement', 'conference')):
        return 'treaties'
    if any(k in t for k in ('force', 'complex', 'office', 'organisation', 'agency', 'fortress', 'military unit')):
        return 'organisations'
    return 'other'


# ---------------------------------------------------------------- normalising

def css_classes(soup):
    """Map Google Docs export classes to bold/italic."""
    props = {}
    for st in soup.find_all('style'):
        for m in re.finditer(r'\.([\w-]+)\s*\{([^}]*)\}', st.get_text()):
            cls, body = m.group(1), m.group(2).lower()
            p = props.setdefault(cls, set())
            if re.search(r'font-weight:\s*(700|bold)', body):
                p.add('b')
            if 'font-style:italic' in body.replace(' ', ''):
                p.add('i')
    return props


def list_level(el):
    for c in el.get('class') or []:
        m = re.match(r'lst-kix_[A-Za-z0-9]+-(\d+)$', c)
        if m:
            return int(m.group(1))
    return None


def nest_lists(body, soup):
    for parent in [body] + body.find_all(['div', 'section']):
        stack = []   # (level, list element) for the run of lists being merged
        for el in list(parent.children):
            if isinstance(el, NavigableString):
                if el.strip():
                    stack = []
                continue
            lvl = list_level(el) if el.name in ('ul', 'ol') else None
            if lvl is None:
                stack = []
                continue
            if not stack:
                stack = [(lvl, el)]
                continue
            while stack and stack[-1][0] > lvl:
                stack.pop()
            if stack and stack[-1][0] == lvl:
                target = stack[-1][1]
                for li in el.find_all('li', recursive=False):
                    target.append(li.extract())
                el.decompose()
            elif stack:
                host = stack[-1][1].find_all('li', recursive=False)
                if host:
                    host[-1].append(el.extract())
                stack.append((lvl, el))
            else:
                stack = [(lvl, el)]


def normalise(raw):
    soup = BeautifulSoup(raw, 'html.parser')
    props = css_classes(soup)
    body = soup.body or soup
    for t in body.find_all(['style', 'script', 'meta', 'title', 'head']):
        t.decompose()
    # google redirect links
    for a in body.find_all('a'):
        href = a.get('href', '')
        m = re.match(r'https?://www\.google\.com/url\?q=([^&]+)', href)
        if m:
            from urllib.parse import unquote
            a['href'] = unquote(m.group(1))
        if not a.get_text(strip=True):
            a.unwrap()
    # spans: style to b/i, then unwrap (drops the lilac highlight)
    for sp in body.find_all('span'):
        styles = set()
        for c in sp.get('class', []) or []:
            styles |= props.get(c, set())
        inline = (sp.get('style') or '').replace(' ', '').lower()
        if re.search(r'font-weight:(700|bold)', inline):
            styles.add('b')
        if 'font-style:italic' in inline:
            styles.add('i')
        inner = sp
        for tag in ('b', 'i'):
            if tag in styles:
                w = soup.new_tag(tag)
                for ch in list(inner.contents):
                    w.append(ch.extract())
                inner.append(w)
        sp.unwrap()
    for t in body.find_all(['strong']):
        t.name = 'b'
    for t in body.find_all(['em']):
        t.name = 'i'
    # Docs exports a nested list as flat sibling lists whose class ends -0, -1, -2 by depth;
    # rebuild the nesting so an order of battle reads as a tree
    nest_lists(body, soup)
    # Docs "title" paragraph becomes h1
    for p in body.find_all('p'):
        if 'title' in (p.get('class') or []):
            p.name = 'h1'
    # strip attributes
    for t in body.find_all(True):
        keep = {}
        if t.name == 'a' and t.get('href'):
            keep['href'] = t['href']
        if t.name in ('td', 'th'):
            for k in ('colspan', 'rowspan'):
                if t.get(k) and t.get(k) != '1':
                    keep[k] = t[k]
        t.attrs = keep
    # paragraphs inside cells and list items
    for cell in body.find_all(['td', 'th', 'li']):
        ps = cell.find_all('p', recursive=False)
        for i, p in enumerate(ps):
            if i:
                p.insert_before(soup.new_tag('br'))
            p.unwrap()
    # tbody wrappers are fine; remove empty paragraphs
    for p in body.find_all(['p', 'h1', 'h2', 'h3', 'h4']):
        if not p.get_text(strip=True):
            p.decompose()
    # merge adjacent identical inline tags (<i>a</i><i>b</i>)
    for tag in ('i', 'b'):
        for t in body.find_all(tag):
            nxt = t.next_sibling
            while isinstance(nxt, Tag) and nxt.name == tag:
                for ch in list(nxt.contents):
                    t.append(ch.extract())
                n2 = nxt.next_sibling
                nxt.decompose()
                nxt = n2
    return body


def block_list(body):
    out = []
    for el in body.children:
        if isinstance(el, NavigableString):
            if el.strip():
                out.append(('p', el.strip()))
            continue
        if el.name in ('div', 'section', 'article', 'main'):
            out.extend(block_list(el))
        else:
            out.append((el.name, el))
    return out


def text(el):
    return el.get_text(' ', strip=True) if isinstance(el, Tag) else str(el)


# ---------------------------------------------------------------- parsing an article

def parse_article(path):
    raw = open(path, encoding='utf-8').read()
    body = normalise(raw)
    blocks = block_list(body)
    art = {'file': os.path.basename(path), 'title': None, 'quote': None, 'quote_src': None,
           'infobox': [], 'body': [], 'sources': []}
    i = 0
    while i < len(blocks) and blocks[i][0] != 'h1':
        i += 1
    if i < len(blocks):
        art['title'] = text(blocks[i][1])
        i += 1
    else:
        art['title'] = os.path.splitext(os.path.basename(path))[0]
        i = 0
    # epigraph
    if i < len(blocks) and blocks[i][0] == 'p':
        p = blocks[i][1]
        kids = [c for c in p.contents if not (isinstance(c, NavigableString) and not c.strip())]
        if len(kids) == 1 and isinstance(kids[0], Tag) and kids[0].name == 'i':
            art['quote'] = kids[0].decode_contents().strip()
            i += 1
            if i < len(blocks) and blocks[i][0] == 'p':
                art['quote_src'] = blocks[i][1].decode_contents().strip()
                i += 1
    rest = blocks[i:]
    # infobox: first table whose first cell says Type
    for j, (name, el) in enumerate(rest):
        if name == 'table':
            rows = el.find_all('tr')
            firsts = [text(r.find(['td', 'th'])).strip().lower() for r in rows if r.find(['td', 'th'])]
            # a summary table: first cell "Type", or Wikipedia-style section rows with a Type row inside
            titled = (j <= 1 and len(rows) > 2 and len(rows[0].find_all(['td', 'th'])) == 1
                      and len(rows[1].find_all(['td', 'th'])) >= 2)
            if firsts and (firsts[0] == 'type' or ('type' in firsts and len(rows[0].find_all(['td', 'th'])) == 1) or titled):
                for r in rows:
                    cells = r.find_all(['td', 'th'])
                    if len(cells) >= 2 and text(cells[1]):
                        art['infobox'].append((text(cells[0]), cells[1].decode_contents().strip()))
                    elif cells and text(cells[0]):
                        if text(cells[0]).strip().lower() == (art['title'] or '').strip().lower():
                            continue   # the title row at the top of a Wikipedia-style box
                        art['infobox'].append((SECTION, text(cells[0])))   # a section row spanning the table
                rest = rest[:j] + rest[j + 1:]
                break
    # sources
    for j, (name, el) in enumerate(rest):
        if name in ('h2', 'h3') and text(el).strip().lower() in ('sources', 'book sources'):
            for n2, e2 in rest[j + 1:]:
                if n2 in ('ul', 'ol'):
                    art['sources'] += [li.decode_contents().strip() for li in e2.find_all('li')]
                elif n2 == 'p':
                    art['sources'].append(e2.decode_contents().strip())
            rest = rest[:j]
            break
    art['body'] = rest
    ib = dict((k.lower(), v) for k, v in art['infobox'])
    art['type'] = BeautifulSoup(ib.get('type', ''), 'html.parser').get_text().strip() or infer_type(art)
    art['category'] = category_for(art['type'])
    art['part_of'] = ib.get('part of', '')
    art['slug'] = slugify(art['title'])
    # plain lead for search and cards
    lead = []
    for name, el in rest:
        if name == 'p':
            lead.append(text(el))
        if name in ('h2', 'h3') and lead:
            break
    art['lead'] = re.sub(r'\[\[([^\]|]+)(?:\|([^\]]+))?\]\]', lambda m: m.group(2) or m.group(1), ' '.join(lead))
    art['headings'] = [text(el) for n, el in rest if n in ('h2', 'h3')]
    return art


# ---------------------------------------------------------------- dates

def parse_date(s):
    s = BeautifulSoup(s, 'html.parser').get_text(' ') if '<' in s else s
    s = s.replace(' ', ' ')
    m = re.search(r'(\d{1,2}) (%s) to \d{1,2} (?:%s) (\d{4})' % (MRX, MRX), s)
    if m:
        return int(m.group(3)), MONTHS.index(m.group(2)) + 1, int(m.group(1))
    m = re.search(r'(\d{1,2})(?: to \d{1,2})? (%s) (\d{4})' % MRX, s)
    if m:
        return int(m.group(3)), MONTHS.index(m.group(2)) + 1, int(m.group(1))
    m = re.search(r'(%s) (\d{4})' % MRX, s)
    if m:
        return int(m.group(2)), MONTHS.index(m.group(1)) + 1, 0
    m = re.search(r'\b(1[89]\d\d|2[0-5]\d\d)\b', s)
    if m:
        return int(m.group(1)), 0, 0
    return None


def fmt_date(d):
    y, m, dd = d
    if dd:
        return '%d %s %d' % (dd, MONTHS[m - 1][:3], y)
    if m:
        return '%s %d' % (MONTHS[m - 1], y)
    return str(y)


EVENT_KEYS = [
    ('date', '{t}'), ('born', 'Birth of {t}'), ('died', 'Death of {t}'),
    ('settled', '{t} settled'), ('founded', '{t} founded'), ('established', '{t} established'),
    ('dissolved', '{t} dissolved'), ('surrender signed', 'Surrender signed: {t}'),
    ('treaty signed', '{t} signed'), ('date issued', '{t} issued'), ('first human visit', 'First human visit to {t}'),
    ('ended', '{t} ends'), ('refounded', '{t} refounded'), ('surveyed', '{t} surveyed'),
]


def events_for(art):
    ev = []
    for k, v in art['infobox']:
        kl = k.lower()
        for key, label in EVENT_KEYS:
            if kl == key:
                d = parse_date(v)
                if d:
                    ev.append({'y': d[0], 'm': d[1], 'd': d[2], 'label': label.format(t=art['title']),
                               'slug': art['slug'], 'cat': art['category']})
    return ev


# ---------------------------------------------------------------- rendering

RANKS = (r'(?:(?:Grand|Fleet|Vice|Rear|Lieutenant|Major|Brigadier|Air|Supreme|Field|Sub|Chief)\s+)*'
         r'(?:Admiral|General|Commodore|Colonel|Brigadier|Captain|Commander|Major|Lieutenant|Marshal|Sergeant|Premier|'
         r'Prime Minister|President|Chancellor|Governor|Commissioner|Chairman|Chairwoman|Director|Ambassador)')


def strip_rank(s):
    """Drop a leading rank from a commander entry: 'Fleet Admiral [[Chen Wei-lun]]' -> '[[Chen Wei-lun]]'."""
    return re.sub(r'^(\s*(?:<[^>]+>\s*)*)' + RANKS + r'\s+(?=\[\[|\\\[|<|[A-Z])', r'\1', s, count=1)


VOID = ('br', 'img', 'hr')


def split_items(s, colon=False, commas=False):
    """Split an infobox cell into entries at '; ' (and, for lists, at ', ' after a colon or between counts),
    keeping tags balanced. A heading before a colon comes back marked with \\x01."""
    if not s:
        return []
    toks = re.split(r'(<[^>]+>)', s)
    pieces, cur, stack = [], '', []
    depth = 0
    def cut():
        nonlocal cur
        closing = ''.join('</%s>' % re.match(r'<\s*(\w+)', t).group(1) for t in reversed(stack))
        pieces.append(cur + closing)
        cur = ''.join(stack)
    for tok in toks:
        if tok.startswith('<'):
            m = re.match(r'<\s*(/?)\s*(\w+)', tok)
            if m and m.group(2).lower() not in VOID and not tok.endswith('/>'):
                if m.group(1):
                    if stack:
                        stack.pop()
                else:
                    stack.append(tok)
            cur += tok
            continue
        i = 0
        while i < len(tok):
            ch = tok[i]
            two = tok[i:i + 2]
            if two == '[[' or ch == '(':
                depth += 1
            elif two == ']]' or ch == ')':
                depth = max(0, depth - 1)
            if depth == 0 and two == '; ':
                cut(); i += 2; continue
            cur += ch
            i += 1
    pieces.append(cur)
    out = []
    for p in pieces:
        txt = BeautifulSoup(p, 'html.parser').get_text()
        if not txt.strip():
            continue
        # 'Terrestrial Coalition: A' or '244 hulls: 6 battleships, 4 carriers'
        if colon and re.match(r'^[^:(\[]{2,60}:\s', txt) and not re.match(r'^\s*\d{1,2}:\d', txt):
            idx = p.find(': ')
            head, tail = p[:idx], p[idx + 2:]
            out.append('\x01' + head if not commas else head)
            p = tail
        if commas:
            sub = re.split(r', (?![^()]*\))', p)
            if len(sub) > 1 and all(re.match(r'^\s*(?:<[^>]+>)*\s*(?:\d|c\. |about |some |one |two |three |four |five |six |seven |eight |nine |ten |the |a |an )', x, re.I) for x in sub):
                out.extend(x for x in sub if x.strip())
                continue
        out.append(p)
    return out



class Site:
    def __init__(self, arts):
        self.arts = arts
        self.by_slug = {a['slug']: a for a in arts}
        self.alias = {}
        for a in arts:
            self.alias[a['title'].lower()] = a['slug']
        # useful redirects
        extra = {'nomotar incident': 'ciriban-incident', 'battle of exedor': 'battle-of-exedor-disambiguation',
                 'siege of exedor': 'siege-of-hiverion', 'une': 'united-nations-of-earth',
                 'usr': 'unified-solar-republic', 'voor war': 'ciriban-gulf-conflict', 'ciriban gulf war': 'ciriban-gulf-conflict', 'cirban': 'ciriban', 'cirban protocol': 'ciriban-protocol'}
        for k, v in extra.items():
            if v in self.by_slug:
                self.alias.setdefault(k, v)
        # a disambiguation page answers for its bare name unless an article holds that name
        for a in arts:
            t = a['title'].lower()
            if t.endswith(' (disambiguation)'):
                self.alias.setdefault(t[:-len(' (disambiguation)')], a['slug'])

    def resolve(self, name):
        n = html.unescape(name).strip().lower()
        if n in self.alias:
            return self.alias[n]
        s = slugify(n)
        return s if s in self.by_slug else None

    def links(self, s, prefix):
        def rep(m):
            target, label = m.group(1), m.group(2) or m.group(1)
            slug = self.resolve(target)
            if slug:
                return '<a href="%s%s.html">%s</a>' % (prefix, slug, label)
            return '<span class="redlink" title="Not yet in the archive">%s</span>' % label
        s = re.sub(r'\\\[\\\[', '[[', s)
        s = re.sub(r'\\\]\\\]', ']]', s)
        return re.sub(r'\[\[([^\]|]+?)(?:\|([^\]]+?))?\]\]', rep, s)

    # shared chrome
    def head(self, title, root, extra=''):
        return ('<!doctype html><html lang="en"><head><meta charset="utf-8">'
                '<meta name="viewport" content="width=device-width,initial-scale=1">'
                '<title>%s</title>'
                '<link rel="preconnect" href="https://fonts.googleapis.com">'
                '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Jost:ital,wght@0,300;0,400;0,500;0,600;1,400&display=swap">'
                '<link rel="stylesheet" href="%sassets/site.css">%s</head><body>') % (html.escape(title), root, extra)

    def header(self, root, current=''):
        nav = [('Eras', root + 'index.html#eras', 'eras'), ('Atlas', root + 'atlas.html', 'atlas'),
               ('Timeline', root + 'timeline.html', 'timeline'), ('Index', root + 'a-z.html', 'index')]
        n = ''.join('<a href="%s"%s>%s</a>' % (h, ' aria-current="page"' if k == current else '', t) for t, h, k in nav)
        return ('<header class="site-header"><a class="brand" href="%sindex.html"><b>SOLAR ETERNAL</b><span>ARCHIVE</span></a>'
                '<form class="search" role="search" action="%ssearch.html"><label class="sr" for="q">Search the archive</label>'
                '<input id="q" name="q" type="search" placeholder="Search the archive" autocomplete="off">'
                '<div class="search-results" id="search-results"></div></form>'
                '<nav class="primary-nav" aria-label="Primary">%s</nav></header>') % (root, root, n)

    def footer(self, root):
        return ('<footer class="site-footer"><span>Solar Eternal is a work of fiction by Lewis Brewer.</span>'
                '<a href="%sabout.html">About the archive</a><a href="https://blog.lewisbrewer.com">blog.lewisbrewer.com</a></footer>'
                '<script>window.ARCHIVE_ROOT=%s;</script><script src="%sassets/search.js" defer></script></body></html>') % (root, json.dumps(root), root)

    # article page
    root_for_infobox = '../'

    def render_infobox(self, art):
        if not art['infobox']:
            return ''
        rows = [(k, self.links(v, '')) for k, v in art['infobox']]
        d = dict((k.lower(), v) for k, v in rows)
        head_small = art['part_of'] and ('Part of ' + BeautifulSoup(self.links(art['part_of'], ''), 'html.parser').get_text()) or art['type']
        out = ['<aside class="infobox" aria-label="Summary"><div class="ib-head"><small>%s</small><b>%s</b></div>' %
               (html.escape(head_small), html.escape(art['title']))]
        # a flag or emblem drawn for the article, kept in static/flags/<slug>.svg
        for ext in ('svg', 'png'):
            if os.path.exists(os.path.join(STATIC, 'flags', '%s.%s' % (art['slug'], ext))):
                out.append('<figure class="ib-flag"><img src="%sassets/flags/%s.%s" alt="Flag of the %s"></figure>' %
                           (self.root_for_infobox, art['slug'], ext, html.escape(art['title'])))
                break
        # a company logo, kept in static/logos/<slug>.svg
        for ext in ('svg', 'png'):
            if os.path.exists(os.path.join(STATIC, 'logos', '%s.%s' % (art['slug'], ext))):
                out.append('<figure class="ib-flag ib-logo"><img src="%sassets/logos/%s.%s" alt="Logo of %s"></figure>' %
                           (self.root_for_infobox, art['slug'], ext, html.escape(art['title'])))
                break
        used = set(['type'])
        if art['part_of']:
            used.add('part of')
        year = None
        for k, v in art['infobox']:
            if k.lower() in ('date', 'founded', 'declared', 'formed'):
                dd = parse_date(v)
                if dd:
                    year = dd[0]
                    break
        # sides: Wikipedia-style section boxes put "Coalition | ..." rows under each section heading
        raw = art['infobox']
        sides = []
        cur = None
        for k, v in raw:
            if k == SECTION:
                cur = BeautifulSoup(v, 'html.parser').get_text().strip().lower()
            elif cur == 'belligerents' and k not in sides:
                sides.append(k)
        side_flags = {}
        out_blocks = []      # ('sec', title) | ('dl', k, v) | ('pair', title, a, b, kind)
        cur = None
        pending = None
        groups = {}
        for k, v in raw:
            m = re.match(r'(.+?) \((.+)\)$', k)
            if m:
                groups.setdefault(m.group(1), []).append((m.group(2), v))
        done_groups = set()
        i = 0
        while i < len(raw):
            k, v = raw[i]
            kl = k.lower()
            if k == SECTION:
                cur = BeautifulSoup(v, 'html.parser').get_text().strip()
                out_blocks.append(('sec', cur))
                i += 1
                continue
            if kl in used:
                i += 1
                continue
            if sides and k in sides and cur:
                vals = {}
                while i < len(raw) and raw[i][0] in sides:
                    vals[raw[i][0]] = raw[i][1]
                    i += 1
                out_blocks.append(('pair', cur, vals.get(sides[0], ''), vals.get(sides[1], '') if len(sides) > 1 else '', [cur] + sides[:2]))
                continue
            if kl == 'belligerents' and ' / ' in BeautifulSoup(v, 'html.parser').get_text():
                parts = re.split(r'\s+/\s+', v, maxsplit=1)
                out_blocks.append(('pair', 'Belligerents', parts[0], parts[1], ['Belligerents']))
                i += 1
                continue
            m = re.match(r'(.+?) \((.+)\)$', k)
            if m and len(groups.get(m.group(1), [])) == 2:
                g = m.group(1)
                if g not in done_groups:
                    done_groups.add(g)
                    lst = groups[g]
                    out_blocks.append(('pair', g, lst[0][1], lst[1][1], [g]))
                i += 1
                continue
            out_blocks.append(('dl', k, v))
            i += 1
        # drop a section heading with nothing under it
        ob = []
        for j, blk in enumerate(out_blocks):
            if blk[0] == 'sec' and (j + 1 >= len(out_blocks) or out_blocks[j + 1][0] == 'sec'):
                continue
            ob.append(blk)
        # the flag each side falls back on: its single flagged belligerent
        for blk in ob:
            if blk[0] == 'pair' and blk[1].lower() == 'belligerents':
                for col, cell in ((0, blk[2]), (1, blk[3])):
                    fl = set()
                    for piece in split_items(cell, colon=True):
                        f = self.item_key(piece, year, None)
                        if f:
                            fl.add(FL.CONFED if f in FL.AREA_KEYS else f)
                    if len(fl) == 1:
                        side_flags[col] = fl.pop()
        dl = []
        def flush():
            if dl:
                out.append('<dl>' + ''.join(dl) + '</dl>')
                del dl[:]
        for blk in ob:
            if blk[0] == 'sec':
                flush()
                out.append('<p class="ib-sec">%s</p>' % html.escape(blk[1]))
            elif blk[0] == 'dl':
                dl.append('<dt>%s</dt><dd>%s</dd>' % (html.escape(blk[1]), self.links(blk[2], '')))
            else:
                flush()
                title = blk[1]
                tl = title.lower()
                kind = ('list' if re.match(r'(strength|casualt|loss|losses)', tl) else
                        'people' if re.search(r'command|leader|signator', tl) else 'flags')
                in_sec = sides and blk[4][0] == title and len(blk[4]) > 1
                head = '' if (in_sec and ob.index(blk) > 0 and ob[ob.index(blk) - 1] == ('sec', title)) else '<p class="h">%s</p>' % html.escape(title)
                cols = []
                for col, cell in ((0, blk[2]), (1, blk[3])):
                    cols.append('<div class="col">%s</div>' % self.render_items(cell, kind, year, side_flags.get(col)))
                out.append('<div class="pair">%s%s</div>' % (head, ''.join(cols)))
        flush()
        sys_id = self.atlas_system(art)
        if sys_id:
            yr = None
            for k, v in art['infobox']:
                if k.lower() in ('date', 'settled'):
                    d = parse_date(v)
                    if d:
                        yr = d[0]
                        break
            out.append('<a class="ib-atlas" href="%satlas.html#%ssys=%s">Open in the Atlas</a>' % (self.root_for_infobox, ('year=%d&amp;' % yr) if yr and 2050 <= yr <= 2515 else '', sys_id))
        out.append('</aside>')
        return ''.join(out)

    def item_flag(self, piece, year, fallback):
        """The flag file for one infobox entry, or None. fallback is a side's flag key."""
        k = self.item_key(piece, year, fallback)
        return FL.flag_file(k) if k else None

    def person_field(self, slug, names):
        a = self.by_slug.get(slug)
        if not a or a.get('category') != 'people':
            return None
        for kk, vv in a['infobox']:
            if kk.lower() in names:
                return vv.replace('\\[', '[').replace('\\]', ']')
        return None

    def item_key(self, piece, year, fallback):
        s = piece.replace('\\[', '[').replace('\\]', ']')
        plain = BeautifulSoup(s, 'html.parser').get_text()
        m = re.match(r'\s*\{([a-z-]+)\}', plain)
        if m:
            key = FL.TAGS.get(m.group(1), m.group(1))
            return FL.settle(key, year) if key else None
        people = []
        key = None
        for lm in re.finditer(r'\[\[([^\]|]+)', s):
            slug = self.resolve(lm.group(1))
            if not slug:
                continue
            if FL.flag_file(slug) or slug in FL.BLOC:
                key = FL.settle(slug, year)
                if key:
                    break
            if self.by_slug.get(slug, {}).get('category') == 'people':
                people.append(slug)
        if not key:
            for slug in people:
                vv = self.person_field(slug, ('allegiance', 'nationality', 'country')) or ''
                for am in re.finditer(r'\[\[([^\]|]+)', vv):
                    s2 = self.resolve(am.group(1))
                    if s2 and FL.settle(s2, year):
                        key = FL.settle(s2, year)
                        break
                if not key and vv:
                    k2 = FL.by_pattern(BeautifulSoup(vv, 'html.parser').get_text())
                    key = FL.settle(k2, year) if k2 else None
                if key:
                    break
        bare = re.sub(r'\[\[([^\]|]+)(?:\|([^\]]+))?\]\]', lambda m: m.group(2) or m.group(1), strip_rank(plain))
        name = re.sub(r'\s*[†(,].*$', '', bare).strip().lower()
        named = FL.NAMES.get(name)
        if not key and named:
            key = FL.settle(named, year)
        if not key:
            k2 = FL.by_pattern(plain)
            key = FL.settle(k2, year) if k2 else None
        if not key:
            key = fallback
        # the Confederation's forces fly their home area's flag
        if key == FL.CONFED and (not year or 2220 <= year <= 2252):
            area = named if named in FL.AREA_KEYS else None
            if not area:
                for slug in people:
                    born = self.person_field(slug, ('born', 'origin', 'home'))
                    area = FL.area_for(BeautifulSoup(born or '', 'html.parser').get_text())
                    if area:
                        break
            area = area or FL.area_for(plain)
            if area and FL.flag_file(area):
                key = area
        return key or None

    def render_items(self, cell, kind, year, fallback):
        out = []
        for piece in split_items(cell, colon=True, commas=(kind == 'list')):
            if piece.startswith('\x01'):     # a heading line before a colon
                out.append('<span class="it it-h">%s</span>' % self.links(piece[1:], ''))
                continue
            fk = None if kind == 'list' else self.item_key(piece, year, fallback)
            fl = FL.flag_file(fk) if fk else None
            body = re.sub(r'^(\s*)\{[a-z-]+\}\s*', r'\1', piece)
            if kind == 'people':
                body = strip_rank(body)
            img = ''
            if fl:
                target = self.resolve(FL.LINK.get(fk, fk)) or (fk if fk in self.by_slug else None)
                title = self.by_slug[target]['title'] if target else ''
                img = '<img class="fl" src="%sassets/flags/%s" alt="%s">' % (self.root_for_infobox, fl, html.escape(title))
                if target:
                    img = '<a class="fl-a" href="%s.html" title="%s">%s</a>' % (target, html.escape(title), img)
            if kind != 'list' and not fl:
                img = '<span class="fl fl-none"></span>'
            text_html = self.links(body.strip(), '')
            # a bare name that is an article title becomes a link
            if '<a ' not in text_html and '[[' not in body:
                bare = BeautifulSoup(text_html, 'html.parser').get_text().strip()
                slug = self.resolve(bare) if bare and len(bare) < 60 else None
                if slug:
                    text_html = '<a href="%s.html">%s</a>' % (slug, text_html)
            out.append('<span class="it">%s<span>%s</span></span>' % (img, text_html))
        return ''.join(out)

    def atlas_system(self, art):
        ids = ATLAS_IDS
        if not ids:
            return None
        if art['slug'] in ids:
            return art['slug']
        for k, v in art['infobox']:
            if k.lower() in ('system', 'location'):
                for m in re.finditer(r'\[\[([^\]|]+)', v.replace('\\[', '[').replace('\\]', ']')):
                    s = slugify(m.group(1))
                    if s in ids:
                        return s
        return None

    def render_body(self, art, prefix):
        out, toc, used_ids = [], [], set()
        for name, el in art['body']:
            if name in ('h2', 'h3', 'h4'):
                t = text(el)
                hid = slugify(t)
                while hid in used_ids:
                    hid += '-x'
                used_ids.add(hid)
                if name != 'h4':
                    toc.append((name, hid, t))
                out.append('<%s id="%s">%s</%s>' % (name, hid, html.escape(t), name))
            elif name == 'table':
                rows = el.find_all('tr')
                t = ['<div class="table-wrap"><table>']
                for ri, r in enumerate(rows):
                    cells = r.find_all(['td', 'th'])
                    is_head = ri == 0 and all((c.find('b') and text(c.find('b')) == text(c)) or not text(c) for c in cells)
                    tag = 'th' if is_head else 'td'
                    t.append('<tr>' + ''.join('<%s>%s</%s>' % (tag, c.decode_contents().replace('<b></b>', ''), tag) for c in cells) + '</tr>')
                t.append('</table></div>')
                out.append(''.join(t))
            elif name in ('p', 'ul', 'ol', 'blockquote', 'figure'):
                out.append(str(el) if isinstance(el, Tag) else '<p>%s</p>' % el)
            elif name == 'h1':
                continue
            else:
                out.append(str(el))
        htmlbody = self.links('\n'.join(out), prefix)
        # bold the first mention of the title in the lead
        return htmlbody, toc

    def article_page(self, art):
        body, toc = self.render_body(art, '')
        cat = dict((c[0], c[1]) for c in CATEGORIES)[art['category']]
        crumbs = ['<a href="../category/%s.html">%s</a>' % (art['category'], html.escape(cat))]
        if art['part_of']:
            first = re.split(r',\s*', art['part_of'])[0]
            crumbs.insert(0, self.links(first, ''))
        tocs = ['<a href="#top" class="on">(Top)</a>'] + ['<a href="#%s"%s>%s</a>' % (h, ' class="sub"' if n == 'h3' else '', html.escape(t)) for n, h, t in toc]
        if art['sources']:
            tocs.append('<a href="#sources">Sources</a>')
        epi = ''
        if art['quote']:
            epi = '<figure class="epigraph"><q>%s</q><cite>%s</cite></figure>' % (self.links(art['quote'], ''), self.links(art['quote_src'] or '', ''))
        src = ''
        if art['sources']:
            src = '<section class="sources" id="sources"><h2>BOOK SOURCES</h2><ol>%s</ol></section>' % ''.join('<li>%s</li>' % s for s in art['sources'])
        series = self.series_box(art)
        h = [self.head('%s: Solar Eternal Archive' % art['title'], '../'), self.header('../'),
             '<div class="page"><nav class="toc" aria-label="Contents"><p class="label">Contents</p>%s</nav>' % ''.join(tocs),
             '<main class="article" id="top"><div class="title-block"><p class="crumbs">%s</p><h1>%s</h1>' % (' / '.join(crumbs), html.escape(art['title'])),
             '<div class="tabs"><a href="#top" class="on">Article</a>%s</div></div>' % ('<a href="#sources">Book sources</a>' if art['sources'] else ''),
             '<div class="columns"><div class="prose">%s%s%s</div>%s</div>%s</main></div>' % (epi, body, src, self.render_infobox(art), series),
             '<script src="../assets/toc.js" defer></script>',
             self.footer('../')]
        return ''.join(h)

    def series_box(self, art):
        if not art['part_of']:
            return ''
        key = re.split(r',\s*', art['part_of'])[-1]
        target = re.sub(r'\[\[([^\]|]+)(?:\|[^\]]+)?\]\]', r'\1', key).strip()
        mates = [a for a in self.arts if a['part_of'] and target.lower() in re.sub(r'\[\[([^\]|]+)(?:\|[^\]]+)?\]\]', r'\1', a['part_of']).lower()]
        if len(mates) < 2:
            return ''
        mates.sort(key=lambda a: self.first_date(a) or (9999, 0, 0))
        items = ''.join('<span>%s</span>' % html.escape(a['title']) if a is art else '<a href="%s.html">%s</a>' % (a['slug'], html.escape(a['title'])) for a in mates)
        return '<nav class="series" aria-label="%s"><p>%s</p><div>%s</div></nav>' % (html.escape(target), html.escape(target), items)

    def first_date(self, a):
        for k, v in a['infobox']:
            if k.lower() in ('date', 'born', 'settled', 'founded', 'established', 'treaty signed', 'date issued'):
                d = parse_date(v)
                if d:
                    return d
        return None

    # listing pages
    def listing(self, title, inner, root, current=''):
        return self.head('%s: Solar Eternal Archive' % title, root) + self.header(root, current) + '<main class="listing">' + inner + '</main>' + self.footer(root)

    def entry(self, a, prefix):
        return '<li><a href="%s%s.html">%s<small>%s</small></a></li>' % (prefix, a['slug'], html.escape(a['title']), html.escape(a['type'] or ''))

    def az_page(self):
        arts = sorted(self.arts, key=lambda a: re.sub(r'^(the |battle of |siege of |fall of )', '', a['title'].lower()))
        groups = {}
        for a in sorted(self.arts, key=lambda a: a['title'].lower()):
            groups.setdefault(a['title'][0].upper(), []).append(a)
        letters = ''.join(('<a href="#%s">%s</a>' % (L, L)) if L in groups else '<span>%s</span>' % L for L in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ')
        inner = '<h1>Index</h1><p class="intro">Every article in the archive, %d in all.</p><div class="az-letters">%s</div>' % (len(self.arts), letters)
        for L in sorted(groups):
            inner += '<section class="az-group" id="%s"><h2>%s</h2><ul class="entries">%s</ul></section>' % (L, L, ''.join(self.entry(a, 'wiki/') for a in groups[L]))
        return self.listing('Index', inner, '', 'index')

    def category_page(self, key, name, desc):
        arts = sorted([a for a in self.arts if a['category'] == key], key=lambda a: a['title'].lower())
        chips = ''.join('<a href="%s.html"%s>%s</a>' % (k, ' class="on"' if k == key else '', n) for k, n, d in CATEGORIES if any(a['category'] == k for a in self.arts))
        inner = '<h1>%s</h1><p class="intro">%s</p><div class="chips">%s</div><ul class="entries">%s</ul>' % (name, desc, chips, ''.join(self.entry(a, '../wiki/') for a in arts))
        return self.listing(name, inner, '../', 'index')

    def events(self):
        ev = []
        for a in self.arts:
            ev += events_for(a)
        ev.sort(key=lambda e: (e['y'], e['m'], e['d'], e['label']))
        return ev

    def timeline_page(self):
        ev = self.events()
        inner = '<h1>Timeline</h1><p class="intro">A chronology drawn from the archive\'s articles: battles, foundings, births, deaths and treaties.</p><ol class="timeline">'
        last = None
        for e in ev:
            if e['y'] != last:
                inner += '<li class="yr" id="y%d">%d</li>' % (e['y'], e['y'])
                last = e['y']
            inner += '<li class="ev"><time>%s</time><span><a href="wiki/%s.html">%s</a></span></li>' % (fmt_date((e['y'], e['m'], e['d'])), e['slug'], html.escape(e['label']))
        inner += '</ol>'
        return self.listing('Timeline', inner, '', 'timeline')

    def search_page(self):
        inner = ('<h1>Search</h1><p class="intro" id="search-summary">Search the archive by title or text.</p>'
                 '<div id="search-page-results"></div>')
        return self.listing('Search', inner, '', '')

    def about_page(self):
        inner = ('<h1>About the archive</h1><div class="prose" style="max-width:760px">'
                 '<p>The Solar Eternal Archive is an encyclopedia of a fictional future history, from the founding of the United Nations to the Reconstruction of the Second Republic. It is written in the voice of the Republic\'s own histories.</p>'
                 '<p>Its articles are drawn from <i>Solar Eternal</i>, a history by Lewis Brewer, and each article lists the sections of the book it is drawn from. Where the book is silent, the archive fills gaps in keeping with it.</p>'
                 '<p>The Atlas places every charted system of known space, after the reference chart of 2235, and lets you travel through the centuries to watch the borders move.</p></div>')
        return self.listing('About', inner, '', '')

    def home_page(self, updated):
        featured = self.by_slug.get('battle-of-the-mog') or self.by_slug.get('second-battle-of-media') or self.arts[0]
        ev = [e for e in self.events() if 2317 <= e['y'] <= 2341][:6] or self.events()[:6]
        tl = ''.join('<li><time>%s</time><span><a href="wiki/%s.html">%s</a></span></li>' % (fmt_date((e['y'], e['m'], e['d'])), e['slug'], html.escape(e['label'])) for e in ev)
        eras = ''.join('<a href="timeline.html#y%d"><small>%s</small><span>%s</span></a>' % (self.first_year_from(y0), html.escape(lbl), html.escape(name)) for lbl, name, y0, y1 in ERAS)
        counts = {}
        for a in self.arts:
            counts[a['category']] = counts.get(a['category'], 0) + 1
        browse = ''.join('<li><a href="category/%s.html">%s<em>%d</em></a></li>' % (k, n, counts[k]) for k, n, d in CATEGORIES if counts.get(k))
        quote = '<blockquote>%s</blockquote>' % self.links(featured['quote'], 'wiki/') if featured.get('quote') else ''
        inner = (
            '<main class="home"><section class="hero"><p class="label">1945 – 2510 · From the United Nations to the Second Republic</p>'
            '<h1>The Solar Eternal Archive</h1><p class="lede">An encyclopedia of human history from the founding of the United Nations to the Reconstruction, and of the peoples humanity met among the stars.</p>'
            '<p class="meta">%d articles · last updated %s</p></section>'
            '<div class="row"><article class="card featured"><p class="label" style="color:#fff">Featured article</p>%s'
            '<h2><a href="wiki/%s.html">%s</a></h2><p>%s</p><a href="wiki/%s.html" style="text-decoration:none;padding:12px 0">Read the article</a></article>'
            '<aside class="from-timeline"><p class="label">From the timeline</p><ol class="tl-mini">%s</ol><a href="timeline.html" style="text-decoration:none;padding:12px 0">Full timeline</a></aside></div>'
            '<section class="eras" id="eras"><h2>Eras</h2><div class="era-grid">%s</div></section>'
            '<div class="row"><section class="browse" id="browse"><h2>Browse</h2><ul>%s<li><a href="a-z.html">All articles, A to Z<em>%d</em></a></li></ul></section>'
            '<a class="card atlas-card" href="atlas.html"><span class="k">THE ATLAS</span>%s<span class="t">Known space in three dimensions</span>'
            '<span class="d">Every charted system, from Sol to the Ibannic Veil. Drag the timeline to travel through the centuries and watch the borders move.</span><span>Open the Atlas</span></a></div></main>'
        ) % (len(self.arts), updated, quote, featured['slug'], html.escape(featured['title']), html.escape(cut_sentences(featured['lead'], 520)),
             featured['slug'], tl, eras, browse, len(self.arts), ATLAS_SVG)
        return self.head('Solar Eternal Archive', '') + self.header('', '') + inner + self.footer('')

    def first_year_from(self, y0):
        ys = sorted(set(e['y'] for e in self.events() if e['y'] >= y0))
        return ys[0] if ys else y0

    def search_index(self):
        return [{'t': a['title'], 'u': 'wiki/%s.html' % a['slug'], 'c': a['type'], 'x': a['lead'][:400],
                 'h': ' '.join(a['headings'])} for a in self.arts]


ATLAS_SVG = ('<svg viewBox="0 0 480 200" style="width:100%;height:auto;display:block" aria-hidden="true">'
             '<g stroke="#1E3A5F" stroke-width="1" fill="none"><path d="M20 170 L460 170 M60 140 L420 140 M100 110 L380 110 M140 80 L340 80"/>'
             '<path d="M60 170 L140 80 M160 170 L200 80 M260 170 L260 80 M360 170 L320 80 M440 170 L360 80"/></g>'
             '<g stroke="rgba(255,255,255,0.35)" stroke-width="1"><line x1="120" y1="104" x2="120" y2="146"/><line x1="210" y1="70" x2="210" y2="120"/>'
             '<line x1="300" y1="92" x2="300" y2="132"/><line x1="380" y1="60" x2="380" y2="118"/></g>'
             '<circle cx="120" cy="104" r="4" fill="#fff"/><circle cx="210" cy="70" r="3" fill="#fff"/><circle cx="300" cy="92" r="3.5" fill="#C9B6E8"/><circle cx="380" cy="60" r="5" fill="#C9B6E8"/></svg>')


def main():
    if os.path.exists(OUT):
        shutil.rmtree(OUT)
    os.makedirs(os.path.join(OUT, 'wiki'))
    os.makedirs(os.path.join(OUT, 'category'))
    shutil.copytree(STATIC, os.path.join(OUT, 'assets'))
    files = sorted(f for f in os.listdir(SRC) if f.endswith('.html'))
    arts = []
    for f in files:
        try:
            a = parse_article(os.path.join(SRC, f))
        except Exception as e:  # keep going; report at the end
            print('SKIP', f, e, file=sys.stderr)
            continue
        if a['title'].lower().startswith('_old draft'):
            continue
        arts.append(a)
    # duplicate titles: keep the longest
    seen = {}
    for a in arts:
        if a['slug'] in seen and len(str(seen[a['slug']]['body'])) >= len(str(a['body'])):
            continue
        seen[a['slug']] = a
    arts = list(seen.values())
    site = Site(arts)
    updated = datetime.date.today().strftime('%-d %B %Y')
    for a in arts:
        open(os.path.join(OUT, 'wiki', a['slug'] + '.html'), 'w').write(site.article_page(a))
    open(os.path.join(OUT, 'index.html'), 'w').write(site.home_page(updated))
    open(os.path.join(OUT, 'a-z.html'), 'w').write(site.az_page())
    open(os.path.join(OUT, 'timeline.html'), 'w').write(site.timeline_page())
    open(os.path.join(OUT, 'search.html'), 'w').write(site.search_page())
    open(os.path.join(OUT, 'about.html'), 'w').write(site.about_page())
    for k, n, d in CATEGORIES:
        open(os.path.join(OUT, 'category', k + '.html'), 'w').write(site.category_page(k, n, d))
    json.dump(site.search_index(), open(os.path.join(OUT, 'assets', 'search-index.json'), 'w'))
    json.dump(site.events(), open(os.path.join(OUT, 'assets', 'events.json'), 'w'))
    json.dump({a['slug']: a['title'] for a in arts}, open(os.path.join(OUT, 'assets', 'articles.json'), 'w'))
    # the atlas is a static app with its own data
    atlas_src = os.path.join(ROOT, 'atlas')
    if os.path.exists(atlas_src):
        # stamp each asset with a hash of its contents so browsers fetch the new copy after a deploy
        import hashlib
        def ver(f):
            return hashlib.sha1(open(os.path.join(atlas_src, f), 'rb').read()).hexdigest()[:10]
        stamps = {f: ver(f) for f in ('atlas.css', 'atlas-data.json') if os.path.exists(os.path.join(atlas_src, f))}
        js = open(os.path.join(atlas_src, 'atlas.js'), encoding='utf-8').read()
        if 'atlas-data.json' in stamps:
            js = js.replace("'assets/atlas-data.json'", "'assets/atlas-data.json?v=%s'" % stamps['atlas-data.json'])
        stamps['atlas.js'] = hashlib.sha1(js.encode('utf-8')).hexdigest()[:10]
        for f in os.listdir(atlas_src):
            p = os.path.join(atlas_src, f)
            if f == 'atlas.html':
                page = open(p, encoding='utf-8').read()
                for name, v in stamps.items():
                    page = page.replace('"assets/%s"' % name, '"assets/%s?v=%s"' % (name, v))
                open(os.path.join(OUT, 'atlas.html'), 'w', encoding='utf-8').write(page)
            elif f == 'atlas.js':
                open(os.path.join(OUT, 'assets', f), 'w', encoding='utf-8').write(js)
            elif os.path.isfile(p) and not f.endswith('.py'):
                shutil.copy(p, os.path.join(OUT, 'assets', f))
    if os.environ.get('SITE_CNAME'):
        open(os.path.join(OUT, 'CNAME'), 'w').write(os.environ['SITE_CNAME'] + '\n')
    print('Built %d articles into %s' % (len(arts), OUT))


if __name__ == '__main__':
    main()
