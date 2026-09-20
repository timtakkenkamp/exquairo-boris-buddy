# Models (Tim’s buddy repo)

Joblib pipelines used by the live buddy overlay in `product/buddy/`.

| File | Role |
|------|------|
| `model_a_best_logreg_elasticnet_no_spline_run1_final.joblib` | **Final A** — short horizon (T1→T2), elastic-net logistic pipeline |
| `model_b_best_xgboost_no_spline_run1_final.joblib` | **Final B** — long horizon (T1→T3), XGBoost pipeline |

Both expect the same 22 T1 columns (including `BRI_T1`, `NHDC_T1`, `THR_T1` and five `*_MISSING` flags). The buddy adapter derives BRI / non-HDL / TG-HDL from waist, height, CHO, HDL and TG when those raw fields are present.

Older first-pass files (`model_{a,b}_best_logreg_elasticnet.joblib`) stay in this folder but are **not** used by the UI.

```bash
cd product/buddy && uv run python smoke_models.py
```
