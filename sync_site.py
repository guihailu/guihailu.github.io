# -*- coding: utf-8 -*-
"""归海录站点一键同步：Lark 导出 -> 构建 -> git 推送"""
import subprocess, sys, pathlib, os

HERE = pathlib.Path(__file__).parent
DOC_URL = "https://u78zyhf3gaz.jp.larksuite.com/docx/QKYtdsvHzoH1aIxuGhrjD81EpWf"

def run(cmd, **kw):
    print("$", " ".join(cmd))
    r = subprocess.run(cmd, cwd=HERE, **kw)
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
# 3) git 提交推送
run(["git", "add", "index.html", "guihailu.md", "build_site.py", "sync_site.py"])
run(["git", "commit", "-m", "站点同步：归海录更新"])
run(["git", "push"])
print("SYNC OK")
