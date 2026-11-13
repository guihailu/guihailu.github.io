from pathlib import Path
import json,re,html,shutil
from urllib.parse import urlsplit,unquote
from bs4 import BeautifulSoup
root=Path(__file__).resolve().parent;src=root;out=root
esc=html.escape
cases=json.loads((root/'reading_cases.json').read_text(encoding='utf-8'))
board_map=json.loads((root/'board_map.json').read_text(encoding='utf-8'))
entries={}
for p in sorted(src.glob('*.html')):
 if not re.fullmatch(r'202\d|undated(?:_\d+)?',p.stem):continue
 soup=BeautifulSoup(p.read_text(encoding='utf-8'),'html.parser')
 for d in soup.select('details.entry[id]'):
  if d['id'] in entries:continue
  _h2=d.find('h2');_tm=_h2.find('span',class_='t-main')
  if _tm is not None:
   _tq=_h2.find('span',class_='t-meta')
   title=_tm.get_text(strip=True)+'｜'+(_tq.get_text(strip=True) if _tq is not None else '')
   _h2.clear();_h2.append(title)
  else:
   title=_h2.get_text(' ',strip=True)
  for el in d.select('iframe,video,audio,img,script,button,style'):el.decompose()
  # p18 接着读是条目末尾的导航层，不计入正文文本（阅读时长/钩子/按问题找评分须与改前一致）
  for el in d.select('.next-read'):el.decompose()
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
  entries[d['id']]={'id':d['id'],'title':title,'raw':title,'body':str(d),'text':d.get_text(' ',strip=True),'page':p.name}
meta={}
for f in sorted(src.glob('search_index_*.json'))+sorted(src.glob('search_shared.json')):
 try:data=json.loads(f.read_text(encoding='utf-8'))
 except Exception:continue
 for e in data.get('entries',[]):
  if e['id'] not in meta:meta[e['id']]={'date':e.get('date',''),'text':e.get('text','')}
def clean_title(t):
 m=re.match(r'^EP\s?\d+\s+(.{1,14}?)·\s*(.+)$',t)
 if m:return m.group(2)
 return re.sub(r'^EP\s?\d+\s+','',t)
HOOK_BAD=['大家好','点赞','关注','订阅','谢谢观看','下期见','直播间','评论区','视频里']
HOOK_SKIP=re.compile(r'^(开场|开头|导语|摘要|本期|这一期|首先)|\d{4}[-/年]\d{1,2}|·\s*\d+:\d{2}')
def make_hook(e):
 t=e['text']
 raw=e.get('raw',e['title'])
 if t.startswith(raw):t=t[len(raw):]
 t=t.strip()
 t=re.sub(r'^\d{4}[-/年]\d{1,2}([-/月]\d{1,2}日?)?\s*(·\s*\d+:\d{2}(:\d{2})?)?\s*','',t)
 cands=[]
 for s in re.split(r'(?<=[。！？])',t):
  s=s.strip().strip(' " "「」『』')
  s=re.sub(r'^[\s💡🔸🔹🎯\-—·•"“”\'（(]+','',s)
  if 12<=len(s)<=70 and not any(b in s for b in HOOK_BAD) and not HOOK_SKIP.search(s[:14]):
   cands.append(s)
 for s in cands:
  if len(s)<=48:return s
 for s in cands:
  cut=max(s.rfind(p,0,48) for p in '，；：、——')
  return (s[:cut+1]+'…') if cut>=16 else (s[:48]+'…')
 return (t[:44]+'…') if len(t)>44 else t
for eid,e in entries.items():
 e['date']=meta.get(eid,{}).get('date','')
 e['board']=board_map[eid]['board'] if eid in board_map else 0
 e['title']=clean_title(e['title'])
 e['hook']=make_hook(e)
 e['mins']=max(1,round(len(e['text'])/400))
missing=[eid for eid in entries if eid not in board_map]
assert not missing,'board_map missing entries: '+str(missing)
extra=[eid for eid in board_map if eid not in entries]
assert not extra,'board_map has unknown entries: '+str(extra)
def datauri(fname,mime):
 # p15 首页瘦身（2026-11-09 公开前改造一）：图片改外链独立文件（assets/boards/ 下与 .b64 并存的解码原件），不再内嵌 data URI；回退＝恢复下方两行原实现。
 return 'assets/boards/'+fname+'?v=20261112p19'
IMG1=datauri('board1-nixiu.webp','image/webp')
IMG2=datauri('board2-linghun.webp','image/webp')
IMG3=datauri('board3-fajie.webp','image/webp')
IMG4=datauri('board4-daofa.webp','image/webp')
HERO_IMG=datauri('hero-fajie.webp','image/webp')
SEAL_IMG=datauri('seal.png','image/png')
FAVICON=datauri('favicon.png','image/png')
SITEDESC='志远行空讲课内容的整理站：121 篇讲课整理分成四部——逆修觉者、灵魂觉者、法界天机、道法自然，每部都有故事案例、讲课原声和小动画。'
TITLE_GUIHAI=datauri('title-guihai.webp','image/webp')
TITLE_SUB=datauri('title-brandsub.webp','image/webp')
TITLE_ZHE=datauri('title-zhe.webp','image/webp')
WMIMG={1:datauri('title-wm1.webp','image/webp'),2:datauri('title-wm2.webp','image/webp'),3:datauri('title-wm3.webp','image/webp'),4:datauri('title-wm4.webp','image/webp')}
TITLES={1:datauri('title-nixiu.webp','image/webp'),2:datauri('title-linghun.webp','image/webp'),3:datauri('title-fajie.webp','image/webp'),4:datauri('title-daofa.webp','image/webp')}
NAVTITLES={1:datauri('title-nixiu-sm.webp','image/webp'),2:datauri('title-linghun-sm.webp','image/webp'),3:datauri('title-fajie-sm.webp','image/webp'),4:datauri('title-daofa-sm.webp','image/webp')}
NAVLIB=datauri('title-lib-sm.webp','image/webp')
TITLE_LIB=datauri('title-lib.webp','image/webp')
BOARDS=[
 {'n':1,'cn':'一','wm':'壹','name':'逆修觉者','img':IMG1,
  'plain':'日子照过活法换一种<br>在红尘里把自己修回来',
  'desc':'这一部讲的是普通人的修行：为什么修、修行到底是什么、从哪儿开始。福报怎么做、话怎么说、事怎么做，逆修自查一条条对着自己量。离生活最近的一部，先从这里进门。',
  'first':'ghl-000018'},
 {'n':2,'cn':'二','wm':'貳','name':'灵魂觉者','img':IMG2,
  'plain':'人除了身体还有一个<br>「自己」在水底下',
  'desc':'这一部讲灵魂这一层：灵魂是怎么回事，洗灵有什么用，人在镜子里外是怎样两个样子。听着玄，其实讲的都是为什么你明明想做好、却总是做不到。',
  'first':'ghl-000070'},
 {'n':3,'cn':'三','wm':'叁','name':'法界天机','img':IMG3,
  'plain':'看不见的那一界<br>也有它的规矩和账本',
  'desc':'这一部讲看不见的世界怎么运作：三界是怎么分的，阴间也有经济学，烧纸为什么有讲究、怎么做才对。好奇心最重的人，通常是从这一部被勾住的。',
  'first':'ghl-000051'},
 {'n':4,'cn':'四','wm':'肆','name':'道法自然','img':IMG4,
  'plain':'道理听完要落回<br>一日三餐里',
  'desc':'这一部最落地：前面听懂的道理，怎么用在过日子上——对家人、对工作、对钱、对脾气。修行不在山上，在你每天怎么活。',
  'first':'ghl-000026'},
]
def board_entries(n):
 es=[e for e in entries.values() if e['board']==n]
 es=sorted(es,key=lambda e:(e['date'] or '0000',e['id']),reverse=True)
 es.sort(key=lambda e:0 if 'video' in e else 1)
 return es
