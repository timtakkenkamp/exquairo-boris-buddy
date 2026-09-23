# Agent conventions — boris-buddy

## Cursor model two-pass (Tim 22 Sep 2026) — STANDARD

Default Cursor-agent = Grok 4.7 voor werkende PR’s. Optionele tweede pass = Claude Opus 5.5 alleen ter polish (structuur, edge cases, tests, naming, dode paden) op dezelfde branch/PR-diff — niet de hele repo. Geen Opus 5.5 bij kleine UI/copy/docs. Escalatie: David stelt voor na Grok-DONE; Tim bevestigt Opus-kosten; FE/BE start de agent. Cloud/Task: model expliciet zetten.

### When to run Opus 5.5 polish
- Diff raakt ≥2 lagen (bijv. app + lib + tests) of ongeveer >150–200 regels
- Gedrag / session-state / API-contract
- “Werkt maar niet strak” na Product PASS
- Multi-module refactor/migratie

### When not
- Copy, CSS, één helper, één testfix, DEMO/docs
- Tweede Grok-loop volstaat
- Tim zegt skip

### Other hard rules
- Repo source of truth: this repository only (`timtakkenkamp/boris-buddy`). Hub: `timtakkenkamp/products`.
- Human gate: **David only** via Product Squad channel — **not** Tim 1:1. Squad bots: **no SendToUser / no Tim status narration**.
- RESULT path: `/workspace/eng/products/squad/<YYYY-MM-DD>-<slug>/RESULT.md` → David (channel pointer). David briefs Tim only for kernkeuze / demo-klaar.
- Stop: max **2** CRITIQUE rounds per BRIEF; outer BRIEF budget in BRIEF+`LOOPS.md` (default 1).
- David does not launch build Cloud Agents unless Tim explicitly asks. FE/BE launch their own.
- Playbook: `/workspace/eng/products/product-squad-fase0.md`.
