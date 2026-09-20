"""Stap 4: thin JSON predict API over the live model adapter (contract bridge)."""

from __future__ import annotations

import copy
from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from live_model import models_available, overlay_live_predictions
from buddy_lib import load_personas, answer_question

app = FastAPI(
    title="Boris Buddy Predict API",
    version="0.4.0",
    description="Demo-only. Not a medical device. Lifestyle coaching + risk scores.",
)


class PredictRequest(BaseModel):
    persona_id: str = Field(..., examples=["persona-river"])
    weight_kg: float | None = Field(None, ge=35, le=180)
    use_live_model: bool = True


class AskRequest(BaseModel):
    persona_id: str
    question: str
    weight_kg: float | None = None
    use_live_model: bool = True


def _persona(persona_id: str) -> dict[str, Any]:
    for p in load_personas():
        if (p.get("patient") or {}).get("persona_id") == persona_id:
            return p
    raise HTTPException(404, f"Unknown persona_id: {persona_id}")


def _payload(persona_id: str, weight_kg: float | None, use_live: bool) -> dict[str, Any]:
    base = copy.deepcopy(_persona(persona_id))
    if use_live and models_available():
        return overlay_live_predictions(base, weight_kg=weight_kg)
    # mock path: import lazily to avoid circulars in some layouts
    from buddy_lib import apply_weight_whatif

    return apply_weight_whatif(base, weight_kg=weight_kg)


@app.get("/health")
def health() -> dict[str, Any]:
    return {
        "ok": True,
        "live_models": models_available(),
        "disclaimer": "Demo only. Not diagnosis or medical advice.",
    }


@app.get("/personas")
def personas() -> list[dict[str, str]]:
    out = []
    for p in load_personas():
        pat = p.get("patient") or {}
        out.append(
            {
                "persona_id": pat.get("persona_id", ""),
                "display_name": pat.get("display_name", ""),
            }
        )
    return out


@app.post("/predict")
def predict(req: PredictRequest) -> dict[str, Any]:
    payload = _payload(req.persona_id, req.weight_kg, req.use_live_model)
    # Return contract-shaped subset
    return {
        "schema_version": payload.get("schema_version", "0.2.0"),
        "source": payload.get("source"),
        "disclaimer": payload.get("disclaimer"),
        "patient": payload.get("patient"),
        "risks": payload.get("risks"),
        "top_factors": (payload.get("top_factors") or [])[:5],
        "whatif": payload.get("whatif"),
        "live_model": payload.get("live_model"),
    }


@app.post("/ask")
def ask(req: AskRequest) -> dict[str, Any]:
    payload = _payload(req.persona_id, req.weight_kg, req.use_live_model)
    text, source = answer_question(req.question, payload)
    return {"answer": text, "source": source, "persona_id": req.persona_id}
