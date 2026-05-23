---
name: grill-with-html
description: Interview the user one question at a time about a UI/UX or design plan. Each turn produces a versioned self-contained HTML artifact; the chat lives in a single sibling markdown file the agent and an optional local server both write to. Use when the user wants to stress-test a visual design (UI flow, layout, copy, state machine, navigation) and seeing the thing being decided matters. For pure-text decisions (terminology, domain modeling, glossary work), pick a text-only grilling approach instead.
---

<what-to-do>

Interview the user relentlessly about every aspect of the plan until you reach a shared understanding. Walk down each branch of the design tree, resolving dependencies between decisions one at a time. For each question, provide your recommended answer.

Ask questions one at a time, waiting for feedback on each before continuing.

If a question can be answered by exploring the codebase, explore it instead.

Each turn produces a new versioned HTML artifact (`turn-NN.html`). The user opens the latest in their browser. Conversation lives in a sidecar `chat.md`. With the optional `grill-server.py` running, the in-page composer posts directly to `chat.md` and the conversation view updates live; without the server, the composer falls back to copy-to-clipboard and the user pastes into `chat.md` themselves.

</what-to-do>

<supporting-info>

## The surface: HTML files + optional local server

Two pieces:

1. **`docs/design/<slug>/turn-NN.html`** — versioned per-turn snapshots of the design surface. Each is self-contained: Tailwind via CDN, no build step, no JS framework. Includes an in-page conversation view, a composer (textarea + Send button), N decision-branch sections with anchor `#` buttons, and a decisions sidebar.
2. **`skills/grill-with-html/server/grill-server.py`** — single-file Python stdlib server that ships with the skill. ~100 lines, zero deps. Run with `python3 server/grill-server.py <design-dir>` to enable live mode. Listens on `127.0.0.1:4388`. Endpoints: `GET /healthz`, `GET /chat.md`, `GET /decisions.md`, `POST /reply`, static file serving from the design dir.

**Live mode (server running):**
- User opens `http://127.0.0.1:4388/turn-NN.html`
- Browser detects server via `/healthz`, switches Send to POST mode
- User types in composer, hits Send → POST `/reply` → server appends to `chat.md`
- Conversation view polls `/chat.md` every 2s and re-renders
- Agent reads `chat.md` on next turn

