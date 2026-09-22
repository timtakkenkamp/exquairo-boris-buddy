# BRIEF — grok-chat-provider

ROUND 1 | ROLE Product | STATUS: **LOCKED** (David gate)  
Datum: 2026-09-22 · Repo: `timtakkenkamp/exquairo-boris-buddy` · Zaal: `?demo=1`  
Poort: David · Tim: only via David

## Outcome
Replace the OpenAI chat provider with **Grok / xAI** for the in-app chat only, so `?demo=1` chat calls `https://api.x.ai/v1` with the box secret `XAI_API_KEY`.

## In scope
- Chat completion path: switch provider from OpenAI → xAI (Grok).
- Config/env: read `XAI_API_KEY` (never log or print the value).
- API base: `https://api.x.ai/v1` (OpenAI-compatible client shape is fine if already used).
- Honest empty/error state if key missing (no fake success).
- Tests/smoke updated for provider switch; DEMO.md note if chat setup changed.
- Evidence: short note or screenshot that chat still works on `?demo=1` (or clear blocked reason if key absent in agent env).

## Out of scope
- LLM-generated **tile** sentences / copy (stap 3 tile-copy = later, not this brief).
- Billing / SuperGrok myths; plan upgrades; console shopping.
- Lever-restore bug (`levers-restore-persona`) — queued after this merges; do not start here.
- Persona_factors / lifestyle overlay fix on PR #3 follow-up — Frontend owns separately; not this BRIEF.
- Other remotes / forks.

## Success criteria
1. Chat requests go to xAI (`api.x.ai`), not OpenAI, when `XAI_API_KEY` is set.
2. No secrets in logs, commits, chat, or artifacts.
3. Missing key → clear patient-safe / operator-safe failure (no crash loop).
4. Tile layout / ranking from prior briefs unchanged.
5. David can demo chat on `?demo=1` (or documents key gap).

## Parallel plan
1. Designer — N/A unless empty-state copy needed (idle).
2. Backend — optional helper in buddy_lib / chat client if cleaner than FE-only.
3. Frontend — wire UI/chat client to xAI; BUILD.md + evidence.
4. Product — CRITIQUE after BUILD DONE (both FE DONE and BE DONE or N/A).

## Env (operators)
- Secret name: `XAI_API_KEY` (box secret).
- Base URL: `https://api.x.ai/v1`.

## Artifact path
`/workspace/eng/exquairo/squad/2026-09-22-grok-chat-provider/`
