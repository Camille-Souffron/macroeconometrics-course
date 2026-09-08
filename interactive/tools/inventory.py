"""Extract chapter headings, methodological sentences and citations once.

Run with --check to detect new or changed course material needing catalog review.
"""
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PATTERN = re.compile(r'\b(test|estimat\w*|prior|parameter|hyperparameter|bootstrap|forecast|filter|identif\w*|regression|GMM|GVAR|VAR|IRF|FEVD|MCMC|quantile|regulari\w*|validation)\b', re.I)

def inventory():
    result = {}
    for path in sorted((ROOT / 'chapters').glob('*.qmd')):
        source = path.read_text()
        prose = re.sub(r'```[\s\S]*?```', '', source)
        result[path.name] = {
            'sha256': hashlib.sha256(source.encode()).hexdigest(),
            'headings': re.findall(r'^#{1,4} (.+)$', prose, re.M),
            'citations': sorted(set(re.findall(r'@([A-Z][A-Za-z0-9]+)', prose))),
            'methods': [line.strip()[:240] for line in prose.splitlines()
                        if PATTERN.search(line) and not line.startswith(('![', '[^'))],
        }
    return result

if __name__ == '__main__':
    destination = ROOT / 'interactive/inventory.json'
    current = inventory()
    if '--check' in sys.argv:
        saved = json.loads(destination.read_text())
        changed = [key for key in current if current[key] != saved.get(key)]
        assert not changed, f'Course changed; review methodological coverage: {changed}'
        print(f'Inventory current: {len(current)} chapters')
    else:
        print(json.dumps(current, indent=2))
