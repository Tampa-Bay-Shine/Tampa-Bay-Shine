/* Hide the fixed booking bar while the hero's booking CTA remains on screen. */
(()=>{
  const init=()=>{
    const root=document.querySelector('[id^="tbs-"]');
    if(!root)return;
    const hero=root.querySelector('.hero');
    const bar=root.querySelector('.mobile-book-bar');
    if(!hero||!bar||!('IntersectionObserver' in window))return;
    const mobile=window.matchMedia('(max-width: 600px)');
    const update=(visible)=>{bar.style.display=mobile.matches&&visible?'none':'';};
    // Start hidden on mobile to avoid a fixed bar covering the initial hero.
    update(true);
    const observer=new IntersectionObserver(entries=>{
      for(const entry of entries)if(entry.target===hero)update(entry.isIntersecting);
    },{threshold:0});
    observer.observe(hero);
    const refresh=()=>{
      const rect=hero.getBoundingClientRect();
      update(rect.bottom>0&&rect.top<window.innerHeight);
    };
    if(mobile.addEventListener)mobile.addEventListener('change',refresh);
    else if(mobile.addListener)mobile.addListener(refresh);
  };
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init,{once:true});
  else init();
})();
