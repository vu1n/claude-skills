# agent-skills

Personal agent skills, versioned and shareable. Format works with Claude Code, Codex, and any other host that consumes `SKILL.md` files.

## Install

Symlink the skill you want into your agent's skills directory. For Claude Code:

```sh
ln -s "$(pwd)/skills/grill-with-html" ~/.claude/skills/grill-with-html
```

For Codex, swap the destination for `~/.codex/skills/` (or wherever your host reads skills from). Copy if you want to pin a version instead of tracking this repo:

```sh
cp -r skills/grill-with-html ~/.claude/skills/
```

## Skills

- **`grill-with-html`** — Interview the user one question at a time about a UI/UX or design plan. One living `design.html` file holds the design surface, the conversation (as `<article>` elements), the decisions sidebar, and any user annotations (as `<mark>` + paired `<aside>` comments) — all inline as semantic HTML. A bundled stdlib Python server (`grill-server.py`, no install) lets the browser write back to the file when the user replies or annotates; the agent edits the file directly. Per-turn history is just git. Composes grill-me (interview methodology), grill-with-docs (ADR discipline), html-effectiveness (single-file artifact ethos), and roughdraft (inline-annotations-in-the-source-file). See [`skills/grill-with-html/SKILL.md`](skills/grill-with-html/SKILL.md).

## Using `grill-with-html`

After installing the skill, trigger it by asking your agent to grill you on a visual design:

> Grill me on the session-resume UI I'm thinking about.

The agent picks a slug, copies the template to `docs/design/<slug>/design.html`, fills the design surface with HTML that visualizes the thing being grilled, appends its first question to `<section data-chat>`, then starts the server:

```sh
python3 skills/grill-with-html/server/grill-server.py docs/design/<slug>/
# open http://127.0.0.1:4388/design.html
```

In the browser:
- Read the agent's question in the Conversation section. Anchor references like `@m1` are clickable — they scroll to and flash the marked region in the design surface.
- Type your reply in the composer at the bottom. Hit Send; the conversation view updates within ~2s.
- Select any text in the design surface to open an inline annotation prompt. Write a comment, hit Save; the selection gets wrapped in a `<mark>` and your comment appears as an `<aside>` in the conversation.

The agent edits `design.html` directly; the server's job is to handle browser-initiated writes. Per-turn history is just git — `git log --oneline docs/design/<slug>/design.html` is the turn-by-turn record. Open `design.html` in any browser without the server too — chat and decisions still render (server only adds live writes).

## Spun off

- **`cocoon`** — moved to its own repo and now ships its skill alongside the published runtime: [vu1n/cocoon](https://github.com/vu1n/cocoon).

## Source tracking

Each skill maintains a `sources.json` listing the upstream skills/projects it learned from, along with a SHA of each upstream's content at absorption time. A weekly GitHub Action ([`check-skill-sources`](.github/workflows/check-skill-sources.yml)) checks each source for drift and:

- Opens a `@claude`-tagged PR that bumps the recorded SHA when a source changes, inviting review of whether the upstream diff is worth absorbing.
- Opens a `@claude`-tagged issue if a source becomes unreachable (moved or removed).

This lets each skill absorb the *thinking* from upstream rather than depending on it at runtime — and stay aware of meaningful upstream evolution without manual polling.
