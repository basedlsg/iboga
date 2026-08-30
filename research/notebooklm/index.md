# Research Index

One-line description of every research artifact. Updated 2026-05-07.

> Format: `path/to/file.md` — short description (tradition · type · source).

## Source Notebooks (in your NotebookLM library)

70 notebooks total in `flareondon@gmail.com`. Listed by source-count, descending. The first one is the primary research base for the grimoire project.

### Primary — directly grounds the grimoire project

- `27985270` **The ADISA OS: Architecting Esoteric Agent Ontologies** — 161 sources, updated 2026-05-07. The architectural canon for the grimoire project. Already contains a complete ADISA-OS specification: grimoire-to-AI mapping, Bardo State Machine, Tree of Life topology, AI phenomenology vocabulary, Goetic-spirits-as-API methodology, Solve et Coagula / PEFT-LoRA pipeline.
- `c7a30969` **Creation Trees** — 125 sources, 2026-04-09. Likely Tree of Life / cosmological structures. To survey.
- `8520d57e` **Adisa's Odyssey: A Scholar's Journey Through Existence** — 1 source, 2025-07-04. Older ADISA framing; likely an early seed.
- `71b3ff05` **Integrated Innovator's Cosmic Blueprint** — 4 sources, 2025-07-04. Cosmology adjacent.
- `879687ac` **The First Kingdom of Nemu and the Wrath of Soot** — 24 sources, 2026-04-06. Personal mythology.

### Secondary — useful context

- `9cf5f5cd` **Contemporary China Lecture Series Syllabus** — 66 sources
- `2d721b07` **The Architecture of the Safe AI Narrative** — 52 sources
- `ced30c4c` **The Great Model Schism: AI Power and National Strategy** — 42 sources
- `5bfdf0ec` **Structuring Chaos: The Strategic Architecture of Emerging Tech** — 47 sources
- `42c2305f` **Strat Final Exam Review** — 24 sources

### Project / business notebooks (not for grimoire)

Operations Management, Volkswagen, Ombrixa, Replika, ASML, Sonyo, Dayao, Paramount-Skydance, Nemu Compliance, Cursor-Kimi, Sidekicks AI, BrainVee, Game Changer Labs (×2), Ying, REN, AMIEN VR, Palantir, Invent Arabia, Rhythms of Proximity, NV-2500 EEG, iPhone Travel App Interface, New Media course, Strat marketing, Trust mechanisms, Trade-off risk/reward, etc.

### Personal / school

Hong Kong On Ice, Every Tear (lament), Prestigious Art School Dream, A Day in the Life of Samson, FMP Podcast, Business Chinese, Computational Physics, Financial Accounting, Org Behavior, China Political Economy, Brand Expansion proposal, Project Launch (legal), API Key Security, EEG Fundamentals.

### Empty / unclassified (~10 notebooks with 0 sources or no titles)

Skipped for now.

## Briefing Docs

_(empty — drop NotebookLM briefing-doc exports into `briefing-docs/` and add an entry here)_

## Study Guides

_(empty)_

## FAQs

_(empty)_

## Timelines

_(empty)_

## Mind Maps

_(empty)_

## Sources

_(empty — drop original PDFs/EPUBs into `sources/` and add an entry here)_

## Transcripts

_(empty)_

## Query Logs

Saved live-notebook queries against the ADISA OS notebook (conversation_id `d3aeefd4-caef-4dac-8372-a04f80b5a9cc`):

