from pathlib import Path
import json,re,html,shutil
from urllib.parse import urlsplit,unquote
from bs4 import BeautifulSoup
root=Path(__file__).resolve().parent;src=root;out=root
esc=html.escape
cases=json.loads((root/'reading_cases.json').read_text(encoding='utf-8'))
entries={}
for p in sorted(src.glob('*.html')):
 if not re.fullmatch(r'202\d|undated(?:_\d+)?',p.stem):continue
 soup=BeautifulSoup(p.read_text(encoding='utf-8'),'html.parser')
 for d in soup.select('details.entry[id]'):
  if d['id'] in entries:continue
  title=d.find('h2').get_text(' ',strip=True)
  for el in d.select('iframe,video,audio,img,script,button,style'):el.decompose()
  for a in d.select('a[href]'):
   if any(x in a['href'] for x in ['youtu','douyin','tiktok']):a.decompose()
  for a in d.select('a[href]'):
   u=urlsplit(a['href'])
   if u.scheme or u.netloc or not u.path:continue
   if u.path=='feedback.html':
    a['href']='https://guihailu.github.io/'+a['href']
   elif u.path.startswith('media/'):
    asset=(src/unquote(u.path)).resolve()
    if not asset.is_relative_to(src.resolve()) or not asset.is_file():raise ValueError('Missing source asset: '+u.path)
    target=out/unquote(u.path);target.parent.mkdir(parents=True,exist_ok=True);
    if asset.resolve()!=target.resolve():shutil.copyfile(asset,target)
  entries[d['id']]={'id':d['id'],'title':title,'body':str(d),'text':d.get_text(' ',strip=True)}
css='''*{box-sizing:border-box}body{margin:0;background:#f5f2ea;color:#172b39;font-family:"Microsoft YaHei",sans-serif}a{color:inherit;text-decoration:none}a:hover{text-decoration:underline}button,input{font:inherit}button,a.button{cursor:pointer;border:1px solid #b6a378;background:transparent;color:inherit;padding:11px 18px;border-radius:3px}button:hover,a.button:hover{background:#e9dfc9}header{background:#112c3c;color:#f4f0e6;padding:22px max(5vw,20px);display:flex;gap:20px;align-items:center;justify-content:space-between}header strong{font-family:SimSun,serif;font-size:29px;letter-spacing:6px}header nav{display:flex;gap:20px;align-items:center;font-size:14px}header .button{background:#e7d7b3;color:#162e3c}main{max-width:1120px;margin:auto;padding:45px 24px}small,.eyebrow{color:#876b39;font-size:12px;letter-spacing:2px}.hero{padding:20px 0 38px;border-bottom:1px solid #cfc7b9}.hero h1{font-family:SimSun,serif;font-weight:normal;font-size:clamp(32px,5vw,52px);margin:18px 0}.hero p{color:#607078;line-height:1.9}.lead{display:grid;grid-template-columns:1.6fr 1fr;gap:24px;margin-top:32px}.feature{padding:34px;background:#fffdf7;border-top:3px solid #b59860}.feature h2{font-family:SimSun,serif;font-weight:normal;font-size:30px;line-height:1.5}.feature p{line-height:1.9;color:#51616b}.side{background:#e9e5db;padding:28px}.side a{display:block;padding:20px 0;border-bottom:1px solid #cdc7bb}.heading{display:flex;align-items:center;justify-content:space-between;margin:46px 0 22px;gap:15px}.heading h2{font-family:SimSun,serif;font-size:27px;font-weight:normal;margin:0}.grid{display:grid;grid-template-columns:repeat(3,1fr);gap:20px}.card{background:#fffdf8;border:1px solid #ddd7c9;padding:24px}.card h3{font-size:19px;line-height:1.6;font-weight:500}.card p{font-size:14px;color:#607078;line-height:1.9}.card a{color:#866632}.screen{aspect-ratio:16/9;background:#183544;color:#f1e2be;display:grid;place-content:center;text-align:center;padding:20px;font-family:SimSun,serif;font-size:23px}.screen button{color:inherit;margin-top:15px}.screen iframe{width:100%;height:100%;border:0}.screen:has(iframe){padding:0;display:block}.muted{color:#6e7475;font-size:13px;line-height:1.8}input{width:100%;padding:16px;border:1px solid #c4b79a;background:#fffdf8;margin:20px 0}details.entry{background:#fffdf8;border-bottom:1px solid #ddd7c9;padding:20px;margin-bottom:10px}summary{cursor:pointer}summary h2{font-size:18px;display:inline;font-weight:500}summary .date{display:block;font-size:12px;color:#777;margin-top:7px}summary .excerpt{display:none}.entry-body{line-height:2;max-width:780px;margin:24px auto;overflow-wrap:anywhere}.entry-body h3{font-size:20px}dialog{max-width:720px;width:calc(100% - 32px);max-height:85vh;border:0;background:#fffdf7;padding:32px;color:#172b39}dialog::backdrop{background:#102c3bc9}dialog p{line-height:2}footer{padding:30px;text-align:center;color:#727877;font-size:12px}a:focus-visible,button:focus-visible{outline:3px solid #aa8036;outline-offset:4px}[hidden]{display:none!important}@media(max-width:700px){header{align-items:flex-start}header nav{flex-wrap:wrap;justify-content:flex-end;gap:12px}.lead,.grid{grid-template-columns:1fr}.hero{padding-top:0}.feature{padding:25px}.heading{margin-top:32px}main{padding:28px 18px}}'''
css+='\n.play-help{font-size:13px;color:#677277;margin-top:18px;border-top:1px solid #ded8ca;padding-top:12px}.play-help p{font-size:13px}.play-help a{text-decoration:underline}\n'
(out/'reading.css').write_text(css,encoding='utf-8')
def shell(title,body,domestic=False,index=False):
 nav='<a href="index.html">视频与阅读</a>' if domestic else '<a class="button" href="domestic.html">国内版 · 纯文字 →</a>'
 seo=''
 if index:
  canonical='https://guihailu.github.io/'
  ld=json.dumps({'@context':'https://schema.org','@type':'WebSite','name':'归海录 · 志远行空','url':canonical,'description':'归海录：志远行空的公开分享与 YouTube 视频讲法合集','inLanguage':'zh-CN'},ensure_ascii=False)
  seo=('<link rel="canonical" href="'+canonical+'">'
       '<meta property="og:url" content="'+canonical+'">'
       '<meta property="og:title" content="'+esc(title)+'">'
       '<meta property="og:description" content="归海录：志远行空的公开分享与 YouTube 视频讲法合集">'
       '<meta property="og:type" content="website">'
       '<meta property="og:site_name" content="归海录 · 志远行空">'
       '<meta property="og:locale" content="zh_CN">'
       '<meta property="og:image" content="https://guihailu.github.io/cover.jpg">'
       '<meta name="twitter:card" content="summary_large_image">'
       '<script type="application/ld+json">'+ld+'</script>')
 return '<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>'+title+'</title>'+seo+'<link rel="stylesheet" href="reading.css"></head><body><header><a href="index.html"><strong>归海录</strong></a><nav><a href="domestic.html#library">完整资料库</a>'+nav+'</nav></header><main>'+body+'</main><footer>志远行空公开分享整理</footer><dialog id="reader"><button id="close">关闭阅读 ×</button><h2 id="reader-title"></h2><div id="reader-body"></div></dialog><script src="reading.js"></script></body></html>'
