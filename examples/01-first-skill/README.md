# Example 1 — Your first custom skill

**A skill is a folder with a `SKILL.md` in it. This is that folder.**

[`morning-brief/SKILL.md`](morning-brief/SKILL.md) is a complete, working custom skill: five lines of morning brief assembled from the weather, today's calendar, and whatever thread you left open yesterday. It's small on purpose — everything in it is a pattern you'll reuse, and nothing in it is filler.

Read the file first. It's about ninety lines of Markdown and it will teach you the format faster than any explanation of the format.

---

## What it does

Three sources, degrading gracefully:

| Line | Source | If unavailable |
| --- | --- | --- |
| Weather | `wttr.in` via `curl`, the same approach the bundled `weather` skill uses | Says so, moves on |
| Calendar | The bundled `gog` skill, if you've set it up | Skips the line entirely |
| Carry-over | The top of `memory/YYYY-MM-DD.md` in your workspace | Skips the line entirely |

**Every source is optional and every failure is silent-but-honest.** A morning brief that refuses to render because the calendar API had a bad night is a worse morning brief than a four-line one. That's the design rule worth taking away — build skills that degrade, not skills that assert.

---

## Where to put it

Copy the folder into your workspace's skills directory:

```bash
cp -r morning-brief ~/.openclaw/workspace/skills/
```

The path is `<workspace>/skills/morning-brief/SKILL.md`. **The folder name and the frontmatter `name:` should match** — the folder is where it lives, the `name` is what you type.

`<workspace>/skills` is the highest-priority location of the six OpenClaw checks, so anything you put here wins over a bundled skill with the same name. Handy for overriding; worth remembering when a skill you installed mysteriously behaves like an older version. Full precedence table in [`../../docs/03-skills.md`](../../docs/03-skills.md).

---

## How it gets picked up

You don't restart anything.

Skills are snapshotted when a session starts, and a watcher refreshes that snapshot when a `SKILL.md` changes — debounced by 250ms, applied on the **next turn**. So the loop is:

1. Save `SKILL.md`
2. Send any message
3. It's there

The one thing that catches people: the change lands on the *next* turn, not the current one. If you edit mid-conversation and immediately ask "do you have a morning-brief skill?", the answer may still be no. Ask twice.

Confirm it registered:

```bash
openclaw skills list          # look for 🌅 morning-brief
openclaw skills inspect morning-brief
```

If it shows `△ needs setup`, the `requires.bins: ["curl"]` gate isn't satisfied — install `curl` and it flips to `✓ ready`.

---

## How to invoke it

```
$morning-brief
```

The `$` prefix forces the skill explicitly. Use it while you're iterating, because it removes the question of whether the model chose to use your skill from the question of whether your skill works.

Once you trust it, just ask — *"what's my morning look like?"*, *"give me the rundown"* — and the model matches on the `description` field. If it doesn't get picked up, the description is what to fix, not the instructions. Descriptions are retrieval bait: they should carry the nouns and phrases a user would actually say.

In the Control UI, typing `$` searches your skills.

---

## Putting it on a schedule

A brief you have to ask for is a worse product than a brief that arrives. OpenClaw's `cron` creates persistent background jobs on the Gateway — which means this only works if the Gateway is installed as a service and the machine stays on.

**Prove the payload before you schedule it.** Run the thing you intend to automate, once, by hand:

```bash
openclaw agent --to +15555550123 --message "\$morning-brief" --deliver
```

That runs one agent turn through the Gateway and delivers the reply. Use `openclaw directory` to look up your own contact ID for the channel you want it delivered to, rather than guessing at the format.

Then schedule it. Cron subcommands and flags differ across builds, so discover them rather than trusting a snippet from the internet — this one included:

```bash
openclaw cron --help
```

You're looking for a subcommand that creates a job, and you'll need to express four things: **when** it runs (weekday mornings, say 07:00), **which agent** runs it, **what** it should do (`$morning-brief`), and **where** the answer goes (your own DM). Inspect what you created with `openclaw cron` and `openclaw tasks`.

One security note, and it's not a footnote: **`cron` creates persistent jobs, so a handler that can reach `cron` can give itself a standing schedule.** That's exactly why the hardened baseline denies `group:automation` for anything untrusted. See [`../02-hardened-config/`](../02-hardened-config/).

---

## Make it yours

Three edits, in the order they pay off:

1. **Change the output block.** Five lines is my taste, not a rule. The output format section is the highest-leverage thing in the file.
2. **Add a source.** A news feed, your task list, an unread count. Keep the degradation rule — if it's down, drop the line.
3. **Tighten the description.** Once it's running, notice the phrasings that *should* have triggered it and didn't, and put those words in.

When you want the agent to draft skills for you, the bundled `skill-creator` skill does that — and `openclaw skills workshop list / inspect / apply` is the review gate where you read the draft before it becomes a capability.

---

**Next:** [`../02-hardened-config/`](../02-hardened-config/) — the secure baseline, annotated line by line. Or back to [`../../docs/03-skills.md`](../../docs/03-skills.md) for the full skills reference.
