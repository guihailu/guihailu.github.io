# -*- coding: utf-8 -*-
"""归海录静态站构建：guihailu.md -> index.html（pandoc 转换）
设计语言（照抄顶级站手法）：Apple CN 超大标题+留白 / Medium 衬线窄栏阅读 / VitePress 侧栏目录"""
import re, pathlib, subprocess, sys, json, hashlib, html as _html
from guide_data import GUIDE, ALIASES  # 问题入口数据（10-17 施工窗 2）

HERE = pathlib.Path(__file__).parent
SRC = HERE / "guihailu.md"

# 繁→简归一表（10-17 施工窗 2）：t2s.json（pair 串，构建端与前端共用）；缺失时降级为空表仅 WARN
try:
    _t2s_pairs = json.loads((HERE / "t2s.json").read_text(encoding="utf-8"))["pairs"]
    T2S = {_t2s_pairs[i]: _t2s_pairs[i + 1] for i in range(0, len(_t2s_pairs), 2)}
except Exception as _e:
    print("WARN t2s.json 读取失败，简繁归一降级:", _e)
    _t2s_pairs, T2S = "", {}

def norm_s(s):
    return "".join(T2S.get(c, c) for c in s)

md = SRC.read_text(encoding="utf-8")

# 1) 去掉 <title> 行
md = re.sub(r"<title>.*?</title>\n", "", md)

# 1.5) 前置元数据清理（09-19 Eli 令）：以下三类块在 Lark 中位于条目标题之前，
# 站点卡片切分时会落入前一张卡片尾部造成孤行/错位——构建时跳过，不碰 Lark 源、不改文字。
# ① 日期头 h2（与各条目 📌 callout 内容重复）
md = re.sub(r'^## 日期不详 · 内部分享\n+', '', md, flags=re.M)
# ② 「主题：」裸行（条目 h1 标题已含主题）
md = re.sub(r'^主题：[^\n]+\n+', '', md, flags=re.M)
# ③ 💜 前置日期 callout（「日期行+主题行」形态；正文/前言中的 💜 不含日期行，不匹配）
md = re.sub(r'<callout emoji="💜">\n\*\*20\d{2}-\d{2}-\d{2}[^*]*\*\*\n\*\*主题：[^*]*\*\*\n</callout>\n*', '', md)

# 1.7) 简介结缘语（🌿…🌹）：保证独立段落与三行换行——Lark 的 <br/> 在 callout→blockquote 的 rstrip 下会丢，这里显式补回
md = md.replace('持续更新。\n🌿 学到知识以后', '持续更新。\n\n🌿 学到知识以后')
md = md.replace('缘分。  \n这是对善知识的回应', '缘分。<br>\n这是对善知识的回应')
md = md.replace('善链接。  \n能够帮助您', '善链接。<br>\n能够帮助您')

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
md = md.replace("日期不详 · 内部分享", "内部分享")

# 2.6) 合并相邻同 URL 的链接段（此前对 TOC 链接文本做 str_replace 时，
# Lark 会把一段链接拆成多段同 URL 链接；此处规范化回单段，保住 TOC 解析）
merge_seg = re.compile(r'\[([^\]]*)\]\((https://[^)]+)\)\[([^\]]*)\]\(\2\)')
while True:
    md2 = merge_seg.sub(r'[\1\3](\2)', md)
    if md2 == md:
        break
    md = md2

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

# 3.1) 永久 ID 注册表（10-14 迁移）：键=doxjp block id，值=ghl-NNNNNN；只增不删不重用；内容决定、幂等
IDMAP_F = HERE / "id_map.json"
LEGACY_F = HERE / "legacy_anchors.json"
id_map = {}
if IDMAP_F.exists():
    try:
        id_map = json.loads(IDMAP_F.read_text(encoding="utf-8"))
    except Exception as e:
        print("WARN id_map.json 解析失败，按空表处理:", e)
        id_map = {}
_maxnum = 0
for _v in id_map.values():
    _m = re.fullmatch(r"ghl-(\d+)", str(_v or ""))
    if _m:
        _maxnum = max(_maxnum, int(_m.group(1)))
_legacy_existed = LEGACY_F.exists()
migration_legacy = {}
print(f"永久ID: 注册表 {len(id_map)} 条（最大号 ghl-{_maxnum:06d}）｜legacy {'已读取（冻结）' if _legacy_existed else '待生成（迁移首跑）'}")

