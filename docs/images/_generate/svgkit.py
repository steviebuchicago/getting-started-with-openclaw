"""Tiny hand-written-SVG toolkit for the diagrams.

Deliberately not matplotlib: box-and-arrow diagrams are assembled as SVG
strings and rasterised with cairosvg at scale 2.

Every text-bearing helper measures the string in the face cairosvg will
actually use (TeX Gyre Heros, what fontconfig resolves "Helvetica" to) and
raises if it would not fit its box, so no label can silently overflow.
"""

from house import (BG_BOT, BG_TOP, BODY, CYAN, HEAD, MUTED, PANEL, SANS_STACK,
                   STROKE, assert_renderable, esc, text_w)

# Authoring space; the SVG is emitted at half these numbers and rasterised at
# scale 2, so the PNG comes out at exactly W x H device pixels.
W, H = 1900, 950


# --------------------------------------------------------------- primitives --
def rrect(x, y, w, h, r=14, fill=PANEL, stroke=STROKE, sw=2, extra=""):
    return ('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" rx="%.1f" '
            'fill="%s" stroke="%s" stroke-width="%.1f"%s/>'
            % (x, y, w, h, r, fill, stroke, sw, (" " + extra) if extra else ""))


def txt(x, y, s, size=24, fill=BODY, bold=False, anchor="start", opacity=None):
    assert_renderable(s, s)
    op = '' if opacity is None else ' opacity="%.2f"' % opacity
    return ('<text x="%.1f" y="%.1f" font-family="%s" font-size="%.1f" '
            'font-weight="%s" fill="%s" text-anchor="%s"%s>%s</text>'
            % (x, y, SANS_STACK, size, "bold" if bold else "normal",
               fill, anchor, op, esc(s)))


def line(x1, y1, x2, y2, color=STROKE, sw=2, dash=None):
    d = '' if dash is None else ' stroke-dasharray="%s"' % dash
    return ('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="%s" '
            'stroke-width="%.1f" stroke-linecap="round"%s/>'
            % (x1, y1, x2, y2, color, sw, d))


def _head(x, y, dx, dy, color, size=11):
    """Filled triangle pointing along the unit vector (dx, dy)."""
    px, py = -dy, dx
    pts = [(x, y),
           (x - dx * size * 1.8 + px * size, y - dy * size * 1.8 + py * size),
           (x - dx * size * 1.8 - px * size, y - dy * size * 1.8 - py * size)]
    return ('<polygon points="%s" fill="%s"/>'
            % (" ".join("%.1f,%.1f" % p for p in pts), color))


def arrow(x1, y1, x2, y2, color=CYAN, sw=3, double=False, size=11):
    """Straight arrow from (x1,y1) to (x2,y2); double adds a head at the tail."""
    dx, dy = x2 - x1, y2 - y1
    n = (dx * dx + dy * dy) ** 0.5 or 1.0
    ux, uy = dx / n, dy / n
    inset = size * 1.6
    out = [line(x1 + (ux * inset if double else 0),
                y1 + (uy * inset if double else 0),
                x2 - ux * inset, y2 - uy * inset, color, sw),
           _head(x2, y2, ux, uy, color, size)]
    if double:
        out.append(_head(x1, y1, -ux, -uy, color, size))
    return "".join(out)


# ------------------------------------------------------------------ text fit --
def wrap(s, size, max_w, bold=False):
    """Greedy word wrap to `max_w` px. Raises if a single word cannot fit."""
    words, lines, cur = s.split(" "), [], ""
    for word in words:
        trial = (cur + " " + word).strip()
        if text_w(trial, size, bold) <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    for ln in lines:
        if text_w(ln, size, bold) > max_w:
            raise ValueError("cannot fit %r in %.0fpx at %dpx" % (ln, max_w, size))
    return lines


def fit(s, size, max_w, bold=False, where=""):
    """Assert a single-line label fits; returns it unchanged."""
    w = text_w(s, size, bold)
    if w > max_w:
        raise ValueError("%s: %r is %.0fpx, box allows %.0fpx"
                         % (where or "label", s, w, max_w))
    assert_renderable(s, where)
    return s


def block(cx, y0, lines, size, fill=BODY, bold=False, lh=None, anchor="middle"):
    """Render pre-wrapped lines, returns (svg, y after the last baseline)."""
    lh = lh or size * 1.34
    out, y = [], y0
    for ln in lines:
        out.append(txt(cx, y, ln, size, fill, bold, anchor))
        y += lh
    return "".join(out), y - lh


# --------------------------------------------------------------- the canvas --
def canvas(body, w=W, h=H, solid=False):
    bg = ('<rect width="%d" height="%d" fill="#0C1626"/>' % (w, h) if solid else
          '<defs><linearGradient id="bg" x1="0" y1="0" x2="0" y2="1">'
          '<stop offset="0" stop-color="%s"/><stop offset="1" stop-color="%s"/>'
          '</linearGradient></defs>'
          '<rect width="%d" height="%d" fill="url(#bg)"/>' % (BG_TOP, BG_BOT, w, h))
    return ('<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" '
            'viewBox="0 0 %d %d">%s%s</svg>'
            % (w // 2, h // 2, w, h, bg, body))


def heading(title, subtitle=None, x=60, y=100):
    out = [txt(x, y, title, 44, HEAD, bold=True)]
    if subtitle:
        out.append(txt(x, y + 46, subtitle, 26, MUTED))
    return "".join(out)


def kicker(x, y, s, fill=CYAN, size=20):
    """Small uppercase band label."""
    return txt(x, y, s.upper(), size, fill, bold=True)


__all__ = ["W", "H", "rrect", "txt", "line", "arrow", "wrap", "fit", "block",
           "canvas", "heading", "kicker", "PANEL", "STROKE", "HEAD", "BODY",
           "CYAN", "MUTED"]
