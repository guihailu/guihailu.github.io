# -*- coding: utf-8 -*-
"""归海录静态站构建：guihailu.md -> index.html（pandoc 转换）
设计语言（照抄顶级站手法）：Apple CN 超大标题+留白 / Medium 衬线窄栏阅读 / VitePress 侧栏目录"""
import re, pathlib, subprocess, sys

HERE = pathlib.Path(__file__).parent
SRC = HERE / "guihailu.md"

md = SRC.read_text(encoding="utf-8")

# 1) 去掉 <title> 行
md = re.sub(r"<title>.*?</title>\n", "", md)

# 2) callout -> blockquote（每行加 "> "）
def callout_to_bq(m):
    emoji, body = m.group(1), m.group(2)
    lines = [f"> {emoji}"]
    for l in body.split("\n"):
        l = l.rstrip()
        lines.append(("> " + l) if l.strip() else ">")
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
    out.append(b[matches[-1].end():])
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
    inner = m.group(1).replace("此合集按时间倒序整理", "<br>此合集按时间倒序整理")
    return f'<div class="intro"><p>💜 {inner}</p></div>'

body_html = re.sub(
    r'<blockquote>\s*<p>💜</p>\s*<p>(<strong>归海2026.*?)</p>\s*</blockquote>',
    intro_repl, body_html, count=1, flags=re.S)

