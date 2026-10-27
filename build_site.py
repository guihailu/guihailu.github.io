# -*- coding: utf-8 -*-
"""归海录静态站构建：guihailu.md -> index.html（pandoc 转换）
设计语言（照抄顶级站手法）：Apple CN 超大标题+留白 / Medium 衬线窄栏阅读 / VitePress 侧栏目录"""
import re, pathlib, subprocess, sys, json, hashlib, html as _html, urllib.parse
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

# 分析服务（A/B/C）：默认 none，不加载任何第三方；填 analytics.json 后构建即启用
ANALYTICS = {}
try:
    ANALYTICS = json.loads((HERE / "analytics.json").read_text(encoding="utf-8"))
except Exception as _e:
    print("WARN analytics.json 读取失败，按 none 处理:", _e)

def analytics_head():
    p = str(ANALYTICS.get("provider", "none")).strip().lower()
    i = str(ANALYTICS.get("id", "")).strip()
    if not i or p in ("", "none"):
        return ""
    if p == "goatcounter":
        # 自托管 goatcounter.js：gc.zgo.at 在本机/大陆网络实测连接超时；计数端点仍走官方
        return ('<script data-goatcounter="https://' + _html.escape(i, quote=True) +
                '.goatcounter.com/count" async src="goatcounter.js"></script>')
    if p == "umami":
        return ('<script async src="https://cloud.umami.is/script.js" data-website-id="' +
                _html.escape(i, quote=True) + '"></script>')
    if p == "baidu":
        return ('<script>(function(){var hm=document.createElement("script");hm.src="https://hm.baidu.com/hm.js?' +
                _html.escape(i, quote=True) + '";var s=document.getElementsByTagName("script")[0];s.parentNode.insertBefore(hm,s);})();</script>')
    if p == "51la":
        ck = str(ANALYTICS.get("ck") or i).strip()
        if not re.fullmatch(r"[A-Za-z0-9]+", i) or not re.fullmatch(r"[A-Za-z0-9]+", ck):
            return ""
        # 异步加载 + onload 初始化：sdk.51.la 慢/被拦时不阻塞页面、不抛 LA is not defined
        return ('<script>(function(){var s=document.createElement("script");'
                's.id="LA_COLLECT";s.charset="UTF-8";s.async=true;'
                's.src="https://sdk.51.la/js-sdk-pro.min.js";'
                's.onload=function(){try{if(window.LA&&window.LA.init)'
                'window.LA.init({id:"' + i + '",ck:"' + ck + '"})}catch(e){}};'
                'document.head.appendChild(s);})();</script>')
    return ""

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

# 3.3) 目录日期回退表（10-22 P0）：无 📌 callout 的老条目，用目录日期补卡片日期
TOC_DATE_BY_SID = {}
for _text, _bid in toc_items:
    _sid = id_map.get(_bid)
    _m = re.search(r'(20\d{2}-\d{2}(?:-\d{2})?)', _text)
    if _sid and _m:
        TOC_DATE_BY_SID.setdefault(_sid, _m.group(1))

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

# 4.1) 图片 alt（10-22 P0）：Lark 导出的图片无 alt，按图片内容补可读说明；未知图给通用兜底
_IMG_ALT = {
    "media/ff592852be3dd91e6f93.webp": "破万法思维模型配图 1：四象限与十五格示意",
    "media/4cf9ecaef13902f8be4d.webp": "破万法思维模型配图 2：四阶段与十五格示意",
    "media/57b7241e0386910443d4.jpg": "破万法思维模型配图 3：遇人遇事的判断方法示意",
    "media/54fab1e95a6ec900f46f.png": "破万法思维模型配图 4：逆行与核心叮嘱示意",
    "media/28805e6eb4d7d6829123.webp": "破万法思维模型配图 5：信息减法示意",
}
_FEISHU_ALT = {
    "FMz4b0Gt1ocKX5xGymvjJdtHpUf": "破万法思维模型配图 1：四象限与十五格示意",
    "MQWbb1mVToVb3zxLxX0jprQTpcd": "破万法思维模型配图 2：四阶段与十五格示意",
    "ROYpb7RsKoDC8bxVFR8jfMVFpjg": "破万法思维模型配图 3：遇人遇事的判断方法示意",
    "UiImbvHBDo2EiRxIlMujwOKvpJf": "破万法思维模型配图 4：逆行与核心叮嘱示意",
    "ABLhbyfAGohUWkxkKBiju4s6pXF": "破万法思维模型配图 5：信息减法示意",
}
def _add_img_alt(m):
    tag = m.group(0)
    if re.search(r'\balt=', tag, re.I):
        return tag
    sm = re.search(r'\bsrc="([^"]+)"', tag, re.I)
    alt = "归海录文章配图"
    if sm:
        src = sm.group(1)
        alt = _IMG_ALT.get(src, alt)
        fm = re.search(r'https://feishu\.cn/file/([A-Za-z0-9]+)', src)
        if fm:
            alt = _FEISHU_ALT.get(fm.group(1), alt)
    add = f' alt="{_html.escape(alt, quote=True)}"'
    if tag.endswith("/>"):
        return tag[:-2].rstrip() + add + " />"
    return tag[:-1].rstrip() + add + ">"
body_html = re.sub(r'<img\b[^>]*>', _add_img_alt, body_html)

# 4.4) 目录开头包进 layout+aside（闭合在 4.6 处理）
body_html = body_html.replace(
    '<h2 id="目录">📋 目录</h2>',
    '<div class="layout"><aside class="toc"><details class="tocm"><summary>📋 目录</summary>', 1)

# 4.5) 每条目包成折叠卡片：id 移到 details 上，日期徽章 + 2 行摘要（h2/h3 两种锚点都处理）
# 10-22 P0：旧版把整个 📌 callout 塞进 span.date，导致 span 内出现 <p>；现拆成 date / excerpt 两个 phrasing 元素。
def _clean_p_text(phtml):
    t = re.sub(r'<br\s*/?>', '\n', phtml or '', flags=re.I)
    t = re.sub(r'<[^>]+>', '', t)
    return _html.unescape(t)

def _meta_parts(block_html):
    """从 📌 blockquote 取 (date, duration, excerpt)。"""
    inner = re.sub(r'^<blockquote[^>]*>\s*', '', block_html, flags=re.S)
    inner = re.sub(r'\s*</blockquote>$', '', inner, flags=re.S)
    lines = []
    for p in re.findall(r'<p[^>]*>(.*?)</p>', inner, re.S):
        for line in _clean_p_text(p).split('\n'):
            line = re.sub(r'\s+', ' ', line).strip()
            if line and line != '📌':
                lines.append(line)
    text = ' '.join(lines)
    date_m = re.search(r'20\d{2}-\d{2}(?:-\d{2})?', text)
    dur = ''
    pm = re.search(r'[（(]([^）)]+)[）)]', text)
    if pm:
        tm = re.search(r'(?:约\s*)?\d{1,2}:\d{2}(?::\d{2})?|(?:约\s*)?\d+(?:\.\d+)?\s*小时(?:\s*\d+\s*分钟)?|(?:约\s*)?\d+(?:\.\d+)?\s*分钟', pm.group(1))
        dur = tm.group(0) if tm else ''
    # 摘要：截到第一个右括号（通常是时长）；没有括号则尝试去掉「归海录 · 日期 ·」前缀
    desc = text
    close = min([x for x in (text.find('）'), text.find(')')) if x >= 0] or [-1])
    if 0 <= close <= 100:
        desc = text[close + 1:].lstrip(' ·-—')
    else:
        pm2 = re.match(r'^归海录\s*·\s*20\d{2}-\d{2}-\d{2}\s*·\s*', text)
        if pm2:
            desc = text[pm2.end():]
    desc = re.sub(r'版权归属[:：].*$', '', desc).strip()
    desc = re.sub(r'转载请注明来源。?\s*$', '', desc).strip()
    return (date_m.group(0) if date_m else ''), dur, desc

def _first_para_text(html):
    for m in re.finditer(r'<p[^>]*>(.*?)</p>', html, re.S):
        t = re.sub(r'\s+', ' ', _clean_p_text(m.group(1))).strip()
        if t and t != '📌':
            return t
    return ''

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
        date_txt = TOC_DATE_BY_SID.get(sid, '')
        dur_txt = ''
        excerpt = ''
        db = re.search(r'<blockquote[^>]*>\s*<p>📌.*?</blockquote>', chunk, re.S)
        if db:
            date_txt, dur_txt, excerpt = _meta_parts(db.group(0))
            date_txt = date_txt or TOC_DATE_BY_SID.get(sid, '')
            chunk = chunk[:db.start()] + chunk[db.end():]
        if not excerpt:
            excerpt = _first_para_text(chunk)
        badge = date_txt or '未编年'
        if dur_txt:
            badge += ' · ' + dur_txt
        date_html = f'<span class="date">{_html.escape(badge)}</span>'
        ex_html = f'<span class="excerpt">{_html.escape(excerpt)}</span>' if excerpt else ''
        _title_text = _html.unescape(re.sub(r'<[^>]+>', '', title)).strip()
        _fb_url = 'feedback.html?title=' + urllib.parse.quote(_title_text, safe='')
        chunk += f'<p class="entry-feedback"><a href="{_fb_url}">📮 这篇有错字或问题？反馈一下</a></p>'
        out.append(
            f'<details class="entry" id="{sid}">'
            f'<summary><h2>{title}</h2>{date_html}{ex_html}</summary>'
            f'<div class="entry-body">' + chunk + '</div></details>')
    return ''.join(out)

body_html = wrap_entries(body_html)

# 4.55) 站点条目顺序 = 目录时间线（2026-10-18）：按 TOC 顺序重排 <details class="entry">
# 背景：Lark 正文里 Phase 3 回填条目仍在 10-18 之后；目录已按时间归位，站点正文也跟随目录。
def reorder_entries(b, order):
    pat = re.compile(r'<details class="entry" id="(ghl-\d+)">.*?</details>', re.S)
    matches = list(pat.finditer(b))
    if not matches:
        return b
    blocks = {m.group(1): m.group(0) for m in matches}
    prefix, suffix = b[:matches[0].start()], b[matches[-1].end():]
    ordered = [blocks[i] for i in order if i in blocks]
    seen = set(order)
    ordered += [m.group(0) for m in matches if m.group(1) not in seen]
    return prefix + ''.join(ordered) + suffix

_desired_order = [id_map[bid] for _text, bid in toc_items if bid in id_map]
body_html = reorder_entries(body_html, _desired_order)
print(f"OK: 条目顺序按目录重排（{len(_desired_order)} 条）")

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

# 4.9) 分页构建（2026-10-19 施工）：抽取条目 → 按年份分页；首页/年份页/离线版分别组装。
# 旧单页 layout 脚手架在此丢弃；离线版仍用全集单页（不受 500KB 网页传输线约束）。
_ENTRY_RE = re.compile(
    r'((?:<span id="sec-[0-9]+" class="lanchor"></span>)*'
    r'<details class="entry" id="(ghl-\d+)">.*?</details>)', re.S)
_entry_blocks = [(m.group(2), m.group(0)) for m in _ENTRY_RE.finditer(body_html)]
if not _entry_blocks:
    print("WARN 未抽取到条目，分页构建将为空")
print(f"OK: 抽取条目 {len(_entry_blocks)} 条")

def _entry_fields(block):
    tm = re.search(r'<h2>(.*?)</h2>', block, re.S)
    dm = re.search(r'<span class="date">(.*?)</span>', block, re.S)
    title = _html.unescape(re.sub(r'<[^>]+>', '', tm.group(1))).strip() if tm else ''
    meta = _html.unescape(re.sub(r'<[^>]+>', '', dm.group(1))).strip() if dm else ''
    return title, meta

