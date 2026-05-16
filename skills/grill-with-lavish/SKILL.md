---
name: grill-with-lavish
description: Interview the user one question at a time about a UI/UX or design plan, with each resolved decision visualized live in a Lavish HTML artifact and recorded as an atomic claim. Use when the user wants to stress-test a visual design — UI flow, layout, copy, state machine, navigation — and seeing the thing being decided matters. For pure-text decisions (terminology, domain modeling without visuals), pick a text-only grilling approach instead.
---

<what-to-do>

Interview the user relentlessly about every aspect of the plan until you reach a shared understanding. Walk down each branch of the design tree, resolving dependencies between decisions one at a time. For each question, provide your recommended answer.

Ask questions one at a time, waiting for feedback on each before continuing.

If a question can be answered by exploring the codebase, explore it instead.

The interview happens through Lavish's chat panel. The HTML artifact is the running visual record of the design as it crystallizes — update it as decisions resolve, so the user can see the design taking shape while you grill.

</what-to-do>

<supporting-info>

## The surface: Lavish

This skill drives a Lavish session. Lavish is invoked via `npx lavish-axi@latest` — no install required, no global hooks. Commands you need:

- `npx lavish-axi@latest docs/design/<slug>.html` — open the artifact in the user's browser. Spawns a chat panel alongside the live preview. If a Lavish server is already running it is reused; otherwise one is spawned in the background.
- `npx lavish-axi@latest poll docs/design/<slug>.html --agent-reply "<your question>"` — post your next grilling question into the chat panel and wait (long-poll) for the user's reply. The `--agent-reply` text is rendered in the conversation; the call returns when the user responds via chat OR via an annotation on the artifact.
- `npx lavish-axi@latest end docs/design/<slug>.html` — close the session when shared understanding is reached.

Annotations on the artifact come back as structured prompts with a `target` that pinpoints what the user is referring to (element selector, or text-range with boundaries). Use them to disambiguate "this part, not that part" — far more precise than chat alone.

Don't try to manage the Lavish server yourself. The CLI handles spawning, health checks, and version upgrades.

## When to use this skill

Trigger when the user is grilling a design *that has a visual shape*: UI flows, page layouts, component composition, copy comparisons, state machines, navigation structure, interaction shape.

Do NOT use for:
- Glossary or terminology decisions ("is this a Customer or a User?") — those are text-only.
- Pure backend or data-model design with no rendered representation.
- Quick one-off clarifications that don't deserve a session.

If you're unsure whether the decision is visual, ask the user. A grilling session that doesn't earn its artifact is more friction than value.

## The loop

