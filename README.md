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

- **`grill-with-html`** — Interview the user one question at a time about a UI/UX or design plan. Each turn produces a versioned self-contained HTML artifact (`turn-NN.html`); chat history lives in a single sibling `chat.md`. Optional one-file Python server (`grill-server.py`, stdlib only, no install) gives the in-page composer live bidirectional chat; without the server, file:// mode still works via copy-to-clipboard fallback. Composes the grill-me interview methodology, grill-with-docs ADR discipline, and the html-effectiveness self-contained-artifact pattern. See [`skills/grill-with-html/SKILL.md`](skills/grill-with-html/SKILL.md).

## Using `grill-with-html`

After installing the skill, trigger it by asking your agent to grill you on a visual design:

> Grill me on the session-resume UI I'm thinking about.

The agent picks a slug, scaffolds `docs/design/<slug>/turn-01.html` from the skill's `template/`, writes the first question into `chat.md`, and the loop begins.

Two ways to open the session:

- **Live mode** (recommended for active grilling):
  ```sh
  python3 skills/grill-with-html/server/grill-server.py docs/design/<slug>/
  # then open http://127.0.0.1:4388/turn-01.html
  ```
  Composer Send posts directly; conversation view polls `chat.md` every 2s; no copy/paste round-trip.
- **File mode** (read-only review, or if you don't want to start the server):
  ```sh
  open docs/design/<slug>/turn-01.html
  ```
  Composer Send falls back to copy-to-clipboard; you paste into `chat.md` under the current turn's `**User**:` block, then tell the agent.

Each turn produces a new versioned snapshot. Open the highest-numbered `turn-NN.html` for the latest design state. Click `#` next to any section heading to insert an anchor reference (`> @<id>:`) into the composer for precision when referencing parts of the artifact. End the session by telling the agent you're done — resolved decisions live in `decisions.md`, chat history in `chat.md`, the design's evolution in the diffs between turn files. Commit the whole directory; the design process is in git.

## Spun off

- **`cocoon`** — moved to its own repo and now ships its skill alongside the published runtime: [vu1n/cocoon](https://github.com/vu1n/cocoon).

## Source tracking

Each skill maintains a `sources.json` listing the upstream skills/projects it learned from, along with a SHA of each upstream's content at absorption time. A weekly GitHub Action ([`check-skill-sources`](.github/workflows/check-skill-sources.yml)) checks each source for drift and:

- Opens a `@claude`-tagged PR that bumps the recorded SHA when a source changes, inviting review of whether the upstream diff is worth absorbing.
- Opens a `@claude`-tagged issue if a source becomes unreachable (moved or removed).

This lets each skill absorb the *thinking* from upstream rather than depending on it at runtime — and stay aware of meaningful upstream evolution without manual polling.
