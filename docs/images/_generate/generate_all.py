#!/usr/bin/env python3
"""Regenerate every PNG in docs/images/ and print the manifest.

    cd docs/images/_generate && python3 generate_all.py

Requires: rich, cairosvg, Pillow, fontTools (pip install cairosvg rich
--break-system-packages if missing) plus the DejaVu and TeX Gyre fonts.

Two pipelines, no matplotlib anywhere:
  * terminal captures - rich Console(record=True) -> save_svg(title=...)
    -> cairosvg @ scale 2. The window chrome is rich's, not ours.
  * diagrams          - hand-written SVG strings -> cairosvg @ scale 2.

Every label is drawn from /root/openclaw_captures/FACTS.md or from the real
captured CLI output in that directory. Nothing here is invented.
"""

import os

import diagrams
import terminal_captures as term
from house import OUT
from PIL import Image

# file -> the exact labels that image contains (checked against FACTS.md)
MANIFEST = [
    ("cli-install.png", [
        "$ npm install -g openclaw",
        "added 296 packages in 29s",
        "$ openclaw --version",
        "OpenClaw 2026.6.34 (5c38f99)",
        'window title: "getting started"',
    ]),
    ("cli-setup.png", [
        "$ openclaw setup",
        "Wrote ~/.openclaw/openclaw.json",
        "Workspace OK: ~/.openclaw/workspace",
        "Sessions OK: ~/.openclaw/agents/main/sessions",
        "Setup complete: config, workspace, and session directories are ready.",
        "Next guided path: openclaw onboard.",
        "Next targeted changes: openclaw configure for models, channels, "
        "Gateway, plugins, skills, and health checks.",
        "Add a chat channel later: openclaw channels add.",
        'window title: "openclaw setup"',
    ]),
    ("cli-status.png", [
        "OpenClaw status", "Overview", "Item", "Value",
        "OS | linux 6.18.44-fc-v22 (x64) · node 22.22.2",
        "Dashboard | http://127.0.0.1:18789/",
        "Tailscale exposure | off", "Channel | stable (default)",
        "Update | npm · deps ok",
        "Gateway | local · ws://127.0.0.1:18789 (local loopback) · "
        "unreachable (connect ECONNREFUSED 127.0.0.1:18789)",
        "Gateway service | systemd user not installed",
        "Node service | systemd user not installed",
        "Agents | 1 · 1 bootstrap file present · sessions 0 · "
        "default main active unknown",
        "Memory | enabled (plugin memory-core) · not checked",
        "Plugin compatibility | none", "Probes | skipped (use --deep)",
        "Events | none", "Tasks | none", "Heartbeat | 30m (main)",
        "Sessions | 0 active · default gpt-5.6-sol (272k ctx) · "
        "~/.openclaw/agents/main/sessions/sessions.json",
        'window title: "openclaw status"',
    ]),
    ("cli-security-audit.png", [
        "OpenClaw security audit",
        "Summary: 1 critical · 2 warn · 1 info",
        "Run deeper: openclaw security audit --deep",
        "CRITICAL", "gateway.loopback_no_auth Gateway auth missing on loopback",
        "WARN", "gateway.trusted_proxies_missing Reverse proxy headers are "
        "not trusted",
        "gateway.http.no_auth Gateway HTTP APIs are reachable without auth",
        "INFO", "summary.attack_surface Attack surface summary",
        "groups: open=0, allowlist=0", "tools.elevated: enabled",
        "hooks.webhooks: disabled", "hooks.internal: disabled",
        "browser control: enabled",
        "trust model: personal assistant (one trusted operator boundary), "
        "not hostile multi-tenant on one shared gateway",
        "(plus the three Fix: lines, verbatim)",
        'window title: "openclaw security audit"',
    ]),
    ("cli-skills.png", [
        "Skills (16/52 ready)", "Status", "Skill", "Description", "Source",
        "1password", "apple-notes", "apple-reminders", "bear-notes",
        "blogwatcher", "blucli", "camsnap", "clawhub", "coding-agent",
        "diagram-maker", "openclaw-bundled", "△ needs setup", "✓ ready",
        "… 52 bundled skills in 2026.6.34",
        'window title: "openclaw skills list"',
    ]),
    ("gateway-architecture.png", (
        ["How OpenClaw is put together", "YOUR CHAT APPS", "29 channels"]
        + diagrams.CHAT_APPS
        + ["OPENCLAW GATEWAY", diagrams.GATEWAY_SUB]
        + diagrams.GATEWAY_CHIPS
        + ["%s — %s" % (t, d) for _, t, d in diagrams.SIDE_BOXES]
        + ["AGENT RUNTIME"]
        + ["%s — %s" % (t, d) for t, d in diagrams.RUNTIME])),
    ("message-lifecycle.png", (
        ["Message lifecycle", "One message, end to end"]
        + ["%d %s — %s" % (i + 1, a, b) for i, (a, b) in enumerate(diagrams.STEPS)]
        + ["unknown sender → pairing code, not access"]
        + ["lane: " + l.upper() for _, _, l, _ in diagrams.LANES])),
    ("workspace-layout.png", (
        ["Where your agent's files live", "~/.openclaw/workspace",
         "the agent's home — git-initialized on first run"]
        + ["%s — %s" % (n, d) for n, d in diagrams.WORKSPACE]
        + ["~/.openclaw", "keep out of git"]
        + ["%s — %s" % (n, d) for n, d in diagrams.PRIVATE]
        + ["PERMISSIONS", "700 on dirs, 600 on files"])),
    ("skills-precedence.png", (
        ["Skill loading precedence",
         "where OpenClaw looks for a skill, in order",
         "same name: higher wins"]
        + ["%d %s%s" % (i + 1, p, (" (" + n + ")") if n else "")
           for i, (p, n) in enumerate(diagrams.PRECEDENCE)]
        + ["highest", "lowest",
           "snapshot at session start · ~24 tokens per skill "
           "in the system prompt"])),
]

