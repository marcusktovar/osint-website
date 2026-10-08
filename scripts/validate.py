#!/usr/bin/env python3
"""Validate public JSON before it can be uploaded to GitHub Pages."""
import json
from pathlib import Path
from urllib.parse import urlparse

FILE = Path(__file__).resolve().parents[1] / 'site' / 'data' / 'sections.json'
content = json.loads(FILE.read_text(encoding='utf8'))
assert len(content['sections']) == 6, 'Must have six sections'
assert len(content['stats']) == 4, 'Must have four headline stats'
assert all(x.get('title') and x.get('paragraphs') for x in content['sections'])
assert len({s['id'] for s in content['sections']}) == len(content['sections'])
assert content['sources'], 'Source reference library missing'
for section in content['sections']:
    for para in section['paragraphs']:
        assert 20 <= len(para['text']) <= 1200, f"Suspicious paragraph in {section['id']}"
        assert para['sources'], 'Paragraph missing citations'
        for src in para['sources']:
            assert src in content['sources'], f'Unknown source: {src}'
for src in content['sources'].values():
    parsed = urlparse(src['url'])
    assert parsed.scheme == 'https' and parsed.netloc, 'Invalid source URL'
print('PASS: six sections, four statistics, valid paragraph references and URLs')