**Static mode (file:// open from disk):**
- User opens `file:///path/to/turn-NN.html`
- Browser detects no server, shows "file:// mode"
- Conversation view renders the baked-in chat snapshot (whatever was current when the agent generated the turn file)
- Send button copies the reply to clipboard; user pastes into `chat.md` under the current turn's `**User**:` block
- Agent reads `chat.md` on next turn

Both modes converge on the same `chat.md`. Kill the server, switch to file://, switch back — nothing is lost.

## When to use this skill

Trigger when the user is grilling a design *that has a visual shape*: UI flows, page layouts, component composition, copy comparisons, state machines, navigation structure, interaction shape.

Do NOT use for:
- Glossary or terminology decisions ("is this a Customer or a User?") — text-only.
- Pure backend or data-model design with no rendered representation.
- Quick one-off clarifications that don't deserve a session.

If unsure whether the decision is visual, ask the user. A grilling session that doesn't earn its artifact is more friction than value.

## Per-design directory layout

```
docs/design/<slug>/
  turn-01.html        # initial scaffold + first question
  turn-02.html        # next round; design surface updated, decisions sidebar grown
  ...
  chat.md             # canonical chat history (agent + user, every turn)
  decisions.md        # resolved decisions, lifecycle-tagged
```

## The loop

### Turn 1 (start)

1. **Pick a slug** for the design (e.g. `checkout-flow`). Create `docs/design/<slug>/`.
2. **Copy the template** at `skills/grill-with-html/template/turn-01.html` into `docs/design/<slug>/turn-01.html`.
3. **Fill the scaffold**: replace placeholder sections with the design's actual decision branches (e.g. "Entry point", "Listing shape", "Per-row actions", "Empty state"). Keep the anchor `#` button on every section so the user can reference it from the composer.
4. **Create `chat.md`** with `# Chat`, then `## Turn 1`, then `**Agent**` block (your question, recommended answer, alternatives), then `**User**:` line (empty — user will fill).
5. **Create `decisions.md`** with `# Decisions`.
6. **Tell the user how to open the session.** Two options:
   - **Server mode** (recommended for active sessions): `python3 skills/grill-with-html/server/grill-server.py docs/design/<slug>/` then open `http://127.0.0.1:4388/turn-01.html`.
   - **File mode** (for read-only review or quick turns): just `open docs/design/<slug>/turn-01.html`.

### Subsequent turns (N+1)

1. **Read `chat.md`**: process the user's reply under the latest `## Turn N` heading's `**User**:` block.
2. **Resolve decisions**: each clear answer becomes a decision. Append to `decisions.md` (see "decisions.md format" below). Most start as `[draft]`; promote to `[spec]` only when precise enough to implement without further questions.
3. **Copy `turn-N.html` to `turn-(N+1).html`.**
4. **Update content** in the new turn file: revise sections to reflect resolved decisions, add new sub-sections as the design grows, keep anchor buttons on every annotatable element. Update the decisions sidebar to mirror `decisions.md`.
5. **Update `<script id="grill-chat-snapshot">` in the new turn file** to a snapshot of `chat.md`'s current content (so file:// readers see the latest conversation if they open the file without the server running).
6. **Append to `chat.md`**: new `## Turn N+1` heading, `**Agent**` block with your next question, `**User**:` line for the reply.
7. **Tell the user**: "Open `turn-(N+1).html` and reply" — if server is running, the open page will auto-pick up the new question on its next poll; if not, the user opens the new file from disk.

### Ending

When the user signals done:
- Final pass on `decisions.md`: promote any `[draft]` that's actually precise enough to `[spec]`.
- Optionally summarize the session in the final turn's chat or in a closing `## Resolution` section of `decisions.md`.
- Suggest any decisions that earn ADRs (see below).
- Commit the whole design directory; git diff between turn files shows the design's evolution.

## Server: starting, stopping, conventions

- **Start**: `python3 path/to/skills/grill-with-html/server/grill-server.py <design-dir>`. Default port `4388` (override with `--port`).
- **Stop**: Ctrl-C. No background process, no PID files, no global state.
- **Multi-session**: one server per design directory. Different sessions = different ports.
- **What it touches**: only the design directory (writes `chat.md`, reads `chat.md`/`decisions.md`/`turn-NN.html`). Nothing outside.
- **Restart-safe**: server has no in-memory state beyond active HTTP connections. Kill and restart freely.

If the user has the server running, prefer that path — composer Send works without copy-paste. If they're opening from disk, the file:// fallback works fine; just slower per-turn because of the manual paste step.

## `chat.md` format

Each turn block:

```md
## Turn N

**Agent** · `@<branch-name>` · <one-line question summary>

(your question content, recommended answer, alternatives)

**User**:

(empty, or the user's reply)

---
```

Key conventions:
- Each turn starts with `## Turn N` (the H2 heading is the turn boundary the server uses to find the latest user block).
- `**Agent**` line carries the active branch as `` `@<branch>` `` and a one-line summary for the conversation-view rendering.
- `**User**:` is the exact marker the server looks for when appending replies. Don't reword it.
- `---` separator between turns. The server uses this as the user-block-end marker.

The conversation view in `turn-NN.html` parses this format and renders agent/user blocks. If you change the format, update the parser in `template/turn-01.html` too.

## `decisions.md` format

Append-only log of resolved decisions, grouped by branch.

```md
# Decisions

## @entry-point
- [spec] `/sessions` route on the design server, reachable independent of any open artifact
- [draft] chrome header links to it from a small "all sessions" affordance

## @listing-shape
- [draft] card-per-session, sorted by last activity descending
```

Lifecycle tags:
- `[draft]` — rough idea, not yet precise enough to build
- `[spec]` — precise; an implementer could pick this up without further questions
- `[implemented]` — code-backed (you won't write these during grilling)

Don't promote `[draft]` to `[spec]` casually. If the user's answer left wiggle room, it's still `[draft]`. And hold `[draft]` longer than feels comfortable — the meta-grill that designed this skill marked `@surface` as `[spec]` prematurely after Turn 1, then had to demote it in Turn 4 once real UX friction surfaced.

## CONTEXT.md compatibility

If the project already has a `CONTEXT.md` or `CONTEXT-MAP.md`, do not duplicate decisions there. If a sibling skill expects one and none exists, create a minimal stub pointing to the design directory:

```md
# Context

> Canonical design for <slug> lives in [docs/design/<slug>/](docs/design/<slug>/).
> Latest snapshot is the highest-numbered `turn-NN.html`. Chat history is `chat.md`;
> resolved decisions are in `decisions.md`.

## Glossary

(intentionally minimal — see the artifact)
```

## ADRs — sparingly

Only suggest an ADR when all three are true:

1. **Hard to reverse** — changing your mind later has meaningful cost.
2. **Surprising without context** — a future reader will wonder "why did they do it this way?"
3. **Real trade-off** — genuine alternatives existed and one was chosen for specific reasons.

If any is missing, skip the ADR. The decision lives in `decisions.md` and the chat transcript; it doesn't need a separate document.

When you do create an ADR, place it at `docs/adr/<NNNN>-<slug>.md` and link to the design directory.

## Sharpening discipline

During the grill:

- **Challenge fuzzy language.** If the user says "the panel" and two panels exist, ask which by anchor name. Propose canonical names for overloaded terms.
- **Stress-test with concrete scenarios.** "What if the viewport is 320px wide?" "What if there are 50 sessions?" Force precision.
- **Cross-reference with code.** If the user states how something currently works, check the code. Surface contradictions.
- **Recommend an answer per question.** Don't ask open-ended "what should we do?" — propose with reasoning, name alternatives, let the user accept/modify/reject.
- **Resolve dependencies in order.** Entry point first, then listing shape, then per-row affordances — not the other way around.
- **Hold `[draft]` longer than feels comfortable.** The shape of a decision often isn't clear until the user has lived with it for a turn or two.

</supporting-info>

## Sources

This skill absorbed ideas from upstream skills/projects rather than depending on them at runtime. The `sources.json` file in this directory tracks each upstream with the SHA of its content at absorption time. A repo-level GitHub Action checks each source for drift on a weekly cron and opens a `@claude`-tagged PR when meaningful upstream changes appear.

- [`grill-me`](https://github.com/mattpocock/skills/tree/main/skills/productivity/grill-me) — one-question-at-a-time interview methodology.
- [`grill-with-docs`](https://github.com/mattpocock/skills/tree/main/skills/engineering/grill-with-docs) — ADR three-criteria rule, CONTEXT.md compatibility shape, sharpening discipline.
- [`html-effectiveness`](https://github.com/ThariqS/html-effectiveness) — self-contained HTML artifacts as design surfaces; copy-export feedback pattern.
