(function(){
  var out = { canvas: !!document.querySelector('canvas'), canvases: document.querySelectorAll('canvas').length };
  var btns = [];
  document.querySelectorAll('button, a, [role=button], [class*="button"], [class*="tab"], [class*="mode"]').forEach(function(el){
    var t = (el.innerText||el.textContent||'').trim();
    if(t.length > 0 && t.length < 60) {
      var r = el.getBoundingClientRect();
      if(r.width > 10 && r.height > 5) btns.push({ text: t.replace(/\n/g,' ').slice(0,35), cx: Math.round(r.x+r.width/2), cy: Math.round(r.y+r.height/2), w: Math.round(r.width), h: Math.round(r.height) });
    }
  });
  out.btns = btns;
  var main = document.querySelector('main, [role=main], #content, .content, .game-area, canvas');
  if(main){ var r = main.getBoundingClientRect(); out.mainRect = { w: r.width, h: r.height, cx: Math.round(r.x+r.width/2), cy: Math.round(r.y+r.height/2) }; }
  var canv = document.querySelector('canvas');
  if(canv){ var r = canv.getBoundingClientRect(); out.canvasRect = { w: r.width, h: r.height, cx: Math.round(r.x+r.width/2), cy: Math.round(r.y+r.height/2) }; }
  return JSON.stringify(out);
})();