id_of_title = {}   # 标题原文 -> 永久 id（ghl-NNNNNN）
used = set()
unmatched = []
_seen_bids = set()
for i, (text, bid) in enumerate(toc_items, 1):
    t = norm(text.split(" ｜ ")[0].strip())
    # 永久 ID：以 doxjp 为键发号/取号（新键=当前最大+1，只增不删不重用）
    if bid in _seen_bids:
        print("  WARN 目录重复 doxjp:", bid)
    _seen_bids.add(bid)
    if bid not in id_map:
        _maxnum += 1
        id_map[bid] = f"ghl-{_maxnum:06d}"
    sid = id_map[bid]
    old_sid = f"sec-{i:02d}"   # 旧顺序锚：仅迁移首跑用于冻结 legacy 表
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
    id_of_title[ht] = sid
    if not _legacy_existed:
        migration_legacy[old_sid] = sid

if unmatched:
    print("  UNMATCHED:", *unmatched, sep="\n    ")

# 3.2) 注册表落盘：id_map 只增不删；legacy 迁移首跑冻结后只读（10-14）
if _legacy_existed:
    try:
        legacy_map = json.loads(LEGACY_F.read_text(encoding="utf-8"))
    except Exception as e:
        print("WARN legacy_anchors.json 解析失败，按空表处理:", e)
        legacy_map = {}
