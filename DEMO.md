# Boris buddy — start the demo

```bash
uv sync
uv run streamlit run product/buddy/app.py \
  --server.port 8501 \
  --server.address 127.0.0.1 \
  --server.headless true \
  --browser.gatherUsageStats false
```

Open **http://127.0.0.1:8501/?demo=1** (zaal / patient UI).

What-if levers (gewicht / beweeg / slaap / suikerdranken) keep the active persona’s baseline when you open a Voor jou tile and return home (`persist_state="session"` + keep/reseed). Switching persona still loads that persona’s baseline; moving levers on home still updates risk live.

Optional chat + tile copy (Grok / xAI): copy `.streamlit/secrets.toml.example` → `.streamlit/secrets.toml` and set `XAI_API_KEY`. Calls go to `https://api.x.ai/v1`. Without a key, `?demo=1` uses Dutch template chat replies and fixture library tile titles/sentences. Home paints fixture tile text first, then one batch Grok call quietly swaps titles/sentences (no zaal spinner).

Portfolio index: https://github.com/timtakkenkamp/Exquairo