css='''*{box-sizing:border-box}
:root{--bg:#f3ecd9;--ink:#1b2f3c;--sub:#44545f;--card:#fffaf0;--card2:#f7efdb;--line:#d8cba6;--gold:#8a6a24;--gold2:#7c5c13;--chip:#fffaf0;--shadow:rgba(90,70,20,.18)}
html.dark{--bg:#0a141f;--ink:#ede4cd;--sub:#a7b5ba;--card:#101f2c;--card2:#0e1e2e;--line:#2c4353;--gold:#c9a55f;--gold2:#f0d48a;--chip:transparent;--shadow:rgba(0,0,0,.4)}
html{scroll-behavior:smooth}
body{margin:0;background:var(--bg);color:var(--ink);font-family:"PingFang SC","Microsoft YaHei",sans-serif;overflow-x:hidden;transition:background .4s,color .4s}
body{background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 52'%3E%3Cg fill='none' stroke='%23c9a55f' stroke-opacity='.032' stroke-width='2'%3E%3Cpath d='M32 6C39 17 39 27 32 37C25 27 25 17 32 6Z'/%3E%3Cpath d='M15 13C23 19 25 29 23 38C15 34 11 23 15 13Z'/%3E%3Cpath d='M49 13C41 19 39 29 41 38C49 34 53 23 49 13Z'/%3E%3Cpath d='M8 44C20 49 44 49 56 44'/%3E%3C/g%3E%3C/svg%3E");background-size:168px auto}
html.dark body{background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 52'%3E%3Cg fill='none' stroke='%23c9a55f' stroke-opacity='.026' stroke-width='2'%3E%3Cpath d='M32 6C39 17 39 27 32 37C25 27 25 17 32 6Z'/%3E%3Cpath d='M15 13C23 19 25 29 23 38C15 34 11 23 15 13Z'/%3E%3Cpath d='M49 13C41 19 39 29 41 38C49 34 53 23 49 13Z'/%3E%3Cpath d='M8 44C20 49 44 49 56 44'/%3E%3C/g%3E%3C/svg%3E")}
a{color:inherit;text-decoration:none}
button{font:inherit;cursor:pointer}
::selection{background:#c9a55f;color:#101f2c}
header{position:fixed;inset:0 0 auto 0;z-index:60;display:flex;justify-content:space-between;align-items:center;padding:16px max(4vw,20px);transition:transform .38s ease,opacity .38s ease,background .35s ease,box-shadow .35s ease}
header.solid{background:rgba(243,236,217,.88);-webkit-backdrop-filter:blur(14px) saturate(1.25);backdrop-filter:blur(14px) saturate(1.25);box-shadow:0 10px 30px rgba(90,70,20,.10);border-bottom:1px solid rgba(216,203,166,.7)}
html.dark header.solid{background:rgba(10,20,31,.86);border-bottom-color:rgba(44,67,83,.8);box-shadow:0 10px 30px rgba(0,0,0,.35)}
header.hidden{transform:translateY(-115%);opacity:0;pointer-events:none}
header .brand,header nav a{text-shadow:0 1px 12px rgba(4,10,16,.35),0 0 3px rgba(4,10,16,.18)}
html.dark header .brand,html.dark header nav a{text-shadow:0 1px 12px rgba(4,10,16,.9),0 0 3px rgba(4,10,16,.65)}
html:not(.dark) header .brand,html:not(.dark) header nav a{text-shadow:0 1px 12px rgba(250,244,226,.95),0 0 3px rgba(250,244,226,.9)}
header.over-hero .brand img,header.over-hero nav a .navimg{filter:drop-shadow(0 2px 12px rgba(0,0,0,.62))}
html:not(.dark) header.over-hero .brand img,html:not(.dark) header.over-hero nav a .navimg{filter:drop-shadow(0 2px 12px rgba(0,0,0,.62))}
header.over-hero + #theme-toggle{color:#f3ecd9;border-color:rgba(243,236,217,.55)}
.brand{font-family:"STXingkai","华文行楷","Xingkai SC","Kaiti SC","STKaiti","KaiTi",serif;font-size:29px;font-weight:700;display:block;width:160px;color:var(--ink)}
.brand img{display:block}
.brand .bimg1{width:100%;height:auto;display:block}
.brand .bimg2{width:100%;height:auto;display:block;margin-top:4px}
html:not(.dark) .brand img{filter:invert(1) brightness(.85)}
nav{display:flex;gap:16px;align-items:center}
nav a{opacity:.92;font-family:"Songti SC","STSong",SimSun,serif;font-size:16.5px;font-weight:700;letter-spacing:2.5px;position:relative;color:var(--ink);padding:7px 13px;border:1px solid transparent;border-radius:999px;transition:border-color .25s ease,background .25s ease}
nav a .navimg{height:26px;width:auto;display:block}
html:not(.dark) nav a .navimg{filter:invert(1) brightness(.82)}
nav a:hover{opacity:1;border-color:rgba(201,165,95,.9);background:rgba(201,165,95,.22);box-shadow:0 0 0 1px rgba(201,165,95,.35),0 4px 14px rgba(0,0,0,.18)}
#theme-toggle{position:fixed;top:42px;right:max(4vw,20px);z-index:65;border:1px solid #b6a378;background:transparent;color:var(--ink);border-radius:999px;width:48px;height:32px;display:grid;place-items:center;padding:0;line-height:1;cursor:pointer}#theme-toggle svg{display:block}.theme-slot{width:48px;height:32px;flex:none}
#to-top{position:fixed;right:22px;bottom:22px;z-index:55;background:#c9a55f;color:#101f2c;border:0;border-radius:999px;padding:12px 17px;font-weight:700;box-shadow:0 10px 26px rgba(0,0,0,.3)}
.hero{position:relative;min-height:100svh;display:grid;place-items:center;text-align:center;overflow:hidden}
.hero .bg{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;animation:kb 30s ease-in-out infinite alternate}
@keyframes kb{from{transform:scale(1.02)}to{transform:scale(1.10)}}
.hero::before{content:'';position:absolute;inset:0;background:linear-gradient(180deg,rgba(4,10,16,.34),rgba(4,10,16,0) 26%),radial-gradient(ellipse at 50% 42%,rgba(0,0,0,0) 30%,rgba(4,10,16,.38) 100%);z-index:1}
.hero .bg,.hero .rays,.hero .dust,.hero::before{-webkit-mask-image:linear-gradient(180deg,#000 74%,transparent 98%);mask-image:linear-gradient(180deg,#000 74%,transparent 98%)}
.hero .rays{position:absolute;inset:0;z-index:1;pointer-events:none;opacity:0;background:conic-gradient(from 180deg at 50% -12%,transparent 40%,rgba(255,214,120,.30) 47%,rgba(255,226,150,.42) 50%,rgba(255,214,120,.30) 53%,transparent 60%),conic-gradient(from 180deg at 50% -12%,transparent 30%,rgba(255,220,140,.20) 36%,transparent 43%),conic-gradient(from 180deg at 50% -12%,transparent 58%,rgba(255,220,140,.20) 64%,transparent 71%),radial-gradient(ellipse 62% 34% at 50% 0%,rgba(255,222,140,.5),transparent 70%);filter:blur(12px);animation:sway 11s ease-in-out infinite alternate,pulse 6.5s ease-in-out infinite alternate;transition:opacity 1.2s}
html:not(.dark) .hero .rays{opacity:.85}
@keyframes sway{from{transform:rotate(-1.6deg) scale(1.15)}to{transform:rotate(1.6deg) scale(1.15)}}
@keyframes pulse{from{filter:blur(12px) brightness(1)}to{filter:blur(12px) brightness(1.28)}}
.hero .dust{position:absolute;inset:0;z-index:1;pointer-events:none}
.hero .dust span{position:absolute;border-radius:50%;background:radial-gradient(circle,rgba(255,230,160,.95),rgba(255,230,160,0) 70%);animation:floatup linear infinite}
@keyframes floatup{from{transform:translateY(26px);opacity:0}18%{opacity:.9}82%{opacity:.7}to{transform:translateY(-120px);opacity:0}}
.hero-seal{position:absolute;top:86px;right:4vw;width:clamp(56px,7vw,92px);z-index:4;filter:drop-shadow(0 8px 22px rgba(0,0,0,.4))}
.hero .inner{position:relative;padding:120px 20px 90px;max-width:900px;z-index:3}
.hero h1{margin:10px 0 6px;line-height:1.1}
.hero h1 img{height:clamp(100px,16.5vw,168px);width:auto;max-width:88vw;filter:drop-shadow(0 6px 44px rgba(0,0,0,.55))}
html:not(.dark) .hero h1 img{filter:invert(1) brightness(.88) drop-shadow(0 0 26px rgba(255,236,170,.9))}
.title-img{display:block}
.part h2 .title-img{height:clamp(50px,7vw,80px);width:auto;max-width:100%;margin:0 auto}
html:not(.dark) .part h2 .title-img{filter:invert(1) brightness(.82)}
.board-hero h1 .title-img{height:clamp(58px,8.5vw,96px);width:auto;max-width:100%;margin:0 auto}
html:not(.dark) .board-hero h1 .title-img{filter:invert(1) brightness(.82)}
.hero .sub{position:relative;color:#f8f0d4;font-size:clamp(15.5px,2.05vw,19.5px);line-height:2.05;font-weight:500;background:linear-gradient(165deg,rgba(9,16,25,.78),rgba(9,16,25,.56));backdrop-filter:blur(9px) saturate(1.15);-webkit-backdrop-filter:blur(9px) saturate(1.15);border:1px solid rgba(230,197,120,.5);border-radius:16px;padding:30px 42px 24px;box-shadow:0 26px 60px rgba(0,0,0,.5),0 0 90px rgba(240,205,120,.10),inset 0 1px 0 rgba(255,240,200,.14);text-shadow:0 1px 2px rgba(8,12,6,.9)}
.hero .sub::before{content:'';position:absolute;inset:7px;border:1px solid rgba(230,197,120,.30);border-radius:10px;pointer-events:none}
.hero .sub .hl{position:relative;z-index:1}
.hero .sub .cnr{position:absolute;width:36px;height:36px;color:rgba(230,197,120,.9);pointer-events:none;z-index:2}
.hero .sub .cnr svg{width:100%;height:100%;display:block}
.hero .sub .cnr.tl{top:5px;left:5px}
.hero .sub .cnr.tr{top:5px;right:5px;transform:scaleX(-1)}
.hero .sub .cnr.bl{bottom:5px;left:5px;transform:scaleY(-1)}
.hero .sub .cnr.br{bottom:5px;right:5px;transform:scale(-1,-1)}
.hero .sub .lotus-chip{position:absolute;top:-14px;left:50%;transform:translateX(-50%);background:#0d1826;border:1px solid rgba(230,197,120,.55);border-radius:999px;padding:5px 13px 3px;line-height:0;z-index:3}
.hero .sub .lotus-chip svg{height:17px;width:auto;display:block}
.hero .sub .lotus-bg{position:absolute;inset:0;display:flex;align-items:center;justify-content:center;pointer-events:none;opacity:.08;z-index:0}
.hero .sub .lotus-bg svg{height:225px;width:auto}
.hero .sub .hl:first-child{font-size:1.15em;font-weight:700;letter-spacing:.05em;color:#fdf6dd}
.hero .sub .hl span{color:#f0cd7d;font-weight:700}
.hero .sub .hl:last-child{font-size:.94em;letter-spacing:.22em;color:#eadfc0}
.hl{display:block}
.cta{margin-top:30px;display:flex;gap:14px;justify-content:center;flex-wrap:wrap}
.btn{display:inline-block;border:1px solid #c9a55f;padding:13px 26px;border-radius:999px;background:rgba(10,20,31,.42);color:#f0d48a;font-weight:700;font-family:"Songti SC","STSong",SimSun,serif;letter-spacing:.1em;transition:transform .25s ease,filter .25s ease,background .25s ease}
.btn.ghost{background:rgba(10,20,31,.42);color:#f0d48a}
.btn:hover{transform:translateY(-2px);filter:brightness(1.07);background:rgba(201,165,95,.18)}
.scrollcue{display:inline-flex;align-items:center;gap:12px;margin-top:46px;padding:14px 30px;border:1px solid rgba(201,165,95,.75);border-radius:999px;background:rgba(10,20,31,.42);color:#f0d48a;font-size:17px;letter-spacing:6px;font-family:"Songti SC","STSong",SimSun,serif;font-weight:700;box-shadow:0 10px 30px rgba(0,0,0,.35);transition:transform .25s ease}
.scrollcue:hover{transform:translateY(-2px)}
.scrollcue .arr{animation:bob 1.8s ease-in-out infinite}
@keyframes bob{0%,100%{transform:translateY(0)}50%{transform:translateY(5px)}}
main{max-width:1180px;margin:0 auto;padding:10px 22px 30px}
.intro{max-width:760px;margin:56px auto 0;text-align:center}
.intro p{font-size:17.5px;line-height:2.1;color:var(--sub);font-family:"Songti SC","STSong",SimSun,serif}
.intro p.lede{position:relative;font-size:clamp(17px,2.3vw,20.5px);line-height:1.95;color:var(--ink);padding-top:30px}
.intro p.lede::after{content:'';position:absolute;top:7px;left:50%;transform:translateX(-50%);width:min(360px,72%);height:1px;background:linear-gradient(90deg,transparent,var(--line) 20%,var(--line) 80%,transparent)}
.intro p.lede::before{content:'◆';position:absolute;top:0;left:50%;transform:translateX(-50%);color:var(--gold);font-size:11px;background:var(--bg);padding:0 12px;z-index:1;line-height:1.4}
.searchbar{display:flex;gap:10px;max-width:560px;margin:26px auto 0}
.searchbar input{flex:1;padding:14px 18px;border:1px solid var(--line);border-radius:999px;background:var(--card);color:var(--ink);font-size:15px}
.searchbar button{border:1px solid #c9a55f;background:#c9a55f;color:#101f2c;border-radius:999px;padding:0 22px;font-weight:600}
.qchips{display:flex;gap:8px;flex-wrap:wrap;justify-content:center;align-items:center;margin-top:14px}
.qchips-lab{font-size:13px;color:var(--sub)}
.qchips button{border:1px solid var(--line);background:var(--card);color:var(--ink);border-radius:999px;padding:6px 14px;font-size:13.5px;cursor:pointer;transition:opacity .45s ease}
.qchips.fading button{opacity:0}
.qchips button:hover{border-color:var(--gold);color:var(--gold2)}
.sresults{max-width:680px;margin:14px auto 0;text-align:left}
.sresults .hit{display:block;padding:11px 14px;border:1px solid var(--line);border-radius:10px;margin-top:8px;background:var(--card)}
.sresults .hit b{font-weight:600}
.sresults .hit span{display:block;font-size:12.5px;color:var(--sub);margin-top:3px;line-height:1.6}
.sresults .none{color:var(--sub);font-size:14px;text-align:center;padding:8px}
.part{display:grid;grid-template-columns:1.15fr 1fr;gap:clamp(22px,4vw,54px);margin-top:110px;align-items:start;scroll-margin-top:84px;position:relative}
.part.flip{grid-template-columns:1fr 1.15fr}
.part ~ .part::after{content:'';position:absolute;top:-58px;left:50%;transform:translateX(-50%);width:min(430px,62%);height:1px;background:linear-gradient(90deg,transparent,rgba(201,165,95,.55),transparent)}
.artwrap{position:sticky;top:96px;z-index:1}.part .art{position:relative}.part .wm{display:none}
html:not(.dark) .part .wm{filter:invert(1) brightness(.85);opacity:.24}
.part.flip .wm{grid-column:2}
.part .art{position:relative;border-radius:18px;overflow:hidden;box-shadow:0 24px 60px var(--shadow);z-index:1;background:#0d1826;min-height:180px}
.part .art::after{content:'';position:absolute;inset:11px;border:1px solid rgba(240,212,138,.38);border-radius:9px;pointer-events:none}
.part .art img{display:block;width:100%;height:auto}
.reveal .art img{transform:scale(1.045);transition:transform 1.4s ease}
.reveal.in .art img{transform:scale(1)}
.part .art:hover img{transform:scale(1.03)}
.part .txt{align-self:center;position:relative;z-index:1}
.part .tag{display:inline-block;border:1px solid var(--gold);color:var(--gold2);background:var(--chip);border-radius:999px;padding:5px 13px;font-size:12px;letter-spacing:2px;font-weight:600}
.part .txt .tag{position:absolute;top:-12px;left:50%;transform:translateX(-50%);background:var(--card);white-space:nowrap;z-index:2}
.part h2{font-family:"STXingkai","华文行楷","Xingkai SC","Kaiti SC","STKaiti","KaiTi",serif;font-weight:600;font-size:clamp(42px,6vw,68px);letter-spacing:.06em;margin:16px 0 6px;line-height:1.15}
.part h2{text-align:center}
.part .plain{font-size:clamp(19px,2.6vw,24px);color:var(--gold2);line-height:1.6;font-family:"Songti SC",SimSun,serif;text-align:center}
.part .txt{border:1px solid var(--line);border-radius:18px;padding:clamp(32px,3.8vw,44px) clamp(24px,3.2vw,38px) clamp(24px,3.2vw,38px);background:var(--card);box-shadow:0 18px 44px var(--shadow)}
.part .art{box-shadow:0 0 0 1px var(--line),0 24px 60px var(--shadow)}
.part .desc{color:var(--sub);line-height:2;font-size:15.5px}
.part .desc .dropcap{float:left;height:52px;width:auto;margin:4px 10px 0 0}
html:not(.dark) .part .desc .dropcap{filter:invert(1) brightness(.82)}
.firstread{background:var(--card);border:1px solid var(--line);border-left:3px solid #c9a55f;border-radius:12px;padding:18px 20px;margin-top:20px;transition:transform .35s ease,border-color .35s ease,box-shadow .35s ease}
.firstread:hover{transform:translateY(-3px);border-color:rgba(201,165,95,.7);box-shadow:0 16px 36px var(--shadow)}
.firstread .lab{color:var(--gold2);font-size:12px;letter-spacing:2px;margin-bottom:8px;font-weight:600}
.firstread h3{margin:0 0 8px;font-size:18.5px;line-height:1.55}
.firstread p{margin:0;color:var(--sub);font-size:14px;line-height:1.85}
.casewall{margin-top:12px;display:flex;flex-wrap:wrap;gap:8px}
.casewall button{border:1px solid var(--line);background:var(--chip);color:var(--gold2);border-radius:999px;padding:7px 13px;font-size:13px;font-weight:600}
.casewall button.on{background:#f3e5bd;border-color:#c9a55f;color:#7c5c13}
html.dark .casewall button.on{background:#243843;color:#f0d48a}
.rot-fade{transition:opacity .45s ease}
.rot-fade.out{opacity:0}
.rot-open{margin-top:10px;background:none;border:0;color:var(--gold2);font-size:14.5px;padding:0;font-weight:600}
.doors{margin-top:20px;display:flex;gap:10px;flex-wrap:wrap;justify-content:center}
.doors a{border:1px solid var(--line);border-radius:999px;padding:9px 16px;font-size:13.5px;color:var(--gold2);background:var(--chip);font-weight:600}
.stage{position:relative;aspect-ratio:16/9;background:#183544;border-radius:10px;overflow:hidden;margin-top:10px}
.stage>button{position:absolute;inset:0;width:100%;height:100%;padding:0;border:0;background:#183544;cursor:pointer}
.stage>button img{width:100%;height:100%;object-fit:cover;display:block}
.stage .play{position:absolute;left:50%;top:50%;transform:translate(-50%,-50%);width:54px;height:54px;border-radius:50%;background:rgba(201,165,95,.94);color:#101f2c;display:grid;place-items:center;font-size:20px}
.stage iframe{width:100%;height:100%;border:0;display:block}
.vopen{margin:9px 2px 0;color:var(--sub);font-size:13.5px}
.vopen a{color:var(--gold2);text-decoration:underline;text-underline-offset:3px}
.vibechips{display:flex;gap:8px;flex-wrap:wrap;margin-top:12px}
.vibechips button{border:1px solid var(--line);background:var(--chip);color:var(--gold2);border-radius:999px;padding:7px 13px;font-size:13px;font-weight:600}
.vibechips button.on{background:#f3e5bd;border-color:#c9a55f;color:#7c5c13}
html.dark .vibechips button.on{background:#243843;color:#f0d48a}
.boardlist{margin-top:22px;border-top:1px solid var(--line)}
.boardlist .first{margin-top:16px}
.boardlist h4{margin:20px 0 4px;font-size:13px;letter-spacing:2px;color:var(--gold);font-weight:600}
.alist a{display:flex;justify-content:space-between;gap:14px;padding:10px 4px;border-bottom:1px solid var(--line);font-size:15px;line-height:1.6}
.alist a:hover{color:var(--gold2)}
.alist .tx{display:flex;flex-direction:column;gap:2px;min-width:0}
.alist .hook{color:var(--sub);font-size:13px;line-height:1.55}
.alist .vchip{cursor:pointer;display:inline-block;background:#a52a21;color:#fff;font-size:11px;line-height:1;padding:3px 8px;border-radius:999px;margin-left:8px;vertical-align:2px;white-space:nowrap;letter-spacing:1px}
.alist .d{color:var(--sub);font-size:12.5px;white-space:nowrap;padding-top:3px;text-align:right}
.more{display:inline-block;margin-top:16px;border:1px solid #c9a55f;color:var(--gold2);border-radius:999px;padding:10px 20px;font-size:14px;background:var(--chip)}
.library{scroll-margin-top:84px;margin:120px auto 0;max-width:1180px;border:1px solid var(--line);border-radius:18px;padding:clamp(26px,4vw,44px);background:linear-gradient(135deg,var(--card2),var(--card));display:grid;grid-template-columns:1.25fr 1fr;gap:26px;align-items:center}
.library h2{font-family:"Songti SC",SimSun,serif;font-size:clamp(24px,3.4vw,34px);margin:0 0 10px}
.library p{color:var(--sub);line-height:1.95;margin:0}
.library .years{display:grid;grid-template-columns:1fr 1fr;gap:10px}
.library .years a{border:1px solid var(--line);border-radius:12px;padding:15px;text-align:center;background:var(--card)}
.library .years b{display:block;font-size:19px;margin-bottom:3px}
.library .years span{font-size:12px;color:var(--sub)}
.board-hero{max-width:1180px;margin:0 auto;padding:130px 22px 0;text-align:center}
.board-hero .board-art{background:#0d1826;width:min(880px,100%);max-height:330px;object-fit:cover;border-radius:18px;margin:24px auto 4px;display:block;box-shadow:0 24px 60px var(--shadow)}
.topics-h1{font-family:"STXingkai","华文行楷","Xingkai SC","Kaiti SC","STKaiti","KaiTi",serif;font-size:clamp(42px,6vw,60px);margin:14px 0 6px}
.topic{margin:46px 0 8px}
.topic h2{font-family:"Songti SC","STSong",SimSun,serif;font-size:clamp(22px,3vw,28px);margin:0 0 4px}
.topic .tdesc{color:var(--sub);margin:0 0 8px;line-height:1.8}
.board-hero h1{font-family:"STXingkai","华文行楷","Xingkai SC","Kaiti SC","STKaiti","KaiTi",serif;font-size:clamp(46px,7vw,76px);margin:14px 0 8px;letter-spacing:.06em}
.board-hero .plain{font-size:clamp(18px,2.4vw,23px);color:var(--gold2);font-family:"Songti SC",SimSun,serif;line-height:1.6}
.board-hero p{color:var(--sub);line-height:2;max-width:720px;margin:14px auto 0}
.board-main{max-width:900px;margin:0 auto;padding:26px 22px 20px}
.board-main .alist a{font-size:16.5px;padding:13px 4px}
footer{text-align:center;color:var(--sub);font-size:12.5px;padding:44px 10px 50px;position:relative}
::selection{background:rgba(201,165,95,.32)}
html{scrollbar-color:rgba(201,165,95,.55) transparent}
::-webkit-scrollbar{width:10px;height:10px}
::-webkit-scrollbar-thumb{background:rgba(201,165,95,.45);border-radius:8px}
::-webkit-scrollbar-track{background:transparent}
.foot-orn{display:flex;align-items:center;gap:12px;justify-content:center;margin:0 auto 18px;color:#b3862c;max-width:420px}
.foot-orn i{flex:1;height:1px;background:linear-gradient(90deg,transparent,var(--line))}
.foot-orn i:last-child{background:linear-gradient(90deg,var(--line),transparent)}
html.dark .foot-orn{color:#e6c578}
.orn-div{display:flex;align-items:center;gap:14px;justify-content:center;max-width:760px;margin:26px auto 6px;padding:0 22px;color:#b3862c}
.orn-div i{flex:1;height:1px;background:linear-gradient(90deg,transparent,var(--line))}
.orn-div i:last-child{background:linear-gradient(90deg,var(--line),transparent)}
html.dark .orn-div{color:#e6c578}\n.partdiv{display:flex;align-items:center;gap:clamp(16px,2.6vw,40px);margin:clamp(28px,3.6vw,50px) 0 -34px;color:#b3862c}\nhtml.dark .partdiv{color:#e6c578}\n.pd-plate{flex:1 1 0;min-width:0;line-height:0}\n.pd-plate svg{width:100%;height:auto;display:block}\n.pd-plate.flip{transform:scaleX(-1)}\n.pd-wm{height:clamp(168px,18vw,236px);width:auto;opacity:.3;user-select:none}\nhtml:not(.dark) .pd-wm{filter:invert(1) brightness(.82);opacity:.34}\n@media(max-width:820px){.partdiv{display:none}}
.footwm{user-select:none}
.footwm img{height:clamp(80px,12vw,150px);width:auto;opacity:.16}
html:not(.dark) .footwm img{filter:invert(1) brightness(.85);opacity:.13}
.flinks{margin:14px 0 10px;display:flex;gap:10px;justify-content:center;flex-wrap:wrap}
.flinks a{border:1px solid var(--gold);color:var(--gold2);background:var(--chip);border-radius:999px;padding:9px 16px;font-size:13.5px}
dialog{max-width:720px;width:calc(100% - 32px);max-height:85vh;border:0;background:var(--card);padding:32px;color:var(--ink);border-radius:14px}
dialog::backdrop{background:rgba(9,18,28,.72)}
dialog p{line-height:2}
dialog .src{color:var(--sub);font-size:12.5px;border-top:1px solid var(--line);padding-top:10px}
#close{border:1px solid var(--line);background:transparent;color:var(--ink);border-radius:999px;padding:8px 15px}
.reveal{opacity:0;transform:translateY(26px);transition:opacity .9s ease,transform .9s ease;animation:revealSafe .8s ease 1.6s forwards}
@keyframes revealSafe{to{opacity:1;transform:none}}
.reveal.in{opacity:1;transform:none}
[hidden]{display:none!important}
a:focus-visible,button:focus-visible{outline:3px solid #aa8036;outline-offset:3px}
@media(prefers-reduced-motion:reduce){.hero .rays{animation:none}.scrollcue .arr{animation:none}.hero .bg{animation:none}.hero .dust span{animation:none}.reveal{transition:none;opacity:1;transform:none}}
@media(max-width:820px){.part,.part.flip{grid-template-columns:1fr}.part .art{position:static}.artwrap{position:static;order:-1}.part .wm,.part.flip .wm{display:block;position:absolute;top:-140px;bottom:auto;left:auto;right:10px;height:150px;transform:none;margin:0}.part .txt{text-align:center}.part .firstread{text-align:left}.part .doors{justify-content:center}.library{grid-template-columns:1fr;text-align:center}.brand{font-size:20px;width:134px}header{flex-wrap:wrap;row-gap:4px}nav{order:3;width:100%;flex-wrap:nowrap;justify-content:space-between;gap:6px;margin-top:2px}nav a{font-size:12.5px;letter-spacing:1px}nav a .navimg{height:19px;width:auto}.themebtn{margin-left:auto}header.over-hero{background:linear-gradient(180deg,rgba(8,12,18,.40),rgba(8,12,18,0))}.board-hero{padding-top:158px}.hero-seal{top:118px}.hero .sub{font-size:14.5px;padding:24px 18px 18px}}
@media(max-width:820px){nav a .navimg{height:17.5px}nav a{padding:5px 4px}#theme-toggle{position:fixed;top:15px;right:16px;margin:0}.theme-slot{display:none}}
'''
(out/'reading.css').write_text(css,encoding='utf-8')
def article_href(article_id):
 e=entries.get(article_id)
 return (e['page']+'#'+article_id) if e else ('all.html#'+article_id)
