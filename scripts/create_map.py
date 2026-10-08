#!/usr/bin/env python3
"""Developer-only offline tool to derive compact SVG boundaries from Natural Earth 1:110m.
Requires geopandas and shapely; prebuilt result is already committed for users.
Natural Earth public-domain dataset is bundled with pyogrio's test fixtures in this build environment.
"""
import json
from pathlib import Path
import geopandas as gpd
from shapely.geometry import Polygon, MultiPolygon

ROOT=Path(__file__).resolve().parents[1]
SRC='/opt/pyvenv/lib/python3.13/site-packages/pyogrio/tests/fixtures/naturalearth_lowres/naturalearth_lowres.shp'
MAP_FIXES={'Norway':'NOR','France':'FRA','N. Cyprus':'XNC','Somaliland':'XSO','Kosovo':'XKX'}
NAME_FIXES={'United States of America':'United States','Dem. Rep. Congo':'DR Congo','Central African Rep.':'Central African Republic','S. Sudan':'South Sudan','W. Sahara':'Western Sahara','Eq. Guinea':'Equatorial Guinea','Dominican Rep.':'Dominican Republic','Bosnia and Herz.':'Bosnia and Herzegovina','Czechia':'Czech Republic','eSwatini':'Eswatini','N. Cyprus':'Northern Cyprus (disputed)','Somaliland':'Somaliland (disputed)','Kosovo':'Kosovo (disputed)','Falkland Is.':'Falkland Islands / Islas Malvinas'}
W=1440; SCALE=4.0; TOP=85

def XY(p):
 return round((p[0]+180)*SCALE,1), round((TOP-p[1])*SCALE,1)

def geo_path(shape):
 if shape is None:return ''
 parts = list(shape.geoms) if isinstance(shape,MultiPolygon) else [shape]
 seq=[]
 for piece in parts:
  if not isinstance(piece, Polygon):continue
  simple=piece.simplify(.18,preserve_topology=True)
  for line in [simple.exterior,*simple.interiors]:
   coords=[XY(p) for p in line.coords]
   if len(coords)<4:continue
   text='M'+'L'.join(f'{x:g},{y:g}' for x,y in coords)+'Z'
   seq.append(text)
 return ''.join(seq)

def main():
 df=gpd.read_file(SRC)
 data=[]
 for _,r in df.iterrows():
  geo=r['geometry']; rp=geo.representative_point(); x,y=XY((rp.x,rp.y))
  country={'code':MAP_FIXES.get(r['name'],r['iso_a3']), 'name':NAME_FIXES.get(r['name'],r['name']), 'continent':r['continent'], 'center':[x,y], 'path':geo_path(geo)}
  data.append(country)
 data.sort(key=lambda p:p['name'].lower())
 path=ROOT/'site/data/map.json'; path.write_text(json.dumps(data,ensure_ascii=False,separators=(',',':')),encoding='utf8')
 print('Map features:',len(data),'Size:',path.stat().st_size,'bytes')

if __name__=='__main__':main()
