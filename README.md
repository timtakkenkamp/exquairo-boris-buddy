# Boris Buddy Boris buddy (Tim)

Standalone repo under **timtakkenkamp**. Patient-facing electronic buddy demo plus training data, models, and preprocessing stubs.

## What’s in here

- `product/buddy/` — Streamlit + FastAPI demo (risk, what-if, lifestyle tiles, chat)
- `data/` — synth raw CSV, filtered set, train/test splits A/B
- `models/` — joblib models used by the live buddy overlay
- `Scripts and Notebooks/` — discovery notebook + preprocessing stubs

## Quick start (buddy)

Full runbook: [DEMO.md](./DEMO.md). Also listed from the [Boris Buddy hub](https://github.com/timtakkenkamp/products).

```bash
uv sync
uv run streamlit run product/buddy/app.py --server.headless true
# zaal view: add ?demo=1
```

Optional xAI key for Grok chat: copy `.streamlit/secrets.toml.example` to `.streamlit/secrets.toml` and set `XAI_API_KEY`.

## Note

This repository is Tim’s own copy for future course/product work. It is **not** a fork and has **no** upstream remote to another GitHub account.
