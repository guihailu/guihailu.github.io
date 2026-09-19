# -*- coding: utf-8 -*-
"""归海录静态站构建：guihailu.md -> index.html（pandoc 转换）
设计语言（照抄顶级站手法）：Apple CN 超大标题+留白 / Medium 衬线窄栏阅读 / VitePress 侧栏目录"""
import re, pathlib, subprocess, sys

HERE = pathlib.Path(__file__).parent
SRC = HERE / "guihailu.md"

md = SRC.read_text(encoding="utf-8")

# 1) 去掉 <title> 行
md = re.sub(r"<title>.*?</title>\n", "", md)

# 1.5) 前置元数据清理（09-19 Eli 令）：以下三类块在 Lark 中位于条目标题之前，
# 站点卡片切分时会落入前一张卡片尾部造成孤行/错位——构建时跳过，不碰 Lark 源、不改文字。
# ① 日期头 h2（与各条目 📌 callout 内容重复）
md = re.sub(r'^## 日期不详 · 师父内部开示\n+', '', md, flags=re.M)
# ② 「主题：」裸行（条目 h1 标题已含主题）
md = re.sub(r'^主题：[^\n]+\n+', '', md, flags=re.M)
# ③ 💜 前置日期 callout（「日期行+主题行」形态；正文/前言中的 💜 不含日期行，不匹配）
md = re.sub(r'<callout emoji="💜">\n\*\*20\d{2}-\d{2}-\d{2}[^*]*\*\*\n\*\*主题：[^*]*\*\*\n</callout>\n*', '', md)

# 2) callout -> blockquote（每行加 "> "；列表行前插空行防止与上文合并成段落）
def callout_to_bq(m):
    emoji, body = m.group(1), m.group(2)
    lines = [f"> {emoji}"]
    prev_list = False
    for l in body.split("\n"):
        l = l.rstrip()
        if not l.strip():
            lines.append(">")
            prev_list = False
            continue
        is_list = l.strip().startswith("- ")
        if is_list and not prev_list:
            lines.append(">")
        lines.append("> " + l)
        prev_list = is_list
    return "\n".join(lines)

md = re.sub(r'<callout emoji="([^"]+)">(.*?)</callout>', callout_to_bq, md, flags=re.S)

# 2.5) 去除「日期不详」标记（Eli 09-15 定：早期文档不再标注）
md = md.replace(" ｜ 日期不详", "")
md = md.replace("日期不详 · 师父内部开示", "师父内部开示")

# 3) 收集 TOC 条目与正文标题，建立锚点映射（精确匹配优先，其次公共前缀>=6字）
toc_pat = re.compile(r'^- \[([^\]]+)\]\(https://[^)]+#(doxjp\w+)\)', re.M)
toc_items = [(m.group(1), m.group(2)) for m in toc_pat.finditer(md)]
print(f"TOC 条目: {len(toc_items)}")

head_pat = re.compile(r'^(#{1,2}) (.+)$', re.M)
headings = [(m.start(), m.group(1), m.group(2).strip()) for m in head_pat.finditer(md)]
headings = [(p, lv, t) for p, lv, t in headings if t != "📋 目录"]
print(f"正文标题: {len(headings)}")

def norm(s):
    return s.replace("“", '"').replace("”", '"').replace(" ", "")

def common_prefix(a, b):
    n = 0
    for x, y in zip(a, b):
        if x == y:
            n += 1
        else:
            break
    return n

sec_of_title = {}   # 标题原文 -> sec id
used = set()
unmatched = []
for i, (text, bid) in enumerate(toc_items, 1):
    t = norm(text.split(" ｜ ")[0].strip())
    sid = f"sec-{i:02d}"
    hit = None
    for pos, lv, ht in headings:
        if pos in used:
            continue
        if norm(ht) == t:
            hit = (pos, lv, ht)
            break
    if hit is None:
        for pos, lv, ht in headings:
            if pos in used:
                continue
            if common_prefix(norm(ht), t) >= 6:
                hit = (pos, lv, ht)
                break
    if hit is None:
        unmatched.append(text)
        continue
    pos, lv, ht = hit
    used.add(pos)
    sec_of_title[ht] = sid