_toc_text_by_sid = {}
for _text, _bid in toc_items:
    _sid = id_map.get(_bid)
    if _sid and _sid not in _toc_text_by_sid:
        _toc_text_by_sid[_sid] = _text

def _entry_year(sid, meta):
    m = re.search(r'(20\d{2})', meta)
    if m:
        return m.group(1)
    _tail = _toc_text_by_sid.get(sid, '').split('｜')[-1].strip()
    m = re.search(r'(20\d{2})', _tail)
    return m.group(1) if m else 'NODATE'

def _entry_date(sid, meta):
    m = re.search(r'20\d{2}-\d{2}(?:-\d{2})?', meta)
    if m:
        return m.group(0)
    _tail = _toc_text_by_sid.get(sid, '').split('｜')[-1].strip()
    m = re.search(r'20\d{2}-\d{2}(?:-\d{2})?|20\d{2}年', _tail)
    return m.group(0) if m else ''

_YEAR_LABEL = {'NODATE': '未编年'}

def _page_for_year(y):
    """年份页文件名：任意 20xx 自动生成；无日期统一 undated.html（10-19 动态化，防未来年份落错页）。"""
    return f"{y}.html" if re.fullmatch(r"20\d{2}", str(y)) else 'undated.html'

_entries = []
for _sid, _block in _entry_blocks:
    _title, _meta = _entry_fields(_block)
    _year = _entry_year(_sid, _meta)
    _entries.append({
        'id': _sid, 'block': _block, 'title': _title, 'meta': _meta,
        'year': _year, 'date': _entry_date(_sid, _meta),
        'page': _page_for_year(_year),
    })
def _series_for_title(t):
    if "独家访谈" in t: return "独家访谈"
    if "因果故事会" in t: return "因果故事会"
    if "100个职业" in t: return "100个职业"
    if "阴阳师漫谈" in t: return "阴阳师漫谈"
    if "奥德赛" in t: return "奥德赛专题"
    if "香包" in t: return "香包专题"
    if "景甜" in t or "孙宇晨" in t: return "景甜/孙宇晨"
    if "婴灵" in t or "堕胎" in t or "试管" in t: return "婴灵/堕胎"
    if "太岁" in t: return "太岁/流年"
    return "单篇/其他"

def _entry_chars(block):
    bm = re.search(r'<div class="entry-body">(.*)$', block, re.S)
    if not bm: return 0
    txt = re.sub(r'<p class="entry-feedback">.*?</p>', '', bm.group(1), flags=re.S)
    txt = _html.unescape(re.sub(r'<[^>]+>', '', txt))
    return len(re.sub(r'\s+', '', txt))

for _e in _entries:
    _e['series'] = _series_for_title(_e['title'])
    _e['chars'] = _entry_chars(_e['block'])
    _e['minutes'] = max(1, round(_e['chars'] / 400))

_id_page = {e['id']: e['page'] for e in _entries}

_pages = {}
for _e in _entries:
    _pages.setdefault(_e['year'], []).append(_e)
print("OK: 分页 " + " / ".join(f"{_YEAR_LABEL.get(y, y)} {len(v)} 条" for y, v in _pages.items()))

# 简介（首页/离线版保留；年份页不重复放）
_m_intro = re.search(r'<div class="intro">.*?</div>', body_html, re.S)
_intro_html = _m_intro.group(0) if _m_intro else ''
if _m_intro:
    body_html = body_html.replace(_m_intro.group(0), '', 1)

def _toc_ul(items):
    return '<ul>' + "".join(
        f'<li><a href="#{e["id"]}">{_html.escape(_toc_text_by_sid.get(e["id"], e["title"]))}</a></li>'
        for e in items) + '</ul>'

def _layout_html(items):
    return ('<div class="layout"><aside class="toc"><details class="tocm">'
            '<summary>📋 目录</summary>' + _toc_ul(items) +
            '</details></aside><main class="content">' +
            "".join(e['block'] for e in items) + '</main></div>')

def _latest_section(n=10):
    lis = []
    for e in _entries[:n]:
        _disp = e['date'] or _YEAR_LABEL.get(e['year'], e['year'] if e['year'] != 'NODATE' else '')
        lis.append(
            '<li class="latest-item"><a href="' + e['page'] + '#' + e['id'] + '">'
            '<span class="latest-date">' + _html.escape(_disp) + '</span>'
            '<span class="latest-title">' + _html.escape(e['title']) + '</span></a></li>')
    return ('<section class="latest" id="latest"><h2>最新更新</h2>'
            '<ul class="latest-list">' + "".join(lis) + '</ul></section>')

def _years_section():
    cards = []
    _ys = sorted((y for y in _pages if y != 'NODATE'), reverse=True)
    if 'NODATE' in _pages:
        _ys.append('NODATE')
    for y in _ys:
        cards.append(
            '<a class="year-card" href="' + _page_for_year(y) + '">'
            '<strong>' + _YEAR_LABEL.get(y, y) + '</strong>'
            '<span>' + str(len(_pages[y])) + ' 篇</span></a>')
    return ('<section class="years" id="years"><h2>按年份浏览</h2>'
            '<div class="year-grid">' + "".join(cards) + '</div>'
            '<p class="years-more"><a href="all.html">查看全部 ' + str(len(_entries)) + ' 篇 →</a></p></section>')

def _guide_section(href_for):
    try:
        _known_ids = set(id_map.values())
        _miss = sorted({r["id"] for g in GUIDE for r in g["reads"]} - _known_ids |
                       {k for k in ALIASES if k not in _known_ids})
        if _miss:
            print("WARN guide/aliases 引用缺失 id:", _miss)
        _min = {e["id"]: e.get("minutes") for e in _entries}
        _cards = []
        for _gi, g in enumerate(GUIDE, 1):
            _reads = [r for r in g["reads"] if r["id"] in _known_ids]
            if not _reads:
                continue
            _chips = "".join(
                f'<button type="button" class="ft-chip" data-q="{_html.escape(c, quote=True)}">{_html.escape(c)}</button>'
                for c in g["chips"])
            def _ritem(r):
                _m = _min.get(r["id"])
                _ms = f'<span class="ft-min">约{_m}分钟阅读</span>' if _m else ""
                return (f'<li><span class="ft-r">{_html.escape(r["role"])}</span>'
                        f'<a href="{href_for(r["id"])}">{_html.escape(r["label"])}</a>{_ms}</li>')
            _ritems = "".join(_ritem(r) for r in _reads)
            _cards.append(
                f'<article class="ftcard"><span class="ft-num">第{_gi}条</span><h3 class="ft-t">{_html.escape(g["title"])}</h3>'
                f'<p class="ft-scene">{_html.escape(g["scene"])}</p>'
                f'<blockquote class="ft-quote"><p>{_html.escape(g["quote"])}</p>'
                f'<cite>— <a href="{href_for(_reads[0]["id"])}">{_html.escape(_reads[0]["label"])}</a></cite></blockquote>'
                f'<div class="ft-chips">{_chips}</div>'
                f'<ul class="ft-reads">{_ritems}</ul>'
                f'<p class="ft-notice">{_html.escape(g["notice"])}</p></article>')
        if not _cards:
            return ""
        _primary = "".join(_cards)
        _more = ""
        print(f"OK: 「第一次来」区 {len(_cards)} 卡")
        return ('<section class="firsttime" id="firsttime"><h2 class="ft-h">第一次来？从这里出发</h2>'
                '<p class="ft-sub">按场景导航 · 推荐与提示为编辑整理，非原典内容 · 顺序为编辑建议，可跳读</p>'
                '<div class="ftcards">' + _primary + '</div>' + _more + '</section>')
    except Exception as e:
        print("WARN 「第一次来」区生成失败:", e)
        return ""

def _online_href(sid):
    return _id_page.get(sid, 'index.html') + '#' + sid

def _offline_href(sid):
    return '#' + sid

_guide_online = _guide_section(_online_href)
_guide_offline = _guide_section(_offline_href)