1. **Pick a slug** for the design (e.g. `checkout-flow`). Artifact path is `docs/design/<slug>.html`. If `docs/design/` doesn't exist, create it.
2. **Scaffold a minimal initial artifact**. Single page, semantic HTML, placeholder sections for what the design will cover. Include an `<aside data-grill="decisions">` panel — resolved decisions will accumulate there as the session progresses. Lavish auto-injects Tailwind + DaisyUI unless you opt out, so use Tailwind classes freely.
3. **Open the session**: `npx lavish-axi@latest docs/design/<slug>.html`. The user's browser opens to the artifact + chat panel.
4. **Ask the first question** via `--agent-reply` and wait for the response.
5. **When a decision resolves**:
   - Update the artifact to reflect it (rendered in the iframe; live-reload picks it up automatically).
   - Append to the `data-grill="decisions"` panel so the user sees it accumulate visually.
   - Record it as a fact (see "Recording resolved decisions" below).
   - Consider whether it earns an ADR (see "ADRs" below — most don't).
6. **Move to the next branch.** Resolve dependencies in order — don't ask about leaf decisions before the parent shape is settled.
7. **End the session** with `npx lavish-axi@latest end docs/design/<slug>.html` when the user signals they're done.

## Recording resolved decisions

Each resolved decision should be an atomic, lifecycle-tagged claim — short, sharp, ideally testable later.

Lifecycle tags:
- `@draft` — rough idea, not yet precise enough to build
- `@spec` — precise, ready to build
- `@implemented` — code-backed and verified (you won't write these during grilling; the implementation step does)

**Where to record:**

- **If `.facts` exists at the repo root** — append the decision there per the facts format. Group under a section heading matching the design domain (e.g. `# checkout-flow`). Tag `@draft` or `@spec`.
- **Otherwise** — append to `docs/design/<slug>.decisions.md` in a simple list:
  ```
  # <slug>

  - [draft] auth banner sits above the hero on mobile only
  - [spec] checkout summary collapses behind a disclosure on viewports < 480px
  ```

Either way, reflect the decision in the artifact's `data-grill="decisions"` sidebar so it's visible during the session.

Don't decide between `@draft` and `@spec` casually. `@spec` means "I could hand this to an implementer right now and they'd build the right thing without further questions." Most grilling output starts as `@draft` and gets sharpened in later turns.

## CONTEXT.md compatibility

If the project already has a `CONTEXT.md` or `CONTEXT-MAP.md`, do not duplicate decisions there. If you need to create one for ecosystem compatibility (e.g. a sibling skill expects it), keep it minimal and point to the artifact:

```md
# Context

> Canonical design for <slug> lives in [docs/design/<slug>.html](docs/design/<slug>.html).
> This file exists for ecosystem compatibility; resolved decisions are recorded in the
> artifact's decisions panel and in `.facts` (or `docs/design/<slug>.decisions.md`).

## Glossary

(intentionally minimal — see artifact)
```

`CONTEXT.md` is a glossary, not a decision log. Don't put implementation details, design decisions, or rationale in it.

## ADRs — sparingly

Only offer to create an ADR when all three are true:

1. **Hard to reverse** — the cost of changing your mind later is meaningful.
2. **Surprising without context** — a future reader will wonder "why did they do it this way?"
3. **Real trade-off** — there were genuine alternatives and one was chosen for specific reasons.

If any is missing, skip the ADR. The decision still gets recorded as a fact and in the artifact — it just doesn't need its own document.

When you do create an ADR, place it at `docs/adr/<NNNN>-<slug>.md` and link to the artifact. Don't batch ADRs; create them inline when the criteria are met.

## Artifact conventions

- **Semantic HTML.** Use real `<section>`, `<article>`, `<nav>`, `<aside>` tags. Lavish's annotation handlers work better with semantic structure.
- **Tailwind + DaisyUI** are auto-injected unless the artifact opts out with `<meta name="lavish-design" content="off">`. Default is to use them.
- **`data-lavish-action`** marks interactive controls you embed that call `window.lavish.queuePrompt(...)` or `window.lavish.sendQueuedPrompts()`. Mark such controls so they get a pointer cursor and are excluded from annotation handlers.
- **`data-grill="decisions"`** marks the decisions sidebar. Keep this convention so a future iteration of the skill (or a sibling) can find it across runs.
- **No implementation code** in the artifact — no DB schemas, server code, ORM queries — unless those are themselves the subject of the design.

## Sharpening discipline

During the grill:

- **Challenge fuzzy language.** If the user says "the panel" and there are two panels in view, ask which one. If they use a term that could mean two things, propose a canonical name and confirm.
- **Stress-test with concrete scenarios.** "What happens if the user resizes to 320px wide mid-flow?" "What if the request takes 8 seconds?" Force precision.
- **Cross-reference with code.** If the user states how something currently works, check the code. If they contradict each other, surface it.
- **Recommend an answer per question.** Don't ask open-ended "what should we do?" — propose an answer with a brief reason, then let the user accept, modify, or reject.

</supporting-info>

## Sources

This skill absorbed ideas from upstream skills/projects rather than depending on them at runtime. The `sources.json` file in this directory tracks each upstream with the SHA of its content at absorption time. A repo-level GitHub Action checks each source for drift on a weekly cron and opens a `@claude`-tagged PR when meaningful upstream changes appear.

- [`grill-me`](https://github.com/mattpocock/skills/tree/main/skills/productivity/grill-me) — interview methodology.
- [`grill-with-docs`](https://github.com/mattpocock/skills/tree/main/skills/engineering/grill-with-docs) — ADR discipline and CONTEXT.md compatibility shape.
- [`facts`](https://github.com/av/facts) — atomic-claim lifecycle and the `.facts` format.
