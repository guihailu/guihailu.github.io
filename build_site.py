# -*- coding: utf-8 -*-
"""归海录静态站构建：guihailu.md -> index.html（pandoc 转换）· 深蓝鎏金×宣纸书卷融合版"""
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

# 把目录部分包进 <div class="toc">
body_html = body_html.replace(
    '<h2 id="目录">📋 目录</h2>',
    '<div class="toc"><h2 id="目录">📋 目录</h2>', 1)
i = body_html.find('<h2 id="sec-')
if i > 0:
    body_html = body_html[:i] + '</div>\n' + body_html[i:]

# 4.5) 每条目包成折叠卡片：id 移到 details 上，日期徽章移进 summary（h2/h3 两种锚点都处理）
def wrap_entries(b):
    pat = re.compile(r'<h([23]) id="sec-(\d+)">(.*?)</h\1>\n', re.S)
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

# 5) 组装 index.html（深蓝鎏金 hero + 宣纸正文）
css = """
:root{--deep:#0b1424;--deep2:#101d36;--gold:#c9a45c;--gold2:#e6c886;--paper:#f6f0e0;--paper2:#efe5cc;--paper3:#e8dcc0;--ink:#2c2518;--ink2:#6f6248;--cin:#b03a2e;--line:#d9caa5;--link:#8a4a3c;--quote:#4a3f2a;--th-ink:#7c3a22;--shadow:rgba(11,20,36,.25);}
html.dark{--paper:#0f1a30;--paper2:#14203a;--paper3:#1b2a49;--ink:#e8e0c8;--ink2:#a89c7e;--cin:#d9744f;--line:#2c3d60;--link:#8fb6e8;--quote:#cfc6b2;--th-ink:#e6c886;--shadow:rgba(0,0,0,.5);}
*{box-sizing:border-box}
html{scroll-behavior:smooth}
body{margin:0;background:var(--deep);color:var(--ink);font-family:"Noto Serif SC","Source Han Serif SC","STZhongsong","Songti SC","SimSun",serif;line-height:1.9;font-size:17px;}
#progress{position:fixed;top:0;left:0;height:3px;width:0;background:linear-gradient(90deg,#8a6a2f,var(--gold2),#8a6a2f);z-index:99;}
header.hero{padding:44px 20px 120px;text-align:center;color:#f2ead8;background:radial-gradient(ellipse at 50% -10%,rgba(201,164,92,.10),transparent 55%);}
header.hero .coverwrap{max-width:880px;margin:0 auto 40px;border-radius:16px;overflow:hidden;box-shadow:0 10px 40px rgba(0,0,0,.45);}
header.hero .coverwrap img{display:block;width:100%;height:auto;}
header.hero h1{margin:0 0 10px;font-size:52px;letter-spacing:.18em;color:var(--gold2);font-weight:600;text-shadow:0 2px 18px rgba(0,0,0,.55);}
header.hero .seal{display:inline-block;margin-left:14px;vertical-align:6px;width:46px;height:46px;border-radius:8px;background:linear-gradient(160deg,#c24430,#93291b);color:#fff5e0;font-size:15px;line-height:23px;text-align:center;padding-top:1px;letter-spacing:0;box-shadow:0 2px 8px rgba(0,0,0,.4);font-family:"KaiTi","STKaiti",serif;}
header.hero .sub{margin:6px 0 0;color:#cbbd9c;font-size:16px;letter-spacing:.28em;}
header.hero .intro{max-width:660px;margin:30px auto 0;text-align:left;font-size:15px;color:#e9dfc6;background:rgba(16,29,54,.55);border:1px solid rgba(201,164,92,.35);border-left:3px solid var(--gold);border-radius:10px;padding:16px 22px;backdrop-filter:blur(2px);}
.paper{background:var(--paper);background-image:radial-gradient(rgba(180,160,120,.07) 1px,transparent 1px);background-size:22px 22px;border-radius:18px 18px 0 0;margin-top:-56px;position:relative;z-index:1;box-shadow:0 -6px 30px rgba(0,0,0,.25);}
html.dark .paper{background-image:radial-gradient(rgba(255,255,255,.04) 1px,transparent 1px);}
.wrap{max-width:880px;margin:0 auto;padding:48px 28px 90px;}
.toc{background:var(--paper2);border:1px solid var(--line);border-radius:14px;padding:26px 30px;margin:0 0 52px;box-shadow:0 2px 10px rgba(140,120,80,.10);}
.toc h2{margin:0 0 18px;color:var(--cin);font-size:22px;border:none;padding:0;letter-spacing:.15em;display:flex;align-items:center;gap:10px;}
.toc h2::after{content:"";flex:1;height:1px;background:linear-gradient(90deg,var(--line),transparent);}
.toc ul{margin:0;padding-left:4px;list-style:none;column-count:2;column-gap:44px;}
.toc li{margin:9px 0;line-height:1.6;break-inside:avoid;padding-left:20px;position:relative;}
.toc li::before{content:"▪";position:absolute;left:0;top:1px;color:var(--cin);font-size:13px;}
.toc a{color:var(--ink);text-decoration:none;font-size:15px;}
.toc a:hover{color:var(--cin);}
.toc a.done{color:var(--ink2);}
.toc a.done::after{content:" ✓";color:var(--cin);font-size:12px;}
.toc a.here{color:var(--cin);font-weight:600;}
.wrap h2{color:var(--ink);font-size:28px;margin:72px 0 18px;padding:0 0 12px 18px;border-bottom:1px solid var(--line);border-left:5px solid var(--cin);line-height:1.5;letter-spacing:.04em;}
.entry{margin:30px 0;border:1px solid var(--line);border-radius:14px;background:var(--paper2);overflow:hidden;box-shadow:0 2px 10px rgba(140,120,80,.08);}
.entry summary{cursor:pointer;list-style:none;display:flex;align-items:center;gap:14px;padding:18px 24px;}
.entry summary::-webkit-details-marker{display:none;}
.entry summary h2{margin:0;padding:0;border:none;font-size:20px;flex:1;color:var(--ink);line-height:1.6;}
.entry summary::before{content:"＋";color:var(--cin);font-size:19px;flex:none;}
.entry[open] summary::before{content:"－";}
.entry summary .date{color:var(--ink2);font-size:13px;flex:none;white-space:nowrap;}
.entry-body{padding:6px 26px 28px;border-top:1px dashed var(--line);}
.entry-body h3{color:var(--cin);font-size:21px;margin:34px 0 14px;letter-spacing:.05em;}
.wrap h3{color:var(--cin);font-size:21px;margin:40px 0 14px;letter-spacing:.05em;}
.wrap h4{color:var(--ink);font-size:18px;margin:30px 0 10px;}
.wrap p{margin:15px 0;}
.wrap blockquote{margin:20px 0;padding:14px 22px;background:var(--paper2);border-left:4px solid var(--cin);border-radius:0 10px 10px 0;color:var(--quote);box-shadow:0 1px 6px rgba(140,120,80,.10);}
.wrap blockquote p{margin:7px 0;}
.wrap ul,.wrap ol{padding-left:28px;}
.wrap li{margin:8px 0;}
.wrap a{color:var(--link);text-decoration:none;border-bottom:1px dashed var(--cin);}
.wrap a:hover{color:var(--cin);border-bottom-style:solid;}
.wrap table{width:100%;border-collapse:collapse;margin:22px 0;font-size:15px;display:block;overflow-x:auto;}
.wrap th,.wrap td{border:1px solid var(--line);padding:10px 14px;text-align:left;}
.wrap th{background:var(--paper3);color:var(--th-ink);}
.wrap hr{border:none;border-top:1px dashed var(--line);margin:52px 0;position:relative;}
.wrap hr::after{content:"❖";position:absolute;left:50%;top:-12px;transform:translateX(-50%);background:var(--paper);color:var(--cin);padding:0 10px;font-size:13px;}
.wrap img{max-width:100%;border-radius:12px;}
footer{background:var(--deep);color:#b9ab8a;font-size:14px;text-align:center;padding:34px 20px 44px;letter-spacing:.06em;}
footer a{color:var(--gold2);text-decoration:none;}
footer .goldline{width:120px;height:1px;background:linear-gradient(90deg,transparent,var(--gold),transparent);margin:0 auto 18px;}
.backtop{position:fixed;right:24px;bottom:26px;width:46px;height:46px;border-radius:9px;background:linear-gradient(160deg,#c24430,#93291b);color:#fff5e0;font-size:19px;cursor:pointer;border:none;box-shadow:0 3px 12px rgba(0,0,0,.35);opacity:.9;font-family:inherit;}
#toggle{position:fixed;top:16px;right:16px;width:42px;height:42px;border-radius:50%;background:rgba(16,29,54,.55);border:1px solid var(--gold);color:var(--gold2);font-size:19px;cursor:pointer;z-index:100;backdrop-filter:blur(3px);}
.backtop:hover{opacity:1;}
@media (max-width:640px){header.hero h1{font-size:36px;letter-spacing:.12em}header.hero{padding:64px 16px 100px}.wrap{padding:36px 18px 70px}.wrap h2{font-size:23px;padding-left:13px}.toc ul{column-count:1}body{font-size:16px}.toc{padding:20px}}
"""

