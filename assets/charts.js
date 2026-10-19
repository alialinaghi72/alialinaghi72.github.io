/* لایهٔ هاور نمودارها: خط راهنمای عمودی + راهنمای همهٔ سری‌ها در آن نقطه، و راهنمای تک‌نشانه برای [data-tip].
   داده‌ها از ویژگی data-hover خوانده می‌شوند تا نمودارهای ابزارها پس از هر بازسازی هم کار کنند.
   متن‌ها همیشه با textContent درج می‌شوند. */
(function(){
  var NS='http://www.w3.org/2000/svg';

  function tipFor(host){
    var t=null;
    for(var i=0;i<host.children.length;i++){ if(host.children[i].classList.contains('chart-tip')){ t=host.children[i]; break; } }
    if(!t){ t=document.createElement('div'); t.className='chart-tip'; t.setAttribute('role','status'); t.hidden=true; host.appendChild(t); }
    return t;
  }
  function place(t, host, sx, sy){
    var r=host.getBoundingClientRect(); t.hidden=false;
    var w=t.offsetWidth, h=t.offsetHeight, x=sx-r.left+14, y=sy-r.top-h-10;
    if(x+w>r.width-4) x=sx-r.left-w-14;
    if(x<4) x=4;
    if(y<4) y=sy-r.top+16;
    t.style.transform='translate('+Math.round(x)+'px,'+Math.round(y)+'px)';
  }

  function initFig(fig){
    if(fig._hv){ fig._hide(); return; }
    fig._hv=true;
    var box=fig.querySelector('.chart-box')||fig, tip=tipFor(fig), idx=-1;
    function data(){ try{ var d=JSON.parse(fig.getAttribute('data-hover')||'null'); return d&&d.px&&d.px.length?d:null; }catch(e){ return null; } }
    function svg(){ return box.querySelector('svg'); }
    function xhair(s,d){
      var l=s.querySelector('line.xhair');
      if(!l){ l=document.createElementNS(NS,'line'); l.setAttribute('class','xhair'); s.appendChild(l); }
      l.setAttribute('y1',d.top); l.setAttribute('y2',d.bottom); return l;
    }
    function nearest(d,x){ var b=0,bd=1e9; for(var i=0;i<d.px.length;i++){ var k=Math.abs(d.px[i]-x); if(k<bd){bd=k;b=i;} } return b; }
    function render(i){
      var d=data(), s=svg(); if(!d||!s) return;
      i=Math.max(0,Math.min(d.px.length-1,i)); idx=i;
      var x=d.px[i], l=xhair(s,d); l.setAttribute('x1',x); l.setAttribute('x2',x); l.style.display='';
      tip.textContent='';
      var hx=document.createElement('div'); hx.className='tt-x'; hx.textContent=d.xl[i]; tip.appendChild(hx);
      d.series.forEach(function(se){
        if(se.vals[i]==null||se.vals[i]==='') return;
        var row=document.createElement('div'); row.className='tt-row';
        var k=document.createElement('i'); k.style.background=se.color;
        var v=document.createElement('b'); v.textContent=se.vals[i];
        var n=document.createElement('span'); n.textContent=se.name;
        row.appendChild(k); row.appendChild(v); row.appendChild(n); tip.appendChild(row);
      });
      var m=s.getScreenCTM(); if(!m) return;
      place(tip, fig, m.a*x+m.e, m.d*(d.top+(d.bottom-d.top)*.25)+m.f);
    }
    function hide(){ var s=svg(), l=s&&s.querySelector('line.xhair'); if(l) l.style.display='none'; tip.hidden=true; idx=-1; }
    box.addEventListener('pointermove',function(e){
      var d=data(), s=svg(); if(!d||!s) return;
      var m=s.getScreenCTM(); if(!m) return;
      var p=s.createSVGPoint(); p.x=e.clientX; p.y=e.clientY;
      render(nearest(d, p.matrixTransform(m.inverse()).x));
    });
    box.addEventListener('pointerleave',hide);
    fig.addEventListener('keydown',function(e){
      if(e.key!=='ArrowRight'&&e.key!=='ArrowLeft') return; e.preventDefault();
      render(idx<0?0:idx+(e.key==='ArrowRight'?1:-1));
    });
    fig.addEventListener('focus',function(e){ if(e.target===fig&&idx<0) render(0); });
    fig.addEventListener('blur',hide);
    fig._hide=hide;
  }

  function initTips(root){
    root.querySelectorAll('[data-tip]').forEach(function(el){
      if(el._tip) return; el._tip=true;
      var host=el.closest('figure, .map-wrap')||document.body;
      if(getComputedStyle(host).position==='static') host.style.position='relative';
      var tip=tipFor(host);
      function show(){ tip.textContent=el.getAttribute('data-tip'); var r=el.getBoundingClientRect(); place(tip, host, r.left+r.width/2, r.top); el.classList.add('hot'); }
      function hide(){ tip.hidden=true; el.classList.remove('hot'); }
      el.addEventListener('pointerenter',show); el.addEventListener('pointerleave',hide);
      el.addEventListener('focus',show); el.addEventListener('blur',hide);
    });
  }

  function init(root){
    root=root||document;
    root.querySelectorAll('figure.chart[data-hover]').forEach(initFig);
    initTips(root);
  }
  window.ChartHover={init:init, refresh:initFig, tips:initTips};
  if(document.readyState==='loading') document.addEventListener('DOMContentLoaded',function(){ init(); }); else init();
})();
