/* TBS decision review: no paid API dependency; reads existing local dashboard datasets. */
(()=>{'use strict';
const root=document.getElementById('tbs-decision-review');if(!root)return;
const $=id=>document.getElementById(id);
const esc=x=>String(x??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const num=x=>Number.isFinite(Number(x))?Number(x):0;
const fmt=x=>num(x).toLocaleString();
const normalize=x=>{try{const u=new URL(x,'https://tampabayshine.com');return u.origin+u.pathname.replace(/\/$/,'')+'/'}catch{return String(x||'')}};
const sourceFiles=[
'./data/site-inventory.json','./data/indexing-intelligence.json',
'./data/opportunity-intelligence.json','./data/ga4.json','./data/gsc.json'];
Promise.all(sourceFiles.map(x=>fetch(x,{cache:'no-store'}).then(r=>{if(!r.ok)throw Error(x+' HTTP '+r.status);return r.json()}))).then(([inventory,indexing,opp,ga4,gsc])=>{
 const sitemap=(inventory.urls||[]);const checked=[...(indexing.pages||[]),...(indexing.student_pages||[])];
 const byURL=new Map();checked.forEach(x=>{const key=normalize(x.url||('https://tampabayshine.com'+(x.path||'/')));byURL.set(key,x)});
 const inventoryKeys=new Set(sitemap.map(normalize));let reviewed=0,positive=0,exceptions=[];
 sitemap.forEach(u=>{const k=normalize(u),x=byURL.get(k);if(!x)return;reviewed++;
 const ok=x.verdict==='PASS'&&/submitted and indexed/i.test(x.coverage_state||'')&&(!x.google_canonical||normalize(x.google_canonical)===k);
 if(ok)positive++;else exceptions.push({url:u,reason:x.coverage_state||x.verdict||'Inspection requires review'});
 });
 const uninspected=Math.max(0,sitemap.length-reviewed);
 const dataAge=inventory.generated_at||'Unknown';
 $('tbs-dr-indexing').innerHTML=`<div class="tbs-dr-metrics"><div><strong>${fmt(sitemap.length)}</strong><span>Canonical sitemap URLs</span></div><div><strong>${fmt(reviewed)}</strong><span>URLs inspected in dashboard dataset</span></div><div><strong>${fmt(positive)}</strong><span>Inspected and indexed</span></div><div><strong>${fmt(uninspected)}</strong><span>Not yet inspected here</span></div></div><p class="tbs-dr-note">These are tracked inspection results, <b>not</b> a Google site-wide indexing count. Snapshot: ${esc(dataAge)}. The site inventory is refreshed when the manifest generator runs; inspect its date before using it.</p>${exceptions.length?`<h4>Inspected pages needing attention</h4><ul>${exceptions.slice(0,8).map(x=>`<li><a href="${esc(x.url)}" target="_blank" rel="noopener noreferrer">${esc(new URL(x.url).pathname)}</a>: ${esc(x.reason)}</li>`).join('')}</ul>`:''}`;
 // Do not turn duplicate queries into multiple site edits. Only actionable, active-business, high-confidence observations.
 const actions=(opp.actions||[]).filter(x=>x.priority==='high'&&x.confidence==='high'&&x.decision_status==='actionable'&&x.business_priority?.status!=='deprioritized');
 const used=new Set();const focused=[];
 actions.sort((a,b)=>num(b.evidence?.impressions)-num(a.evidence?.impressions));
 for(const item of actions){const topic=(item.page?new URL(item.page,'https://tampabayshine.com').pathname:item.type||'search')+'|'+(item.query||item.subject||'').toLowerCase().replace(/\b(services?|tampa|fl|florida|near me|company|companies)\b/g,'').replace(/[^a-z]+/g,' ').trim();if(used.has(topic))continue;used.add(topic);focused.push(item);if(focused.length===5)break}
 $('tbs-dr-actions').innerHTML=`<p class="tbs-dr-note">${fmt(actions.length)} high-confidence actionable findings in the source data; showing up to 5 by 28-day search impressions. Validate intent and competing URLs before editing a page.</p>${focused.length?`<ol class="tbs-dr-list">${focused.map(x=>`<li><strong>${esc(x.subject||x.query||x.page||x.type||'SEO opportunity')}</strong><p>${fmt(x.evidence?.impressions)} impressions; ${fmt(x.evidence?.clicks)} clicks; avg position ${esc(x.evidence?.position??'—')}. ${esc(x.why_flagged||'')}</p><small>${esc(x.recommended_action||'Review ranking URL and search intent.')}</small></li>`).join('')}</ol>`:'<p>No sufficiently supported high-confidence actions right now.</p>'}`;
 const p=ga4.periods?.['28']||{};const ov=p.overview?.current||{},intent=p.intent?.current||{},confirmed=p.confirmed_bookings?.current||{};
 const q=ga4.attribution_quality||{};
 $('tbs-dr-conversions').innerHTML=`<div class="tbs-dr-metrics"><div><strong>${fmt(ov.sessions)}</strong><span>Organic Search sessions</span></div><div><strong>${fmt(intent.booknow_click)}</strong><span>Organic booking starts</span></div><div><strong>${fmt(confirmed.confirmed_bookings)}</strong><span>Organic completed bookings attributed</span></div><div><strong>${fmt(q.confirmed_bookings_all_channels)}</strong><span>Completed bookings: all channels</span></div></div><p class="tbs-dr-note"><b>Attribution status:</b> ${esc(q.status||'Unverified')}. ${q.exact_booking_origin_available===true?'Exact source joins reported available; validate test booking.':'Exact join between a Google search click, booking start, and BookingKoala completion is <b>not verified</b>.'} Do not claim Direct completions were organic.</p><p class="tbs-dr-note">GA4 period generated ${esc(ga4.generated_at||'unknown')}; GSC period ${esc(gsc.period?.start||'?')} to ${esc(gsc.period?.end||'?')}.</p>`;
 $('tbs-dr-status').textContent='Loaded from the existing dashboard datasets — no GSC Wizard subscription required.';
}).catch(err=>{$('tbs-dr-status').textContent='Decision review could not load dashboard data: '+err.message;});
})();