js = """<script>
(function(){var p=document.getElementById('progress');function upd(){var h=document.documentElement;var d=h.scrollHeight-h.clientHeight;p.style.width=(d>0?(h.scrollTop/d)*100:0)+'%';}document.addEventListener('scroll',upd,{passive:true});upd();})();
(function(){var b=document.getElementById('toggle');function sync(){var d=document.documentElement.classList.contains('dark');b.textContent=d?'☀️':'🌙';}b.addEventListener('click',function(){document.documentElement.classList.toggle('dark');try{localStorage.setItem('ghl_theme',document.documentElement.classList.contains('dark')?'dark':'light')}catch(e){}sync();});sync();})();
(function(){var read=[];try{read=JSON.parse(localStorage.getItem('ghl_read')||'[]')}catch(e){}
document.querySelectorAll('.toc a[href^="#sec-"]').forEach(function(a){
  var id=a.getAttribute('href').slice(1);
  if(read.indexOf(id)>-1){a.classList.add('done')}
  a.addEventListener('click',function(){
    var d=document.getElementById(id);
    if(d){d.open=true;if(read.indexOf(id)<0){read.push(id);try{localStorage.setItem('ghl_read',JSON.stringify(read))}catch(e){}}}
    document.querySelectorAll('.toc a.here').forEach(function(x){x.classList.remove('here')});
    a.classList.add('here');a.classList.add('done');
  });
});
var saved=0;try{saved=parseInt(localStorage.getItem('ghl_scroll')||'0',10)}catch(e){}
if(saved>0&&!location.hash){window.scrollTo(0,saved)}
var t;document.addEventListener('scroll',function(){clearTimeout(t);t=setTimeout(function(){try{localStorage.setItem('ghl_scroll',String(window.scrollY))}catch(e){}},400)},{passive:true});
})();
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
<header class="hero">
  <div class="coverwrap"><img src="cover.jpg" alt="归海录封面"></div>
  <h1>归海录<span class="seal">歸海<br>之錄</span></h1>
  <div class="sub">归海2026 · 师父志远行空的开示合集</div>
  <div class="intro">本合集收录师父在「归海2026」群中的日常开示与 YouTube 视频讲法。每一段语音，一个故事，一个道理，润物无声。此合集按时间倒序整理，持续更新。欢迎随手转发、复制分享——让智慧流到更多人那里。</div>
</header>
<div class="paper">
<div class="wrap">
{body_html}
</div>
</div>
<footer>
  <div class="goldline"></div>
  归海录 · 持续更新中 ｜ 更新日期：2026-09-15<br>
  源文档（Lark 版，需登录）：<a href="https://u78zyhf3gaz.jp.larksuite.com/docx/QKYtdsvHzoH1aIxuGhrjD81EpWf">📿 归海录</a>
</footer>
<button class="backtop" onclick="window.scrollTo({{top:0,behavior:'smooth'}})" aria-label="回到顶部">↑</button>
<button id="toggle" aria-label="切换深浅色">🌙</button>
{js}
</body>
</html>"""

out = HERE / "index.html"
out.write_text(html, encoding="utf-8")
print(f"OK: {out} ({out.stat().st_size/1024:.0f} KB)")
