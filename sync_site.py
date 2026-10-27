# -*- coding: utf-8 -*-
"""归海录站点一键同步：Lark 导出 -> 构建 -> git 推送"""
import subprocess, sys, pathlib, os, json

HERE = pathlib.Path(__file__).parent
DOC_URL = "https://u78zyhf3gaz.jp.larksuite.com/docx/QKYtdsvHzoH1aIxuGhrjD81EpWf"

def run(cmd, **kw):
    print("$", " ".join(cmd))
    # lark-cli 是 .cmd shim，Windows 下必须走 shell 才能被解析
    r = subprocess.run(cmd, cwd=HERE, shell=True, **kw)
    if r.returncode != 0:
        sys.exit(r.returncode)

# ---- P0-1 发布门禁（构建之后、git add 之前；失败则不提交、不推送）----
def _gate_fail(msg):
    print(f"GATE FAIL: {msg}", file=sys.stderr)
    sys.exit(2)

def _read_manifest_count(path):
    try:
        data = json.loads(pathlib.Path(path).read_text(encoding="utf-8"))
        count = int(data["count"])
    except Exception as e:
        _gate_fail(f"无法读取 {path} 的 count：{e}")
    return count

def _git_show_text(relpath):
    r = subprocess.run(["git", "show", f"HEAD:{relpath}"],
                       cwd=HERE, capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    if r.returncode != 0:
        _gate_fail(f"无法读取上一版 {relpath}（git show HEAD:{relpath} 失败）：{r.stderr.strip()}")
    return r.stdout

def _count_toc_items(text):
    lines = text.splitlines()
    start = None
    end = None
    for i, line in enumerate(lines):
        if line.strip() == "# 📋 目录" and start is None:
            start = i
        elif start is not None and i > start and line.startswith("# "):
            end = i
            break
    section = lines[start:end] if start is not None else []
    return sum(1 for line in section if line.startswith("- ["))

def check_release_gate(base):
    """P0-1 门禁。base 为站点目录。任一检查失败即以退出码 2 终止，不提交、不推送。"""
    base = pathlib.Path(base)
    # 1) 新版条数不得低于上一版（以 search_manifest.json 的 count 为准）
    new_count = _read_manifest_count(base / "search_manifest.json")
    try:
        old_data = json.loads(_git_show_text("search_manifest.json"))
        old_count = int(old_data["count"])
    except SystemExit:
        raise
    except Exception as e:
        _gate_fail(f"无法解析上一版 search_manifest.json 的 count：{e}")
    if new_count < old_count:
        _gate_fail(f"条数下降：新版 {new_count} < 上一版 {old_count}，拒绝提交")
    # 2) 导出文件非空，且 TOC 条数不得低于上一版
    src = base / "guihailu.md"
    if not src.exists() or src.stat().st_size == 0:
        _gate_fail("guihailu.md 缺失或为空，拒绝提交")
    new_text = src.read_text(encoding="utf-8", errors="replace")
    if "# 📋 目录" not in new_text:
        _gate_fail("guihailu.md 缺少“# 📋 目录”标记，可能导出不完整，拒绝提交")
    new_toc = _count_toc_items(new_text)
    old_toc = _count_toc_items(_git_show_text("guihailu.md"))
    if new_toc < old_toc:
        _gate_fail(f"TOC 条数下降：新版 {new_toc} < 上一版 {old_toc}，拒绝提交")
    # 3) 健康检查必须通过。脚本为本地工具（站点/_scripts/site_health.py）；
    #    找不到脚本时同样拒绝提交（fail-closed），避免在没有健康检查的机器上裸推。
    health = base / "_scripts" / "site_health.py"
    if not health.exists():
        _gate_fail(f"未找到健康检查脚本 {health}，拒绝提交（请先确认该脚本已随站点目录部署）")
    r = subprocess.run([sys.executable, str(health)], cwd=base,
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode != 0:
        tail = (r.stdout + r.stderr).strip().splitlines()[-20:]
        _gate_fail("健康检查未通过，拒绝提交\n" + "\n".join(tail))
    print(f"GATE PASS: manifest {old_count} -> {new_count}，TOC {old_toc} -> {new_toc}，健康检查通过")

env = dict(os.environ)
# 本地代理 11304 已于 09-20 挂掉；Lark/git 均可直连，proxy 一律置空（代理恢复后可还原）
env.setdefault("HTTPS_PROXY", "")
env.setdefault("HTTP_PROXY", "")
env["LARKSUITE_CLI_NO_UPDATE_NOTIFIER"] = "1"
env["PYTHONIOENCODING"] = "utf-8"

# 1) 导出 Lark 文档（10 月：--profile qinglai 经新号清籁读取；主号 API 额度冻结）
run(["lark-cli", "--profile", "qinglai", "drive", "+export", "--url", DOC_URL,
     "--file-extension", "markdown", "--file-name", "guihailu.md", "--overwrite"], env=env)
# 2) 构建
run([sys.executable, "build_site.py"], env=env)
# 3) 将需要登录的 Lark 图片镜像成公开静态资源
run([sys.executable, "mirror_media.py"], env=env)
# 3.5) P0-1 发布门禁：构建之后、git add 之前；失败则直接退出，不提交、不推送
check_release_gate(HERE)
# 4) git 提交推送（无变化则静默跳过；页面与资源必须同一次提交）
_page_files = (["index.html", "undated.html", "404.html", "feedback.html", "all.html", "newcomer.html"] +
               sorted(p.name for p in HERE.glob("20[0-9][0-9].html")) +
               sorted(p.name for p in HERE.glob("newcomer-*.html")))
_index_files = (["search_shared.json", "search_manifest.json"] +
                sorted(p.name for p in HERE.glob("search_index_*.json")))
_aux_files = ["sitemap.xml", "robots.txt", "favicon.svg", "favicon.ico", "manifest.json", "feed.xml", "cover.jpg", "goatcounter.js"]
run(["git", "add", "-A", "--", *_page_files,
     "guihailu.md", "build_site.py",
     "sync_site.py", "mirror_media.py", "style.v5.css", "main.v5.js",
     *_index_files, *_aux_files, "归海录_离线版.html", "id_map.json",
     "legacy_anchors.json", "guide_data.py", "t2s.json", "analytics.json", "media"])
r = subprocess.run(["git", "commit", "-m", "站点同步：归海录更新"],
                   cwd=HERE, capture_output=True, text=True, encoding="utf-8", errors="replace")
if r.returncode == 0:
    run(["git", "push"])
    print("SYNC PUSHED")
    sys.exit(0)
elif "nothing to commit" in (r.stdout + r.stderr) or "nothing added to commit" in (r.stdout + r.stderr):
    print("NO CHANGE")
    sys.exit(0)   # 无变化=任务成功，退出码 0（修复任务计划"结果=1"误判；git 有 untracked 文件时报"nothing added to commit"）
else:
    print(r.stdout, r.stderr)
    sys.exit(r.returncode)
