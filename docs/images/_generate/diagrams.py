"""Box-and-arrow diagrams for docs/images.

Hand-written SVG strings -> cairosvg at scale 2. Authoring space is
1900 x 950; the SVG is emitted at half size so each PNG lands on
1900 x 950 device pixels.

Every label is checked against /root/openclaw_captures/FACTS.md and measured
against its box before it is drawn (svgkit.fit / svgkit.wrap raise on
overflow).
"""

import os

from house import (BODY, CRIMSON, CYAN, HEAD, MONO_STACK, MUTED, OUT, PANEL,
                   STROKE, esc, svg_to_png, text_w, text_w_mono, verify)
from svgkit import H, W, arrow, block, canvas, fit, heading, kicker, line, rrect, txt

SCRATCH = os.path.join(OUT, "_generate", "_svg")
os.makedirs(SCRATCH, exist_ok=True)

BAND_FILL = "#0D1A2B"
BAND_STROKE = "#1B3350"
CHIP_FILL = "#193049"
CHIP_STROKE = "#2B4C6D"


def emit(name, body, w=W, h=H):
    svg = os.path.join(SCRATCH, name + ".svg")
    with open(svg, "w", encoding="utf-8") as fh:
        fh.write(canvas(body, w, h))
    png = os.path.join(OUT, name + ".png")
    svg_to_png(svg, png, scale=2)
    return verify(png)


def mono(x, y, s, size=24, fill=HEAD, bold=False, anchor="start"):
    return ('<text x="%.1f" y="%.1f" font-family="%s" font-size="%.1f" '
            'font-weight="%s" fill="%s" text-anchor="%s">%s</text>'
            % (x, y, MONO_STACK, size, "bold" if bold else "normal",
               fill, anchor, esc(s)))


def lerp_hex(a, b, t):
    a, b = a.lstrip("#"), b.lstrip("#")
    return "#" + "".join(
        "%02X" % round(int(a[i:i + 2], 16) * (1 - t) + int(b[i:i + 2], 16) * t)
        for i in (0, 2, 4))


# =========================================================== 6. architecture ==
CHAT_APPS = ["WhatsApp", "Telegram", "Discord", "Slack",
             "Signal", "iMessage", "Matrix", "Teams"]
GATEWAY_CHIPS = ["Pairing & auth", "Sessions", "Skills",
                 "Cron", "Webhooks", "Control UI"]
GATEWAY_SUB = "self-hosted, loopback by default (ws://127.0.0.1:18789)"
SIDE_BOXES = [(380, "Nodes", "iOS / Android"),
              (514, "MCP servers", "openclaw mcp")]
RUNTIME = [("Agent 'main'", "model + tools"),
           ("Workspace", "AGENTS.md · SOUL.md · memory/"),
           ("Sandbox", "Docker isolation")]


