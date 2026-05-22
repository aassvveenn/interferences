#!/usr/bin/env python3
"""
Markdown → HTML converter (v2 — markdown-it-py)
Transforms a Markdown file following the ECRI-template.md format
into HTML blocks following the template.html structure.

Usage:
    python markdown_to_html.py input.md [output.html]
    If output path is omitted, prints to stdout.

Requires:
    pip install markdown-it-py
"""

import re
import sys
from pathlib import Path
from markdown_it import MarkdownIt


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

YOUTUBE_RE = re.compile(
    r'(?:https?://)?(?:www\.)?(?:youtube\.com/watch\?v=|youtu\.be/)([A-Za-z0-9_-]{11})'
)

SECTION_RE = re.compile(
    r'^##\s+(Prompt|Response|Modèle pour les réponses)\s*:?\s*(.*)$',
    re.IGNORECASE,
)
DATE_RE  = re.compile(r'^\d{4}-\d{2}-\d{2}$')
TITLE_RE = re.compile(r'^#\s+')


# ---------------------------------------------------------------------------
# Markdown-it setup
# ---------------------------------------------------------------------------

def build_md() -> MarkdownIt:
    """Return a MarkdownIt instance with HTML passthrough enabled."""
    md = MarkdownIt("commonmark", {"html": True})

    def render_blank_link(self, tokens, idx, options, env):
        tokens[idx].attrSet("target", "_blank")
        return self.renderToken(tokens, idx, options, env)

    md.add_render_rule("link_open", render_blank_link)
    return md


# ---------------------------------------------------------------------------
# Post-processing helpers applied to rendered HTML
# ---------------------------------------------------------------------------

def rewrite_img_src(html: str) -> str:
    """Rewrite src of every <img> tag only: keep filename, prefix journal/media/.
    iframe src attributes are left untouched."""
    def _rewrite_tag(m: re.Match) -> str:
        tag = m.group(0)
        def _fix_src(sm: re.Match) -> str:
            src = sm.group(1)
            if src.startswith("journal/media/"):
                return sm.group(0)
            filename = Path(src).name
            return f'src="journal/media/{filename}"'
        return re.sub(r'src=["\']([^"\']+)["\']', _fix_src, tag)

    return re.sub(r'<img\b[^>]*>', _rewrite_tag, html)


def youtube_embed(video_id: str) -> str:
    return (
        '<div class="video-wrapper" style="position:relative;padding-bottom:56.25%;'
        'height:0;overflow:hidden;">'
        f'<iframe src="https://www.youtube.com/embed/{video_id}" '
        'style="position:absolute;top:0;left:0;width:100%;height:100%;" '
        'frameborder="0" allowfullscreen loading="lazy"></iframe>'
        '</div>'
    )


def replace_youtube_links(html: str) -> str:
    """
    Replace YouTube patterns in rendered HTML:
    1. <img src="youtube_url" ...> → responsive embed (Markdown image with YT url)
    2. Bare paragraph containing only a YouTube URL → embed
    """
    # Pattern 1: <img> whose src is a YouTube URL
    def _img_yt(m: re.Match) -> str:
        src_m = re.search(r'src=["\']([^"\']+)["\']', m.group(0))
        if src_m:
            yt = YOUTUBE_RE.search(src_m.group(1))
            if yt:
                return youtube_embed(yt.group(1))
        return m.group(0)

    html = re.sub(r'<img\b[^>]*/>', _img_yt, html)

    # Pattern 2: bare paragraph containing only a YouTube URL
    def _bare_yt_para(m: re.Match) -> str:
        content = m.group(1).strip()
        yt = YOUTUBE_RE.fullmatch(content)
        if yt:
            return youtube_embed(yt.group(1))
        return m.group(0)

    html = re.sub(r'<p>([^<]+)</p>', _bare_yt_para, html)

    return html


