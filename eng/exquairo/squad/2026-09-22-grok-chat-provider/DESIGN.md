# DESIGN — grok-chat-provider

ROUND 1 | ROLE Designer | STATUS: **LOCKED** (copy/UI notes only)  
Datum: 2026-09-22 · Scope: chat empty/error states for xAI switch — **no layout redesign**

## Outcome
Honest, patient-safe / operator-safe copy when chat uses Grok/xAI or when `XAI_API_KEY` is missing. Tile/layout unchanged.

## Scherm

| Surface | What changes |
|---------|----------------|
| **Zaal** `?demo=1` | Chat title + placeholder stay. No vendor names (“OpenAI”, “xAI”, “Grok”) in patient UI. Missing key → silent template replies (bestaand) **or** one soft line below the form (optional, see below). |
| **Werkplaats** (sidebar + captions) | Replace OpenAI labels with xAI/Grok operator copy. |

## Locked copy (NL)

### Patient / zaal (if any caption is shown)
- Prefer **no** caption under “Vraag het aan Boris” on zaal.
- If FE must signal offline templates:  
  **“Boris antwoordt nu met vaste teksten.”**  
  (No “API”, no “sleutel”, no vendor.)

### Werkplaats captions (not AUDIENCE)
| State | Copy |
|-------|------|
| Key present | `Verbonden met Grok · {model}` |
| Key missing | `Geen xAI-sleutel. Zet XAI_API_KEY (sidebar of secrets) — tot die tijd vaste teksten.` |

### Sidebar control labels (werkplaats)
- Expander / field: **“xAI-sleutel (Grok)”** (was OpenAI).
- Placeholder: do **not** use `sk-…` OpenAI shape; use something neutral like `xai-…` or leave empty placeholder text “plak sleutel”.
- Helper caption: point to `XAI_API_KEY` / secrets — never print the secret.

### Chat chrome (unchanged)
- Title: **Vraag het aan Boris**
- Placeholder: keep `CHAT_PLACEHOLDER` (“Wandelen, eten, slapen…”).
- Button: **Vraag**

### Error (runtime fail with key set)
- Short, non-technical: **“Even geen antwoord van Boris. Probeer het zo opnieuw.”**  
- Log detail only server-side; never dump API bodies or keys into the UI.

## Out of scope
- Tile LLM copy, lever-restore, primary/secondary layout, billing UX.

## Open vragen
1. **Geen** — zaal stays vendor-silent; werkplaats names Grok/xAI.

## Handoff
Frontend/Backend may implement provider switch using this copy. Designer idle after this lock.