LARK='https://u78zyhf3gaz.jp.larksuite.com/docx/QKYtdsvHzoH1aIxuGhrjD81EpWf'
def shell(title,body,home=False):
 seo=''
 if home:
  canonical='https://guihailu.github.io/'
  ld=json.dumps({'@context':'https://schema.org','@type':'WebSite','name':'归海录 · 志远行空','url':canonical,'description':'归海录：志远行空的公开分享与 YouTube 视频讲法合集','inLanguage':'zh-CN'},ensure_ascii=False)
  seo=('<link rel="canonical" href="'+canonical+'">'
       '<meta property="og:url" content="'+canonical+'">'
       '<meta property="og:image" content="https://guihailu.github.io/cover.jpg">'
       '<meta name="twitter:card" content="summary_large_image">'
       '<script type="application/ld+json">'+ld+'</script>')
 navp='' if home else 'index.html'
 nav=''.join(f'<a href="{navp}#part{b["n"]}" aria-label="{b["name"]}"><img class="navimg" src="{NAVTITLES[b["n"]]}" alt="{b["name"]}"></a>' for b in BOARDS)
 return ('<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
 '<title>'+esc(title)+'</title>'
 f'<link rel="icon" type="image/png" href="{FAVICON}">'
 f'<meta name="description" content="{SITEDESC}">'
 f'<meta property="og:type" content="website"><meta property="og:site_name" content="归海录"><meta property="og:title" content="{esc(title)}"><meta property="og:description" content="{SITEDESC}">'
 +seo+
 '<script>try{var t=localStorage.getItem(\'ghl_theme\');if(t===\'dark\'||(!t&&window.matchMedia(\'(prefers-color-scheme: dark)\').matches))document.documentElement.classList.add(\'dark\')}catch(e){}</script>'
 '<link rel="stylesheet" href="reading.css?v=20261112p19"></head><body>'
 f'<header><a class="brand" href="index.html" aria-label="归海录 首页"><img class="bimg1" src="{TITLE_GUIHAI}" alt="归海录">'
 f'<img class="bimg2" src="{TITLE_SUB}" alt="志远行空·讲课整理"></a>'
 '<nav>'+nav+'<a href="all.html" aria-label="资料库"><img class="navimg" src="'+NAVLIB+'" alt="资料库"></a><span class="theme-slot" aria-hidden="true"></span></nav></header><button id="theme-toggle" type="button" aria-label="切换晚上模式"><svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg></button>'
 +body+
 f'<footer><div class="foot-orn"><i></i>'+_LOTUS_CC+'<i></i></div>'+f'<div class="footwm" aria-hidden="true"><img src="{TITLE_GUIHAI}" alt="" width="220" loading="lazy"></div><div class="flinks"><a href="'+LARK+'" target="_blank" rel="noopener">📿 归海录 · Lark 源文档</a></div>归海录 · 志远行空公开分享整理</footer>'
 '<button id="to-top" type="button" aria-label="回到顶部" hidden>↑ 顶部</button>'
 '<dialog id="reader"><button id="close" type="button">关闭阅读 ×</button><h2 id="reader-title"></h2><div id="reader-body"></div><p class="src">这里是故事梗概，完整原文在资料库里。</p></dialog>'
 '<script src="reading.js?v=20261112p19"></script></body></html>')
