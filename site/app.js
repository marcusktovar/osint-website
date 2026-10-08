'use strict';

// All text and map paths are drawn from bundled, first-party JSON. Public source
// text is inserted with textContent, never with untrusted innerHTML.
const NS = 'http://www.w3.org/2000/svg';
const BOX = { width: 1440, height: 680 };
const QUICK_CODES = ['YEM', 'USA', 'CHN', 'RUS', 'BRA', 'JPN', 'IND', 'FRA'];
const TAB_LABELS = {overview:'COUNTRY OVERVIEW', history:'HISTORICAL BACKGROUND', geography:'TERRAIN & GEOGRAPHY', culture:'PEOPLE & CULTURE'};
const $ = id => document.getElementById(id);
const state = {countries: {}, geometry: [], geometryByCode: new Map(), selected: 'YEM', activeTab: 'overview', filter:'all', search:'', view:{x:0,y:0,w:BOX.width,h:BOX.height}, pointer:null, dragging:false};

function svgEl(tag, attrs={}) {
 const node = document.createElementNS(NS,tag);
 for (const [key,value] of Object.entries(attrs)) node.setAttribute(key,String(value));
 return node;
}
function displayFlag(alpha2) {
 if (!/^[A-Z]{2}$/.test(alpha2 || '')) return '◈';
 return [...alpha2].map(char => String.fromCodePoint(char.charCodeAt(0) - 65 + 0x1F1E6)).join('');
}
function displayNum(number) {
 return typeof number==='number' && Number.isFinite(number) ? new Intl.NumberFormat('en-US',{maximumFractionDigits:0}).format(number) : '—';
}
function setText(id,text) {$(id).textContent = text ?? '—';}
function setClock() {const now = new Date();$('utc-clock').textContent = now.toLocaleTimeString('en-GB',{timeZone:'UTC',hour12:false});}
function countryName(code){return state.countries[code]?.name || state.geometryByCode.get(code)?.name || code;}
function showToast(message){const el=$('toast');el.textContent=message;el.hidden=false;window.clearTimeout(showToast.timeout);showToast.timeout=window.setTimeout(()=>el.hidden=true,2600);}

