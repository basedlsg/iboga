# CLAUDE.md — Iboga Project (Scoped)

You are working on the Iboga research project. **This folder is the entire allowed scope.**

## Hard scoping rule

When the user mentions "Iboga," "the experiment," "pre-reg," "the protocol," or anything related to this research program:

**READ ONLY** from `/Users/carlos/Brain/OBSIDIAN/projects/iboga/` and its subdirectories.

Do NOT read from:
- `../life-compiler/` — different project
- `../nemo-compliance/` — different project (yes, even though Iboga uses Nemo as a deployment vignette; that's a separate code path)
- `../innoxera-ksa/` — different project
- `../brain-itself/` — different project
- `../../inbox/` — vault capture stream, out of scope
- `../../notes/` — vault notes, out of scope
- `../../ideas/` — vault ideas, out of scope
- `../../archive/` — vault history, out of scope
- `../../daily-briefs/` — automated briefs, out of scope
- `../../weekly-syntheses/` — automated syntheses, out of scope

**WRITE ONLY** to files inside this folder.

If you need information from another folder, **ask the user to manually copy it in** rather than reading it yourself.

## The one exception

The final paper draft will draw lightly on `/Users/carlos/NEMU-TEST-main/` (the Nemo code repo, NOT the vault folder) for the deployment vignette chapter. This is allowed **only** when explicitly invoked by the user with words like "now read Nemo's code for the case-study chapter." Default off.

## What this project is

A pre-registered, 4-model, 3-arm, ICLR 2027 workshop submission characterizing how vocabulary choice and structural constraint on a retrospective protocol mediates structural-erosion slope and solve rate on the SlopCodeBench benchmark, with exploratory SAE mechanistic analysis on Llama-3.3-70B.

Pre-reg in `prereg.md`. Pre-lock checklist in `next-steps.md`. Status flags in `README.md`.

## What this project is NOT

- It is not the silentvault paper (that's already a workshop submission, separate).
- It is not Nemo's product development (that's commercial, separate).
- It is not a general-purpose introspection paper (it's narrowly scoped to retrospective protocols on a code-quality benchmark).

## How to read

If the user asks an open-ended question about Iboga, default to reading `README.md` and `next-steps.md` first. The `prereg.md` is the authoritative document and should be quoted when specifics are needed.

## Style

- Cite vault-relative paths (drop `/Users/carlos/Brain/OBSIDIAN/` prefix) when referring to files within Iboga.
- Use absolute paths only when crossing out of this folder (which should be rare).
- Treat the pre-reg as locked starting `status: locked` in its frontmatter. Before lock, edits are tracked in `next-steps.md`'s living decision log.
- No sycophancy. The reviewers were harsh and the candidate accepted it. Maintain that tone.

## Hard rules

- Never edit files outside this folder unless explicitly asked.
- Never read other project folders to "get context."
- Never propose adding cross-links to sibling project folders.
- Always convert relative dates to absolute (e.g., "Thursday" → `2026-05-14`).
- Today's date is in the system prompt; use it.