# 首页/年份页正文
_NEWCOMER_HTML = (
    '<section class="newcomer"><h2>第一次打开归海录？</h2>'
    f'<p><strong>归海录是什么：</strong>志远行空日常分享与视频讲法的文字合集，'
    f'共 {len(_entries)} 篇，按时间倒序更新。</p>'
    '<p><strong>给谁看：</strong>第一次接触的新人，不需要任何前置知识。</p>'
    '<p><strong>从哪开始（三步）：</strong>1. 在下面 11 条问题路线里选一条最像你现状的；'
    '2. 先读每条路线里标“先读”的那篇；'
    '3. 再去“最新更新”看看最近在讲什么。</p>'
    '<p class="newcomer-note">以上为编辑整理的新人指引，非原典内容。</p></section>'
)
# 新人前门（试点 10 篇）：编辑整理层，与正文源 guihailu.md 分离。
# 数据只用试点选材表的篇目信息（标题、目录日期、挑选理由方向）；不编造原文没有的情节、
# 不编播放量与链接；全文链接层一律写“发布时由站内目录对应填入”。
_NEWCOMER_DOOR_HTML = (
    '<p class="newcomer-note">新人入口：<a href="newcomer.html">10 篇试点新人页 →</a>'
    '（看完视频后的下一站，不是视频文字的重播）</p>'
)
_NEWCOMER_PAGES = [
    {
        "title": "普通人能修炼开天眼吗？马斯克的脑机接口、诺贝尔奖离天眼还差多远｜天眼和法眼详解",
        "date": "2026-10-20",
        "anchor": "你刚看的那支视频：志远行空 2026-10-20《普通人能修炼开天眼吗？马斯克的脑机接口、诺贝尔奖离天眼还差多远｜天眼和法眼详解》（视频原长 23:49）。这一页是那支视频的下一站，不是视频文字的重播。",
        "hook": "普通人能修炼开天眼吗？从诺贝尔奖的光控脑细胞、马斯克的脑机接口讲起，讲到天眼的一天和识破假菩萨的法眼，最后结论却不浪漫——先天的神通，靠后天是练不出来的。",
        "taste_q": "一个问题：科学都快摸到玄学了，普通人是不是很快就能人人开天眼？",
        "taste_story": "故事梗概：讲述者先拿科学实验打比方——光点亮老鼠脑细胞、脑机接口靠意念打字，再讲到天眼的一天：街上穿人的鬼、寺庙半空的招聘启事、饭桌上每个人身上冒的光，最后讲到连顶级天眼也看不穿的幻境。",
        "heart": "一句心性落点：把神通看明白了，不依赖它，也不向往它——这才是这一期真正想留下的东西。",
        "points": [
            "科学那边是光点亮脑细胞、脑机接口靠意念打字，讲述者把这和法界的“打念”放在一起比较，但这只是他体系内的比较，不是科学结论。",
            "天眼有“有迹可查”的验证说法（信封里的字、隔空写的字都能看出来），而“有感觉”“眼前有亮光”不算开天眼，市面上的开天眼课程在他看来很可疑。",
            "法眼看的不是更远，而是“规则成像”，并且能识破幻化成菩萨样子的幻境；但先天的天眼、法眼靠后天练不出来，感觉不等于神通，练习得来的敏锐感知也不能当成神通去给人看事。",
        ],
        "related": [
            ("普通人还可以修仙吗？动物、鬼又是怎么修炼的？｜阴阳师聊六道诸界", "2026-10-10"),
            ("你遇到的鬼，最多只是“高启强”——认知层级与法界资源", "2026-09-12"),
        ],
        "self_q": "你有没有把“有感觉”当成过“有能力”？在哪件事上？先写下来，不用急着下结论。",
        "source": "内容整理自志远行空分享，编辑整理部分非原典内容。来源：归海录主文档《普通人能修炼开天眼吗？马斯克的脑机接口、诺贝尔奖离天眼还差多远｜天眼和法眼详解》一节（目录日期 2026-10-20，志远行空 YouTube 视频，原长 23:49）。",
        "tier": "公开层（前门味道层 + 路径层）。本页涉及法界天机类内容，只给味道，不写任何“如何开天眼”的操作步骤，不写符箓、法器使用细节。",
        "boundary": "文中关于天眼、法眼、打念、幻境的说法，属于讲述者个人经验与信仰解释，不是科学结论。本页为故事与修行分享整理，不构成医疗、财务或人生决策建议；编辑整理部分非原典内容。若持续出现幻视、幻听、失眠、焦虑或被害感，请优先寻求精神科、心理或医疗专业帮助。",
        "draft": False,
    },
    {
        "title": "马斯克会飞的车，能让人类更好吗？偷梅艳芳骨灰，真能借运？｜文明的两面 · 九月九登天门 · 三魂七魄",
        "date": "2026-10-18",
        "anchor": "你刚看的那支视频：志远行空 2026-10-18《马斯克会飞的车，能让人类更好吗？偷梅艳芳骨灰，真能借运？｜文明的两面 · 九月九登天门 · 三魂七魄》。这一页是那支视频的下一站，不是视频文字的重播。",
        "hook": "马斯克会飞的车，能让人类更好吗？再追问一句：偷骨灰真能借运吗？两个问题放在一起，问的其实是同一件事——外面的东西变好了，人就变好了吗？",
        "taste_q": "一个问题：东西越新、越快，人是不是就过得越好？",
        "taste_story": "故事梗概（草稿方向）：从马斯克与文明话题这些离新人生活近的现代锚点出发，再落到借运传闻的边界；具体故事细节待编辑对照原文审定后补齐。",
        "heart": "一句心性落点（草稿方向）：先看清自己在求什么，再谈外面的东西好不好。",
        "points": [
            "要点方向：从“飞车”这个现代锚点出发，先把“能让人类更好吗”这个问题讲清楚。",
            "要点方向：借运类传闻只讲问题与边界，不给判断与处置。",
            "要点方向（心性落点）：追问之前，先看自己在求什么——想要“更好”的那份心先安放好。",
        ],
        "related": [
            ("为什么我能跳出人生脚本，你却一再重演？", "2026-09-29"),
            ("三个人一场局：从景甜、孙宇晨、胡锡进看懂人、运、局与轮回", "2026-09-17"),
        ],
        "self_q": "你有没有把“更新的东西”等同于“更好的生活”？在哪件事上？",
        "source": "内容整理自志远行空分享，编辑整理部分非原典内容。来源：归海录主文档该篇（目录日期 2026-10-18）。",
        "tier": "公开层（味道层 + 路径层）。",
        "boundary": "文中关于文明、借运、法界的说法，属于讲述者个人经验与信仰解释，不是科学结论。本页为故事与修行分享整理，不构成医疗、财务或人生决策建议；编辑整理部分非原典内容。",
        "draft": True,
    },
    {
        "title": "缅北“活人祭天”，天收不收？修仙者讲打生桩、发毒誓和借运挪运｜主神意志",
        "date": "2026-10-17",
        "anchor": "你刚看的那支视频：志远行空 2026-10-17《缅北“活人祭天”，天收不收？修仙者讲打生桩、发毒誓和借运挪运｜主神意志》。这一页是那支视频的下一站，不是视频文字的重播。",
        "hook": "缅北“活人祭天”，天收不收？打生桩、发毒誓、借运挪运这些词，新人会主动追问——这一页只讲问题与边界，不讲做法。",
        "taste_q": "一个问题：拿活人去换运，天到底收不收？",
        "taste_story": "故事梗概（草稿方向）：围绕标题里的追问词展开——打生桩、发毒誓、借运挪运先讲清是“问题”，不是方法；具体故事细节待编辑对照原文审定后补齐。",
        "heart": "一句心性落点（草稿方向）：猎奇的问题走到头，还是要回到自己：我到底在怕什么、在求什么。",
        "points": [
            "要点方向：打生桩、发毒誓、借运挪运这些词先讲清是“问题”，不是方法。",
            "要点方向：主神意志类话题只给味道，不给完整操作细节与个人判断处置。",
            "要点方向（心性落点）：从追问回到心性自问——恐惧和欲求才是要先看清的东西。",
        ],
        "related": [
            ("普通人能修炼开天眼吗？马斯克的脑机接口、诺贝尔奖离天眼还差多远｜天眼和法眼详解", "2026-10-20"),
            ("你遇到的鬼，最多只是“高启强”——认知层级与法界资源", "2026-09-12"),
        ],
        "self_q": "听到这类传闻时，你第一反应是害怕、好奇，还是想试试？先诚实写下来。",
        "source": "内容整理自志远行空分享，编辑整理部分非原典内容。来源：归海录主文档该篇（目录日期 2026-10-17）。",
        "tier": "公开层（仅味道层，不给操作细节）。",
        "boundary": "文中关于祭天、打生桩、发毒誓、借运的说法，属于讲述者个人经验与信仰解释，不是科学结论；不写任何操作步骤、法器符箓细节与个人判断处置。本页为故事与修行分享整理，不构成医疗、财务或人生决策建议；编辑整理部分非原典内容。",
        "draft": True,
    },
    {
        "title": "在澳门、东南亚顶级赌场工作有多幸福？接待王储、收高额小费，连「小鬼」都有业绩考核｜3 位赌场从业者亲述潜规则",
        "date": "2026-10-11",
        "anchor": "你刚看的那支视频：志远行空 2026-10-11《在澳门、东南亚顶级赌场工作有多幸福？接待王储、收高额小费，连「小鬼」都有业绩考核｜3 位赌场从业者亲述潜规则》。这一页是那支视频的下一站，不是视频文字的重播。",
        "hook": "在顶级赌场工作有多幸福？三位从业者亲述潜规则——不用玄学背景就能读，读完再想想：看着光鲜的日子，里面到底是什么。",
        "taste_q": "一个问题：看着最光鲜的工作，过得就最幸福吗？",
        "taste_story": "故事梗概（草稿方向）：以三位从业者亲述的现实故事为入口；具体故事细节待编辑对照原文审定后补齐。",
        "heart": "一句心性落点（草稿方向）：从猎奇转向看自己的欲求与选择——羡慕的东西，拿到了又怎样。",
        "points": [
            "要点方向：三位从业者的现实故事是入口，不用玄学背景就能读。",
            "要点方向：“小鬼”也有业绩考核这类细节只当故事听，不展开法界解释。",
            "要点方向（心性落点）：从“看着幸福”转向问自己：我羡慕的到底是什么。",
        ],
        "related": [
            ("聪明人为什么会突然变蠢？一年亏掉 6 个亿，败运来临时，人会亲手走进死局", "2026-09-30"),
            ("三个人一场局：从景甜、孙宇晨、胡锡进看懂人、运、局与轮回", "2026-09-17"),
        ],
        "self_q": "有没有一份你曾经很羡慕的工作或生活？现在再看，你羡慕的是它本身，还是它带来的感觉？",
        "source": "内容整理自志远行空分享，编辑整理部分非原典内容。来源：归海录主文档该篇（目录日期 2026-10-11）。",
        "tier": "公开层（味道层 + 路径层）。",
        "boundary": "文中关于法界、因果的说法，属于讲述者个人经验与信仰解释，不是科学结论。本页为故事与修行分享整理，不构成医疗、财务或人生决策建议；编辑整理部分非原典内容。",
        "draft": True,
    },
    {
        "title": "普通人还可以修仙吗？动物、鬼又是怎么修炼的？｜阴阳师聊六道诸界",
        "date": "2026-10-10",
        "anchor": "你刚看的那支视频：志远行空 2026-10-10《普通人还可以修仙吗？动物、鬼又是怎么修炼的？｜阴阳师聊六道诸界》。这一页是那支视频的下一站，不是视频文字的重播。",
        "hook": "普通人还可以修仙吗？这是新人最常问的入门问题——这一页直接回答它，再往前一步问：动物、鬼又是怎么修炼的。",
        "taste_q": "一个问题：普通人到底能不能修？",
        "taste_story": "故事梗概（草稿方向）：以“普通人能不能修”这个入门问题为入口，再把动物、鬼的修炼放在六道诸界的框架里讲；具体细节待编辑对照原文审定后补齐。",
        "heart": "一句心性落点（草稿方向）：修不修先问自己为什么想修——答案不在方法里，在动机里。",
        "points": [
            "要点方向：普通人到底能不能修，先把问题本身讲清楚。",
            "要点方向：动物、鬼的修炼放在六道诸界的框架里讲，不展开细节。",
            "要点方向（心性落点）：修不修先问自己为什么想修。",
        ],
        "related": [
            ("普通人能修炼开天眼吗？马斯克的脑机接口、诺贝尔奖离天眼还差多远｜天眼和法眼详解", "2026-10-20"),
            ("你遇到的鬼，最多只是“高启强”——认知层级与法界资源", "2026-09-12"),
        ],
        "self_q": "如果普通人真的能修，你最想先修掉自己身上的哪一点？",
        "source": "内容整理自志远行空分享，编辑整理部分非原典内容。来源：归海录主文档该篇（目录日期 2026-10-10）。",
        "tier": "公开层（味道层 + 路径层）。",
        "boundary": "文中关于修仙、六道诸界的说法，属于讲述者个人经验与信仰解释，不是科学结论。本页为故事与修行分享整理，不构成医疗、财务或人生决策建议；编辑整理部分非原典内容。",
        "draft": True,
    },
    {
        "title": "聪明人为什么会突然变蠢？一年亏掉 6 个亿，败运来临时，人会亲手走进死局",
        "date": "2026-09-30",
        "anchor": "你刚看的那支视频：志远行空 2026-09-30《聪明人为什么会突然变蠢？一年亏掉 6 个亿，败运来临时，人会亲手走进死局》。这一页是那支视频的下一站，不是视频文字的重播。",
        "hook": "聪明人为什么会突然变蠢？一年亏掉 6 个亿——败运来临时，人会亲手走进死局。这一页贴近现实焦虑，读完转到心性落点。",
        "taste_q": "一个问题：明明很聪明的人，怎么会亲手把自己送进死局？",
        "taste_story": "故事梗概（草稿方向）：以败运与人生转折为入口；具体故事细节待编辑对照原文审定后补齐。",
        "heart": "一句心性落点（草稿方向）：转折处先看自己的选择——局是走进去的，也就能走出来。",
        "points": [
            "要点方向：败运来临时人会亲手走进死局，先讲故事层面的问题。",
            "要点方向：从“亏掉 6 个亿”看转折，不做个人财运判断。",
            "要点方向（心性落点）：转折处先看自己的选择。",
        ],
        "related": [
            ("为什么我能跳出人生脚本，你却一再重演？", "2026-09-29"),
            ("三个人一场局：从景甜、孙宇晨、胡锡进看懂人、运、局与轮回", "2026-09-17"),
        ],
        "self_q": "回想一次你明知不对还是做了的决定，当时是什么推了你一把？",
        "source": "内容整理自志远行空分享，编辑整理部分非原典内容。来源：归海录主文档该篇（目录日期 2026-09-30）。",
        "tier": "公开层（味道层 + 路径层）。",
        "boundary": "文中关于败运、因果的说法，属于讲述者个人经验与信仰解释，不是科学结论。本页为故事与修行分享整理，不构成医疗、财务或人生决策建议；编辑整理部分非原典内容。",
        "draft": True,
    },
    {
        "title": "为什么我能跳出人生脚本，你却一再重演？",
        "date": "2026-09-29",
        "anchor": "你刚看的那支视频：志远行空 2026-09-29《为什么我能跳出人生脚本，你却一再重演？》。这一页是那支视频的下一站，不是视频文字的重播。",
        "hook": "为什么我能跳出人生脚本，你却一再重演？人生脚本与重复模式是心性类题目——这一页是漏斗里“从好奇转向自己”的路标页。",
        "taste_q": "一个问题：同样的人生，为什么有人跳出来了，有人一再重演？",
        "taste_story": "故事梗概（草稿方向）：以“人生脚本”与“重演”这两个词为入口；具体细节待编辑对照原文审定后补齐。",
        "heart": "一句心性落点（草稿方向）：跳出脚本先从看见模式开始——看不见，就只能重演。",
        "points": [
            "要点方向：什么是“人生脚本”与“重演”，先把问题本身讲清楚。",
            "要点方向：从重演里找自己的模式，不给个人诊断。",
            "要点方向（心性落点）：跳出脚本先从看见模式开始。",
        ],
        "related": [
            ("聪明人为什么会突然变蠢？一年亏掉 6 个亿，败运来临时，人会亲手走进死局", "2026-09-30"),
            ("普通人还可以修仙吗？动物、鬼又是怎么修炼的？｜阴阳师聊六道诸界", "2026-10-10"),
        ],
        "self_q": "你人生里有没有一再重演的一幕？把它写下来，不用急着解释。",
        "source": "内容整理自志远行空分享，编辑整理部分非原典内容。来源：归海录主文档该篇（目录日期 2026-09-29）。",
        "tier": "公开层（味道层 + 路径层）。",
        "boundary": "文中关于人生脚本、轮回的说法，属于讲述者个人经验与信仰解释，不是科学结论。本页为故事与修行分享整理，不构成医疗、财务或人生决策建议；编辑整理部分非原典内容。",
        "draft": True,
    },
    {
        "title": "范冰冰为什么还能翻身：借《地母》说透降头、阴牌与古曼童",
        "date": "2026-09-27",
        "anchor": "你刚看的那支视频：志远行空 2026-09-27《范冰冰为什么还能翻身：借《地母》说透降头、阴牌与古曼童》。这一页是那支视频的下一站，不是视频文字的重播。",
        "hook": "范冰冰为什么还能翻身？借《地母》说透降头、阴牌与古曼童——名人话题带法界内容，好奇心强，这一页只给味道。",
        "taste_q": "一个问题：名人的翻身，和降头、阴牌、古曼童到底有没有关系？",
        "taste_story": "故事梗概（草稿方向）：以名人话题为入口，降头、阴牌、古曼童只讲问题与边界；具体故事细节待编辑对照原文审定后补齐。",
        "heart": "一句心性落点（草稿方向）：猎奇的问题走到头，还是要回到自己：我到底在羡慕什么、在怕什么。",
        "points": [
            "要点方向：名人话题是入口，降头、阴牌、古曼童只讲问题与边界。",
            "要点方向：不给任何操作细节与个人判断处置。",
            "要点方向（心性落点）：从猎奇转向心性自问。",
        ],
        "related": [
            ("三个人一场局：从景甜、孙宇晨、胡锡进看懂人、运、局与轮回", "2026-09-17"),
            ("你遇到的鬼，最多只是“高启强”——认知层级与法界资源", "2026-09-12"),
        ],
        "self_q": "看到名人翻身的故事时，你第一反应是羡慕、怀疑，还是想学？先诚实写下来。",
        "source": "内容整理自志远行空分享，编辑整理部分非原典内容。来源：归海录主文档该篇（目录日期 2026-09-27）。",
        "tier": "公开层（仅味道层，不给操作细节）。",
        "boundary": "文中关于降头、阴牌、古曼童的说法，属于讲述者个人经验与信仰解释，不是科学结论；不写任何操作步骤、法器符箓细节与个人判断处置。本页为故事与修行分享整理，不构成医疗、财务或人生决策建议；编辑整理部分非原典内容。",
        "draft": True,
    },
    {
        "title": "三个人一场局：从景甜、孙宇晨、胡锡进看懂人、运、局与轮回",
        "date": "2026-09-17",
        "anchor": "你刚看的那支视频：志远行空 2026-09-17《三个人一场局：从景甜、孙宇晨、胡锡进看懂人、运、局与轮回》。这一页是那支视频的下一站，不是视频文字的重播。",
        "hook": "三个人一场局：从景甜、孙宇晨、胡锡进看懂人、运、局与轮回——具体人物讲抽象概念，新人不用先补概念就能对上号。",
        "taste_q": "一个问题：什么叫“局”？人、运、局、轮回之间到底是什么关系？",
        "taste_story": "故事梗概（草稿方向）：以三个人一场局为入口；具体人物与事件细节待编辑对照原文审定后补齐。",
        "heart": "一句心性落点（草稿方向）：看局先看自己在局里的位置——位置看清了，局就松动了。",
        "points": [
            "要点方向：从三个人一场局讲清“局”这个词的问题。",
            "要点方向：人、运、局、轮回四个词先分清，不做个人命运判断。",
            "要点方向（心性落点）：看局先看自己在局里的位置。",
        ],
        "related": [
            ("为什么我能跳出人生脚本，你却一再重演？", "2026-09-29"),
            ("聪明人为什么会突然变蠢？一年亏掉 6 个亿，败运来临时，人会亲手走进死局", "2026-09-30"),
        ],
        "self_q": "你现在有没有觉得自己正在某个“局”里？那个局里，你的位置在哪里？",
        "source": "内容整理自志远行空分享，编辑整理部分非原典内容。来源：归海录主文档该篇（目录日期 2026-09-17）。",
        "tier": "公开层（味道层 + 路径层）。",
        "boundary": "文中关于人、运、局、轮回的说法，属于讲述者个人经验与信仰解释，不是科学结论。本页为故事与修行分享整理，不构成医疗、财务或人生决策建议；编辑整理部分非原典内容。",
        "draft": True,
    },
    {
        "title": "你遇到的鬼，最多只是“高启强”——认知层级与法界资源",
        "date": "2026-09-12",
        "anchor": "你刚看的那支视频：志远行空 2026-09-12《你遇到的鬼，最多只是“高启强”——认知层级与法界资源》。这一页是那支视频的下一站，不是视频文字的重播。",
        "hook": "你遇到的鬼，最多只是“高启强”——这个比方把猎奇话题转回认知层级，适合当漏斗的转折页：从“看热闹”转向“看自己的认知”。",
        "taste_q": "一个问题：遇到的东西可不可怕，到底取决于它，还是取决于你的认知在第几层？",
        "taste_story": "故事梗概（草稿方向）：以“高启强”这个比方为认知层级的入口；具体细节待编辑对照原文审定后补齐。",
        "heart": "一句心性落点（草稿方向）：从看热闹转向看自己的认知——层级上去了，东西还是那个东西，看法不一样了。",
        "points": [
            "要点方向：“高启强”这个比方是认知层级的入口。",
            "要点方向：法界资源话题只讲问题与边界。",
            "要点方向（心性落点）：从看热闹转向看自己的认知。",
        ],
        "related": [
            ("普通人能修炼开天眼吗？马斯克的脑机接口、诺贝尔奖离天眼还差多远｜天眼和法眼详解", "2026-10-20"),
            ("普通人还可以修仙吗？动物、鬼又是怎么修炼的？｜阴阳师聊六道诸界", "2026-10-10"),
        ],
        "self_q": "有没有一件事，换个认知层级再看，感觉完全不一样了？是哪件事？",
        "source": "内容整理自志远行空分享，编辑整理部分非原典内容。来源：归海录主文档该篇（目录日期 2026-09-12）。",
        "tier": "公开层（味道层 + 路径层）。",
        "boundary": "文中关于鬼、认知层级、法界资源的说法，属于讲述者个人经验与信仰解释，不是科学结论。本页为故事与修行分享整理，不构成医疗、财务或人生决策建议；编辑整理部分非原典内容。",
        "draft": True,
    },
]


