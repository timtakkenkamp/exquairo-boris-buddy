# Boris buddy (simplified mock)

Patient-facing demo on **Tim’s own GitHub repo**. Three steps: **je risico → waarom jij → doe dit**. Style follows the Boris board (soft blues, sprout green, rounded cards, *Small steps. Big impact. With Boris.*).

Nothing here is a clinical claim.

## How to run

```bash
uv sync
uv run streamlit run product/buddy/app.py
```

Without `uv`:

```bash
pip install -r product/buddy/requirements.txt
streamlit run product/buddy/app.py
```

Open the URL Streamlit prints (usually http://localhost:8501). Sidebar: **Pietje / Sam / Noor**.

**Zaalweergave:** `http://localhost:8501/?demo=1` of de knop **Zaalweergave** in de werkplaats-sidebar. Sidebar is weg; persona is drie pillen onder *Hoi Pietje*. Key komt uit `secrets.toml` / `XAI_API_KEY`. Zonder `?demo=1` is het de werkplaats.

## What was simplified

| Before | Now |
| --- | --- |
| Long home, English leftovers | 3-step Dutch home + always-visible **Vraag het Boris** chat |
| 5 local factors | Max **3** (*verhoogt/verlaagt je risico op diabetes*) |
| Three equal cards | **Three tiles** again, ordered by this person’s strongest factors |
| Cream/coral chrome | Boris sky-blue + sprout green |

Official mascot: `product/buddy/assets/boris-mascot.png` (top-left header). See `assets/README.md`.

## Kept

- Two big numbers: korte- / lange-termijn risico op diabetes (HbA1c > 6.5% only as small disclaimer)
- Weight/BMI what-if plus taille, beweegminuten, slaap and suikerdranken (live risks + bars)
- Movement detail: Groningen Plantsoen–gracht–Martini-lus + back
- Personas Pietje / Sam / Noor
- Guardrails: no meds, no triage
- Chat via xAI / Grok when a key is present (sidebar, `.streamlit/secrets.toml`, or `XAI_API_KEY`); otherwise Dutch templates

## Grok chat (xAI)

De vragenbox **Vraag het aan Boris** gebruikt `grok-4` via `https://api.x.ai/v1` zodra er een sleutel is. De sleutel wordt niet gecommit.

1. Plak de key in de sidebar onder **xAI-sleutel (Grok)**, of
2. Kopieer `.streamlit/secrets.toml.example` naar `.streamlit/secrets.toml` en vul `XAI_API_KEY` in, of
3. Zet `XAI_API_KEY` in je omgeving.

Zonder sleutel blijft de demo werken met vaste Nederlandse teksten. Medische vragen worden nog steeds geweigerd voordat xAI wordt aangeroepen. Op zaal (`?demo=1`) geen vendor-namen in de UI.

De system prompt staat in `prompts/boris_system.md` (Barbecue Bob-stijl: rol, toon, grenzen, voorbeelden). Per vraag plakt de app de actuele demo-kaart (risico’s, factoren, tegels) op `{SESSIE_CONTEXT}`. In de sidebar zit een dichte expander **System prompt (demo)** om te itereren, plus **Herstel default**. Dat is voor ons, niet voor de patiënt. Regex-guardrails blijven de harde deur.

## What-if formula

```
short_term = clip(base_short + 0.025 * dBMI + lifestyle_short + 0.004 * extra_cm, 0.02, 0.95)
long_term  = clip(base_long  + 0.035 * dBMI + lifestyle_long  + 0.006 * extra_cm, 0.03, 0.97)
extra_cm   = taille - (taille0 + 0.7 * dkg)   # 0 when taille only follows gewicht
lifestyle_short = -0.008 * d_move30 - 0.012 * d_sleep + 0.006 * d_drinks
lifestyle_long  = -0.011 * d_move30 - 0.016 * d_sleep + 0.008 * d_drinks
```

Not a trained model. BMI direction flips at 25. Height/length is not a patient lever. Live models keep the 22 T1 columns; taille maps to `WAIST_T1` → `BRI_T1`. Movement, sleep and sugary drinks are mock-overlaid on the displayed what-if.

```bash
uv run python product/buddy/test_buddy.py
```

Keep all work in this repository (`timtakkenkamp/exquairo-boris-buddy`).

## Live models (stap 3)

Sidebar toggle **Live model (final A/B)** uses the no-spline finals via `live_model.py` + `model_adapter.py`:

- `models/model_a_best_logreg_elasticnet_no_spline_run1_final.joblib` (T1→T2)
- `models/model_b_best_xgboost_no_spline_run1_final.joblib` (T1→T3)

Persona feature snapshots live in `fixtures/persona-*-features.json`. The adapter derives `BRI_T1`, `NHDC_T1` and `THR_T1`. Toggle off = mock fixtures.

## Stap 4 — coaching API + guardrails

- Strengere NL/EN medical + jailbreak guardrails (pre + post LLM).
- Thin FastAPI bridge: `uv run uvicorn product.buddy.api:app --app-dir product/buddy --port 8080`
  - `GET /health`, `GET /personas`, `POST /predict`, `POST /ask`
- Demo video: `product/buddy/demo/boris-buddy-demo.mp4`