def gateway_architecture():
    s = [heading("How OpenClaw is put together", y=88)]

    # ---- band 1: your chat apps -------------------------------------------
    b1y, b1h = 128, 152
    s.append(rrect(60, b1y, 1780, b1h, 18, BAND_FILL, BAND_STROKE))
    s.append(kicker(88, b1y + 40, "Your chat apps"))
    s.append(txt(1812, b1y + 40, "29 channels", 22, MUTED, anchor="end"))

    px, pw, gap = 88.0, (1724 - 7 * 16) / 8.0, 16
    for app in CHAT_APPS:
        fit(app, 23, pw - 24, True, "chat app pill")
        s.append(rrect(px, b1y + 62, pw, 66, 33, PANEL, STROKE))
        s.append(txt(px + pw / 2, b1y + 62 + 41, app, 23, HEAD, True, "middle"))
        px += pw + gap

    # ---- band 2: the gateway ----------------------------------------------
    b2y, b2h = 376, 260
    gw_w = 1390
    s.append(rrect(60, b2y, gw_w, b2h, 20, PANEL, CYAN, 2.5, 'opacity="0.98"'))
    s.append(txt(96, b2y + 56, "OPENCLAW GATEWAY", 36, HEAD, True))
    fit(GATEWAY_SUB, 24, gw_w - 72, False, "gateway subtitle")
    s.append(txt(96, b2y + 92, GATEWAY_SUB, 24, BODY))

    cw = (1318 - 5 * 14) / 6.0
    cx = 96.0
    for chip in GATEWAY_CHIPS:
        fit(chip, 21, cw - 22, False, "gateway chip")
        s.append(rrect(cx, b2y + 126, cw, 72, 12, CHIP_FILL, CHIP_STROKE, 1.5))
        s.append(txt(cx + cw / 2, b2y + 126 + 44, chip, 21, BODY, False, "middle"))
        cx += cw + 14

    # side boxes hanging off the gateway band
    for sy, title, detail in SIDE_BOXES:
        fit(title, 26, 302, True, "side box title")
        fit(detail, 22, 302, False, "side box detail")
        s.append(line(1450, sy + 59, 1490, sy + 59, CYAN, 2.5))
        s.append(rrect(1490, sy, 350, 118, 16, PANEL, STROKE))
        s.append(txt(1665, sy + 48, title, 26, HEAD, True, "middle"))
        s.append(txt(1665, sy + 80, detail, 22, BODY, False, "middle"))

    # ---- band 3: agent runtime --------------------------------------------
    b3y, b3h = 732, 180
    s.append(rrect(60, b3y, 1780, b3h, 18, BAND_FILL, BAND_STROKE))
    s.append(kicker(88, b3y + 40, "Agent runtime"))

    bw = (1724 - 40) / 3.0
    bx = 88.0
    for title, detail in RUNTIME:
        fit(title, 26, bw - 48, True, "runtime title")
        fit(detail, 22, bw - 48, False, "runtime detail")
        s.append(rrect(bx, b3y + 60, bw, 104, 16, PANEL, STROKE))
        s.append(txt(bx + bw / 2, b3y + 100, title, 26, HEAD, True, "middle"))
        s.append(txt(bx + bw / 2, b3y + 134, detail, 22, BODY, False, "middle"))
        bx += bw + 20

    # ---- the two coupling gaps --------------------------------------------
    for ax in (480, 950, 1420):
        s.append(arrow(ax, 292, ax, 364, CYAN, 3, double=True))
        s.append(arrow(ax, 648, ax, 720, CYAN, 3, double=True))

    return emit("gateway-architecture", "".join(s))


# ======================================================== 7. message lifecycle ==
STEPS = [
    ("Message arrives", "WhatsApp DM"),
    ("Channel plugin", "receives"),
    ("Gateway", "pairing check + session routing"),
    ("Agent turn", "model + skills + workspace"),
    ("Tool calls", "exec gated by approvals / sandbox"),
    ("Reply back", "through the channel"),
]

LANES = [(0, 0, "your chat app", MUTED),
         (1, 2, "Gateway", CYAN),
         (3, 4, "agent runtime", MUTED),
         (5, 5, "your chat app", MUTED)]


