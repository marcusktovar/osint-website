#!/usr/bin/env python3
"""Refresh a provenance-aware multi-country dataset for the static atlas.

Offline seed uses the packaged historical CountryInfo reference and curated,
source-linked prose. Online mode enriches it with Rest Countries API metadata,
World Bank population observations and Wikipedia introductory article checks.
Never treats unverified excerpts as published original editorial prose.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, quote
from urllib.request import Request, urlopen

ROOT=Path(__file__).resolve().parents[1]
SEED=ROOT/'sources/base_countries.json'
NOTES=ROOT/'sources/research_notes.json'
OUTPUT=ROOT/'site/data/countries.json'
USER_AGENT='AtlasArchiveEducational/1.0 (GitHub Pages static informational project; contact repository owner)'
COMMON_SOURCES={
 'naturalearth':{'name':'Natural Earth 1:110m','url':'https://www.naturalearthdata.com/about/terms-of-use/'},
 'countryinfo':{'name':'CountryInfo offline reference (undated)','url':'https://github.com/porimol/countryinfo'},
 'restcountries':{'name':'REST Countries API','url':'https://restcountries.com/'},
 'worldbank':{'name':'World Bank population indicator','url':'https://data.worldbank.org/indicator/SP.POP.TOTL'},
 'wikipedia':{'name':'Wikipedia contributors (CC BY-SA)','url':'https://en.wikipedia.org/wiki/Wikipedia:Copyrights'}
}

def load_json(path):
 return json.loads(path.read_text(encoding='utf-8'))

def get_json(url, timeout=18):
 req=Request(url,headers={'User-Agent':USER_AGENT,'Accept':'application/json'})
 with urlopen(req,timeout=timeout) as resp:
  if resp.status!=200:raise ValueError(f'HTTP {resp.status}')
  return json.load(resp)

def clean_restcountries(rows):
 """Return verified structured facts keyed by standard alpha-3 code."""
 if not isinstance(rows,list): raise ValueError('Expected REST Countries list')
 cleaned={}
 for r in rows:
  if not isinstance(r,dict):continue
  key=r.get('cca3')
  if not isinstance(key,str) or len(key)!=3:continue
  cap=r.get('capital')
  capital=', '.join(str(c) for c in cap[:2]) if isinstance(cap,list) else None
  l=r.get('languages');languages=list(l.values())[:5] if isinstance(l,dict) else []
  cur=r.get('currencies');currency=', '.join(list(cur)[:3]) if isinstance(cur,dict) else ''
  area=r.get('area')
  if not isinstance(area,(int,float)) or area<=0 or area>20_000_000:area=None
  cleaned[key]={'capital':capital,'languages':languages,'currency':currency,'area_km2':area,
                 'subregion':r.get('subregion') or '', 'region_api':r.get('region') or ''}
 return cleaned

def parse_worldbank(raw):
 """The most recent valid dated observation per ISO3 code."""
 if not isinstance(raw,list) or len(raw)<2 or not isinstance(raw[1],list):raise ValueError('Invalid World Bank response')
 results={}
 for row in raw[1]:
  if not isinstance(row,dict):continue
  info=row.get('countryiso3code') or ''
  try:
   year=int(row.get('date'));val=float(row.get('value'))
  except (TypeError,ValueError):continue
  if len(info)!=3 or not 1950<=year<=2100 or not 0<val<2_000_000_000:continue
  if info not in results or year>results[info][1]:results[info]=(round(val),year)
 return results

def wikipedia_confirmed(raw):
 """Article availability only; not evidence that a changing government claim is true."""
 if not isinstance(raw,dict):return set()
 pages=raw.get('query',{}).get('pages',[])
 if isinstance(pages,dict):pages=list(pages.values())
 return {p.get('title','') for p in pages if isinstance(p,dict) and 'missing' not in p and p.get('extract')}

def make_dataset(base, notes, *, rest=None, populations=None, wiki_titles=None, timestamp=None, online=False, warnings=None):
 rest=rest or {};populations=populations or {};wiki_titles=wiki_titles or set();warnings=warnings or []
 countries={}
 for code,seed in base.items():
  d={**seed}
  if code in rest:
   info=rest[code]
   for key in ('capital','languages','currency','area_km2','subregion'):
    if info.get(key):d[key]=info[key]
   d['metadata_source']='restcountries'
  if code in populations:
   n,year=populations[code]
   old_year=d.get('population_year') or 0
   if year>=old_year:
    d['population']=n;d['population_year']=year;d['population_source']='worldbank'
  desc=notes.get(code,{})
  d['notes']={k:desc[k] for k in ('overview','history','geography','culture','caution') if desc.get(k)}
  article=desc.get('wiki_page') or d['name']
  # Wiki article links are research references, not automatically copied text.
  d['references']=[{'label':'Wikipedia · '+article,'url':'https://en.wikipedia.org/wiki/'+quote(article.replace(' ','_'),safe='_')},
                   {'label':'Natural Earth · mapping','url':'https://www.naturalearthdata.com/'},
                   {'label':'CountryInfo · reference snapshot','url':'https://github.com/porimol/countryinfo'}]
  if d.get('alpha2') and len(d['alpha2'])==2:
   d['references'].append({'label':'World Bank · population','url':f"https://data.worldbank.org/indicator/SP.POP.TOTL?locations={d['alpha2']}"})
  if code in rest:d['references'].append({'label':'REST Countries · current metadata','url':'https://restcountries.com/'})
  for x in desc.get('extra_sources',[]):
   if x.get('label') and x.get('url','').startswith('https://'):d['references'].append(x)
  d['wiki_checked']=article in wiki_titles
  countries[code]=d
 return {'project':'ATLAS / GLOBAL DOSSIER','edition':'REFERENCE BUILD' if not online else ('SYNCED' if not warnings else 'PARTIAL SYNC'),
         'built_at':timestamp or datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
         'feature_count':len(base),'profile_count':len(notes),'countries':countries,
         'sources':COMMON_SOURCES,'warnings':warnings,
         'methodology':'Manually reviewed thematic briefs are combined with structured, dated external facts. Live API data enriches but never silently replaces editorial history or political claims. Map uses generalized Natural Earth boundaries.'}

def refresh(fetcher=get_json):
 errors=[];rest={};population={};confirmed=set();success=0
 try:
  raw=fetcher('https://restcountries.com/v3.1/all?fields=name,cca2,cca3,capital,region,subregion,area,languages,currencies')
  rest=clean_restcountries(raw)
  if len(rest)<100:raise ValueError('REST Countries response unexpectedly short')
  success+=1
 except (URLError,HTTPError,TimeoutError,ValueError,TypeError,KeyError,OSError) as e:errors.append('REST Countries: '+type(e).__name__)
 # Group queries avoid overly long URLs and allow independent partial successes.
 base=load_json(SEED)
 valid=[c for c in base if len(c)==3 and c.isalpha() and not c.startswith('X')]
 for start in range(0,len(valid),30):
  batch=valid[start:start+30]
  url=f"https://api.worldbank.org/v2/country/{';'.join(batch)}/indicator/SP.POP.TOTL?format=json&mrv=1&per_page=120"
  try:
   values=parse_worldbank(fetcher(url));population.update(values)
  except (URLError,HTTPError,TimeoutError,ValueError,TypeError,KeyError,OSError) as e:
   errors.append('World Bank batch: '+type(e).__name__)
 if len(population)>20:success+=1
 notes=load_json(NOTES)
 titles=[(entry.get('wiki_page') or base[k]['name']) for k,entry in notes.items()]
 params=urlencode({'action':'query','format':'json','prop':'extracts','exintro':'1','explaintext':'1','exchars':'260','titles':'|'.join(titles),'formatversion':'2','redirects':'1'})
 try:
  confirmed=wikipedia_confirmed(fetcher('https://en.wikipedia.org/w/api.php?'+params))
  if confirmed: success+=1
 except (URLError,HTTPError,TimeoutError,ValueError,TypeError,KeyError,OSError) as e:errors.append('Wikipedia: '+type(e).__name__)
 return rest,population,confirmed,errors,success

def main():
 p=argparse.ArgumentParser();p.add_argument('--offline',action='store_true',help='Rebuild only from committed reference data')
 args=p.parse_args();base=load_json(SEED);notes=load_json(NOTES)
 if args.offline:
  data=make_dataset(base,notes,online=False)
 else:
  rest,pop,wiki,errors,n_ok=refresh()
  # Avoid republishing an apparently fresher snapshot when every network source is unavailable.
  if n_ok==0 and OUTPUT.exists():
   print('Remote APIs unavailable; keeping last-known-good countries.json. Problems:', '; '.join(errors));return
  data=make_dataset(base,notes,rest=rest,populations=pop,wiki_titles=wiki,online=True,warnings=errors)
  # Persist last known dated population on partial source outages, never make up freshness.
  if OUTPUT.exists():
   previous=load_json(OUTPUT).get('countries',{})
   for code,d in data['countries'].items():
    old=previous.get(code,{})
    if old.get('population_year') and old['population_year']>(d.get('population_year') or 0):
     for k in ('population','population_year','population_source'):d[k]=old.get(k)
 out=OUTPUT;out.parent.mkdir(parents=True,exist_ok=True)
 tmp=out.with_suffix('.tmp');tmp.write_text(json.dumps(data,ensure_ascii=False,separators=(',',':'))+'\n',encoding='utf-8');tmp.replace(out)
 print('Built',out,'profiles',len(data['countries']),'edition',data['edition'],'warnings',len(data['warnings']))

if __name__=='__main__':main()
