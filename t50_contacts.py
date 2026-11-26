"""T50 contact blocks shared by the reviewed post-build step."""
from __future__ import annotations

from pathlib import Path

CONTACT = """<section class=\"t50-contact\" aria-labelledby=\"t50-{place}\">
<h2 id=\"t50-{place}\">联系我们</h2>
<p><a href=\"https://wa.me/4407706981476\" target=\"_blank\" rel=\"noopener noreferrer\">WhatsApp：wa.me/4407706981476</a>（加时请注明来处，如“油管”“TikTok”）</p>
<p><a href=\"https://t.me/zyxk888\" target=\"_blank\" rel=\"noopener noreferrer\">Telegram：t.me/zyxk888</a></p>
</section>"""

STYLE = """<style id=\"t50-contact-style\">
.t50-contact{box-sizing:border-box;max-width:56rem;margin:1.5rem auto;padding:1rem clamp(.85rem,3vw,1.6rem);text-align:start;border:1px solid currentColor;border-radius:.65rem;line-height:1.7}
.t50-contact h2{font:inherit;font-size:1.16rem;font-weight:700;margin:0 0 .4rem}.t50-contact p{margin:.2rem 0}.t50-contact a{color:inherit;text-decoration:underline;text-underline-offset:.18em;overflow-wrap:anywhere}
@media(max-width:640px){.t50-contact{margin:1rem .75rem}}
</style>"""


def render(name: str, source: str) -> str:
    if name == "index.html":
        boundaries = [("</main>", "home-body"), ("</footer>", "home-footer")]
    elif name == "newcomer.html":
        boundaries = [("</section>\n</div>\n<footer>", "newcomer")]
    else:
        raise ValueError(name)
    result = source
    for boundary, place in boundaries:
        if result.count(boundary) != 1:
            raise ValueError(f"Unexpected {name} boundary {boundary!r}")
        block = CONTACT.format(place=place)
        result = result.replace(
            boundary,
            ("</section>\n" + block + "\n</div>\n<footer>" if place == "newcomer" else block + "\n" + boundary),
        )
    if result.count("</head>") != 1:
        raise ValueError(f"Unexpected {name} head count")
    return result.replace("</head>", STYLE + "\n</head>", 1)


def build(source_dir: Path, output_dir: Path) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    written = []
    for name in ("index.html", "newcomer.html"):
        target = output_dir / name
        target.write_text(render(name, (source_dir / name).read_text(encoding="utf-8")), encoding="utf-8", newline="\n")
        written.append(target)
    return written


def patch_file(path: Path) -> bool:
    """Apply the correct block once; return whether the file changed."""
    name = path.name
    source = path.read_text(encoding="utf-8")
    markers = {
        "index.html": ("t50-home-body", "t50-home-footer"),
        "newcomer.html": ("t50-newcomer",),
    }[name]
    if 'id="t50-contact-style"' in source and all(f'id="{marker}"' in source for marker in markers):
        return False
    if 'id="t50-contact-style"' in source:
        raise ValueError(f"Partial T50 contact patch in {name}")
    updated = render(name, source)
    path.write_text(updated, encoding="utf-8", newline="\n")
    return True