def message_lifecycle():
    from svgkit import wrap
    s = [heading("Message lifecycle", "One message, end to end", y=96)]

    gap = 52
    bw = (1780 - 5 * gap) / 6.0
    top, bh = 250, 250
    xs = [60 + i * (bw + gap) for i in range(6)]

    for i, (lead, detail) in enumerate(STEPS):
        x, cx = xs[i], xs[i] + bw / 2
        s.append(rrect(x, top, bw, bh, 18, PANEL, STROKE))
        fit(lead, 25, bw - 40, True, "step %d lead" % (i + 1))
        s.append(txt(cx, top + 96, lead, 25, HEAD, True, "middle"))
        lines = wrap(detail, 22, bw - 40)
        assert len(lines) <= 3, (i, lines)
        s.append(block(cx, top + 142, lines, 22, BODY, lh=32)[0])
        # numbered badge, straddling the top edge
        s.append('<circle cx="%.1f" cy="%d" r="27" fill="%s" stroke="%s" '
                 'stroke-width="3"/>' % (cx, top, "#0B1524", CYAN))
        s.append(txt(cx, top + 10, str(i + 1), 27, CYAN, True, "middle"))
        if i < 5:
            s.append(arrow(x + bw + 10, top + bh / 2,
                           x + bw + gap - 10, top + bh / 2, CYAN, 3))

    # the pairing gate, called out under step 3
    note = "unknown sender → pairing code, not access"
    nw = text_w(note, 26) + 76
    ncx = xs[2] + bw / 2
    s.append(line(ncx, top + bh, ncx, 580, CRIMSON, 2, dash="6 7"))
    s.append(rrect(ncx - nw / 2, 580, nw, 90, 16, "#1C1A22", CRIMSON, 2.5))
    s.append(txt(ncx, 634, note, 26, CRIMSON, True, "middle"))

    # lanes tying the flow back to the architecture
    for a, b, label, colour in LANES:
        x1, x2 = xs[a], xs[b] + bw
        s.append(line(x1, 792, x2, 792, colour, 2))
        s.append(line(x1, 780, x1, 792, colour, 2))
        s.append(line(x2, 780, x2, 792, colour, 2))
        s.append(txt((x1 + x2) / 2, 836, label.upper(), 20, colour, True, "middle"))

    return emit("message-lifecycle", "".join(s))


# ========================================================= 8. workspace layout ==
WORKSPACE = [
    ("AGENTS.md", "operating instructions"),
    ("SOUL.md", "persona & boundaries"),
    ("IDENTITY.md", "name, vibe, emoji"),
    ("USER.md", "who you are"),
    ("TOOLS.md", "tool notes"),
    ("HEARTBEAT.md", "periodic check-ins"),
    ("MEMORY.md", "curated long-term"),
    ("memory/", "daily logs (YYYY-MM-DD.md)"),
    ("skills/", "your custom skills"),
]

PRIVATE = [
    ("openclaw.json", "config"),
    ("credentials/", "channel secrets"),
    ("state/openclaw.sqlite", "sessions & tokens"),
]


def _tree(entries, rail_x, text_x, y0, step, right, name_size, desc_size):
    """A file-tree listing: rail + tick per row, name in mono, note in sans."""
    out = []
    ys = [y0 + i * step for i in range(len(entries))]
    out.append(line(rail_x, y0 - 20, rail_x, ys[-1] - 8, STROKE, 2))
    for y, (name, desc) in zip(ys, entries):
        out.append(line(rail_x, y - 8, rail_x + 30, y - 8, STROKE, 2))
        nw = text_w_mono(name, name_size)
        note = "— " + desc
        total = text_x + nw + 16 + text_w(note, desc_size)
        if total > right:
            raise ValueError("tree row %r overflows by %.0fpx" % (name, total - right))
        out.append(mono(text_x, y, name, name_size, HEAD, bold=True))
        out.append(txt(text_x + nw + 16, y, note, desc_size, BODY))
    return "".join(out), ys[-1]


def workspace_layout():
    s = [heading("Where your agent's files live", y=92)]

    # ---- left: the workspace ----------------------------------------------
    s.append(rrect(60, 150, 1040, 740, 20, PANEL, STROKE))
    s.append(mono(100, 208, "~/.openclaw/workspace", 32, CYAN, bold=True))
    s.append(txt(100, 246, "the agent's home — git-initialized on first run",
                 22, MUTED))
    tree, _ = _tree(WORKSPACE, 104, 150, 306, 64, 1060, 26, 24)
    s.append(tree)

    # ---- right: the private state dir (smaller card) ----------------------
    s.append(rrect(1150, 150, 690, 420, 20, PANEL, STROKE))
    s.append(mono(1190, 208, "~/.openclaw", 32, CYAN, bold=True))
    tag = "keep out of git"
    tw = text_w(tag, 18, True) + 30
    tx = 1190 + text_w_mono("~/.openclaw", 32) + 22
    if tx + tw > 1800:
        raise ValueError("keep-out-of-git tag overflows")
    s.append(rrect(tx, 184, tw, 32, 16, "#1C1A22", CRIMSON, 2))
    s.append(txt(tx + tw / 2, 207, tag, 18, CRIMSON, True, "middle"))
    tree, _ = _tree(PRIVATE, 1194, 1240, 312, 90, 1800, 24, 22)
    s.append(tree)

    # ---- the permissions note (bottom-aligned with the workspace card) ----
    s.append(rrect(1150, 730, 690, 160, 18, "#1C1A22", CRIMSON, 2.5))
    s.append(txt(1190, 786, "PERMISSIONS", 20, CRIMSON, True))
    perm = "700 on dirs, 600 on files"
    fit(perm, 30, 610, True, "permissions note")
    s.append(txt(1190, 836, perm, 30, HEAD, True))

    return emit("workspace-layout", "".join(s))


