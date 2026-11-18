const cases=[{"id": "case-01", "title": "赈济灾民的王爷", "intro": "遇到旱灾，国库又拿不出足够的钱。一位年轻王爷决定挨家募捐，让救济真正落到灾民身上。", "paragraphs": ["原案例讲述，一位出身王府的年轻人，从小心地善良，学习各种技艺也很快。长大后，他继承了父亲的王位。", "有一年发生旱灾，粮食歉收，许多百姓流离失所。当时国库空虚，能够用于赈灾的银子有限。皇帝鼓励大臣捐款，但一些富有的官员担心财产来路暴露，募款收效很小。", "他不忍看灾民挨饿，主动请求到各个大臣府中募捐，并得到皇帝授予的权力。之后，他设法让官员和富商匿名捐助，帮助灾民渡过难关。", "原答复将这一段经历与受询者今生的福报联系起来，并称没有特别的使命或任务。"]}, {"id": "case-02", "title": "把饭馆当成自己家", "intro": "他从饭馆伙计做到了管事，凡事认真、处处操心。老板很欣赏他，同事却并不喜欢他的管理方式。", "paragraphs": ["原案例讲述，一个在饭馆打工的人，凭着勤快当上了管事，负责收钱和照看店里的工作人员。", "他看店就像看自己家一样，盯着所有人，不让他们偷懒。这让老板很喜欢他，却也让员工对他不满。他并不在意，只想多挣些钱。", "原答复把聪明、勤奋、爱操心和责任心视为延续下来的特点，也提到照顾家人的长处。与此同时，答复指出，与家人相处时过于强势、爱挑毛病，是需要改善的地方；没有特别的任务。"]}, {"id": "case-03", "title": "把零用钱攒给受灾的人", "intro": "一位家境优裕的少年，没有拿身份胡作非为。他把零用钱存起来，听说哪里受灾，就买物资赶去帮助。", "paragraphs": ["原案例讲述，一位出身富裕家庭的少年，并没有借着身份胡作非为，而是把平时的零用钱存了起来。", "听说哪里受灾，他就用积攒的钱购买物资，尽快去帮助受灾的人。", "原答复将善良、真诚、厚道和值得信赖，视为这段经历留下的特点，并描述受询者的事业与家庭较稳定，没有特别的任务。答复同时提醒，思想散漫、做事不积极和懒惰，需要调整。"]}, {"id": "case-04", "title": "经营生意，也延续善意", "intro": "接手家族生意之后，他既把生意经营好，也继续做长辈做过的慈善。原案例随后谈到领导能力与性格中的棱角。", "paragraphs": ["原案例讲述，一位家族显赫的富家少爷，一生把家族生意经营得很好，也继承了长辈的善意，默默做慈善。", "原答复把对生活品位的追求、较高的认知，以及领导和组织能力，视为延续下来的特点和天赋，并称没有特别的任务。", "答复也指出，性格太耿直、容易发脾气和倔强，是需要留意和改善的地方。"]}, {"id": "case-05", "title": "一笔本钱，开出一条新商路", "intro": "父亲拿出一笔钱考验几个儿子。最小的儿子没有只守着旧生意，而是利用此前建立的联系，把丝绸卖向草原。", "paragraphs": ["原案例讲述，一位做布匹买卖的富商，家中最小的儿子从小聪明伶俐。随着父亲年纪渐长，他想锻炼孩子，便给了一笔钱。", "这个儿子拿到钱后，请管家帮助购进一批上等丝绸。此前几年，他已与北方一个部落建立联系，对方能够保障货物在草原运输的安全。如今有了本钱，他终于能够把想法付诸行动。", "几个月后，父亲召集几个儿子，宣布由他接班。面对其他人的惊讶和不服，父亲解释：他不仅拿本钱做成了买卖、获得盈利，更重要的是开辟了一条新的赚钱渠道。", "原答复将做事有方法、有手段视为这段经历留下的天赋，并称没有特别的任务。"]}, {"id": "case-06", "title": "爱护动物，也要面对自己的脾气", "intro": "她常买下小动物放归自然，却会因别人吃动物而发火，甚至让人动手。故事里的善意，与急躁同时存在。", "paragraphs": ["原案例讲述，一位家境很好的女子，经常去市场买小动物，再将它们放归自然。", "但遇到吃小动物的人，她就很生气，会让手下打对方一顿，随后赔钱。原叙述说，她这样做是为了让自己消气。", "原答复描述了善心、责任心、执着、事业心以及对生活品位的追求，同时指出，遇事容易发火、性格急躁，是需要改善的方面。"]}];
let SEARCH=null;let searchPromise=null;

