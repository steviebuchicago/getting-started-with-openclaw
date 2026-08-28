# Example 2 — The hardened baseline

**A fresh OpenClaw install reports one CRITICAL, two warnings, and an attack-surface summary. This directory is the file that answers them.**

[`openclaw.json5`](openclaw.json5) is a secure starting posture with a comment on every line explaining what it buys you. It is not a finished policy — nobody can write your policy — but it is a defensible place to start, and it's a much better place than the default.

This is the governance chapter of this repo, expressed as configuration rather than prose.

---

## First, run the audit

Before you change anything, look at what you've actually got:

```bash
openclaw security audit
```

On a bare install that comes back **1 critical · 2 warn · 1 info**.

<img src="../../docs/images/cli-security-audit.png" alt="openclaw security audit on a fresh install: 1 critical, 2 warn, 1 info" width="100%">

**CRITICAL — `gateway.loopback_no_auth`.** The Gateway binds loopback, but no auth secret is configured. The audit's own words: *"If the Control UI is exposed through a reverse proxy, unauthenticated access is possible."*

**WARN — `gateway.trusted_proxies_missing`.** `gateway.trustedProxies` is empty. Expose the Control UI through a reverse proxy and the local-client check can be spoofed.

**WARN — `gateway.http.no_auth`.** `gateway.auth.mode="none"` leaves `/tools/invoke` callable without a shared secret.

**INFO — attack surface.** Elevated tools enabled, browser control enabled, webhooks and internal hooks disabled, no open or allowlisted groups. Plus the line that frames everything else:

> trust model: personal assistant (one trusted operator boundary), not hostile multi-tenant on one shared gateway

**Read that sentence twice.** OpenClaw assumes exactly one trusted operator per Gateway. It is not built to keep two users safely apart on one box, and it says so. Every hardening decision below sits inside that assumption — you are defending the perimeter, not partitioning the interior.

Those three findings are one story told three ways: **the Gateway is safe because it's on loopback, and the moment anything sits in front of it, it isn't.** The config in this directory sets the token anyway, so that assumption stops being load-bearing.

---

## Four questions

Every block in `openclaw.json5` answers one of them. If you remember nothing else from this repo, remember the questions — they port to any agent platform.

| Question | Config block | The control |
| --- | --- | --- |
| **Who can reach it?** | `gateway` | `bind: "loopback"`, token auth, empty `trustedProxies` |
| **Who can talk to it?** | `channels`, `session` | `dmPolicy: "pairing"`, `requireMention`, `dmScope` |
| **What can it touch and do?** | `tools`, `browser` | deny-lists, `exec.security: "deny"`, SSRF guard |
| **Who approves?** | `tools.exec.ask`, skills workshop | `ask: "always"`, human review gate |

### Who can reach it

`bind: "loopback"` is the highest-value line in the file. Everything else is defence in depth behind it. Setting `auth.mode: "token"` closes the CRITICAL and means a proxy misconfiguration is no longer a full compromise. `trustedProxies: []` stays empty until you genuinely reverse-proxy — an unnecessary entry there is a spoofing primitive you installed yourself.

If you need it away from your desk, **don't widen the bind**. See [`../03-remote-access/`](../03-remote-access/).

### Who can talk to it

`dmPolicy: "pairing"` is already the default and the config states it explicitly, because defaults drift and explicit beats implicit in a file people copy. Unknown senders get a time-limited code — one hour, three pending maximum per channel — and you approve it with `openclaw pairing`. The alternative, open mode, means anyone who has your number is in conversation with something that can read your files.

`requireMention: true` in groups is the underrated one. An agent that processes every message in every group chat is reading a lot of other people's conversation.

`session.dmScope: "per-channel-peer"` isolates conversation state per person per channel, so context from one contact can't surface in a reply to another.

### What can it touch and do

The deny-list is the blunt instrument and it's the right one to start with:

```json5
deny: ["group:automation", "group:runtime", "group:fs", "sessions_spawn", "sessions_send"]
```

`group:automation` covers scheduling and webhooks — **cron creates persistent jobs, so a handler that can reach cron can grant itself a standing schedule.** That's the capability-escalation path most people don't picture. `sessions_spawn` and `sessions_send` stop an agent writing into sessions that aren't its own.

Two more worth knowing: the `gateway` tool is owner-only because it exposes config and secrets, and `exec.security: "deny"` with `ask: "always"` means shell execution is off, and re-enabled only with a human in the loop on every call.

**On spending:** OpenClaw's config controls *reach* and *capability*, not budget. Cost is bounded indirectly — which model you run, how often the heartbeat fires (30m by default), what tools exist to be looped over. If you want a hard ceiling, that lives with your model provider. Worth knowing before you find out the other way.

### Who approves

`ask: "always"` on exec, and the skills workshop (`openclaw skills workshop list / inspect / apply`) where an agent-drafted skill needs a human to apply it. **Both are the same control: the agent proposes, a person disposes, and there's a record.**

---

## Prompt injection is a model-choice problem too

Treat links, attachments and pasted text as hostile — that's table stakes, and the bundled skills already carry the instruction inline.

But the numbers matter. In a 2026 crowdsourced injection arena, success rates ran around **0.5% against Claude Opus 4.5 and over 8.5% against older and smaller tiers.**

**Your first prompt-injection mitigation is which model you point at the thing.** The gap between those two numbers is not something you can deny-list your way out of. Turn off `web_search` / `web_fetch` / browser control where they aren't needed, and where they are, run a frontier model.

---

## The loop

Hardening isn't a file you write once.

```bash
openclaw security audit          # findings carry structured checkIds
openclaw security audit --fix    # applies safe remediations
# ... edit config, then:
openclaw config validate
openclaw security audit --deep   # probes the live Gateway
```

Fast audit for config; `--deep` when you want it to actually poke the running process. Re-run after every change to the config, every channel you add, and every plugin you install.

Also worth running: the bundled `healthcheck` skill audits the host itself — SSH, firewall, updates, exposure, backups, disk encryption.

**Filesystem hygiene, since config can't do it for you:** `~/.openclaw` holds `credentials/` and `state/openclaw.sqlite` with OAuth tokens in it. Directories `700`, files `600`, full-disk encryption on, and a dedicated OS user if you're being serious.

**If something goes wrong:** stop the Gateway → set bind back to loopback → rotate tokens and channel credentials → review `openclaw logs` and `openclaw transcripts` → re-audit with `--deep`. In that order.

---

## When to loosen it

You will loosen some of this. Most people need `exec` eventually; some need a plugin; a few genuinely need LAN access.

The only rule: **loosening is a decision, not a default.** Write down what you opened, why, and what would make you close it again — a comment in the config file is enough. The failure mode isn't people making the wrong call, it's a config that drifted open across six months of small conveniences and nobody remembering which one mattered.

Open one thing at a time. Re-run the audit after each. If you can't say what a permission is for, that's your answer.

---

**Next:** [`../03-remote-access/`](../03-remote-access/) — using it away from your desk without undoing any of this. Or the full reasoning in [`../../docs/04-security-hardening.md`](../../docs/04-security-hardening.md).
