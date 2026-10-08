#!/usr/bin/env python3
"""Sanity checks before publication. Requires Python standard library only."""
from pathlib import Path
import json,sys
root=Path(__file__).resolve().parents[1]
countries=json.loads((root/'site/data/countries.json').read_text(encoding='utf8'))
features=json.loads((root/'site/data/map.json').read_text(encoding='utf8'))
assert isinstance(countries.get('countries'),dict) and len(countries['countries'])>=170,'missing country profiles'
assert isinstance(features,list) and len(features)>=170,'missing geometry'
codes={f['code'] for f in features}
assert all(f.get('path','').startswith('M') for f in features),'missing map shapes'
assert all(code in countries['countries'] for code in codes),'unmatched country codes'
assert countries['countries']['YEM']['notes'].get('history'),'Yemen historical profile missing'
assert sum(bool(c['notes']) for c in countries['countries'].values())>=20,'curated profiles missing'
for code,c in countries['countries'].items():
 assert c.get('name') and c.get('region') and c.get('references'),f'bad metadata {code}'
 for r in c['references']:
  assert r['url'].startswith('https://'),f'invalid outbound source {code}'
 if c.get('population') is not None:
  assert isinstance(c.get('population_year'),int) and c['population_year']<=2100,f'undated population {code}'
for f in ('index.html','style.css','app.js','favicon.svg','.nojekyll'):
 assert (root/'site'/f).exists(),f'missing site/{f}'
print(f"VALID: {len(countries['countries'])} country dossiers; {len(features)} map regions; {sum(bool(c['notes']) for c in countries['countries'].values())} edited profiles; citations and dated stats checked.")
