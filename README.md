# claude-skills

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

- **`grill-with-html`** — Interview the user one question at a time about a UI/UX or design plan. Each turn produces a versioned self-contained HTML artifact; resolved decisions accumulate in a sidecar markdown file. No daemon, no install, no dependencies — the artifact is a single HTML file the user opens in any browser, and feedback flows through anchor-into-clipboard references and a sidecar `feedback.md`. Composes the grill-me interview methodology, grill-with-docs ADR discipline, and the html-effectiveness copy-export pattern. See [`skills/grill-with-html/SKILL.md`](skills/grill-with-html/SKILL.md).

## Using `grill-with-html`

After installing the skill, trigger it by asking your agent to grill you on a visual design:

> Grill me on the session-resume UI I'm thinking about.

The agent picks a slug, scaffolds `docs/design/<slug>/turn-01.html` from the skill's `template/`, asks its first question (with a recommended answer and named alternatives), and the loop begins.

Replying:

- **Simple answers** — type your response in the terminal. The agent processes and produces `turn-02.html`.
- **Precise feedback** — open `docs/design/<slug>/turn-NN.html` in any browser. Click the `#` next to any section heading to copy a `> @<anchor>:` reference to your clipboard, paste into the sibling `feedback.md` under the latest `## Turn N` heading, and write your comment after. The agent reads `feedback.md` on the next turn.

Each turn produces a new versioned snapshot. Open the highest-numbered `turn-NN.html` for the latest design state and the embedded transcript. End the session by telling the agent you're done — resolved decisions live in `decisions.md`, the design's evolution lives in the diffs between turn files. Commit the whole directory; the design process is in git.

## Spun off

- **`cocoon`** — moved to its own repo and now ships its skill alongside the published runtime: [vu1n/cocoon](https://github.com/vu1n/cocoon).

## Source tracking

Each skill maintains a `sources.json` listing the upstream skills/projects it learned from, along with a SHA of each upstream's content at absorption time. A weekly GitHub Action ([`check-skill-sources`](.github/workflows/check-skill-sources.yml)) checks each source for drift and:

- Opens a `@claude`-tagged PR that bumps the recorded SHA when a source changes, inviting review of whether the upstream diff is worth absorbing.
- Opens a `@claude`-tagged issue if a source becomes unreachable (moved or removed).

This lets each skill absorb the *thinking* from upstream rather than depending on it at runtime — and stay aware of meaningful upstream evolution without manual polling.
