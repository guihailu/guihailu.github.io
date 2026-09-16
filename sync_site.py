# -*- coding: utf-8 -*-
"""归海录站点一键同步：Lark 导出 -> 构建 -> git 推送"""
import subprocess, sys, pathlib, os

HERE = pathlib.Path(__file__).parent
DOC_URL = "https://u78zyhf3gaz.jp.larksuite.com/docx/QKYtdsvHzoH1aIxuGhrjD81EpWf"

def run(cmd, **kw):
    print("$", " ".join(cmd))
    # lark-cli 是 .cmd shim，Windows 下必须走 shell 才能被解析
    r = subprocess.run(cmd, cwd=HERE, shell=True, **kw)
    if r.returncode != 0:
        sys.exit(r.returncode)

env = dict(os.environ)
env.setdefault("HTTPS_PROXY", "http://127.0.0.1:11304")
env.setdefault("HTTP_PROXY", "http://127.0.0.1:11304")
env["LARKSUITE_CLI_NO_UPDATE_NOTIFIER"] = "1"
env["PYTHONIOENCODING"] = "utf-8"

# 1) 导出 Lark 文档
run(["lark-cli", "drive", "+export", "--url", DOC_URL,
     "--file-extension", "markdown", "--file-name", "guihailu.md", "--overwrite"], env=env)
# 2) 构建
run([sys.executable, "build_site.py"], env=env)
# 3) git 提交推送（无变化则静默跳过）
run(["git", "add", "index.html", "guihailu.md", "build_site.py", "sync_site.py"])
r = subprocess.run(["git", "commit", "-m", "站点同步：归海录更新"],
                   cwd=HERE, capture_output=True, text=True)
if r.returncode == 0:
    run(["git", "push"])
    print("SYNC PUSHED")
elif "nothing to commit" in (r.stdout + r.stderr):
    print("NO CHANGE")
else:
    print(r.stdout, r.stderr)
    sys.exit(r.returncode)
