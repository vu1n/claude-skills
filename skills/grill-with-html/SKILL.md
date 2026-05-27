---
name: grill-with-html
description: Interview the user one question at a time about a UI/UX or design plan. The artifact is a single living `design.html` that holds the design surface, the conversation, the decisions, and any inline annotations — all as semantic HTML elements the agent and the user both edit. A bundled localhost server (`grill-server.py`, Python stdlib, no install) syncs browser writes back into the file. Use when the user wants to stress-test a visual design (UI flow, layout, copy, state machine, navigation) and seeing the thing being decided matters. Not for pure-text decisions.
---

<what-to-do>

Interview the user relentlessly about every aspect of the plan until you reach a shared understanding. Walk down each branch of the design tree, resolving dependencies one at a time. For each question, provide your recommended answer with alternatives named.

Ask questions one at a time, waiting for feedback on each before continuing.

If a question can be answered by exploring the codebase, explore it instead.

The framework is one HTML file. Your job is to use that framework — fill `<section data-design-surface>` with whatever HTML best visualizes the thing being grilled (layouts, flows, forms, SVG diagrams, copy comparisons), wrap any phrase the conversation references in `<mark id="m1">`, append your questions as `<article data-from="agent">` inside `<section data-chat>`, and record resolved decisions as `<article>` inside `<aside data-decisions>`. The HTML file IS the design record AND the conversation AND the decisions log, all in one place.

</what-to-do>

<supporting-info>

## Architecture (one paragraph)

There is one file per design: `docs/design/<slug>/design.html`. It contains the design surface, the conversation, the decisions sidebar, and any inline annotations — every part of the session lives as semantic HTML inside this file. A bundled Python script `skills/grill-with-html/server/grill-server.py` runs as a localhost daemon so the browser can write back to the file (user composer Send, user text-selection annotations). The agent (you) edits the file directly via the filesystem; the server only handles writes initiated by the browser. The file's history is just git — each turn boundary is a commit. No sidecar markdown files, no per-turn HTML snapshots, no separate state stores.

## Per-design directory layout

```
docs/design/<slug>/
  design.html        # the canonical living document — design + chat + decisions + annotations
```

That's it. Git history is the conversation log.

## File structure conventions

The HTML has three semantic regions the agent and server know how to read and write:

```html
<main>
  <section data-design-surface>
    <!-- agent fills this with HTML that visualizes the design.
         Use real elements — <section id="...">, headings, lists,
         tables, forms, SVG. Wrap phrases or regions you want the
         chat to reference in <mark id="m1">phrase</mark>. -->
  </section>

  <section data-chat>
    <!-- conversation grows here. Each turn appends two articles. -->
    <article data-turn="1" data-from="agent" data-branch="@listing">
      <p>Should @listing show full @m1 or just basename?</p>
    </article>
    <article data-turn="1" data-from="user">
      <p>Basename — full path is too long.</p>
    </article>
    <!-- user inline annotations land here too: -->
    <aside id="a1" data-comment-target="m1" data-from="user">
      <p>this part is interesting</p>
    </aside>
  </section>
</main>

<aside data-decisions>
  <!-- decisions accumulate here as the grill resolves them. -->
  <article data-decision="d1">
    <h3>@listing</h3>
    <p data-status="spec">show basename only, never full path</p>
  </article>
</aside>
```

Conventions:
- **Anchors** (`@<id>`) are how everything references everything. Type `@m1` in a chat article and the renderer auto-links it to `<mark id="m1">`. Same syntax for decision branches: `@listing`, `@empty-state`, etc.
- **Marks** wrap phrases or regions the agent wants the chat to reference. Add them when generating the design surface; reuse the ids across turns. The next available numeric id is determined by scanning existing `id="mN"` attributes.
- **Articles** in `<section data-chat>` are the conversation. `data-from="agent"` or `data-from="user"`. `data-turn="N"` is optional but recommended. `data-branch="@foo"` carries the active decision branch.
- **Asides** with `data-comment-target` are user annotations. The target id points at the `<mark>` the comment is attached to.

