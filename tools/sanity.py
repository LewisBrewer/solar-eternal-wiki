"""Sanity report on the built infoboxes. Prints problems to the build log; never fails the build.

Checks, per article page:
  1. a unit, commander or strength flag that is one of the other side's belligerent flags
  2. the Martian-Jovian Confederation's flag on a page dated before 2224
  3. a belligerent with no flag
  4. a flag link to a page that does not exist
  5. a Units involved column whose flags all belong to the other side
"""
import os, re, sys
from bs4 import BeautifulSoup

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, 'out')
WIKI = os.path.join(OUT, 'wiki')

CONFED = {'martian-jovian-confederation', 'league-for-jovian-rule', 'mars', 'free-io', 'free-europa',
          'free-ganymede', 'free-callisto', 'free-luna'}


def fam(k):
    return 'CONFED' if k in CONFED else k


def key(img):
    return os.path.splitext(os.path.basename(img.get('src', '')))[0]


def first_year(ib):
    for dt in ib.select('dt'):
        if dt.get_text().strip().lower() == 'date':
            m = re.search(r'\b(2\d{3})\b', dt.find_next_sibling('dd').get_text())
            return int(m.group(1)) if m else None
    return None


def main():
    pages = set(os.listdir(WIKI))
    problems = []
    for fn in sorted(pages):
        if not fn.endswith('.html'):
            continue
        soup = BeautifulSoup(open(os.path.join(WIKI, fn), encoding='utf-8').read(), 'html.parser')
        ib = soup.select_one('aside.infobox')
        if not ib:
            continue
        name = fn[:-5]
        year = first_year(ib)
        bel = [set(), set()]
        for pair in ib.select('div.pair'):
            h = pair.select_one('p.h')
            if h and h.get_text().strip().lower() == 'belligerents':
                for c, col in enumerate(pair.select(':scope > div.col')[:2]):
                    for it in col.select('span.it'):
                        if 'it-h' in (it.get('class') or []):
                            continue
                        img = it.select_one('img.fl')
                        if img:
                            bel[c].add(fam(key(img)))
                        else:
                            problems.append((name, 'belligerent without a flag: %s' % it.get_text(' ', strip=True)[:60]))
        for pair in ib.select('div.pair'):
            h = pair.select_one('p.h')
            label = h.get_text().strip() if h else 'Units involved'
            if label.lower() == 'belligerents':
                continue
            for c, col in enumerate(pair.select(':scope > div.col')[:2]):
                keys = []
                for img in col.select('img.fl'):
                    k = fam(key(img))
                    keys.append(k)
                    other = bel[1 - c] - bel[c]
                    if k in other:
                        it = img.find_parent(class_='it')
                        problems.append((name, '%s, column %d: "%s" flies the other side\'s flag (%s)'
                                         % (label, c + 1, it.get_text(' ', strip=True)[:60] if it else '?', key(img))))
                if keys and bel[1 - c] and all(k in bel[1 - c] - bel[c] for k in keys):
                    problems.append((name, '%s, column %d: every flag belongs to the other side' % (label, c + 1)))
        if year and year < 2224:
            for img in ib.select('img.fl'):
                if key(img) == 'martian-jovian-confederation':
                    it = img.find_parent(class_='it')
                    problems.append((name, 'Confederation flag in %d: %s' % (year, it.get_text(' ', strip=True)[:60] if it else '?')))
        for a in soup.select('a.fl-a'):
            href = a.get('href', '')
            if href and not href.startswith(('http', '#', '..')) and href.split('#')[0] not in pages:
                problems.append((name, 'flag links to a missing page: %s' % href))
    print('=== Infobox sanity report: %d problems ===' % len(problems))
    for n, p in problems:
        print('SANITY %s: %s' % (n, p))


if __name__ == '__main__':
    main()
