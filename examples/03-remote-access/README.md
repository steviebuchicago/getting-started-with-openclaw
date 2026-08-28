# Example 3 — Using it away from your desk

**You do not need to expose the Gateway to reach your assistant from a train.**

This is the shortest guide in the repo because the correct answer is short: keep the Gateway on loopback, and get to it through something that already handles identity. Everything below is an alternative to widening `gateway.bind`, which is the change you should be most reluctant to make.

---

## The rule

`openclaw status` has a row for this — **Tailscale exposure**, which reads `off` on a fresh install. The Gateway binds `ws://127.0.0.1:18789` and the Control UI sits on the same port. That's the safe default and the one worth defending.

**Every option below leaves `bind: "loopback"` alone.** If a remote-access approach requires you to change it, you've picked the wrong approach.

---

## Option 1 — Nodes (the phone in your pocket)

The intended answer, and the one most people should stop at. OpenClaw has iOS and Android companion clients — nodes — that pair with your Gateway and bring their own capabilities, camera and voice among them.

```bash
openclaw qr        # generate the mobile pairing QR / setup code
openclaw nodes     # pair nodes and run node-host commands through the Gateway
openclaw devices    # device pairing + token management
```

Scan, pair, done. The Gateway stays on loopback; the node connects to it rather than the other way around.

If pairing fails, there's a bundled skill for exactly this: `node-connect` diagnoses Android, iOS and macOS node pairing — QR/setup code, route, auth and connection failures. Ask your agent to run it before you start editing config.

---

## Option 2 — Your chat app

Worth stating because it gets forgotten while people are busy solving the harder problem: **OpenClaw's whole design is that you talk to it through chat apps you already use.** WhatsApp or Telegram on your phone is remote access. It has been the entire time. No ports, no VPN, no reverse proxy.

The Gateway makes those connections outbound. There is nothing to expose.

---

## Option 3 — Tailscale, when you need the Control UI itself

Sometimes you genuinely want the Control UI from elsewhere. The documented preference is a **Tailscale Serve** pattern: your machines join a private tailnet, Tailscale handles identity and encryption, and the Gateway keeps listening only on loopback while Tailscale brokers the connection.

OpenClaw ships helpers for the discovery side:

```bash
openclaw dns --help    # DNS helpers for wide-area discovery (Tailscale + CoreDNS)
```

For the exact `tailscale serve` invocation, use Tailscale's own documentation and `openclaw docs tailscale` — the flags belong to Tailscale, they change, and you should not copy them from a repo README, this one included.

**The property that makes this the recommended pattern:** authentication happens before anything reaches OpenClaw. You're not relying on the Gateway to be the thing that says no.

---

## What not to do

**Don't port-forward 18789.** Not to your LAN, not to the internet. Remember what the audit says about a fresh install: `gateway.auth.mode="none"` leaves `/tools/invoke` callable without a shared secret. Forwarding that port publishes a tool-invocation endpoint with your credentials behind it.

**Don't bind to `0.0.0.0` because it was easier.** LAN and custom binds need auth *and* a firewall, both, and now you own that configuration forever. "It's only my home network" includes every device on your home network.

**Don't put it behind a reverse proxy without doing both halves.** Set `gateway.auth` to token *and* set `gateway.trustedProxies` to your proxy's IPs. The audit warns about these separately for a reason: a proxy makes remote requests look local, and with `trustedProxies` empty the "is this client local?" check can be spoofed. Auth without trusted proxies, or trusted proxies without auth, is half a control.

**Don't skip TLS pinning on `wss`.** If you're connecting over `wss` to something you control, pin the TLS fingerprint. It's the difference between encrypted and encrypted-to-the-right-machine.

---

## The check

Whatever you set up, verify it rather than assuming:

```bash
openclaw security audit --deep    # probes the live Gateway
openclaw status                   # confirm the Tailscale exposure row says what you expect
```

**If you can reach the Control UI from a network you didn't intend, so can something else.** Test from a device that isn't on your tailnet — the negative result is the one worth having.

---

**Next:** back to [`../02-hardened-config/`](../02-hardened-config/) for the config this assumes, or [`../../docs/04-security-hardening.md`](../../docs/04-security-hardening.md) for the full threat model.
