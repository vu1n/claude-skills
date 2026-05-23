# Decisions

## @surface

- [spec] **hybrid**: per-turn HTML files + optional `grill-server.py` (Python stdlib, ships with the skill).
  - **Without server**: HTML files open standalone in any browser. Composer falls back to copy-to-clipboard; user pastes into `chat.md`. Artifact remains fully archivable.
  - **With server**: `python3 grill-server.py <design-dir>` enables live mode. Composer POSTs to `/reply` (server appends to `chat.md`); conversation view polls `/chat.md` for updates. Server is single-file, zero deps, no global config mutation, auto-shuts on Ctrl-C.
- **Lesson:** marked `[spec]` after Turn 1 prematurely. Real UX friction only surfaced once the in-page composer was built and used. Hold `[draft]` longer than feels comfortable.

## @feedback-channel

- [spec] in-page composer inside the artifact; no separate window or editor required during a turn.
- [spec] single sibling `chat.md` is the canonical chat history (every turn's agent + user blocks).
- [spec] each `turn-NN.html` renders `chat.md` content into its conversation view. With server: live polling. Without server: baked-in snapshot at scaffold time.

## @versioning

- [spec] per-turn `turn-NN.html` snapshots. Each file is complete reading (conversation + design + decisions all embedded). `git diff turn-NN.html turn-(NN+1).html` shows what one round resolved.

## @annotation-precision

- (not yet grilled)

## @decision-recording

- (not yet grilled, but this file is a draft demonstration: lifecycle tags inline, kebab-case branch headings, structured-enough-to-grep, free-form prose under each)