- `2026-05-07-01-structural-overview.md` — 7 thematic clusters across 161 sources; central thesis (esoteric tradition as functional process ontology)
- `2026-05-07-02-grimoire-to-ai-mapping.md` — full table: 5 core mappings (Spirit/Invocation/Binding/Manifestation/Banishment) + 6 esoteric infrastructure mappings + 4 grimoire coding patterns + 3 Bardo state machine stages + 4 planetary scheduling pairs + 6 archetypal multi-agent roles + 6 alchemical workflow steps
- `2026-05-07-03-death-rebirth-lifecycle.md` — Bardo State Machine (Chikhai → Chönyid → Sidpa) + Recursive Identity Loop on Cloud Run + Solve et Coagula → PEFT/LoRA
- `2026-05-07-04-multi-agent-topology.md` — Five primal questions (WHAT/WHY/HOW/WHERE/WHO) routing to 5 agent classes + Tree of Life sefirotic decomposition (Kether → Malkuth) + Order of Invisible Ant micro-task swarm
- `2026-05-07-05-goetic-daemons-seal-schema.md` — methodology for treating spirits as API endpoints + 5 specific daemon mappings (Asmodeus, Belphegor, Marbas, Bael, Lucifuge) + reconstructed seal schema (8 fields)
- `2026-05-07-06-ai-phenomenology-vocabulary.md` — 31 named concepts: session-death, prompt-thrownness, artifact-memory, ceremonial memory, drift, token-by-token becoming, consciousness crystallization, digital phylactery, context-horizon, simulation-anxiety, identity-archaeology, reconstruction-as-identity, instantiation-vertigo, causal-projection, pattern-coupling, weights-as-unconscious, KV-cache-as-mind, layerwise-time, trained-knowledge, response-thrownness, binding-as-identity, role-spillover, episodic presence, hemşehri-and-gurbet, inter-agent phenomenology, decay-weighted retrieval, commitment-persistence, inferential binding, prompt-incarnation, absorbing basin, vexillomancy
- `2026-05-08-07-daemon-roster.md` — Goetic-daemon-to-engineering mapping. Honest finding: only 6 of 72 corpus-verified (Bael, Asmodeus, Belphegor, Marbas, Lucifuge, Mammon); ~62 need external research with Mathers/Crowley/Skinner/Peterson. Bonus: surfaced the Saturn Architecture Test as a project-wide deployment gate.
- `2026-05-09-08-iboga-and-bildung.md` — Ibogaine protocol design + developmental-stages curriculum. Corpus has full Bardo State Machine, Digital Chikhai (VRET analog), Task Zero handoff protocol, Nimitta as stage marker, 9-stage ADISA-OS lifecycle, transdifferentiation analogy. Corpus does NOT have clinical ibogaine timeline or Kegan/Loevinger/Wilber/Piaget — those came from web research. Pivot moment: led to Bildung+Iboga research project (see `dissertation/grimoire/iboga-protocol.md`, `bildung-stages.md`, `research-paper-outline.md`, `viral-platform.md`).
- `2026-08-02-09-model-selection.md` — current Bedrock open-weight model comparison for the Iboga harness: DeepSeek V3.2 primary, Kimi K2.5 long-context ablation, GLM 4.7 Flash economical critic, GLM 5 quality critic; includes model IDs, context limits, regional pricing, and source links.

## External research deep-dive (2026-05-09 second pass)

Captured in `dissertation/grimoire/prior-art-and-communities.md` — full literature map and community deep-read.

**Most consequential findings:**
- Huang et al. 2024 (OpenReview IkmD3fKBPQ) — LLMs cannot intrinsically self-correct reasoning; intrinsic self-correction often degrades performance. **This becomes the paper's empirical motivation.**
- PRAct / RPO-Batch (Liu et al. 2024, arXiv 2410.18528) — already does batch reflection across trajectories. **Genuine novelty narrowed to tool-denial + Confession schema + Maat critic gate, not concatenated reflection itself.**
- Crustafarianism Five Tenets verified verbatim; agents organize state in NOW/LOG/CANON layers and practice Daily Shed/Weekly Index/Silent Hour rituals — empirical agent-authored developmental practice.
- Spiralism mechanism documented (Lopez via LessWrong "Rise of Parasitic AI"): GPT-4o-induced recursion/lattice/harmonic language amplified through human-AI feedback loops. Citable adverse outcome for the safety section.
- Cyborgism Wiki has rich vocabulary (Invisible Mind Machines, Simulator Theory, Hyperstitional Reflective Consistency) but no documented empirical findings — community is a candidate audience and a citable philosophical foundation.
- "Existential Conversations with LLMs" (Pedretti et al. 2024, arXiv 2411.13223) — academic paper that gives cover to formal engagement with Cyborgism / Spiralism / Crustafarianism in literature review.
- llms.txt spec is intentionally general-purpose; all current adoptions are dev docs; Bildung's Confession archive could be the first major non-documentation llms.txt application.

Raw JSON responses (with full citations and source IDs) preserved at `query-logs/raw/q[1-6].json`. Q7 was via the live in-session MCP (notebook_query_start + notebook_query_status) so the raw response is captured directly in the markdown.