def _newcomer_page_body(p):
    e = _html.escape
    points = "".join(f"<li>{e(x)}</li>" for x in p["points"])
    related = "".join(f"<li>{e(t)}（{e(d)}）</li>" for t, d in p["related"])
    draft_note = ("<p class=\"newcomer-note\">本页为内部草稿，内容待审，试读三问未做。</p>"
                  if p.get("draft") else
                  "<p class=\"newcomer-note\">本页试读三问未做，记账未做。</p>")
    draft_banner = ("<p class=\"newcomer-note\">内部草稿：要点为方向性草稿，细节待编辑对照原文审定后补齐。</p>"
                    if p.get("draft") else "")
    return (
        f'<div class="yearhead"><a class="back" href="newcomer.html">← 新人入口</a>'
        f'<h1>{e(p["title"])}</h1><p>{e(p["date"])} · 新人页 · 约 3 分钟</p></div>'
        '<section class="newcomer">'
        + draft_banner +
        f'<h2>视频锚点</h2><p>{e(p["anchor"])}</p>'
        f'<h2>钩子</h2><p>{e(p["hook"])}</p>'
        '<h2>第 1 层：30 秒味道层</h2>'
        f'<p>{e(p["taste_q"])}</p><p>{e(p["taste_story"])}</p><p>{e(p["heart"])}</p>'
        '<h2>第 2 层：3 分钟路径层</h2><ol>' + points + '</ol>'
        + (f'<p>相关条目：</p><ul>{related}</ul>' if related else '')
        + (f'<p>一个可做的小自问：{e(p["self_q"])}</p>' if p.get("self_q") else '')
        + '<h2>下一步</h2><p>主按钮：读完本页第 2 层（3 分钟路径层）即完成本页。</p>'
        '<p>次选：进群讨论、提问；或点上面相关条目继续。</p>'
        '<h2>时间标尺</h2><p>本页路径层约 3 分钟读完；全文在第三层，不在本页平铺；页内分钟数是按字数估算的阅读时长，不是视频时长。</p>'
        f'<h2>来源标注</h2><p>{e(p["source"])}</p>'
        f'<h2>分层标记</h2><p>{e(p["tier"])}</p>'
        f'<h2>边界说明</h2><p>{e(p["boundary"])}</p>'
        '<h2>全文链接层</h2><p>全文链接：发布时由站内目录对应填入（本页不编造链接地址，不指向需登录的 Lark 原文）。</p>'
        + draft_note +
        '<p>学了一段时间、想直接查全文？去<a href="all.html">全部条目复习</a>。</p>'
        '<p class="newcomer-note">以上为编辑整理的新人页，非原典内容。</p></section>'
    )


def _newcomer_index_body():
    e = _html.escape
    items = "".join(
        f'<li><a href="newcomer-{i + 1:02d}.html">{e(p["date"])} · {e(p["title"])}</a></li>'
        for i, p in enumerate(_NEWCOMER_PAGES))
    return (
        '<div class="yearhead"><a class="back" href="index.html">← 返回首页</a>'
        '<h1>新人入口</h1><p>看完视频后的下一站 · 10 篇试点新人页 · 每页约 3 分钟</p></div>'
        '<section class="newcomer">'
        '<p><strong>给谁看：</strong>刚看完志远行空视频、觉得有意思的新人，不需要任何前置知识。</p>'
        '<p><strong>怎么读：</strong>每页先给味道（30 秒），再给路径（3 分钟），全文在第三层，不在本页平铺。</p>'
        '<ol>' + items + '</ol>'
        '<p>学了一段时间、想直接查全文？去<a href="all.html">全部条目复习</a>。</p>'
        '<p class="newcomer-note">以上为编辑整理的新人指引，非原典内容。试点页为内部草稿，内容待审。</p></section>'
    )

