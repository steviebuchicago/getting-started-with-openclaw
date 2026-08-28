# When it doesn't work

**Most OpenClaw problems are one of four things: the Gateway isn't running, a credential expired, a dependency is missing, or something else already owns port 18789.**

Organised by what you actually see, not by subsystem. Start with `openclaw status` — it answers most of these in one screen.

<img src="images/cli-status.png" alt="openclaw status overview table" width="100%">

---

## "Gateway unreachable · ECONNREFUSED 127.0.0.1:18789"

The most common thing you'll see, and on a fresh install it isn't a fault. **It means the Gateway process isn't running.** Nothing is broken; nothing has started.

```bash
openclaw gateway status      # is it up?
openclaw gateway probe       # test reachability specifically
openclaw gateway run --force # start it, replacing anything on its port
```

`--force` is the right hammer when a previous run didn't exit cleanly, and the wrong one if you haven't checked what's actually listening. If the Gateway works in the foreground and dies with your terminal, you never installed the service — see the next section.

---

## "systemd user not installed" in status

Two rows say this — **Gateway service** and **Node service**. Nothing was registered as a background service, so nothing restarts after a reboot. Expected on a fresh install; a problem the first time you reboot and your assistant is gone.

```bash
openclaw onboard --install-daemon   # systemd user unit on Linux, launchd on macOS
```

Re-run `openclaw status` afterwards and watch those rows change.

---

## Which diagnostic am I supposed to run?

Four commands with overlapping names. They are not interchangeable.

| Command | What it's for |
| --- | --- |
| `openclaw status` | Snapshot: Gateway, channels, models, recent sessions. Start here, always. |
| `openclaw doctor` | Diagnose **and repair** config, Gateway, plugin and channel problems. `--fix` applies repairs. |
| `openclaw health` | Detailed health **from the running Gateway** — needs it to be up. |
| `openclaw crestodian` | Interactive setup and repair assistant, when you'd rather be walked through it. |

Rough order: `status` to see it, `doctor --fix` to repair it, `health` for detail once it's running. Add `--deep` to run the probes fast status skips, or `--all` for the shareable version.

The docs also refer to `openclaw triage` as a guided variant. It isn't in this build's top-level `openclaw --help`, so if it's not on your install, use `doctor` and check the live docs rather than assuming your install is broken.

---

## Reading logs

```bash
openclaw logs --follow            # watch it live
openclaw --log-level debug <cmd>  # when the default is too quiet
```

`--follow` in one pane while you reproduce the problem in another is the fastest loop for anything channel- or plugin-shaped. For a past run, `openclaw transcripts` and `openclaw sessions` hold stored conversation state.

---

## A channel stopped working

Channel logins expire, get revoked, or get invalidated when you sign in somewhere else. Symptom: everything looks healthy, messages don't arrive.

```bash
openclaw channels status   # connected accounts and login state
openclaw channels add      # re-run guided setup / re-login
openclaw pairing           # approve inbound DM requests
```

If DMs from someone *new* go nowhere, that's usually not a fault — pairing is the default, and unknown senders get a time-limited code (one hour, max three pending per channel) that you approve.

---

## Model auth failures

**Check the provider before debugging anything model-shaped** — an expired key surfaces as vague failure several layers from the actual cause. `openclaw models status` reports provider auth health, and `openclaw status` shows the session default, `gpt-5.6-sol` (272k ctx) on this build.

---

## Skills showing "needs setup"

On a bare box, `openclaw skills list` reports 16 of 52 ready. **That is not breakage — it's the gating system doing its job.**

A skill declares `requires.bins`, `requires.env`, `requires.config` and an `os` filter. When a dependency is missing it marks itself `△ needs setup` and stays out of the model's way instead of failing halfway through a task. Run `openclaw skills inspect <name>` to see what it's waiting on.

The fix is almost always: install the binary, set the environment variable, or accept that a macOS-only skill won't run on Linux. Full detail in [`03-skills.md`](03-skills.md).

---

## Port 18789 already in use

The Gateway WebSocket and the Control UI share `127.0.0.1:18789`. Two things want it and only one gets it — usually an older Gateway that didn't shut down. `openclaw gateway run --force` takes the port back.

If you genuinely need two instances, don't fight over the port — isolate:

```bash
openclaw --dev <command>              # state in ~/.openclaw-dev, gateway on 19001
openclaw --profile work <command>     # state + config under ~/.openclaw-work
```

Both isolate `OPENCLAW_STATE_DIR` / `OPENCLAW_CONFIG_PATH`, and `--dev` also shifts the derived browser and canvas ports.

---

## Resetting, safely

**Back up first. Always.** `openclaw backup` creates and verifies a local archive of your state. Then pick your blast radius:

| Command | What it removes | What survives |
| --- | --- | --- |
| `openclaw reset` | Local config and state | The CLI |
| `openclaw uninstall` | Gateway service **and** local data | The CLI |

`reset` is the "start the configuration over" button. `uninstall` takes your data with it — including the workspace your agent has been writing to. That workspace is git-initialized, so if you've been committing, its history is the thing worth rescuing before you run either.

---

## Updating

`openclaw update` updates and reports your channel status. `openclaw status` shows which channel you're on — `stable (default)` unless you moved it. Stable is what npm gives you and it's the right default for a process holding your message accounts. A beta channel lands new capability first, along with the new bugs; moving to it is a decision about the box your assistant lives on, so make it deliberately.

---

## When the answer isn't here

The CLI searches the real documentation, which beats guessing at a flag:

```bash
openclaw docs <search terms>
openclaw <command> --help      # commands marked * in help have subcommands
openclaw crestodian            # interactive setup and repair assistant
```

Live references: [docs.openclaw.ai/faq](https://docs.openclaw.ai/faq) · [docs.openclaw.ai/troubleshooting](https://docs.openclaw.ai/troubleshooting) · [docs.openclaw.ai/cli](https://docs.openclaw.ai/cli)

And if what's failing is a security finding rather than a crash — a CRITICAL from `openclaw security audit`, an exposed Control UI — that isn't a troubleshooting problem, it's a configuration decision. See [`04-security-hardening.md`](04-security-hardening.md) and [`../examples/02-hardened-config/`](../examples/02-hardened-config/).

---

**Next:** back to the [README](../README.md), and the working code in [`../examples/`](../examples/) — a custom skill, a hardened config, and remote access without exposing the Gateway.
