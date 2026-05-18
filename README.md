# claude-skills

Personal Claude skills, versioned and shareable.

## Install

Symlink each skill into your local Claude skills directory:

```sh
ln -s "$(pwd)/skills/grill-with-lavish" ~/.claude/skills/grill-with-lavish
```

Or copy if you prefer to pin a version:

```sh
cp -r skills/grill-with-lavish ~/.claude/skills/
```

## Skills

- **`grill-with-html`** — Interview the user one question at a time about a UI/UX or design plan. Each turn produces a versioned self-contained HTML artifact; resolved decisions accumulate in a sidecar markdown file. No daemon, no install, no dependencies — the artifact is a single HTML file the user opens in any browser, and feedback flows through anchor-into-clipboard references and a sidecar `feedback.md`. Composes the grill-me interview methodology, grill-with-docs ADR discipline, and the html-effectiveness copy-export pattern. See [`skills/grill-with-html/SKILL.md`](skills/grill-with-html/SKILL.md).

## Spun off

- **`cocoon`** — moved to its own repo and now ships its skill alongside the published runtime: [vu1n/cocoon](https://github.com/vu1n/cocoon).

## Source tracking

Each skill maintains a `sources.json` listing the upstream skills/projects it learned from, along with a SHA of each upstream's content at absorption time. A weekly GitHub Action ([`check-skill-sources`](.github/workflows/check-skill-sources.yml)) checks each source for drift and:

- Opens a `@claude`-tagged PR that bumps the recorded SHA when a source changes, inviting review of whether the upstream diff is worth absorbing.
- Opens a `@claude`-tagged issue if a source becomes unreachable (moved or removed).

This lets each skill absorb the *thinking* from upstream rather than depending on it at runtime — and stay aware of meaningful upstream evolution without manual polling.
