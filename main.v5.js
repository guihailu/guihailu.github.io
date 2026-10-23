
/* 事件钩子（A/B/C）：未接分析服务时静默；接 GoatCounter/Umami/百度/51LA 后自动上报 */
window.ghlTrack=function(name,data){try{
  if(window.goatcounter&&window.goatcounter.count)window.goatcounter.count({path:name,title:name,event:true});
  if(window.umami&&window.umami.track)window.umami.track(name,data||{});
  if(window._hmt)window._hmt.push(['_trackEvent',name,'click',JSON.stringify(data||{})]);
}catch(e){}};
(function(){var p=document.getElementById('progress');function upd(){var h=document.documentElement;var d=h.scrollHeight-h.clientHeight;p.style.width=(d>0?(h.scrollTop/d)*100:0)+'%';}document.addEventListener('scroll',upd,{passive:true});upd();})();
(function(){var b=document.getElementById('toggle');var MOON='<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>';var SUN='<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="4.2"/><path d="M12 2v2.6M12 19.4V22M4.9 4.9l1.8 1.8M17.3 17.3l1.8 1.8M2 12h2.6M19.4 12H22M4.9 19.1l1.8-1.8M17.3 6.7l1.8-1.8"/></svg>';function sync(){var d=document.documentElement.classList.contains('dark');b.innerHTML=d?SUN:MOON;}b.addEventListener('click',function(){document.documentElement.classList.toggle('dark');try{localStorage.setItem('ghl_theme',document.documentElement.classList.contains('dark')?'dark':'light')}catch(e){}sync();});sync();})();
(function(){var LG=(window.__GHL_LEGACY__||{});var read=[];try{read=JSON.parse(localStorage.getItem('ghl_read')||'[]')}catch(e){}
/* 已读态一次性迁移（10-14）：旧 sec-NN → ghl；无法映射即丢弃（可接受损失） */
var mig=[],chg=false;for(var mi=0;mi<read.length;mi++){var mv=read[mi];var nv=/^ghl-[0-9]+$/.test(mv)?mv:(LG[mv]||null);if(nv){mig.push(nv);}if(nv!==mv){chg=true;}}
if(chg){read=mig;try{localStorage.setItem('ghl_read',JSON.stringify(read))}catch(e){}}
var cur=null;
document.querySelectorAll('.toc a[href^="#ghl-"]').forEach(function(a){
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
  s.addEventListener('click',function(){var e=s.parentElement;if(e&&e.id){cur=e.id;window.ghlTrack('entry_open',{id:e.id});}});
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
var SCROLL_KEY='ghl_scroll_'+(window.__GHL_PAGE__||'index.html');
var saved=0;try{saved=parseInt(localStorage.getItem(SCROLL_KEY)||'0',10)}catch(e){}
if(saved>0&&!location.hash){window.scrollTo(0,saved)}
var t;document.addEventListener('scroll',function(){clearTimeout(t);t=setTimeout(function(){try{localStorage.setItem(SCROLL_KEY,String(window.scrollY))}catch(e){}},400);findCur();updateNav();},{passive:true});
})();
/* 跨页锚点（10-19 分页）：旧 #sec-NN / #ghl 若不在本页，按 id→page 表重定向（保留原 hash） */
(function(){var h=(location.hash||'').slice(1);if(!h)return;if(document.getElementById(h))return;var LG=(window.__GHL_LEGACY__||{});var t=/^sec-[0-9]+$/.test(h)?LG[h]:h;if(!t||!/^ghl-[0-9]+$/.test(t))return;var pg=(window.__GHL_IDPAGE__||{})[t];if(pg&&pg!==(window.__GHL_PAGE__||''))location.replace(pg+'#'+h);})();
/* 旧 #sec-NN / 新 #ghl 直链（10-14）：载入时展开命中条目（原生锚点负责滚动，这里补展开） */
(function(){var LG=(window.__GHL_LEGACY__||{});var h=(location.hash||'').slice(1);if(!h)return;var t=/^sec-[0-9]+$/.test(h)?LG[h]:h;if(!t||!/^ghl-[0-9]+$/.test(t))return;var d=document.getElementById(t);if(d){d.open=true;}})();
(function(){var d=document.querySelector('details.tocm');if(d){var wide=null;function sync(){var now=window.innerWidth>960;if(now!==wide){d.open=now;wide=now;}}sync();window.addEventListener('resize',sync);}})();
(function(){var p=document.querySelector('.intro p');if(p&&p.firstChild&&p.firstChild.nodeType===3){p.firstChild.textContent=p.firstChild.textContent.replace('💜 ','');}})();
/* ---- 全文检索 v2（10-17 施工窗 2）：简繁归一 + 多字段排序 + 问题入口引导 ---- */
(function(){var box=document.getElementById('q'),res=document.getElementById('qres');if(!box||!res)return;var idx=null;var p=null;var restP=null;
function fetchJson(u){return fetch(u).then(function(r){if(!r.ok)throw 0;return r.json();}).catch(function(){return null;});}
function shardForPage(){
 var pg=window.__GHL_PAGE__||'index.html';
 if(pg==='2025.html')return 'search_index_2025.json';
 if(pg==='2024.html')return 'search_index_2024.json';
 if(pg==='undated.html')return 'search_index_undated.json';
 return 'search_index_2026.json';
}
function mergeEntries(list){
 if(!idx)return;
 if(!idx._map)idx._map={};
 for(var i=0;i<list.length;i++){var e=list[i];if(!e||!e.id||idx._map[e.id])continue;idx._map[e.id]=1;idx.entries.push(e);}
 idx.count=idx.entries.length;
}
function getIdx(){
 if(p)return p;
 if(window.__GHL_INDEX__){p=Promise.resolve(window.__GHL_INDEX__);return p;}
 var ss=window.__GHL_SHARDS__||[];
 var cur=shardForPage();
 var order=[cur];
 for(var i=0;i<ss.length;i++){if(ss[i]!==cur)order.push(ss[i]);}
 p=Promise.all([fetchJson('search_shared.json'),fetchJson(cur)]).then(function(a){
  var sh=a[0]||{};
  idx={generated:sh.generated||'',count:0,guide:sh.guide||[],t2s:sh.t2s||'',entries:[],_map:{},_rest:order.slice(1)};
  if(a[1]&&a[1].entries)mergeEntries(a[1].entries);
  if(!idx.entries.length&&order.length)throw 0;
  return idx;
 }).catch(function(){return {entries:[],count:0,err:1};});
 return p;
}
function loadRest(){
 if(restP)return restP;
 if(!idx||!idx._rest||!idx._rest.length)return Promise.resolve(idx);
 restP=Promise.all(idx._rest.map(fetchJson)).then(function(list){
  for(var i=0;i<list.length;i++){if(list[i]&&list[i].entries)mergeEntries(list[i].entries);}
  idx._rest=[];
  return idx;
 });
 return restP;
}
function esc(s){return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');}
var _t2s=null;
function norm(s){if(!_t2s){_t2s={};var pr=(idx&&idx.t2s)||'';for(var i=0;i<pr.length;i+=2)_t2s[pr[i]]=pr[i+1];}var o='';for(var j=0;j<s.length;j++){o+=(_t2s[s[j]]||s[j]);}return o;}
function cnt(h,n){var c=0,i=0;if(!n)return 0;for(;;){i=h.indexOf(n,i);if(i<0)return c;c++;i+=n.length;}}
function has4(a,b){if(a.length<4||b.length<4)return false;for(var i=0;i+4<=a.length;i++){if(b.indexOf(a.slice(i,i+4))>-1)return true;}return false;}
function thit(qs,s){if(!s||s.length<2||qs.length<2)return false;if(s.indexOf(qs)>-1)return true;if(qs.indexOf(s)>-1)return true;return has4(qs,s);}
function hl(orig,nq,lw){var i=nq.indexOf(lw);if(i<0)return esc(orig);return esc(orig.slice(0,i))+'<mark>'+esc(orig.slice(i,i+lw.length))+'</mark>'+esc(orig.slice(i+lw.length));}
function snipH(orig,nq,lw){var i=nq.indexOf(lw);var s=i<0?0:Math.max(0,i-15);var e0=Math.min(orig.length,s+60);var frag;if(i>=0&&i<e0){var i2=i-s;var mEnd=Math.min(i2+lw.length,e0-s);frag=esc(orig.slice(s,s+i2))+'<mark>'+esc(orig.slice(s+i2,s+mEnd))+'</mark>'+esc(orig.slice(s+mEnd,e0));}else{frag=esc(orig.slice(s,e0));}return (s>0?'…':'')+frag+(e0<orig.length?'…':'');}
function prep(){if(!idx)return;var es=idx.entries||[];for(var i=0;i<es.length;i++){var e=es[i];if(e._warmed)continue;var bt=String(e.title||''),bx=String(e.text||'');
if(e.titleN)bt=e.titleN;else if(e.titleP){var at=bt.split('');for(var p=0;p<e.titleP.length;p++){at[e.titleP[p][0]]=e.titleP[p][1];}bt=at.join('');}
if(e.textN)bx=e.textN;else if(e.textP){var ax=bx.split('');for(var q=0;q<e.textP.length;q++){ax[e.textP[q][0]]=e.textP[q][1];}bx=ax.join('');}
e._tl=bt.toLowerCase();e._xl=bx.toLowerCase();e._warmed=1;}}
function renderNow(q,pending){
 if(idx&&idx.err){res.innerHTML='<div class="qnone">检索数据加载失败，刷新页面重试</div>';res.classList.add('on');return;}
 prep();var es=(idx&&idx.entries)||[];var qs=norm(q).toLowerCase();if(!qs)return;
 var i,k,out=[],byId={};
 for(i=0;i<es.length;i++){var e=es[i];byId[e.id]=e;e._s=0;e._bg=null;
  if(e._tl.indexOf(qs)>-1)e._s+=120;
  var c=cnt(e._xl,qs);if(c)e._s+=Math.min(c,12)*4;
  if(e.aliases){for(k=0;k<e.aliases.length;k++){if(thit(qs,String(e.aliases[k]).toLowerCase()))e._s+=180;}}
 }
 var gh=(idx&&idx.guide)||[];
 for(i=0;i<gh.length;i++){var g=gh[i],hitg=false;
  for(k=0;k<g.questions.length;k++){if(thit(qs,norm(g.questions[k]).toLowerCase())){hitg=true;break;}}
  if(hitg){for(k=0;k<g.reads.length;k++){var re=byId[g.reads[k].id];if(re)re._s+=(k===0?90:45);}}
 }
 var soft=false;
 for(i=0;i<es.length;i++){if(es[i]._s>0){es[i]._i=i;out.push(es[i]);}}
 if(!out.length&&qs.length>=3){
  var bgs=[],seen={};
  for(i=0;i+2<=qs.length;i++){var bg=qs.slice(i,i+2);if(!/^[一-鿿]{2}$/.test(bg))continue;if(!seen[bg]){seen[bg]=1;bgs.push(bg);}}
  if(bgs.length>=2){for(i=0;i<es.length;i++){var e2=es[i],hn=0,sc=0,bb=null,bc=0;
    for(k=0;k<bgs.length;k++){var c4=cnt(e2._tl,bgs[k])*3+cnt(e2._xl,bgs[k]);if(c4>0){hn++;sc+=Math.min(c4,6);if(c4>bc){bc=c4;bb=bgs[k];}}}
    if(hn>=2){e2._s=sc;e2._bg=bb;e2._i=i;out.push(e2);soft=true;}}}
 }
 if(!out.length){
  if(pending){res.innerHTML='<div class="qnone">正在加载全部年份…</div>';res.classList.add('on');return;}
  var gg='';if(gh.length){gg='<div class="qguide"><div class="qgt">也可以从这里出发：</div>';for(i=0;i<gh.length;i++){gg+='<div class="qgr" data-goto="firsttime">'+esc(gh[i].title)+'</div>';}gg+='</div>';}
  var fb='<div class="qfeedback"><a href="feedback.html?type=search&q='+encodeURIComponent(q)+'">没找到？告诉我们你想找什么</a></div>';
  window.ghlTrack('search_zero',{q:q});
  res.innerHTML='<div class="qnone">没有找到与「'+esc(q)+'」相关的内容</div>'+gg+fb;res.classList.add('on');return;
 }
 out.sort(function(a,b){return (b._s-a._s)||(a._i-b._i);});
 var h='';
 if(pending)h+='<div class="qnote">正在加载全部年份…</div>';
 if(soft)h+='<div class="qnote">没有与「'+esc(q)+'」完全匹配的内容，以下按关键词近似检索：</div>';
 h+='<div class="qcount">'+out.length+' 条结果'+(soft?'（近似）':'')+'</div>';
 for(i=0;i<out.length;i++){var e3=out[i];var lw=(soft&&e3._bg)?e3._bg:qs;
  h+='<div class="qitem" data-id="'+e3.id+'" data-page="'+esc(e3.page||'')+'"><div class="qhead"><span class="qt">'+hl(String(e3.title||''),e3._tl,lw)+'</span><span class="qd">'+esc(e3.date||'')+'</span></div><div class="qs">'+snipH(String(e3.text||''),e3._xl,lw)+'</div></div>';
 }
 res.innerHTML=h;res.classList.add('on');
}
function render(q){q=q.trim();if(!q){res.classList.remove('on');res.innerHTML='';return;}
 var myq=q;
 getIdx().then(function(j){if(j)idx=j;
  if(idx&&idx.err){renderNow(myq,false);return;}
  var pending=!!(idx&&idx._rest&&idx._rest.length);
  renderNow(myq,pending);
  if(pending){loadRest().then(function(){if(box.value.trim()===myq)renderNow(myq,false);});}
 });
}
box.addEventListener('input',function(){render(box.value)});
box.addEventListener('focus',function(){if(box.value.trim())render(box.value)});
res.addEventListener('click',function(ev){var n=ev.target;
while(n&&n!==res&&!(n.classList&&(n.classList.contains('qitem')||n.classList.contains('qgr'))))n=n.parentNode;
if(!n||n===res)return;
if(n.classList.contains('qgr')){res.classList.remove('on');var ft=document.getElementById('firsttime');if(ft){ft.scrollIntoView({behavior:'smooth',block:'start'});}else{location.href='index.html#firsttime';}return;}
var id=n.getAttribute('data-id');var pg=n.getAttribute('data-page')||'';res.classList.remove('on');var el=document.getElementById(id);
if(!el&&pg&&pg!==(window.__GHL_PAGE__||'')){location.href=pg+'#'+id;return;}
var a=document.querySelector('.toc a[href="#'+id+'"]');if(a)a.click();if(el){setTimeout(function(){el.scrollIntoView({behavior:'smooth',block:'start'});},60);}});
document.addEventListener('click',function(ev){var n=ev.target;while(n){if(n.classList&&n.classList.contains('searchbar'))return;n=n.parentNode;}res.classList.remove('on');});
document.querySelectorAll('.ft-chip').forEach(function(b){b.addEventListener('click',function(){box.value=b.getAttribute('data-q');render(box.value);box.scrollIntoView({behavior:'smooth',block:'center'});try{box.focus({preventScroll:true})}catch(e){}});});
})();
/* 「第一次来」区文章链接（10-17 施工窗 2）：点击时展开对应条目（原生锚点负责滚动） */
(function(){document.querySelectorAll('.firsttime a[href^="#ghl-"]').forEach(function(a){a.addEventListener('click',function(){var d=document.getElementById(a.getAttribute('href').slice(1));if(d)d.open=true;});});})();
/* 10-22 P0：移动端浮动按钮滚动后才出现，避免遮挡卡片摘要 */
(function(){var ns=document.querySelector('.navstack');if(!ns)return;function v(){ns.classList.toggle('show',window.scrollY>600);}window.addEventListener('scroll',v,{passive:true});v();})();
