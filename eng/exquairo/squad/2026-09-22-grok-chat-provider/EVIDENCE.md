# Evidence — grok-chat-provider

Datum: 2026-09-22

## Chat provider
- In-app completions use OpenAI-compatible client with `base_url=https://api.x.ai/v1` and secret `XAI_API_KEY`.
- Default model: `grok-4` (override via `XAI_MODEL`).

## Agent env
- This cloud-agent environment does **not** have `XAI_API_KEY` set (checked presence only; value never printed).
- Therefore live Grok replies could not be exercised here.
- Without a key, `?demo=1` chat falls back to Dutch template replies (no crash, no fake “connected” success).
- Unit/AppTest coverage: mocked client asserts `base_url`, model, runtime error copy, and zaal vendor-silence.

## Manual check for David
1. Set box secret `XAI_API_KEY`.
2. Open `/?demo=1`, ask a lifestyle question under **Vraag het aan Boris**.
3. Expect a Grok reply; no OpenAI/xAI/Grok captions on zaal.
4. Werkplaats should show `Verbonden met Grok · grok-4` when the key is present.