else:
    legacy_map = migration_legacy
    LEGACY_F.write_text(
        json.dumps(dict(sorted(legacy_map.items())), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8", newline="\n")
    print(f"OK: legacy_anchors.json 已生成并冻结（迁移快照 {len(legacy_map)} 条）")
_ids_sorted = sorted(id_map.items(), key=lambda kv: int(kv[1].split("-")[1]))
_idmap_txt = json.dumps(dict(_ids_sorted), ensure_ascii=False, indent=2) + "\n"
if (not IDMAP_F.exists()) or IDMAP_F.read_text(encoding="utf-8") != _idmap_txt:
    IDMAP_F.write_text(_idmap_txt, encoding="utf-8", newline="\n")
    print(f"OK: id_map.json 写入（{len(id_map)} 条）")
else:
    print(f"OK: id_map.json 未变（{len(id_map)} 条）")
legacy_json = json.dumps(legacy_map, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")

# TOC 链接 -> 页内锚点
def toc_repl(m):
    text, bid = m.group(1), m.group(2)
    t = norm(text.split(" ｜ ")[0].strip())
    # 精确匹配优先（两遍式）——避免「…（上/中/下）」等同前缀标题全部命中最早一条（10-14 修正旧缺陷）
    for ht, sid in id_of_title.items():
        if norm(ht) == t:
            return f"- [{text}](#{sid})"
    for ht, sid in id_of_title.items():
        if common_prefix(norm(ht), t) >= 6:
            return f"- [{text}](#{sid})"
    return f"- [{text}](#top)"

md = toc_pat.sub(toc_repl, md)

# 正文标题加锚点（按标题原文唯一替换；id 随 doxjp 注册，永不漂移）
_injected = set()
for ht, sid in id_of_title.items():
    if sid in _injected:
        continue   # 防御：目录重复 doxjp 时同一 id 不重复注入
    pat = re.compile(rf'^(#{{1,2}}) ({re.escape(ht)})$', re.M)
    md = pat.sub(rf'\1 \2 {{#{sid}}}', md, count=1)
    _injected.add(sid)

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
    pat = re.compile(r'<h([23])\s+id="(ghl-\d+)">(.*?)</h\1>\n', re.S)
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
            f'<details class="entry" id="{sid}">'
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

# 4.65) 旧锚兼容空 span（10-14）：按冻结的 legacy 映射在对应条目前注入 <span id="sec-NN" class="lanchor">，
# 锚随条目走、永不漂移；空 span 位于闭卡之外——无 JS 时浏览器原生跳转亦可命中
_rev_legacy = {}
for _k, _v in legacy_map.items():
    _rev_legacy.setdefault(_v, []).append(_k)
def inject_lanchors(b):
    def _rep(m):
        return ''.join(f'<span id="{k}" class="lanchor"></span>'
                       for k in sorted(_rev_legacy.get(m.group(1), []))) + m.group(0)
    return re.sub(r'<details class="entry" id="(ghl-\d+)">', _rep, b)
body_html = inject_lanchors(body_html)

# 4.7) 文档自带的 💜 简介 callout -> 引言段落（去重：页面标题下不再重复放简介）
def intro_repl(m):
    title, _, body = m.group(1).partition('</strong>')
    body = body.replace('每一段语音', '</p><p class="intro-copy">每一段语音', 1)
    body = body.replace('此合集按时间倒序整理', '</p><p class="intro-note">此合集按时间倒序整理', 1)
    extra = (m.group(2) or '').strip()
    extra_html = f'<p class="intro-copy">{extra}</p>' if extra else ''
    return f'<div class="intro"><p class="intro-title">{title}</strong></p><p class="intro-copy">{body}</p>{extra_html}</div>'

body_html = re.sub(
    r'<blockquote>\s*<p>💜</p>\s*<p>(<strong>归海2026.*?)</p>\s*(?:<p>(.*?)</p>\s*)?</blockquote>',
    intro_repl, body_html, count=1, flags=re.S)

# 4.8) 页脚「内容更新至」日期（10-14）：取全部条目徽章中最大合法日期——内容决定、保持幂等
_latest_date = ""
for _dspan in re.finditer(r'<span class="date">(.*?)</span>', body_html, re.S):
    for _dv in re.findall(r'20\d{2}-\d{2}-\d{2}', _dspan.group(1)):
        if _dv > _latest_date:
            _latest_date = _dv
_footer_date = f" ｜ 内容更新至 {_latest_date}" if _latest_date else ""
print(f"页脚日期: {_latest_date or '(未取到，省略)'}")

# 4.9) 「第一次来」问题入口区（10-17 施工窗 2）：guide 数据渲染为三卡；id 缺失即 WARN 并跳过该条
_guide_html = ""
try:
    _known_ids = set(id_map.values())
    _miss = sorted({r["id"] for g in GUIDE for r in g["reads"]} - _known_ids |
                   {k for k in ALIASES if k not in _known_ids})
    if _miss:
        print("WARN guide/aliases 引用缺失 id:", _miss)
    _cards = []
    for g in GUIDE:
        _reads = [r for r in g["reads"] if r["id"] in _known_ids]
        if not _reads:
            continue
        _chips = "".join(
            f'<button type="button" class="ft-chip" data-q="{_html.escape(c, quote=True)}">{_html.escape(c)}</button>'
            for c in g["chips"])
        _ritems = "".join(
            f'<li><span class="ft-r">{_html.escape(r["role"])}</span>'
            f'<a href="#{r["id"]}">{_html.escape(r["label"])}</a></li>'
            for r in _reads)
        _cards.append(
            f'<article class="ftcard"><h3 class="ft-t">{_html.escape(g["title"])}</h3>'
            f'<p class="ft-scene">{_html.escape(g["scene"])}</p>'
            f'<blockquote class="ft-quote"><p>{_html.escape(g["quote"])}</p>'
            f'<cite>— <a href="#{_reads[0]["id"]}">{_html.escape(_reads[0]["label"])}</a></cite></blockquote>'
            f'<div class="ft-chips">{_chips}</div>'
            f'<ul class="ft-reads">{_ritems}</ul>'
            f'<p class="ft-notice">{_html.escape(g["notice"])}</p></article>')
    if _cards:
        _guide_html = ('<section class="firsttime" id="firsttime"><h2 class="ft-h">第一次来？从这里出发</h2>'
                       '<p class="ft-sub">按场景导航 · 推荐与提示为编辑整理，非原典内容</p>'
                       '<div class="ftcards">' + "".join(_cards) + '</div></section>')
    _anchor = '<div class="layout">'
    if _guide_html and _anchor in body_html:
        body_html = body_html.replace(_anchor, _guide_html + _anchor, 1)
        print(f"OK: 「第一次来」区已插入（{len(_cards)} 卡）")
    else:
        print("WARN 「第一次来」区未插入（anchor 缺失或无卡）")
except Exception as e:
    print("WARN 「第一次来」区生成失败:", e)

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
.intro .intro-copy+.intro-copy{margin-top:12px}.intro .intro-note{margin-top:18px;font-size:13px;line-height:1.8}.intro .intro-note+.intro-copy{margin-top:16px}
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
.entry:first-of-type{border-top:1px solid var(--line)}
.lanchor{display:block;width:0;height:0;overflow:hidden;scroll-margin-top:24px}
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
.navstack{position:fixed;right:22px;bottom:24px;z-index:98;display:flex;flex-direction:column;align-items:flex-end;gap:10px}
.navbtn{display:none;place-items:center;min-width:44px;height:44px;padding:0 16px;border:1px solid var(--gold);border-radius:999px;background:var(--deep);color:var(--gold2);font-size:14px;font-weight:600;line-height:1;cursor:pointer;transition:background .2s,color .2s}
.navbtn.nav-on,#toTop{display:grid}
.navbtn:hover{background:var(--gold2);color:var(--deep)}
#toggle{display:grid;place-items:center;width:44px;height:44px;border:1px solid var(--gold);border-radius:50%;background:var(--deep);color:var(--gold2);font-size:17px;line-height:1;cursor:pointer;transition:background .2s,color .2s}
#toggle svg{display:block;margin:auto}
#toggle:hover{background:var(--gold2);color:var(--deep)}
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
  .intro{padding:42px 23px 38px;font-size:14.5px;line-height:1.95}.intro::before{margin-bottom:19px}.intro strong{font-size:16px}.intro .intro-copy{text-align:center}
  .layout{padding:0 20px 84px}.tocm>summary{padding:14px 0}.entry>summary{column-gap:11px;padding:20px 0}
  .entry>summary h2{font-size:18px;line-height:1.65}.entry>summary .date{font-size:11.5px}
  .entry-body{padding-bottom:37px;font-size:16.5px;line-height:2.05}.entry-body h3{font-size:18px}
  .entry-body blockquote{padding-left:15px;font-size:15.5px}
  footer{padding:48px 20px 56px}.fbtn{display:flex;width:max-content;margin:10px auto}
  .navstack{right:12px;bottom:calc(16px + env(safe-area-inset-bottom));gap:8px}
  .navbtn{min-width:40px;height:40px;padding:0 13px;font-size:13px}#toggle{width:40px;height:40px;font-size:16px;top:12px;right:12px}
}
@media(max-width:380px){.doctitle h1{font-size:42px}.doctitle .sub{letter-spacing:.05em}}
@media(prefers-reduced-motion:reduce){html{scroll-behavior:auto}*,*::before,*::after{transition:none!important}}
/* ---- 全文检索（10-07 新增）：搜索条 + 结果面板 ---- */
.searchbar{background:var(--deep);padding:0 24px 64px}
.searchwrap{position:relative;max-width:700px;margin:0 auto}
#q{width:100%;height:46px;padding:0 18px;border:1px solid var(--gold);border-radius:999px;background:rgba(250,248,241,.05);color:#faf8f1;font-size:14.5px;letter-spacing:.02em;outline:none;-webkit-appearance:none;appearance:none}
#q::placeholder{color:#9d927c}
#q:focus{background:rgba(250,248,241,.09);border-color:var(--gold2)}
#q::-webkit-search-cancel-button{filter:invert(.8)}
#qres{display:none;position:absolute;left:0;right:0;top:calc(100% + 8px);z-index:60;max-height:60vh;overflow:auto;-webkit-overflow-scrolling:touch;background:#101a2e;border:1px solid rgba(178,139,74,.45);border-radius:12px;box-shadow:0 18px 40px rgba(0,0,0,.45);text-align:left}
#qres.on{display:block}
.qcount{padding:9px 14px;border-bottom:1px solid rgba(178,139,74,.2);color:#c8baa0;font-size:12px}
.qitem{padding:11px 14px;border-bottom:1px solid rgba(178,139,74,.14);cursor:pointer}
.qitem:last-child{border-bottom:0}
.qitem:hover{background:rgba(178,139,74,.08)}
.qhead{display:flex;align-items:baseline;flex-wrap:wrap;gap:4px 8px}
.qt{color:#faf8f1;font-size:14.5px;font-weight:600;line-height:1.6}
.qd{color:#c8baa0;font-size:11.5px}
.qs{margin-top:3px;color:#b9b1a0;font-size:12.5px;line-height:1.7}
#qres mark{background:rgba(217,184,120,.35);color:#f3e9d2;border-radius:2px;padding:0 1px}
.qnone{padding:14px;color:#c8baa0;font-size:13.5px}
/* ---- 搜索 v2 补充（10-17 施工窗 2）：近似提示 + 问题入口引导面板 ---- */
.qnote{padding:10px 14px;border-bottom:1px solid rgba(178,139,74,.2);color:#c8baa0;font-size:12.5px;line-height:1.7}
.qguide{padding:10px 14px 12px}
.qgt{color:#c8baa0;font-size:12.5px;margin-bottom:7px}
.qgr{padding:7px 0;color:#e8ddc3;font-size:13.5px;font-weight:600;cursor:pointer;border-bottom:1px dashed rgba(178,139,74,.25)}
.qgr:last-child{border-bottom:0}
.qgr:hover{color:var(--gold2)}
@media(max-width:640px){.searchbar{padding:0 20px 46px}#q{height:44px;font-size:14px}#qres{max-height:55vh}.qt{font-size:14px}.qs{font-size:12px}}
/* ---- 「第一次来」问题入口（10-17 施工窗 2） ---- */
.firsttime{max-width:1024px;margin:0 auto;padding:0 32px 58px}
.ft-h{margin:0 0 7px;color:var(--ink);font-size:20px;font-weight:700;letter-spacing:.06em;text-align:center}
.ft-sub{margin:0 0 26px;color:var(--muted);font-size:12.5px;text-align:center;letter-spacing:.03em}
.ftcards{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:18px;align-items:start}
.ftcard{border:1px solid var(--line);border-radius:14px;background:var(--paper2);padding:20px 18px 15px}
.ft-t{margin:0 0 8px;color:var(--ink);font-size:16.5px;font-weight:700;line-height:1.5}
.ft-scene{margin:0;color:var(--muted);font-size:13px;line-height:1.85}
.ft-quote{margin:14px 0 12px;padding:0 0 0 12px;border-left:2px solid var(--gold);color:var(--quote);font-size:13px;line-height:1.8}
.ft-quote p{margin:0}
.ft-quote cite{display:block;margin-top:5px;color:var(--muted);font-size:11.5px;font-style:normal;line-height:1.6}
.ft-quote cite a{color:var(--muted);text-decoration:none;border-bottom:1px dotted var(--gold)}
.ft-quote cite a:hover{color:var(--link)}
.ft-chips{display:flex;flex-wrap:wrap;gap:6px;margin:0 0 13px}
.ft-chip{padding:3px 11px;border:1px solid var(--line);border-radius:999px;background:transparent;color:var(--muted);font-size:12px;line-height:1.7;cursor:pointer;font-family:inherit}
.ft-chip:hover{border-color:var(--gold);color:var(--ink)}
.ft-reads{margin:0;padding:0;list-style:none}
.ft-reads li{display:flex;align-items:baseline;gap:9px;margin:7px 0;font-size:13.5px;line-height:1.7}
.ft-r{flex:none;padding:1px 8px;border-radius:4px;background:var(--cin);color:#faf3ea;font-size:11px;letter-spacing:.08em;white-space:nowrap}
.ft-reads li:not(:first-child) .ft-r{background:transparent;border:1px solid var(--line);color:var(--muted)}
.ft-reads a{color:var(--ink);text-decoration:none;border-bottom:1px solid var(--gold)}
.ft-reads a:hover{color:var(--cin);border-color:var(--cin)}
.ft-notice{margin:12px 0 0;padding-top:9px;border-top:1px dashed var(--line);color:var(--muted);font-size:11.5px;line-height:1.75}
@media(max-width:960px){.firsttime{padding:0 20px 46px}.ftcards{grid-template-columns:1fr;gap:14px}}
"""

js = """
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
/* 旧 #sec-NN / 新 #ghl 直链（10-14）：载入时展开命中条目（原生锚点负责滚动，这里补展开） */
(function(){var LG=(window.__GHL_LEGACY__||{});var h=(location.hash||'').slice(1);if(!h)return;var t=/^sec-[0-9]+$/.test(h)?LG[h]:h;if(!t||!/^ghl-[0-9]+$/.test(t))return;var d=document.getElementById(t);if(d){d.open=true;}})();
(function(){var d=document.querySelector('details.tocm');if(d){var wide=null;function sync(){var now=window.innerWidth>960;if(now!==wide){d.open=now;wide=now;}}sync();window.addEventListener('resize',sync);}})();
(function(){var p=document.querySelector('.intro p');if(p&&p.firstChild&&p.firstChild.nodeType===3){p.firstChild.textContent=p.firstChild.textContent.replace('💜 ','');}})();
/* ---- 全文检索 v2（10-17 施工窗 2）：简繁归一 + 多字段排序 + 问题入口引导 ---- */
(function(){var box=document.getElementById('q'),res=document.getElementById('qres');if(!box||!res)return;var idx=null;var p=null;
function getIdx(){if(!p)p=(window.__GHL_INDEX__)?Promise.resolve(window.__GHL_INDEX__):fetch('search_index.json').then(function(r){if(!r.ok)throw 0;return r.json()}).catch(function(){return{entries:[],count:0,err:1}});return p;}
function esc(s){return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');}
var _t2s=null;
function norm(s){if(!_t2s){_t2s={};var pr=(idx&&idx.t2s)||'';for(var i=0;i<pr.length;i+=2)_t2s[pr[i]]=pr[i+1];}var o='';for(var j=0;j<s.length;j++){o+=(_t2s[s[j]]||s[j]);}return o;}
function cnt(h,n){var c=0,i=0;if(!n)return 0;for(;;){i=h.indexOf(n,i);if(i<0)return c;c++;i+=n.length;}}
function has4(a,b){if(a.length<4||b.length<4)return false;for(var i=0;i+4<=a.length;i++){if(b.indexOf(a.slice(i,i+4))>-1)return true;}return false;}
function thit(qs,s){if(!s||s.length<2||qs.length<2)return false;if(s.indexOf(qs)>-1)return true;if(qs.indexOf(s)>-1)return true;return has4(qs,s);}
function hl(orig,nq,lw){var i=nq.indexOf(lw);if(i<0)return esc(orig);return esc(orig.slice(0,i))+'<mark>'+esc(orig.slice(i,i+lw.length))+'</mark>'+esc(orig.slice(i+lw.length));}
function snipH(orig,nq,lw){var i=nq.indexOf(lw);var s=i<0?0:Math.max(0,i-15);var e0=Math.min(orig.length,s+60);var frag;if(i>=0&&i<e0){var i2=i-s;var mEnd=Math.min(i2+lw.length,e0-s);frag=esc(orig.slice(s,s+i2))+'<mark>'+esc(orig.slice(s+i2,s+mEnd))+'</mark>'+esc(orig.slice(s+mEnd,e0));}else{frag=esc(orig.slice(s,e0));}return (s>0?'…':'')+frag+(e0<orig.length?'…':'');}
function prep(){if(!idx||idx._warmed)return;idx._warmed=1;var es=idx.entries||[];for(var i=0;i<es.length;i++){var e=es[i];
var bt=String(e.title||''),bx=String(e.text||'');
if(e.titleN)bt=e.titleN;else if(e.titleP){var at=bt.split('');for(var p=0;p<e.titleP.length;p++){at[e.titleP[p][0]]=e.titleP[p][1];}bt=at.join('');}
if(e.textN)bx=e.textN;else if(e.textP){var ax=bx.split('');for(var q=0;q<e.textP.length;q++){ax[e.textP[q][0]]=e.textP[q][1];}bx=ax.join('');}
e._tl=bt.toLowerCase();e._xl=bx.toLowerCase();}}
function render(q){q=q.trim();if(!q){res.classList.remove('on');res.innerHTML='';return;}
getIdx().then(function(j){if(j)idx=j;
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
  for(i=0;i+2<=qs.length;i++){var bg=qs.slice(i,i+2);if(!/^[\\u4e00-\\u9fff]{2}$/.test(bg))continue;if(!seen[bg]){seen[bg]=1;bgs.push(bg);}}
  if(bgs.length>=2){for(i=0;i<es.length;i++){var e2=es[i],hn=0,sc=0,bb=null,bc=0;
    for(k=0;k<bgs.length;k++){var c4=cnt(e2._tl,bgs[k])*3+cnt(e2._xl,bgs[k]);if(c4>0){hn++;sc+=Math.min(c4,6);if(c4>bc){bc=c4;bb=bgs[k];}}}
    if(hn>=2){e2._s=sc;e2._bg=bb;e2._i=i;out.push(e2);soft=true;}}}
}
if(!out.length){
  var gg='';if(gh.length){gg='<div class="qguide"><div class="qgt">也可以从这里出发：</div>';for(i=0;i<gh.length;i++){gg+='<div class="qgr" data-goto="firsttime">'+esc(gh[i].title)+'</div>';}gg+='</div>';}
  res.innerHTML='<div class="qnone">没有找到与「'+esc(q)+'」相关的内容</div>'+gg;res.classList.add('on');return;
}
out.sort(function(a,b){return (b._s-a._s)||(a._i-b._i);});
var h='';
if(soft)h+='<div class="qnote">没有与「'+esc(q)+'」完全匹配的内容，以下按关键词近似检索：</div>';
h+='<div class="qcount">'+out.length+' 条结果'+(soft?'（近似）':'')+'</div>';
for(i=0;i<out.length;i++){var e3=out[i];var lw=(soft&&e3._bg)?e3._bg:qs;
  h+='<div class="qitem" data-id="'+e3.id+'"><div class="qhead"><span class="qt">'+hl(String(e3.title||''),e3._tl,lw)+'</span><span class="qd">'+esc(e3.date||'')+'</span></div><div class="qs">'+snipH(String(e3.text||''),e3._xl,lw)+'</div></div>';
}
res.innerHTML=h;res.classList.add('on');});}
box.addEventListener('input',function(){render(box.value)});
box.addEventListener('focus',function(){if(box.value.trim())render(box.value)});
res.addEventListener('click',function(ev){var n=ev.target;
while(n&&n!==res&&!(n.classList&&(n.classList.contains('qitem')||n.classList.contains('qgr'))))n=n.parentNode;
if(!n||n===res)return;
if(n.classList.contains('qgr')){res.classList.remove('on');var ft=document.getElementById('firsttime');if(ft)ft.scrollIntoView({behavior:'smooth',block:'start'});return;}
var id=n.getAttribute('data-id');res.classList.remove('on');var a=document.querySelector('.toc a[href="#'+id+'"]');if(a)a.click();var el=document.getElementById(id);if(el){setTimeout(function(){el.scrollIntoView({behavior:'smooth',block:'start'});},60);}});
document.addEventListener('click',function(ev){var n=ev.target;while(n){if(n.classList&&n.classList.contains('searchbar'))return;n=n.parentNode;}res.classList.remove('on');});
document.querySelectorAll('.ft-chip').forEach(function(b){b.addEventListener('click',function(){box.value=b.getAttribute('data-q');render(box.value);box.scrollIntoView({behavior:'smooth',block:'center'});try{box.focus({preventScroll:true})}catch(e){}});});
})();
/* 「第一次来」区文章链接（10-17 施工窗 2）：点击时展开对应条目（原生锚点负责滚动） */
(function(){document.querySelectorAll('.firsttime a[href^="#ghl-"]').forEach(function(a){a.addEventListener('click',function(){var d=document.getElementById(a.getAttribute('href').slice(1));if(d)d.open=true;});});})();
"""

html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>📿 归海录 · 志远行空</title>
<meta name="description" content="归海录：志远行空的日常分享与 YouTube 视频讲法合集——每一段语音，一个故事，一个道理，润物无声。按时间倒序，持续更新。">
<meta property="og:title" content="📿 归海录 · 志远行空">
<meta property="og:description" content="志远行空的日常分享与 YouTube 视频讲法合集。因果、修行、认知、人间智慧——百川归海，智慧汇流。">
<meta property="og:type" content="website">
<meta property="og:image" content="https://guihailu.github.io/cover.jpg">
<script>try{{if(localStorage.getItem('ghl_theme')==='dark')document.documentElement.classList.add('dark')}}catch(e){{}}</script>
<script>window.__GHL_LEGACY__={legacy_json};</script>
<link rel="stylesheet" href="style.v5.css">
</head>
<body id="top">
<div id="progress"></div>
<header class="hero">
  <div class="doctitle">
    <div class="titleline"><h1>归海录<span class="seal" aria-hidden="true">归<br>海</span></h1></div>
    <p class="sub">归海2026 · 志远行空</p>
    <a class="yt" href="https://www.youtube.com/@zyxk999" target="_blank" rel="noopener">▶ YouTube</a>
  </div>
</header>
<div class="searchbar"><div class="searchwrap"><input id="q" type="search" placeholder="搜索全文…" autocomplete="off" aria-label="搜索全文"><div id="qres"></div></div></div>
<div class="paper">
{body_html}
</div>
<footer>
  <div class="flinks">
    <a class="fbtn" href="https://www.youtube.com/@zyxk999" target="_blank" rel="noopener">▶ 志远行空 YouTube 频道</a>
    <a class="fbtn" href="https://u78zyhf3gaz.jp.larksuite.com/docx/QKYtdsvHzoH1aIxuGhrjD81EpWf" target="_blank" rel="noopener">📿 归海录 · Lark 源文档</a>
    <a class="fbtn" href="https://www.oceanwards.com/" target="_blank" rel="noopener">🌊 归海论坛</a>
    <a class="fbtn" href="归海录_离线版.html" download>📥 离线版下载</a>
  </div>
  <div class="fmeta">归海录 · 持续更新中{_footer_date}</div>
</footer>
<div class="navstack">
  <button class="navbtn" id="toReading" aria-label="回到本篇开头">↩ 本篇开头</button>
  <button class="navbtn" id="toTop" aria-label="回到文档顶部">↑ 顶部</button>
</div>
<button id="toggle" aria-label="切换深浅色">🌙</button>
<script src="main.v5.js" defer></script>
</body>
</html>"""

# 三文件输出：LF 行尾；CSS/主 JS 外置，页头保留主题初始化内联脚本
(HERE / "style.v5.css").write_text(css, encoding="utf-8", newline="\n")
(HERE / "main.v5.js").write_text(js, encoding="utf-8", newline="\n")
out = HERE / "index.html"
out.write_text(html, encoding="utf-8", newline="\n")

# 6) 全文检索索引 + 离线单文件版（10-07 新增；失败不阻塞主链路，退出码仍 0）
def _note(msg):
    with open(HERE / "sync_log.txt", "a", encoding="utf-8") as f:
        f.write(msg + "\n")

def _norm_extra(s):
    """10-17 施工窗 2：繁简归一差异补丁 [[位置,替换字],…]（位置按 UTF-16 码元计，与 JS 字符串索引一致，
    星平面字符出现前逐位补偿；替换字均为 BMP）。逐字符 1:1、与原文等长，保前端高亮定位。无差异返回 None。"""
    ns = norm_s(s)
    if ns == s:
        return None
    out, off = [], 0
    for i, (a, b) in enumerate(zip(s, ns)):
        if a != b:
            out.append([i + off, b])
        if ord(a) > 0xFFFF:
            off += 1
    return out

def _plain(s):
    s = re.sub(r'<[^>]+>', ' ', s or '')
    s = (s.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
           .replace('&quot;', '"').replace('&#39;', "'"))
    return re.sub(r'\s+', ' ', s).strip()

try:
    _items = []
    for m in re.finditer(r'<details class="entry" id="(ghl-\d+)">(.*?)</details>', body_html, re.S):
        sid, blk = m.group(1), m.group(2)
        tm = re.search(r'<h2>(.*?)</h2>', blk, re.S)
        dm = re.search(r'<span class="date">(.*?)</span>', blk, re.S)
        bm = re.search(r'<div class="entry-body">(.*)$', blk, re.S)
        _title = _plain(tm.group(1) if tm else '')
        # 10-14：date=首个合法 YYYY-MM-DD（不定则空，不伪造）；meta=徽章原文整串留档
        _meta = _plain(dm.group(1) if dm else '').replace('📌', '').strip()
        _dmm = re.search(r'20\d{2}-\d{2}-\d{2}', _meta)
        _date = _dmm.group(0) if _dmm else ''
        _text = _plain(bm.group(1) if bm else '')
        if sid and _title:
            _it = {"id": sid, "title": _title, "date": _date, "meta": _meta, "text": _text}
            # 10-17 施工窗 2：简繁归一增量（差异补丁，见 _norm_extra）+ 检索别名
            _te = _norm_extra(_title)
            if _te:
                _it["titleP"] = _te
            _xe = _norm_extra(_text)
            if _xe:
                _it["textP"] = _xe
            _al = ALIASES.get(sid)
            if _al:
                _it["aliases"] = list(_al)
            _items.append(_it)
    # 顶层新增 guide / t2s（10-17 施工窗 2）；指纹覆盖全部内容，保幂等
    _payload = {"guide": GUIDE, "t2s": _t2s_pairs, "entries": _items}
    _fp = hashlib.sha256(json.dumps(_payload, ensure_ascii=False, sort_keys=True,
                                    separators=(',', ':')).encode('utf-8')).hexdigest()[:12]
    _idx_json = json.dumps({"generated": _fp, "count": len(_items), "guide": GUIDE,
                            "t2s": _t2s_pairs, "entries": _items},
                           ensure_ascii=False, separators=(',', ':'))
    (HERE / "search_index.json").write_text(_idx_json + "\n", encoding="utf-8", newline="\n")
    print(f"OK: search_index.json {len(_items)} entries, fingerprint {_fp}")
except Exception as e:
    _note("WARN search_index 生成失败: %r" % (e,))
    print("WARN: search_index.json 生成失败:", e)

try:
    _off = html.replace('<link rel="stylesheet" href="style.v5.css">',
                        "<style>\n" + css + "</style>", 1)
    if '<style>' not in _off:
        raise ValueError('style 内联替换失败')
    _off = _off.replace('<script src="main.v5.js" defer></script>',
                        '<script>window.__GHL_INDEX__=' + _idx_json.replace('</', '<\\/') + ';</script>\n<script>' + js + '</script>', 1)
    if 'window.__GHL_INDEX__=' not in _off:
        raise ValueError('js 内联替换失败')
    _dl = '<a class="fbtn" href="归海录_离线版.html" download>📥 离线版下载</a>'
    if _dl not in _off:
        raise ValueError('下载入口锚点缺失')
    _off = _off.replace(_dl, '<span class="fbtn">📥 本页即离线版</span>', 1)
    # 离线版图片走在线链接：feishu 原链 → 站点已镜像的公开图（与 mirror_media 同源缓存；
    # 未命中则保留原链回落，不下载、不阻塞）
    _resolved = 0
    for _tok in dict.fromkeys(re.findall(r'https://feishu\.cn/file/([A-Za-z0-9]+)', _off)):
        _stem = hashlib.sha256(_tok.encode('ascii')).hexdigest()[:20]
        _cand = [p for p in (HERE / "media").glob(_stem + '.*')
                 if p.suffix.lower() in {'.png', '.jpg', '.jpeg', '.webp', '.gif'}]
        if len(_cand) == 1:
            _off = _off.replace('https://feishu.cn/file/' + _tok,
                                'https://guihailu.github.io/media/' + _cand[0].name)
            _resolved += 1
    (HERE / "归海录_离线版.html").write_text(_off, encoding="utf-8", newline="\n")
    print(f"OK: 归海录_离线版.html {(HERE/'归海录_离线版.html').stat().st_size} B | 在线图 {_resolved} 张")
except Exception as e:
    _note("WARN 离线版生成失败: %r" % (e,))
    print("WARN: 归海录_离线版.html 生成失败:", e)
print(f"OK: index.html {out.stat().st_size} B | style.v5.css {(HERE/'style.v5.css').stat().st_size} B | main.v5.js {(HERE/'main.v5.js').stat().st_size} B")
