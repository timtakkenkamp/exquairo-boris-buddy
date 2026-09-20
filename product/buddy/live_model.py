"""Overlay final A/B model predictions onto Boris persona payloads."""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

from buddy_lib import persona_body
from model_adapter import (
    FEATURE_COLS,
    MODEL_A_FILE,
    MODEL_B_FILE,
    body_roundness_index,
    models_on_disk,
    predict_diabetes_risks,
)

ROOT = Path(__file__).resolve().parent
FIXTURES = ROOT / "fixtures"

# Map model feature ids → buddy factor ids / themes when possible
_FEATURE_TO_FACTOR_ID = {
    "BMI_T1": "bmi",
    "BRI_T1": "bri",
    "WAIST_T1": "waist",
    "HIP_T1": "hip",
    "NHDC_T1": "cho",
    "THR_T1": "tgl",
    "HBAC_T1": "hbac",
    "SPORTS_T1": "sports",
    "CHO_T1": "cho",
    "TGL_T1": "tgl",
    "HDC_T1": "hdc",
    "LDC_T1": "ldc",
    "MAP_T1": "map",
    "HTN_MED_T1": "htn_med",
    "AGE_T1": "age",
    "DEPRESSION_T1": "depression",
    "BKR_T1": "bkr",
    "HBF_T1": "hbf",
    "EDUCATION_LOWER_T1": "education",
    "RESPIRATORY_DISEASE_T1": "respiratory",
}


def models_available() -> bool:
    return models_on_disk(ROOT.parents[1] / "models")


def load_feature_snapshot(persona_id: str) -> dict[str, Any]:
    path = FIXTURES / f"{persona_id}-features.json"
    if not path.exists():
        raise FileNotFoundError(f"Missing feature snapshot: {path}")
    return json.loads(path.read_text(encoding="utf-8"))["features"]


def _band(score: float) -> str:
    if score < 0.20:
        return "low"
    if score < 0.55:
        return "medium"
    return "high"


def features_with_weight(
    base_features: dict[str, Any],
    *,
    weight_kg: float,
    height_cm: float,
    waist_cm: float | None = None,
) -> dict[str, Any]:
    """Adjust BMI (and waist / BRI) when the user moves gewicht or taille."""
    feats = dict(base_features)
    height_m = max(height_cm, 100.0) / 100.0
    old_bmi = float(feats.get("BMI_T1") or 25.0)
    new_bmi = weight_kg / (height_m**2)
    feats["BMI_T1"] = round(new_bmi, 2)
    feats["HEIGHT_T1"] = height_cm
    if waist_cm is not None:
        feats["WAIST_T1"] = float(waist_cm)
        feats["BRI_T1"] = body_roundness_index(float(waist_cm), height_cm)
    elif feats.get("WAIST_T1") is not None:
        # Keep waist coherent with weight change (~0.7 cm per kg), same heuristic as mock what-if
        old_weight = old_bmi * height_m**2
        delta_kg = weight_kg - old_weight
        feats["WAIST_T1"] = float(feats["WAIST_T1"]) + 0.7 * delta_kg
        feats["BRI_T1"] = body_roundness_index(float(feats["WAIST_T1"]), height_cm)
    return feats


def overlay_live_predictions(
    payload: dict[str, Any],
    *,
    weight_kg: float | None = None,
    waist_cm: float | None = None,
) -> dict[str, Any]:
    """Return payload copy with risks/top_factors from live models."""
    updated = copy.deepcopy(payload)
    # Persona lifestyle card — used when live top-5 is mostly labs the patient cannot change.
    updated["persona_factors"] = copy.deepcopy(payload.get("top_factors") or [])
    body = persona_body(updated)
    patient = updated.get("patient") or {}
    persona_id = patient.get("persona_id")
    if not persona_id:
        raise ValueError("persona_id missing on payload")

    base = load_feature_snapshot(persona_id)
    height_cm = float(patient.get("height_cm") or body["height_cm"] or 170)
    body_weight = float(weight_kg if weight_kg is not None else body["weight_kg"])
    feats = features_with_weight(
        base, weight_kg=body_weight, height_cm=height_cm, waist_cm=waist_cm
    )

    pred = predict_diabetes_risks(feats, top_k=5)
    p_short = float(pred["risk_t1_t2"])
    p_long = float(pred["risk_t1_t3"])

    updated["source"] = "live_final_models"
    updated["risks"] = [
        {
            "id": "t1_t2",
            "horizon": "Korte-termijn risico op diabetes",
            "label": "Final model A (T1→T2, elastic-net). Proxy: kans op diabetes / HbA1c > 6,5%. Geen diagnose.",
            "risk_score": round(p_short, 4),
            "risk_label": _band(p_short),
        },
        {
            "id": "t1_t3",
            "horizon": "Lange-termijn risico op diabetes",
            "label": "Final model B (T1→T3, XGBoost). Proxy: kans op diabetes / HbA1c > 6,5%. Geen diagnose.",
            "risk_score": round(p_long, 4),
            "risk_label": _band(p_long),
        },
    ]

    top_factors = []
    for f in pred.get("top_factors") or []:
        fid = _FEATURE_TO_FACTOR_ID.get(f["id"], str(f["id"]).lower())
        direction = f.get("direction")
        if direction not in {"increases_risk", "decreases_risk"}:
            direction = "increases_risk"
        top_factors.append(
            {
                "id": fid,
                "label": f.get("label") or fid,
                "direction": direction,
                "importance": round(float(f.get("share") or f.get("importance") or 0), 4),
                "patient_value": f"{f.get('patient_value')}",
                "unit": f.get("unit") or None,
                "note": "Lokale bijdrage uit final model A (elastic-net, coef × geschaalde waarde).",
            }
        )
    updated["top_factors"] = top_factors

    # keep patient anthropometrics in sync with slider
    height_m = height_cm / 100.0
    new_bmi = body_weight / (height_m**2)
    patient["weight_kg"] = round(body_weight, 1)
    patient["bmi"] = round(new_bmi, 1)
    snap = patient.setdefault("snapshot", {})
    snap["bmi"] = f"{new_bmi:.1f}"
    snap["weight"] = f"{body_weight:.1f} kg"
    if feats.get("WAIST_T1") is not None:
        snap["waist"] = f"{float(feats['WAIST_T1']):.0f} cm"

    base_bmi = float(base.get("BMI_T1") or new_bmi)
    live_waist = None
    if feats.get("WAIST_T1") is not None:
        live_waist = float(feats["WAIST_T1"])
    waist_changed = (
        waist_cm is not None and abs(float(waist_cm) - body["waist_cm"]) >= 0.5
    )
    updated["whatif"] = {
        "weight_kg": round(body_weight, 1),
        "bmi": round(new_bmi, 1),
        "bri": round(body_roundness_index(float(live_waist or body["waist_cm"]), height_cm), 2),
        "height_cm": height_cm,
        "waist_cm": round(live_waist, 0) if live_waist is not None else None,
        "delta_kg": round(body_weight - body["weight_kg"], 1),
        "delta_bmi": round(new_bmi - body["bmi"], 2),
        "active": abs(body_weight - body["weight_kg"]) >= 0.25 or waist_changed,
        "mode": "live_model",
    }
    updated["live_model"] = {
        "enabled": True,
        "model_a": MODEL_A_FILE,
        "model_b": MODEL_B_FILE,
        "features_used": FEATURE_COLS,
    }
    return updated
