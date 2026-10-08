#!/usr/bin/env python3
"""Build a traceable Yemen country guide from curated prose and public data.

No AI key required. Never invents live political information or silently changes
source dates. External requests only run when --offline is not specified.
"""
from __future__ import annotations

import argparse
import copy
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import sys
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / 'site' / 'data' / 'sections.json'
USER_AGENT = 'YemenFieldNotesStarter/1.0 (educational project; https://github.com/)' 
WIKI_ARTICLES = {
    'wiki_yemen': 'Yemen',
    'wiki_geography': 'Geography of Yemen',
    'wiki_history': 'History of Yemen',
    'wiki_politics': 'Politics of Yemen',
    'wiki_culture': 'Culture of Yemen',
}


def read_json(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def fetch_json(url, timeout=18):
    req = Request(url, headers={'User-Agent': USER_AGENT, 'Accept': 'application/json'})
    with urlopen(req, timeout=timeout) as response:
        if response.status != 200:
            raise ValueError(f'HTTP {response.status}')
        return json.load(response)


def get_wikipedia_excerpt(title):
    url = 'https://en.wikipedia.org/w/api.php?' + urlencode({
        'action': 'query', 'format': 'json', 'prop': 'extracts',
        'titles': title, 'exintro': '1', 'explaintext': '1',
        'exchars': '1100', 'redirects': '1', 'formatversion': '2'
    })
    pages = fetch_json(url)['query']['pages']
    extract = pages[0].get('extract', '').strip()
    if not extract:
        raise ValueError(f'No Wikipedia extract found for {title}')
    return extract


def parse_wikidata(entity):
    claims = entity['entities']['Q805']['claims']

    def get_value(prop):
        for statement in claims.get(prop, []):
            if statement.get('rank') == 'deprecated':
                continue
            value = statement.get('mainsnak', {}).get('datavalue', {}).get('value')
            if value is not None:
                return value
        return None

    iso = get_value('P297')
    raw_start = get_value('P571')
    iso_code = iso if isinstance(iso, str) and re.fullmatch(r'[A-Z]{2}', iso) else None
    founding_date = None
    if isinstance(raw_start, dict):
        match = re.search(r'([12]\d{3})-(\d\d)-(\d\d)', raw_start.get('time', ''))
        if match:
            year, month, day = (int(x) for x in match.groups())
            if 1800 <= year <= 2100 and 1 <= month <= 12 and 1 <= day <= 31:
                founding_date = f'{day} {datetime(year, month, day).strftime("%B")} {year}'
    return {'country_code': iso_code, 'inception_date': founding_date}


def parse_population(response):
    if not isinstance(response, list) or len(response) < 2 or not isinstance(response[1], list):
        raise ValueError('Unexpected World Bank response')
    candidates = []
    for item in response[1]:
        try:
            year = int(item.get('date', ''))
            value = item.get('value')
            if value is not None and 1900 <= year <= 2100 and 0 < float(value) < 1_000_000_000:
                candidates.append((year, round(float(value))))
        except (TypeError, ValueError):
            continue
    if not candidates:
        raise ValueError('No usable World Bank population series data')
    year, value = max(candidates)
    return {'year': year, 'value': value, 'source': 'worldbank'}


def compose(editorial, archive, population, wikidata, checked, mode, warnings, checked_at):
    sections = copy.deepcopy(editorial['sections'])
    by_id = {s['id']: s for s in sections}
    facts = archive['facts']

    def add(section_id, sentence, sources):
        by_id[section_id]['paragraphs'].append({'text': sentence, 'sources': sources})

    add('geography',
        f"The archived World Factbook lists Yemen's area as {facts['area_sq_km']:,} square kilometers and its coastline as {facts['coastline_km']:,} kilometers. These are archive figures from {archive['edition_date']}, not measurements refreshed today.",
        ['cia_archive'])

    if wikidata.get('inception_date'):
        add('history',
            f"Wikidata records {wikidata['inception_date']} as the inception date of the modern Republic of Yemen.",
            ['wikidata'])

    if population and population.get('value') and population.get('year'):
        add('people',
            f"For {population['year']}, the World Bank's population series records approximately {population['value']:,} people. The year is essential: this figure is not presented as a real-time census.",
            ['worldbank'])

    # Wikipedia is fetched as a changing corroborating research input, never
    # pasted unedited into prose. These conservative checks only add statements
    # already backed by the editorial research and a linked source.
    wiki_evidence = {
        'overview': ('wiki_yemen', ['arabian', 'peninsula']),
        'geography': ('wiki_geography', ['mountain', 'desert']),
        'history': ('wiki_history', ['saba']),
        'government': ('wiki_politics', ['conflict']),
        'culture': ('wiki_culture', ['arabic']),
    }
    for section_id, (source_id, tokens) in wiki_evidence.items():
        excerpt = checked.get('wiki_excerpts', {}).get(source_id, '').lower()
        by_id[section_id]['encyclopedia_checked'] = (
            bool(excerpt) and all(token in excerpt for token in tokens)
        )

    for section in sections:
        source_ids = []
        for paragraph in section['paragraphs']:
            if not isinstance(paragraph['text'], str) or not paragraph['text'].strip():
                raise ValueError(f"Empty paragraph for {section['id']}")
            for key in paragraph['sources']:
                if key not in editorial['sources']:
                    raise ValueError(f'Unknown source {key}')
                if key not in source_ids:
                    source_ids.append(key)
        section['source_ids'] = source_ids

    population_value = population.get('value') if population else None
    population_year = population.get('year') if population else None
    stats = [
        {'label':'Land area', 'value':f"{facts['area_sq_km']:,}", 'unit':'km²', 'detail':'CIA archived figure · Jan 2026', 'source_id':'cia_archive'},
        {'label':'Population', 'value':f"{population_value / 1_000_000:.1f}M" if population_value else '—',
         'unit':'people', 'detail':f'World Bank · {population_year}' if population_year else 'No verified value', 'source_id':'worldbank'},
        {'label':'World Heritage sites', 'value':'5', 'unit':'UNESCO-listed', 'detail':'UNESCO World Heritage List', 'source_id':'unesco'},
        {'label':'Modern unification', 'value':'1990', 'unit':'year', 'detail':'North and South Yemen', 'source_id':'wikidata'},
    ]
    return {
        'site_name':'Yemen / Field Notes',
        'site_subtitle':'An independent, sourced introduction to Yemen',
        'build_mode':mode,
        'generated_at_utc':checked_at,
        'source_snapshot':archive['edition_date'],
        'edition_note':editorial['edition_note'],
        'stats':stats,
        'sections':sections,
        'sources':editorial['sources'],
        'live_checks':checked.get('live_checks', {}),
        'warnings':warnings,
        'population':population,
        'wikidata':wikidata,
        'methodology':'Curated editorial text combines CIA archive/UNESCO references with live Wikidata and World Bank facts. Wikipedia intros are fetched to corroborate selected themes; no unreviewed generated narrative is published.'
    }


def build(offline=False, now=None, fetcher=fetch_json, wiki_fetcher=None):
    editorial = read_json(ROOT / 'sources' / 'editorial.json')
    archive = read_json(ROOT / 'sources' / 'factbook_archive.json')
    previous = read_json(OUTPUT) if OUTPUT.exists() else {}
    # Transparent seed data from the World Bank page, checked 2026-10-07.
    population = previous.get('population') or {'value':41773878,'year':2025,'source':'worldbank','checked_at':'2026-10-07'}
    wikidata = previous.get('wikidata') or {'country_code':'YE','inception_date':'22 May 1990'}
    checked = {'live_checks':{}, 'wiki_excerpts':{}}
    warnings = []
    now = now or datetime.now(timezone.utc)
    timestamp = now.isoformat(timespec='seconds').replace('+00:00','Z')
    wiki_fetcher = wiki_fetcher or get_wikipedia_excerpt

    if not offline:
        for source_id, article in WIKI_ARTICLES.items():
            try:
                excerpt = wiki_fetcher(article)
                if not isinstance(excerpt, str) or len(excerpt) < 20:
                    raise ValueError('No substantial text returned')
                checked['wiki_excerpts'][source_id] = excerpt
                checked['live_checks'][source_id] = timestamp
            except (HTTPError, URLError, TimeoutError, ValueError, KeyError, OSError) as exc:
                warnings.append(f'Wikipedia article {article}: {type(exc).__name__}')

        try:
            raw = fetcher('https://www.wikidata.org/wiki/Special:EntityData/Q805.json')
            new_wikidata = parse_wikidata(raw)
            if any(new_wikidata.values()):
                wikidata = {**wikidata, **{k:v for k,v in new_wikidata.items() if v}}
            checked['live_checks']['wikidata'] = timestamp
        except (HTTPError, URLError, TimeoutError, ValueError, KeyError, OSError) as exc:
            warnings.append(f'Wikidata: {type(exc).__name__}')

        try:
            raw = fetcher('https://api.worldbank.org/v2/country/YEM/indicator/SP.POP.TOTL?format=json&mrv=12')
            fresh = parse_population(raw)
            # An upstream error should not make an older number appear newer.
            if not population or fresh['year'] >= population['year']:
                population = {**fresh, 'checked_at':timestamp[:10]}
            checked['live_checks']['worldbank'] = timestamp
        except (HTTPError, URLError, TimeoutError, ValueError, KeyError, OSError) as exc:
            warnings.append(f'World Bank: {type(exc).__name__}')

    checks = len(checked['live_checks'])
    mode = 'starter' if offline else ('refreshed' if checks == len(WIKI_ARTICLES) + 2 else 'partial' if checks else 'cached')
    if not offline and checks == 0:
        raise RuntimeError('No external sources could be checked; keeping existing published data unchanged')
    data = compose(editorial, archive, population, wikidata, checked, mode, warnings, timestamp if not offline else '2026-10-07T00:00:00Z')
    if offline:
        data['warnings'] = ['Starter snapshot: the network sources were not queried during packaging. Run build.py to refresh.']
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    return data


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--offline', action='store_true', help='generate using the dated seed and curated source snapshots')
    args = parser.parse_args()
    try:
        data = build(offline=args.offline)
    except Exception as exc:
        print(f'Build failed; last published data preserved: {exc}', file=sys.stderr)
        return 1
    print(f"Created {OUTPUT.relative_to(ROOT)}: {len(data['sections'])} sections, mode={data['build_mode']}")
    for warning in data['warnings']:
        print('Warning:', warning)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
