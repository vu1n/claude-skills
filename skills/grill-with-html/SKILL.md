---
name: grill-with-html
description: Interview the user one question at a time about a UI/UX or design plan. Each turn produces a versioned self-contained HTML artifact; resolved decisions accumulate in a sidecar markdown file. Use when the user wants to stress-test a visual design (UI flow, layout, copy, state machine, navigation) and seeing the thing being decided matters. For pure-text decisions (terminology, domain modeling, glossary work), pick a text-only grilling approach instead.
---

<what-to-do>

Interview the user relentlessly about every aspect of the plan until you reach a shared understanding. Walk down each branch of the design tree, resolving dependencies between decisions one at a time. For each question, provide your recommended answer.

Ask questions one at a time, waiting for feedback on each before continuing.

If a question can be answered by exploring the codebase, explore it instead.

Each turn produces a new versioned HTML artifact (`turn-NN.html`). The user opens the latest, reads your question from the embedded transcript, and replies — either directly in the terminal for simple answers, or in a sidecar `feedback.md` file when they want to write richer notes referencing specific parts of the artifact.

</what-to-do>

<supporting-info>

## The surface: per-turn HTML + sidecar markdown

There is no daemon, no install, no dependency. The artifact is a single self-contained HTML file the user opens with their default browser. Tailwind ships via CDN in the file itself; no build step. Versioning is per-turn: each round of grilling produces a new `turn-NN.html` snapshot, so the design's evolution is the diff between turns.

Per-design directory layout:

```
docs/design/<slug>/
  turn-01.html        # initial scaffold + first question (embedded transcript)
  turn-02.html        # next round; content updated, decisions added, transcript grown
  turn-03.html
  ...
  feedback.md         # single file, append-only; user writes per-turn responses under "## Turn N" headings
  decisions.md        # agent appends resolved decisions (lifecycle-tagged)
```

The user opens the highest-numbered `turn-NN.html` to see the current state. Each turn file is a complete snapshot: embedded transcript covers turns 1..N, decisions sidebar shows everything resolved through N, content sections reflect the current state of the design.

## When to use this skill

Trigger when the user is grilling a design *that has a visual shape*: UI flows, page layouts, component composition, copy comparisons, state machines, navigation structure, interaction shape.

Do NOT use for:
- Glossary or terminology decisions ("is this a Customer or a User?") — text-only.
- Pure backend or data-model design with no rendered representation.
- Quick one-off clarifications that don't deserve a session.

If unsure whether the decision is visual, ask the user. A grilling session that doesn't earn its artifact is more friction than value.

## The loop

### Turn 1 (start)

1. **Pick a slug** for the design (e.g. `checkout-flow`). Create `docs/design/<slug>/`.
2. **Copy the template** at `template/turn-01.html` from this skill directory to `docs/design/<slug>/turn-01.html`.
3. **Fill the scaffold**: rename the placeholder sections to match the design's actual decision branches (e.g. "Entry point", "Listing shape", "Per-row actions", "Empty state"). Each section heading must keep its anchor button (the `#` next to the heading) — these are the precision references the user will use in feedback.
4. **Write the first question** into the embedded transcript section at the bottom of the HTML, with your recommended answer and 1-2 sentences of reasoning. Name the alternatives you considered.
5. **Create `feedback.md`** with an initial `# Feedback` heading and a `## Turn 1` heading underneath. The user writes under `## Turn 1`.
6. **Create `decisions.md`** with an initial `# Decisions` heading. Empty list to start.
7. **Tell the user**: "Open `docs/design/<slug>/turn-01.html` and reply in the terminal, or write notes under `## Turn 1` in `feedback.md` if precision matters."

### Subsequent turns (N+1)

1. **Read `feedback.md`**: process the section under the most recent `## Turn` heading. Reconcile with anything the user said directly in the terminal.
2. **Resolve decisions**: each clear answer becomes a decision. Append to `decisions.md` (see "decisions.md format" below). Most start as `@draft`; promote to `@spec` only when they're precise enough to implement without further questions.
3. **Copy** `turn-N.html` to `turn-(N+1).html`.
4. **Update content** in the new turn file: revise placeholder sections to reflect resolved decisions, add new sub-sections as the design grows, keep anchor buttons on every annotatable element.
5. **Append to the embedded transcript**: a new entry for turn N+1 — your previous question, the user's response (summarized), the decisions resolved, then your next question with recommended answer and alternatives.
6. **Update the decisions sidebar** in the HTML to reflect everything in `decisions.md`.
7. **Append a `## Turn N+1` heading to `feedback.md`** so the user has a fresh section to write under (see "feedback.md format" below).
8. **Tell the user**: "Open `turn-(N+1).html` and reply."

### Ending

When the user signals they're done (no more questions to resolve, or asks you to stop):
- Make a final pass on `decisions.md`: any `@draft` that's actually precise enough should be promoted to `@spec`.
- Optionally summarize the session in the final turn's embedded transcript.
- Suggest whether any decisions earn ADRs (see "ADRs — sparingly" below).
- The design is now archived as a series of turn files plus the two markdown sidecars. Commit them.

## Artifact conventions

The `template/turn-01.html` file in this skill directory is the starting point. Copy it for each new design and edit. Key conventions:

