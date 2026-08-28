"""Terminal captures for docs/images.

rich Console(record=True) -> console.save_svg(title=...) -> cairosvg @ scale 2.
The mac-style window chrome comes from rich's `title` parameter; we never draw
our own. All content is the real CLI output captured in /root/openclaw_captures.

Console width is 100 columns, widened only where a box-drawing table would
otherwise wrap and break (status: 120, skills: fitted). Prose wraps at 100 the
way a real 100-column terminal wraps it.
"""

import os
import re  # noqa: F401
import textwrap

from rich.console import Console
from rich.terminal_theme import TerminalTheme
from rich.text import Text

from house import (BODY, CAPTURES, CRIMSON, CYAN, HEAD, MONO_TTF, MUTED, OUT,
                   patch_terminal_svg, svg_to_png, verify)

AMBER = "#E6C06E"

SCRATCH = os.path.join(OUT, "_generate", "_svg")
os.makedirs(SCRATCH, exist_ok=True)


def _rgb(h):
    h = h.lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


# House terminal theme: palette background, headline foreground.
HOUSE_THEME = TerminalTheme(
    _rgb("#0C1626"), _rgb(HEAD),
    [_rgb(MUTED), _rgb(CRIMSON), (126, 211, 133), _rgb(AMBER),
     _rgb(CYAN), (190, 150, 220), _rgb(CYAN), _rgb(BODY)],
    [_rgb("#78A0BE"), _rgb(CRIMSON), (126, 211, 133), _rgb(AMBER),
     _rgb(CYAN), (190, 150, 220), _rgb(CYAN), _rgb(HEAD)],
)

BOX_RE = r"[─-╿]"


def read(name):
    with open(os.path.join(CAPTURES, name), encoding="utf-8") as fh:
        return fh.read()


def soft_wrap(block, width=98):
    """Wrap long lines at `width`, hanging the continuation under its parent.

    Word order and wording are untouched; only line breaks are added, exactly
    as a terminal would add them.
    """
    out = []
    for line in block.split("\n"):
        if len(line) <= width:
            out.append(line)
            continue
        indent = line[:len(line) - len(line.lstrip(" "))]
        out.extend(textwrap.wrap(
            line, width=width, subsequent_indent=indent + "  ",
            drop_whitespace=True, break_long_words=False,
            break_on_hyphens=False))
    return "\n".join(out)


def render(name, title, body, width=100):
    """body: a rich Text. Writes <name>.png next to the other images."""
    console = Console(record=True, width=width, file=open(os.devnull, "w"))
    console.print(body)
    svg = os.path.join(SCRATCH, name + ".svg")
    console.save_svg(svg, title=title, theme=HOUSE_THEME)
    patch_terminal_svg(svg)
    png = os.path.join(OUT, name + ".png")
    svg_to_png(svg, png, scale=2)
    return verify(png)


# --------------------------------------------------------------- 1. install --
def cli_install():
    t = Text()
    t.append("$ npm install -g openclaw\n", style="bold " + CYAN)
    t.append("added 296 packages in 29s\n", style=BODY)
    t.append("$ openclaw --version\n", style="bold " + CYAN)
    t.append("OpenClaw 2026.6.34 (5c38f99)", style=BODY)
    return render("cli-install", "getting started", t)


# ----------------------------------------------------------------- 2. setup --
def cli_setup():
    t = Text(soft_wrap(read("setup_output.txt").rstrip("\n")), style=BODY)
    t.highlight_regex(r"(?m)^\$ openclaw setup$", "bold " + CYAN)
    t.highlight_regex(r"~/\.openclaw[^\s]*", CYAN)
    t.highlight_regex(r"openclaw (onboard|configure|channels add)", CYAN)
    t.highlight_regex(r"(?m)^Setup complete[^\n]*$", HEAD)
    return render("cli-setup", "openclaw setup", t)


# ---------------------------------------------------------------- 3. status --
def cli_status():
    lines = read("status.txt").split("\n")
    end = next(i for i, l in enumerate(lines) if l.startswith("└"))
    block = "\n".join(lines[:end + 1])
    width = max(len(l) for l in block.split("\n"))

    t = Text(block, style=BODY)
    t.highlight_regex(BOX_RE, MUTED)
    t.highlight_regex(r"(?m)^OpenClaw status$", "bold " + HEAD)
    t.highlight_regex(r"(?m)^Overview$", "bold " + CYAN)
    t.highlight_regex(r"(Item|Value)", "bold " + HEAD)
    t.highlight_regex(r"(ws|http)://127\.0\.0\.1:18789/?", CYAN)
    t.highlight_regex(r"gpt-5\.6-sol \(272k ctx\)", CYAN)
    t.highlight_regex(r"unreachable \(connect ECONNREFUSED 127\.0\.0\.", CRIMSON)
    t.highlight_regex(r"(?m)^│ {22}│ 1:18789\)", CRIMSON)
    t.highlight_regex(r"(not installed|skipped \(use --deep\))", AMBER)
    return render("cli-status", "openclaw status", t, width=width)