if unmatched:
    print("  UNMATCHED:", *unmatched, sep="\n    ")

# TOC 链接 -> 页内锚点
def toc_repl(m):
    text, bid = m.group(1), m.group(2)
    t = norm(text.split(" ｜ ")[0].strip())
    for ht, sid in sec_of_title.items():
        if norm(ht) == t or common_prefix(norm(ht), t) >= 6:
            return f"- [{text}](#{sid})"
    return f"- [{text}](#top)"

md = toc_pat.sub(toc_repl, md)

# 正文标题加锚点（按标题原文唯一替换）
for ht, sid in sec_of_title.items():
    pat = re.compile(rf'^(#{{1,2}}) ({re.escape(ht)})$', re.M)
    md = pat.sub(rf'\1 \2 {{#{sid}}}', md, count=1)

# 4) pandoc 转 HTML
pre = HERE / "guihailu_pre.md"
pre.write_text(md, encoding="utf-8")
res = subprocess.run(
    ["pandoc", str(pre), "-f", "markdown+east_asian_line_breaks", "-t", "html5",
     "--shift-heading-level-by=1"],
    capture_output=True, text=True, encoding="utf-8",
)
if res.returncode != 0:
    print(res.stderr)
    sys.exit(1)
body_html = res.stdout

# 4.4) 目录开头包进 layout+aside（闭合在 4.6 处理）
body_html = body_html.replace(
    '<h2 id="目录">📋 目录</h2>',
    '<div class="layout"><aside class="toc"><details class="tocm"><summary>📋 目录</summary>', 1)

# 4.5) 每条目包成折叠卡片：id 移到 details 上，日期徽章移进 summary（h2/h3 两种锚点都处理）
def wrap_entries(b):
    pat = re.compile(r'<h([23])\s+id="sec-(\d+)">(.*?)</h\1>\n', re.S)
    matches = list(pat.finditer(b))
    if not matches:
        return b
    out = [b[:matches[0].start()]]
    for idx, m in enumerate(matches):
        lv, sid, title = m.group(1), m.group(2), m.group(3)
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(b)
        chunk = b[m.end():end]
        date_html = ""
        db = re.search(r'<blockquote>\s*<p>(📌.*?)</p>\s*</blockquote>', chunk, re.S)
        if db:
            date_html = '<span class="date">' + db.group(1) + '</span>'
            chunk = chunk[:db.start()] + chunk[db.end():]
        out.append(
            f'<details class="entry" id="sec-{sid}">'
            f'<summary><h2>{title}</h2>{date_html}</summary>'
            f'<div class="entry-body">' + chunk + '</div></details>')
    return ''.join(out)

body_html = wrap_entries(body_html)

# 4.6) 闭合 aside.toc，开启 main.content（4.5 之后才能定位条目起点）
j = body_html.find('<details class="entry"')
if j > 0:
    body_html = body_html[:j] + '</details></aside><main class="content">' + body_html[j:]
    body_html += '</main></div>'
else:
    body_html += '</details></aside></div>'

# 4.7) 文档自带的 💜 简介 callout -> 引言段落（去重：页面标题下不再重复放简介）
def intro_repl(m):
    title, _, body = m.group(1).partition('</strong>')
    body = body.replace('每一段语音', '</p><p class="intro-copy">每一段语音', 1)
    body = body.replace('此合集按时间倒序整理', '</p><p class="intro-note">此合集按时间倒序整理', 1)
    return f'<div class="intro"><p class="intro-title">{title}</strong></p><p class="intro-copy">{body}</p></div>'

body_html = re.sub(
    r'<blockquote>\s*<p>💜</p>\s*<p>(<strong>归海2026.*?)</p>\s*</blockquote>',
    intro_repl, body_html, count=1, flags=re.S)

