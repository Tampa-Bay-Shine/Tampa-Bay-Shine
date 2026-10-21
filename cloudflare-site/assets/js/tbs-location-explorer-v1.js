(function(){
  var root=document.querySelector('#tbs-locations-funnel-v1');
  if(!root)return;
  var data={
    tampa:{title:'Tampa / South Tampa',badge:'Tampa',blurb:'House cleaning, apartments, Airbnb turnovers, move-out cleaning and office cleaning in Tampa and South Tampa.',services:[['House Cleaning','Routine and one-time home cleaning','/house-cleaning-south-tampa-fl/'],['Apartment Cleaning','Apartments, condos and townhomes','/apartment-cleaning-tampa/'],['Airbnb Cleaning','Short-term rental turnovers','/airbnb-cleaning-tampa/'],['Move-Out Cleaning','Moving, rentals and handoffs','/move-out-cleaning-tampa/'],['Office Cleaning','Professional office and janitorial service','/office-cleaning-south-tampa/']]},
    brandon:{title:'Brandon',badge:'Brandon',blurb:'House, apartment, Airbnb, move-out and office cleaning for Brandon customers.',services:[['House Cleaning','Routine and one-time home cleaning','/house-cleaning-brandon-fl/'],['Apartment Cleaning','Apartments and condos','/apartment-cleaning-brandon/'],['Airbnb Cleaning','Turnover cleaning for hosts','/airbnb-cleaning-brandon/'],['Move-Out Cleaning','Move and rental handoffs','/move-out-cleaning-brandon/'],['Office Cleaning','Commercial office service','/office-cleaning-brandon/']]},
    riverview:{title:'Riverview',badge:'Riverview',blurb:'House, apartment, Airbnb, move-out and office cleaning in Riverview.',services:[['House Cleaning','Routine and one-time home cleaning','/house-cleaning-riverview-fl/'],['Apartment Cleaning','Apartments and condos','/apartment-cleaning-riverview/'],['Airbnb Cleaning','Turnover cleaning for hosts','/airbnb-cleaning-riverview/'],['Move-Out Cleaning','Move and rental handoffs','/move-out-cleaning-riverview/'],['Office Cleaning','Commercial office service','/office-cleaning-riverview/']]},
    wesley:{title:'Wesley Chapel',badge:'Wesley Chapel',blurb:'Residential and commercial cleaning options for Wesley Chapel.',services:[['House Cleaning','Routine and one-time home cleaning','/house-cleaning-wesley-chapel-fl/'],['Apartment Cleaning','Apartments and condos','/apartment-cleaning-wesley-chapel/'],['Airbnb Cleaning','Turnover cleaning for hosts','/airbnb-cleaning-wesley-chapel/'],['Move-Out Cleaning','Move and rental handoffs','/move-out-cleaning-wesley-chapel/'],['Office Cleaning','Commercial office service','/office-cleaning-wesley-chapel/']]},
    apollo:{title:'Apollo Beach',badge:'Apollo Beach',blurb:'House, apartment, Airbnb, move-out and office cleaning for Apollo Beach.',services:[['House Cleaning','Routine and one-time home cleaning','/house-cleaning-apollo-beach/'],['Apartment Cleaning','Apartments and condos','/apartment-cleaning-apollo-beach/'],['Airbnb Cleaning','Turnover cleaning for hosts','/airbnb-cleaning-apollo-beach/'],['Move-Out Cleaning','Move and rental handoffs','/move-out-cleaning-apollo-beach/'],['Office Cleaning','Commercial office service','/office-cleaning-apollo-beach/']]},
    downtown:{title:'Downtown Tampa',badge:'Downtown Tampa',blurb:'Start with Downtown Tampa house cleaning, or choose another type of cleaning from the Services page.',services:[['House Cleaning','Downtown Tampa home cleaning','/house-cleaning-downtown-tampa/'],['Choose Another Service','Find the right clean first','/services/']]},
    ruskin:{title:'Ruskin',badge:'Ruskin',blurb:'Start with Ruskin house cleaning, or choose another type of cleaning from the Services page.',services:[['House Cleaning','Ruskin home cleaning','/house-cleaning-ruskin-fl/'],['Choose Another Service','Find the right clean first','/services/']]},
    scc:{title:'Sun City Center',badge:'Sun City Center',blurb:'Start with Sun City Center house cleaning, or choose another type of cleaning from the Services page.',services:[['House Cleaning','Sun City Center home cleaning','/house-cleaning-sun-city-center-fl/'],['Choose Another Service','Find the right clean first','/services/']]}
  };
  var title=root.querySelector('#f-city-title'),
      blurb=root.querySelector('#f-city-blurb'),
      badge=root.querySelector('#f-city-badge'),
      services=root.querySelector('#f-city-services'),
      select=root.querySelector('#f-city-select');

  function syncButtons(key){
    root.querySelectorAll('.f-city-button').forEach(function(x){
      var active=x.getAttribute('data-city')===key;
      x.classList.toggle('active',active);
      x.setAttribute('aria-pressed',active?'true':'false');
    });
  }

  function render(key){
    var d=data[key];if(!d)return;
    title.textContent=d.title;
    blurb.textContent=d.blurb;
    badge.textContent=d.badge;
    services.innerHTML='';
    d.services.forEach(function(s){
      var a=document.createElement('a');
      a.className='f-service-link';
      a.href=s[2];
      a.innerHTML='<strong>'+s[0]+'</strong><span>'+s[1]+'</span>';
      services.appendChild(a);
    });
    if(select && select.value!==key)select.value=key;
    syncButtons(key);
  }

  root.querySelectorAll('.f-city-button').forEach(function(btn){
    btn.addEventListener('click',function(){
      render(btn.getAttribute('data-city'));
    });
  });

  if(select){
    select.addEventListener('change',function(){
      render(select.value);
    });
  }

  render('tampa');
})();