def alist_rows(es):
 rows=''
 for e in es:
  meta_line=f'{esc(e["date"])}<br>约 {e["mins"]} 分钟' if e['date'] else f'约 {e["mins"]} 分钟'
  chip=('<span class="vchip" data-v="'+article_href(e["id"])+'-video" role="link" tabindex="0">▶ 有视频</span>') if 'video' in e else ''
  rows+=f'<a href="{article_href(e["id"])}"><span class="tx"><span>{esc(e["title"])}{chip}</span><span class="hook">{esc(e["hook"])}</span></span><span class="d">{meta_line}</span></a>'
 return rows
def rotator(start):
 return (f'<div data-rot data-start="{start}"><div class="lab">故事案例 · 一则接一则随机播</div>'
 '<h3 class="rot-title rot-fade"></h3><p class="rot-intro rot-fade"></p>'
 '<button class="rot-open" type="button">看看这个故事 →</button>'
 '<div class="casewall"></div></div>')
vibes=json.loads((src/'vibe_cards.json').read_text(encoding='utf-8'))['cards']
vibes=sorted((c for c in vibes if c.get('status')=='published' and c.get('youtube_url')),key=lambda x:x['published_at'])
clips=json.loads((src/'video_cards.json').read_text(encoding='utf-8'))['cards']
clips=sorted((c for c in clips if c.get('status')=='published' and c.get('youtube_url')),key=lambda x:x['published_at'],reverse=True)
# 文章↔Vibe视频对照（逐条按标题/正文核对后写死；新增视频先核对再加行，勿自动猜配）
VIDEO_MAP={'ghl-000018':('li_zfTRp690','卡车司机理论'),'ghl-000004':('jvRbI_nnxxM','聪明人走进死局'),'ghl-000022':('boVkmwiauS4','人生如棋，别做那个臭棋篓子'),'ghl-000026':('q6wj4WzT1XE','选择大于努力')}
_vibe_urls={c['youtube_url'].rsplit('/',1)[-1] for c in vibes}
for _eid,(_vid,_vt) in VIDEO_MAP.items():
 assert _vid in _vibe_urls,'VIDEO_MAP video not in published vibe cards: '+_vid
 assert _eid in entries,'VIDEO_MAP unknown article: '+_eid
 entries[_eid]['video']=(_vid,_vt)
