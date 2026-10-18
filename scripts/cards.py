"""SVG builders for the profile README: hero, section headers, project cards and the stack panel. Stdlib only.

Every builder takes `t`, one theme mode from theme.json (colours plus fonts), so restyling never touches this file.
Backgrounds are transparent unless a panel is needed, so the images sit on GitHub's own page colour.
"""
import textwrap
from html import escape


def hero(t: dict, name: str, role: str, tagline: str, now: str) -> str:
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 900 210" width="900" height="210" font-family="{t["sans"]}">'
        f'<text x="2" y="34" fill="{t["muted"]}" font-size="13" letter-spacing="1.5" font-family="{t["mono"]}">{escape(role.upper())}</text>'
        f'<text x="0" y="102" fill="{t["text"]}" font-size="58" font-weight="700" font-family="{t["serif"]}">{escape(name)}</text>'
        f'<text x="2" y="144" fill="{t["text"]}" fill-opacity="0.88" font-size="18">{escape(tagline)}</text>'
        f'<text x="2" y="186" fill="{t["accent"]}" font-size="14" font-family="{t["mono"]}">▸ now: {escape(now)} '
        '<tspan><animate attributeName="opacity" values="1;0;1" dur="1s" calcMode="discrete" repeatCount="indefinite"/>▌</tspan>'
        "</text></svg>"
    )


def header(t: dict, text: str, phase: float = 0.0) -> str:
    """Section header. The accent bar breathes slowly; `phase` offsets it so headers don't pulse in sync."""
    w = int(len(text) * 13 + 30)
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 900 48" width="900" height="48">'
        f'<rect x="0" y="11" width="5" height="26" rx="2.5" fill="{t["accent"]}">'
        f'<animate attributeName="opacity" values="0.6;1;0.6" dur="5s" begin="{phase:.1f}s" repeatCount="indefinite"/></rect>'
        f'<text x="20" y="33" fill="{t["text"]}" font-size="23" font-weight="700" font-family="{t["serif"]}">{escape(text)}</text>'
        f'<line x1="{w}" y1="24" x2="900" y2="24" stroke="{t["line"]}" stroke-width="1.5"/></svg>'
    )


def project_card(t: dict, p: dict, index: int) -> str:
    lines = textwrap.wrap(p["impact"], 46)[:3]
    body = "".join(
        f'<text x="24" y="{106 + i * 21}" fill="{t["muted"]}" font-size="14">{escape(line)}</text>' for i, line in enumerate(lines)
    )
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 440 170" width="440" height="170" font-family="{t["sans"]}">'
        f'<rect x="1" y="1" width="438" height="168" rx="10" fill="{t["panel"]}" stroke="{t["line"]}" stroke-width="1.5"/>'
        f'<text x="416" y="34" fill="{t["muted"]}" font-size="12" text-anchor="end" font-family="{t["mono"]}">{index:02d}</text>'
        f'<text x="24" y="42" fill="{t["text"]}" font-size="19" font-weight="700" font-family="{t["serif"]}">{escape(p["title"][:34])}</text>'
        f'<text x="24" y="70" fill="{t["accent"]}" font-size="12" font-family="{t["mono"]}">{escape(p["stack"])}</text>'
        f'{body}</svg>'
    )


def stack_panel(t: dict, groups: list, highlight: list) -> str:
    """Neutral chips; skills listed in `highlight` get the accent colour."""
    x0, y = 190, 8
    parts = []
    for gi, (label, items) in enumerate(groups):
        parts.append(f'<text x="2" y="{y + 18}" fill="{t["muted"]}" font-size="12" font-family="{t["mono"]}">{escape(label)}</text>')
        x = x0
        for item in items:
            w = len(item) * 7.4 + 24
            if x + w > 898:
                x, y = x0, y + 34
            col = t["accent"] if item in highlight else t["line"]
            txt = t["accent"] if item in highlight else t["text"]
            parts.append(
                f'<rect x="{x:.0f}" y="{y}" width="{w:.0f}" height="26" rx="13" fill="none" stroke="{col}" stroke-width="1.5"/>'
                f'<text x="{x + w / 2:.0f}" y="{y + 17}" fill="{txt}" font-size="12" text-anchor="middle" font-family="{t["mono"]}">{escape(item)}</text>'
            )
            x += w + 8
        y += 44
        if gi < len(groups) - 1:
            parts.append(f'<line x1="0" y1="{y - 9}" x2="900" y2="{y - 9}" stroke="{t["line"]}" stroke-width="1"/>')
    h = y - 4
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 900 {h}" width="900" height="{h}">' + "".join(parts) + "</svg>"