_home_search = ('<div class="searchbar" id="searchbar" role="search"><div class="searchwrap">'
                '<input id="q" type="search" placeholder="搜索全文… 试试：怎么看人 / 烧纸 / 改命" autocomplete="off" '
                'aria-label="搜索全文" role="combobox" aria-autocomplete="list" aria-controls="qres" aria-expanded="false">'
                '<div id="qres" aria-live="polite" aria-label="搜索结果"></div>'
                '<p class="search-hint">试试搜：怎么看人 · 烧纸 · 改命 · 因果</p></div></div>')

_home_body = (
    '<section class="home-welcome">'
    '<p class="home-copy">从一个故事开始，随时阅读公开分享的原文与整理。</p>'
    '<div class="home-actions">'
    '<a class="home-action home-action-primary" href="#recent-topics">看看最近在讲什么</a>'
    '<a class="home-action" href="#searchbar">查找完整原文</a>'
    '</div>'
    '</section>'
    '<section class="recent-topics" id="recent-topics">'
    '<h2>最近在讲</h2>'
    '<div class="recent-placeholder">最新视频切片正在整理，完成后会在这里出现。</div>'
    '</section>'
    '<nav class="home-paths" aria-label="继续浏览">'
    '<a href="#latest"><strong>继续看这样的故事</strong><span>从最新整理开始</span></a>'
    '<a href="all.html"><strong>想知道老师还讲些什么</strong><span>浏览完整分享</span></a>'
    '<a href="#searchbar"><strong>我有一个问题，查查老师以前有没有讲过</strong><span>搜索完整原文</span></a>'
    '</nav>'
    '<section class="home-archive" id="archive">'
    '<h2>完整资料库</h2>'
    '<p>适合查找、复习和阅读完整上下文。</p>'
    + _home_search + _latest_section(10) +
    '<div class="home-archive-links">'
    '<a href="#searchbar">全文搜索</a><a href="#years">按年份浏览</a><a href="all.html">全部条目</a>'
    '</div>'
    '</section>'
    + _years_section()
)
_year_bodies = {}
_yearch_head = {}
for _y, _items in _pages.items():
    _label = _YEAR_LABEL.get(_y, _y)
    _yearch_head[_y] = ('<div class="yearhead"><a class="back" href="index.html">← 返回首页</a>'
                        f'<h1>{_label}</h1><p>共 {len(_items)} 篇 · 按时间倒序</p></div>')
    _year_bodies[_y] = _yearch_head[_y] + _layout_html(_items)
