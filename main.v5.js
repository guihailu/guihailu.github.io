
// Load a platform player only after an explicit click; keep outbound fallbacks visible.
document.querySelectorAll('.video-play').forEach(function(button){
 button.addEventListener('click',function(){
  var id=button.getAttribute('data-video-id');
  if(!/^[A-Za-z0-9_-]{11}$/.test(id))return;
  var frame=document.createElement('iframe');
  frame.src='https://www.youtube.com/embed/'+id+'?autoplay=1&playsinline=1';
  frame.title=button.getAttribute('aria-label');
  frame.allow='autoplay; encrypted-media; picture-in-picture; fullscreen';
  frame.allowFullscreen=true;
  frame.referrerPolicy='strict-origin-when-cross-origin';
  button.parentElement.classList.add('is-playing');
  button.replaceWith(frame);
  frame.focus();
 });
});

// Play the full source in the same card, with an explicit return to the clip.
document.querySelectorAll('.source-video-play').forEach(function(link){
 link.addEventListener('click',function(event){
  var source=new URL(link.href), id=source.searchParams.get('v');
  if(!/^(www\.)?youtube\.com$/.test(source.hostname)||!/^[A-Za-z0-9_-]{11}$/.test(id))return;
  event.preventDefault();
  var stage=link.closest('.video-card').querySelector('.video-stage');
  var full=link.dataset.mode!=='full';
  var frame=document.createElement('iframe');
  frame.src='https://www.youtube.com/embed/'+(full?id:link.dataset.clipVideo)+'?autoplay=1&playsinline=1';
  frame.title=full?'完整视频':'视频片段';
  frame.allow='autoplay; encrypted-media; picture-in-picture; fullscreen';
  frame.allowFullscreen=true;
  frame.referrerPolicy='strict-origin-when-cross-origin';
  stage.replaceChildren(frame);
  stage.classList.add('is-playing');
  stage.style.aspectRatio=full?'16 / 9':'9 / 16';
  link.dataset.mode=full?'full':'clip';
  link.textContent=full?'返回片段':'观看完整视频';
  stage.scrollIntoView({block:'nearest'});
  frame.focus();
 });
});

