/* Tampa Bay Shine independent SEO decision review v2. No paid GSC Wizard calls. */
(()=>{'use strict';
const root=document.getElementById('tbs-decision-review');if(!root)return;
const $=id=>document.getElementById(id);
const esc=x=>String(x??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const num=x=>Number.isFinite(Number(x))?Number(x):0;
const fmt=x=>num(x).toLocaleString('en-US');
const normalize=x=>{try{const u=new URL(x,'https://tampabayshine.com');return u.origin+u.pathname.replace(/\/$/,'')+'/'}catch{return String(x||'')}};
const readable=x=>{if(!x)return 'unknown';const d=new Date(x);return Number.isFinite(d.getTime())?d.toLocaleString('en-US',{timeZone:'America/New_York',month:'short',day:'numeric',year:'numeric'}):String(x)};
const sourceFiles=['./data/site-inventory.json','./data/indexing-intelligence.json','./data/opportunity-intelligence.json','./data/ga4.json','./data/gsc.json'];
Promise.all(sourceFiles.map(x=>fetch(x,{cache:'no-store'}).then(r=>{if(!r.ok)throw Error(x+' HTTP '+r.status);return r.json()}))).then(([inventory,indexing,opp,ga4,gsc])=>{
 const sitemap=inventory.urls||[];const checked=[...(indexing.pages||[]),...(indexing.student_pages||[])];
 const byURL=new Map();checked.forEach(x=>byURL.set(normalize(x.url||('https://tampabayshine.com'+(x.path||'/'))),x));
 let reviewed=0,positive=0;const exceptions=[];
 sitemap.forEach(u=>{const key=normalize(u),x=byURL.get(key);if(!x)return;reviewed++;
 const ok=x.verdict==='PASS'&&/submitted and indexed/i.test(x.coverage_state||'')&&(!x.google_canonical||normalize(x.google_canonical)===key);
 if(ok)positive++;else exceptions.push({url:u,reason:x.coverage_state||x.verdict||'Inspection requires review'});
 });
 const uninspected=Math.max(0,sitemap.length-reviewed);
 $('tbs-dr-indexing').innerHTML=`<div class="tbs-dr-metrics"><div><strong>${fmt(sitemap.length)}</strong><span>Submitted sitemap URLs</span></div><div><strong>${fmt(reviewed)}</strong><span>Inspected in this dashboard</span></div><div><strong>${fmt(positive)}</strong><span>Inspected and indexed</span></div><div><strong>${fmt(uninspected)}</strong><span>Without an inspection result</span></div></div><p class="tbs-dr-note">Inventory last refreshed ${esc(readable(inventory.generated_at))} from the production sitemap. An uninspected URL is <b>not</b> necessarily unindexed.</p>${exceptions.length?`<details><summary>${exceptions.length} inspected URL(s) need attention</summary><ul>${exceptions.slice(0,12).map(x=>`<li><a href="${esc(x.url)}" target="_blank" rel="noopener noreferrer">${esc(new URL(x.url).pathname)}</a>: ${esc(x.reason)}</li>`).join('')}</ul></details>`:''}`;
 const p=ga4.periods?.['28']||{};const ov=p.overview?.current||{},intent=p.intent?.current||{},confirmed=p.confirmed_bookings?.current||{};
 const q=ga4.attribution_quality||{};const organic=num(confirmed.confirmed_bookings);
 $('tbs-dr-conversions').innerHTML=`<div class="tbs-dr-metrics"><div><strong>${fmt(ov.sessions)}</strong><span>Organic search sessions</span></div><div><strong>${fmt(intent.booknow_click)}</strong><span>Organic booking starts</span></div><div><strong>${fmt(organic)}</strong><span>Bookings GA4 attributes to organic</span></div><div><strong>${fmt(q.confirmed_bookings_all_channels)}</strong><span>Confirmed bookings — all channels</span></div></div><p class="tbs-dr-note tbs-dr-warning"><b>Attribution not fully verified.</b> GA4 reports the channel of each booking completion, but we have not proven it is the same person who originally clicked from Google. Do not count Direct bookings as SEO conversions.</p><p class="tbs-dr-note">GA4 refreshed ${esc(readable(ga4.generated_at))}; Search Console covers ${esc(gsc.period?.start||'?')} through ${esc(gsc.period?.end||'?')}.</p>`;
 // Five focused actions: suppress tiny samples, repeated query variants and unattributed claims.
 const valid=(opp.actions||[]).filter(x=>x.priority==='high'&&x.confidence==='high'&&x.decision_status==='actionable'&&x.business_priority?.status!=='deprioritized'&&num(x.evidence?.impressions)>=40&&num(x.evidence?.position)>=4&&num(x.evidence?.position)<=25);
 const used=new Set(),focused=[];
 const canonicalTopic=x=>{const q=String(x.query||x.subject||'').toLowerCase();const stripped=q.replace(/\b(tampa|fl|florida|near me|in|best|services?|company|companies|professional|local)\b/g,' ').replace(/[^a-z0-9]+/g,' ').trim();return stripped.replace(/\b(cleaning|cleaners)\b/g,'clean').replace(/\s+/g,' ').trim()||q};
 valid.sort((a,b)=>{const priority=x=>num(x.evidence?.impressions)*(1+Math.min(1,num(x.evidence?.clicks)/5))*(num(x.evidence?.position)<=15?1.2:1);return priority(b)-priority(a)});
 for(const item of valid){const topic=canonicalTopic(item);if(used.has(topic))continue;used.add(topic);focused.push(item);if(focused.length===5)break}
 $('tbs-dr-actions').innerHTML=`<p class="tbs-dr-note">${fmt(valid.length)} observations meet the review threshold (40+ impressions, positions 4–25, high confidence); showing up to five distinct query themes. These are <b>candidates</b>, not promises of more traffic.</p>${focused.length?`<ol class="tbs-dr-action-list">${focused.map((x,i)=>`<li><div class="tbs-dr-rank">Review ${i+1} · ${fmt(x.evidence?.impressions)} impressions · position ${esc(x.evidence?.position??'—')}</div><strong>${esc(x.subject||x.query||x.page||'SEO opportunity')}</strong><p>${fmt(x.evidence?.clicks)} clicks in the current 28-day period. ${esc(x.why_flagged||'Search visibility merits investigation.')}</p><details><summary>Recommended check and measurement</summary><p>${esc(x.recommended_action||'Confirm the ranking URL and intent before editing.')}</p><p>${esc(x.measurement?.['30_days']||'Compare subsequent performance after changes.')}</p></details></li>`).join('')}</ol>`:'<p class="tbs-dr-note">No actions meet the current evidence threshold. Use the full Opportunity Intelligence view for research.</p>'}`;
 $('tbs-dr-status').textContent='GSC, GA4, and existing inspection data — independent of GSC Wizard.';
}).catch(err=>{$('tbs-dr-status').textContent='Decision review could not load: '+err.message;});
})();