def vid_of(c):return c['youtube_url'].rstrip('/').split('/')[-1].split('?')[0]
def poster_of(c):
 v=vid_of(c)
 return c.get('poster') or ('https://i.ytimg.com/vi/'+v+'/hqdefault.jpg')
# p17 失效兜底：外站海报（i.ytimg.com）加载失败时换成本地归海印章，不留破图；data-fb 防兜底图自身失败时死循环。
POSTER_FB=' onerror="if(!this.dataset.fb){this.dataset.fb=1;this.src=\''+SEAL_IMG+'\'}"'
def video_block():
 c=clips[0];v=vid_of(c)
 return ('<div class="lab">讲课原声 · 先听一段</div>'
 f'<h3>《{esc(c["title"])}》· 志远行空原声</h3><p>{esc(c.get("description",""))}</p>'
 f'<div class="stage" id="clip-stage"><button type="button" data-video="{v}" aria-label="播放：{esc(c["title"])}"><img src="{poster_of(c)}" alt="" loading="lazy"{POSTER_FB}><span class="play">▶</span></button></div>'
 f'<p class="vopen">这里播不了的话，<a href="https://youtu.be/{v}" target="_blank" rel="noopener">去 YouTube 看这一条 ↗</a></p>')
def vibe_block():
 c0=vibes[0];v0=vid_of(c0)
 chips=''.join(f'<button type="button" data-vibe="{vid_of(c)}" data-t="{esc(c["title"])}"{" class=\"on\"" if i==0 else ""}>《{esc(c["title"])}》</button>' for i,c in enumerate(vibes))
 return ('<div class="lab">知识大赏 · 小动画</div>'
 f'<h3 id="vibe-title">《{esc(c0["title"])}》</h3>'
 f'<div class="stage" id="vibe-stage"><button type="button" data-video="{v0}" aria-label="播放：{esc(c0["title"])}"><img src="{poster_of(c0)}" alt="" loading="lazy"{POSTER_FB}><span class="play">▶</span></button></div>'
 f'<p class="vopen">这里播不了的话，<a id="vibe-open" href="https://youtu.be/{v0}" target="_blank" rel="noopener">去 YouTube 看这一条 ↗</a></p>'
 f'<div class="vibechips">{chips}</div>')
