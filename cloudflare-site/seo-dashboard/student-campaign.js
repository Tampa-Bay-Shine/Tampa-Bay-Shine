(() => {
'use strict';
const pages = [{"path": "/student-housing-cleaning-tampa/", "label": "Student Housing Hub", "group": "Hub", "code": ""}, {"path": "/usf-apartment-cleaning/", "label": "USF Apartment Cleaning", "group": "College", "code": "USF20"}, {"path": "/utampa-apartment-cleaning/", "label": "University of Tampa", "group": "College", "code": "UTAMPA20"}, {"path": "/hillsborough-college-apartment-cleaning/", "label": "Hillsborough College", "group": "College", "code": "HC20"}, {"path": "/florida-college-apartment-cleaning/", "label": "Florida College", "group": "College", "code": "FC20"}, {"path": "/keiser-university-apartment-cleaning-tampa/", "label": "Keiser University Tampa", "group": "College", "code": "KEISER20"}, {"path": "/phsc-student-apartment-cleaning/", "label": "PHSC / Wesley Chapel", "group": "College", "code": "PHSC20"}, {"path": "/rasmussen-university-apartment-cleaning/", "label": "Rasmussen University", "group": "College", "code": "RASMUSSEN20"}, {"path": "/college-apartment-move-out-cleaning/", "label": "College Move-Out Cleaning", "group": "Supporting", "code": ""}, {"path": "/college-student-cleaning-gift-cards/", "label": "Student Cleaning Gift Cards", "group": "Supporting", "code": ""}];
const launch='2026-11-04';
const pageMap = new Map(pages.map(p=>[p.path,p]));
const $ = id => document.getElementById(id);
const esc = v => String(v ?? '').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const norm = x => { try {let p=new URL(String(x||''),'https://tampabayshine.com').pathname;return p.replace(/\/+$/,'/')||'/';}catch(e){return String(x||'').split('?')[0].replace(/\/+$/,'/')||'/';} };
const num = n => Number.isFinite(Number(n)) ? Number(n) : 0;
const fmt = n => n==null?'—':Intl.NumberFormat('en-US',{maximumFractionDigits:0}).format(n);
const dateRange = (end,days) => {const d=new Date(end+'T12:00:00Z');d.setUTCDate(d.getUTCDate()-days+1);return d.toISOString().slice(0,10);};
const reading=async file=>{const r=await fetch('./data/'+file,{cache:'no-store'});if(!r.ok)throw new Error(file+' HTTP '+r.status);return r.json();};
let data=null;
let days=28;
let group='all';
const isActive=p=>group==='all'||p.group===group;
const weighted = points => {let clicks=0,impressions=0,positionSum=0;for(const item of points){const im=num(item[2]);clicks+=num(item[1]);impressions+=im;if(item[4]!=null)positionSum+=num(item[4])*im;}return {clicks,impressions,ctr:impressions?100*clicks/impressions:null,position:impressions?positionSum/impressions:null};};
const dates=p=>p?.period?.end||p?.data_through||new Date().toISOString().slice(0,10);
function perPage(record,end){if(!record)return null;const start=dateRange(end,days);return weighted((record.points||[]).filter(x=>x[0]>=start&&x[0]<=end));}
function queryMatch(q){const t=String(q||'').toLowerCase();return /\b(usf|utampa|university of tampa|south florida university|hillsborough college|florida college|keiser|phsc|pasco.hernando|rasmussen|student housing|student apartment|college apartment|dorm cleaning|semester move.out)\b/i.test(t);}
function render(){
 if(!data)return;
 const pIndex=new Map((data.history.pages||[]).map(r=>[norm(r.page),r]));
 const ix=new Map((data.indexing.student_pages||[]).map(r=>[norm(r.path||r.url),r]));
 const ga=new Map((data.ga.landing_pages||[]).map(r=>[norm(r.landing_page),r]));
 const end=dates(data.history), rows=pages.filter(isActive).map(p=>({p,metrics:perPage(pIndex.get(p.path),end),index:ix.get(p.path),analytics:ga.get(p.path)}));
 const observed=rows.filter(r=>r.metrics!==null);
 const total=weighted(observed.flatMap(r=>(pIndex.get(r.p.path)?.points||[]).filter(x=>x[0]>=dateRange(end,days)&&x[0]<=end)));
 const indexed=rows.filter(x=>x.index?.verdict==='PASS'&&x.index?.coverage_state==='Submitted and indexed').length;
 const inspected=rows.filter(x=>!!x.index).length;
 const cards=[['GSC clicks',observed.length?fmt(total.clicks):'—'],['GSC impressions',observed.length?fmt(total.impressions):'—'],['Weighted CTR',observed.length&&total.ctr!=null?total.ctr.toFixed(2)+'%':'—'],['Indexed / inspected',inspected?indexed+' / '+inspected:'Not inspected']];
 $('sh-cards').innerHTML=cards.map(([k,v])=>`<div class="sh-card"><div class="sh-meta">${esc(k)}</div><div class="sh-metric">${esc(v)}</div></div>`).join('');
 $('sh-dates').textContent='GSC through '+esc(end)+' · '+days+'-day window · '+observed.length+'/'+rows.length+' pages have retained observations';
 const q=(data.queries.queries||[]).filter(x=>queryMatch(x.query)).map(x=>{let points=(x.points||[]).filter(p=>p[0]>=dateRange(end,days)&&p[0]<=end);return {q:x.query,m:points.length?weighted(points):null};}).filter(x=>x.m&&x.m.impressions>0).sort((a,b)=>b.m.impressions-a.m.impressions).slice(0,10);
 $('sh-queries').innerHTML=q.length?q.map(x=>`<tr><td>${esc(x.q)}</td><td>${fmt(x.m.clicks)}</td><td>${fmt(x.m.impressions)}</td><td>${x.m.position?.toFixed(1)||'—'}</td></tr>`).join(''):'<tr><td colspan="4">No matching retained search queries in this period.</td></tr>';
 $('sh-pages').innerHTML=rows.map(({p,metrics:m,index:st,analytics:a})=>{
 const status=!st?'Not inspected':st.verdict==='PASS'&&st.coverage_state==='Submitted and indexed'?'Indexed':st.coverage_state||st.verdict||'Inspected';
 const cls=status==='Indexed'?'sh-pass':'sh-notyet';
 return `<tr><td><a href="https://tampabayshine.com${esc(p.path)}" target="_blank" rel="noopener">${esc(p.label)}</a><div class="sh-meta">${esc(p.code||p.group)}</div></td><td>${m?fmt(m.clicks):'—'}</td><td>${m?fmt(m.impressions):'—'}</td><td>${m?.position!=null?m.position.toFixed(1):'—'}</td><td><span class="sh-status ${cls}">${esc(status)}</span></td><td>${a?fmt(a.sessions):'—'}</td><td>${a?fmt(a.booknow_click):'—'}</td></tr>`;
 }).join('');
 const sessions=rows.reduce((s,r)=>s+num(r.analytics?.sessions),0),starts=rows.reduce((s,r)=>s+num(r.analytics?.booknow_click),0);
 $('sh-ga4').textContent='28-day organic landing sessions: '+fmt(sessions)+' · Booking-start clicks: '+fmt(starts)+' · '+rows.filter(r=>r.analytics).length+' pages observed in GA4 landing-page data. These are intent events, not confirmed bookings.';
 $('sh-index-date').textContent=data.indexing.generated_at?'URL Inspection checked '+esc(data.indexing.generated_at.slice(0,10)):'URL Inspection has not yet refreshed with the new cohort.';
 $('sh-query-date').textContent='Query rows reflect matching site-wide Google searches, not searches attributed to these landing pages. Low-volume/anonymized queries may be absent.';
}
function init(){
 const b=$('student-campaign');if(!b)return;
 $('sh-days').addEventListener('change',e=>{days=Number(e.target.value);render();});
 $('sh-group').addEventListener('change',e=>{group=e.target.value;render();});
 const btn=document.querySelector('#executive-nav [data-tab="student-campaign"]');
 if(btn)btn.addEventListener('click',()=>{document.querySelectorAll('section.tab').forEach(x=>x.classList.toggle('active',x.id==='student-campaign'));document.querySelectorAll('#executive-nav [data-tab]').forEach(x=>x.classList.toggle('active',x===btn));});
 Promise.allSettled([reading('page-history.json'),reading('query-history.json'),reading('ga4.json'),reading('indexing-intelligence.json')]).then(results=>{
  const [h,q,g,i]=results;
  data={history:h.status==='fulfilled'?h.value:{pages:[],period:{}},queries:q.status==='fulfilled'?q.value:{queries:[]},ga:g.status==='fulfilled'?g.value:{landing_pages:[]},indexing:i.status==='fulfilled'?i.value:{student_pages:[]}};
  const failed=results.map((r,j)=>r.status==='rejected'?['GSC pages','GSC queries','GA4','Indexing'][j]:null).filter(Boolean);
  $('sh-errors').textContent=failed.length?'Unavailable sources: '+failed.join(', ')+'. Metrics from unavailable feeds are omitted.':'Data feeds connected. Values refresh with the existing daily dashboard workflow.';
  render();
 });
}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init);else init();
})();
