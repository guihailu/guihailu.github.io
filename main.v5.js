
(function(){var p=document.getElementById('progress');function upd(){var h=document.documentElement;var d=h.scrollHeight-h.clientHeight;p.style.width=(d>0?(h.scrollTop/d)*100:0)+'%';}document.addEventListener('scroll',upd,{passive:true});upd();})();
(function(){var b=document.getElementById('toggle');var MOON='<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>';var SUN='<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="4.2"/><path d="M12 2v2.6M12 19.4V22M4.9 4.9l1.8 1.8M17.3 17.3l1.8 1.8M2 12h2.6M19.4 12H22M4.9 19.1l1.8-1.8M17.3 6.7l1.8-1.8"/></svg>';function sync(){var d=document.documentElement.classList.contains('dark');b.innerHTML=d?SUN:MOON;}b.addEventListener('click',function(){document.documentElement.classList.toggle('dark');try{localStorage.setItem('ghl_theme',document.documentElement.classList.contains('dark')?'dark':'light')}catch(e){}sync();});sync();})();
(function(){var read=[];try{read=JSON.parse(localStorage.getItem('ghl_read')||'[]')}catch(e){}
var cur=null;
document.querySelectorAll('.toc a[href^="#sec-"]').forEach(function(a){
  var id=a.getAttribute('href').slice(1);
  if(read.indexOf(id)>-1){a.classList.add('done')}
  a.addEventListener('click',function(){
    var d=document.getElementById(id);
    if(d){d.open=true;if(read.indexOf(id)<0){read.push(id);try{localStorage.setItem('ghl_read',JSON.stringify(read))}catch(e){}}}
    document.querySelectorAll('.toc a.here').forEach(function(x){x.classList.remove('here')});
    a.classList.add('here');a.classList.add('done');
    cur=id;
  });
});
document.querySelectorAll('.entry summary').forEach(function(s){
  s.addEventListener('click',function(){var e=s.parentElement;if(e&&e.id){cur=e.id;}});
});
function findCur(){var best=null;document.querySelectorAll('.entry').forEach(function(e){var r=e.getBoundingClientRect();if(r.top<=120){best=e;}});if(best){cur=best.id;var a=document.querySelector('.toc a[href="#'+cur+'"]');if(a&&!a.classList.contains('here')){document.querySelectorAll('.toc a.here').forEach(function(x){x.classList.remove('here')});a.classList.add('here');}}return cur;}
document.getElementById('toTop').addEventListener('click',function(){window.scrollTo({top:0,behavior:'smooth'});});
function curOpenArticle(){
  // 当前文章 = 已展开(details[open])且其标题已滚出视口上方的卡片；取距视口顶最近的一张
  var best=null;
  document.querySelectorAll('.entry[open]').forEach(function(e){
    var s=e.querySelector('summary');
    if(!s)return;
    var b=s.getBoundingClientRect().bottom;
    if(b<=0&&(!best||b>best.b)){best={id:e.id,b:b};}
  });
  return best?best.id:null;
}
function updateNav(){
  var btn=document.getElementById('toReading');
  if(!btn)return;
  if(curOpenArticle()){btn.classList.add('nav-on');}else{btn.classList.remove('nav-on');}
}
document.getElementById('toReading').addEventListener('click',function(){
  var id=curOpenArticle();
  if(id){var el=document.getElementById(id);if(el){var s=el.querySelector('summary');window.scrollTo({top:s.getBoundingClientRect().top+window.scrollY-16,behavior:'smooth'});return;}}
  window.scrollTo({top:0,behavior:'smooth'});
});
document.addEventListener('toggle',function(ev){if(ev.target&&ev.target.classList&&ev.target.classList.contains('entry')){updateNav();}},true);
var saved=0;try{saved=parseInt(localStorage.getItem('ghl_scroll')||'0',10)}catch(e){}
if(saved>0&&!location.hash){window.scrollTo(0,saved)}
var t;document.addEventListener('scroll',function(){clearTimeout(t);t=setTimeout(function(){try{localStorage.setItem('ghl_scroll',String(window.scrollY))}catch(e){}},400);findCur();updateNav();},{passive:true});
})();
(function(){var d=document.querySelector('details.tocm');if(d){var wide=null;function sync(){var now=window.innerWidth>960;if(now!==wide){d.open=now;wide=now;}}sync();window.addEventListener('resize',sync);}})();
(function(){var p=document.querySelector('.intro p');if(p&&p.firstChild&&p.firstChild.nodeType===3){p.firstChild.textContent=p.firstChild.textContent.replace('💜 ','');}})();
/* ---- 全文检索（10-07 新增）：即时过滤 + 点击展开定位 ---- */
(function(){var box=document.getElementById('q'),res=document.getElementById('qres');if(!box||!res)return;var idx=null;
var p=(window.__GHL_INDEX__)?Promise.resolve(window.__GHL_INDEX__):fetch('search_index.json').then(function(r){if(!r.ok)throw 0;return r.json()}).catch(function(){return{entries:[],count:0,err:1}});
function esc(s){return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');}
function mark(s,q){var i=String(s).toLowerCase().indexOf(q.toLowerCase());if(i<0)return esc(s);return esc(String(s).slice(0,i))+'<mark>'+esc(String(s).slice(i,i+q.length))+'</mark>'+esc(String(s).slice(i+q.length));}
function snip(t,q){t=String(t);var i=t.toLowerCase().indexOf(q.toLowerCase());var s=i<0?0:Math.max(0,i-15);return (s>0?'…':'')+t.slice(s,s+60)+(t.length>s+60?'…':'');}
function render(q){q=q.trim();if(!q){res.classList.remove('on');res.innerHTML='';return;}
p.then(function(j){if(j)idx=j;var es=(idx&&idx.entries)||[];
if(idx&&idx.err){res.innerHTML='<div class="qnone">检索数据加载失败，刷新页面重试</div>';res.classList.add('on');return;}
var ql=q.toLowerCase(),out=[];for(var i=0;i<es.length;i++){var e=es[i];if((e.title||'').toLowerCase().indexOf(ql)>-1||(e.text||'').toLowerCase().indexOf(ql)>-1)out.push(e);}
if(!out.length){res.innerHTML='<div class="qnone">没有找到与「'+esc(q)+'」相关的内容</div>';}
else{var h='<div class="qcount">'+out.length+' 条结果</div>';for(var k=0;k<out.length;k++){var e2=out[k];h+='<div class="qitem" data-id="'+e2.id+'"><div class="qhead"><span class="qt">'+mark(e2.title||'',q)+'</span><span class="qd">'+esc(e2.date||'')+'</span></div><div class="qs">'+mark(snip(e2.text||'',q),q)+'</div></div>';}res.innerHTML=h;}
res.classList.add('on');});}
box.addEventListener('input',function(){render(box.value)});
box.addEventListener('focus',function(){if(box.value.trim())render(box.value)});
res.addEventListener('click',function(ev){var n=ev.target;while(n&&n!==res&&!(n.classList&&n.classList.contains('qitem')))n=n.parentNode;if(!n||n===res)return;var id=n.getAttribute('data-id');res.classList.remove('on');var a=document.querySelector('.toc a[href="#'+id+'"]');if(a)a.click();var el=document.getElementById(id);if(el){setTimeout(function(){el.scrollIntoView({behavior:'smooth',block:'start'});},60);}});
document.addEventListener('click',function(ev){var n=ev.target;while(n){if(n.classList&&n.classList.contains('searchbar'))return;n=n.parentNode;}res.classList.remove('on');});
})();
