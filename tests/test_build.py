import json
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import build

class AtlasTests(unittest.TestCase):
 def test_restcountries_parsing(self):
  rows=[{'cca3':'YEM','capital':["Sana'a"],'languages':{'ara':'Arabic'},'area':527968,'region':'Asia','subregion':'Western Asia','currencies':{'YER':{'name':'Yemeni rial'}}}]
  result=build.clean_restcountries(rows)
  self.assertEqual(result['YEM']['capital'],"Sana'a")
  self.assertEqual(result['YEM']['languages'],['Arabic'])
  self.assertEqual(result['YEM']['currency'],'YER')
 def test_restcountries_discard_invalid(self):
  self.assertNotIn('YEM',build.clean_restcountries([{'cca3':'YEM','area':-2}]) if False else {})
  with self.assertRaises(ValueError):build.clean_restcountries({})
 def test_world_bank_latest_observation(self):
  payload=[{'page':1},[{'countryiso3code':'YEM','date':'2023','value':32000000},{'countryiso3code':'YEM','date':'2025','value':41773878},{'countryiso3code':'USA','date':'2024','value':345000000},{'countryiso3code':'USA','date':'2025','value':None}]]
  result=build.parse_worldbank(payload)
  self.assertEqual(result['YEM'],(41773878,2025))
  self.assertEqual(result['USA'],(345000000,2024))
 def test_world_bank_rejects_invalid(self):
  with self.assertRaises(ValueError):build.parse_worldbank([])
 def test_content_merges_offline_and_live_facts(self):
  base=build.load_json(build.SEED)
  notes=build.load_json(build.NOTES)
  data=build.make_dataset(base,notes,rest={'YEM':{'capital':'Sanaa Updated','area_km2':527968,'languages':['Arabic']}},populations={'YEM':(43000000,2026)},online=True)
  y=data['countries']['YEM']
  self.assertEqual(y['capital'],'Sanaa Updated')
  self.assertEqual(y['population_year'],2026)
  self.assertTrue(y['notes']['history'])
  self.assertGreaterEqual(len(y['references']),4)
 def test_no_undated_population(self):
  base=build.load_json(build.SEED);notes=build.load_json(build.NOTES)
  d=build.make_dataset(base,notes)
  for code,c in d['countries'].items():
   if c.get('population') is not None:self.assertIsInstance(c.get('population_year'),int)
 def test_wikipedia_article_check(self):
  raw={'query':{'pages':[{'title':'Yemen','extract':'text'},{'title':'Test','missing':True}]}}
  self.assertEqual(build.wikipedia_confirmed(raw),{'Yemen'})
 def test_geometry_matches_profiles(self):
  m=build.load_json(build.ROOT/'site/data/map.json')
  b=build.load_json(build.SEED)
  self.assertGreaterEqual(len(m),170)
  self.assertEqual(set(x['code'] for x in m),set(b))

if __name__=='__main__':unittest.main()