# 5) 组装 index.html（Apple CN 排版 + Medium 阅读 + 侧栏目录）
css = """
:root{
  --deep:#0a1220;--paper:#faf8f1;--paper2:#f2eee2;--ink:#211e18;
  --muted:#6d685e;--line:#ded8c9;--gold:#b28b4a;--gold2:#d9b878;
  --cin:#a03028;--link:#8b3d34;--quote:#514b42;
}
html.dark{
  --paper:#0d1526;--paper2:#17233b;--ink:#eee8db;--muted:#b4ad9e;
  --line:#34415a;--link:#d9b878;--quote:#cec5b5;
}
*{box-sizing:border-box}
html{scroll-behavior:smooth}
body{margin:0;background:var(--deep);color:var(--ink);font-family:-apple-system,BlinkMacSystemFont,"PingFang SC","Hiragino Sans GB","Microsoft YaHei",sans-serif;-webkit-font-smoothing:antialiased}
button,a,summary{-webkit-tap-highlight-color:transparent}
button:focus-visible,a:focus-visible,summary:focus-visible{outline:2px solid var(--gold);outline-offset:4px}
#progress{position:fixed;top:0;left:0;height:2px;width:0;background:var(--gold2);z-index:101}
.hero{background:var(--deep);color:var(--paper);text-align:center}
.doctitle{max-width:900px;margin:auto;padding:112px 24px 104px}
.titleline{display:flex;justify-content:center}
.doctitle h1{display:flex;align-items:center;justify-content:center;gap:22px;margin:0;color:#faf8f1;font-size:72px;font-weight:700;letter-spacing:.13em;line-height:1.2}
.seal{display:inline-flex;flex-direction:column;align-items:center;justify-content:center;width:42px;height:64px;flex:none;border-radius:8px;background:var(--cin);color:#fff6e9;font-family:"KaiTi","STKaiti",serif;font-size:22px;font-weight:400;letter-spacing:0;line-height:1.1}
.doctitle .sub{margin:25px 0 0;color:#c8baa0;font-size:14px;letter-spacing:.24em;line-height:1.8}
.yt{display:inline-flex;align-items:center;justify-content:center;margin-top:34px;padding:9px 23px;border:1px solid var(--gold);border-radius:999px;color:var(--gold2);font-size:13px;font-weight:600;letter-spacing:.09em;text-decoration:none;transition:background .2s,color .2s}
.yt:hover{background:var(--gold2);color:var(--deep)}
.paper{background:var(--paper);min-height:60vh}
.intro{max-width:700px;margin:0 auto;padding:88px 24px 78px;text-align:center;color:var(--muted);font-size:15px;line-height:2.05}
.intro::before{content:"";display:block;width:38px;height:2px;margin:0 auto 25px;background:var(--gold)}
.intro p{margin:0}.intro .intro-title{margin-bottom:16px}.intro strong{display:block;color:var(--ink);font-size:17px;font-weight:600}
.intro .intro-copy+.intro-copy{margin-top:12px}.intro .intro-note{margin-top:18px;font-size:13px;line-height:1.8}
.layout{display:grid;grid-template-columns:220px minmax(0,1fr);gap:clamp(32px,4vw,64px);align-items:start;max-width:1160px;margin:auto;padding:0 32px 128px}
aside.toc{position:sticky;top:32px;max-height:calc(100vh - 64px);overflow-y:auto;scrollbar-width:thin}
.tocm>summary{display:block;margin:0 0 18px;list-style:none;cursor:pointer;font-size:0;line-height:1.5}
.tocm>summary::-webkit-details-marker,.entry>summary::-webkit-details-marker{display:none}
.tocm>summary::before{content:"目录";color:var(--ink);font-size:16px;font-weight:700;letter-spacing:.12em}
.toc ul{margin:0;padding:0;list-style:none;border-left:1px solid var(--line)}
.toc li{margin:0}.toc a{display:block;margin-left:-1px;padding:8px 12px;border-left:2px solid transparent;color:var(--muted);font-size:13px;font-weight:500;line-height:1.6;text-decoration:none;overflow-wrap:anywhere;transition:color .2s,border-color .2s}
.toc a:hover{color:var(--ink)}.toc a.here{border-left-color:var(--cin);color:var(--cin);font-weight:700}
.toc a.done::after{content:" ✓";color:var(--cin);font-size:11px}
main.content{min-width:0;max-width:720px;width:100%;justify-self:center}
.entry{margin:0;border-bottom:1px solid var(--line);scroll-margin-top:24px}
.entry:first-child{border-top:1px solid var(--line)}
.entry>summary{display:grid;grid-template-columns:18px minmax(0,1fr);column-gap:16px;align-items:start;padding:27px 0;list-style:none;cursor:pointer}
.entry>summary::before{content:"+";grid-column:1;grid-row:1;color:var(--gold);font-size:20px;font-weight:300;line-height:1.55}
.entry[open]>summary::before{content:"−"}
.entry>summary h2{grid-column:2;grid-row:1;min-width:0;width:100%;margin:0;color:var(--ink);font-size:21px;font-weight:650;letter-spacing:.015em;line-height:1.65;overflow-wrap:anywhere;transition:color .2s}
.entry>summary:hover h2{color:var(--cin)}
.entry>summary .date{grid-column:2;grid-row:2;justify-self:start;min-width:0;max-width:100%;margin-top:10px;padding:3px 9px;border-radius:4px;background:var(--paper2);color:var(--muted);font-size:12px;font-weight:500;letter-spacing:.02em;line-height:1.65;white-space:normal;overflow-wrap:anywhere}
.date p{display:inline;margin:0}.date strong{font-weight:500}
.entry-body{padding:0 0 46px;color:var(--ink);font-family:"Songti SC","Noto Serif SC","STSong","SimSun",serif;font-size:17.5px;line-height:2.08;overflow-wrap:anywhere}
.entry-body p{margin:16px 0}.entry-body h3,.entry-body h4{color:var(--ink);font-family:-apple-system,BlinkMacSystemFont,"PingFang SC","Microsoft YaHei",sans-serif;line-height:1.55}
.entry-body h3{margin:40px 0 14px;color:var(--cin);font-size:19px}.entry-body h4{margin:30px 0 10px;color:#856326;font-size:17px;letter-spacing:.04em}
html.dark .entry-body h3{color:#d68476}html.dark .entry-body h4{color:var(--gold2)}
.entry-body blockquote{margin:27px 0;padding:0 0 0 20px;border-left:2px solid var(--gold);color:var(--quote);font-size:16.5px}
.entry-body blockquote p{margin:8px 0}.entry-body ul,.entry-body ol{padding-left:26px}.entry-body li{margin:9px 0}
.entry-body a{color:var(--link);text-decoration:none;border-bottom:1px solid var(--gold)}
.entry-body a:hover{border-color:var(--cin)}
.entry-body table{display:block;max-width:100%;margin:25px 0;border-collapse:collapse;overflow-x:auto;font-family:-apple-system,BlinkMacSystemFont,"PingFang SC","Microsoft YaHei",sans-serif;font-size:14px}
.entry-body th,.entry-body td{border:1px solid var(--line);padding:9px 13px;text-align:left}
.entry-body th{background:var(--paper2);font-weight:600}.entry-body pre{max-width:100%;overflow-x:auto}
.entry-body hr{margin:48px 0;border:0;border-top:1px solid var(--line)}.entry-body img{max-width:100%;height:auto}
footer{padding:58px 20px 64px;background:var(--deep);color:#b3a994;text-align:center;font-size:13px;letter-spacing:.05em;line-height:1.9}
.flinks{margin-bottom:24px}.fbtn{display:inline-flex;align-items:center;justify-content:center;max-width:100%;margin:6px 9px;padding:10px 25px;border:1px solid var(--gold);border-radius:999px;color:var(--gold2);font-size:13px;font-weight:600;line-height:1.6;text-decoration:none;transition:background .2s,color .2s}
.fbtn:hover{background:var(--gold2);color:var(--deep)}.fmeta{color:#a99d86}
.navstack{position:fixed;right:22px;bottom:24px;z-index:98;display:flex;flex-direction:column;gap:10px}
.navbtn,#toggle{display:grid;place-items:center;width:44px;height:44px;border:1px solid var(--gold);border-radius:50%;background:var(--deep);color:var(--gold2);font-size:17px;cursor:pointer;transition:background .2s,color .2s}
.navbtn:hover,#toggle:hover{background:var(--gold2);color:var(--deep)}
#toggle{position:fixed;top:16px;right:18px;z-index:100}
@media(max-width:960px){
  .layout{display:block;max-width:768px;padding:0 24px 96px}
  aside.toc{position:static;max-height:none;overflow:visible;margin:0 auto 22px}
  .tocm{border-top:1px solid var(--line);border-bottom:1px solid var(--line)}
  .tocm>summary{display:flex;align-items:center;justify-content:space-between;margin:0;padding:17px 0}
  .tocm>summary::after{content:"⌄";color:var(--gold);font-size:22px;line-height:1}
  .tocm[open]>summary::after{transform:rotate(180deg)}
  .tocm ul{max-height:55vh;margin:0 0 15px;overflow-y:auto}
  main.content{max-width:720px;margin:auto}
}
@media(max-width:640px){
  .doctitle{padding:64px 22px 52px}.doctitle h1{gap:14px;font-size:44px;letter-spacing:.08em}
  .seal{width:36px;height:54px;border-radius:8px;font-size:18px}
  .doctitle .sub{margin-top:16px;font-size:12px;letter-spacing:.1em}.yt{margin-top:20px}
  .intro{padding:42px 23px 38px;font-size:14.5px;line-height:1.95}.intro::before{margin-bottom:19px}.intro strong{font-size:16px}.intro .intro-copy{text-align:left}
  .layout{padding:0 20px 84px}.tocm>summary{padding:14px 0}.entry>summary{column-gap:11px;padding:20px 0}
  .entry>summary h2{font-size:18px;line-height:1.65}.entry>summary .date{font-size:11.5px}
  .entry-body{padding-bottom:37px;font-size:16.5px;line-height:2.05}.entry-body h3{font-size:18px}
  .entry-body blockquote{padding-left:15px;font-size:15.5px}
  footer{padding:48px 20px 56px}.fbtn{display:flex;width:max-content;margin:10px auto}
  .navstack{right:12px;bottom:calc(16px + env(safe-area-inset-bottom));gap:8px}
  .navbtn,#toggle{width:40px;height:40px;font-size:16px}#toggle{top:12px;right:12px}
}
@media(max-width:380px){.doctitle h1{font-size:42px}.doctitle .sub{letter-spacing:.05em}}
@media(prefers-reduced-motion:reduce){html{scroll-behavior:auto}*,*::before,*::after{transition:none!important}}
"""

