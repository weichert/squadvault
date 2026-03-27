"""Season HTML export — single-page styled archive of weekly recaps.

Read-only export. No canonical writes. Produces a self-contained HTML
file with dark mode support, table of contents, and collapsible facts.
"""

from __future__ import annotations

import html as html_mod
from dataclasses import dataclass


@dataclass(frozen=True)
class WeekRecapData:
    week: int
    narrative: str
    bullets: list[str]
    version: int
    state: str


def extract_shareable_parts(
    rendered_text: str,
) -> tuple[str, list[str]]:
    """Extract narrative and bullet facts from rendered_text.

    Returns (narrative_text, list_of_bullet_strings).
    """
    SHARE_START = "--- SHAREABLE RECAP ---"
    SHARE_END = "--- END SHAREABLE RECAP ---"
    OLD_DELIM = "--- Narrative Draft (AI-assisted, requires human approval) ---"
    BULLETS_MARKER = "What happened this week:"

    # Extract narrative
    if SHARE_START in rendered_text:
        start = rendered_text.index(SHARE_START) + len(SHARE_START)
        end = (
            rendered_text.index(SHARE_END)
            if SHARE_END in rendered_text
            else len(rendered_text)
        )
        narrative = rendered_text[start:end].strip()
    elif OLD_DELIM in rendered_text:
        start = rendered_text.index(OLD_DELIM) + len(OLD_DELIM)
        narrative = rendered_text[start:].strip()
    else:
        narrative = rendered_text.strip()

    # Extract bullets
    bullets: list[str] = []
    if BULLETS_MARKER in rendered_text and SHARE_START in rendered_text:
        b_start = rendered_text.index(BULLETS_MARKER) + len(BULLETS_MARKER)
        b_end = rendered_text.index(SHARE_START)
        raw_bullets = rendered_text[b_start:b_end].strip()
        for line in raw_bullets.split("\n"):
            line = line.strip()
            if line.startswith("- ") or line.startswith("\u2022 "):
                bullets.append(line[2:].strip())
            elif line:
                bullets.append(line)

    return narrative, bullets


def _esc(s: str) -> str:
    return html_mod.escape(s)


def _narrative_to_html(text: str) -> str:
    """Convert narrative text to HTML paragraphs."""
    paragraphs = []
    for para in text.split("\n\n"):
        para = para.strip()
        if para:
            paragraphs.append("<p>" + _esc(para) + "</p>")
    return "\n".join(paragraphs)


_CSS = """\
:root {
  --bg: #fafaf9;
  --fg: #1c1917;
  --accent: #dc2626;
  --muted: #78716c;
  --border: #e7e5e4;
  --card-bg: #ffffff;
  --card-shadow: 0 1px 3px rgba(0,0,0,0.08);
}
@media (prefers-color-scheme: dark) {
  :root {
    --bg: #1c1917;
    --fg: #fafaf9;
    --accent: #f87171;
    --muted: #a8a29e;
    --border: #44403c;
    --card-bg: #292524;
    --card-shadow: 0 1px 3px rgba(0,0,0,0.3);
  }
}
* { margin: 0; padding: 0; box-sizing: border-box; }
body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
  background: var(--bg);
  color: var(--fg);
  line-height: 1.65;
  padding: 2rem 1rem;
  max-width: 680px;
  margin: 0 auto;
}
header {
  text-align: center;
  margin-bottom: 2.5rem;
  padding-bottom: 1.5rem;
  border-bottom: 2px solid var(--accent);
}
header h1 {
  font-size: 1.75rem;
  font-weight: 700;
  letter-spacing: -0.02em;
}
header .subtitle {
  color: var(--muted);
  font-size: 0.95rem;
  margin-top: 0.25rem;
}
nav.toc {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  justify-content: center;
  margin-bottom: 2rem;
}
nav.toc a {
  color: var(--muted);
  text-decoration: none;
  font-size: 0.85rem;
  padding: 0.25rem 0.5rem;
  border: 1px solid var(--border);
  border-radius: 4px;
  transition: all 0.15s;
}
nav.toc a:hover {
  color: var(--accent);
  border-color: var(--accent);
}
article.week {
  background: var(--card-bg);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 1.5rem;
  margin-bottom: 1.5rem;
  box-shadow: var(--card-shadow);
}
article.week h2 {
  font-size: 1.15rem;
  font-weight: 600;
  color: var(--accent);
  margin-bottom: 1rem;
  padding-bottom: 0.5rem;
  border-bottom: 1px solid var(--border);
}
.narrative p {
  margin-bottom: 0.85rem;
}
.narrative p:last-child {
  margin-bottom: 0;
}
details.facts {
  margin-top: 1rem;
  border-top: 1px solid var(--border);
  padding-top: 0.75rem;
}
details.facts summary {
  font-size: 0.85rem;
  color: var(--muted);
  cursor: pointer;
  user-select: none;
}
details.facts ul {
  margin-top: 0.5rem;
  padding-left: 1.25rem;
  font-size: 0.85rem;
  color: var(--muted);
}
details.facts li {
  margin-bottom: 0.25rem;
}
footer {
  text-align: center;
  margin-top: 2rem;
  padding-top: 1rem;
  border-top: 1px solid var(--border);
  font-size: 0.8rem;
  color: var(--muted);
}
"""


def render_season_html(
    week_data: list[WeekRecapData],
    league_name: str,
    season: int,
) -> str:
    """Render a list of WeekRecapData into a self-contained HTML page."""
    if not week_data:
        return ""

    # Build week sections
    week_sections = []
    for wd in week_data:
        bullets_html = ""
        if wd.bullets:
            items = "\n".join(
                "<li>" + _esc(b) + "</li>" for b in wd.bullets
            )
            bullets_html = (
                '\n<details class="facts">\n'
                "<summary>What happened this week ("
                + str(len(wd.bullets))
                + " events)</summary>\n<ul>\n"
                + items
                + "\n</ul>\n</details>"
            )

        week_sections.append(
            '\n<article class="week" id="week-'
            + str(wd.week)
            + '">\n<h2>Week '
            + str(wd.week)
            + "</h2>\n"
            + '<div class="narrative">\n'
            + _narrative_to_html(wd.narrative)
            + "\n</div>"
            + bullets_html
            + "\n</article>"
        )

    # TOC
    toc_items = "\n".join(
        '<a href="#week-'
        + str(wd.week)
        + '">Week '
        + str(wd.week)
        + "</a>"
        for wd in week_data
    )

    return (
        "<!DOCTYPE html>\n"
        '<html lang="en">\n<head>\n'
        '<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        "<title>"
        + _esc(league_name)
        + " &mdash; "
        + str(season)
        + " Season Recaps</title>\n"
        "<style>\n"
        + _CSS
        + "</style>\n</head>\n<body>\n"
        "<header>\n<h1>"
        + _esc(league_name)
        + "</h1>\n"
        '<div class="subtitle">'
        + str(season)
        + " Season Recaps &middot; "
        + str(len(week_data))
        + " Weeks</div>\n</header>\n"
        '<nav class="toc">\n'
        + toc_items
        + "\n</nav>\n"
        + "".join(week_sections)
        + "\n<footer>\n"
        "Generated by SquadVault &middot; Facts are canonical, narratives are derived\n"
        "</footer>\n</body>\n</html>"
    )
