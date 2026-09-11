"""Copy a verified dashboard build into the retired GitHub Pages frontend.
No crawling, report regeneration, or deployment is performed.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('dashboard', type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    docs = root / 'docs'
    assert (docs / 'old-site/index.html').is_file(), 'Preserve legacy site first'
    build = json.loads((args.dashboard / 'dist/data-app-build.json').read_text())
    for key in ('html', 'snapshot'):
        data = (args.dashboard / 'dist' / build[key]['path']).read_bytes()
        assert hashlib.sha256(data).hexdigest() == build[key]['sha256']
    html = (args.dashboard / 'dist/index.html').read_text()
    # Public visitors must not inherit a machine-local Codex task handoff.
    html = re.sub(r'<meta name="data-app-local-thread"[^>]*>\n?', '', html)
    html = html.replace('<title>', '<link rel="canonical" href="https://frankiejvaldez.com/KingKullenResearch/">\n<meta name="description" content="Final historical King Kullen grocery-price dashboard. Project retired September 6, 2026; data and legacy reports remain available for reference.">\n<title>', 1)
    (docs / 'index.html').write_text(html)
    shutil.copy2(args.dashboard / 'dist' / build['snapshot']['path'], docs / build['snapshot']['path'])
    build['html']['sha256'] = hashlib.sha256((docs / 'index.html').read_bytes()).hexdigest()
    build['html']['bytes'] = (docs / 'index.html').stat().st_size
    (docs / 'data-app-build.json').write_text(json.dumps(build, indent=2)+'\n')
    (docs / '.nojekyll').touch()
    authored = root / 'site-source/dashboard'
    authored.mkdir(parents=True, exist_ok=True)
    for filename in ('DashboardContent.jsx', 'price-model.js', 'dashboard.css'):
        shutil.copy2(args.dashboard / 'src/content/dashboard' / filename, authored / filename)
    shutil.copy2(args.dashboard / 'src/theme.css', authored / 'theme.css')
    print('Packaged verified dashboard and frozen snapshot for /KingKullenResearch/.')

if __name__ == '__main__':
    main()