# ======================================================== 9. skills precedence ==
PRECEDENCE = [
    ("<workspace>/skills", ""),
    ("<workspace>/.agents/skills", ""),
    ("~/.agents/skills", ""),
    ("managed", "<state-dir>/skills"),
    ("bundled", "52 ship with OpenClaw"),
    ("plugins & extra dirs", ""),
]


def skills_precedence():
    s = [heading("Skill loading precedence",
                 "where OpenClaw looks for a skill, in order", y=96)]

    n = len(PRECEDENCE)
    top, bottom, gap = 200, 800, 14
    rh = (bottom - top - gap * (n - 1)) / n

    # the "higher wins" rail
    s.append(arrow(145, bottom - 8, 145, top + 8, CYAN, 4, size=13))
    s.append('<text transform="rotate(-90 100 %.1f)" x="100" y="%.1f" '
             'font-family="Helvetica, Arial, sans-serif" font-size="24" '
             'font-weight="bold" fill="%s" text-anchor="middle">%s</text>'
             % ((top + bottom) / 2, (top + bottom) / 2, CYAN,
                esc("same name: higher wins")))

    for i, (path, note) in enumerate(PRECEDENCE):
        y = top + i * (rh + gap)
        shade = lerp_hex(CYAN, MUTED, i / (n - 1))
        s.append(rrect(270, y, 1570, rh, 14, PANEL, STROKE))
        s.append(rrect(270, y, 9, rh, 4, shade, shade, 0))
        cy = y + rh / 2
        s.append('<circle cx="326" cy="%.1f" r="21" fill="none" stroke="%s" '
                 'stroke-width="2.5"/>' % (cy, shade))
        s.append(txt(326, cy + 9, str(i + 1), 24, shade, True, "middle"))

        pw = text_w_mono(path, 27)
        s.append(mono(372, cy + 10, path, 27, HEAD, bold=True))
        if note:
            note_x = 372 + pw + 20
            note_s = "(" + note + ")"
            if note_x + text_w(note_s, 24) > 1560:
                raise ValueError("precedence note overflows: %r" % note_s)
            s.append(txt(note_x, cy + 9, note_s, 24, BODY))
        if i == 0 or i == n - 1:
            tag = "highest" if i == 0 else "lowest"
            tw = text_w(tag, 19, True) + 34
            s.append(rrect(1810 - tw, cy - 18, tw, 36, 18, CHIP_FILL, shade, 1.5))
            s.append(txt(1810 - tw / 2, cy + 7, tag, 19, shade, True, "middle"))

    foot = ("snapshot at session start · ~24 tokens per skill "
            "in the system prompt")
    fw = text_w(foot, 26) + 80
    fx = (270 + 1840) / 2 - fw / 2
    s.append(rrect(fx, 838, fw, 76, 38, CHIP_FILL, CHIP_STROKE, 2))
    s.append(txt(fx + fw / 2, 884, foot, 26, BODY, False, "middle"))

    return emit("skills-precedence", "".join(s))


ALL = [gateway_architecture, message_lifecycle, workspace_layout,
       skills_precedence]

if __name__ == "__main__":
    for fn in ALL:
        print(fn.__name__)
        fn()