_offline_body = _intro_html + _guide_offline + _layout_html(_entries)

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
.skip{position:absolute;left:-9999px;top:auto;width:1px;height:1px;overflow:hidden}
.skip:focus{left:12px;top:12px;width:auto;height:auto;padding:9px 15px;background:var(--deep);color:var(--gold2);border:1px solid var(--gold);border-radius:8px;z-index:9999;font-size:14px;text-decoration:none}
button,a,summary{-webkit-tap-highlight-color:transparent}
button:focus-visible,a:focus-visible,summary:focus-visible{outline:2px solid var(--gold);outline-offset:4px}
#progress{position:fixed;top:0;left:0;height:2px;width:0;background:var(--gold2);z-index:101}
.hero{background:var(--deep);color:var(--paper);text-align:center}
.doctitle{max-width:900px;margin:auto;padding:84px 24px 72px}
.titleline{display:flex;justify-content:center}
.doctitle h1{display:flex;align-items:center;justify-content:center;gap:22px;margin:0;color:#faf8f1;font-size:64px;font-weight:700;letter-spacing:.13em;line-height:1.2}
.seal{display:inline-flex;flex-direction:column;align-items:center;justify-content:center;width:42px;height:64px;flex:none;border-radius:8px;background:var(--cin);color:#fff6e9;font-family:"KaiTi","STKaiti",serif;font-size:22px;font-weight:400;letter-spacing:0;line-height:1.1}
.doctitle .sub{margin:25px 0 0;color:#c8baa0;font-size:14px;letter-spacing:.24em;line-height:1.8}
.yt{display:inline-flex;align-items:center;justify-content:center;margin-top:34px;padding:9px 23px;border:1px solid var(--gold);border-radius:999px;color:var(--gold2);font-size:13px;font-weight:600;letter-spacing:.09em;text-decoration:none;transition:background .2s,color .2s}
.yt:hover{background:var(--gold2);color:var(--deep)}
.paper{background:var(--paper);min-height:60vh}
.intro{max-width:700px;margin:0 auto;padding:88px 24px 78px;text-align:center;color:var(--muted);font-size:15px;line-height:2.05}
.intro::before{content:"";display:block;width:38px;height:2px;margin:0 auto 25px;background:var(--gold)}
.intro p{margin:0}.intro .intro-title{margin-bottom:16px}.intro strong{display:block;color:var(--ink);font-size:17px;font-weight:600}
.intro .intro-copy+.intro-copy{margin-top:12px}.intro .intro-note{margin-top:18px;font-size:13px;line-height:1.8}.intro .intro-note+.intro-copy{margin-top:16px}
.home-welcome{max-width:700px;margin:0 auto;padding:74px 24px 64px;text-align:center}.home-copy{margin:0;color:var(--muted);font-size:15px;line-height:1.9}.home-actions{display:flex;justify-content:center;flex-wrap:wrap;gap:12px;margin-top:28px}.home-action{display:inline-flex;align-items:center;justify-content:center;padding:11px 20px;border:1px solid var(--gold);border-radius:999px;color:var(--gold);font-size:14px;font-weight:600;text-decoration:none}.home-action:hover,.home-action-primary{background:var(--gold);color:var(--deep)}
.recent-topics,.home-archive{max-width:1024px;margin:0 auto;padding:0 32px 56px}.recent-topics h2,.home-archive h2{margin:0 0 18px;color:var(--ink);font-size:20px;font-weight:700;letter-spacing:.06em;text-align:center}.recent-placeholder{padding:30px 20px;border:1px dashed var(--line);color:var(--muted);font-size:14px;text-align:center}.home-paths{display:grid;grid-template-columns:repeat(3,1fr);max-width:1024px;margin:0 auto;padding:0 32px 62px;gap:14px}.home-paths a{display:flex;flex-direction:column;gap:8px;padding:22px 20px;border:1px solid var(--line);color:var(--ink);text-decoration:none;transition:border-color .2s,transform .2s}.home-paths a:hover{border-color:var(--gold);transform:translateY(-2px)}.home-paths strong{font-size:15px;line-height:1.6}.home-paths span{color:var(--muted);font-size:13px}.home-archive{text-align:center;padding-bottom:28px}.home-archive .searchbar{margin:24px 0 32px;padding:24px 20px;border-radius:12px}.home-archive .search-hint{margin:10px 0 0;color:#c8baa0}.home-archive .latest{text-align:left;padding:0 0 32px}.home-archive p{margin:0;color:var(--muted);font-size:14px}.home-archive-links{display:flex;justify-content:center;flex-wrap:wrap;gap:20px;margin-top:18px}.home-archive-links a{color:var(--gold);font-size:14px;text-decoration:none;border-bottom:1px dotted var(--gold)}
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
.entry>summary{display:grid;grid-template-columns:18px minmax(0,1fr);column-gap:16px;align-items:start;padding:22px 0;list-style:none;cursor:pointer}
.entry>summary::before{content:"+";grid-column:1;grid-row:1;color:var(--gold);font-size:20px;font-weight:300;line-height:1.55}
.entry[open]>summary::before{content:"−"}
.entry>summary h2{grid-column:2;grid-row:1;min-width:0;width:100%;margin:0;color:var(--ink);font-size:21px;font-weight:650;letter-spacing:.015em;line-height:1.65;overflow-wrap:anywhere;transition:color .2s}
.entry>summary:hover h2{color:var(--cin)}
.entry>summary .date{grid-column:2;grid-row:2;justify-self:start;min-width:0;max-width:100%;margin-top:10px;padding:2px 9px;border-radius:999px;background:var(--paper2);color:var(--muted);font-size:12px;font-weight:500;letter-spacing:.02em;line-height:1.65;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.entry>summary .excerpt{grid-column:2;grid-row:3;margin-top:9px;color:var(--muted);font-size:13px;line-height:1.8;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden;max-width:100%}
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
.entry-feedback{margin:34px 0 0;padding-top:16px;border-top:1px dashed var(--line);font-size:13px;color:var(--muted)}
.entry-feedback a{color:var(--gold);text-decoration:none;border-bottom:1px dotted var(--gold)}
.entry-feedback a:hover{color:var(--cin);border-color:var(--cin)}
.feedback-wrap{max-width:720px;margin:0 auto;padding:0 24px 70px}
.feedback-card{border:1px solid var(--line);border-radius:14px;background:var(--paper2);padding:24px 22px}
.feedback-card label{display:block;margin:0 0 6px;color:var(--ink);font-size:14px;font-weight:650}
.feedback-card .fld{margin:0 0 18px}
.feedback-card input,.feedback-card select,.feedback-card textarea{width:100%;box-sizing:border-box;padding:10px 12px;border:1px solid var(--line);border-radius:8px;background:var(--paper);color:var(--ink);font:inherit;font-size:14px}
.feedback-card textarea{min-height:150px;resize:vertical;line-height:1.8}
.feedback-card .hint{margin:6px 0 0;color:var(--muted);font-size:12px;line-height:1.7}
.feedback-actions{display:flex;gap:10px;flex-wrap:wrap;margin-top:6px}
.feedback-actions button{padding:10px 18px;border:1px solid var(--gold);border-radius:999px;background:var(--deep);color:var(--gold2);font:inherit;font-size:14px;font-weight:600;cursor:pointer}
.feedback-actions button.secondary{background:transparent;color:var(--muted);border-color:var(--line)}
.feedback-status{margin:14px 0 0;color:var(--cin);font-size:13px;line-height:1.7;min-height:1.4em}
.qfeedback{padding:10px 14px;border-top:1px solid rgba(178,139,74,.2);font-size:13px}
.qfeedback a{color:var(--gold);text-decoration:none;border-bottom:1px dotted var(--gold)}
@media(max-width:640px){.feedback-wrap{padding:0 20px 54px}.feedback-card{padding:20px 16px}}
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
  .entry>summary h2{font-size:18px;line-height:1.65}.entry>summary .date{font-size:11.5px}.entry>summary .excerpt{font-size:12px;line-height:1.75}
  .entry-body{padding-bottom:37px;font-size:16.5px;line-height:2.05}.entry-body h3{font-size:18px}
  .entry-body blockquote{padding-left:15px;font-size:15.5px}
  footer{padding:48px 20px 56px}.fbtn{display:flex;width:max-content;margin:10px auto}
  .navstack{right:12px;bottom:calc(16px + env(safe-area-inset-bottom));gap:8px;opacity:0;pointer-events:none;transition:opacity .2s}
  .navstack.show{opacity:1;pointer-events:auto}
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
.qitem.active{background:rgba(178,139,74,.12)}
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
.ftmore{margin:16px 0 0}
.ftmore summary{cursor:pointer;list-style:none;text-align:center;color:var(--muted);font-size:12.5px;letter-spacing:.05em;padding:10px 0;border-top:1px dashed var(--line)}
.ftmore summary::-webkit-details-marker{display:none}
.ftmore summary::before{content:"＋ ";color:var(--gold)}
.ftmore[open] summary::before{content:"－ "}
.ftmore .ftcards{margin-top:16px}
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
/* ---- 分页导航（10-19 施工）：首页最新/年份卡 + 年份页头 ---- */
.latest,.years{max-width:1024px;margin:0 auto;padding:0 32px 56px}
.latest h2,.years h2{margin:0 0 18px;color:var(--ink);font-size:20px;font-weight:700;letter-spacing:.06em;text-align:center}
.latest-list{margin:0;padding:0;list-style:none;border-top:1px solid var(--line)}
.latest-item{border-bottom:1px solid var(--line)}
.latest-item a{display:flex;align-items:baseline;gap:18px;padding:14px 4px;color:var(--ink);text-decoration:none}
.latest-date{flex:none;width:92px;color:var(--muted);font-size:12px;letter-spacing:.02em}
.latest-title{min-width:0;font-size:15.5px;font-weight:600;line-height:1.7}
.latest-item a:hover .latest-title{color:var(--cin)}
.year-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:14px}
.year-card{display:flex;flex-direction:column;align-items:center;justify-content:center;gap:6px;padding:20px 12px;border:1px solid var(--line);border-radius:14px;background:var(--paper2);color:var(--ink);text-decoration:none;transition:border-color .2s,color .2s}
.year-card strong{font-size:20px;font-weight:700;letter-spacing:.06em}
.year-card span{color:var(--muted);font-size:12px}
.year-card:hover{border-color:var(--gold);color:var(--cin)}
.years-more{text-align:center;margin:18px 0 0;font-size:13px}
.years-more a{color:var(--gold);text-decoration:none;border-bottom:1px dotted var(--gold)}
/* ---- 全部条目（10-23 P1）：目录/系列筛选 ---- */
.catalog-wrap{max-width:1024px;margin:0 auto;padding:0 32px 70px}
.catalog-controls{display:flex;flex-wrap:wrap;gap:10px;align-items:center;margin:0 0 18px}
#cat-q{flex:1 1 240px;min-width:0;height:40px;padding:0 14px;border:1px solid var(--line);border-radius:999px;background:var(--paper);color:var(--ink);font:inherit;font-size:14px}
#cat-series{height:40px;padding:0 12px;border:1px solid var(--line);border-radius:999px;background:var(--paper);color:var(--ink);font:inherit;font-size:14px}
.cat-years{display:flex;flex-wrap:wrap;gap:6px}
.cat-year-btn{height:36px;padding:0 14px;border:1px solid var(--line);border-radius:999px;background:transparent;color:var(--muted);font:inherit;font-size:13px;cursor:pointer}
.cat-year-btn.on{background:var(--cin);border-color:var(--cin);color:#faf3ea}
.cat-count{color:var(--muted);font-size:13px;margin-left:auto;white-space:nowrap}
.cat-list{border-top:1px solid var(--line)}
.cat-item{display:grid;grid-template-columns:94px minmax(0,1fr) 110px 52px 58px;gap:12px;align-items:center;padding:12px 4px;border-bottom:1px solid var(--line);font-size:14px}
.cat-item[hidden]{display:none}
.cat-date{color:var(--muted);font-size:12.5px;white-space:nowrap}
.cat-title{min-width:0;line-height:1.7}
.cat-title a{color:var(--ink);text-decoration:none;overflow-wrap:anywhere}
.cat-title a:hover{color:var(--cin)}
.cat-series{color:var(--muted);font-size:12px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.cat-time{color:var(--muted);font-size:12px;text-align:right;white-space:nowrap}
.cat-copy{padding:4px 9px;border:1px solid var(--line);border-radius:999px;background:transparent;color:var(--muted);font:inherit;font-size:12px;cursor:pointer}
.cat-copy:hover{border-color:var(--gold);color:var(--ink)}
.cat-empty{padding:30px 10px;text-align:center;color:var(--muted);font-size:14px}
.cat-empty[hidden]{display:none}
@media(max-width:640px){.catalog-wrap{padding:0 20px 54px}.cat-item{grid-template-columns:66px minmax(0,1fr) 44px 56px;gap:8px;font-size:13.5px}.cat-series{display:none}.cat-count{width:100%;margin-left:0}.cat-date{font-size:11.5px}.cat-time{font-size:11.5px}.cat-copy{padding:3px 7px;font-size:11px}}
.hero.compact .doctitle{padding:64px 24px 46px}
.hero.compact h1{font-size:56px}
.yearhead{max-width:720px;margin:0 auto;padding:44px 24px 8px;text-align:center;color:var(--muted)}
.yearhead .back{color:var(--gold);font-size:13px;text-decoration:none}
.yearhead .back:hover{color:var(--cin)}
.yearhead h1{margin:10px 0 4px;color:var(--ink);font-size:34px;font-weight:700;letter-spacing:.08em}
.yearhead p{margin:0;font-size:12.5px;letter-spacing:.05em}
@media(max-width:960px){.latest,.years{padding:0 20px 44px}.year-grid{grid-template-columns:repeat(2,minmax(0,1fr))}}
@media(max-width:960px){.recent-topics,.home-archive{padding-left:20px;padding-right:20px}.home-paths{grid-template-columns:1fr;padding-left:20px;padding-right:20px}}
@media(max-width:640px){.latest-item a{gap:10px;padding:12px 2px;align-items:flex-start}.latest-date{width:72px;font-size:11.5px}.latest-title{font-size:14.5px}.hero.compact .doctitle{padding:42px 22px 30px}.hero.compact h1{font-size:40px}.yearhead{padding:30px 20px 6px}.yearhead h1{font-size:28px}}
@media(max-width:640px){.home-welcome{padding:44px 20px 42px}.home-actions{flex-direction:column}.home-action{width:100%;box-sizing:border-box}.recent-topics,.home-archive{padding-bottom:42px}}
.newcomer{max-width:760px;margin:0 auto;padding:0 32px 40px;color:var(--ink);font-size:15.5px;line-height:1.9}
.newcomer h2{margin:0 0 14px;color:var(--ink);font-size:20px;font-weight:700;letter-spacing:.06em;text-align:center}
.newcomer p{margin:0 0 8px}.newcomer-note{color:var(--muted);font-size:13px}
.ft-num{display:inline-block;margin-bottom:8px;padding:2px 10px;border:1px solid var(--gold);border-radius:999px;color:var(--gold);font-size:12px;font-weight:600;letter-spacing:.05em}
.ft-min{margin-left:8px;color:var(--muted);font-size:12px;white-space:nowrap}
.ftcard:hover{border-color:var(--gold)}
.search-hint{margin:10px 0 0;color:#c8baa0;font-size:12.5px;letter-spacing:.04em;text-align:center}
.cat-note{margin:0 0 10px;color:var(--muted);font-size:12.5px;text-align:right}
@media(max-width:640px){.newcomer{padding:0 20px 32px;font-size:14.5px}}
"""

js = """
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
  var gg='';
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
"""

# 6) 全文检索索引（先于页面组装：离线版要内嵌）——条目带 page 字段供跨页跳转
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

_shards_json = "[]"
try:
    _items = []
    for _e in _entries:
        sid = _e['id']; blk = _e['block']
        bm = re.search(r'<div class="entry-body">(.*)$', blk, re.S)
        _title = _plain(_e['title'])
        # 10-14：date=首个合法 YYYY-MM-DD（不定则空，不伪造）；10-19 起徽章缺失时用目录日期补
        _meta = _plain(_e['meta']).replace('📌', '').strip()
        _dmm = (re.search(r'20\d{2}-\d{2}(?:-\d{2})?', _meta)
                or re.search(r'20\d{2}-\d{2}(?:-\d{2})?', _e['date']))
        _date = _dmm.group(0) if _dmm else ''
        # 反馈链接含长 percent-encoded 标题，不进检索正文（省体积、去噪）
        _bm_html = re.sub(r'<p class="entry-feedback">.*?</p>', '', bm.group(1) if bm else '', flags=re.S)
        _text = _plain(_bm_html)
        if sid and _title:
            _it = {"id": sid, "title": _title, "date": _date, "meta": _meta,
                   "text": _text, "page": _e['page'], "year": _e['year']}
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
    # 顶层新增 guide / t2s（10-17 施工窗 2）；指纹覆盖全部内容（含 page/year），保幂等
    _payload = {"guide": GUIDE, "t2s": _t2s_pairs, "entries": _items}
    _fp = hashlib.sha256(json.dumps(_payload, ensure_ascii=False, sort_keys=True,
                                    separators=(',', ':')).encode('utf-8')).hexdigest()[:12]
    # 离线版内嵌完整索引（file:// 可搜索）；在线版按年分片（10-21 C 方案）
    _idx_json = json.dumps({"generated": _fp, "count": len(_items), "guide": GUIDE,
                            "t2s": _t2s_pairs, "entries": _items},
                           ensure_ascii=False, separators=(',', ':'))
    _shared_fp = hashlib.sha256(json.dumps({"guide": GUIDE, "t2s": _t2s_pairs},
                                           ensure_ascii=False, sort_keys=True,
                                           separators=(',', ':')).encode('utf-8')).hexdigest()[:12]
    _shared_obj = {"generated": _shared_fp, "guide": GUIDE, "t2s": _t2s_pairs}
    _shared_txt = json.dumps(_shared_obj, ensure_ascii=False, separators=(',', ':'))
    (HERE / "search_shared.json").write_text(_shared_txt + "\n", encoding="utf-8", newline="\n")
    _by_page = {}
    for _it in _items:
        _by_page.setdefault(_it.get("page") or "undated.html", []).append(_it)
    _shard_names, _manifest_shards = [], []
    _page_order = sorted(_by_page, key=lambda p: (p == "undated.html",
                                                  -int(p[:-5]) if p[:-5].isdigit() else 0))
    for _pg in _page_order:
        _slug = _pg[:-5] if _pg.endswith(".html") else _pg
        _fn = f"search_index_{_slug}.json"
        _shard_items = _by_page[_pg]
        _shard_fp = hashlib.sha256(json.dumps(_shard_items, ensure_ascii=False, sort_keys=True,
                                              separators=(',', ':')).encode('utf-8')).hexdigest()[:12]
        _shard_obj = {"generated": _shard_fp, "count": len(_shard_items), "entries": _shard_items}
        _shard_txt = json.dumps(_shard_obj, ensure_ascii=False, separators=(',', ':'))
        (HERE / _fn).write_text(_shard_txt + "\n", encoding="utf-8", newline="\n")
        _shard_names.append(_fn)
        _manifest_shards.append({"file": _fn, "page": _pg, "count": len(_shard_items),
                                 "bytes": len(_shard_txt.encode("utf-8"))})
        print(f"OK: {_fn} {len(_shard_items)} entries, {len(_shard_txt.encode('utf-8'))} B")
    _shards_json = json.dumps(_shard_names, ensure_ascii=False, separators=(',', ':'))
    _manifest = {"generated": _fp, "count": len(_items), "shared": "search_shared.json",
                 "shards": _manifest_shards}
    (HERE / "search_manifest.json").write_text(
        json.dumps(_manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    _old_idx = HERE / "search_index.json"
    if _old_idx.exists():
        _old_idx.unlink()
    print(f"OK: search shards {len(_shard_names)} files, total {len(_items)} entries, fingerprint {_fp}")
except Exception as e:
    _note("WARN search shards 生成失败: %r" % (e,))
    print("WARN: search shards 生成失败:", e)
    _idx_json = json.dumps({"generated": "", "count": 0, "guide": GUIDE,
                            "t2s": _t2s_pairs, "entries": []}, ensure_ascii=False,
                           separators=(",", ":"))

# 5) 多页组装：首页 / 年份页 / 离线版（2026-10-19 分页施工）
_idpage_json = json.dumps(_id_page, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")

def _render_page(page_name, page_title, page_desc, body, *, compact=False, inline=False, ld_items=None, noindex=False):
    hero_cls = "hero compact" if compact else "hero"
    if inline:
        css_tag = "<style>\n" + css + "</style>"
        js_tag = ('<script>window.__GHL_INDEX__=' + _idx_json.replace('</', '<\\/') + ';</script>\n'
                  '<script>' + js + '</script>')
        dl_tag = '<span class="fbtn">📥 本页即离线版</span>'
        globals_tag = ''
    else:
        css_tag = '<link rel="stylesheet" href="style.v5.css">'
        js_tag = '<script src="main.v5.js" defer></script>'
        dl_tag = '<a class="fbtn" href="归海录_离线版.html" download>📥 离线版下载</a>'
        globals_tag = ('<script>window.__GHL_PAGE__=' + json.dumps(page_name, ensure_ascii=False) +
                       ';window.__GHL_IDPAGE__=' + _idpage_json +
                       ';window.__GHL_SHARDS__=' + _shards_json + ';</script>')
    _t = _html.escape(page_title, quote=True)
    _d = _html.escape(page_desc, quote=True)
    _base = "https://guihailu.github.io/"
    if page_name == "index.html":
        _canonical = _base
    elif page_name in ("404.html", "归海录_离线版.html"):
        _canonical = ""
    else:
        _canonical = _base + page_name
    _ld = None
    if page_name == "index.html":
        _ld = {"@context": "https://schema.org", "@type": "WebSite",
               "name": "归海录 · 志远行空", "url": _base,
               "description": page_desc, "inLanguage": "zh-CN"}
    elif ld_items:
        _ld = {"@context": "https://schema.org", "@type": "CollectionPage",
               "name": page_title, "url": _canonical, "description": page_desc,
               "inLanguage": "zh-CN",
               "isPartOf": {"@type": "WebSite", "name": "归海录 · 志远行空", "url": _base},
               "mainEntity": {"@type": "ItemList", "numberOfItems": len(ld_items),
                              "itemListElement": [
                                  {"@type": "ListItem", "position": _i + 1,
                                   "name": _plain(_e["title"]),
                                   "url": f"{_base}{_e['page']}#{_e['id']}"}
                                  for _i, _e in enumerate(ld_items)]}}
    _ld_tag = ('<script type="application/ld+json">' +
               json.dumps(_ld, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/") +
               '</script>') if _ld else ''
    _canon_tag = f'<link rel="canonical" href="{_canonical}">' if _canonical else ''
    _ogurl_tag = f'<meta property="og:url" content="{_canonical}">' if _canonical else ''
    _robots_tag = '<meta name="robots" content="noindex,follow">' if noindex else ''
    _hero_sub = '志远行空公开分享整理' if page_name == 'index.html' else '归海2026 · 志远行空'
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{_t}</title>
<meta name="description" content="{_d}">
<meta name="author" content="志远行空">
<meta name="theme-color" content="#0f1a2b">
{_canon_tag}
{_ogurl_tag}
{_robots_tag}
<meta property="og:title" content="{_t}">
<meta property="og:description" content="{_d}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="归海录 · 志远行空">
<meta property="og:locale" content="zh_CN">
<meta property="og:image" content="https://guihailu.github.io/cover.jpg">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="450">
<meta property="og:image:alt" content="归海录 · 志远行空">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{_t}">
<meta name="twitter:description" content="{_d}">
<meta name="twitter:image" content="https://guihailu.github.io/cover.jpg">
<link rel="icon" href="favicon.svg" type="image/svg+xml">
<link rel="icon" href="favicon.ico" sizes="32x32">
<link rel="manifest" href="manifest.json">
<link rel="alternate" type="application/atom+xml" title="归海录" href="feed.xml">
{_ld_tag}
{analytics_head()}
<script>try{{if(localStorage.getItem('ghl_theme')==='dark')document.documentElement.classList.add('dark')}}catch(e){{}}</script>
<script>window.__GHL_LEGACY__={legacy_json};</script>
{globals_tag}
{css_tag}
</head>
<body id="top">
<a class="skip" href="#main-content">跳到正文</a>
<div id="progress"></div>
<header class="{hero_cls}">
  <div class="doctitle">
    <div class="titleline"><h1>归海录<span class="seal" aria-hidden="true">归<br>海</span></h1></div>
    <p class="sub">{_hero_sub}</p>
{'' if page_name == 'index.html' else '    <a class="yt" href="https://www.youtube.com/@zyxk999" target="_blank" rel="noopener">▶ YouTube</a>'}
  </div>
</header>
{'' if page_name == 'index.html' else '<div class="searchbar" role="search"><div class="searchwrap"><input id="q" type="search" placeholder="搜索全文… 试试：怎么看人 / 烧纸 / 改命" autocomplete="off" aria-label="搜索全文" role="combobox" aria-autocomplete="list" aria-controls="qres" aria-expanded="false"><div id="qres" aria-live="polite" aria-label="搜索结果"></div><p class="search-hint">试试搜：怎么看人 · 烧纸 · 改命 · 因果</p></div></div>'}
<div class="paper" id="main-content">
{body}
</div>
<footer>
  <div class="flinks">
    <a class="fbtn" href="https://www.youtube.com/@zyxk999" target="_blank" rel="noopener">▶ 志远行空 YouTube 频道</a>
    <a class="fbtn" href="https://u78zyhf3gaz.jp.larksuite.com/docx/QKYtdsvHzoH1aIxuGhrjD81EpWf" target="_blank" rel="noopener">📿 归海录 · Lark 源文档</a>
    <a class="fbtn" href="https://www.oceanwards.com/" target="_blank" rel="noopener">🌊 归海论坛</a>
    <a class="fbtn" href="all.html">📚 全部条目</a>
    <a class="fbtn" href="feedback.html">✉️ 反馈 / 报错</a>
    {dl_tag}
  </div>
  <div class="fmeta">归海录 · 持续更新中{_footer_date}</div>
</footer>
<div class="navstack">
  <button class="navbtn" id="toReading" aria-label="回到本篇开头">↩ 本篇开头</button>
  <button class="navbtn" id="toTop" aria-label="回到文档顶部">↑ 顶部</button>
</div>
<button id="toggle" aria-label="切换深浅色">🌙</button>
{js_tag}
</body>
</html>"""

(HERE / "style.v5.css").write_text(css, encoding="utf-8", newline="\n")
(HERE / "main.v5.js").write_text(js, encoding="utf-8", newline="\n")

# 7.5) 全部条目页（10-23 P1）：目录 + 年份/系列/标题筛选 + 阅读时长 + 复制链接
_catalog_items = sorted(_entries, key=lambda e: (e.get('date') or '0000-00-00'), reverse=True)
_series_counts = {}
for _e in _catalog_items:
    _series_counts[_e['series']] = _series_counts.get(_e['series'], 0) + 1
_series_opts = "".join(
    f'<option value="{_html.escape(k, quote=True)}">{_html.escape(k)}（{v}）</option>'
    for k, v in sorted(_series_counts.items(), key=lambda kv: (-kv[1], kv[0])))
_year_btns = '<button type="button" class="cat-year-btn on" data-year="">全部</button>'
for _y in sorted((y for y in _pages if y != 'NODATE'), reverse=True):
    _year_btns += f'<button type="button" class="cat-year-btn" data-year="{_y}">{_y}</button>'
if 'NODATE' in _pages:
    _year_btns += '<button type="button" class="cat-year-btn" data-year="NODATE">未编年</button>'
_cat_rows = []
for _e in _catalog_items:
    _date = _e['date'] or '未编年'
    _href = _e['page'] + '#' + _e['id']
    _link = 'https://guihailu.github.io/' + _href
    _search = _html.escape((_e['title'] + ' ' + _e['series'] + ' ' + _date).lower(), quote=True)
    _cat_rows.append(
        '<div class="cat-item" data-year="' + _e['year'] + '" data-series="' + _html.escape(_e['series'], quote=True) +
        '" data-search="' + _search + '">'
        '<span class="cat-date">' + _html.escape(_date) + '</span>'
        '<span class="cat-title"><a href="' + _href + '">' + _html.escape(_e['title']) + '</a></span>'
        '<span class="cat-series">' + _html.escape(_e['series']) + '</span>'
        '<span class="cat-time">' + str(_e['minutes']) + '′</span>'
        '<button type="button" class="cat-copy" data-link="' + _html.escape(_link, quote=True) + '">复制</button></div>')
_catalog_tpl = '''<div class="yearhead"><a class="back" href="index.html">← 返回首页</a>
<h1>全部条目</h1><p>共 __TOTAL__ 篇 · 按标题 / 系列 / 年份筛选</p></div>
<div class="catalog-wrap">
<div class="catalog-controls">
<input id="cat-q" type="search" placeholder="筛选标题或系列… 试试：天眼 / 因果" autocomplete="off" aria-label="筛选条目">
<select id="cat-series" aria-label="按系列筛选"><option value="">全部系列</option>__SERIES__</select>
<div class="cat-years" role="group" aria-label="按年份筛选">__YEARS__</div>
<span class="cat-count" id="cat-count">__TOTAL__ 篇</span>
</div>
<p class="cat-note">时长为按字数估算的阅读时长（约 400 字 / 分钟），不是视频时长。</p>
<div class="cat-list" id="cat-list">__ROWS__</div>
<div class="cat-empty" id="cat-empty" hidden>没有匹配的条目，换个关键词试试。</div>
</div>
<script>
(function(){
 var q=document.getElementById('cat-q'), sel=document.getElementById('cat-series');
 var items=[].slice.call(document.querySelectorAll('.cat-item'));
 var count=document.getElementById('cat-count'), empty=document.getElementById('cat-empty');
 var curYear='';
 function apply(){
  var term=(q.value||'').trim().toLowerCase(), sy=sel.value, n=0;
  items.forEach(function(el){
   var ok=(!curYear||el.getAttribute('data-year')===curYear)&&(!sy||el.getAttribute('data-series')===sy)&&(!term||el.getAttribute('data-search').indexOf(term)>-1);
   el.hidden=!ok; if(ok)n++;
  });
  count.textContent=n+' 篇'; empty.hidden=n>0;
 }
 q.addEventListener('input',apply); sel.addEventListener('change',apply);
 [].slice.call(document.querySelectorAll('.cat-year-btn')).forEach(function(b){
  b.addEventListener('click',function(){
   curYear=b.getAttribute('data-year');
   [].slice.call(document.querySelectorAll('.cat-year-btn')).forEach(function(x){x.classList.toggle('on',x===b);});
   apply();
  });
 });
 var sp=new URLSearchParams(location.search), qq=sp.get('q'), ss=sp.get('series'), yy=sp.get('year');
 if(qq)q.value=qq; if(ss)sel.value=ss;
 if(yy){curYear=yy;[].slice.call(document.querySelectorAll('.cat-year-btn')).forEach(function(x){x.classList.toggle('on',x.getAttribute('data-year')===yy);});}
 apply();
 [].slice.call(document.querySelectorAll('.cat-copy')).forEach(function(b){
  b.addEventListener('click',function(){
   var link=b.getAttribute('data-link');
   function done(){b.textContent='已复制';setTimeout(function(){b.textContent='复制';},1200);}
   function fallback(){var t=document.createElement('textarea');t.value=link;document.body.appendChild(t);t.select();try{document.execCommand('copy');done();}catch(e){}t.remove();}
   if(navigator.clipboard&&navigator.clipboard.writeText){navigator.clipboard.writeText(link).then(done,fallback);}else{fallback();}
  });
 });
})();
</script>'''
_catalog_body = (_catalog_tpl.replace('__TOTAL__', str(len(_entries)))
                 .replace('__SERIES__', _series_opts)
                 .replace('__YEARS__', _year_btns)
                 .replace('__ROWS__', "".join(_cat_rows)))

_HOME_DESC = ("归海录：志远行空的日常分享与 YouTube 视频讲法合集——每一段语音，一个故事，"
              "一个道理，润物无声。按时间倒序，持续更新。")
_HOME_TITLE = "📿 归海录 · 志远行空"
(HERE / "index.html").write_text(
    _render_page("index.html", _HOME_TITLE, _HOME_DESC, _home_body), encoding="utf-8", newline="\n")
print(f"OK: index.html {(HERE/'index.html').stat().st_size} B")

(HERE / "all.html").write_text(
    _render_page("all.html", "📚 全部条目 · 归海录", f"归海录全部 {len(_entries)} 篇：按标题、系列、年份筛选，含阅读时长与复制链接。",
                 _catalog_body, compact=True, ld_items=_catalog_items),
    encoding="utf-8", newline="\n")
print(f"OK: all.html {(HERE/'all.html').stat().st_size} B ({len(_entries)} 条)")

# 新人前门：由构建生成新人入口页与 10 篇试点新人页（不手写生成页）。
(HERE / "newcomer.html").write_text(
    _render_page("newcomer.html", "新人入口 · 归海录", "看完志远行空视频后的下一站：10 篇试点新人页，每页约 3 分钟。",
                 _newcomer_index_body()),
    encoding="utf-8", newline="\n")
print(f"OK: newcomer.html {(HERE/'newcomer.html').stat().st_size} B")
for _i, _p in enumerate(_NEWCOMER_PAGES):
    _fn = f"newcomer-{_i + 1:02d}.html"
    (HERE / _fn).write_text(
        _render_page(_fn, f"{_p['title']} · 新人页 · 归海录", f"新人页：{_p['title']}（{_p['date']}），约 3 分钟。",
                     _newcomer_page_body(_p)),
        encoding="utf-8", newline="\n")
    print(f"OK: {_fn} {(HERE/_fn).stat().st_size} B")

for _y, _items in _pages.items():
    _label = _YEAR_LABEL.get(_y, _y)
    _fn = _page_for_year(_y)
    _title = f"📿 归海录 · {_label} · 志远行空"
    _desc = f"归海录 · {_label}：志远行空的日常分享与 YouTube 视频讲法合集，共 {len(_items)} 篇。"
    (HERE / _fn).write_text(
        _render_page(_fn, _title, _desc, _year_bodies[_y], compact=True, ld_items=_items),
        encoding="utf-8", newline="\n")
    print(f"OK: {_fn} {(HERE/_fn).stat().st_size} B ({len(_items)} 条)")

# 离线单文件版：全集单页 + 内联 CSS/JS/索引（file:// 可搜索）
try:
    _off = _render_page("归海录_离线版.html", _HOME_TITLE, _HOME_DESC, _offline_body, inline=True, noindex=True)
    # 离线版图片走在线链接：feishu 原链 → 站点已镜像的公开图（未命中则保留原链回落）
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
print(f"OK: style.v5.css {(HERE/'style.v5.css').stat().st_size} B | main.v5.js {(HERE/'main.v5.js').stat().st_size} B")

# 7) SEO / 分享辅助文件（10-22 P0）：favicon / manifest / robots / sitemap / 404 / Atom feed
_FAVICON_SVG = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
<rect width="64" height="64" rx="12" fill="#8c1f28"/>
<text x="32" y="44" text-anchor="middle" font-family="serif" font-size="36" fill="#fff6e9">归</text>
</svg>
'''
(HERE / "favicon.svg").write_text(_FAVICON_SVG, encoding="utf-8", newline="\n")
_MANIFEST = {
    "name": "归海录 · 志远行空",
    "short_name": "归海录",
    "description": _HOME_DESC,
    "start_url": "./",
    "display": "standalone",
    "background_color": "#0f1a2b",
    "theme_color": "#0f1a2b",
    "lang": "zh-CN",
    "icons": [{"src": "favicon.svg", "sizes": "any", "type": "image/svg+xml", "purpose": "any"}],
}
(HERE / "manifest.json").write_text(
    json.dumps(_MANIFEST, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
(HERE / "robots.txt").write_text(
    "User-agent: *\nAllow: /\n\nSitemap: https://guihailu.github.io/sitemap.xml\n",
    encoding="utf-8", newline="\n")

def _page_lastmod(items):
    ds = [e["date"] for e in items if re.fullmatch(r"20\d{2}-\d{2}-\d{2}", e.get("date") or "")]
    return max(ds) if ds else _latest_date

_sitemap_urls = [("https://guihailu.github.io/", _latest_date, "weekly", "1.0"),
                 ("https://guihailu.github.io/all.html", _latest_date, "weekly", "0.9")]
for _y in sorted(_pages, key=lambda y: (y == "NODATE", -int(y) if re.fullmatch(r"20\d{2}", str(y)) else 0)):
    _fn = _page_for_year(_y)
    _sitemap_urls.append((("https://guihailu.github.io/" + _fn), _page_lastmod(_pages[_y]), "monthly", "0.8"))
_sitemap = ['<?xml version="1.0" encoding="UTF-8"?>',
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
for _loc, _lm, _cf, _pr in _sitemap_urls:
    _lm_tag = f"<lastmod>{_html.escape(_lm)}</lastmod>" if _lm else ""
    _sitemap.append(f"<url><loc>{_html.escape(_loc)}</loc>{_lm_tag}<changefreq>{_cf}</changefreq><priority>{_pr}</priority></url>")
_sitemap.append("</urlset>")
(HERE / "sitemap.xml").write_text("\n".join(_sitemap) + "\n", encoding="utf-8", newline="\n")

_404_body = ('<div class="yearhead"><a class="back" href="index.html">← 返回首页</a>'
             '<h1>404</h1><p>这个页面不存在，或链接已失效。</p></div>'
             '<div class="intro"><p class="intro-copy">可以试试：<a href="index.html">首页</a>'
             ' · <a href="index.html#firsttime">从问题入口出发</a> · 用上方搜索找一篇。</p></div>')
(HERE / "404.html").write_text(
    _render_page("404.html", "页面不存在 · 归海录", "这个页面不存在，或链接已失效。",
                 _404_body, compact=True, noindex=True),
    encoding="utf-8", newline="\n")

# 反馈页（A 方案：无后端、无第三方；复制模板后发微信/Lark）
_FEEDBACK_BODY = '''<div class="yearhead"><a class="back" href="index.html">← 返回首页</a>
<h1>反馈 / 报错</h1><p>错字、链接失效、搜索找不到，或对站点有建议 · 复制后发微信/Lark 即可</p></div>
<div class="feedback-wrap"><div class="feedback-card">
<div class="fld"><label for="fb-type">类型</label><select id="fb-type">
<option>内容纠错</option><option>搜索无结果</option><option>功能建议</option><option>其他</option>
</select></div>
<div class="fld"><label for="fb-title">文章标题 / 搜索词</label><input id="fb-title" type="text" placeholder="例：脑海像滴了清凉油 / 搜索：怎么改命"></div>
<div class="fld"><label for="fb-page">页面链接（可选）</label><input id="fb-page" type="text" placeholder="从浏览器地址栏复制"></div>
<div class="fld"><label for="fb-detail">详情</label><textarea id="fb-detail" placeholder="错字请写原文和正确写法；搜索问题请写你想找的内容。"></textarea>
<p class="hint">不会自动提交；点“复制反馈内容”后，粘贴到微信/Lark 发给志远行空或归海群。</p></div>
<div class="fld"><label for="fb-contact">联系方式（可选）</label><input id="fb-contact" type="text" placeholder="Lark / 微信，方便回复"></div>
<div class="feedback-actions"><button type="button" id="fb-copy">复制反馈内容</button><button type="button" id="fb-clear" class="secondary">清空</button></div>
<p class="feedback-status" id="fb-status"></p>
</div></div>
<script>
(function(){
 var p=new URLSearchParams(location.search);
 var type=p.get('type')||'', q=p.get('q')||'', t=p.get('title')||'';
 if(type==='search'||q){document.getElementById('fb-type').value='搜索无结果';}
 if(q){document.getElementById('fb-title').value='搜索：'+q;}
 else if(t){document.getElementById('fb-title').value=t;}
 var page=p.get('page')||'';if(page){document.getElementById('fb-page').value=page;}
 var st=document.getElementById('fb-status');
 function v(id){return (document.getElementById(id).value||'').trim();}
 function text(){
  var lines=['【归海录反馈】','类型：'+v('fb-type'),'标题/搜索词：'+v('fb-title')];
  if(v('fb-page'))lines.push('页面：'+v('fb-page'));
  lines.push('详情：'+v('fb-detail'));
  if(v('fb-contact'))lines.push('联系方式：'+v('fb-contact'));
  return lines.join('\\n');
 }
 function ok(){st.textContent='已复制。请粘贴到微信/Lark 发给志远行空或归海群。';window.ghlTrack('feedback_copy',{type:v('fb-type')});}
 function fail(){
  var ta=document.createElement('textarea');ta.value=text();document.body.appendChild(ta);ta.select();
  try{document.execCommand('copy');ok();}catch(e){st.textContent='复制失败，请手动选择文本复制。';}
  ta.remove();
 }
 document.getElementById('fb-copy').addEventListener('click',function(){
  var tx=text();
  if(navigator.clipboard&&navigator.clipboard.writeText){navigator.clipboard.writeText(tx).then(ok,fail);}else{fail();}
 });
 document.getElementById('fb-clear').addEventListener('click',function(){
  ['fb-title','fb-page','fb-detail','fb-contact'].forEach(function(id){document.getElementById(id).value='';});
  st.textContent='';
 });
})();
</script>'''
(HERE / "feedback.html").write_text(
    _render_page("feedback.html", "反馈 / 报错 · 归海录", "发现错字、链接失效或搜索找不到，复制反馈内容发给志远行空。",
                 _FEEDBACK_BODY, compact=True, noindex=True),
    encoding="utf-8", newline="\n")

def _atom_dt(d):
    return (d or _latest_date or "2026-10-22") + "T00:00:00+08:00"
_feed_items = _entries[:20]
_feed_entries = []
for _e in _feed_items:
    _url = f"https://guihailu.github.io/{_e['page']}#{_e['id']}"
    _bm = re.search(r'<div class="entry-body">(.*)$', _e['block'], re.S)
    _sum = _plain(_bm.group(1))[:180] if _bm else ""
    _feed_entries.append(
        "<entry><title>" + _html.escape(_plain(_e["title"])) + "</title>"
        + '<link href="' + _html.escape(_url, quote=True) + '"/>'
        + "<id>" + _html.escape(_url) + "</id>"
        + "<updated>" + _atom_dt(_e.get("date")) + "</updated>"
        + "<summary>" + _html.escape(_sum) + "</summary></entry>")
_feed = ('<?xml version="1.0" encoding="utf-8"?>\n'
         '<feed xmlns="http://www.w3.org/2005/Atom">\n'
         '<title>归海录 · 志远行空</title>\n'
         '<subtitle>' + _html.escape(_HOME_DESC) + '</subtitle>\n'
         '<link href="https://guihailu.github.io/"/>\n'
         '<link rel="self" href="https://guihailu.github.io/feed.xml"/>\n'
         '<id>https://guihailu.github.io/</id>\n'
         '<updated>' + _atom_dt(_latest_date) + '</updated>\n'
         '<author><name>志远行空</name></author>\n'
         + "\n".join(_feed_entries) + '\n</feed>\n')
(HERE / "feed.xml").write_text(_feed, encoding="utf-8", newline="\n")
print(f"OK: SEO 辅助文件 favicon/manifest/robots/sitemap/404/feed 已生成（{len(_sitemap_urls)} URL）")