# spellings that must appear exactly as written in FACTS.md
SPELLING = ["OpenClaw", "Gateway", "iMessage", "ClawHub", "AGENTS.md",
            "SOUL.md", "HEARTBEAT.md", "ws://127.0.0.1:18789", "2026.6.34"]


def check_spelling():
    """Guard against a near-miss like 'Openclaw' or 'ws://127.0.0.1:18798'."""
    import re
    blob = "\n".join(l for _, labels in MANIFEST for l in labels)
    wrong = {
        r"\bOpenclaw\b|\bopenClaw\b|\bOpen Claw\b": "OpenClaw",
        r"\biMessages\b|\bIMessage\b|\bimessage\b": "iMessage",
        r"\bClawhub\b|\bclawHub\b": "ClawHub",
        r"\bAgents\.md\b|\bagents\.md\b": "AGENTS.md",
        r"\bSoul\.md\b|\bsoul\.md\b": "SOUL.md",
        r"\bHeartbeat\.md\b|\bheartbeat\.md\b": "HEARTBEAT.md",
        r"ws://127\.0\.0\.1:(?!18789)\d+": "ws://127.0.0.1:18789",
        r"\b2026\.6\.(?!34)\d+\b": "2026.6.34",
    }
    for pattern, want in wrong.items():
        hit = re.search(pattern, blob)
        assert not hit, "misspelling %r, expected %r" % (hit.group(0), want)
    print("spelling check: %s -- all clean" % ", ".join(SPELLING))


def main():
    print("== terminal captures (rich -> cairosvg) ==")
    for fn in term.ALL:
        print(fn.__name__)
        fn()
    print("\n== diagrams (hand-written SVG -> cairosvg) ==")
    for fn in diagrams.ALL:
        print(fn.__name__)
        fn()

    print("\n== spelling ==")
    check_spelling()

    print("\n" + "=" * 78)
    print("MANIFEST -- %s" % OUT)
    print("=" * 78)
    for name, labels in MANIFEST:
        path = os.path.join(OUT, name)
        with Image.open(path) as im:
            w, h = im.size
        assert w > 1200, "%s is only %dpx wide" % (name, w)
        kb = os.path.getsize(path) / 1024.0
        print("\n%s  ->  %d x %d px  (%.0f KB)" % (name, w, h, kb))
        for label in labels:
            print("      · %s" % label)
    print("\n%d images, all wider than 1200px." % len(MANIFEST))


if __name__ == "__main__":
    main()