feature=cases[0]
body='<section class="hero"><small>志远行空公开分享整理</small><h1>从一则故事，慢慢读进去。</h1><p>读过的分享，在这里找到；感兴趣的话题，从这里继续。</p></section><div class="lead"><article class="feature" id="'+esc(feature['id'])+'"><small>先读一则 · 案例选读</small><h2>'+esc(feature['title'])+'</h2><p>'+esc(feature['intro'])+'</p><a class="button" href="#'+feature['id']+'">读完整故事 →</a></article><aside class="side"><small>从这里继续</small><a href="#stories">再读一则故事 →</a><a href="#videos">看看最近的分享 →</a><a href="domestic.html#library">查找师父完整原文 →</a><p class="muted">读故事，也可以继续查找相关讲课原文。</p></aside></div><section id="stories"><div class="heading"><h2>也许，你还想读</h2><button id="shuffle">换一组 ↻</button></div><div class="grid" id="stories-grid"></div></section>'
body+='<section id="videos"><div class="heading"><h2>换个角度看人生</h2><span class="muted">中文故事短片</span></div><div class="grid">'
vibes=json.loads((src/'vibe_cards.json').read_text(encoding='utf-8'))['cards']
for c in sorted(vibes,key=lambda x:x['published_at'],reverse=True)[:3]:
 body+='<article class="card"><div class="screen">'+esc(c['title'])+'</div><p>'+esc(c['description'])+'</p><a href="domestic.html#'+c['article_id']+'">先读相关原文 →</a></article>'
body+='</div></section><section><div class="heading"><h2>听师父讲一段</h2></div><div class="grid">'
clips=json.loads((src/'video_cards.json').read_text(encoding='utf-8'))['cards']
for c in sorted(clips,key=lambda x:x['published_at'],reverse=True)[:3]:
 vid=c['youtube_url'].split('/')[-1]
 body+='<article class="card"><div class="screen"><span>'+esc(c['title'])+'</span><button data-video="'+vid+'">▶ 点击播放</button></div><p>'+esc(c['description'])+'</p><a href="domestic.html#'+c['article_id']+'">阅读完整原文 →</a></article>'