# -------------------------------------------------------- 4. security audit --
def cli_security_audit():
    # Verbatim words, soft-wrapped with a hanging indent so the continuation
    # of an indented finding stays visually attached to it.
    block = soft_wrap(read("security_audit.txt").rstrip("\n"))

    t = Text(block, style=BODY)
    t.highlight_regex(r"(?m)^OpenClaw security audit$", "bold " + HEAD)
    t.highlight_regex(r"(?m)^Summary:[^\n]*$", HEAD)
    t.highlight_regex(r"1 critical", "bold " + CRIMSON)
    t.highlight_regex(r"2 warn", "bold " + AMBER)
    t.highlight_regex(r"1 info", "bold " + CYAN)
    t.highlight_regex(r"(?m)^CRITICAL$", "bold " + CRIMSON)
    t.highlight_regex(r"(?m)^WARN$", "bold " + AMBER)
    t.highlight_regex(r"(?m)^INFO$", "bold " + CYAN)
    t.highlight_regex(r"(?m)^(gateway|summary|tools|hooks)\.[a-z_.]+", "bold " + CYAN)
    t.highlight_regex(r"(?m)^ {2}Fix:", "bold " + HEAD)
    t.highlight_regex(r"openclaw security audit --deep", CYAN)
    return render("cli-security-audit", "openclaw security audit", t)


# ---------------------------------------------------------------- 5. skills --
def _mono_cmap():
    """Codepoints the terminal face can actually draw.

    cairosvg has no font fallback, and no colour-emoji font is installed, so
    the per-skill emoji in `openclaw skills list` would render as tofu and
    knock the columns out of line. Drop exactly the characters the face lacks
    (the emoji) and keep the ones it has (the ✓ / △ status marks).
    """
    from fontTools.ttLib import TTFont
    return set(TTFont(MONO_TTF).getBestCmap())


def strip_unrenderable(s, cmap):
    return "".join(c for c in s if ord(c) in cmap or c == " ")


def cli_skills():
    cmap = _mono_cmap()
    lines = read("skills_list.txt").split("\n")
    header = lines[0]                       # "Skills (16/52 ready)"
    body = [l for l in lines if l.startswith("│")]
    body = [l for l in body if "│ Status" not in l]

    # Rebuild the table without the (unrenderable) colour emoji, so every
    # column still lines up. Content words are untouched.
    def cells(line):
        return [strip_unrenderable(c, cmap).strip()
                for c in line.split("│")[1:-1]]

    rows, count = [], 0
    for line in body:
        c = cells(line)
        if c[1]:                            # a new skill starts here
            if count == 10:
                break
            count += 1
        rows.append(c)

    widths = [max(len(r[i]) for r in rows) for i in range(4)]
    widths[0] = max(widths[0], len("Status"))
    widths[1] = max(widths[1], len("Skill"))
    widths[2] = max(widths[2], len("Description"))
    widths[3] = max(widths[3], len("Source"))

    def rule(l, m, r):
        return l + m.join("─" * (w + 2) for w in widths) + r

    def row(c):
        return "│" + "│".join(
            " " + c[i].ljust(widths[i]) + " " for i in range(4)) + "│"

    out = [header,
           rule("┌", "┬", "┐"),
           row(["Status", "Skill", "Description", "Source"]),
           rule("├", "┼", "┤")]
    out += [row(c) for c in rows]
    out.append(rule("└", "┴", "┘"))
    out.append("")
    out.append("… 52 bundled skills in 2026.6.34")
    block = "\n".join(out)
    width = max(len(l) for l in block.split("\n"))

    t = Text(block, style=BODY)
    t.highlight_regex(BOX_RE, MUTED)
    t.highlight_regex(r"(?m)^Skills \(16/52 ready\)$", "bold " + HEAD)
    t.highlight_regex(r"(Status|Skill|Description|Source)\s+│", "bold " + HEAD)
    t.highlight_regex(r"✓ ready", "bold " + CYAN)
    t.highlight_regex(r"△ needs setup", AMBER)
    t.highlight_regex(r"openclaw-bundled", MUTED)
    t.highlight_regex(r"(?m)^… 52 bundled skills in 2026\.6\.34$", MUTED)
    return render("cli-skills", "openclaw skills list", t, width=width)


ALL = [cli_install, cli_setup, cli_status, cli_security_audit, cli_skills]

if __name__ == "__main__":
    for fn in ALL:
        print(fn.__name__)
        fn()
