"""Builds README.md from profile.json, plus a local preview at assets/preview.html.

Local tool only (the nightly workflow never runs it). After changing profile.json or theme.json:

    python3 scripts/generate.py && python3 scripts/build_readme.py

then open assets/preview.html in any browser. The preview loads the SVGs from assets/ next to it, so it works offline
and follows your system's dark/light setting just like GitHub does.
"""
import base64
import json
import re
from html import escape
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
RAW = "https://raw.githubusercontent.com/virajchikhale/virajchikhale"
ASSETS = f"{RAW}/agent-output"   # published by .github/workflows/agent-card.yml
SNAKE = f"{RAW}/output"          # published by .github/workflows/snake.yml


def pic(base: str, stem: str, alt: str, dark_name: str = "{}-dark.svg", light_name: str = "{}-light.svg") -> str:
    dark, light = f"{base}/{dark_name.format(stem)}", f"{base}/{light_name.format(stem)}"
    return (f'<picture>\n  <source media="(prefers-color-scheme: dark)" srcset="{dark}" />\n'
            f'  <source media="(prefers-color-scheme: light)" srcset="{light}" />\n'
            f'  <img width="100%" src="{light}" alt="{escape(alt)}" />\n</picture>')


def render(profile: dict, base: str) -> str:
    links = dict(profile["links"])
    head = lambda key, text: pic(base, f"header-{key}", text)  # noqa: E731

    cells = []
    for p in profile["projects"]:
        card = pic(base, f'card-{p["slug"]}', f'{p["title"]}: {p["impact"]}')
        if p.get("url"):
            card = f'<a href="{p["url"]}">\n{card}\n</a>'
        cells.append(f'<td width="50%" valign="top">\n{card}\n</td>')
    rows = "\n".join("<tr>\n" + "\n".join(cells[i:i + 2]) + "\n</tr>" for i in range(0, len(cells), 2))

    about = "\n".join(f"<p>{escape(line)}</p>" for line in profile["about"])
    link_bar = " &nbsp;·&nbsp; ".join(f'<a href="{url}">{escape(label)}</a>' for label, url in profile["links"])

    return f"""{pic(base, "hero", f'{profile["name"]}: {profile["role"]}')}

<p>{link_bar}</p>

{head("agent", "This Profile Runs an Agent")}

<p>Every night a small pipeline refreshes this page: a commit agent calls an MCP server for my latest commits, a drafting skill turns them into a summary, and the result is rendered below, including the "now" line at the top.</p>

{pic(base, "agent-loop", "Agent loop: nightly run, commit agent, MCP server, draft skill, LLM, README card")}

{pic(base, "agent-trace", "Agent trace of what I am building")}

{head("projects", "Featured Projects")}

<table width="100%">
{rows}
</table>

{head("stack", "Stack")}

{pic(base, "stack", "Stack: " + "; ".join(f"{g}: {', '.join(items)}" for g, items in profile["stack"]))}

{head("about", "About Me")}

{about}
<p>Work history and experience are on <a href="{links["LinkedIn"]}">LinkedIn</a>.</p>

{head("activity", "Activity")}

{pic(SNAKE, "github-snake", "GitHub contribution snake", "{}-dark.svg", "{}.svg")}

<p><i>{escape(profile["footer"])}</i></p>
"""


PREVIEW_CSS = """
:root{{color-scheme:light dark}}
body{{max-width:900px;margin:0 auto;padding:32px 16px;background:{lb};color:{lt};
font:16px/1.6 -apple-system,Segoe UI,Helvetica,Arial,sans-serif}}
a{{color:{la}}} img{{max-width:100%;display:block}} table{{border-collapse:collapse;width:100%}} td{{padding:6px}}
@media (prefers-color-scheme: dark){{body{{background:{db};color:{dt}}} a{{color:{da}}}}}
"""


def main() -> None:
    profile = json.loads((HERE / "profile.json").read_text(encoding="utf-8"))
    theme = json.loads((HERE / "theme.json").read_text(encoding="utf-8"))
    (ROOT / "README.md").write_text(render(profile, ASSETS), encoding="utf-8")

    css = PREVIEW_CSS.format(lb=theme["light"]["bg"], lt=theme["light"]["text"], la=theme["light"]["accent"],
                             db=theme["dark"]["bg"], dt=theme["dark"]["text"], da=theme["dark"]["accent"])
    page = (f'<!doctype html>\n<html lang="en"><head><meta charset="utf-8">'
            f'<meta name="viewport" content="width=device-width,initial-scale=1"><title>README preview</title>'
            f'<style>{css}</style></head><body>\n{render(profile, ".")}\n</body></html>\n')
    (ROOT / "assets" / "preview.html").write_text(page, encoding="utf-8")
    # single-file copy with the SVGs embedded, for sending to another device
    standalone = re.sub(r'"\./([\w-]+\.svg)"', lambda m: '"data:image/svg+xml;base64,'
                        + base64.b64encode((ROOT / "assets" / m.group(1)).read_bytes()).decode() + '"', page)
    (ROOT / "assets" / "preview-standalone.html").write_text(standalone, encoding="utf-8")
    print("wrote README.md, assets/preview.html and assets/preview-standalone.html")


if __name__ == "__main__":
    main()