def first_block(b):
 if b['n']==1:return rotator(3)
 if b['n']==2:return rotator(5)
 if b['n']==3:return video_block()
 return vibe_block()
def doors(b):
 if b['n']==1:return '<a href="#part1" data-shuffle>换一则案例</a><a href="#library">本部原文（资料库）</a>'
 if b['n']==2:return '<a href="#part2" data-shuffle>换一则案例</a><a href="#part3">听一段原声</a>'
 if b['n']==3:return '<a href="#part3" data-replay>再播一遍</a><a href="clips.html">切片合集</a>'
 return '<a href="#library">本部原文（资料库）</a><a href="#part1">回到第一部</a>'
def part_section(b):
 es=board_entries(b['n'])
 fe=entries[b['first']]
 fechip=('<span class="vchip" data-v="'+article_href(fe["id"])+'-video" role="link" tabindex="0">▶ 有视频</span>') if 'video' in fe else ''
 prev=[e for e in es if e['id']!=b['first']][:5]
 blist=('<div class="boardlist"><h4>本部文章 · 共 '+str(len(es))+' 篇</h4>'
 f'<div class="alist"><a href="{article_href(fe["id"])}"><span>从这一篇开始 · {esc(fe["title"])}{fechip}</span></a>'
 +alist_rows(prev)+'</div>'
 f'<a class="more" href="board{b["n"]}.html">本部全部 {len(es)} 篇 →</a></div>')
 txt=(f'<div class="txt"><span class="tag">第{b["cn"]}部</span><h2><img class="title-img" src="{TITLES[b["n"]]}" alt="{b["name"]}" loading="lazy"></h2>'
 f'<div class="plain">{b["plain"]}</div><p class="desc"><img class="dropcap" src="{TITLE_ZHE}" alt="" loading="lazy">{b["desc"][1:]}</p>'
 f'<div class="firstread">{first_block(b)}</div>'
 f'<div class="doors">{doors(b)}</div>{blist}</div>')
 art=f'<div class="artwrap"><div class="art"><img src="{b["img"]}" alt="{b["name"]}" loading="lazy"></div></div><img class="wm" src="{WMIMG[b["n"]]}" alt="" aria-hidden="true" loading="lazy">'
 inner=(txt+art) if b['n']%2==0 else (art+txt)
 cls='part flip reveal' if b['n']%2==0 else 'part reveal'
 return f'<section class="{cls}" id="part{b["n"]}">'+inner+'</section>'
_LOTUS_CC='<svg width="22" height="18" viewBox="0 0 64 52" fill="none" stroke="currentColor" stroke-width="3" stroke-linejoin="round" stroke-linecap="round"><path d="M32 6 C39 17 39 27 32 37 C25 27 25 17 32 6 Z"/><path d="M15 13 C23 19 25 29 23 38 C15 34 11 23 15 13 Z"/><path d="M49 13 C41 19 39 29 41 38 C49 34 53 23 49 13 Z"/><path d="M3 25 C11 27 15 33 16 40 C9 40 4 34 3 25 Z"/><path d="M61 25 C53 27 49 33 48 40 C55 40 60 34 61 25 Z"/><path d="M8 44 C20 49 44 49 56 44"/></svg>'
ORN_DIV='<div class="orn-div" aria-hidden="true"><i></i>'+_LOTUS_CC+'<i></i></div>'
_PD_PLATE='<svg viewBox="0 0 560 120" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><line x1="0" y1="57" x2="118" y2="57" stroke-width="1.4" opacity=".55"/><line x1="0" y1="64" x2="118" y2="64" stroke-width=".8" opacity=".35"/><path d="M138 51 l9 9 -9 9 -9 -9 Z" fill="currentColor" stroke="none" opacity=".85"/><circle cx="222" cy="60" r="31" stroke-width="2.2"/><path d="M222 29 V91 M191 60 H253 M200 38 L244 82 M244 38 L200 82" stroke-width="1.6"/><circle cx="222" cy="60" r="7" stroke-width="2"/><g transform="translate(322,33)" stroke-width="3"><path d="M32 6 C39 17 39 27 32 37 C25 27 25 17 32 6 Z"/><path d="M15 13 C23 19 25 29 23 38 C15 34 11 23 15 13 Z"/><path d="M49 13 C41 19 39 29 41 38 C49 34 53 23 49 13 Z"/><path d="M3 25 C11 27 15 33 16 40 C9 40 4 34 3 25 Z"/><path d="M61 25 C53 27 49 33 48 40 C55 40 60 34 61 25 Z"/><path d="M8 44 C20 49 44 49 56 44"/></g><g transform="translate(428,26) scale(1.55)" stroke-width="1.8"><path d="M18.5 18.5 q6.5 0 6.5 6.5 q0 5.5 -5.5 5.5 q-4.5 0 -4.5 -4.5 q0 -3.5 3.5 -3.5"/></g><path d="M492 51 l9 9 -9 9 -9 -9 Z" fill="currentColor" stroke="none" opacity=".85"/><line x1="512" y1="57" x2="560" y2="57" stroke-width="1.4" opacity=".55"/><line x1="512" y1="64" x2="560" y2="64" stroke-width=".8" opacity=".35"/></svg>'
def part_divider(b):
    return f'<div class="partdiv" aria-hidden="true"><span class="pd-plate">{_PD_PLATE}</span><img class="pd-wm" src="{WMIMG[b["n"]]}" alt="" loading="lazy"><span class="pd-plate flip">{_PD_PLATE}</span></div>'
def board_page(b):
 es=board_entries(b['n'])
 body=(f'<section class="board-hero"><span class="tag">第{b["cn"]}部</span><h1><img class="title-img" src="{TITLES[b["n"]]}" alt="{b["name"]}"></h1>'
 f'<img class="board-art" src="{b["img"]}" alt="" loading="lazy">'
 f'<div class="plain">{b["plain"]}</div><p>{b["desc"]}</p>'
 f'<p>本部共 {len(es)} 篇：有视频版的排在前面，其余按时间从新到旧，点开就是完整原文。</p></section>'+ORN_DIV+
 f'<main class="board-main"><div class="alist">{alist_rows(es)}</div>'
 '<p style="margin-top:26px"><a class="more" href="index.html">← 回到首页</a> <a class="more" href="all.html">完整资料库 →</a></p></main>')
 return shell(f'归海录 · {b["name"]}',body)