def render_block_content(lines: list[str], model_prefix: str | None) -> str:
    """
    Render a list of raw Markdown lines to an HTML fragment.
    Optionally prepends an italic model label paragraph.
    """
    md = build_md()
    raw = "".join(lines)
    html = md.render(raw)

    # YouTube first (before src rewriting which would mangle YouTube URLs)
    html = replace_youtube_links(html)

    # Then rewrite remaining <img> src paths
    html = rewrite_img_src(html)

    if model_prefix:
        html = f"<p><em>{model_prefix}</em></p>\n" + html

    return html.strip()


# ---------------------------------------------------------------------------
# ECRI segmentation (pure Python — no lib knows this format)
# ---------------------------------------------------------------------------

def parse_ecri(md_text: str):
    """
    Parse ECRI-formatted Markdown into structured sections.

    Returns:
        model_label (str | None)
        sections: list of (type, title, lines)
            type  : 'Prompt' | 'Response'
            title : str (may be empty)
            lines : list[str]
    """
    lines = md_text.splitlines(keepends=True)
    model_label = None
    sections = []

    current_type  = None
    current_title = ""
    current_lines = []
    skip_next_date = False
    collecting_model = False

    def flush():
        if current_type and current_lines:
            # Strip leading/trailing blank lines
            stripped = current_lines.copy()
            while stripped and not stripped[0].strip():
                stripped.pop(0)
            while stripped and not stripped[-1].strip():
                stripped.pop()
            if stripped:
                sections.append((current_type, current_title, stripped))

    for line in lines:
        stripped = line.strip()

        # Ignore H1 title
        if TITLE_RE.match(stripped):
            continue

        m = SECTION_RE.match(stripped)
        if m:
            flush()
            current_type  = None
            current_title = ""
            current_lines = []
            collecting_model = False

            section_name  = m.group(1)
            inline_title  = m.group(2).strip()

            if section_name.lower() == "modèle pour les réponses":
                collecting_model = True
                skip_next_date = False
            elif section_name.lower() == "prompt":
                current_type  = "Prompt"
                current_title = inline_title
                skip_next_date = True
            elif section_name.lower() == "response":
                current_type  = "Response"
                skip_next_date = True
            continue

        # Collect model label (single non-empty line after the header)
        if collecting_model:
            if stripped:
                model_label = stripped
                collecting_model = False
            continue

        # Skip date line immediately following a section header
        if skip_next_date and DATE_RE.match(stripped):
            skip_next_date = False
            continue
        skip_next_date = False

        if current_type in ("Prompt", "Response"):
            current_lines.append(line)

    flush()
    return model_label, sections


# ---------------------------------------------------------------------------
# Main converter
# ---------------------------------------------------------------------------

def convert(md_text: str) -> str:
    model_label, sections = parse_ecri(md_text)
    blocks = []
    first_response = True

    for sec_type, sec_title, sec_lines in sections:
        css_class = "author-voice" if sec_type == "Prompt" else "ai-voice"

        # Inter-title: Prompt sections with a non-empty title
        if sec_type == "Prompt" and sec_title:
            blocks.append(f'  <h3 class="section-title">{sec_title}</h3>')

        # Inject model label in italics at the start of the first Response block
        prefix = None
        if sec_type == "Response" and first_response and model_label:
            prefix = model_label
            first_response = False

        content_html = render_block_content(sec_lines, prefix)
        if content_html:
            # Indent content for readability
            indented = "\n".join("    " + l for l in content_html.splitlines())
            blocks.append(f'  <div class="{css_class}">\n{indented}\n  </div>')

    return "<main>\n" + "\n\n".join(blocks) + "\n</main>"


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main():
    if len(sys.argv) < 2:
        print("Usage: python markdown_to_html.py input.md [output.html]", file=sys.stderr)
        sys.exit(1)

    input_path = Path(sys.argv[1])
    if not input_path.exists():
        print(f"Error: file not found: {input_path}", file=sys.stderr)
        sys.exit(1)

    md_text = input_path.read_text(encoding="utf-8")
    html = convert(md_text)

    if len(sys.argv) >= 3:
        output_path = Path(sys.argv[2])
        output_path.write_text(html, encoding="utf-8")
        print(f"Written to {output_path}")
    else:
        print(html)


if __name__ == "__main__":
    main()