const hdr=document.querySelector('header');
const heroEl=document.querySelector('.hero');
let lastY=0;
const toTop=document.querySelector('#to-top');
function onScroll(){
  const y=window.scrollY;
  if(hdr){const oh=heroEl?(y<heroEl.offsetHeight-120):false;hdr.classList.toggle('over-hero',oh);hdr.classList.toggle('solid',!oh&&y>30)}
  if(hdr){ if(y>140&&y>lastY+4){hdr.classList.add('hidden');} else if(y<lastY-4||y<=140){hdr.classList.remove('hidden');} }
  lastY=y;
  if(toTop)toTop.hidden=y<600;
}
window.addEventListener('scroll',onScroll,{passive:true});onScroll();
if(toTop)toTop.onclick=()=>window.scrollTo({top:0,behavior:'smooth'});
const themeBtn=document.querySelector('#theme-toggle');
const MOON='<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>';const SUN='<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="4.2"/><path d="M12 2v2.6M12 19.4V22M4.9 4.9l1.8 1.8M17.3 17.3l1.8 1.8M2 12h2.6M19.4 12H22M4.9 19.1l1.8-1.8M17.3 6.7l1.8-1.8"/></svg>';const SEPIA='<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="10" r="4.2"/><path d="M4 17h16M7 20.5h10"/></svg>';const THEME_ORDER=['light','dark','sepia'];function curTheme(){const c=document.documentElement.classList;return c.contains('dark')?'dark':(c.contains('sepia')?'sepia':'light')}function applyTheme(t){const c=document.documentElement.classList;c.remove('dark','sepia');if(t!=='light')c.add(t);try{localStorage.setItem('ghl_theme',t)}catch(e){}}function paintTheme(){if(themeBtn){const nx=THEME_ORDER[(THEME_ORDER.indexOf(curTheme())+1)%3];themeBtn.innerHTML=nx==='dark'?MOON:(nx==='sepia'?SEPIA:SUN);themeBtn.setAttribute('aria-label',nx==='dark'?'切换晚上模式':(nx==='sepia'?'切换米色模式':'切换白天模式'))}}
if(themeBtn){try{const st=localStorage.getItem('ghl_theme');if(st==='dark'||st==='sepia')applyTheme(st)}catch(e){}themeBtn.onclick=()=>{applyTheme(THEME_ORDER[(THEME_ORDER.indexOf(curTheme())+1)%3]);paintTheme()};paintTheme()}
const dustBox=document.getElementById('dust');
if(dustBox){for(let i=0;i<16;i++){const s=document.createElement('span');const sz=3+Math.random()*6;s.style.width=sz+'px';s.style.height=sz+'px';s.style.left=(18+Math.random()*64)+'%';s.style.top=(12+Math.random()*62)+'%';s.style.animationDuration=(9+Math.random()*14)+'s';s.style.animationDelay=(-Math.random()*16)+'s';dustBox.appendChild(s)}}
const io=new IntersectionObserver(es=>es.forEach(e=>{if(e.isIntersecting){e.target.classList.add('in');io.unobserve(e.target)}}),{threshold:0.12});
document.querySelectorAll('.reveal').forEach(el=>io.observe(el));
const dialog=document.querySelector('#reader');
function openCase(c){
  if(!c||!dialog)return;
  document.querySelector('#reader-title').textContent=c.title;
  const body=document.querySelector('#reader-body');
  body.replaceChildren(...c.paragraphs.map(t=>{const p=document.createElement('p');p.textContent=t;return p}));
  if(!dialog.open)dialog.showModal();
}
if(dialog){document.querySelector('#close').onclick=()=>dialog.close();dialog.addEventListener('close',()=>history.replaceState(null,'',location.pathname+location.search))}
function route(){const id=location.hash.slice(1);const c=cases.find(c=>c.id===id);if(c)openCase(c)}
window.addEventListener('hashchange',route);route();
document.querySelectorAll('[data-rot]').forEach(box=>{
  const title=box.querySelector('.rot-title'),intro=box.querySelector('.rot-intro'),wall=box.querySelector('.casewall'),open=box.querySelector('.rot-open');
  let idx=parseInt(box.dataset.start||'0',10)%cases.length;
  function paint(fade){
    const c=cases[idx];
    const apply=()=>{title.textContent='《'+c.title+'》';intro.textContent=c.intro;[...wall.children].forEach((b,i)=>b.classList.toggle('on',cases[i].id===c.id));title.classList.remove('out');intro.classList.remove('out')};
    if(fade){title.classList.add('out');intro.classList.add('out');setTimeout(apply,450)}else apply();
  }
  cases.forEach((c,i)=>{const b=document.createElement('button');b.type='button';b.textContent=c.title;b.onclick=()=>{idx=i;paint(true)};wall.appendChild(b)});
  if(open)open.onclick=()=>openCase(cases[idx]);
  box._next=()=>{idx=(idx+1)%cases.length;paint(true)};
  paint(false);
  setInterval(()=>{if(!document.hidden)box._next()},5200);
});
document.querySelectorAll('[data-shuffle]').forEach(a=>{a.addEventListener('click',ev=>{const sec=a.closest('section');const box=sec&&sec.querySelector('[data-rot]');if(box&&box._next){ev.preventDefault();box._next()}})});
function playInto(stage,vid,title){
  const f=document.createElement('iframe');f.src='https://www.youtube.com/embed/'+vid+'?autoplay=1&playsinline=1';f.title=title||'视频';f.allow='autoplay; encrypted-media; fullscreen; picture-in-picture';f.allowFullscreen=true;f.referrerPolicy='strict-origin-when-cross-origin';stage.replaceChildren(f);
}
document.querySelectorAll('.stage>button[data-video]').forEach(b=>{b.onclick=()=>playInto(b.parentElement,b.dataset.video,b.getAttribute('aria-label'))});
document.querySelectorAll('[data-replay]').forEach(a=>{a.addEventListener('click',ev=>{ev.preventDefault();location.reload()})});
const vibeStage=document.getElementById('vibe-stage'),vibeTitle=document.getElementById('vibe-title');
document.querySelectorAll('[data-vibe]').forEach(ch=>{
  ch.onclick=()=>{
    document.querySelectorAll('[data-vibe]').forEach(x=>x.classList.remove('on'));ch.classList.add('on');
    if(vibeTitle)vibeTitle.textContent='《'+ch.dataset.t+'》';
    const vo=document.getElementById('vibe-open');if(vo)vo.href='https://youtu.be/'+ch.dataset.vibe;
    if(vibeStage){const old=vibeStage.querySelector('button');if(old){old.dataset.video=ch.dataset.vibe;old.setAttribute('aria-label','播放：'+ch.dataset.t);const img=old.querySelector('img');if(img){img.removeAttribute('data-fb');img.src='https://i.ytimg.com/vi/'+ch.dataset.vibe+'/hqdefault.jpg'}}else{playInto(vibeStage,ch.dataset.vibe,ch.dataset.t)}}
  };
});
const sForm=document.getElementById('search-form'),sInput=document.getElementById('search-input'),sBox=document.getElementById('search-results');
function ensureSearch(){if(SEARCH)return Promise.resolve(SEARCH);if(!searchPromise){searchPromise=fetch('reading_search.json?v=20261115p6').then(r=>{if(!r.ok)throw new Error('http '+r.status);return r.json()}).then(d=>{SEARCH=d;return d}).catch(()=>{SEARCH=[];return SEARCH})}return searchPromise}
function hlText(el,text,q){
  if(!q){el.textContent=text;return;}
  const low=text.toLowerCase();let i=0;
  for(;;){const j=low.indexOf(q,i);if(j<0)break;if(j>i)el.appendChild(document.createTextNode(text.slice(i,j)));const m=document.createElement('mark');m.textContent=text.slice(j,j+q.length);el.appendChild(m);i=j+q.length;}
  if(i<text.length)el.appendChild(document.createTextNode(text.slice(i)));
}
function doSearch(rec){
  if(!sBox)return;
  const raw=(sInput.value||'').trim();
  const q=raw.toLowerCase();
  if(!q){sBox.replaceChildren();return;}
  if(!SEARCH){ensureSearch().then(()=>{doSearch(rec)});return;}
  sBox.replaceChildren();
  const hits=SEARCH.filter(e=>(e.t+' '+e.x).toLowerCase().includes(q)).slice(0,8);
  if(!hits.length){
    const d=document.createElement('div');d.className='none';d.textContent='没找到「'+q+'」';sBox.appendChild(d);
    const POOL=['修行','因果','福报','轮回','孩子','菩萨','鬼','投胎','灵魂','事业','父母','健康','去世','财运','婚姻','天眼','超度','阴债','烧纸','风水','祖先','冤亲','改命','做梦'];
    const hit=w=>SEARCH.some(e=>(e.t+' '+e.x).toLowerCase().includes(w));
    const sim=[];for(const w of POOL){if(w===q)continue;let n=0;for(const ch of w){if(q.includes(ch))n++;}if(n>0&&hit(w))sim.push([n,w]);}
    sim.sort((a,b)=>b[0]-a[0]);
    const simW=sim.slice(0,4).map(x=>x[1]);
    const hot=[];for(const w of POOL){if(hot.length>=6)break;if(simW.indexOf(w)<0&&w!==q&&hit(w))hot.push(w);}
    for(const w of POOL){if(hot.length>=6)break;if(simW.indexOf(w)<0&&w!==q&&hot.indexOf(w)<0)hot.push(w);}
    const sg=document.createElement('div');sg.className='qsugg';
    const mk=(lab,ws)=>{if(!ws.length)return;const s=document.createElement('span');s.className='qsugg-lab';s.textContent=lab;sg.appendChild(s);ws.forEach(w=>{const b=document.createElement('button');b.type='button';b.textContent=w;b.onclick=()=>{sInput.value=w;doSearch(true);sInput.focus();hideSugg();};sg.appendChild(b);});};
    mk('相近的词，点一下就搜：',simW);
    mk('大家常搜：',hot);
    const lk=document.createElement('span');lk.className='qsugg-link';const a=document.createElement('a');a.href='all.html';a.textContent='去资料库用全文搜索 →';lk.appendChild(a);sg.appendChild(lk);
    sBox.appendChild(sg);return;
  }
  if(rec&&hits.length)saveHist(raw);
  hits.forEach(e=>{const a=document.createElement('a');a.className='hit';a.href=e.p+'#'+e.id;const b=document.createElement('b');hlText(b,e.t,q);const s=document.createElement('span');hlText(s,(e.d?e.d+' · ':'')+e.x,q);a.append(b,s);sBox.appendChild(a)});
}
const HOTWORDS=['修行','因果','福报','轮回','孩子','菩萨','鬼','投胎','灵魂','事业','父母','去世','财运','婚姻','天眼','超度','阴债','烧纸','风水','祖先','冤亲','改命'];
const HIST_KEY='ghl_search_hist';
function loadHist(){try{const v=JSON.parse(localStorage.getItem(HIST_KEY)||'[]');return Array.isArray(v)?v.filter(x=>typeof x==='string'):[]}catch(e){return[]}}
function saveHist(term){term=(term||'').trim();if(!term||term.length>24)return;try{const h=loadHist().filter(x=>x!==term);h.unshift(term);localStorage.setItem(HIST_KEY,JSON.stringify(h.slice(0,8)))}catch(e){}}
function clearHist(){try{localStorage.removeItem(HIST_KEY)}catch(e){}}
const sPanel=document.getElementById('search-sugg');
let sgHi=-1;
let suggOpenedAt=0;
let userScrollAt=0;
function markUserScroll(){userScrollAt=Date.now();}
function suggList(){
  const q=(sInput.value||'').trim().toLowerCase();
  const hist=loadHist();
  const out=[];
  const push=w=>{if(w&&out.length<5&&out.indexOf(w)<0)out.push(w)};
  const hitW=w=>!SEARCH||!SEARCH.length||SEARCH.some(e=>(e.t+' '+e.x).toLowerCase().includes(w.toLowerCase()));
  if(!q){hist.forEach(push);for(const w of HOTWORDS){if(out.length>=5)break;if(hitW(w))push(w);}return out;}
  hist.filter(h=>h.toLowerCase().includes(q)).slice(0,2).forEach(push);
  for(const w of HOTWORDS){if(out.length>=5)break;if(w.toLowerCase().includes(q)&&hitW(w))push(w);}
  if(SEARCH){for(const e of SEARCH){if(out.length>=5)break;if(e.t.toLowerCase().includes(q))push(e.t);}}
  return out;
}
function renderSugg(){
  if(!sPanel||!sForm)return;
  const q=(sInput.value||'').trim();
  const list=suggList();
  sPanel.replaceChildren();
  sgHi=-1;
  if(!list.length){hideSugg();return;}
  const hist=loadHist();
  list.forEach(w=>{
    const b=document.createElement('button');b.type='button';b.className='sg-row';b.setAttribute('role','option');
    const t=document.createElement('span');t.className='sg-t';t.textContent=w;b.appendChild(t);
    if(hist.indexOf(w)>=0){const tag=document.createElement('span');tag.className='sg-tag';tag.textContent='历史';b.appendChild(tag);}
    b.addEventListener('click',()=>{sInput.value=w;hideSugg();doSearch(true);sInput.focus();});
    sPanel.appendChild(b);
  });
  if(!q&&hist.length){
    const c=document.createElement('button');c.type='button';c.className='sg-clear';c.textContent='清除搜索记录';
    c.addEventListener('click',()=>{clearHist();renderSugg();sInput.focus();});
    sPanel.appendChild(c);
  }
  sPanel.hidden=false;
  suggOpenedAt=Date.now();
  userScrollAt=0;
  sInput.setAttribute('aria-expanded','true');
}
function hideSugg(){if(!sPanel)return;sPanel.hidden=true;sgHi=-1;if(sInput)sInput.setAttribute('aria-expanded','false');}
function refreshSugg(){if(document.activeElement===sInput)renderSugg();}
if(sForm){
  sForm.addEventListener('submit',ev=>{ev.preventDefault();hideSugg();doSearch(true)});
  sInput.addEventListener('input',()=>{doSearch(false);refreshSugg()});
  sInput.addEventListener('focus',()=>{renderSugg();ensureSearch().then(()=>refreshSugg())});
  sInput.addEventListener('keydown',ev=>{
    if(!sPanel||sPanel.hidden)return;
    const rows=[...sPanel.querySelectorAll('.sg-row')];
    if(ev.key==='Escape'){ev.preventDefault();hideSugg();return;}
    if(ev.key==='ArrowDown'||ev.key==='ArrowUp'){ev.preventDefault();if(!rows.length)return;sgHi=ev.key==='ArrowDown'?(sgHi+1)%rows.length:(sgHi-1+rows.length)%rows.length;rows.forEach((r,i)=>r.classList.toggle('on',i===sgHi));return;}
    if(ev.key==='Enter'&&sgHi>=0&&rows[sgHi]){ev.preventDefault();rows[sgHi].click();}
  });
  sForm.addEventListener('focusout',ev=>{if(!sForm.contains(ev.relatedTarget))hideSugg();});
  if(sPanel)sPanel.addEventListener('mousedown',ev=>ev.preventDefault());
  document.addEventListener('click',ev=>{if(!ev.target.closest('#search-form'))hideSugg();});
  window.addEventListener('wheel',markUserScroll,{passive:true});
  window.addEventListener('touchmove',markUserScroll,{passive:true});
  window.addEventListener('keydown',ev=>{if(ev.target!==sInput&&['ArrowDown','ArrowUp','PageDown','PageUp','Home','End',' '].indexOf(ev.key)>=0)markUserScroll();});
  window.addEventListener('scroll',()=>{if(sPanel&&!sPanel.hidden&&Date.now()-suggOpenedAt>400&&userScrollAt&&Date.now()-userScrollAt<1500)hideSugg();},{passive:true});
}
document.querySelectorAll('[data-q]').forEach(b=>b.addEventListener('click',()=>{if(sInput){sInput.value=b.getAttribute('data-q');doSearch(true);sInput.focus();hideSugg()}}));
document.addEventListener('click',e=>{const c=e.target.closest?e.target.closest('.vchip[data-v]'):null;if(c){e.preventDefault();e.stopPropagation();location.href=c.getAttribute('data-v')}},true);
const pageSearch=document.querySelector('#search');
if(pageSearch&&!sInput){const rows=[...document.querySelectorAll('details.entry')];function filter(){let n=0;for(const r of rows){r.hidden=!r.textContent.toLowerCase().includes(pageSearch.value.trim().toLowerCase());if(!r.hidden)n++}const c=document.querySelector('#count');if(c)c.textContent=n+' 篇';const em=document.querySelector('#empty');if(em)em.hidden=n!==0}pageSearch.oninput=filter;filter()}
;(function(){var POOL=['修行','因果','福报','轮回','孩子','菩萨','鬼','投胎','灵魂','事业','父母','健康','去世','财运','婚姻','天眼','超度','阴债','烧纸','风水','祖先','冤亲','改命','做梦'];var wrap=document.querySelector('.qchips');if(!wrap)return;var btns=[].slice.call(wrap.querySelectorAll('button[data-q]'));if(!btns.length)return;function pick(){var p=POOL.slice();for(var i=p.length-1;i>0;i--){var j=Math.floor(Math.random()*(i+1));var t=p[i];p[i]=p[j];p[j]=t}return p.slice(0,btns.length)}function apply(w){btns.forEach(function(b,i){b.textContent=w[i];b.setAttribute('data-q',w[i])})}apply(pick());setInterval(function(){var inp=document.getElementById('search-input');if(inp&&inp.value.trim())return;wrap.classList.add('fading');setTimeout(function(){apply(pick());wrap.classList.remove('fading')},480)},12000)})();