body+='</div></section><div class="heading"><h2>想找以前讲过的内容？</h2><a class="button" href="domestic.html#library">进入完整资料库 →</a></div>'
(out/'index.html').write_text(shell('归海录 · 视频与阅读',body,index=True),encoding='utf-8')
body='<section class="hero"><small>国内版 · 纯文字</small><h1>把读过的，再找回来。</h1><p>完整原文与案例阅读，不加载视频、封面或第三方播放器。</p></section><section id="stories"><div class="heading"><h2>先读一则故事</h2><button id="shuffle">换一组 ↻</button></div><p class="muted">案例经匿名整理，叙述与观点来自原案例。</p><div class="grid" id="stories-grid"></div></section><section id="library"><div class="heading"><h2>完整原文</h2><span id="count"></span></div><label for="search">搜索标题或正文</label><input id="search" type="search" placeholder="输入你想找的词，例如：六通"><div id="entries">'+''.join(e['body'] for e in entries.values())+'</div><p id="empty" hidden>没有找到匹配原文，试试更短的关键词。</p></section>'
(out/'domestic.html').write_text(shell('归海录 · 国内纯文字版',body,True),encoding='utf-8')
js='const cases='+json.dumps(cases,ensure_ascii=False)+';\n'+'''const grid=document.querySelector('#stories-grid');let last=[];function render(){const pool=cases.filter(c=>!last.includes(c.id));for(let i=pool.length-1;i>0;i--){let j=Math.floor(Math.random()*(i+1));[pool[i],pool[j]]=[pool[j],pool[i]]}const batch=pool.slice(0,3);last=batch.map(c=>c.id);grid.replaceChildren(...batch.map(c=>{const el=document.createElement('article');el.className='card';const h=document.createElement('h3'),p=document.createElement('p'),a=document.createElement('a');h.textContent=c.title;p.textContent=c.intro;a.href='#'+c.id;a.textContent='阅读完整故事 →';el.append(h,p,a);return el}));}document.querySelector('#shuffle').onclick=render;render();const dialog=document.querySelector('dialog');function route(){const id=location.hash.slice(1),c=cases.find(c=>c.id===id);if(c){document.querySelector('#reader-title').textContent=c.title;document.querySelector('#reader-body').replaceChildren(...c.paragraphs.map(t=>{const p=document.createElement('p');p.textContent=t;return p}));if(!dialog.open)dialog.showModal()}else{const d=document.getElementById(id);if(d&&d.matches('details')){d.open=true;d.scrollIntoView()}}}window.addEventListener('hashchange',route);document.querySelector('#close').onclick=()=>dialog.close();dialog.addEventListener('close',()=>history.replaceState(null,'',location.pathname));route();const search=document.querySelector('#search');if(search){const rows=[...document.querySelectorAll('details.entry')];function filter(){let n=0;for(const r of rows){r.hidden=!r.textContent.toLowerCase().includes(search.value.trim().toLowerCase());if(!r.hidden)n++}document.querySelector('#count').textContent=n+' 篇';document.querySelector('#empty').hidden=n!==0}search.oninput=filter;filter()}document.querySelectorAll('[data-video]').forEach(b=>{const stage=b.parentElement,card=stage.parentElement,title=stage.querySelector('span').textContent;const help=document.createElement('details');help.className='play-help';const summary=document.createElement('summary');summary.textContent='播放遇到问题？';const note=document.createElement('p');note.textContent='若播放器要求登录，可打开此视频的 YouTube 页面；也可以继续阅读完整原文。';const link=document.createElement('a');link.href='https://www.youtube.com/watch?v='+b.dataset.video;link.target='_blank';link.rel='noopener';link.textContent='在 YouTube 打开此视频 ↗';help.append(summary,note,link);card.append(help);const stop=document.createElement('button');stop.textContent='收起播放器';stop.hidden=true;stop.style.marginTop='12px';card.append(stop);const original=[...stage.childNodes];b.onclick=()=>{document.querySelectorAll('[data-stop]').forEach(x=>{if(!x.hidden)x.click()});const f=document.createElement('iframe');f.src='https://www.youtube.com/embed/'+b.dataset.video+'?autoplay=1&playsinline=1';f.title=title;f.allow='autoplay; encrypted-media; fullscreen; picture-in-picture';f.allowFullscreen=true;f.referrerPolicy='strict-origin-when-cross-origin';stage.style.aspectRatio='9 / 16';stage.replaceChildren(f);stop.hidden=false;};stop.dataset.stop='';stop.onclick=()=>{stage.replaceChildren(...original);stage.style.aspectRatio='16 / 9';stop.hidden=true;b.focus();};});
'''
(out/'reading.js').write_text(js,encoding='utf-8')
print('Preview created:',len(entries),'full original articles;',len(cases),'anonymous samples')
assert len(entries)>=100
assert not BeautifulSoup((out/'domestic.html').read_text(encoding='utf-8'),'html.parser').select('iframe,video,img,[data-video]')
for page in ['index.html','domestic.html']:
 soup=BeautifulSoup((out/page).read_text(encoding='utf-8'),'html.parser')
 for a in soup.select('a[href^="domestic.html#"]'):assert a['href'].split('#')[1] in entries or a['href'].endswith('#library')
print('PASS: domestic page no video/image triggers; article destinations exist')