function setupGrid(){
 const layer=$('grid-lines');
 for(let lon=-150;lon<=150;lon+=30){const x=(lon+180)*4;layer.append(svgEl('line',{x1:x,y1:0,x2:x,y2:680,class:'grid-line'}));
  if(lon%60===0){const label=svgEl('text',{x:x+5,y:658,class:'grid-label'});label.textContent=`${Math.abs(lon)}°${lon>=0?'E':'W'}`;layer.append(label);}}
 for(let lat=-60;lat<=75;lat+=15){const y=(85-lat)*4;layer.append(svgEl('line',{x1:0,y1:y,x2:1440,y2:y,class:lat===0?'grid-line grid-equator':'grid-line'}));
  if(lat%30===0){const label=svgEl('text',{x:9,y:y-6,class:'grid-label'});label.textContent=`${Math.abs(lat)}°${lat>=0?'N':'S'}`;layer.append(label);}}
}
function renderMap() {
 setupGrid();const layer=$('countries-layer');const fragment=document.createDocumentFragment();
 for(const feature of state.geometry){
  const path=svgEl('path',{d:feature.path,'data-code':feature.code,class:'nation',role:'button',tabindex:'0','aria-label':`Select ${feature.name}`});
  const title=svgEl('title');title.textContent=feature.name;path.append(title);fragment.append(path);
 }
 layer.append(fragment);
 $('map-dataset').textContent=`${state.geometry.length} FEATURES LOADED`;
 markCountry();updateView();
}
function markCountry(){
 for(const el of $('countries-layer').querySelectorAll('.nation.selected')) el.classList.remove('selected');
 for(const el of $('countries-layer').querySelectorAll('.nation')){if(el.dataset.code===state.selected)el.classList.add('selected');}
 const feature=state.geometryByCode.get(state.selected);const labelLayer=$('labels-layer');labelLayer.replaceChildren();
 if(feature){const [x,y]=feature.center;
  labelLayer.append(svgEl('circle',{cx:x,cy:y,r:10,class:'map-marker-outer'}));
  labelLayer.append(svgEl('circle',{cx:x,cy:y,r:3,class:'map-marker-center'}));
  const label=svgEl('text',{x:x+14,y:y-13,class:'map-country-label'});label.textContent=feature.code;labelLayer.append(label);
 }
 setText('focus-name',countryName(state.selected).toUpperCase());
}
function clampView(v){
 v.w=Math.max(120,Math.min(BOX.width,v.w));v.h=v.w*BOX.height/BOX.width;
 v.x=Math.max(0,Math.min(BOX.width-v.w,v.x));v.y=Math.max(0,Math.min(BOX.height-v.h,v.y));return v;
}
function updateView(){
 clampView(state.view);
 const {x,y,w,h}=state.view;$('world-map').setAttribute('viewBox',`${x.toFixed(2)} ${y.toFixed(2)} ${w.toFixed(2)} ${h.toFixed(2)}`);
 setText('zoom-value',`${Math.round(BOX.width/w*100)}%`);
 setText('map-mode',w>=1439?'GLOBAL VIEW':'REGIONAL VIEW');
}
function zoom(factor,clientX=null,clientY=null){
 const v=state.view;const svg=$('world-map');const rect=svg.getBoundingClientRect();
 const rx=clientX==null?.5:Math.max(0,Math.min(1,(clientX-rect.left)/rect.width));
 const ry=clientY==null?.5:Math.max(0,Math.min(1,(clientY-rect.top)/rect.height));
 const beforeX=v.x+v.w*rx,beforeY=v.y+v.h*ry;
 const nextW=Math.max(120,Math.min(BOX.width,v.w*factor));const nextH=nextW*BOX.height/BOX.width;
 v.x=beforeX-nextW*rx;v.y=beforeY-nextH*ry;v.w=nextW;v.h=nextH;updateView();
}
function focusCountry(code){
 const feature=state.geometryByCode.get(code);if(!feature)return;
 const [cx,cy]=feature.center;const v=state.view;
 const zoomWidth=Math.min(v.w,900);const zoomHeight=zoomWidth*BOX.height/BOX.width;
 v.w=zoomWidth;v.h=zoomHeight;v.x=cx-zoomWidth/2;v.y=cy-zoomHeight/2;updateView();
}
function resetView(){state.view={x:0,y:0,w:BOX.width,h:BOX.height};updateView();}
function formatCoord(number,positive,negative){return `${Math.abs(number).toFixed(1)}° ${number>=0?positive:negative}`;}
function setupMapEvents(){
 const svg=$('world-map');
 svg.addEventListener('click',event=>{
  if(state.dragging){state.dragging=false;return;}
  const target=event.target.closest('[data-code]');if(target?.dataset.code)selectCountry(target.dataset.code,{focus:true});
 });
 svg.addEventListener('keydown',event=>{
  if((event.key==='Enter'||event.key===' ') && event.target.dataset?.code){event.preventDefault();selectCountry(event.target.dataset.code,{focus:true});}
 });
 svg.addEventListener('wheel',event=>{event.preventDefault();zoom(event.deltaY>0?1.17:.84,event.clientX,event.clientY);},{passive:false});
 svg.addEventListener('pointerdown',event=>{if(event.button!==0)return;state.pointer={x:event.clientX,y:event.clientY,view:{...state.view},moved:false};state.dragging=false;svg.setPointerCapture(event.pointerId);svg.classList.add('grabbing');});
 svg.addEventListener('pointermove',event=>{
  const bounds=svg.getBoundingClientRect();const v=state.view;
  const px=((event.clientX-bounds.left)/bounds.width*v.w)+v.x;
  const py=((event.clientY-bounds.top)/bounds.height*v.h)+v.y;
  const lon=px/4-180,lat=85-py/4;
  if(lon>=-180&&lon<=180&&lat>=-85&&lat<=85)setText('coordinates',`${formatCoord(lon,'E','W')} / ${formatCoord(lat,'N','S')}`);
  if(!state.pointer)return;
  const dx=event.clientX-state.pointer.x,dy=event.clientY-state.pointer.y;
  if(Math.hypot(dx,dy)>4)state.pointer.moved=true;
  if(state.pointer.moved){state.view.x=state.pointer.view.x-dx*state.pointer.view.w/bounds.width;state.view.y=state.pointer.view.y-dy*state.pointer.view.h/bounds.height;updateView();}
 });
 const finish=()=>{if(state.pointer){state.dragging=state.pointer.moved;state.pointer=null;svg.classList.remove('grabbing');}};
 svg.addEventListener('pointerup',finish);svg.addEventListener('pointercancel',finish);
 $('zoom-in').addEventListener('click',()=>zoom(.78));$('zoom-out').addEventListener('click',()=>zoom(1.28));$('zoom-reset').addEventListener('click',resetView);
}
function makeCountryRow(country){
 const btn=document.createElement('button');btn.type='button';btn.className='country-row';btn.setAttribute('role','option');
 btn.setAttribute('aria-selected',String(country.code===state.selected));if(country.code===state.selected)btn.classList.add('active');
 const name=document.createElement('span');name.className='row-name';
 const flag=document.createElement('span');flag.className='flag';flag.textContent=displayFlag(country.alpha2);
 const label=document.createElement('span');label.className='row-title';label.textContent=country.name;
 name.append(flag,label);const code=document.createElement('span');code.className='row-code';code.textContent=country.featured?'◆ '+country.code:country.code;
 btn.append(name,code);btn.addEventListener('click',()=>selectCountry(country.code,{focus:true}));return btn;
}
function renderCountries(){
 const list=$('country-list');const items=Object.values(state.countries);
 const filtered=items.filter(c=>(state.filter==='all'||c.region===state.filter)&&(!state.search||`${c.name} ${c.code} ${c.alpha2||''}`.toLowerCase().includes(state.search)));
 filtered.sort((a,b)=>Number(b.featured)-Number(a.featured)||a.name.localeCompare(b.name));
 const frag=document.createDocumentFragment();for(const item of filtered)frag.append(makeCountryRow(item));
 if(!filtered.length){const p=document.createElement('p');p.className='empty-results';p.textContent='NO MATCHES / TRY A DIFFERENT COUNTRY OR REGION';frag.append(p);}
 list.replaceChildren(frag);setText('list-count',`${filtered.length} / ${items.length} RESULTS`);
}
function renderQuick(){
 const quick=$('quick-access');const frag=document.createDocumentFragment();
 for(const code of QUICK_CODES){const c=state.countries[code];if(!c)continue;const b=document.createElement('button');b.type='button';b.className='quick-button'+(code===state.selected?' active':'');b.title=`Select ${c.name}`;b.setAttribute('aria-label',`Select ${c.name}`);
  const f=document.createElement('span');f.className='flag';f.textContent=displayFlag(c.alpha2);const l=document.createElement('span');l.textContent=code;b.append(f,l);b.addEventListener('click',()=>selectCountry(code,{focus:true}));frag.append(b);}
 quick.replaceChildren(frag);
}
function fallbackNarrative(country,topic){
 const loc=country.subregion||country.region||'the world';
 if(topic==='overview')return `${country.name} is shown in the ${loc} region of this atlas. The data panels combine a generalized map with offline reference information, and—when available—dated World Bank population observations. Use the source links to research this country in greater depth.`;
 if(topic==='geography')return `Natural Earth's world map places ${country.name} within ${country.region||'its mapped region'}. ${country.capital?`The reference data lists ${country.capital} as its capital. `:''}This generalized map is not suitable for legal or very detailed border interpretation.`;
 if(topic==='history')return `A reviewed historical narrative for ${country.name} has not yet been added to this atlas. Open the linked Wikipedia article and other research sources for context. This panel avoids generating an unsupported summary.`;
 return `A curated cultural briefing for ${country.name} has not yet been added. Please use its linked sources for information about languages, traditions, literature, and local communities.`;
}
function renderPanel(){
 const c=state.countries[state.selected];if(!c)return;
 setText('country-flag',displayFlag(c.alpha2));setText('country-title',c.name.toUpperCase());setText('country-subtitle',`${(c.region||'UNKNOWN').toUpperCase()} / ${(c.subregion||'WORLD ATLAS').toUpperCase()}`);
 setText('profile-id',`REC / ${c.code}`);setText('country-code',`${c.code} / ${c.alpha2||'—'}`);
 setText('profile-edition',c.population_year?`STATISTICS · ${c.population_year}`:'REFERENCE DATA');
 setText('fact-capital',c.capital||'Unlisted');setText('fact-area',displayNum(c.area_km2));
 setText('fact-population',displayNum(c.population));
 setText('fact-pop-year',c.population_year?`WORLD BANK · ${c.population_year}`:'AWAITING DATED SYNC');
 setText('fact-language',c.languages?.length?c.languages.slice(0,2).join(' / '):'Unlisted');
 setText('fact-region',c.region||'Unlisted');setText('fact-currency',c.currency||'Unlisted');
 setText('fact-data-source',`METADATA: ${c.metadata_source==='restcountries'?'REST COUNTRIES API':'HISTORICAL COUNTRYINFO SNAPSHOT'} · POPULATION: ${c.population_year?'WORLD BANK OBSERVATION':'NOT YET VERIFIED'}`);
 renderTab();
 const links=$('source-links');const fragment=document.createDocumentFragment();
 for(const reference of c.references||[]){if(!reference.url?.startsWith('https://'))continue;
  const a=document.createElement('a');a.href=reference.url;a.target='_blank';a.rel='noopener noreferrer';a.textContent=reference.label;
  const arrow=document.createElement('span');arrow.textContent='↗';a.append(arrow);fragment.append(a);
 }
 links.replaceChildren(fragment);
}
function renderTab(){
 const c=state.countries[state.selected];if(!c)return;
 setText('report-title',`// ${TAB_LABELS[state.activeTab]}`);
 setText('report-text',c.notes?.[state.activeTab]||fallbackNarrative(c,state.activeTab));
 const caution=$('report-caution');caution.hidden=!(c.notes?.caution);caution.textContent=c.notes?.caution?`⚠ ${c.notes.caution}`:'';
 for(const tab of document.querySelectorAll('.topic-tabs button')){
  const active=tab.dataset.tab===state.activeTab;tab.classList.toggle('active',active);tab.setAttribute('aria-selected',String(active));tab.tabIndex=active?0:-1;
 }
}
function selectCountry(code,{focus=false}={}){
 if(!state.countries[code])return;
 state.selected=code;state.activeTab='overview';renderPanel();markCountry();renderCountries();renderQuick();
 if(focus)focusCountry(code);
 try{history.replaceState(null,'',`#${encodeURIComponent(code)}`);}catch(_ignored){}
}
function addControls(){
 $('search-countries').addEventListener('input',e=>{state.search=e.target.value.trim().toLowerCase();renderCountries();});
 $('region-filter').addEventListener('change',e=>{state.filter=e.target.value;renderCountries();});
 document.addEventListener('keydown',e=>{
  const tag=document.activeElement?.tagName;if(e.key==='/'&&!e.ctrlKey&&!e.altKey&&!e.metaKey&&tag!=='INPUT'&&tag!=='TEXTAREA'){e.preventDefault();$('search-countries').focus();}
  if(e.key==='Escape'&&document.activeElement===$('search-countries')){$('search-countries').value='';state.search='';renderCountries();$('search-countries').blur();}
 });
 for(const tab of $('topic-tabs').querySelectorAll('button'))tab.addEventListener('click',()=>{state.activeTab=tab.dataset.tab;renderTab();});
}
async function init(){
 setClock();setInterval(setClock,1000);addControls();setupMapEvents();
 try{
  const [dataResponse,mapResponse]=await Promise.all([fetch('./data/countries.json'),fetch('./data/map.json')]);
  if(!dataResponse.ok||!mapResponse.ok)throw Error('Site data could not be found.');
  const [data,geometry]=await Promise.all([dataResponse.json(),mapResponse.json()]);
  if(!data.countries||!Array.isArray(geometry)||geometry.length<100)throw Error('Country dataset incomplete.');
  state.countries=data.countries;state.geometry=geometry;state.geometryByCode=new Map(geometry.map(c=>[c.code,c]));
  const requested=decodeURIComponent(location.hash.replace('#','')).toUpperCase();
  state.selected=state.countries[requested]?requested:'YEM';
  setText('index-total',`${geometry.length} MAPPED`);setText('build-date',data.built_at.slice(0,10));
  setText('global-status',`${geometry.length} COUNTRIES / TERRITORIES LOADED · ${data.profile_count} EXTENDED REPORTS`);
  setText('right-source-state',data.edition||'REFERENCE BUILD');
  renderMap();renderQuick();renderCountries();renderPanel();
  // The initial view exposes the full globe; subsequent selections zoom toward the chosen area.
 }catch(error){console.error('Atlas loading error:',error);setText('global-status','ERROR: COULD NOT LOAD LOCAL ATLAS DATA');
  $('country-list').textContent='Failed to load country profiles. Serve the site over HTTP (not file://).';
  $('report-text').textContent='This atlas requires the bundled JSON files. See the README for setup instructions.';
  showToast('Data load failed. Use a local HTTP server or GitHub Pages.');}
}
window.addEventListener('hashchange',()=>{
 const code=decodeURIComponent(location.hash.replace('#','')).toUpperCase();if(state.countries[code]&&code!==state.selected)selectCountry(code,{focus:true});
});
init();
