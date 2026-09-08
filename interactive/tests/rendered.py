"""Verify published lab assets, chapter deep links and bibliography targets."""
import json
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit, parse_qs

ROOT = Path(__file__).resolve().parents[2]
BOOK = ROOT / '_book'


class Links(HTMLParser):
    def __init__(self, source):
        super().__init__()
        self.links = []
        self.ids = set()
        self.feed(source)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        self.ids.add(attrs.get('id'))
        for key in ('href', 'src'):
            if key in attrs:
                self.links.append(attrs[key])


catalog = json.loads((ROOT / 'interactive/catalog.json').read_text())
ids = {e['id'] for e in catalog['experiments']}
references = Links((BOOK / 'references.html').read_text()).ids
for experiment in catalog['experiments']:
    assert 'ref-' + experiment['reference'] in references, experiment['reference']
    assert (BOOK / experiment['implementation'].split(':')[0]).is_file()
metadata = json.loads((BOOK / 'interactive/data/metadata.json').read_text())
for dataset in metadata.values():
    for key in ('path', 'join'):
        if key in dataset:
            assert (BOOK / dataset[key]).is_file(), dataset[key]
links_checked = 0
for path in [BOOK / 'interactive-lab.html', BOOK / 'interactive/scope.html', *sorted((BOOK / 'chapters').glob('*.html'))]:
    parsed = Links(path.read_text())
    if path.name != 'interactive-lab.html':
        assert not any('pyodide' in link or 'interactive/js' in link for link in parsed.links), path
    for link in parsed.links:
        parts = urlsplit(link)
        if parts.scheme or parts.netloc or not parts.path:
            continue
        target = (path.parent / unquote(parts.path)).resolve()
        if 'interactive' not in parts.path and path.name!='scope.html':
            continue
        assert target.is_file(), (path, link)
        query = parse_qs(parts.query)
        if 'method' in query:
            assert query['method'][0] in ids, link
        links_checked += 1
assert not list((BOOK / 'interactive').rglob('__pycache__'))
assert not (BOOK / 'interactive/tests').exists()
assert not (BOOK / 'interactive/tools').exists()
assert not (BOOK / 'data/us_ml_time_series_fred.csv').exists(), 'Do not publish the inherited restricted spread column.'
assert not (BOOK / 'data/us_hours_baa_spread_fred.csv').exists(), 'Do not publish the inherited restricted spread column.'
print(f'Rendered assets, {links_checked} lab links and {len(ids)} citation targets verified.')
