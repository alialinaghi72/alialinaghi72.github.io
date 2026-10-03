(function(){
  var doc=document.documentElement, fa=doc.lang==='fa';
  var EMAIL='alialinaghi72@gmail.com', WA='989135133397';

  // header shadow + mobile menu
  var header=document.querySelector('header'), menuBtn=document.getElementById('menu-btn');
  function onScroll(){ header.classList.toggle('scrolled', window.scrollY>8); }
  window.addEventListener('scroll',onScroll,{passive:true}); onScroll();
  function setMenu(open){
    doc.classList.toggle('menu-open',open);
    menuBtn.setAttribute('aria-expanded',open?'true':'false');
  }
  menuBtn.addEventListener('click',function(){ setMenu(!doc.classList.contains('menu-open')); });
  document.querySelectorAll('nav .links a').forEach(function(a){ a.addEventListener('click',function(){ setMenu(false); }); });
  document.addEventListener('keydown',function(e){ if(e.key==='Escape') setMenu(false); });

  // highlight current section in nav
  var navLinks={};
  document.querySelectorAll('nav .links a[href^="#"]').forEach(function(a){ navLinks[a.getAttribute('href').slice(1)]=a; });
  if('IntersectionObserver' in window){
    var spy=new IntersectionObserver(function(entries){
      entries.forEach(function(en){
        var a=navLinks[en.target.id]; if(!a) return;
        if(en.isIntersecting){ Object.keys(navLinks).forEach(function(k){ navLinks[k].classList.remove('active'); }); a.classList.add('active'); }
      });
    },{rootMargin:'-45% 0px -50% 0px'});
    Object.keys(navLinks).forEach(function(id){ var s=document.getElementById(id); if(s) spy.observe(s); });

    // reveal on scroll
    var rv=new IntersectionObserver(function(entries){
      entries.forEach(function(en){ if(en.isIntersecting){ en.target.classList.add('in'); rv.unobserve(en.target); } });
    },{rootMargin:'0px 0px -8% 0px'});
    document.querySelectorAll('.rv').forEach(function(el){ rv.observe(el); });
  } else {
    document.querySelectorAll('.rv').forEach(function(el){ el.classList.add('in'); });
  }

  // footer year
  var y=document.getElementById('year'); if(y) y.textContent=fa ? new Date().getFullYear().toLocaleString('fa-IR',{useGrouping:false}) : new Date().getFullYear();

  // contact form: posts to a form service when data-endpoint is set, otherwise email / WhatsApp
  var form=document.getElementById('form'); if(!form) return;
  var status=document.getElementById('f-status');
  function fields(){
    return {n:form.elements.name.value.trim(), m:form.elements.email.value.trim(), t:form.elements.message.value.trim()};
  }
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