js = """
(function(){var p=document.getElementById('progress');function upd(){var h=document.documentElement;var d=h.scrollHeight-h.clientHeight;p.style.width=(d>0?(h.scrollTop/d)*100:0)+'%';}document.addEventListener('scroll',upd,{passive:true});upd();})();
(function(){var b=document.getElementById('toggle');function sync(){var d=document.documentElement.classList.contains('dark');b.textContent=d?'☀️':'🌙';}b.addEventListener('click',function(){document.documentElement.classList.toggle('dark');try{localStorage.setItem('ghl_theme',document.documentElement.classList.contains('dark')?'dark':'light')}catch(e){}sync();});sync();})();
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
document.getElementById('toReading').addEventListener('click',function(){
  var id=cur||findCur();
  if(id){var el=document.getElementById(id);if(el){window.scrollTo({top:el.getBoundingClientRect().top+window.scrollY-16,behavior:'smooth'});return;}}
  window.scrollTo({top:0,behavior:'smooth'});
});
var saved=0;try{saved=parseInt(localStorage.getItem('ghl_scroll')||'0',10)}catch(e){}
if(saved>0&&!location.hash){window.scrollTo(0,saved)}
var t;document.addEventListener('scroll',function(){clearTimeout(t);t=setTimeout(function(){try{localStorage.setItem('ghl_scroll',String(window.scrollY))}catch(e){}},400);findCur();},{passive:true});
})();
(function(){var d=document.querySelector('details.tocm');if(d){var wide=null;function sync(){var now=window.innerWidth>960;if(now!==wide){d.open=now;wide=now;}}sync();window.addEventListener('resize',sync);}})();
(function(){var p=document.querySelector('.intro p');if(p&&p.firstChild&&p.firstChild.nodeType===3){p.firstChild.textContent=p.firstChild.textContent.replace('💜 ','');}})();
"""

