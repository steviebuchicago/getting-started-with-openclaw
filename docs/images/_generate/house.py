"""Shared house style + helpers for the getting-started-with-openclaw imagery.

Palette (dark house style), fonts, and the two render pipelines:
  * terminal captures : rich Console(record=True) -> save_svg -> cairosvg
  * diagrams          : hand-written SVG strings -> cairosvg

Nothing here invents product facts; all copy comes from
/root/openclaw_captures/FACTS.md and the captured CLI output.
"""

import os
import re
import subprocess

import cairosvg
from PIL import Image, ImageFont

# ---------------------------------------------------------------- palette ---
BG_TOP = "#0A1220"
BG_BOT = "#0E1B2E"
BG_SOLID = "#0C1626"
PANEL = "#12233A"
STROKE = "#23405F"
HEAD = "#E8F1F8"
BODY = "#AFC6DA"
CYAN = "#7FD8E8"
CRIMSON = "#E4573D"
MUTED = "#5E7A94"

# --------------------------------------------------------------- outputs ---
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.abspath(os.path.join(HERE, ".."))
CAPTURES = "/root/openclaw_captures"

# ----------------------------------------------------------------- fonts ---
# cairosvg has no font fallback, so every glyph must exist in the font that
# fontconfig actually resolves. Verified on this box:
#   "Helvetica, Arial, sans-serif" -> TeX Gyre Heros (Helvetica metric clone)
#   monospace for terminals        -> DejaVu Sans Mono (full box-drawing set)
SANS_STACK = "Helvetica, Arial, sans-serif"
MONO_STACK = "DejaVu Sans Mono, monospace"
MONO_TTF = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
MONO_ADVANCE_EM = 0.602046875  # DejaVu Sans Mono advance width


def _fc_file(pattern):
    return subprocess.run(
        ["fc-match", "-f", "%{file}", pattern],
        capture_output=True, text=True, check=True,
    ).stdout.strip()


SANS_REG_TTF = _fc_file("Helvetica")
SANS_BOLD_TTF = _fc_file("Helvetica:bold")

_font_cache = {}


def font(size, bold=False):
    key = (size, bold)
    if key not in _font_cache:
        _font_cache[key] = ImageFont.truetype(
            SANS_BOLD_TTF if bold else SANS_REG_TTF, size)
    return _font_cache[key]


def text_w(s, size, bold=False):
    """Rendered width in px of `s` in the diagram sans face."""
    return font(size, bold).getlength(s)


def text_w_mono(s, size):
    """Rendered width in px of `s` in the monospace face (DejaVu Sans Mono)."""
    return len(s) * MONO_ADVANCE_EM * size


# TeX Gyre Heros has no U+21C5 / U+2713; arrows are drawn as paths instead.
_FORBIDDEN = {"⇅", "✓", "△", "①", "②", "③",
              "④", "⑤", "⑥"}


def assert_renderable(s, where=""):
    bad = sorted(set(s) & _FORBIDDEN)
    if bad:
        raise ValueError("glyph(s) %r missing from the diagram font (%s)"
                         % (bad, where))
    return s


def esc(s):
    """XML-escape text for an SVG <text> node."""
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


# ------------------------------------------------------- rich terminal SVG --
# rich writes textLength on every run and assumes a 12.2px cell; cairosvg
# ignores textLength, so we pin the monospace face at the size whose natural
# advance is exactly 12.2px (DejaVu Sans Mono advance = 0.602046875 em).
CELL_PX = 12.2
MONO_PX = CELL_PX / MONO_ADVANCE_EM  # ~20.264


def patch_terminal_svg(path):
    svg = open(path, encoding="utf-8").read()
    # Drop the remote Fira Code @font-face blocks (cairosvg cannot fetch them).
    svg = re.sub(r"@font-face \{.*?\}\n", "", svg, flags=re.S)
    svg = svg.replace("font-family: Fira Code, monospace;",
                      "font-family: %s;" % MONO_STACK)
    svg = svg.replace("font-size: 20px;", "font-size: %.4fpx;" % MONO_PX)
    svg = svg.replace("font-family: arial;", "font-family: %s;" % SANS_STACK)
    open(path, "w", encoding="utf-8").write(svg)
    return path


def svg_to_png(svg_path, png_path, scale=2):
    cairosvg.svg2png(url=svg_path, write_to=png_path, scale=scale)
    return png_path


def verify(png_path, min_width=1200):
    """Mandatory post-render check: open it, assert it is big enough, report."""
    with Image.open(png_path) as im:
        w, h = im.size
    assert w > min_width, "%s is only %dpx wide" % (png_path, w)
    print("  verified %-28s %d x %d px" % (os.path.basename(png_path), w, h))
    return (w, h)
