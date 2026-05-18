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

- **`grill-with-lavish`** — Interview the user one question at a time about a UI/UX or design plan, with each resolved decision visualized live in a Lavish HTML artifact and recorded as an atomic claim. Composes the grill-me interview methodology, grill-with-docs ADR discipline, the facts atomic-claim lifecycle, and Lavish Editor as the surface. See [`skills/grill-with-lavish/SKILL.md`](skills/grill-with-lavish/SKILL.md).
- **`cocoon`** — MCP facade over the [printing-press](https://github.com/mvanhorn/cli-printing-press) CLI corpus: four meta-tools (`find_capability`, `describe_capability`, `call_capability`, `list_apis`) let an agent discover and call any indexed API on demand, with lazy CLI materialization and per-call sandboxed execution. Skill at [`skills/cocoon/SKILL.md`](skills/cocoon/SKILL.md), runtime at [`cocoon/`](cocoon/).

## Source tracking

Each skill maintains a `sources.json` listing the upstream skills/projects it learned from, along with a SHA of each upstream's content at absorption time. A weekly GitHub Action ([`check-skill-sources`](.github/workflows/check-skill-sources.yml)) checks each source for drift and:

- Opens a `@claude`-tagged PR that bumps the recorded SHA when a source changes, inviting review of whether the upstream diff is worth absorbing.
- Opens a `@claude`-tagged issue if a source becomes unreachable (moved or removed).

This lets each skill absorb the *thinking* from upstream rather than depending on it at runtime — and stay aware of meaningful upstream evolution without manual polling.