PROBLEMS=[
 {'name':'钱和生意','desc':'赚钱、花钱、做生意栽过跟头，先看看这笔账在讲什么。','kw':['钱','财','生意','经商','创业','投资','股票','赚钱','老板','财富']},
 {'name':'工作和前途','desc':'换工作、考学、走仕途，卡住的时候先看清局势再动。','kw':['工作','职业','事业','跳槽','职场','上班','考试','高考','体制','当官','行业','转行','辞职','中年危机','适合干什么']},
 {'name':'家人和关系','desc':'父母、孩子、夫妻之间过不去的坎，先看看别人的故事。','kw':['父母','孩子','夫妻','婚姻','家庭','亲子','婆婆','子女','儿女']},
 {'name':'身体和心里','desc':'身体出了问题、心静不下来，讲清背后的道理再谈怎么办。','kw':['身体','生病','健康','癌症','医院','焦虑','失眠','情绪','脾气','抑郁']},
 {'name':'命运和选择','desc':'站在岔路口不知道怎么选，先看懂这盘棋再落子。','kw':['命运','改命','运气','选择','算命','占卜','八字','风水','大运','命里']},
]
def problem_entries(p):
 scored=[]
 for e in entries.values():
  th=sum(1 for k in p['kw'] if k in e['title'])
  tx=len({k for k in p['kw'] if k in e['text']})
  lead=len({k for k in p['kw'] if k in e['text'][:600]})
  s=3*th+tx
  if s>=3 and (th>=1 or s>=5):scored.append((s+lead,e['date'] or '0000',e))
 scored.sort(key=lambda x:(x[0],x[1]),reverse=True)
 es=[e for s,d,e in scored]
 es.sort(key=lambda e:0 if 'video' in e else 1)
 return es
def topics_page():
 secs=''
 for p in PROBLEMS:
  es=problem_entries(p)
  secs+=(f'<section class="topic"><h2>{p["name"]}</h2><p class="tdesc">{p["desc"]}这一类共选出 {len(es)} 篇，先读靠前的几篇。</p>'
  f'<div class="alist">{alist_rows(es[:12])}</div></section>')
 body=('<section class="board-hero"><span class="tag">资料库</span><h1 class="topics-h1">按问题找</h1>'
 '<p>不用先弄懂四部是什么。带着你现在最头疼的问题来，从下面挑一篇开始读，就是入口。</p></section>'
 f'<main class="board-main">{secs}'
 '<p style="margin-top:26px"><a class="more" href="index.html">← 回到首页</a> <a class="more" href="all.html">完整资料库 →</a></p></main>')
 return shell('归海录 · 按问题找',body)
search_entries=[]
for e in sorted(entries.values(),key=lambda x:x['id']):
 t=' '.join(meta.get(e['id'],{}).get('text','').split())[:240]
 search_entries.append({'id':e['id'],'t':e['title'],'p':e['page'],'d':e['date'],'x':t})
_PLAQUE_ORN=('<span class="lotus-bg"><svg width="276" height="225" viewBox="0 0 64 52" fill="none" stroke="#e6c578" stroke-width="0.9" stroke-linejoin="round" stroke-linecap="round"><path d="M32 6 C39 17 39 27 32 37 C25 27 25 17 32 6 Z"/><path d="M15 13 C23 19 25 29 23 38 C15 34 11 23 15 13 Z"/><path d="M49 13 C41 19 39 29 41 38 C49 34 53 23 49 13 Z"/><path d="M3 25 C11 27 15 33 16 40 C9 40 4 34 3 25 Z"/><path d="M61 25 C53 27 49 33 48 40 C55 40 60 34 61 25 Z"/><path d="M8 44 C20 49 44 49 56 44"/></svg></span><span class="lotus-chip"><svg width="21" height="17" viewBox="0 0 64 52" fill="none" stroke="#e6c578" stroke-width="2.2" stroke-linejoin="round" stroke-linecap="round"><path d="M32 6 C39 17 39 27 32 37 C25 27 25 17 32 6 Z"/><path d="M15 13 C23 19 25 29 23 38 C15 34 11 23 15 13 Z"/><path d="M49 13 C41 19 39 29 41 38 C49 34 53 23 49 13 Z"/><path d="M3 25 C11 27 15 33 16 40 C9 40 4 34 3 25 Z"/><path d="M61 25 C53 27 49 33 48 40 C55 40 60 34 61 25 Z"/><path d="M8 44 C20 49 44 49 56 44"/></svg></span>'+'<span class="cnr tl"><svg width="36" height="36" viewBox="0 0 48 48" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M5 43 V16 Q5 5 16 5 H43"/><path d="M11.5 43 V20 Q11.5 11.5 20 11.5 H43"/><path d="M18.5 18.5 q6.5 0 6.5 6.5 q0 5.5 -5.5 5.5 q-4.5 0 -4.5 -4.5 q0 -3.5 3.5 -3.5"/><path d="M43 2.6 l2.4 2.4 -2.4 2.4 -2.4 -2.4 Z" fill="currentColor" stroke="none"/><path d="M2.6 43 l2.4 2.4 -2.4 2.4 -2.4 -2.4 Z" fill="currentColor" stroke="none"/></svg></span><span class="cnr tr"><svg width="36" height="36" viewBox="0 0 48 48" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M5 43 V16 Q5 5 16 5 H43"/><path d="M11.5 43 V20 Q11.5 11.5 20 11.5 H43"/><path d="M18.5 18.5 q6.5 0 6.5 6.5 q0 5.5 -5.5 5.5 q-4.5 0 -4.5 -4.5 q0 -3.5 3.5 -3.5"/><path d="M43 2.6 l2.4 2.4 -2.4 2.4 -2.4 -2.4 Z" fill="currentColor" stroke="none"/><path d="M2.6 43 l2.4 2.4 -2.4 2.4 -2.4 -2.4 Z" fill="currentColor" stroke="none"/></svg></span><span class="cnr bl"><svg width="36" height="36" viewBox="0 0 48 48" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M5 43 V16 Q5 5 16 5 H43"/><path d="M11.5 43 V20 Q11.5 11.5 20 11.5 H43"/><path d="M18.5 18.5 q6.5 0 6.5 6.5 q0 5.5 -5.5 5.5 q-4.5 0 -4.5 -4.5 q0 -3.5 3.5 -3.5"/><path d="M43 2.6 l2.4 2.4 -2.4 2.4 -2.4 -2.4 Z" fill="currentColor" stroke="none"/><path d="M2.6 43 l2.4 2.4 -2.4 2.4 -2.4 -2.4 Z" fill="currentColor" stroke="none"/></svg></span><span class="cnr br"><svg width="36" height="36" viewBox="0 0 48 48" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M5 43 V16 Q5 5 16 5 H43"/><path d="M11.5 43 V20 Q11.5 11.5 20 11.5 H43"/><path d="M18.5 18.5 q6.5 0 6.5 6.5 q0 5.5 -5.5 5.5 q-4.5 0 -4.5 -4.5 q0 -3.5 3.5 -3.5"/><path d="M43 2.6 l2.4 2.4 -2.4 2.4 -2.4 -2.4 Z" fill="currentColor" stroke="none"/><path d="M2.6 43 l2.4 2.4 -2.4 2.4 -2.4 -2.4 Z" fill="currentColor" stroke="none"/></svg></span>')
hero=('<section class="hero">'
 f'<img class="bg" src="{HERO_IMG}" alt="" aria-hidden="true"><div class="rays" aria-hidden="true"></div><div class="dust" id="dust" aria-hidden="true"></div>'
 f'<img class="hero-seal" src="{SEAL_IMG}" alt="归海">'
 f'<div class="inner"><h1><img src="{TITLE_GUIHAI}" alt="归海录"></h1>'
 '<p class="sub">'+_PLAQUE_ORN+'<span class="hl">这里是志远行空讲课内容的整理站</span>'
 '<span class="hl">全部内容分成四部&ensp;<span style="white-space:nowrap">逆修觉者</span>&ensp;<span style="white-space:nowrap">灵魂觉者</span>&ensp;<span style="white-space:nowrap">法界天机</span>&ensp;<span style="white-space:nowrap">道法自然</span></span>'
 '<span class="hl">每一部里都有故事案例、讲课原声和小动画，点开就能看</span>'
 '<span class="hl">第一次来，从第一部开始往下看</span></p>'
 '<div class="cta"><a class="btn" href="#part1">从第一部开始</a><a class="btn ghost" href="#library">直接查资料库</a></div>'
 '<a class="scrollcue" href="#part1"><span class="arr">↓</span> 向 下 逛 <span class="arr">↓</span></a></div></section>')