# 5) 组装 index.html（Apple CN 排版 + Medium 阅读 + 侧栏目录）
css = """
:root{--deep:#0a1220;--paper:#faf8f1;--paper2:#f2eee2;--paper3:#eae4d2;--ink:#1f1a10;--ink2:#8a8170;--gold:#b28b4a;--gold2:#d9b878;--cin:#a03028;--line:#e2dccb;--line2:#c9c1ab;--link:#9a4636;--quote:#57503f;--th-ink:#8a4a3a;}
html.dark{--paper:#0d1526;--paper2:#111c33;--paper3:#172442;--ink:#ece5d3;--ink2:#93896f;--line:#23304f;--line2:#33415f;--link:#8fb6e8;--quote:#cfc6b2;--th-ink:#e6c886;}
*{box-sizing:border-box}
html{scroll-behavior:smooth}
body{margin:0;background:var(--deep);color:var(--ink);font-family:-apple-system,BlinkMacSystemFont,"PingFang SC","Hiragino Sans GB","Microsoft YaHei","Segoe UI",sans-serif;font-size:18px;line-height:1.9;-webkit-font-smoothing:antialiased;}
#progress{position:fixed;top:0;left:0;height:2px;width:0;background:linear-gradient(90deg,#8a6a2f,var(--gold2),#8a6a2f);z-index:99;}
header.hero{background:var(--deep);}
header.hero img.cover{display:block;width:100%;height:auto;border:none;}
.paper{background:var(--paper);position:relative;z-index:1;}
.doctitle{text-align:center;padding:110px 24px 64px;}
.titleline{display:flex;align-items:center;justify-content:center;gap:26px;flex-wrap:wrap;}
.doctitle h1{margin:0;font-size:72px;font-weight:800;letter-spacing:.18em;color:var(--ink);font-family:-apple-system,BlinkMacSystemFont,"PingFang SC","Hiragino Sans GB","Microsoft YaHei",sans-serif;}
.doctitle .seal{display:inline-flex;flex-direction:column;align-items:center;justify-content:center;margin-left:16px;width:40px;height:58px;border-radius:8px;background:linear-gradient(160deg,#c24430,#93291b);color:#fff5e0;font-size:21px;line-height:1.2;box-shadow:0 2px 10px rgba(0,0,0,.3);font-family:"KaiTi","STKaiti",serif;}
.yt{display:inline-flex;align-items:center;gap:7px;font-size:14px;font-weight:600;color:var(--ink2);text-decoration:none;border:1px solid var(--line2);border-radius:999px;padding:8px 18px;letter-spacing:.06em;transition:all .15s;}
.yt:hover{color:var(--cin);border-color:var(--cin);}
.doctitle .sub{margin-top:18px;color:var(--ink2);font-size:14px;letter-spacing:.34em;}
.intro{max-width:640px;margin:0 auto 90px;text-align:center;font-size:16px;color:var(--ink2);line-height:2.05;}
.intro p{margin:0;}
.intro strong{color:var(--ink);font-weight:600;}
.intro::before{content:"";display:block;width:36px;height:2px;background:var(--gold);margin:0 auto 22px;border-radius:1px;}
.layout{display:grid;grid-template-columns:252px minmax(0,1fr);gap:64px;max-width:1200px;margin:0 auto;padding:0 32px 120px;align-items:start;}
aside.toc{position:sticky;top:32px;max-height:calc(100vh - 64px);overflow-y:auto;padding-right:10px;scrollbar-width:thin;}
.tocm summary{list-style:none;cursor:pointer;margin:0 0 20px;color:var(--ink);font-size:24px;letter-spacing:.16em;font-weight:700;}
.tocm summary::-webkit-details-marker{display:none;}
.toc ul{margin:0;padding:0;list-style:none;border-left:1px solid var(--line);}
.toc li{margin:0;}
.toc a{display:block;padding:8px 16px;color:var(--ink2);text-decoration:none;font-size:13.5px;line-height:1.6;font-weight:600;transition:color .15s;}
.toc a:hover{color:var(--ink);}
.toc a.done::after{content:" ✓";color:var(--cin);font-size:10px;}
.toc a.here{color:var(--cin);font-weight:600;border-left:2px solid var(--cin);padding-left:14px;}
main.content{max-width:720px;min-width:0;}
.entry{margin:0;border-bottom:1px solid var(--line);}
.entry summary{cursor:pointer;list-style:none;display:flex;align-items:baseline;gap:16px;padding:26px 0;}
.entry summary::-webkit-details-marker{display:none;}
.entry summary h2{margin:0;font-size:21px;font-weight:700;flex:1;color:var(--ink);line-height:1.55;letter-spacing:.02em;transition:color .15s;}
.entry summary:hover h2{color:var(--cin);}
.entry summary::before{content:"＋";color:var(--gold);font-size:15px;flex:none;font-weight:400;}
.entry[open] summary::before{content:"－";}
.entry summary .date{color:var(--ink2);font-size:12.5px;flex:none;white-space:nowrap;letter-spacing:.05em;}
.entry-body{padding:8px 0 44px;font-family:"Songti SC","Noto Serif SC","STSong","SimSun",serif;font-size:17.5px;line-height:2.05;color:var(--ink);}
.entry-body h3{font-family:-apple-system,BlinkMacSystemFont,"PingFang SC","Microsoft YaHei",sans-serif;color:var(--ink);font-size:19px;font-weight:700;margin:38px 0 14px;letter-spacing:.03em;}
.entry-body h4{font-family:-apple-system,BlinkMacSystemFont,"PingFang SC","Microsoft YaHei",sans-serif;color:var(--ink);font-size:17px;font-weight:600;margin:28px 0 10px;}
.entry-body p{margin:16px 0;}
.entry-body blockquote{margin:24px 0;padding:0 0 0 20px;border-left:2px solid var(--gold);color:var(--quote);font-size:16.5px;}
.entry-body blockquote p{margin:8px 0;}
.entry-body ul,.entry-body ol{padding-left:26px;}
.entry-body li{margin:9px 0;}
.entry-body a{color:var(--link);text-decoration:none;border-bottom:1px solid var(--line2);transition:border-color .15s;}
.entry-body a:hover{border-bottom-color:var(--cin);}
.entry-body table{width:100%;border-collapse:collapse;margin:24px 0;font-size:15px;display:block;overflow-x:auto;font-family:-apple-system,BlinkMacSystemFont,"PingFang SC","Microsoft YaHei",sans-serif;}
.entry-body th,.entry-body td{border:1px solid var(--line);padding:9px 13px;text-align:left;}
.entry-body th{background:var(--paper2);color:var(--th-ink);font-weight:600;}
.entry-body hr{border:none;border-top:1px solid var(--line);margin:48px 0;}
.entry-body img{max-width:100%;border-radius:8px;}
footer{background:var(--deep);color:#8d846f;font-size:13px;text-align:center;padding:56px 20px 60px;letter-spacing:.1em;line-height:2.1;}
footer a{color:var(--gold2);text-decoration:none;}
.navstack{position:fixed;right:24px;bottom:28px;display:flex;flex-direction:column;gap:10px;z-index:98;}
.navbtn{width:44px;height:44px;border-radius:50%;background:rgba(16,29,54,.85);border:1px solid rgba(201,164,92,.5);color:var(--gold2);font-size:17px;cursor:pointer;backdrop-filter:blur(4px);transition:all .15s;}
.navbtn:hover{background:var(--gold);color:var(--deep);}
.flinks{margin-bottom:26px;}
.fbtn{display:inline-block;margin:8px 10px;padding:11px 28px;border:1px solid var(--gold);border-radius:999px;color:var(--gold2);font-size:14px;letter-spacing:.08em;text-decoration:none;transition:all .15s;font-weight:600;}
.fbtn:hover{background:var(--gold);color:var(--deep);}
.fmeta{color:#8d846f;}
#toggle{position:fixed;top:16px;right:16px;width:40px;height:40px;border-radius:50%;background:rgba(16,29,54,.6);border:1px solid rgba(201,164,92,.5);color:var(--gold2);font-size:18px;cursor:pointer;z-index:100;backdrop-filter:blur(4px);}
@media (max-width:960px){.layout{grid-template-columns:1fr;gap:28px;padding:0 24px 90px;}aside.toc{position:static;max-height:none;overflow:visible;}aside.toc ul{column-count:2;column-gap:28px;border-left:none;}main.content{max-width:100%;}.tocm summary::after{content:"▾";font-size:13px;color:var(--ink2);margin-left:10px;}}
@media (max-width:640px){.doctitle{padding:60px 16px 40px}.titleline{flex-direction:column;gap:16px}.doctitle h1{font-size:42px;letter-spacing:.1em}.doctitle .seal{width:34px;height:48px;font-size:18px;border-radius:6px;margin-left:10px}.doctitle .sub{font-size:12.5px;letter-spacing:.2em;margin-top:12px}.yt{font-size:13px;padding:7px 16px}.intro{margin:0 auto 48px;font-size:15px;padding:0 6px}.layout{padding:0 18px 72px;gap:24px}aside.toc ul{column-count:1}.tocm summary{font-size:20px}.toc a{font-size:13.5px;padding:7px 10px}.entry summary{flex-wrap:wrap;gap:6px 12px;padding:20px 0}.entry summary h2{font-size:18px;flex:1 1 100%}.entry summary .date{font-size:12px}.entry summary::before{font-size:13px}.entry-body{padding:2px 0 34px;font-size:16.5px;line-height:1.95}.entry-body h3{font-size:18px;margin:30px 0 12px}.entry-body blockquote{padding-left:14px;font-size:15.5px}footer{padding:44px 16px 52px}.fbtn{display:block;width:fit-content;margin:10px auto;padding:10px 24px}.navstack{right:14px;bottom:20px;gap:8px}.navbtn{width:40px;height:40px;font-size:15px}#toggle{width:36px;height:36px;font-size:16px}}
"""