/* 事件钩子（A/B/C）：未接分析服务时静默；接 GoatCounter/Umami/百度/51LA 后自动上报 */
window.ghlTrack=function(name,data){try{
  if(window.goatcounter&&window.goatcounter.count)window.goatcounter.count({path:name,title:name,event:true});
  if(window.umami&&window.umami.track)window.umami.track(name,data||{});
  if(window._hmt)window._hmt.push(['_trackEvent',name,'click',JSON.stringify(data||{})]);
}catch(e){}};
(function(){var p=document.getElementById('progress');function upd(){var h=document.documentElement;var d=h.scrollHeight-h.clientHeight;p.style.width=(d>0?(h.scrollTop/d)*100:0)+'%';}document.addEventListener('scroll',upd,{passive:true});upd();})();
(function(){var b=document.getElementById('toggle');if(!b)return;var MOON='<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>';var SUN='<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="4.2"/><path d="M12 2v2.6M12 19.4V22M4.9 4.9l1.8 1.8M17.3 17.3l1.8 1.8M2 12h2.6M19.4 12H22M4.9 19.1l1.8-1.8M17.3 6.7l1.8-1.8"/></svg>';var SEPIA='<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="10" r="4.2"/><path d="M4 17h16M7 20.5h10"/></svg>';var ORDER=['light','dark','sepia'];function cur(){var c=document.documentElement.classList;return c.contains('dark')?'dark':(c.contains('sepia')?'sepia':'light')}function apply(t){var c=document.documentElement.classList;c.remove('dark','sepia');if(t!=='light')c.add(t);try{localStorage.setItem('ghl_theme',t)}catch(e){}}function sync(){var nx=ORDER[(ORDER.indexOf(cur())+1)%3];b.innerHTML=nx==='dark'?MOON:(nx==='sepia'?SEPIA:SUN);b.setAttribute('aria-label',nx==='dark'?'切换晚上模式':(nx==='sepia'?'切换米色模式':'切换白天模式'))}try{var st=localStorage.getItem('ghl_theme');if(st==='dark'||st==='sepia')apply(st)}catch(e){}b.addEventListener('click',function(){apply(ORDER[(ORDER.indexOf(cur())+1)%3]);sync()});sync();})();
var GHL_READIDS=["ghl-000001", "ghl-000002", "ghl-000003", "ghl-000004", "ghl-000005", "ghl-000006", "ghl-000007", "ghl-000008", "ghl-000009", "ghl-000010", "ghl-000011", "ghl-000012", "ghl-000013", "ghl-000014", "ghl-000015", "ghl-000016", "ghl-000017", "ghl-000018", "ghl-000019", "ghl-000020", "ghl-000021", "ghl-000022", "ghl-000023", "ghl-000024", "ghl-000025", "ghl-000026", "ghl-000027", "ghl-000028", "ghl-000029", "ghl-000030", "ghl-000031", "ghl-000032", "ghl-000033", "ghl-000034", "ghl-000035", "ghl-000036", "ghl-000037", "ghl-000038", "ghl-000039", "ghl-000040", "ghl-000041", "ghl-000042", "ghl-000043", "ghl-000044", "ghl-000045", "ghl-000046", "ghl-000047", "ghl-000048", "ghl-000049", "ghl-000050", "ghl-000051", "ghl-000052", "ghl-000053", "ghl-000054", "ghl-000055", "ghl-000056", "ghl-000057", "ghl-000058", "ghl-000059", "ghl-000060", "ghl-000061", "ghl-000062", "ghl-000063", "ghl-000064", "ghl-000065", "ghl-000066", "ghl-000067", "ghl-000068", "ghl-000069", "ghl-000070", "ghl-000071", "ghl-000072", "ghl-000073", "ghl-000074", "ghl-000075", "ghl-000076", "ghl-000077", "ghl-000078", "ghl-000079", "ghl-000080", "ghl-000081", "ghl-000082", "ghl-000083", "ghl-000084", "ghl-000085", "ghl-000086", "ghl-000087", "ghl-000088", "ghl-000089", "ghl-000090", "ghl-000091", "ghl-000092", "ghl-000093", "ghl-000094", "ghl-000095", "ghl-000096", "ghl-000097", "ghl-000098", "ghl-000099", "ghl-000100", "ghl-000101", "ghl-000102", "ghl-000103", "ghl-000104", "ghl-000105", "ghl-000106", "ghl-000107", "ghl-000108", "ghl-000109", "ghl-000110", "ghl-000111", "ghl-000112", "ghl-000113", "ghl-000114", "ghl-000115", "ghl-000116", "ghl-000117", "ghl-000118", "ghl-000119", "ghl-000120", "ghl-000121", "ghl-000122", "ghl-000123"];
(function(){var LG=(window.__GHL_LEGACY__||{});var read=[];try{read=JSON.parse(localStorage.getItem('ghl_read')||'[]')}catch(e){}
/* 已读态一次性迁移（10-14）：旧 sec-NN → ghl；无法映射即丢弃（可接受损失） */
var mig=[],chg=false;for(var mi=0;mi<read.length;mi++){var mv=read[mi];var nv=/^ghl-[0-9]+$/.test(mv)?mv:(LG[mv]||null);if(nv){mig.push(nv);}if(nv!==mv){chg=true;}}
if(chg){read=mig;try{localStorage.setItem('ghl_read',JSON.stringify(read))}catch(e){}}
/* p37 全站已读进度：页眉角标显示已读总数（与阅读线同键 ghl_read；只计库内编号） */
function refreshProgress(){var c=document.getElementById('read-chip');if(!c)return;var n=0;read.forEach(function(id){if(GHL_READIDS.indexOf(id)>-1)n++});c.textContent='已读 '+n+'/'+GHL_READIDS.length;}
window.__ghlRefreshProgress=refreshProgress;
window.addEventListener('storage',function(e){if(e.key==='ghl_read'){try{read=JSON.parse(e.newValue||'[]')}catch(err){read=[]}refreshProgress();}});
refreshProgress();
document.addEventListener('click',function(){setTimeout(refreshProgress,0);});
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
/* p18 接着读：同页推荐点开即展开目标条目（与目录链接同行为）；跨页链接本页无目标、放行导航，由目标页加载时展开 */
document.querySelectorAll('.next-read a[href*="#ghl-"]').forEach(function(a){
  a.addEventListener('click',function(){
    var id=a.getAttribute('href').split('#')[1];
    var d=id&&document.getElementById(id);
    if(d){d.open=true;if(read.indexOf(id)<0){read.push(id);try{localStorage.setItem('ghl_read',JSON.stringify(read))}catch(e){}}}
  });
});
/* p32 入门先读：路线下一篇链点击即记目标已读（同键同格式；与接着读不同：跨页目标本页无 details 也照记，否则跨页步骤永不打勾）；同页目标同时展开；本篇已读则行内打勾 */
document.querySelectorAll('.route-next a[href*="#ghl-"]').forEach(function(a){
  a.addEventListener('click',function(){
    var id=a.getAttribute('href').split('#')[1];
    if(!id||!/^ghl-[0-9]+$/.test(id))return;
    if(read.indexOf(id)<0){read.push(id);try{localStorage.setItem('ghl_read',JSON.stringify(read))}catch(e){}}
    var d=document.getElementById(id);
    if(d){d.open=true;}
  });
});
document.querySelectorAll('.route-next').forEach(function(r){
  var e=r.closest?r.closest('.entry'):null;
  if(e&&e.id&&read.indexOf(e.id)>-1)r.classList.add('done');
});
/* p19 年份页月份定位：点月份跳到该月首篇并展开（与目录链接同行为；只定位，不记已读） */
document.querySelectorAll('.month-nav a[href^="#ghl-"]').forEach(function(a){
  a.addEventListener('click',function(){
    var d=document.getElementById(a.getAttribute('href').slice(1));
    if(d){d.open=true;}
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
(function(){var LG=(window.__GHL_LEGACY__||{});var h=(location.hash||'').slice(1);if(!h)return;var t=/^sec-[0-9]+$/.test(h)?LG[h]:h;if(!t)return;var base=t.replace(/-video$/,'');if(!/^ghl-[0-9]+$/.test(base))return;var d=document.getElementById(base);if(d){d.open=true;if(h!==base){var v=document.getElementById(h);if(v)setTimeout(function(){v.scrollIntoView({block:'center'})},80)}}})();
(function(){var d=document.querySelector('details.tocm');if(d){var wide=null;function sync(){var now=window.innerWidth>960;if(now!==wide){d.open=now;wide=now;}}sync();window.addEventListener('resize',sync);}})();
(function(){var p=document.querySelector('.intro p');if(p&&p.firstChild&&p.firstChild.nodeType===3){p.firstChild.textContent=p.firstChild.textContent.replace('💜 ','');}})();
/* ---- 全文检索 v2（10-17 施工窗 2）：简繁归一 + 多字段排序 + 问题入口引导 ---- */
(function(){var box=document.getElementById('q'),res=document.getElementById('qres');if(!box||!res)return;var idx=null;var p=null;var restP=null;var active=-1;
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
 active=-1;
 if(idx&&idx.err){res.innerHTML='<div class="qnone">检索数据加载失败，刷新页面重试</div>';res.classList.add('on');box.setAttribute('aria-expanded','true');return;}
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
  if(pending){res.innerHTML='<div class="qnone">正在加载全部年份…</div>';res.classList.add('on');box.setAttribute('aria-expanded','true');return;}
  var gg=(function(){
   var HOTW=['修行','因果','福报','轮回','孩子','菩萨','鬼','投胎','灵魂','事业','父母','健康','去世','财运','婚姻','天眼','超度','阴债','烧纸','风水','祖先','冤亲','改命','做梦'];
   function hit(w){for(var i=0;i<es.length;i++){var e=es[i];if(e._tl.indexOf(w)>-1)return true;if(cnt(e._xl,w)>0)return true;}return false;}
   var sim=[],i,j,n;
   for(i=0;i<HOTW.length;i++){var w=HOTW[i];if(w===qs)continue;n=0;for(j=0;j<w.length;j++){if(qs.indexOf(w[j])>-1)n++;}if(n>0&&hit(w))sim.push([n,w]);}
   sim.sort(function(a,b){return b[0]-a[0];});
   var simW=sim.slice(0,4).map(function(x){return x[1];});
   var hot=[];for(i=0;i<HOTW.length&&hot.length<6;i++){if(simW.indexOf(HOTW[i])<0&&HOTW[i]!==qs&&hit(HOTW[i]))hot.push(HOTW[i]);}
   for(i=0;i<HOTW.length&&hot.length<6;i++){if(simW.indexOf(HOTW[i])<0&&HOTW[i]!==qs&&hot.indexOf(HOTW[i])<0)hot.push(HOTW[i]);}
   function chips(ws){return ws.map(function(w){return '<button type="button" class="qchip" data-q="'+w+'">'+w+'</button>';}).join('');}
   var h='';
   if(simW.length)h+='<span class="qsugg-lab">相近的词，点一下就搜：</span>'+chips(simW);
   if(hot.length)h+='<span class="qsugg-lab">大家常搜：</span>'+chips(hot);
   h+='<span class="qsugg-link">不知道搜什么？<a href="topics.html">按问题找 →</a></span>';
   return '<div class="qsugg">'+h+'</div>';
  })();
  var fb='<div class="qfeedback"><a href="feedback.html?type=search&q='+encodeURIComponent(q)+'">没找到？告诉我们你想找什么</a></div>';
  window.ghlTrack('search_zero',{q:q});
  res.innerHTML='<div class="qnone">没有找到与「'+esc(q)+'」相关的内容</div>'+gg+fb;res.classList.add('on');box.setAttribute('aria-expanded','true');return;
 }
 out.sort(function(a,b){return (b._s-a._s)||(a._i-b._i);});
 var h='';
 if(pending)h+='<div class="qnote">正在加载全部年份…</div>';
 if(soft)h+='<div class="qnote">没有与「'+esc(q)+'」完全匹配的内容，以下按关键词近似检索：</div>';
 h+='<div class="qcount">'+out.length+' 条结果'+(soft?'（近似）':'')+'</div>';
 for(i=0;i<out.length;i++){var e3=out[i];var lw=(soft&&e3._bg)?e3._bg:qs;
  h+='<div class="qitem" role="option" tabindex="-1" aria-selected="false" data-id="'+e3.id+'" data-page="'+esc(e3.page||'')+'"><div class="qhead"><span class="qt">'+hl(String(e3.title||''),e3._tl,lw)+'</span><span class="qd">'+esc(e3.date||'')+'</span></div><div class="qs">'+snipH(String(e3.text||''),e3._xl,lw)+'</div></div>';
 }
 res.innerHTML=h;res.classList.add('on');box.setAttribute('aria-expanded','true');
}
function render(q){q=q.trim();if(!q){res.classList.remove('on');res.innerHTML='';box.setAttribute('aria-expanded','false');return;}
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
box.addEventListener('keydown',function(e){
 var a=[].slice.call(res.querySelectorAll('.qitem'));
 if(e.key==='ArrowDown'){if(!a.length)return;e.preventDefault();active=active+1>=a.length?0:active+1;}
 else if(e.key==='ArrowUp'){if(!a.length)return;e.preventDefault();active=active-1<0?a.length-1:active-1;}
 else if(e.key==='Enter'){if(active>=0&&a[active]){e.preventDefault();a[active].click();}return;}
 else if(e.key==='Escape'){res.classList.remove('on');box.setAttribute('aria-expanded','false');active=-1;return;}
 else{return;}
 a.forEach(function(el,i){el.classList.toggle('active',i===active);el.setAttribute('aria-selected',i===active?'true':'false');});
 if(a[active])a[active].scrollIntoView({block:'nearest'});
});
res.addEventListener('click',function(ev){var n=ev.target;
while(n&&n!==res&&!(n.classList&&(n.classList.contains('qitem')||n.classList.contains('qgr'))))n=n.parentNode;
if(!n||n===res)return;
if(n.classList.contains('qgr')){res.classList.remove('on');box.setAttribute('aria-expanded','false');var ft=document.getElementById('firsttime');if(ft){ft.scrollIntoView({behavior:'smooth',block:'start'});}else{location.href='index.html#firsttime';}return;}
var id=n.getAttribute('data-id');var pg=n.getAttribute('data-page')||'';res.classList.remove('on');box.setAttribute('aria-expanded','false');var el=document.getElementById(id);
if(!el&&pg&&pg!==(window.__GHL_PAGE__||'')){location.href=pg+'#'+id;return;}
var a=document.querySelector('.toc a[href="#'+id+'"]');if(a)a.click();if(el){setTimeout(function(){el.scrollIntoView({behavior:'smooth',block:'start'});},60);}});
document.addEventListener('click',function(ev){var n=ev.target;while(n){if(n.classList&&n.classList.contains('searchbar'))return;n=n.parentNode;}res.classList.remove('on');box.setAttribute('aria-expanded','false');});
document.querySelectorAll('.ft-chip').forEach(function(b){b.addEventListener('click',function(){box.value=b.getAttribute('data-q');render(box.value);box.scrollIntoView({behavior:'smooth',block:'center'});try{box.focus({preventScroll:true})}catch(e){}});});
})();
/* 「第一次来」区文章链接（10-17 施工窗 2）：点击时展开对应条目（原生锚点负责滚动） */
(function(){document.querySelectorAll('.firsttime a[href^="#ghl-"]').forEach(function(a){a.addEventListener('click',function(){var d=document.getElementById(a.getAttribute('href').slice(1));if(d)d.open=true;});});})();
/* 10-22 P0：移动端浮动按钮滚动后才出现，避免遮挡卡片摘要 */
(function(){var ns=document.querySelector('.navstack');if(!ns)return;function v(){ns.classList.toggle('show',window.scrollY>600);}window.addEventListener('scroll',v,{passive:true});v();})();

(()=>{
const area=document.querySelector('.story-carousel');if(!area)return;
const slides=Array.from(area.children),toggle=document.querySelector('#story-toggle'),next=document.querySelector('#story-next'),position=document.querySelector('#story-position');
for(let i=slides.length-1;i>0;i--){const j=Math.floor(Math.random()*(i+1));[slides[i],slides[j]]=[slides[j],slides[i]];}
let index=0,paused=matchMedia('(prefers-reduced-motion: reduce)').matches;
try{const previous=sessionStorage.getItem('ghl-last-story');if(slides.length>1&&slides[0].querySelector('h3 a').href===previous){slides.push(slides.shift());}}catch(e){}
slides.forEach(s=>area.append(s));
function show(){slides.forEach((s,i)=>{s.hidden=i!==index;});position.textContent=(index+1)+' / '+slides.length;try{sessionStorage.setItem('ghl-last-story',slides[index].querySelector('h3 a').href);}catch(e){}}
function update(){toggle.textContent=paused?'自动轮换':'暂停轮换';toggle.setAttribute('aria-pressed',String(paused));}
next.addEventListener('click',()=>{index=(index+1)%slides.length;show();});toggle.addEventListener('click',()=>{paused=!paused;update();});
setInterval(()=>{if(!paused&&!document.hidden&&!area.matches(':hover')&&!area.contains(document.activeElement)){index=(index+1)%slides.length;show();}},9000);
show();update();
})();

document.querySelectorAll('.intro-toggle').forEach(button=>{
 const intro=button.previousElementSibling;
 function measure(){button.hidden=!intro.classList.contains('is-expanded')&&intro.scrollHeight<=intro.clientHeight+1;}
 button.addEventListener('click',()=>{const expanded=intro.classList.toggle('is-expanded');button.setAttribute('aria-expanded',String(expanded));button.textContent=expanded?'收起':'展开全文';measure();});
 new ResizeObserver(measure).observe(intro);measure();
});

(function(){var b=document.getElementById('fsbtn');if(!b)return;var order=['','l','xl'];function cur(){var c=document.documentElement.classList;return c.contains('fs-xl')?'xl':(c.contains('fs-l')?'l':'');}b.addEventListener('click',function(){var n=order[(order.indexOf(cur())+1)%order.length];document.documentElement.classList.remove('fs-l','fs-xl');if(n)document.documentElement.classList.add('fs-'+n);try{localStorage.setItem('ghl_fs',n)}catch(e){}});})();

(function(){var g=document.querySelector('.fsgrp');if(!g)return;var btns=[].slice.call(g.querySelectorAll('[data-fs]'));function apply(n,save){var c=document.documentElement.classList;c.remove('fs-s','fs-l','fs-xl');if(n)c.add('fs-'+n);btns.forEach(function(b){b.setAttribute('aria-pressed',String(b.getAttribute('data-fs')===n))});if(save){try{localStorage.setItem('ghl_fs',n)}catch(e){}}}var cur='';var cl=document.documentElement.classList;if(cl.contains('fs-s'))cur='s';else if(cl.contains('fs-l')||cl.contains('fs-xl'))cur='l';apply(cur,false);btns.forEach(function(b){b.addEventListener('click',function(){apply(b.getAttribute('data-fs'),true)})});})();

(function(){var b=document.getElementById('printbtn');if(b)b.addEventListener('click',function(){window.print()});})();

window.__GHL_GLOSSARY__={"修行": "日常过日子里改自己、面对真实，不是躲起来空谈。站内说，修行不能脱离对真实世界的了解；连最起码的品德都没有，再谈修行都是空谈。", "天道": "天上运行的那套道理和法则，跟人间的道理不一样。人常把自己揣测的人间道理当成天道法则，一代一代传下去，就会越传越歪。", "因果": "以前做的事，会在后面结出对应的结果，像一张网一样连着，谁也绕不开。站内说，生死不是两端而是闭环，因果就是那张网。", "轮回": "人去世后，灵魂不是就没了，而是要再走一轮：过一道有时限的门，重新投胎做人。同一类日子过久了，还会在里面打转，站内叫它轮回惯性。", "福报": "人以前攒下的福分，体现在日子顺不顺、条件好不好上；福报厚的人顺顺利利、波折少。但认知配不上福报，错误也会拖得更久。", "前世": "这一世之前的某一世。比如一篇里说，一个孩子的病，牵出一段前世的事；前世做过的事，会连到今生来。", "法界": "看不见的那一界；那一边也有自己的规矩和账本。不过站内也提醒，不是所有的头疼、失眠、情绪低落，都是法界攻击。", "功德": "日常行善、帮人一点点攒下的好，会记下来。站内还讨论过，它能不能转送给别人。", "投胎": "人去世后，灵魂重新进一个新身体、再做一世人。站内说，这要过一道门，还要付成本；走错了，会投错地方。", "仙家": "另一界的同行者，常被问到怎么跟它沟通、怎么感恩。站内说，仙家是同行者，不是工具。"};

(function(){
var G=window.__GHL_GLOSSARY__||{};
if(!Object.keys(G).length)return;
var card=null,cur=null,openedAt=0;
function close(){if(card)card.hidden=true;if(cur){cur.setAttribute('aria-expanded','false');cur=null;}}
function open(btn){
var t=btn.getAttribute('data-term');
if(!t||!G[t])return;
if(!card){
card=document.createElement('div');
card.id='gcard';card.className='gcard';card.setAttribute('role','dialog');card.hidden=true;
card.innerHTML='<div class="gcard-t"><span class="gcard-term"></span><button type="button" class="gcard-x" aria-label="关闭释义">×</button></div><p class="gcard-d"></p>';
document.body.appendChild(card);
card.querySelector('.gcard-x').addEventListener('click',function(e){e.stopPropagation();close();});
card.addEventListener('click',function(e){e.stopPropagation();});
}
if(cur===btn&&!card.hidden){close();return;}
if(cur)cur.setAttribute('aria-expanded','false');
cur=btn;btn.setAttribute('aria-expanded','true');
card.querySelector('.gcard-term').textContent=t;
card.querySelector('.gcard-d').textContent=G[t];
card.hidden=false;
openedAt=Date.now();
var r=btn.getBoundingClientRect();
var cw=card.offsetWidth,ch=card.offsetHeight;
var vw=window.innerWidth,vh=window.innerHeight;
var left=Math.max(8,Math.min(r.left,vw-cw-8));
var top=(r.bottom+8+ch<=vh)?r.bottom+8:Math.max(8,r.top-ch-8);
card.style.left=left+'px';card.style.top=top+'px';
}
document.addEventListener('click',function(e){
var b=e.target&&e.target.closest?e.target.closest('.gterm'):null;
if(b){open(b);return;}
if(card&&!card.hidden)close();
});
document.addEventListener('keydown',function(e){
if(e.key==='Escape'){close();return;}
var b=e.target&&e.target.closest?e.target.closest('.gterm'):null;
if(b&&(e.key==='Enter'||e.key===' ')){e.preventDefault();open(b);}
});
window.addEventListener('scroll',function(){if(card&&!card.hidden&&Date.now()-openedAt>500)close();},true);
window.addEventListener('resize',function(){if(card&&!card.hidden)close();});
})();

(function(){document.addEventListener('click',function(e){var b=e.target.closest?e.target.closest('[data-ev]'):null;if(b){var f=document.createElement('iframe');f.src='https://www.youtube.com/embed/'+b.getAttribute('data-ev')+'?autoplay=1&playsinline=1';f.title='视频';f.allow='autoplay; encrypted-media; fullscreen; picture-in-picture';f.allowFullscreen=true;f.referrerPolicy='strict-origin-when-cross-origin';b.replaceWith(f);return}var c=e.target.closest?e.target.closest('.qchip'):null;if(c){var q=document.getElementById('q');if(q){q.value=c.getAttribute('data-q');q.dispatchEvent(new Event('input',{bubbles:true}));q.focus()}}});})();

(function(){document.addEventListener('click',function(e){var b=e.target.closest?e.target.closest('[data-share]'):null;if(!b)return;var d=b.closest('details.entry');var sid=d?d.id:'';var url=location.href.split('#')[0]+(sid?'#'+sid:'');var title=b.getAttribute('data-title')||document.title;var done=function(){var t=b.textContent;b.textContent='已复制';setTimeout(function(){b.textContent=t;},1500);};if(navigator.share){navigator.share({title:title,text:title,url:url}).catch(function(){});return;}function fb(){try{var ta=document.createElement('textarea');ta.value=url;ta.style.position='fixed';ta.style.opacity='0';document.body.appendChild(ta);ta.select();document.execCommand('copy');ta.remove();done();}catch(err){}}if(navigator.clipboard&&navigator.clipboard.writeText){navigator.clipboard.writeText(url).then(done,fb);}else{fb();}});})();

(function(){var POOL=['修行','因果','福报','轮回','孩子','菩萨','鬼','投胎','灵魂','事业','父母','健康','去世','财运','婚姻','天眼','超度','阴债','烧纸','风水','祖先','冤亲','改命','做梦'];var chips=[].slice.call(document.querySelectorAll('.search-hint .qchip'));if(!chips.length)return;function pick(){var p=POOL.slice();for(var i=p.length-1;i>0;i--){var j=Math.floor(Math.random()*(i+1));var t=p[i];p[i]=p[j];p[j]=t}return p}function apply(){var w=pick();chips.forEach(function(c,i){var v=w[i%w.length];c.textContent=v;c.setAttribute('data-q',v);c.style.opacity=''})}apply();setInterval(function(){var q=document.getElementById('q');if(q&&q.value.trim())return;chips.forEach(function(c){c.style.opacity='0'});setTimeout(apply,480)},12000)})();