html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>📿 归海录 · 师父志远行空的开示合集</title>
<meta name="description" content="归海录：师父志远行空的每日开示与 YouTube 视频讲法合集——每一段语音，一个故事，一个道理，润物无声。按时间倒序，持续更新。">
<meta property="og:title" content="📿 归海录 · 师父志远行空的开示合集">
<meta property="og:description" content="师父志远行空的每日开示与 YouTube 视频讲法合集。因果、修行、认知、人间智慧——百川归海，智慧汇流。">
<meta property="og:type" content="website">
<meta property="og:image" content="https://guihailu.github.io/cover.jpg">
<script>try{{if(localStorage.getItem('ghl_theme')==='dark')document.documentElement.classList.add('dark')}}catch(e){{}}</script>
<link rel="stylesheet" href="style.css">
</head>
<body id="top">
<div id="progress"></div>
<header class="hero">
  <div class="doctitle">
    <div class="titleline"><h1>归海录<span class="seal" aria-hidden="true">归<br>海</span></h1></div>
    <p class="sub">归海2026 · 师父志远行空的开示合集</p>
    <a class="yt" href="https://www.youtube.com/@zyxk999" target="_blank" rel="noopener">▶ YouTube</a>
  </div>
</header>
<div class="paper">
{body_html}
</div>
<footer>
  <div class="flinks">
    <a class="fbtn" href="https://www.youtube.com/@zyxk999" target="_blank" rel="noopener">▶ 师父 YouTube 频道</a>
    <a class="fbtn" href="https://u78zyhf3gaz.jp.larksuite.com/docx/QKYtdsvHzoH1aIxuGhrjD81EpWf" target="_blank" rel="noopener">📿 归海录 · Lark 源文档</a>
    <a class="fbtn" href="https://www.oceanwards.com/" target="_blank" rel="noopener">🌊 归海论坛</a>
  </div>
  <div class="fmeta">归海录 · 持续更新中 ｜ 更新日期：2026-09-15</div>
</footer>
<div class="navstack">
  <button class="navbtn" id="toReading" title="回到当前阅读标题" aria-label="回到当前阅读标题">📖</button>
  <button class="navbtn" id="toTop" title="回到文档顶部" aria-label="回到文档顶部">↑</button>
</div>
<button id="toggle" aria-label="切换深浅色">🌙</button>
<script src="main.js" defer></script>
</body>
</html>"""

# 三文件输出：LF 行尾；CSS/主 JS 外置，页头保留主题初始化内联脚本
(HERE / "style.css").write_text(css, encoding="utf-8", newline="\n")
(HERE / "main.js").write_text(js, encoding="utf-8", newline="\n")
out = HERE / "index.html"
out.write_text(html, encoding="utf-8", newline="\n")
print(f"OK: index.html {out.stat().st_size} B | style.css {(HERE/'style.css').stat().st_size} B | main.js {(HERE/'main.js').stat().st_size} B")