counts={y:0 for y in ['2026','2025','2024']}
for e in entries.values():
 if e['date'][:4] in counts:counts[e['date'][:4]]+=1
total=len(entries)
intro=('<section class="intro reveal"><p class="lede">不用从头读起。先挑一部顺眼的，<br>读一则故事、听一段原声，觉得对味，再往深处走。</p>'
 '<form class="searchbar" id="search-form"><input id="search-input" type="search" placeholder="搜一搜：天眼、烧纸、轮回…" aria-label="搜索站内文章"><button type="submit">搜索</button></form><div class="qchips"><span class="qchips-lab">点一下就搜：</span><button type="button" data-q="天眼">天眼</button><button type="button" data-q="烧纸">烧纸</button><button type="button" data-q="福报">福报</button><button type="button" data-q="轮回">轮回</button><button type="button" data-q="改命">改命</button><button type="button" data-q="怎么看人">怎么看人</button></div>'
 '<div class="sresults" id="search-results"></div></section>')
library=(f'<section class="library reveal" id="library"><div><h2>完整资料库</h2>'
 f'<p>四部之外的全部原文都在这里：{total} 篇讲课整理，按年份排好，带全文搜索。想查什么，直接去资料库里找。</p></div>'
 '<div class="years">'
 f'<a href="2026.html"><b>2026 年</b><span>{counts["2026"]} 篇</span></a>'
 f'<a href="2025.html"><b>2025 年</b><span>{counts["2025"]} 篇</span></a>'
 f'<a href="2024.html"><b>2024 年</b><span>{counts["2024"]} 篇</span></a>'
 f'<a href="all.html"><b>全部文章</b><span>{total} 篇 · 全文搜索</span></a>'
 '<a href="topics.html" style="grid-column:1/-1"><b>按问题找</b><span>钱 · 工作 · 家人 · 身体 · 命运——按你带着来的问题选篇</span></a></div></section>')
parts_html=''.join(part_section(b)+(part_divider(b) if i<3 else '') for i,b in enumerate(BOARDS))
index_body=hero+'<main>'+intro+parts_html+ORN_DIV+library+'</main>'
(out/'index.html').write_text(shell('归海录 · 志远行空讲课整理',index_body,home=True),encoding='utf-8')
for b in BOARDS:
 (out/f'board{b["n"]}.html').write_text(board_page(b),encoding='utf-8')
(out/'topics.html').write_text(topics_page(),encoding='utf-8')
(out/'domestic.html').write_text('<!doctype html><meta charset="utf-8"><meta http-equiv="refresh" content="0; url=all.html"><title>归海录 · 完整资料库</title><p>正在进入<a href="all.html">完整资料库</a>…</p>',encoding='utf-8')
related=('<section class="board-hero"><span class="tag">知识大赏</span><h1>换个角度看人生</h1><p>小动画对应的完整原文都在这里，点开就是全文。</p></section>'
 '<main class="board-main"><div class="alist">'
 +''.join(f'<a href="{article_href(c["article_id"])}"><span>{esc(c["title"])}</span></a>' for c in vibes)
 +'</div><p style="margin-top:26px"><a class="more" href="index.html#part4">← 回到道法自然</a></p></main>')
(out/'vibe.html').write_text(shell('归海录 · 人生观察相关阅读',related),encoding='utf-8')
js='const cases='+json.dumps(cases,ensure_ascii=False)+';\n'
js+='const SEARCH='+json.dumps(search_entries,ensure_ascii=False)+';\n'
js+=r'''
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
const MOON='<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>';const SUN='<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="4.2"/><path d="M12 2v2.6M12 19.4V22M4.9 4.9l1.8 1.8M17.3 17.3l1.8 1.8M2 12h2.6M19.4 12H22M4.9 19.1l1.8-1.8M17.3 6.7l1.8-1.8"/></svg>';function paintTheme(){if(themeBtn){const dark=document.documentElement.classList.contains('dark');themeBtn.innerHTML=dark?SUN:MOON;themeBtn.setAttribute('aria-label',dark?'切换白天模式':'切换晚上模式')}}
if(themeBtn){themeBtn.onclick=()=>{const dark=document.documentElement.classList.toggle('dark');try{localStorage.setItem('ghl_theme',dark?'dark':'light')}catch(e){}paintTheme()};paintTheme()}
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
function doSearch(){
  if(!sBox)return;
  const q=(sInput.value||'').trim().toLowerCase();sBox.replaceChildren();
  if(!q)return;
  const hits=SEARCH.filter(e=>(e.t+' '+e.x).toLowerCase().includes(q)).slice(0,8);
  if(!hits.length){const d=document.createElement('div');d.className='none';d.textContent='没找到，去资料库里用全文搜索试试。';sBox.appendChild(d);return}
  hits.forEach(e=>{const a=document.createElement('a');a.className='hit';a.href=e.p+'#'+e.id;const b=document.createElement('b');b.textContent=e.t;const s=document.createElement('span');s.textContent=(e.d?e.d+' · ':'')+e.x;a.append(b,s);sBox.appendChild(a)});
}
if(sForm){sForm.addEventListener('submit',ev=>{ev.preventDefault();doSearch()});sInput.addEventListener('input',doSearch)}
document.querySelectorAll('[data-q]').forEach(b=>b.addEventListener('click',()=>{if(sInput){sInput.value=b.getAttribute('data-q');doSearch();sInput.focus()}}));
document.addEventListener('click',e=>{const c=e.target.closest?e.target.closest('.vchip[data-v]'):null;if(c){e.preventDefault();e.stopPropagation();location.href=c.getAttribute('data-v')}},true);
const pageSearch=document.querySelector('#search');
if(pageSearch&&!sInput){const rows=[...document.querySelectorAll('details.entry')];function filter(){let n=0;for(const r of rows){r.hidden=!r.textContent.toLowerCase().includes(pageSearch.value.trim().toLowerCase());if(!r.hidden)n++}const c=document.querySelector('#count');if(c)c.textContent=n+' 篇';const em=document.querySelector('#empty');if(em)em.hidden=n!==0}pageSearch.oninput=filter;filter()}
;(function(){var POOL=['修行','因果','福报','轮回','孩子','菩萨','鬼','投胎','灵魂','事业','父母','健康','去世','财运','婚姻','天眼','超度','阴债','烧纸','风水','祖先','冤亲','改命','做梦'];var wrap=document.querySelector('.qchips');if(!wrap)return;var btns=[].slice.call(wrap.querySelectorAll('button[data-q]'));if(!btns.length)return;function pick(){var p=POOL.slice();for(var i=p.length-1;i>0;i--){var j=Math.floor(Math.random()*(i+1));var t=p[i];p[i]=p[j];p[j]=t}return p.slice(0,btns.length)}function apply(w){btns.forEach(function(b,i){b.textContent=w[i];b.setAttribute('data-q',w[i])})}apply(pick());setInterval(function(){var inp=document.getElementById('search-input');if(inp&&inp.value.trim())return;wrap.classList.add('fading');setTimeout(function(){apply(pick());wrap.classList.remove('fading')},480)},12000)})();
'''
(out/'reading.js').write_text(js,encoding='utf-8')
print('Preview created:',len(entries),'full original articles;',len(cases),'anonymous samples')
assert len(entries)>=100
assert sum(1 for e in entries.values() if e['board'])==len(entries)
for b in BOARDS:
 assert len(board_entries(b['n']))>=10,b['name']
 assert b['first'] in entries
idx=(out/'index.html').read_text(encoding='utf-8')
assert 'douyin' not in idx.lower()
assert '未编年' not in idx
for page in ['index.html','board1.html','board2.html','board3.html','board4.html','vibe.html','topics.html']:
 soup=BeautifulSoup((out/page).read_text(encoding='utf-8'),'html.parser')
 for a in soup.select('a[href]'):
  href=a['href'].split('#')[0]
  if not href or href.startswith('http'):continue
  assert (out/href).exists(),page+' -> missing '+href
 for im in soup.select('img[src]'):
  s=im['src'].split('?')[0]
  if s.startswith('http') or s.startswith('data:'):continue
  assert (out/s).exists(),page+' -> missing img '+s
print('PASS: boards cover all',len(entries),'articles; all local links and images exist; no Douyin links')
