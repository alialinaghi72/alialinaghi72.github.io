/* ابزارهای آنلاین: عیار حد، تبدیل واحد و فلز محتوا، آزمایشگاه واریوگرام. همه‌چیز در مرورگر اجرا می‌شود. */
(function(){
  var fa=document.documentElement.lang==='fa';
  var S1='#C07A45', S2='#34A38C', SURF='#111619', GRID='#222C31', AXIS='#3A464C', MUTED='#8A9599', INK='#E9E5DF', INK2='#98A2A6';
  var NS='http://www.w3.org/2000/svg', DG='۰۱۲۳۴۵۶۷۸۹';
  var TX=fa?{pct:'٪', gpt:'گرم در تن', perPct:'دلار برای هر ۱٪ در هر تن کانسنگ', perGpt:'دلار برای هر گرم در تن', price:'قیمت ($/', priceAx:'قیمت فلز', cogAx:'عیار حد', neg:'قیمت خالص منفی است',
            be:'سربه‌سر', mg:'حاشیه‌ای', strong:'پیوستگی فضایی قوی', moderate:'پیوستگی فضایی متوسط', weak:'پیوستگی فضایی ضعیف', lag:'فاصله (h، متر)', gamma:'واریوگرام γ(h)',
            exp:'تجربی', model:'مدل', pairs:'جفت', m:'متر', t:'تن', kg:'کیلوگرم', oz:'اونس تروی', lb:'پوند', mill:'میلیون', bill:'میلیارد', usd:'دلار'}
           :{pct:'%', gpt:'g/t', perPct:'$ per 1% per tonne of ore', perGpt:'$ per g/t', price:'Price ($/', priceAx:'Metal price', cogAx:'Cut-off grade', neg:'net price is negative',
            be:'Break-even', mg:'Marginal', strong:'strong spatial dependence', moderate:'moderate spatial dependence', weak:'weak spatial dependence', lag:'Lag distance (h, m)', gamma:'Variogram γ(h)',
            exp:'Experimental', model:'Model', pairs:'pairs', m:'m', t:'t', kg:'kg', oz:'troy oz', lb:'lb', mill:'million', bill:'billion', usd:'$'};

  function fmt(v,dec){
    if(v==null||!isFinite(v)) return '—';
    var s=Number(v).toLocaleString('en-US',{minimumFractionDigits:dec,maximumFractionDigits:dec});
    if(fa) s=s.replace(/,/g,'٬').replace(/\./g,'٫').replace(/-/g,'−').replace(/\d/g,function(d){return DG[+d];});
    return s;
  }
  function sig(v){ var a=Math.abs(v); return fmt(v, a>=1000?0:a>=100?1:a>=10?2:a>=1?2:a>=.1?3:4); }
  function big(v){
    if(!isFinite(v)) return '—'; var a=Math.abs(v);
    if(a>=1e9) return fmt(v/1e9,2)+' '+TX.bill; if(a>=1e6) return fmt(v/1e6,2)+' '+TX.mill; return fmt(v,0);
  }
  function nice(lo,hi,n){
    var span=hi-lo||1, raw=span/(n||5), mag=Math.pow(10,Math.floor(Math.log10(raw))), step=mag;
    [1,2,2.5,5,10].some(function(m){ if(raw<=m*mag){ step=m*mag; return true; } });
    var t=[], v=Math.ceil(lo/step-1e-9)*step; while(v<=hi+1e-9){ t.push(+v.toFixed(10)); v+=step; }
    return {t:t, step:step};
  }
  function decOf(step){ var d=Math.max(0,-Math.floor(Math.log10(step)+1e-9)); return Math.abs(step*Math.pow(10,d)-Math.round(step*Math.pow(10,d)))<1e-9?d:d+1; }
  function el(tag,attrs,text){ var e=document.createElementNS(NS,tag); for(var k in attrs) e.setAttribute(k,attrs[k]); if(text!=null) e.textContent=text; return e; }
  /* برچسب فارسی در SVG چپ‌به‌راست: جهت راست‌به‌چپ و جابه‌جایی start/end تا جای دیداری ثابت بماند */
  function label(attrs,text){
    if(fa && /[\u0600-\u06FF]/.test(text)){ attrs.direction='rtl'; var a=attrs['text-anchor']||'start'; attrs['text-anchor']=a==='start'?'end':a==='end'?'start':a; }
    return el('text',attrs,text);
  }

  /* نمودار خطی ساده: cfg = {xs, xlim, ylim, xlabel, ylabel, series:[{name,color,ys,dots,line}], curves:[{color,pts}], hoverX, fmtY, table:{head,rows}} */
  function lineChart(fig, cfg){
    var W=640,H=320,ml=62,mr=18,mt=16,mb=46,x0=ml,x1=W-mr,y0=mt,y1=H-mb;
    var xl=cfg.xlim, yl=cfg.ylim;
    function X(v){ return x0+(v-xl[0])/(xl[1]-xl[0])*(x1-x0); }
    function Y(v){ return y1-(v-yl[0])/(yl[1]-yl[0])*(y1-y0); }
    var svg=el('svg',{viewBox:'0 0 '+W+' '+H,role:'img','aria-label':cfg.label||'',direction:'ltr'});
    var xt=nice(xl[0],xl[1],6), yt=nice(yl[0],yl[1],5), xd=decOf(xt.step), yd=decOf(yt.step);
    var g=el('g',{stroke:GRID,'stroke-width':1});
    yt.t.forEach(function(v){ if(v>=yl[0]&&v<=yl[1]) g.appendChild(el('line',{x1:x0,x2:x1,y1:Y(v),y2:Y(v)})); });
    svg.appendChild(g);
    svg.appendChild(el('line',{x1:x0,x2:x1,y1:y1,y2:y1,stroke:AXIS,'stroke-width':1}));
    var tk=el('g',{fill:MUTED,'font-size':11});
    xt.t.forEach(function(v){ if(v>=xl[0]&&v<=xl[1]) tk.appendChild(el('text',{x:X(v),y:y1+17,'text-anchor':'middle'},(cfg.fmtX||function(v){return fmt(v,xd);})(v))); });
    yt.t.forEach(function(v){ if(v>=yl[0]&&v<=yl[1]) tk.appendChild(el('text',{x:x0-8,y:Y(v)+4,'text-anchor':'end'},fmt(v,yd))); });
    svg.appendChild(tk);
    svg.appendChild(label({x:(x0+x1)/2,y:H-8,'text-anchor':'middle',fill:INK2,'font-size':12},cfg.xlabel));
    svg.appendChild(label({transform:'translate(14 '+((y0+y1)/2)+') rotate(-90)','text-anchor':'middle',fill:INK2,'font-size':12},cfg.ylabel));
    (cfg.curves||[]).forEach(function(c){
      var pts=c.pts.filter(function(p){ return isFinite(p[1]); }).map(function(p){ return X(p[0]).toFixed(1)+','+Y(Math.min(p[1],yl[1])).toFixed(1); }).join(' ');
      svg.appendChild(el('polyline',{points:pts,fill:'none',stroke:c.color,'stroke-width':2,'stroke-linejoin':'round','stroke-linecap':'round'}));
    });
    cfg.series.forEach(function(s){
      if(s.line){
        var pts=cfg.xs.map(function(x,i){ return isFinite(s.ys[i])?X(x).toFixed(1)+','+Y(Math.min(s.ys[i],yl[1])).toFixed(1):null; }).filter(Boolean).join(' ');
        svg.appendChild(el('polyline',{points:pts,fill:'none',stroke:s.color,'stroke-width':2,'stroke-linejoin':'round','stroke-linecap':'round'}));
      }
      if(s.dots) cfg.xs.forEach(function(x,i){ if(isFinite(s.ys[i])) svg.appendChild(el('circle',{cx:X(x),cy:Y(s.ys[i]),r:4.5,fill:s.color,stroke:SURF,'stroke-width':2})); });
    });
    (cfg.marks||[]).forEach(function(m){
      if(!isFinite(m.y)) return;
      svg.appendChild(el('circle',{cx:X(m.x),cy:Y(m.y),r:5,fill:m.color,stroke:SURF,'stroke-width':2}));
      if(m.label) svg.appendChild(label({x:X(m.x)+9,y:Y(m.y)-9,fill:INK,'font-size':12},m.label));
    });
    var box=fig.querySelector('.chart-box'); box.textContent=''; box.appendChild(svg);
    fig.setAttribute('data-hover',JSON.stringify({top:y0,bottom:y1,px:cfg.xs.map(X),xl:cfg.hoverX,
      series:cfg.series.map(function(s){ return {name:s.name,color:s.color,vals:s.ys.map(function(v){ return isFinite(v)?cfg.fmtY(v):''; })}; })}));
    if(window.ChartHover) window.ChartHover.refresh(fig);
    var tbl=fig.querySelector('details.tbl table');
    if(tbl&&cfg.table){
      tbl.textContent='';
      var th=document.createElement('thead'), tr=document.createElement('tr');
      cfg.table.head.forEach(function(h){ var c=document.createElement('th'); c.textContent=h; tr.appendChild(c); }); th.appendChild(tr); tbl.appendChild(th);
      var tb=document.createElement('tbody');
      cfg.table.rows.forEach(function(r){ var row=document.createElement('tr'); r.forEach(function(v){ var c=document.createElement('td'); c.textContent=v; row.appendChild(c); }); tb.appendChild(row); });
      tbl.appendChild(tb);
    }
  }
  function num(form,k){ var v=parseFloat(form.elements[k].value); return isFinite(v)?v:NaN; }
  function out(root,k){ return root.querySelector('[data-o="'+k+'"]'); }

  /* ---------- عیار حد ---------- */
  var PER_T={t:1, lb:2204.62262, oz:32150.7466};
  function initCog(root){
    var P=JSON.parse(root.getAttribute('data-presets')), form=root.querySelector('form'), fig=root.querySelector('figure');
    function labels(){ root.querySelectorAll('[data-pu]').forEach(function(e){ e.textContent='$/'+form.elements.pu.value; }); }
    function preset(id){ var p=P[id]; ['price','sell','rec','pay','mine','proc','ga'].forEach(function(k){ form.elements[k].value=p[k]; }); form.elements.pu.value=p.pu; labels(); calc(); }
    function perUnit(netPrice,pu,unit){ var perT=netPrice*PER_T[pu]; return unit==='pct'?perT/100:perT/1e6; }
    function calc(){
      var unit=P[form.elements.metal.value].unit, pu=form.elements.pu.value;
      var price=num(form,'price'), sell=num(form,'sell')||0, rec=num(form,'rec')/100, pay=num(form,'pay')/100;
      var mine=num(form,'mine')||0, proc=num(form,'proc')||0, ga=num(form,'ga')||0;
      var u=unit==='pct'?TX.pct:' '+TX.gpt, dec=unit==='pct'?3:2;
      var net=perUnit(price-sell,pu,unit)*rec*pay;
      if(!(net>0)){ out(root,'be').textContent=out(root,'mg').textContent='—'; out(root,'nv').textContent=TX.neg; out(root,'nvu').textContent=''; return; }
      out(root,'be').textContent=fmt((mine+proc+ga)/net,dec)+u;
      out(root,'mg').textContent=fmt((proc+ga)/net,dec)+u;
      out(root,'nv').textContent=fmt(net,2)+' $';
      out(root,'nvu').textContent=unit==='pct'?TX.perPct:TX.perGpt;
      var fs=[], xs=[], be=[], mg=[];
      for(var f=.6;f<=1.4001;f+=.05){ fs.push(f); xs.push(price*f); }
      xs.forEach(function(p){ var n=perUnit(p-sell,pu,unit)*rec*pay; be.push(n>0?(mine+proc+ga)/n:NaN); mg.push(n>0?(proc+ga)/n:NaN); });
      var fin=be.filter(isFinite), ymax=fin.length?Math.max.apply(null,fin)*1.1:1;
      var pd=price>=100?0:2;
      lineChart(fig,{xs:xs, xlim:[xs[0],xs[xs.length-1]], ylim:[0,ymax], xlabel:TX.priceAx+' ($/'+pu+')', ylabel:TX.cogAx+' ('+(unit==='pct'?'%':'g/t')+')',
        fmtX:function(v){ return fmt(v,pd); }, fmtY:function(v){ return fmt(v,dec)+u; },
        series:[{name:TX.be,color:S1,ys:be,line:true},{name:TX.mg,color:S2,ys:mg,line:true}],
        marks:[{x:price,y:(mine+proc+ga)/net,color:S1,label:fmt((mine+proc+ga)/net,dec)+u}],
        hoverX:xs.map(function(p){ return TX.price+pu+') '+fmt(p,pd); }),
        table:{head:[TX.priceAx+' ($/'+pu+')',TX.be,TX.mg], rows:xs.map(function(p,i){ return [fmt(p,pd),fmt(be[i],dec),fmt(mg[i],dec)]; })}});
    }
    form.elements.metal.addEventListener('change',function(){ preset(form.elements.metal.value); });
    form.addEventListener('input',function(e){ if(e.target.name==='pu') labels(); if(e.target.name!=='metal') calc(); });
    form.addEventListener('change',function(e){ if(e.target.name==='pu'){ labels(); calc(); } });
    preset('cu');
  }

  /* ---------- تبدیل واحد و فلز محتوا ---------- */
  var TO_GPT={pct:1e4, ppm:1, gpt:1, ppb:1e-3, ozst:34.2857143};
  function initConv(root){
    var form=root.querySelector('form');
    function calc(){
      var ton=num(form,'ton'); if(!(ton>0)) ton=num(form,'vol')*num(form,'dens');
      var g=num(form,'grade')*TO_GPT[form.elements.gu.value], grams=ton*g;
      out(root,'t').textContent=isFinite(ton)?big(ton)+' '+TX.t:'—';
      var precious=form.elements.gu.value!=='pct';
      if(isFinite(grams)){
        out(root,'m').textContent=precious?big(grams/31.1034768)+' '+TX.oz:big(grams/1e6)+' '+TX.t;
        out(root,'m2').textContent=precious?big(grams/1e3)+' '+TX.kg:big(grams/453.59237)+' '+TX.lb;
      } else { out(root,'m').textContent='—'; out(root,'m2').textContent=''; }
      var price=num(form,'price'), pu=form.elements.pu.value;
      var perG=pu==='t'?price/1e6:pu==='lb'?price/453.59237:price/31.1034768;
      out(root,'v').textContent=(price>0&&isFinite(grams))?(fa?big(grams*perG)+' '+TX.usd:'$'+big(grams*perG)):'—';
      var tb=out(root,'tbl'); tb.textContent='';
      [['%',g/1e4],['ppm',g],['g/t',g],['ppb',g*1e3],['oz/st',g/34.2857143],['oz/t ('+(fa?'متریک':'metric')+')',g/31.1034768]].forEach(function(r){
        var tr=document.createElement('tr'), a=document.createElement('td'), b=document.createElement('td'); a.textContent=r[0]; b.textContent=isFinite(r[1])?sig(r[1]):'—';
        tr.appendChild(a); tr.appendChild(b); tb.appendChild(tr);
      });
    }
    form.addEventListener('input',calc); form.addEventListener('change',calc); calc();
  }

  /* ---------- آزمایشگاه واریوگرام ---------- */
  function vmodel(k,h,c0,c1,a){
    if(h<=0) return 0;
    if(k==='sph') return h<a?c0+c1*(1.5*h/a-.5*Math.pow(h/a,3)):c0+c1;
    if(k==='exp') return c0+c1*(1-Math.exp(-3*h/a));
    return c0+c1*(1-Math.exp(-3*h*h/(a*a)));
  }
  function initVlab(root){
    var sets=JSON.parse(root.getAttribute('data-sets')), form=root.querySelector('form'), fig=root.querySelector('figure');
    function set(){ var id=form.elements.set.value; return sets.filter(function(s){ return s.id===id; })[0]; }
    function err(s,k,c0,c1,a){ var sw=0,se=0; s.lags.forEach(function(h,i){ var w=s.pairs[i], d=s.gam[i]-vmodel(k,h,c0,c1,a); sw+=w; se+=w*d*d; }); return Math.sqrt(se/sw); }
    function apply(p){ form.elements.model.value=p.model; form.elements.c0.value=p.c0; form.elements.c1.value=p.c1; form.elements.a.value=p.a; draw(); }
    function setRanges(){ var s=set(), mx=Math.ceil(s.lags[s.lags.length-1]*1.2/10)*10; form.elements.a.max=mx; form.elements.a.min=Math.max(2,Math.round(s.lags[0]/2)); }
    function draw(){
      var s=set(), k=form.elements.model.value, c0=+form.elements.c0.value, c1=+form.elements.c1.value, a=+form.elements.a.value;
      out(root,'c0').textContent=fmt(c0,2); out(root,'c1').textContent=fmt(c1,2); out(root,'a').textContent=fmt(a,0);
      var e=err(s,k,c0,c1,a), sill=c0+c1, r=sill>0?c0/sill:NaN;
      out(root,'err').textContent=fmt(e,3); out(root,'sill').textContent=fmt(sill,2); out(root,'ratio').textContent=isFinite(r)?fmt(r*100,0)+(fa?'٪':'%'):'—';
      var cls=r<.25?TX.strong:r<=.75?TX.moderate:TX.weak; out(root,'cls').textContent=isFinite(r)?cls:'';
      out(root,'interp').textContent=fa
        ? 'با این مدل، '+fmt(r*100,0)+'٪ از واریانس در اثر قطعه‌ای است ('+cls+'). نمونه‌هایی که در فاصلهٔ کمتر از حدود '+fmt(a,0)+' متر از نقطهٔ تخمین قرار دارند در کریجینگ وزن معنادار می‌گیرند'+(k==='exp'?' (دامنهٔ عملی مدل نمایی).':'.')
        : 'With this model, '+fmt(r*100,0)+'% of the variance is nugget ('+cls+'). Samples closer than about '+fmt(a,0)+' m to the estimation point receive meaningful kriging weight'+(k==='exp'?' (practical range of the exponential model).':'.');
      var xmax=s.lags[s.lags.length-1]*1.08, ymax=Math.max(1.25,Math.max.apply(null,s.gam)*1.15,sill*1.1), pts=[];
      for(var i=0;i<=160;i++){ var h=xmax*i/160; pts.push([h,h===0?c0:vmodel(k,h,c0,c1,a)]); }
      lineChart(fig,{xs:s.lags, xlim:[0,xmax], ylim:[0,ymax], xlabel:TX.lag, ylabel:TX.gamma, label:TX.gamma,
        curves:[{color:S1,pts:pts}],
        series:[{name:TX.exp,color:S2,ys:s.gam,dots:true},{name:TX.model,color:S1,ys:s.lags.map(function(h){ return vmodel(k,h,c0,c1,a); })}],
        fmtY:function(v){ return fmt(v,3); },
        hoverX:s.lags.map(function(h,i){ return 'h = '+fmt(h,0)+' '+TX.m+' · '+fmt(s.pairs[i],0)+' '+TX.pairs; }),
        table:{head:[TX.lag,TX.exp,TX.model,TX.pairs], rows:s.lags.map(function(h,i){ return [fmt(h,0),fmt(s.gam[i],3),fmt(vmodel(k,h,c0,c1,a),3),fmt(s.pairs[i],0)]; })}});
    }
    function fit(){
      var s=set(), k=form.elements.model.value, amin=+form.elements.a.min, amax=+form.elements.a.max, best={e:1e9};
      for(var c0=0;c0<=1.2001;c0+=.05) for(var c1=0;c1<=1.5001;c1+=.05) for(var j=0;j<=40;j++){
        var a=amin+(amax-amin)*j/40, e=err(s,k,c0,c1,a); if(e<best.e) best={e:e,c0:c0,c1:c1,a:a};
      }
      var b=best, da=(amax-amin)/40;
      for(var c0f=Math.max(0,b.c0-.05);c0f<=b.c0+.0501;c0f+=.01) for(var c1f=Math.max(0,b.c1-.05);c1f<=b.c1+.0501;c1f+=.01) for(var af=Math.max(amin,b.a-da);af<=b.a+da;af+=Math.max(1,da/10)){
        var ef=err(s,k,c0f,c1f,af); if(ef<best.e) best={e:ef,c0:c0f,c1:c1f,a:af};
      }
      apply({model:k,c0:+best.c0.toFixed(2),c1:+best.c1.toFixed(2),a:Math.round(best.a)});
    }
    form.addEventListener('input',function(e){ if(e.target.name==='set'){ setRanges(); apply(set().start); } else draw(); });
    form.addEventListener('change',function(e){ if(e.target.name==='set'){ setRanges(); apply(set().start); } else if(e.target.name==='model') draw(); });
    root.querySelector('[data-act="fit"]').addEventListener('click',fit);
    root.querySelector('[data-act="reset"]').addEventListener('click',function(){ apply(set().start); });
    setRanges(); apply(set().start);
  }

  var INIT={cog:initCog, conv:initConv, vlab:initVlab};
  document.querySelectorAll('.tool[data-tool]').forEach(function(t){ var f=INIT[t.getAttribute('data-tool')]; if(f) f(t); });
})();
