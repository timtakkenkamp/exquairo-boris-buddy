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

Optional chat: copy `.streamlit/secrets.toml.example` → `.streamlit/secrets.toml` and set `OPENAI_API_KEY`.

Portfolio index: https://github.com/timtakkenkamp/Exquairo
