"""Verify final static publication and preservation of the legacy frontend."""
import hashlib
import json
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit, unquote

root = Path(__file__).resolve().parents[1]
docs = root / 'docs'
manifest = json.loads((root / 'site-source/legacy-manifest.json').read_text())
allowed = set(manifest['intentional_html_edits'])
for name, digest in manifest['files'].items():
    path = docs / 'old-site' / name
    assert path.is_file(), name
    if name not in allowed:
        assert hashlib.sha256(path.read_bytes()).hexdigest() == digest, name

class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.refs = []
    def handle_starttag(self, tag, attrs):
        for key, value in attrs:
            if key in ('href', 'src') and value:
                self.refs.append(value)

for name in allowed:
    path = docs / 'old-site' / name
    html = path.read_text()
    assert 'Project retired' in html and 'September 6, 2026' in html
    parser = Links()
    parser.feed(html)
    for ref in parser.refs:
        url = urlsplit(ref)
        if url.scheme or url.netloc or not url.path:
            continue
        target = (path.parent / unquote(url.path)).resolve()
        assert target.exists(), (name, ref)

build = json.loads((docs / 'data-app-build.json').read_text())
for kind in ('html', 'snapshot'):
    data = (docs / build[kind]['path']).read_bytes()
    assert len(data) == build[kind]['bytes']
    assert hashlib.sha256(data).hexdigest() == build[kind]['sha256']
html = (docs / 'index.html').read_text()
assert 'data-app-local-thread' not in html
assert './old-site/' in html and 'Project retirement notice' in html
assert 'Maintenance, support, and automated updates have ended.' in html
assert (docs / '.nojekyll').exists()
print(f"PASS: {len(manifest['files'])} legacy files preserved; local HTML links resolve; final HTML and frozen snapshot hashes verified.")
