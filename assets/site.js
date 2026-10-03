(function(){
  var doc=document.documentElement, fa=doc.lang==='fa';
  var EMAIL='alialinaghi72@gmail.com', WA='989135133397';
  var reduce=window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var IO='IntersectionObserver' in window;
  function faNum(n){ return fa ? Number(n).toLocaleString('fa-IR',{useGrouping:false}) : String(n); }
  function clamp(v,a,b){ return v<a?a:v>b?b:v; }

  // header: shadow after scrolling, hides on scroll down and returns on scroll up
  var header=document.querySelector('.site-header'), menuBtn=document.getElementById('menu-btn'), lastY=window.scrollY;
  function setMenu(open){ doc.classList.toggle('menu-open',open); menuBtn.setAttribute('aria-expanded',open?'true':'false'); }
  menuBtn.addEventListener('click',function(){ setMenu(!doc.classList.contains('menu-open')); });
  document.querySelectorAll('nav .links a').forEach(function(a){ a.addEventListener('click',function(){ setMenu(false); }); });
  document.addEventListener('keydown',function(e){ if(e.key==='Escape') setMenu(false); });

  // hero fades/scales away; statement words light up in reading order
  var hero=document.querySelector('.hero'), words=[], say=document.querySelector('.say');
  if(say){
    var hl=(say.getAttribute('data-hl')||'').split(' ').filter(Boolean);
    say.innerHTML=say.textContent.trim().split(/\s+/).map(function(w){
      var on=hl.some(function(h){ return w.replace(/[.،,]/g,'')===h; });
      return '<span class="w'+(on?' hl':'')+'">'+w+'</span>';
    }).join(' ');
    words=[].slice.call(say.querySelectorAll('.w'));
  }
  function frame(){
    var y=window.scrollY, vh=window.innerHeight;
    header.classList.toggle('scrolled', y>8);
    if(!doc.classList.contains('menu-open')) header.classList.toggle('hide', y>lastY && y>420);
    lastY=y;
    if(reduce) return;
    if(hero){ doc.style.setProperty('--hp', clamp(y/(hero.offsetHeight*.9),0,1).toFixed(3)); }
    if(words.length){
      var r=say.getBoundingClientRect(), p=clamp((vh*.85-r.top)/(vh*.5),0,1)*words.length;
      words.forEach(function(w,i){ w.style.setProperty('--o', Math.max(.14, clamp(p-i,0,1)).toFixed(2)); });
    }
  }
  var ticking=false;
  window.addEventListener('scroll',function(){ if(!ticking){ ticking=true; requestAnimationFrame(function(){ frame(); ticking=false; }); } },{passive:true});
  window.addEventListener('resize',frame); frame();

  if(IO){
    // reveal on scroll
    var rv=new IntersectionObserver(function(es){
      es.forEach(function(e){ if(e.isIntersecting){ e.target.classList.add('in'); rv.unobserve(e.target); } });
    },{rootMargin:'0px 0px -10% 0px'});
    document.querySelectorAll('.rv').forEach(function(el){ rv.observe(el); });

    // active link: main nav on the home page, table of contents on topic pages
    function spy(selector){
      var map={};
      document.querySelectorAll(selector).forEach(function(a){ var id=a.getAttribute('href').split('#')[1]; if(id) map[id]=a; });
      var o=new IntersectionObserver(function(es){
        es.forEach(function(e){
          if(!e.isIntersecting||!map[e.target.id]) return;
          Object.keys(map).forEach(function(k){ map[k].classList.remove('active'); }); map[e.target.id].classList.add('active');
        });
      },{rootMargin:'-40% 0px -55% 0px'});
      Object.keys(map).forEach(function(id){ var s=document.getElementById(id); if(s) o.observe(s); });
    }
    spy('nav .links a[href^="#"]'); spy('.toc a');

    // story: each step drives the sticky model
    var stage=document.getElementById('stage');
    if(stage){
      var steps=[].slice.call(document.querySelectorAll('.story-steps li'));
      var so=new IntersectionObserver(function(es){
        es.forEach(function(e){
          if(!e.isIntersecting) return;
          steps.forEach(function(s){ s.classList.toggle('on', s===e.target); });
          stage.setAttribute('data-step', e.target.getAttribute('data-step'));
        });
      },{rootMargin:'-45% 0px -45% 0px'});
      steps.forEach(function(s){ so.observe(s); });
      steps[0].classList.add('on');
    }

    // counters
    var co=new IntersectionObserver(function(es){
      es.forEach(function(e){
        if(!e.isIntersecting) return; co.unobserve(e.target);
        var el=e.target, to=+el.getAttribute('data-count'), pre=el.getAttribute('data-prefix')||'', suf=el.getAttribute('data-suffix')||'';
        if(reduce){ return; }
        var t0=performance.now(), dur=1400;
        (function step(t){
          var k=clamp((t-t0)/dur,0,1), v=Math.round(to*(1-Math.pow(1-k,3)));
          el.textContent=pre+faNum(v)+suf; if(k<1) requestAnimationFrame(step);
        })(t0);
      });
    },{threshold:.6});
    document.querySelectorAll('[data-count]').forEach(function(el){ co.observe(el); });
  } else {
    document.querySelectorAll('.rv').forEach(function(el){ el.classList.add('in'); });
  }

  // business card follows the pointer slightly
  var card=document.querySelector('.vcard.tilt');
  if(card && !reduce && window.matchMedia('(pointer:fine)').matches){
    card.addEventListener('pointermove',function(e){
      var r=card.getBoundingClientRect(), x=(e.clientX-r.left)/r.width-.5, y=(e.clientY-r.top)/r.height-.5;
      card.style.setProperty('--ry',(x*10).toFixed(2)+'deg'); card.style.setProperty('--rx',(-y*10).toFixed(2)+'deg');
    });
    card.addEventListener('pointerleave',function(){ card.style.setProperty('--ry','0deg'); card.style.setProperty('--rx','0deg'); });
  }

  // footer year
  var yr=document.getElementById('year'); if(yr) yr.textContent=faNum(new Date().getFullYear());

  // contact form: posts to a form service when data-endpoint is set, otherwise email / WhatsApp
  var form=document.getElementById('form'); if(!form) return;
  var status=document.getElementById('f-status');
  function fields(){ return {n:form.elements.name.value.trim(), m:form.elements.email.value.trim(), t:form.elements.message.value.trim()}; }
  function text(f){ return f.t+'\n\n'+f.n+(f.m?' — '+f.m:''); }
  function subject(f){ return (fa?'درخواست مشاوره از ':'Consulting enquiry from ')+f.n; }
  document.getElementById('f-wa').addEventListener('click',function(){
    if(!form.reportValidity()) return;
    window.open('https://wa.me/'+WA+'?text='+encodeURIComponent(text(fields())),'_blank','noopener');
  });
  form.addEventListener('submit',function(e){
    e.preventDefault();
    var f=fields(), endpoint=form.getAttribute('data-endpoint');
    if(!endpoint){
      window.location.href='mailto:'+EMAIL+'?subject='+encodeURIComponent(subject(f))+'&body='+encodeURIComponent(text(f));
      status.textContent=fa?'برنامهٔ ایمیل باز شد. اگر باز نشد، از دکمهٔ واتس‌اپ استفاده کنید.':'Your email app should open. If it does not, use the WhatsApp button.';
      return;
    }
    status.textContent=fa?'در حال ارسال…':'Sending…';
    fetch(endpoint,{method:'POST',headers:{'Accept':'application/json','Content-Type':'application/json'},
      body:JSON.stringify({name:f.n,email:f.m,message:f.t,_subject:subject(f)})})
      .then(function(r){ if(!r.ok) throw 0; form.reset(); status.textContent=fa?'پیام شما ارسال شد. سپاس.':'Message sent. Thank you.'; })
      .catch(function(){ status.textContent=fa?'ارسال انجام نشد. لطفاً از واتس‌اپ یا ایمیل استفاده کنید.':'Sending failed. Please use WhatsApp or email.'; });
  });
})();