## The server (`grill-server.py`)

Bundled at `skills/grill-with-html/server/grill-server.py`. Stdlib Python only — no install, no deps, no global config mutation. Run:

```sh
python3 path/to/skills/grill-with-html/server/grill-server.py docs/design/<slug>/
# then open http://127.0.0.1:4388/design.html
```

What it does:
- Serves `design.html` and reloads happen via 2s polling in the page.
- Accepts `POST /reply` from the browser's composer Send — appends `<article data-from="user">` to `<section data-chat>`.
- Accepts `POST /annotation` from the browser's text-selection prompt — wraps the selected text in `<mark>` with a paired `<aside>` comment in the chat section.
- Exposes scoped read endpoints for agents that want context without re-reading the whole file:

```
GET /healthz               liveness
GET /design.html           full file
GET /chat/latest-reply     plain-text of most recent <article data-from="user">
GET /chat/recent?turns=N   last N turns of chat (article elements only)
GET /design                <section data-design-surface> contents
GET /decisions             <aside data-decisions> contents
GET /annotations/pending   <aside> annotations the agent has not responded to yet
```

You can read the full file with the `Read` tool too — the scoped endpoints exist so a long session does not blow your context budget. For session length under ~10 turns, reading the whole file is fine; for longer sessions, prefer the scoped endpoints.

What the server does NOT do:
- Manage agent state. The agent owns the file; server writes only what the browser sends.
- Install anything globally, mutate `~/.claude/`, install hooks. None of that.
- Persist anything beyond the file itself.

## When to use this skill

Trigger when the user wants to grill a design *that has a visual shape*: UI flows, page layouts, component composition, copy comparisons, state machines, navigation, interaction shape.

Do NOT use for:
- Glossary or terminology decisions ("is this a Customer or a User?") — text-only.
- Pure backend or data-model design with no rendered representation.
- Quick one-off clarifications that don't deserve a session.

If unsure whether the decision is visual, ask the user.

## The loop

### Turn 1 (start)

1. **Pick a slug** for the design. Create `docs/design/<slug>/`.
2. **Copy the template**: `cp skills/grill-with-html/template/design.html docs/design/<slug>/design.html`.
3. **Fill the design surface**: replace the `<section id="placeholder">` block with real HTML that visualizes the thing being grilled. Use whichever elements help most — sections, forms, tables, lists, SVG. Give each meaningful region a stable `id`. Wrap phrases the chat will reference in `<mark id="m1">…</mark>`.
4. **Set the title**: update `<h1 data-grill-title>` and the framing `<p>` in the header.
5. **Append the first question** to `<section data-chat>` as `<article data-turn="1" data-from="agent" data-branch="@<branch>">`. Inside: your question text (use `@<id>` to reference marks), recommended answer with reasoning, and named alternatives.
6. **Start the server** (in the background of your conversation):
   ```sh
   python3 skills/grill-with-html/server/grill-server.py docs/design/<slug>/
   ```
   Tell the user to open `http://127.0.0.1:4388/design.html`.

### Subsequent turns (N+1)

1. **Read the latest user reply.** Either `GET /chat/latest-reply` for just the text, or use the `Read` tool on the file directly for full context.
2. **Read any pending annotations.** `GET /annotations/pending` returns user `<aside>` blocks whose `data-comment-target` mark hasn't been responded to by you yet.
3. **Resolve decisions.** Each clear answer becomes a decision. Append `<article>` to `<aside data-decisions>` with the branch as `<h3>@<branch>` and the resolution as `<p data-status="draft|spec">…</p>`. Promote `draft` to `spec` only when precise enough to implement without further questions.
4. **Update the design surface** to reflect resolved decisions. Add new `<mark>` elements for phrases the next question will reference.
5. **Append the next question** as a new `<article data-turn="N+1" data-from="agent" data-branch="@<branch>">` to `<section data-chat>`.
6. **Reply to any annotations** by appending `<aside data-comment-target="m<id>" data-from="agent">` with your response to the user's annotation. This marks the annotation as answered (removes it from `/annotations/pending`).
7. **Commit** the design.html change to git. One commit per turn means `git log --oneline docs/design/<slug>/design.html` is the turn-by-turn history.
8. The user's browser polls every 2s and picks up your changes — no need to tell them to refresh.

