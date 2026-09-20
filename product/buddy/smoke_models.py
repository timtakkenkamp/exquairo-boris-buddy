"""Smoke-test final A/B models via model_adapter + persona overlay."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from buddy_lib import interventions_for_local_factors, load_personas
from live_model import models_available, overlay_live_predictions
from model_adapter import FEATURE_COLS, predict_diabetes_risks, prepare_features

ROOT = Path(__file__).resolve().parents[2]
FILTERED = ROOT / "data" / "processed" / "df_filtered.xlsx"
DEFAULT_HEIGHT_CM = 170.0


def _with_height(row: pd.Series) -> pd.Series:
    out = row.copy()
    if "HEIGHT_T1" not in out.index or pd.isna(out.get("HEIGHT_T1")):
        out["HEIGHT_T1"] = DEFAULT_HEIGHT_CM
    return out


def _assert_prob(value: float) -> None:
    assert 0.0 <= float(value) <= 1.0


def smoke_personas() -> list[dict]:
    assert models_available(), "final A/B joblibs missing under models/"
    results = []
    print("Smoke overlay (Pietje / Sam / Noor)\n")
    for payload in load_personas():
        patient = payload["patient"]
        live = overlay_live_predictions(payload)
        short = live["risks"][0]["risk_score"]
        long = live["risks"][1]["risk_score"]
        _assert_prob(short)
        _assert_prob(long)
        tiles = [c["theme"] for c in interventions_for_local_factors(live, 3)]
        assert live["source"] == "live_final_models"
        assert live["live_model"]["model_a"].endswith("_final.joblib")
        assert live["live_model"]["model_b"].endswith("_final.joblib")
        assert len(tiles) == 3
        print(
            f"[{patient['display_name']}] kort={short:.4f} lang={long:.4f} "
            f"tiles={tiles} factors={[f['id'] for f in live['top_factors'][:3]]}"
        )
        results.append(
            {
                "persona": patient["display_name"],
                "risk_t1_t2": short,
                "risk_t1_t3": long,
                "tiles": tiles,
                "top": [f["id"] for f in live["top_factors"]],
            }
        )
    return results


def smoke_filtered() -> list[dict]:
    if not FILTERED.exists():
        print(f"\nSkip excel smoke — missing {FILTERED}")
        return []
    df = pd.read_excel(FILTERED)
    ok = df["HBAC_T1"].notna() & df["BMI_T1"].notna()
    sub = df.loc[ok].copy()
    sub["bmi_q"] = pd.qcut(sub["BMI_T1"], 3, labels=["low_bmi", "mid_bmi", "high_bmi"])
    rows = []
    for label in ["low_bmi", "mid_bmi", "high_bmi"]:
        part = sub.loc[sub["bmi_q"] == label]
        rows.append(_with_height(part.iloc[len(part) // 2]))

    print("\nSmoke predict (3 rows from df_filtered.xlsx)\n")
    results = []
    for i, row in enumerate(rows, 1):
        out = predict_diabetes_risks(row, top_k=5)
        print(f"[{i}] BMI={row['BMI_T1']:.1f}  HBAC={row['HBAC_T1']:.2f}")
        print(f"    T1→T2 (kort)={out['risk_t1_t2']:.4f}  T1→T3 (lang)={out['risk_t1_t3']:.4f}")
        print(
            "    top factors: "
            + ", ".join(f"{f['label']} ({f['direction'][:3]})" for f in out["top_factors"][:3])
        )
        results.append(
            {
                "bmi": float(row["BMI_T1"]),
                "hbac": float(row["HBAC_T1"]),
                "risk_t1_t2": out["risk_t1_t2"],
                "risk_t1_t3": out["risk_t1_t3"],
                "top": [f["id"] for f in out["top_factors"]],
            }
        )
        bumped = row.copy()
        bumped["BMI_T1"] = float(row["BMI_T1"]) + 2.0
        out2 = predict_diabetes_risks(bumped, top_k=3)
        print(f"    what-if BMI+2 → kort={out2['risk_t1_t2']:.4f} lang={out2['risk_t1_t3']:.4f}")
        _assert_prob(out["risk_t1_t2"])
        _assert_prob(out["risk_t1_t3"])
        _assert_prob(out2["risk_t1_t2"])
        _assert_prob(out2["risk_t1_t3"])

    X = prepare_features(rows[0])
    assert list(X.columns) == FEATURE_COLS
    assert X.shape == (1, 22)
    assert float(X["BRI_T1"].iloc[0]) > 0
    return results


def main() -> None:
    persona_results = smoke_personas()
    excel_results = smoke_filtered()
    print("\nOK — final A/B smoke passed.")
    out_path = Path("/tmp/smoke_models_last.json")
    out_path.write_text(
        json.dumps({"personas": persona_results, "filtered": excel_results}, indent=2),
        encoding="utf-8",
    )
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
