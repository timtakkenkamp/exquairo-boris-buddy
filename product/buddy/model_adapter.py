"""Adapter: final A/B joblib models → Boris buddy risk payload."""

from __future__ import annotations

import math
from functools import lru_cache
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
MODELS_DIR = REPO_ROOT / "models"

MODEL_A_FILE = "model_a_best_logreg_elasticnet_no_spline_run1_final.joblib"
MODEL_B_FILE = "model_b_best_xgboost_no_spline_run1_final.joblib"

# Exact columns expected by the final no-spline pipelines (passthrough order).
FEATURE_COLS: list[str] = [
    "AGE_T1",
    "BKR_T1",
    "BMI_T1",
    "BRI_T1",
    "DEPRESSION_T1",
    "EDUCATION_LOWER_T1",
    "EDUCATION_LOWER_T1_MISSING",
    "HBAC_T1",
    "HBF_T1",
    "HBF_T1_MISSING",
    "HIP_T1",
    "HTN_MED_T1",
    "HTN_MED_T1_MISSING",
    "LDC_T1",
    "MAP_T1",
    "MAP_T1_MISSING",
    "NHDC_T1",
    "RESPIRATORY_DISEASE_T1",
    "RESPIRATORY_DISEASE_T1_MISSING",
    "SPORTS_T1",
    "SPORTS_T1_MISSING",
    "THR_T1",
]

_CORE_WITH_MISSING_FLAG = [
    "EDUCATION_LOWER_T1",
    "HBF_T1",
    "HTN_MED_T1",
    "MAP_T1",
    "RESPIRATORY_DISEASE_T1",
    "SPORTS_T1",
]

_FRIENDLY = {
    "AGE_T1": ("Leeftijd", "jaar"),
    "BMI_T1": ("BMI", "kg/m²"),
    "BRI_T1": ("Body roundness (BRI)", ""),
    "HIP_T1": ("Heupomtrek", "cm"),
    "WAIST_T1": ("Taille", "cm"),
    "EDUCATION_LOWER_T1": ("Lagere opleiding", ""),
    "HBF_T1": ("Vetpercentage", "%"),
    "MAP_T1": ("Bloeddruk (MAP)", "mmHg"),
    "HTN_MED_T1": ("Bloeddrukmedicatie", ""),
    "BKR_T1": ("Kreatinine", ""),
    "NHDC_T1": ("Non-HDL cholesterol", "mmol/L"),
    "HBAC_T1": ("HbA1c", "%"),
    "LDC_T1": ("LDL", "mmol/L"),
    "THR_T1": ("TG/HDL-ratio", ""),
    "RESPIRATORY_DISEASE_T1": ("Luchtwegziekte", ""),
    "SPORTS_T1": ("Sport", ""),
    "DEPRESSION_T1": ("Depressie", ""),
}


def body_roundness_index(waist_cm: float, height_cm: float) -> float:
    """Thomas BRI; waist and height in cm."""
    height_m = float(height_cm) / 100.0
    waist_m = float(waist_cm) / 100.0
    denom = (0.5 * height_m) ** 2
    if denom <= 0:
        return 0.0
    inner = 1.0 - ((waist_m / (2.0 * math.pi)) ** 2) / denom
    inner = max(0.0, min(1.0, inner))
    return float(364.2 - 365.5 * math.sqrt(inner))


def waist_cm_from_bri(bri: float, height_cm: float) -> float:
    """Invert Thomas BRI to waist (cm). Height stays fixed."""
    height_m = float(height_cm) / 100.0
    denom = (0.5 * height_m) ** 2
    if denom <= 0:
        return 0.0
    ratio = (364.2 - float(bri)) / 365.5
    ratio = max(0.0, min(1.0, ratio))
    inner = ratio**2
    frac = max(0.0, 1.0 - inner)
    waist_m = 2.0 * math.pi * math.sqrt(frac * denom)
    return float(waist_m * 100.0)


@lru_cache(maxsize=1)
def load_models(
    models_dir: str | None = None,
) -> tuple[Any, Any]:
    root = Path(models_dir) if models_dir else MODELS_DIR
    model_a = joblib.load(root / MODEL_A_FILE)
    model_b = joblib.load(root / MODEL_B_FILE)
    return model_a, model_b


def models_on_disk(models_dir: str | Path | None = None) -> bool:
    root = Path(models_dir) if models_dir else MODELS_DIR
    return (root / MODEL_A_FILE).exists() and (root / MODEL_B_FILE).exists()


