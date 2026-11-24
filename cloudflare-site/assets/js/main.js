(()=>{const b=document.querySelector('.nav-toggle'),n=document.querySelector('.site-nav');if(b&&n)b.addEventListener('click',()=>{const o=n.classList.toggle('is-open');b.setAttribute('aria-expanded',o?'true':'false')})})();
(()=>{const f=document.getElementById('sms-opt-in-form');if(!f)return;
const care=document.getElementById('customer-care-consent'),marketing=document.getElementById('marketing-consent'),none=document.getElementById('no-text-consent');
const gCare=document.getElementById('google-customer-care'),gMarketing=document.getElementById('google-marketing'),gNone=document.getElementById('google-no-text'),gUrl=document.getElementById('google-page-url');
const started=document.getElementById('submission-started'),msg=document.getElementById('submission-message'),btn=document.getElementById('submit-button'),frame=document.getElementById('google-form-response');
const show=(done)=>{if(!msg)return;msg.style.display='block';msg.innerHTML=done?'<h2>Thank You!</h2><p><strong>Your text messaging preferences have been submitted successfully.</strong></p><p>You do not need to submit this form again.</p>':'<h2>Thank You!</h2><p><strong>Your text messaging preferences are being submitted.</strong></p><p>Please do not submit this form again.</p>';};
if(care)care.addEventListener('change',()=>{if(care.checked&&none)none.checked=false});
if(marketing)marketing.addEventListener('change',()=>{if(marketing.checked&&none)none.checked=false});
if(none)none.addEventListener('change',()=>{if(none.checked){if(care)care.checked=false;if(marketing)marketing.checked=false}});
f.addEventListener('submit',()=>{if(gCare)gCare.value=care&&care.checked?'Yes':'No';if(gMarketing)gMarketing.value=marketing&&marketing.checked?'Yes':'No';if(gNone)gNone.value=none&&none.checked?'Yes':'No';if(gUrl)gUrl.value=window.location.href;if(started)started.value='yes';show(false);if(btn){btn.disabled=true;btn.textContent='Submitted - Thank You'}if(msg)msg.scrollIntoView({behavior:'smooth',block:'center'});});
if(frame)frame.addEventListener('load',()=>{if(started&&started.value==='yes')show(true)});
})();

(()=>{const classify=(a)=>{const h=a.getAttribute('href')||'',p=location.pathname;if(h.startsWith('tel:'))return'phone_click';let u;try{u=new URL(h,location.href)}catch(_){u=null}const path=u?u.pathname:h.split(/[?#]/)[0];if(u&&/^(?:tampabayshine\.bookingkoala\.com|booking\.tampabayshine\.com)$/i.test(u.hostname)){if(path==='/booknow'||path==='/booknow/')return'booking_external_fallback_click';if(path==='/contact-us'||path==='/contact-us/')return'contact_external_fallback_click';}if(path==='/booknow'||path==='/booknow/'||path==='/book'||path==='/book/')return'booknow_click';if(path==='/coupons'||path==='/coupons/')return'coupon_click';if(/google\.com\/search\?q=.*reviews|google\.com\/maps/i.test(h))return'review_click';if(path==='/contact-us'||path==='/contact-us/')return /office-cleaning|commercial-cleaning|medical-office|common-area|floor-|gym-cleaning|post-construction|post-event/.test(p)?'commercial_quote_start':'contact_click';return''};document.addEventListener('click',e=>{const a=e.target.closest&&e.target.closest('a[href]');if(!a)return;const event=classify(a);if(!event)return;const detail={event,event_name:event,page_path:location.pathname,link_url:a.href,link_text:(a.textContent||'').trim().replace(/\s+/g,' ').slice(0,120)};window.dispatchEvent(new CustomEvent('tbs:conversion',{detail}));if(Array.isArray(window.dataLayer))window.dataLayer.push(detail);if(typeof window.gtag==='function')window.gtag('event',event,{send_to:'G-XK4CTL9KWM',page_path:detail.page_path,link_url:detail.link_url,link_text:detail.link_text})})})();

/* TBS_MOBILE_CTA_SITEWIDE_20261124 */
(()=>{
  const path=location.pathname.toLowerCase();
  // Avoid conversion/checkout/contact forms and unrelated utility pages.
  if (/^\/(?:book|booknow|login|contact-us|signature\/book|privacy-policy|terms|sms-opt-in|careers|gift-card|404)(?:\/|$)/.test(path)) return;
  if (document.body.classList.contains('has-tbs-mobile-sticky-cta')) return;
  // Keep all native sticky buttons; do not display a second bar.
  if (document.querySelector('.mobile-book-bar,.tbs-mobile-sticky-cta,.mobile-sticky-cta,.sticky-book-bar,[data-mobile-cta]')) return;
  const main=document.querySelector('main');
  if (!main) return;
  const links=[...main.querySelectorAll('a[href]')];
  const candidates=links.map((a,i)=>{
    const label=(a.textContent||'').replace(/\s+/g,' ').trim();
    let url;
    try{url=new URL(a.getAttribute('href'),location.href)}catch(_){return null}
    if (url.origin!==location.origin) return null;
    const book=/^\/(?:book|booknow)\/?$/.test(url.pathname);
    const contact=/^\/contact-us\/?$/.test(url.pathname);
    if(!book&&!contact) return null;
    if(!/(?:book|price|pricing|quote|walkthrough|estimate|contact us|schedule|consultation)/i.test(label)) return null;
    const button=a.matches('[class*="btn"],[class*="button"],[class*="cta"],.site-book');
    return {a,i,label,book,contact,button};
  }).filter(Boolean);
  if(!candidates.length) return;
  // Commercial pages should lead to a scoped quote rather than residential booking.
  const commercial=/commercial|office-cleaning|gym-cleaning|medical-office|floor-cleaning|floor-stripping|post-construction|post-event|common-area|property-management|janitorial|restroom|window-cleaning-commercial/.test(path);
  const preferred=candidates.filter(x=>commercial?x.contact:x.book);
  const pool=preferred.length?preferred:candidates;
  const chosen=pool.find(x=>x.button)||pool[0];
  if(!chosen) return;
  const bar=document.createElement('div');
  bar.className='tbs-mobile-sticky-cta';
  bar.setAttribute('role','region');
  bar.setAttribute('aria-label','Quick booking or quote request');
  const copy=document.createElement('div');
  copy.className='tbs-mobile-sticky-copy';
  const title=document.createElement('strong');
  title.textContent=commercial?'COMMERCIAL CLEANING':'TAMPA BAY SHINE';
  const sub=document.createElement('span');
  sub.textContent=chosen.book?'See your price online':'Get a customized cleaning quote';
  copy.append(title,sub);
  const action=document.createElement('a');
  action.className='tbs-mobile-sticky-button';
  action.href=chosen.a.href;
  action.textContent=chosen.book?'Get My Price':/walkthrough/i.test(chosen.label)?'Request Walkthrough':'Request a Quote';
  action.setAttribute('aria-label',action.textContent+' — Tampa Bay Shine');
  bar.append(copy,action);
  document.body.append(bar);
  document.body.classList.add('has-tbs-mobile-sticky-cta');
})();
