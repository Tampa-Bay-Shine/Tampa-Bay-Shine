/* Tampa Bay Shine Signature booking selector.
 * Only the URL parameters already implemented in the main booking flow are used.
 * Never send PII to a URL or analytics. Property and contact fields stay in BookingKoala.
 */
(function(){
  'use strict';
  var form=document.getElementById('signature-choices');
  var panel=document.getElementById('signature-step-choice');
  var booking=document.getElementById('signature-step-booking');
  var frame=document.getElementById('signature-booking-frame');
  var fallback=document.getElementById('signature-external-booking');
  var frequencyGroup=document.getElementById('signature-frequency');
  var summary=document.getElementById('signature-selection-summary');
  var edit=document.getElementById('signature-edit');
  if(!form||!panel||!booking||!frame||!fallback||!frequencyGroup||!summary||!edit)return;

  var serviceIds={standard:'6',deep:'18'};
  var serviceLabels={standard:'Standard Cleaning',deep:'Deep Cleaning'};
  var frequencyIds={'one-time':'1','weekly':'9','biweekly':'4','every-3-weeks':'5','every-4-weeks':'2'};
  var frequencyLabels={'unspecified':'Frequency to be chosen in booking','one-time':'One-time','weekly':'Weekly','biweekly':'Every 2 weeks','every-3-weeks':'Every 3 weeks','every-4-weeks':'Every 4 weeks'};
  var params=new URLSearchParams(location.search);
  var wantedService=params.get('cleaning');
  var wantedFrequency=params.get('frequency');
  if(Object.prototype.hasOwnProperty.call(serviceIds,wantedService)){
    var selected=form.querySelector('input[name="cleaning"][value="'+wantedService+'"]');
    if(selected)selected.checked=true;
  }
  if(Object.prototype.hasOwnProperty.call(frequencyLabels,wantedFrequency)){
    var frequencyInput=form.querySelector('input[name="frequency"][value="'+wantedFrequency+'"]');
    if(frequencyInput)frequencyInput.checked=true;
  }

  function currentService(){return form.querySelector('input[name="cleaning"]:checked').value;}
  function currentFrequency(){return form.querySelector('input[name="frequency"]:checked').value;}
  function updateFrequency(){
    var deep=currentService()==='deep';
    frequencyGroup.hidden=deep;
    if(deep){var fallbackChoice=form.querySelector('input[name="frequency"][value="unspecified"]');if(fallbackChoice)fallbackChoice.checked=true;}
  }
  form.addEventListener('change',function(event){if(event.target.name==='cleaning')updateFrequency();});
  updateFrequency();

  function makeBookingUrl(embed){
    var service=currentService();
    var url=new URL('https://tampabayshine.bookingkoala.com/booknow');
    if(embed)url.searchParams.set('embed','true');
    url.searchParams.set('service_id',serviceIds[service]);
    var freq=currentFrequency();
    if(service==='standard'&&Object.prototype.hasOwnProperty.call(frequencyIds,freq)){
      url.searchParams.set('frequency_id',frequencyIds[freq]);
    }
    return url.toString();
  }
  function track(name){
    var data={event:name,page_path:location.pathname,signature_cleaning:currentService(),signature_frequency:currentService()==='standard'?currentFrequency():'not_applicable'};
    if(Array.isArray(window.dataLayer))window.dataLayer.push(data);
    if(typeof window.gtag==='function')window.gtag('event',name,{page_path:data.page_path,signature_cleaning:data.signature_cleaning,signature_frequency:data.signature_frequency,send_to:'G-XK4CTL9KWM'});
  }

  form.addEventListener('submit',function(event){
    event.preventDefault();
    var service=currentService(),freq=currentFrequency();
    // The frame is updated only on Continue, avoiding accidental loss of entered BK data.
    frame.src=makeBookingUrl(true);
    fallback.href=makeBookingUrl(false);
    summary.textContent=serviceLabels[service]+(service==='standard'?' · '+frequencyLabels[freq]:' · Details and price in the booking form');
    panel.hidden=true;
    booking.hidden=false;
    document.getElementById('signature-stage-service').classList.remove('is-current');
    document.getElementById('signature-stage-service').classList.add('is-complete');
    document.getElementById('signature-stage-details').classList.add('is-current');
    document.getElementById('signature-stage-reserve').classList.add('is-ready');
    track('signature_booking_start');
    booking.scrollIntoView({behavior:window.matchMedia('(prefers-reduced-motion: reduce)').matches?'auto':'smooth',block:'start'});
  });
  edit.addEventListener('click',function(){
    if(frame.src&&frame.src!=='about:blank'){
      var okay=window.confirm('Changing your cleaning will restart the booking form. Continue?');
      if(!okay)return;
    }
    frame.removeAttribute('src');
    booking.hidden=true;
    panel.hidden=false;
    document.getElementById('signature-stage-service').classList.remove('is-complete');
    document.getElementById('signature-stage-service').classList.add('is-current');
    document.getElementById('signature-stage-details').classList.remove('is-current');
    document.getElementById('signature-stage-reserve').classList.remove('is-ready');
    panel.scrollIntoView({behavior:window.matchMedia('(prefers-reduced-motion: reduce)').matches?'auto':'smooth',block:'start'});
  });
})();