- **Tailwind v3 Play CDN** is loaded via `<script src="https://cdn.tailwindcss.com">` in the head. Single file, no build, works offline if the CDN has been cached. Use Tailwind utility classes freely.
- **Semantic HTML**: real `<section>`, `<article>`, `<nav>`, `<aside>`, `<header>` tags. Anchor buttons rely on heading structure.
- **Anchor buttons** (`data-grill-anchor="<id>"`) sit next to every annotatable region's heading. The accompanying inline JS copies `> @<id>: ` to the clipboard on click — the user pastes that into `feedback.md` and writes their comment after.
- **Embedded transcript** lives in a `<section id="grill-transcript">` at the bottom of the file. Each turn appends a `<details>` block: question, recommended answer, alternatives, user response, decisions resolved. The transcript IS the design record.
- **Decisions sidebar** lives in `<aside data-grill="decisions">`. Mirrors `decisions.md` content; updated each turn so a reader looking at any turn file can see what's been resolved up to that point.
- **No implementation code** in the artifact unless it's the subject of the design. No DB schemas, no server code, no ORM queries.
- **No JS frameworks**. The only JS in the artifact is the ~20-line anchor-copy snippet. The artifact must remain openable in any browser years from now without setup.

## Anchor references

In `feedback.md` the user references parts of the artifact via `> @<anchor-id>:` markdown blockquotes:

```md
## Turn 2

> @listing: too dense with metadata, drop the relative timestamp from the row
> @empty-state-cta: this should send the user to "open existing" not "create new"

The header looks fine. One thing I want to push back on: the entry point
recommendation feels off — see @listing comment.
```

When you read `feedback.md`, parse the `> @<anchor>:` lines as targeted feedback on specific parts of the artifact. Free-form prose between them is general session feedback.

When you scaffold a new section in the artifact, give it a stable `id` and an anchor button. Don't rename ids between turns — the user's prior feedback references them.

## `feedback.md` format

Single file, append-only, lives at `docs/design/<slug>/feedback.md`. Starts with:

```md
# Feedback

## Turn 1

(user writes here)
```

You add a fresh `## Turn N+1` heading after generating `turn-(N+1).html`. That's the only mutation you make to this file — never edit the user's content. Each turn, read the section under the most recent `## Turn` heading; everything above it has already been processed.

If the user typed their response directly in the terminal instead of writing in `feedback.md`, the section under the latest `## Turn` heading may be empty. That's fine — process the terminal response.

## `decisions.md` format

Append-only log of resolved decisions, lifecycle-tagged. Lives at `docs/design/<slug>/decisions.md`.

```md
# Decisions

## entry-point
- [spec] `/sessions` route on the lavish server, reachable independent of any open artifact
- [draft] chrome page links to it from a small "all sessions" affordance in the header

## listing-shape
- [draft] card-per-session, sorted by last activity descending
- [draft] each card shows: canonical path, last-activity timestamp, count of queued prompts
```

Lifecycle tags:
- `[draft]` — rough idea, not yet precise enough to build
- `[spec]` — precise, an implementer could pick this up without further questions
- `[implemented]` — code-backed (you won't write these during grilling; the implementation step does)

Don't promote `[draft]` to `[spec]` casually. If the user's answer left wiggle room, it's still `[draft]`.

## CONTEXT.md compatibility

If the project already has a `CONTEXT.md` or `CONTEXT-MAP.md`, do not duplicate decisions there. If a sibling skill expects one and none exists, create a minimal stub that points to the design directory:

```md
# Context

> Canonical design for <slug> lives in [docs/design/<slug>/](docs/design/<slug>/).
> Latest snapshot is the highest-numbered `turn-NN.html`. Resolved decisions
> are in `decisions.md`; per-turn feedback is in `feedback.md`.

## Glossary

(intentionally minimal — see the artifact)
```

`CONTEXT.md` is a glossary. Don't put implementation details, design decisions, or rationale in it.

## ADRs — sparingly

Only suggest an ADR when all three are true:

1. **Hard to reverse** — changing your mind later has meaningful cost.
2. **Surprising without context** — a future reader will wonder "why did they do it this way?"
3. **Real trade-off** — there were genuine alternatives and one was chosen for specific reasons.

If any is missing, skip the ADR. The decision still lives in `decisions.md` and the turn transcripts — it just doesn't need its own document.

When you do create an ADR, place it at `docs/adr/<NNNN>-<slug>.md` and link back to the design directory.

## Sharpening discipline

During the grill:

- **Challenge fuzzy language.** If the user says "the panel" and two panels exist in the artifact, ask which (use anchor names). If they use a term that could mean two things, propose a canonical name and confirm.
- **Stress-test with concrete scenarios.** "What if the viewport is 320px wide?" "What if there are 50 sessions in the list?" "What if a session is from a deleted file?" Force precision.
- **Cross-reference with code.** If the user states how something currently works, check the code. If their model and the code disagree, surface it.
- **Recommend an answer per question.** Don't ask open-ended "what should we do?" — propose an answer with a brief reason, name alternatives, then let the user accept, modify, or reject.
- **Resolve dependencies in order.** Don't ask about leaf decisions before the parent shape is settled. Entry point first, then listing shape, then per-row affordances — not the other way around.

</supporting-info>

## Sources

This skill absorbed ideas from upstream skills/projects rather than depending on them at runtime. The `sources.json` file in this directory tracks each upstream with the SHA of its content at absorption time. A repo-level GitHub Action checks each source for drift on a weekly cron and opens a `@claude`-tagged PR when meaningful upstream changes appear.

- [`grill-me`](https://github.com/mattpocock/skills/tree/main/skills/productivity/grill-me) — one-question-at-a-time interview methodology.
- [`grill-with-docs`](https://github.com/mattpocock/skills/tree/main/skills/engineering/grill-with-docs) — ADR three-criteria rule, CONTEXT.md compatibility shape, sharpening discipline.
- [`html-effectiveness`](https://github.com/ThariqS/html-effectiveness) — self-contained HTML artifacts with copy-export feedback (anchor-into-clipboard pattern adapted from this).
