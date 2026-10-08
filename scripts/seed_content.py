"""Developer-only seed builder. Generated sources/base_countries.json is checked in."""
import json
from pathlib import Path
from countryinfo import CountryInfo
import pycountry
ROOT=Path(__file__).resolve().parents[1]
maps=json.loads((ROOT/'site/data/map.json').read_text())
ALIASES={'United States':'United States','DR Congo':'Democratic Republic of the Congo','Czech Republic':'Czech Republic','North Korea':'North Korea','South Korea':'South Korea','Ivory Coast':'Ivory Coast','S. Sudan':'South Sudan','Falkland Islands / Islas Malvinas':'Falkland Islands','Western Sahara':'Western Sahara','Central African Republic':'Central African Republic','Republic of the Congo':'Republic of the Congo','United Republic of Tanzania':'Tanzania','Taiwan':'Taiwan','Northern Cyprus (disputed)':'Northern Cyprus','Somaliland (disputed)':'Somaliland','Kosovo (disputed)':'Kosovo'}
OVERRIDE_ALPHA={'XNC':'','XSO':'','XKX':'XK'}
FALLBACK_REGION={'North America':'Americas','South America':'Americas','Europe':'Europe','Asia':'Asia','Africa':'Africa','Oceania':'Oceania','Antarctica':'Antarctica'}
source={}
for m in maps:
 code=m['code']; name=m['name']; info={}
 for query in [ALIASES.get(name,name), name]:
  try:
   info=CountryInfo(query).info()
   if info:break
  except (KeyError,ValueError,TypeError):continue
 country=pycountry.countries.get(alpha_3=code) if len(code)==3 else None
 cc=info.get('ISO',{}).get('alpha2') if info else None
 if not cc and country:cc=country.alpha_2
 if not cc: cc=OVERRIDE_ALPHA.get(code,'')
 capital=info.get('capital') or None
 if isinstance(capital, list): capital=', '.join(capital)
 langs=info.get('languages') or []
 friendly=[]
 for lang in langs[:5]:
  lang_ref=pycountry.languages.get(alpha_2=lang) or pycountry.languages.get(alpha_3=lang)
  friendly.append(lang_ref.name if lang_ref else lang.upper())
 # Legacy CountryInfo values are undated; they serve only as offline reference,
 # never as a claim of up-to-date population or political authority.
 area=info.get('area') or None
 source[code]={'code':code,'name':name,'region':m['continent'],'subregion':info.get('subregion') or '', 'capital':capital, 'languages':friendly, 'currency':', '.join(info.get('currencies') or []), 'area_km2':area, 'alpha2':cc, 'population':None, 'population_year':None, 'metadata_source':'countryinfo','featured':False}
for code in ['YEM','USA','CHN','RUS','BRA','IND','JPN','FRA','DEU','GBR','CAN','MEX','EGY','SAU','KEN','AUS','ZAF','IDN','TUR','UKR']:
 source[code]['featured']=True
# Explicit World Bank Yemen 2025 reference from the user's existing vetted project.
source['YEM']['population']=41773878
source['YEM']['population_year']=2025
source['YEM']['population_source']='worldbank'
(Root:=ROOT/'sources/base_countries.json').write_text(json.dumps(source,ensure_ascii=False,indent=2)+'\n')
print(len(source),'countries seeded',sum(bool(x['capital']) for x in source.values()),'with capitals',sum(bool(x['area_km2']) for x in source.values()),'with areas')