### Ending

When the user signals done:
- Final pass on decisions: promote `draft` to `spec` where they're precise enough.
- Optionally add a summary `<section data-summary>` at the bottom of the design surface.
- Suggest any decisions that earn ADRs (see below).
- Stop the server (Ctrl-C). The file remains; it's the durable record.

## Drawing the design surface

This is the part the framework can't prescribe. The agent's job is to use HTML expressively to visualize the thing being designed. Examples by domain:

- **Page layouts** — `<section>`s with Tailwind classes representing each region (header, sidebar, main, footer). The visual hierarchy lives in the HTML structure + Tailwind grid/flex utilities.
- **Forms** — actual `<form>` with `<input>`, `<label>`, `<fieldset>`. Real form semantics let the user see how it'd actually behave.
- **Flows** — ordered `<ol>` with each step as an `<li>`, or `<section>`s connected by `<svg>` arrows for visual flow diagrams.
- **State machines** — `<svg>` with states as `<circle>` + `<text>` and transitions as `<path>` + arrows.
- **Copy comparisons** — side-by-side `<div>`s with the variants, marks on the disputed phrases.
- **Data structures** — `<table>` showing example rows, or nested `<dl>` for hierarchical models.
- **Component variants** — multiple instances of the component, each in its own `<section id="variant-N">` for direct reference.

Tailwind via CDN is already loaded — use utility classes freely. Don't pull in additional frameworks (React, etc.); the artifact must remain a single-file living document.

## ADRs — sparingly

Only suggest an ADR when all three are true:

1. Hard to reverse — changing your mind later has meaningful cost.
2. Surprising without context — a future reader will wonder "why did they do it this way?"
3. Real trade-off — genuine alternatives existed and one was chosen for specific reasons.

If any is missing, skip the ADR. The decision lives in `<aside data-decisions>` and the chat transcript; it doesn't need a separate document.

When you do create an ADR, place it at `docs/adr/<NNNN>-<slug>.md` and link back to the design directory.

## Sharpening discipline

- **Challenge fuzzy language.** If the user says "the panel" and two regions exist, ask which by anchor name. Propose canonical names for overloaded terms.
- **Stress-test with concrete scenarios.** "What if the viewport is 320px wide?" "What if there are 50 sessions?" Force precision.
- **Cross-reference with code.** If the user states how something currently works, check the code. Surface contradictions.
- **Recommend an answer per question.** Don't ask open-ended "what should we do?" — propose with reasoning, name alternatives, let the user accept/modify/reject.
- **Resolve dependencies in order.** Entry point first, then listing shape, then per-row affordances — not the other way around.
- **Hold `draft` longer than feels comfortable.** Decisions often shift once the user has lived with a turn or two. Don't commit `spec` after one round.

</supporting-info>

## Sources

This skill absorbed ideas from upstream skills/projects rather than depending on them at runtime. The `sources.json` file in this directory tracks each upstream with the SHA of its content at absorption time. A repo-level GitHub Action checks each source for drift and opens a `@claude`-tagged PR when meaningful upstream changes appear.

- [`grill-me`](https://github.com/mattpocock/skills/tree/main/skills/productivity/grill-me) — one-question-at-a-time interview methodology.
- [`grill-with-docs`](https://github.com/mattpocock/skills/tree/main/skills/engineering/grill-with-docs) — ADR three-criteria rule, CONTEXT.md compatibility shape, sharpening discipline.
- [`html-effectiveness`](https://github.com/ThariqS/html-effectiveness) — self-contained HTML artifacts as design surfaces.
- [`roughdraft`](https://github.com/Lex-Inc/roughdraft) — inline-annotations-in-the-source-file pattern (CriticMarkup for markdown; adapted here as semantic-HTML-elements-in-the-design-file).
