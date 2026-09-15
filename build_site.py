# -*- coding: utf-8 -*-
"""归海录静态站构建：guihailu.md -> index.html（pandoc 转换）"""
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

# 5) 组装 index.html
css = """
:root{--bg:#0b1220;--bg2:#101a2e;--gold:#d4af6a;--gold2:#b08d4f;--ink:#e8e2d5;--ink2:#a9a18f;--line:#2a3550;}
*{box-sizing:border-box}
html{scroll-behavior:smooth}
body{margin:0;background:var(--bg);color:var(--ink);font-family:"PingFang SC","Hiragino Sans GB","Microsoft YaHei","Noto Sans SC",-apple-system,"Segoe UI",sans-serif;line-height:1.85;font-size:17px;}
.wrap{max-width:860px;margin:0 auto;padding:0 20px 80px;}
header.hero{padding:72px 0 36px;text-align:center;border-bottom:1px solid var(--line);margin-bottom:40px;background:radial-gradient(ellipse at 50% 0%,rgba(212,175,106,.12),transparent 60%);}
header.hero h1{margin:0 0 14px;font-size:44px;letter-spacing:.12em;color:var(--gold);font-weight:700;}
header.hero .sub{color:var(--ink2);font-size:16px;letter-spacing:.05em;}
header.hero .intro{margin:22px auto 0;max-width:640px;color:var(--ink);background:var(--bg2);border:1px solid var(--line);border-left:3px solid var(--gold);border-radius:10px;padding:16px 22px;text-align:left;font-size:15px;}
.toc{background:var(--bg2);border:1px solid var(--line);border-radius:12px;padding:22px 28px;margin:0 0 48px;}
.toc h2{margin:0 0 14px;color:var(--gold);font-size:20px;border:none;padding:0;}
.toc ul{margin:0;padding-left:22px;column-count:2;column-gap:40px;}
.toc li{margin:7px 0;line-height:1.6;break-inside:avoid;}
.toc a{color:var(--ink);text-decoration:none;font-size:15px;}
.toc a:hover{color:var(--gold);}
.wrap h2{color:var(--gold);font-size:27px;margin:64px 0 16px;padding-bottom:10px;border-bottom:1px solid var(--line);line-height:1.5;}
.wrap h3{color:var(--gold2);font-size:21px;margin:36px 0 12px;}
.wrap h4{color:var(--ink);font-size:18px;margin:28px 0 10px;}
.wrap p{margin:14px 0;}
.wrap blockquote{margin:18px 0;padding:12px 20px;background:rgba(212,175,106,.06);border-left:3px solid var(--gold);border-radius:0 8px 8px 0;color:#cfc6b2;}
.wrap blockquote p{margin:6px 0;}
.wrap ul,.wrap ol{padding-left:26px;}
.wrap li{margin:7px 0;}
.wrap a{color:#8fb6e8;text-decoration:none;border-bottom:1px dotted #4a5a7a;}
.wrap a:hover{color:var(--gold);}
.wrap table{width:100%;border-collapse:collapse;margin:20px 0;font-size:15px;display:block;overflow-x:auto;}
.wrap th,.wrap td{border:1px solid var(--line);padding:9px 13px;text-align:left;}
.wrap th{background:var(--bg2);color:var(--gold);}
.wrap hr{border:none;border-top:1px solid var(--line);margin:48px 0;}
.wrap img{max-width:100%;border-radius:10px;}
footer{margin-top:70px;padding-top:26px;border-top:1px solid var(--line);color:var(--ink2);font-size:14px;text-align:center;}
footer a{color:#8fb6e8;text-decoration:none;}
.backtop{position:fixed;right:22px;bottom:22px;width:44px;height:44px;border-radius:50%;background:var(--bg2);border:1px solid var(--gold);color:var(--gold);font-size:20px;cursor:pointer;opacity:.85;}
@media (max-width:640px){header.hero h1{font-size:32px}.wrap h2{font-size:23px}.wrap{padding:0 15px 60px}body{font-size:16px}.toc ul{column-count:1}}
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
<style>{css}</style>
</head>
<body id="top">
<header class="hero">
  <h1>📿 归海录</h1>
  <div class="sub">归海2026 · 师父志远行空的开示合集</div>
  <div class="intro">本合集收录师父在「归海2026」群中的日常开示与 YouTube 视频讲法。每一段语音，一个故事，一个道理，润物无声。此合集按时间倒序整理，持续更新。欢迎随手转发、复制分享——让智慧流到更多人那里。</div>
</header>
<div class="wrap">
{body_html}
<footer>
  归海录 · 持续更新中<br>
  更新日期：2026-09-15 ｜ 源文档（Lark 版，需登录）：<a href="https://u78zyhf3gaz.jp.larksuite.com/docx/QKYtdsvHzoH1aIxuGhrjD81EpWf">📿 归海录</a>
</footer>
</div>
<button class="backtop" onclick="window.scrollTo({{top:0,behavior:'smooth'}})" aria-label="回到顶部">↑</button>
</body>
</html>"""

out = HERE / "index.html"
out.write_text(html, encoding="utf-8")
print(f"OK: {out} ({out.stat().st_size/1024:.0f} KB)")