js = """<script>
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
function findCur(){var best=null;document.querySelectorAll('.entry').forEach(function(e){var r=e.getBoundingClientRect();if(r.top<=120){best=e;}});if(best){cur=best.id;}return cur;}
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
(function(){var d=document.querySelector('details.tocm');if(d){function sync(){if(window.innerWidth>960){d.open=true;}}sync();window.addEventListener('resize',sync);}})();
</script>"""

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
<style>{css}</style>
</head>
<body id="top">
<div id="progress"></div>
<header class="hero"><img class="cover" src="cover.jpg" alt="归海录封面"></header>
<div class="paper">
  <div class="doctitle">
    <div class="titleline">
      <h1>归海录<span class="seal">归<br>海</span></h1>
      <a class="yt" href="https://www.youtube.com/@zyxk999" target="_blank" rel="noopener">▶ YouTube</a>
    </div>
    <div class="sub">归海2026 · 师父志远行空的开示合集</div>
  </div>
{body_html}
</div>
<footer>
  <div class="flinks">
    <a class="fbtn" href="https://www.youtube.com/@zyxk999" target="_blank" rel="noopener">▶ 师父 YouTube 频道</a>
    <a class="fbtn" href="https://u78zyhf3gaz.jp.larksuite.com/docx/QKYtdsvHzoH1aIxuGhrjD81EpWf" target="_blank" rel="noopener">📿 归海录 · Lark 源文档</a>
  </div>
  <div class="fmeta">归海录 · 持续更新中 ｜ 更新日期：2026-09-15</div>
</footer>
<div class="navstack">
  <button class="navbtn" id="toReading" title="回到当前阅读标题" aria-label="回到当前阅读标题">📖</button>
  <button class="navbtn" id="toTop" title="回到文档顶部" aria-label="回到文档顶部">↑</button>
</div>
<button id="toggle" aria-label="切换深浅色">🌙</button>
{js}
</body>
</html>"""

out = HERE / "index.html"
out.write_text(html, encoding="utf-8")
print(f"OK: {out} ({out.stat().st_size/1024:.0f} KB)")
