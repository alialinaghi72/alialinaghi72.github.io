/* اطلس کانسارها: فیلتر بر اساس ماده معدنی (نشانه‌های دیگر کم‌رنگ می‌شوند و کارت‌ها پنهان) */
(function(){
  var f=document.querySelector('.map-filter'); if(!f) return;
  var marks=[].slice.call(document.querySelectorAll('.iran-map .dep, .iran-map .dep-l')), cards=[].slice.call(document.querySelectorAll('.dep-card[data-c]'));
  f.addEventListener('click',function(e){
    var b=e.target.closest('button'); if(!b) return;
    var k=b.getAttribute('data-f');
    f.querySelectorAll('button').forEach(function(x){ x.classList.toggle('on',x===b); x.setAttribute('aria-pressed',x===b?'true':'false'); });
    marks.forEach(function(m){ m.classList.toggle('dim',k!=='all'&&m.getAttribute('data-c')!==k); });
    cards.forEach(function(c){ c.hidden=k!=='all'&&c.getAttribute('data-c')!==k; });
  });
})();
