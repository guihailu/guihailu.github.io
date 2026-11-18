#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""归海录内容计数与生成脚本回归；云端只读，不改动原文或部署。"""
from pathlib import Path
import json
import re
import sys

root = Path(__file__).resolve().parents[1]
errors = []
board = json.loads((root / "board_map.json").read_text(encoding="utf-8"))
count = len(board)
stats = {}
for item in board.values():
    b = int(item["board"])
    stats[b] = stats.get(b, 0) + 1
if stats != {1: 48, 2: 20, 3: 40, 4: 15}:
    errors.append(f"四部基线出现变动，需重新验算内容归属：{stats}")
for page in ("index.html", "topics.html"):
    doc = (root / page).read_text(encoding="utf-8")
    m = re.search(r'<meta name="description" content="[^"]*?(\d+) 篇讲课整理', doc)
    if not m or int(m.group(1)) != count:
        errors.append(f"{page}: Meta 描述篇数与目录 {count} 不一致")
    og = re.search(r'<meta property="og:description" content="[^"]*?(\d+) 篇讲课整理', doc)
    if not og or int(og.group(1)) != count:
        errors.append(f"{page}: OG 分享文案篇数与目录 {count} 不一致")
all_html = (root / "all.html").read_text(encoding="utf-8")
if f"归海录全部 {count} 篇" not in all_html:
    errors.append(f"all.html 不符合当前 {count} 篇总数")
builder = (root / "build_reading_front.py").read_text(encoding="utf-8")
if "{len(entries)} 篇讲课整理" not in builder:
    errors.append("生成脚本没有动态计算篇数，后续同步可能把旧数字覆盖")
if errors:
    for e in errors: print("FAIL:", e)
    sys.exit(1)
print(f"PASS: {count} 篇；四部 {stats}；index/topics/all 元描述与构建逻辑一致")
print("注意：真实原文对账、页面浏览器兼容性、线上部署和移动端访问未由本脚本验证")
