# -*- coding: utf-8 -*-
"""Mirror Lark document images for visitors who are not signed in to Lark."""
import hashlib
import json
import os
import pathlib
import re
import shutil
import subprocess
import tempfile


HERE = pathlib.Path(__file__).resolve().parent
MEDIA = HERE / "media"
INDEX = HERE / "index.html"
IMAGE = re.compile(r'(<img\b[^>]*?\bsrc=")https://feishu\.cn/file/([A-Za-z0-9]+)("[^>]*>)')
EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".gif"}


def local_image(token):
    stem = hashlib.sha256(token.encode("ascii")).hexdigest()[:20]
    existing = [path for path in MEDIA.glob(stem + ".*") if path.suffix.lower() in EXTENSIONS]
    if len(existing) == 1:
        return existing[0]
    if existing:
        raise RuntimeError(f"Multiple media files for {stem}")

    with tempfile.TemporaryDirectory(prefix="lark-media-", dir=HERE) as directory:
        temporary = pathlib.Path(directory)
        result = subprocess.run(
            ["lark-cli", "docs", "+media-download", "--token", token,
             "--output", "./source", "--overwrite"],
            cwd=temporary, capture_output=True, text=True,
            shell=os.name == "nt", encoding="utf-8", errors="replace",
        )
        json_start = result.stdout.find("{")
        data = json.loads(result.stdout[json_start:]) if json_start >= 0 else {}
        sources = list(temporary.glob("source.*"))
        if result.returncode or not data.get("ok") or len(sources) != 1:
            raise RuntimeError(f"Lark image download failed for {stem}: {data.get('error', result.stderr)}")
        source = sources[0]
        if source.suffix.lower() not in EXTENSIONS or not data["data"]["content_type"].startswith("image/"):
            raise RuntimeError(f"Unsupported Lark image type for {stem}")

        chosen = source
        if source.suffix.lower() in {".png", ".jpg", ".jpeg"} and source.stat().st_size > 1_000_000:
            webp = temporary / "optimized.webp"
            conversion = subprocess.run(
                ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(source),
                 "-frames:v", "1", "-c:v", "libwebp", "-pix_fmt", "bgra",
                 "-preset", "text", "-compression_level", "6", "-quality", "100",
                 "-lossless", "1", str(webp)],
                capture_output=True, text=True,
            )
            if conversion.returncode == 0 and webp.exists() and webp.stat().st_size < source.stat().st_size:
                chosen = webp

        MEDIA.mkdir(exist_ok=True)
        target = MEDIA / (stem + chosen.suffix.lower())
        partial = MEDIA / (stem + ".partial")
        shutil.copyfile(chosen, partial)
        os.replace(partial, target)
        print(f"Mirrored image {stem}: {target.stat().st_size} bytes")
        return target


def main():
    html = INDEX.read_text(encoding="utf-8")
    tokens = set(IMAGE.findall(html))
    if not tokens:
        print("No Lark images to mirror")
        return
    replacements = {}
    for _, token, _ in tokens:
        replacements[token] = "media/" + local_image(token).name

    def replace(match):
        beginning, token, ending = match.groups()
        if "loading=" not in ending:
            ending = ending.replace(" />", ' loading="lazy" decoding="async" />')
        path = replacements[token]
        image = beginning + path + ending
        return f'<a href="{path}" target="_blank" rel="noopener" aria-label="打开原图">{image}</a>'

    updated = IMAGE.sub(replace, html)
    if updated != html:
        INDEX.write_text(updated, encoding="utf-8", newline="")
    print(f"Mirrored {len(replacements)} unique images")


if __name__ == "__main__":
    main()