def _float(value: Any, default: float = float("nan")) -> float:
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return default
    try:
        if pd.isna(value):
            return default
    except Exception:
        pass
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def derive_engineered_fields(row: pd.Series | dict[str, Any]) -> dict[str, Any]:
    """Fill BRI / non-HDL / TG-HDL from raw T1 fields when the finals need them."""
    s = pd.Series(row) if not isinstance(row, pd.Series) else row
    data = {k: s[k] for k in s.index}
    cho = _float(s.get("CHO_T1"))
    hdc = _float(s.get("HDC_T1"))
    tgl = _float(s.get("TGL_T1"))
    if _needs_engineered(s.get("NHDC_T1")) and not pd.isna(cho) and not pd.isna(hdc):
        data["NHDC_T1"] = cho - hdc
    if _needs_engineered(s.get("THR_T1")) and not pd.isna(tgl) and hdc and hdc > 0:
        data["THR_T1"] = tgl / hdc
    waist = _float(s.get("WAIST_T1"))
    height = _float(s.get("HEIGHT_T1"))
    if pd.isna(height):
        height = _float(s.get("height_cm"))
    if _needs_engineered(s.get("BRI_T1")) and not pd.isna(waist) and not pd.isna(height):
        data["BRI_T1"] = body_roundness_index(waist, height)
    return data


def _needs_engineered(value: Any) -> bool:
    """Treat missing or placeholder 0 as unset so raw waist/lipids can fill BRI/NHDC/THR."""
    number = _float(value)
    return bool(pd.isna(number) or number == 0.0)


def prepare_features(row: pd.Series | dict[str, Any]) -> pd.DataFrame:
    """Build a 1×22 frame matching the final A/B ColumnTransformer."""
    derived = derive_engineered_fields(row)
    s = pd.Series(derived)
    data: dict[str, float] = {}
    for col in FEATURE_COLS:
        if col.endswith("_MISSING"):
            continue
        data[col] = _float(s.get(col))

    for core in _CORE_WITH_MISSING_FLAG:
        flag = f"{core}_MISSING"
        if flag in s.index and not pd.isna(_float(s.get(flag), default=float("nan"))):
            data[flag] = _float(s.get(flag), default=0.0)
        else:
            data[flag] = 1.0 if pd.isna(data.get(core, np.nan)) else 0.0
        if pd.isna(data.get(core, np.nan)):
            data[core] = 0.0

    for col in FEATURE_COLS:
        if col not in data or pd.isna(data[col]):
            data[col] = 0.0

    return pd.DataFrame([[data[c] for c in FEATURE_COLS]], columns=FEATURE_COLS)


def _local_factor_contributions(model: Any, X: pd.DataFrame, top_k: int = 5) -> list[dict[str, Any]]:
    """Local contributions from logreg (coef × scaled x) or tree importances."""
    clf = model.named_steps["clf"]
    pre = model.named_steps["preprocessor"]
    Xs = pre.transform(X)
    if hasattr(Xs, "toarray"):
        Xs = Xs.toarray()
    x = np.asarray(Xs).ravel()
    try:
        names = [n.split("__", 1)[-1] for n in pre.get_feature_names_out()]
    except Exception:
        names = FEATURE_COLS[: len(x)]

    if hasattr(clf, "coef_"):
        contrib = np.asarray(clf.coef_).ravel() * x
    else:
        importance = np.asarray(getattr(clf, "feature_importances_", np.ones_like(x))).ravel()
        contrib = importance * np.sign(x) * np.abs(x)

    items = []
    raw_lookup = {col: float(X.iloc[0][col]) for col in X.columns}
    for name, c in zip(names, contrib):
        if name.endswith("_MISSING"):
            continue
        label, unit = _FRIENDLY.get(name, (name, ""))
        items.append(
            {
                "id": name,
                "label": label,
                "unit": unit,
                "patient_value": raw_lookup.get(name, 0.0),
                "contribution": float(c),
                "direction": "increases_risk" if c > 0 else "decreases_risk",
            }
        )
    items.sort(key=lambda d: abs(d["contribution"]), reverse=True)
    top = items[:top_k]
    total = sum(abs(d["contribution"]) for d in top) or 1.0
    for d in top:
        d["share"] = abs(d["contribution"]) / total
    return top


def predict_diabetes_risks(
    row: pd.Series | dict[str, Any],
    *,
    models_dir: str | None = None,
    top_k: int = 5,
) -> dict[str, Any]:
    model_a, model_b = load_models(models_dir)
    X = prepare_features(row)
    p_a = float(model_a.predict_proba(X)[0, 1])
    p_b = float(model_b.predict_proba(X)[0, 1])
    factors = _local_factor_contributions(model_a, X, top_k=top_k)
    return {
        "schema_version": "0.4.0-final",
        "source": "final_model_a_logreg_b_xgboost",
        "risk_t1_t2": p_a,
        "risk_t1_t3": p_b,
        "risks": [
            {
                "id": "t1_t2",
                "label": "Korte termijn",
                "risk_score": p_a,
                "risk_label": _band(p_a),
            },
            {
                "id": "t1_t3",
                "label": "Lange termijn",
                "risk_score": p_b,
                "risk_label": _band(p_b),
            },
        ],
        "top_factors": factors,
        "features_used": FEATURE_COLS,
    }


def _band(p: float) -> str:
    if p < 0.1:
        return "low"
    if p < 0.25:
        return "medium"
    return "high"
