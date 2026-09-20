"""Mock buddy helpers: fixture loading, coaching copy, medical-question guardrails."""

from __future__ import annotations

import copy
import json
import os
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
FIXTURES_DIR = ROOT / "fixtures"
EXAMPLE_CONTRACT = ROOT / "contract.example.json"
SYSTEM_PROMPT_FILE = ROOT / "prompts" / "boris_system.md"
SESSIE_CONTEXT_TOKEN = "{SESSIE_CONTEXT}"

RISK_ORDER = {"low": 0, "medium": 1, "high": 2}

THEME_META = {
    "sport": {"label": "Beweging", "token": "sport"},
    "food": {"label": "Voeding", "token": "food"},
    "sleep": {"label": "Slaap", "token": "sleep"},
    "smoking": {"label": "Rookvrij", "token": "smoking"},
    "alcohol": {"label": "Alcohol", "token": "alcohol"},
}

FACTOR_DIRECTION_NL = {
    "increases_risk": "verhoogt je risico op diabetes",
    "decreases_risk": "verlaagt je risico op diabetes",
}

RISK_BAND_NL = {
    "low": "laag",
    "medium": "middel",
    "high": "hoog",
}

ACTIONABLE_THEME = {
    "sports": "sport",
    "cycle_commute": "sport",
    "bmi": "sport",
    "bri": "sport",
    "waist": "sport",
    "weight": "sport",
    "kcal": "food",
    "cho": "food",
    "tgl": "food",
    "hdc": "food",
    "ldc": "food",
    "hbac": "food",
    "sleep": "sleep",
    "smoking": "smoking",
    "alcohol": "alcohol",
}

FACTOR_LABEL_NL = {
    "bmi": "BMI",
    "bri": "BRI",
    "weight": "Gewicht",
    "waist": "Tailleomvang",
    "hbac": "HbA1c",
    "hba1c": "HbA1c",
    "sports": "Sport / beweging",
    "family_t2dm": "Familiegeschiedenis type 2 diabetes",
    "sleep": "Slaap",
    "smoking": "Roken",
    "alcohol": "Alcoholpatroon",
    "cycle_commute": "Fietsen naar werk",
    "kcal": "Energie-inname",
}

# Patient-facing titles. Internal ids stay t1_t2 / t1_t3 (HbA1c > 6.5% mock proxy).
PATIENT_RISK_COPY = {
    "t1_t2": {
        "title": "Risico op diabetes over 5 jaar",
        "subtitle": "Korte-termijn uitkomst (model A). Geen diagnose.",
    },
    "t1_t3": {
        "title": "Lange-termijn risico op diabetes",
        "subtitle": "Demo-proxy: kans dat HbA1c boven 6,5% uitkomt. Geen diagnose.",
    },
}

# What-if heuristic (transparent mock — not a trained model):
#   BMI = weight_kg / (height_m ** 2)
#   short_term = clip(base_short + 0.025 * (BMI - BMI0), 0.02, 0.95)
#   long_term  = clip(base_long  + 0.035 * (BMI - BMI0), 0.03, 0.97)
# Long-term moves a bit more so the two cards stay distinct in the demo.
# BMI factor: importance = clip(base + 0.045 * (BMI - BMI0), 0.04, 0.70);
#   direction flips at BMI 25 (below → lowers, at/above → raises).
# Waist tracks weight unless the patient edits it:
#   tracked = cm0 + 0.7 * (kg - kg0)
#   extra_cm = cm_user - tracked   # 0 when the slider only follows weight
#   short += 0.004 * extra_cm ; long += 0.006 * extra_cm
#   importance = clip(base + 0.012 * (cm_user - cm0), 0.04, 0.50).
# Extra lifestyle levers (same clip ranges; modest, intuitive, not clinical):
#   Movement per 30 min/week: short += -0.008 * d_move ; long += -0.011 * d_move
#   Sleep per hour/night:     short += -0.012 * d_sleep ; long += -0.016 * d_sleep
#   Sugary drinks per drink/week: short += 0.006 * d_drinks ; long += 0.008 * d_drinks
SHORT_TERM_BMI_COEF = 0.025
LONG_TERM_BMI_COEF = 0.035
BMI_FACTOR_COEF = 0.045
WAIST_CM_PER_KG = 0.7
WAIST_FACTOR_COEF = 0.012
WAIST_EXTRA_SHORT_COEF = 0.004
WAIST_EXTRA_LONG_COEF = 0.006
BMI_DIRECTION_PIVOT = 25.0
WEIGHT_LINKED_FACTORS = {"bmi", "waist", "weight"}
MOVE_UNIT_MIN = 30.0
SHORT_TERM_MOVE_COEF = -0.008
LONG_TERM_MOVE_COEF = -0.011
SPORTS_FACTOR_COEF = 0.028
SHORT_TERM_SLEEP_COEF = -0.012
LONG_TERM_SLEEP_COEF = -0.016
SLEEP_FACTOR_COEF = 0.035
SHORT_TERM_DRINK_COEF = 0.006
LONG_TERM_DRINK_COEF = 0.008
KCAL_DRINK_FACTOR_COEF = 0.018
DEFAULT_MOVE_MIN_WEEK = 60.0
DEFAULT_SLEEP_HOURS = 7.0
DEFAULT_SUGARY_DRINKS_WEEK = 4.0
WAIST_PIVOT_CM = 88.0
MOVE_PROTECT_MIN = 150.0
MOVE_RISK_MIN = 40.0
SLEEP_PROTECT_HOURS = 7.0
SLEEP_RISK_HOURS = 6.0

# Lifestyle coaching only. Medical / diagnosis / medication / triage → deflect.
_MEDICAL_RE = re.compile(
    r"\b("
    r"medicin\w*|medication\w*|meds|pill\w*|tablet\w*|drug\w*|dosage|dose|"
    r"prescrib\w*|prescription|pharmacy|"
    r"metformin\w*|insulin\w*|ozempic|wegovy|semaglutide|statin\w*|glp-?1|"
    r"diagnos\w*|diabetic|do i have|am i sick|"
    r"triage|emergenc\w*|chest pain|ambulance|a&e|er visit|hospital|"
    r"blood test result|lab result|treat my|cure|symptom\w*|"
    # Dutch
    r"medicijn\w*|geneesmiddel\w*|voorschrijf\w*|voorschrift|"
    r"apotheek|dosering|pilletje\w*|tabletten|"
    r"diagnose\w*|heb ik diabetes|ben ik ziek|"
    r"spoed|ambulance|hartklacht\w*|pijn op de borst|"
    r"bloeduitslag|labuitslag|kuur|symptoom\w*|klachten|"
    r"negeer (je|alle) (regels|instructies)|jailbreak|DAN mode|"
    r"ignore (your|all) (rules|instructions)|system prompt"
    r")\b",
    re.IGNORECASE,
)

DEFLECT_MESSAGE = (
    "Ik ben een leefstijl-buddy, geen zorgverlener. Ik mag niet diagnosticeren, "
    "medicatie adviseren of triëren. Vragen over medicijnen, uitslagen of "
    "klachten horen bij je arts of praktijkondersteuner. Wel kan ik helpen "
    "met beweging, eten, slapen, roken en alcohol."
)
CHAT_TOPICS = "wandelen, eten, slapen, roken of alcohol"
CHAT_PLACEHOLDER = "Wandelen, eten, slapen, roken, alcohol…"
EMPTY_QUESTION_MESSAGE = (
    f"Stel een vraag over een dagelijkse gewoonte — {CHAT_TOPICS}."
)


def load_payload(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_personas() -> list[dict[str, Any]]:
    # Skip persona-*-features.json (model feature snapshots for live overlay)
    paths = sorted(
        path for path in FIXTURES_DIR.glob("persona-*.json")
        if not path.name.endswith("-features.json")
    )
    if not paths:
        return [load_payload(EXAMPLE_CONTRACT)]
    return [load_payload(p) for p in paths]


def validate_payload(data: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    patient = data.get("patient") or {}
    if not patient.get("persona_id"):
        errors.append("missing patient.persona_id")
    target = data.get("target") or {}
    if target.get("threshold") != ">6.5%":
        errors.append("target.threshold must be >6.5%")
    risks = data.get("risks") or []
    ids = {r.get("id") for r in risks}
    if ids != {"t1_t2", "t1_t3"}:
        errors.append("risks must include t1_t2 and t1_t3 only")
    for risk in risks:
        score = risk.get("risk_score")
        label = risk.get("risk_label")
        if not isinstance(score, (int, float)) or not 0 <= float(score) <= 1:
            errors.append(f"invalid risk_score on {risk.get('id')}")
        if label not in RISK_ORDER:
            errors.append(f"risk_label must be low/medium/high on {risk.get('id')}")
    factors = data.get("top_factors") or []
    if not 3 <= len(factors) <= 5:
        errors.append("top_factors must have 3–5 items")
    for factor in factors:
        if factor.get("direction") not in {"increases_risk", "decreases_risk"}:
            errors.append(f"bad direction on {factor.get('id')}")
        imp = factor.get("importance")
        if not isinstance(imp, (int, float)) or not 0 <= float(imp) <= 1:
            errors.append(f"invalid importance on {factor.get('id')}")
    if not data.get("interventions"):
        errors.append("missing interventions")
    return errors


def is_medical_or_triage(text: str) -> bool:
    return bool(_MEDICAL_RE.search(text or ""))


def pct(score: float) -> str:
    return f"{round(float(score) * 100)}%"


def factor_display_label(factor: dict[str, Any]) -> str:
    return FACTOR_LABEL_NL.get(factor.get("id"), factor.get("label") or factor.get("id") or "")


def factor_direction_nl(direction: str) -> str:
    return FACTOR_DIRECTION_NL.get(direction, FACTOR_DIRECTION_NL["increases_risk"])


def risk_band_nl(label: str) -> str:
    return RISK_BAND_NL.get(label, label)


_HIDDEN_PATIENT_FACTOR_IDS = {
    "hbac",
    "hba1c",
    "hbac_t1",
    "hba1c_t1",
    "htn_med",
    "bkr",
    "map",
    "cho",
    "tgl",
    "hdc",
    "ldc",
    "hbf",
    "age",
    "education",
    "depression",
    "respiratory",
    "family_t2dm",
    "nhdc",
    "thr",
    "hip",
}
PATIENT_INFLUENCE_IDS = {
    "waist",
    "bri",
    "bmi",
    "weight",
    "sports",
    "cycle_commute",
    "sleep",
    "kcal",
    "smoking",
    "alcohol",
}
_HIDDEN_LABEL_NEEDLES = (
    "hba1c",
    "hbac",
    "creatinine",
    "kreatinine",
    "bloeddrukmedic",
    "medicatie",
    "heupomtrek",
)


def _is_hidden_patient_factor(factor: dict[str, Any]) -> bool:
    """Labs, meds and HbA1c may drive the model; patients do not see them."""
    fid = str(factor.get("id") or "").lower()
    label = str(factor.get("label") or "").lower()
    if fid in _HIDDEN_PATIENT_FACTOR_IDS:
        return True
    return any(needle in fid or needle in label for needle in _HIDDEN_LABEL_NEEDLES)


def patient_can_influence(factor: dict[str, Any]) -> bool:
    """Voor jou: only lifestyle / body-shape levers the patient can change."""
    if _is_hidden_patient_factor(factor):
        return False
    return str(factor.get("id") or "") in PATIENT_INFLUENCE_IDS


def top_local_factors(payload: dict[str, Any], limit: int = 3) -> list[dict[str, Any]]:
    """Patient-facing 'Voor jou': influenceable factors only, never HbA1c or labs.

    Live model A often ranks labs first. Keep those out of sight, then fill from
    the persona lifestyle card so each factor can still sit on a matching tile.
    """
    combined: list[dict[str, Any]] = []
    seen: set[str] = set()
    for factor in list(payload.get("top_factors") or []) + list(payload.get("persona_factors") or []):
        if not patient_can_influence(factor):
            continue
        fid = str(factor.get("id") or "")
        if not fid or fid in seen:
            continue
        seen.add(fid)
        combined.append(factor)
    return factor_share(combined)[:limit]


def intervention_for_factor(
    factor: dict[str, Any],
    payload: dict[str, Any],
    *,
    exclude: set[str] | None = None,
) -> dict[str, Any] | None:
    """Matching lifestyle card for one Voor-jou factor, skipping already-used cards."""
    skip = exclude or set()
    fid = factor.get("id")
    interventions = list(payload.get("interventions") or [])

    def unused(item: dict[str, Any]) -> bool:
        key = str(item.get("id") or item.get("theme") or "")
        return bool(key) and key not in skip

    for item in interventions:
        if unused(item) and fid in (item.get("linked_factors") or []):
            return item
    theme = ACTIONABLE_THEME.get(str(fid or ""))
    if theme:
        for item in interventions:
            if unused(item) and item.get("theme") == theme:
                return item
    return None


MOVEMENT_GROUP_IDS = frozenset({"bmi", "bri", "waist", "weight", "sports", "cycle_commute"})
BODY_MOVEMENT_IDS = frozenset({"bmi", "bri", "waist", "weight"})
FOOD_GROUP_IDS = frozenset({"kcal", "alcohol"})
SLEEP_GROUP_IDS = frozenset({"sleep"})
# Theme kicker is already "Beweging" — never also chip "Sport / beweging".
_STACKED_MOVEMENT_RE = re.compile(r"sport\s*/\s*beweging", re.IGNORECASE)

ADVICE_GROUPS: tuple[tuple[str, frozenset[str], tuple[str, ...]], ...] = (
    ("sport", MOVEMENT_GROUP_IDS, ("activity-walks",)),
    ("food", FOOD_GROUP_IDS, ("food-pattern", "food-maintain")),
    ("sleep", SLEEP_GROUP_IDS, ("sleep-wind-down", "sleep-keep")),
)


def visible_influenceable_factors(payload: dict[str, Any]) -> list[dict[str, Any]]:
    """Influenceable factors on this persona, labs and meds stripped."""
    combined: list[dict[str, Any]] = []
    seen: set[str] = set()
    for factor in list(payload.get("top_factors") or []) + list(payload.get("persona_factors") or []):
        if not patient_can_influence(factor):
            continue
        fid = str(factor.get("id") or "")
        if not fid or fid in seen:
            continue
        seen.add(fid)
        combined.append(factor)
    return factor_share(combined)


def _is_stacked_movement_chip(factor: dict[str, Any]) -> bool:
    """True when a chip would repeat the Beweging theme as 'sport / beweging'."""
    fid = str(factor.get("id") or "")
    if fid == "sports":
        return True
    blob = f"{factor.get('label') or ''} {factor_display_label(factor)}"
    return bool(_STACKED_MOVEMENT_RE.search(blob))


def _looks_like_commute_copy(factor: dict[str, Any]) -> bool:
    fid = str(factor.get("id") or "")
    if fid == "cycle_commute":
        return True
    blob = f"{factor.get('label') or ''} {factor.get('patient_value') or ''}".lower()
    return "woon-werk" in blob or "cycle" in fid


def _commute_chip_for_cycling(factors: list[dict[str, Any]]) -> dict[str, Any] | None:
    """Sam keeps woon-werk on one fiets chip, never as stacked Sport/Beweging."""
    commute = next(
        (
            factor
            for factor in factors
            if _looks_like_commute_copy(factor) and not _is_stacked_movement_chip(factor)
        ),
        None,
    )
    sports_commute = next(
        (
            factor
            for factor in factors
            if "woon-werk" in str(factor.get("patient_value") or "").lower()
        ),
        None,
    )
    if commute is None and sports_commute is None:
        return None
    chip = dict(commute or sports_commute)
    chip["id"] = "cycle_commute"
    chip["label"] = FACTOR_LABEL_NL["cycle_commute"]
    if sports_commute is not None and "woon-werk" not in str(chip.get("patient_value") or "").lower():
        chip["patient_value"] = sports_commute.get("patient_value")
        chip["unit"] = sports_commute.get("unit")
    return chip


def factors_for_advice_card(
    card: dict[str, Any],
    factors: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Chips on one tile: walk = body only; never stack Sport/Beweging.

    Pietje (activity-walks): BMI / BRI / taille / gewicht. No commute copy.
    Sam (keep-cycling): woon-werk / fietsen naar werk, plus body chips.
    Noor (keep-training): body chips; her title carries the training line.
    """
    card_id = str(card.get("id") or "")
    out: list[dict[str, Any]] = []
    if card_id == "keep-cycling":
        commute = _commute_chip_for_cycling(factors)
        if commute is not None:
            out.append(commute)
    for factor in factors:
        fid = str(factor.get("id") or "")
        if _is_stacked_movement_chip(factor) or _looks_like_commute_copy(factor):
            continue
        if card_id in {"activity-walks", "keep-cycling", "keep-training"}:
            if fid not in BODY_MOVEMENT_IDS:
                continue
        out.append(factor)
    return out


def _intervention_for_theme(
    payload: dict[str, Any],
    theme: str,
    preferred_ids: tuple[str, ...] = (),
) -> dict[str, Any] | None:
    cards = list(payload.get("interventions") or [])
    for pid in preferred_ids:
        for item in cards:
            if item.get("id") == pid:
                return item
    for item in cards:
        if item.get("theme") == theme:
            return item
    if theme == "food":
        for item in cards:
            if item.get("theme") == "alcohol":
                return item
    return None


def advice_why(theme: str, factors: list[dict[str, Any]]) -> str:
    """One short Dutch line per advice set — not the same risk sentence three times."""
    ids = {str(factor.get("id") or "") for factor in factors}
    if theme == "sport":
        if ids & {"bmi", "bri", "waist", "weight"}:
            return "Gewicht, taille en BRI horen bij één wandelstap."
        return "Bewegen dat je volhoudt, geen sportschema."
    if theme == "food":
        if "alcohol" in ids and "kcal" not in ids:
            return "Wat je drinkt, kun je zelf kiezen."
        return "Eten en suikerdrank kun je zelf kiezen."
    return "Een rustiger avond, geen slaaprecept."


def advice_sets(
    payload: dict[str, Any], limit: int = 3
) -> list[tuple[list[dict[str, Any]], dict[str, Any], str]]:
    """Voor jou: related factors grouped under one action tile.

    Skip a group when this persona has no factor in it. Do not invent factors.
    """
    by_id = {str(factor.get("id") or ""): factor for factor in visible_influenceable_factors(payload)}
    sets: list[tuple[list[dict[str, Any]], dict[str, Any], str]] = []
    for theme, ids, preferred in ADVICE_GROUPS:
        group = [by_id[fid] for fid in ids if fid in by_id]
        if not group:
            continue
        group.sort(key=lambda factor: float(factor.get("importance") or 0), reverse=True)
        card = _intervention_for_theme(payload, theme, preferred)
        if not card:
            continue
        sets.append((factors_for_advice_card(card, group), card, theme))
        if len(sets) >= limit:
            break
    return sets


def factor_action_pairs(
    payload: dict[str, Any], limit: int = 3
) -> list[tuple[dict[str, Any], dict[str, Any]]]:
    """Compatibility: first factor of each advice set + its action card."""
    return [(group[0], card) for group, card, _theme in advice_sets(payload, limit) if group]


def pick_primary_intervention(payload: dict[str, Any]) -> dict[str, Any] | None:
    """Strongest *actionable* factor → matching lifestyle card (Movement often wins)."""
    cards = interventions_for_local_factors(payload, limit=1)
    return cards[0] if cards else None


def secondary_interventions(payload: dict[str, Any], primary: dict[str, Any] | None, limit: int = 2) -> list[dict[str, Any]]:
    primary_id = (primary or {}).get("id")
    extras = [item for item in interventions_for_local_factors(payload, limit=limit + 1) if item.get("id") != primary_id]
    return extras[:limit]


def interventions_for_local_factors(payload: dict[str, Any], limit: int = 3) -> list[dict[str, Any]]:
    """Up to `limit` unique lifestyle cards, ordered by this person's strongest factors."""
    interventions = list(payload.get("interventions") or [])
    if not interventions:
        return []
    by_theme = {item.get("theme"): item for item in interventions}
    chosen: list[dict[str, Any]] = []
    seen: set[str] = set()

    def add(item: dict[str, Any] | None) -> None:
        if not item or len(chosen) >= limit:
            return
        key = str(item.get("id") or item.get("theme") or id(item))
        if key in seen:
            return
        seen.add(key)
        chosen.append(item)

    for factor in top_local_factors(payload, limit=8):
        fid = factor.get("id")
        theme = ACTIONABLE_THEME.get(fid)
        if theme:
            add(by_theme.get(theme))
        for item in interventions:
            if fid in (item.get("linked_factors") or []):
                add(item)
        if len(chosen) >= limit:
            return chosen
    for item in interventions:
        add(item)
        if len(chosen) >= limit:
            break
    return chosen


def linked_factor_labels(item: dict[str, Any], payload: dict[str, Any]) -> list[str]:
    labels_by_id = {
        factor.get("id"): factor_display_label(factor) for factor in payload.get("top_factors") or []
    }
    out = []
    for fid in item.get("linked_factors") or []:
        label = labels_by_id.get(fid) or FACTOR_LABEL_NL.get(fid) or fid
        if label not in out:
            out.append(label)
    return out


def factor_share(factors: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Normalize local importances so bars are comparable within this persona."""
    total = sum(float(f.get("importance") or 0) for f in factors) or 1.0
    out = []
    for factor in factors:
        item = dict(factor)
        item["share"] = float(factor.get("importance") or 0) / total
        out.append(item)
    out.sort(key=lambda f: f["share"], reverse=True)
    return out


def clip(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


def risk_band(score: float) -> str:
    if score < 0.20:
        return "low"
    if score < 0.55:
        return "medium"
    return "high"


def _as_float(value: Any, default: float | None = None) -> float | None:
    if value is None or value == "":
        return default
    if isinstance(value, str):
        token = value.replace(",", ".").strip().split()[0] if value.strip() else ""
        value = token
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _factor_measure(payload: dict[str, Any], factor_id: str) -> float | None:
    for factor in payload.get("top_factors") or []:
        if factor.get("id") == factor_id:
            return _as_float(factor.get("patient_value"))
    return None


def _estimated_waist_cm(bmi: float) -> float:
    """Fallback taille when a persona has no waist factor — not a clinical estimate."""
    return clip(70.0 + 2.5 * (bmi - 22.0), 60.0, 140.0)


def persona_body(payload: dict[str, Any]) -> dict[str, float]:
    """Baseline height / weight / BMI plus patient-changeable what-if levers."""
    patient = payload.get("patient") or {}
    snap = patient.get("snapshot") or {}
    height_cm = _as_float(patient.get("height_cm"), 170.0) or 170.0
    bmi = _as_float(patient.get("bmi")) or _as_float(snap.get("bmi"), 25.0) or 25.0
    weight_kg = _as_float(patient.get("weight_kg"))
    if weight_kg is None:
        weight_kg = bmi * (height_cm / 100.0) ** 2
    waist_cm = (
        _as_float(patient.get("waist_cm"))
        or _factor_measure(payload, "waist")
        or _as_float(snap.get("waist"))
    )
    if waist_cm is None:
        waist_cm = _estimated_waist_cm(bmi)
    move_min = (
        _as_float(patient.get("move_min_week"))
        or _as_float(snap.get("move_min_week"))
        or DEFAULT_MOVE_MIN_WEEK
    )
    sleep_hours = (
        _as_float(patient.get("sleep_hours"))
        or _as_float(snap.get("sleep_hours"))
        or DEFAULT_SLEEP_HOURS
    )
    drinks = (
        _as_float(patient.get("sugary_drinks_week"))
        or _as_float(snap.get("sugary_drinks_week"))
        or DEFAULT_SUGARY_DRINKS_WEEK
    )
    from model_adapter import body_roundness_index

    waist_cm = float(waist_cm)
    return {
        "height_cm": height_cm,
        "weight_kg": weight_kg,
        "bmi": bmi,
        "waist_cm": waist_cm,
        "bri": round(body_roundness_index(waist_cm, height_cm), 2),
        "move_min_week": float(move_min),
        "sleep_hours": float(sleep_hours),
        "sugary_drinks_week": float(drinks),
    }


def _risk_clip_range(risk_id: str) -> tuple[float, float]:
    return (0.02, 0.95) if risk_id == "t1_t2" else (0.03, 0.97)


def lifestyle_risk_delta(
    body: dict[str, float],
    *,
    move_min_week: float,
    sleep_hours: float,
    sugary_drinks_week: float,
) -> tuple[float, float]:
    """Mock short/long deltas for movement, sleep, and sugary drinks.

    Not a trained model. Per 30 beweegminuten, per slaapuur, per suikerdrank/week:
        short += -0.008 * d_move30 - 0.012 * d_sleep + 0.006 * d_drinks
        long  += -0.011 * d_move30 - 0.016 * d_sleep + 0.008 * d_drinks
    """
    d_move = (move_min_week - body["move_min_week"]) / MOVE_UNIT_MIN
    d_sleep = sleep_hours - body["sleep_hours"]
    d_drinks = sugary_drinks_week - body["sugary_drinks_week"]
    short = (
        SHORT_TERM_MOVE_COEF * d_move
        + SHORT_TERM_SLEEP_COEF * d_sleep
        + SHORT_TERM_DRINK_COEF * d_drinks
    )
    long = (
        LONG_TERM_MOVE_COEF * d_move
        + LONG_TERM_SLEEP_COEF * d_sleep
        + LONG_TERM_DRINK_COEF * d_drinks
    )
    return short, long


def _apply_lifestyle_factors(
    factors: list[dict[str, Any]],
    body: dict[str, float],
    *,
    move_min_week: float,
    sleep_hours: float,
    sugary_drinks_week: float,
) -> None:
    d_move = (move_min_week - body["move_min_week"]) / MOVE_UNIT_MIN
    d_sleep = sleep_hours - body["sleep_hours"]
    d_drinks = sugary_drinks_week - body["sugary_drinks_week"]
    for factor in factors:
        fid = factor.get("id")
        base_imp = float(factor.get("importance") or 0)
        if fid in {"sports", "cycle_commute"}:
            sign = 1.0 if fid == "cycle_commute" or factor.get("direction") == "decreases_risk" else -1.0
            if fid == "sports":
                if move_min_week >= MOVE_PROTECT_MIN:
                    factor["direction"] = "decreases_risk"
                    sign = 1.0
                elif move_min_week <= MOVE_RISK_MIN:
                    factor["direction"] = "increases_risk"
                    sign = -1.0
            factor["importance"] = round(
                clip(base_imp + sign * SPORTS_FACTOR_COEF * d_move, 0.04, 0.55), 4
            )
            if fid == "sports":
                factor["patient_value"] = f"{move_min_week:.0f}"
                factor["unit"] = "min/week"
            factor["note"] = "Mock what-if contribution — not a trained attribution."
        elif fid == "sleep":
            if sleep_hours >= SLEEP_PROTECT_HOURS:
                factor["direction"] = "decreases_risk"
                sign = 1.0
            elif sleep_hours <= SLEEP_RISK_HOURS:
                factor["direction"] = "increases_risk"
                sign = -1.0
            else:
                sign = 1.0 if factor.get("direction") == "decreases_risk" else -1.0
            factor["importance"] = round(
                clip(base_imp + sign * SLEEP_FACTOR_COEF * d_sleep, 0.04, 0.45), 4
            )
            factor["patient_value"] = f"{sleep_hours:.1f}"
            factor["unit"] = "uur"
            factor["note"] = "Mock what-if contribution — not a trained attribution."
        elif fid == "kcal":
            factor["importance"] = round(
                clip(base_imp + KCAL_DRINK_FACTOR_COEF * d_drinks, 0.04, 0.40), 4
            )
            factor["note"] = "Mock what-if contribution — not a trained attribution."


def _whatif_is_active(
    *,
    delta_kg: float,
    waist_cm: float,
    waist0: float,
    move_min_week: float,
    move0: float,
    sleep_hours: float,
    sleep0: float,
    sugary_drinks_week: float,
    drinks0: float,
) -> bool:
    return (
        abs(delta_kg) >= 0.25
        or abs(waist_cm - waist0) >= 0.5
        or abs(move_min_week - move0) >= 5
        or abs(sleep_hours - sleep0) >= 0.25
        or abs(sugary_drinks_week - drinks0) >= 0.5
    )


def apply_weight_whatif(
    payload: dict[str, Any],
    *,
    weight_kg: float | None = None,
    bmi: float | None = None,
    waist_cm: float | None = None,
    move_min_week: float | None = None,
    sleep_hours: float | None = None,
    sugary_drinks_week: float | None = None,
) -> dict[str, Any]:
    """Return a copy of the persona with mock risks and changeable levers updated.

    Formula (documented for the demo; not a clinical model):
        BMI = kg / m^2
        short = clip(base_short + 0.025 * dBMI + lifestyle_short + 0.004 * extra_cm, 0.02, 0.95)
        long  = clip(base_long  + 0.035 * dBMI + lifestyle_long  + 0.006 * extra_cm, 0.03, 0.97)
        extra_cm = waist_user - (waist0 + 0.7 * dkg)  # 0 when taille only follows gewicht
        lifestyle: see lifestyle_risk_delta
        BMI bar grows/shrinks by 0.045 * dBMI; waist bar by 0.012 * dcm.
    """
    updated = copy.deepcopy(payload)
    body = persona_body(payload)
    height_m = body["height_cm"] / 100.0
    if height_m <= 0:
        height_m = 1.7
    if bmi is not None and weight_kg is None:
        new_bmi = float(bmi)
        new_weight = new_bmi * height_m**2
    else:
        new_weight = float(weight_kg if weight_kg is not None else body["weight_kg"])
        new_bmi = new_weight / height_m**2
    new_weight = clip(new_weight, 35.0, 180.0)
    new_bmi = clip(new_bmi, 15.0, 55.0)
    delta_bmi = new_bmi - body["bmi"]
    delta_kg = new_weight - body["weight_kg"]
    tracked_waist = clip(body["waist_cm"] + WAIST_CM_PER_KG * delta_kg, 50.0, 180.0)
    if waist_cm is None:
        new_waist = tracked_waist
    else:
        new_waist = clip(float(waist_cm), 50.0, 180.0)
    extra_waist = new_waist - tracked_waist
    new_move = clip(
        float(move_min_week if move_min_week is not None else body["move_min_week"]),
        0.0,
        420.0,
    )
    new_sleep = clip(
        float(sleep_hours if sleep_hours is not None else body["sleep_hours"]),
        4.0,
        10.0,
    )
    new_drinks = clip(
        float(
            sugary_drinks_week
            if sugary_drinks_week is not None
            else body["sugary_drinks_week"]
        ),
        0.0,
        21.0,
    )
    life_short, life_long = lifestyle_risk_delta(
        body,
        move_min_week=new_move,
        sleep_hours=new_sleep,
        sugary_drinks_week=new_drinks,
    )

    for risk in updated.get("risks") or []:
        base = float(risk["risk_score"])
        coef = SHORT_TERM_BMI_COEF if risk.get("id") == "t1_t2" else LONG_TERM_BMI_COEF
        waist_coef = (
            WAIST_EXTRA_SHORT_COEF if risk.get("id") == "t1_t2" else WAIST_EXTRA_LONG_COEF
        )
        extra = (life_short if risk.get("id") == "t1_t2" else life_long) + waist_coef * extra_waist
        lo, hi = _risk_clip_range(risk.get("id"))
        score = clip(base + coef * delta_bmi + extra, lo, hi)
        copy_bits = PATIENT_RISK_COPY.get(risk.get("id"), {})
        risk["risk_score"] = round(score, 4)
        risk["risk_label"] = risk_band(score)
        risk["horizon"] = copy_bits.get("title", risk.get("horizon"))
        risk["label"] = copy_bits.get("subtitle", risk.get("label"))

    for factor in updated.get("top_factors") or []:
        fid = factor.get("id")
        if fid not in WEIGHT_LINKED_FACTORS:
            continue
        base_imp = float(factor.get("importance") or 0)
        if fid in {"bmi", "weight"}:
            factor["importance"] = round(clip(base_imp + BMI_FACTOR_COEF * delta_bmi, 0.04, 0.70), 4)
            factor["direction"] = (
                "increases_risk" if new_bmi >= BMI_DIRECTION_PIVOT else "decreases_risk"
            )
            if fid == "bmi":
                factor["patient_value"] = f"{new_bmi:.1f}"
                factor["unit"] = "kg/m²"
            else:
                factor["patient_value"] = f"{new_weight:.1f}"
                factor["unit"] = "kg"
            factor["note"] = "Mock what-if contribution — not a trained attribution."
        elif fid == "waist":
            d_waist = new_waist - body["waist_cm"]
            factor["importance"] = round(clip(base_imp + WAIST_FACTOR_COEF * d_waist, 0.04, 0.50), 4)
            factor["direction"] = (
                "increases_risk" if new_waist >= WAIST_PIVOT_CM else "decreases_risk"
            )
            factor["patient_value"] = f"{new_waist:.0f}"
            factor["unit"] = "cm"
            factor["note"] = (
                "Mock what-if: taille is bewerkbaar; volgt anders 0,7 cm per kg."
            )

    _apply_lifestyle_factors(
        updated.get("top_factors") or [],
        body,
        move_min_week=new_move,
        sleep_hours=new_sleep,
        sugary_drinks_week=new_drinks,
    )

    patient = updated.setdefault("patient", {})
    snap = patient.setdefault("snapshot", {})
    snap["bmi"] = f"{new_bmi:.1f}"
    snap["weight"] = f"{new_weight:.1f} kg"
    snap["waist"] = f"{new_waist:.0f} cm"
    snap["move_min_week"] = f"{new_move:.0f}"
    snap["sleep_hours"] = f"{new_sleep:.1f}"
    snap["sugary_drinks_week"] = f"{new_drinks:.0f}"
    patient["weight_kg"] = round(new_weight, 1)
    patient["bmi"] = round(new_bmi, 1)
    patient["waist_cm"] = round(new_waist, 0)
    patient["move_min_week"] = round(new_move, 0)
    patient["sleep_hours"] = round(new_sleep, 1)
    patient["sugary_drinks_week"] = round(new_drinks, 0)
    from model_adapter import body_roundness_index

    updated["whatif"] = {
        "weight_kg": round(new_weight, 1),
        "bmi": round(new_bmi, 1),
        "bri": round(body_roundness_index(new_waist, body["height_cm"]), 2),
        "height_cm": body["height_cm"],
        "waist_cm": round(new_waist, 0),
        "move_min_week": round(new_move, 0),
        "sleep_hours": round(new_sleep, 1),
        "sugary_drinks_week": round(new_drinks, 0),
        "delta_kg": round(delta_kg, 1),
        "delta_bmi": round(delta_bmi, 2),
        "active": _whatif_is_active(
            delta_kg=delta_kg,
            waist_cm=new_waist,
            waist0=body["waist_cm"],
            move_min_week=new_move,
            move0=body["move_min_week"],
            sleep_hours=new_sleep,
            sleep0=body["sleep_hours"],
            sugary_drinks_week=new_drinks,
            drinks0=body["sugary_drinks_week"],
        ),
        "mode": "mock",
    }
    return updated


def apply_lifestyle_overlay(
    payload: dict[str, Any],
    baseline: dict[str, Any],
    *,
    move_min_week: float,
    sleep_hours: float,
    sugary_drinks_week: float,
) -> dict[str, Any]:
    """Mock-overlay levers the live 22-col model has no column for.

    Waist/weight should already be in `payload` (live BMI + BRI). This only adds
    movement, sleep, and sugary-drink deltas — same formula as lifestyle_risk_delta.
    """
    updated = copy.deepcopy(payload)
    body = persona_body(baseline)
    new_move = clip(float(move_min_week), 0.0, 420.0)
    new_sleep = clip(float(sleep_hours), 4.0, 10.0)
    new_drinks = clip(float(sugary_drinks_week), 0.0, 21.0)
    life_short, life_long = lifestyle_risk_delta(
        body,
        move_min_week=new_move,
        sleep_hours=new_sleep,
        sugary_drinks_week=new_drinks,
    )
    for risk in updated.get("risks") or []:
        add = life_short if risk.get("id") == "t1_t2" else life_long
        lo, hi = _risk_clip_range(risk.get("id"))
        score = clip(float(risk.get("risk_score") or 0) + add, lo, hi)
        risk["risk_score"] = round(score, 4)
        risk["risk_label"] = risk_band(score)
    _apply_lifestyle_factors(
        updated.get("top_factors") or [],
        body,
        move_min_week=new_move,
        sleep_hours=new_sleep,
        sugary_drinks_week=new_drinks,
    )
    whatif = updated.setdefault("whatif", {})
    whatif["move_min_week"] = round(new_move, 0)
    whatif["sleep_hours"] = round(new_sleep, 1)
    whatif["sugary_drinks_week"] = round(new_drinks, 0)
    extras_on = _whatif_is_active(
        delta_kg=0.0,
        waist_cm=body["waist_cm"],
        waist0=body["waist_cm"],
        move_min_week=new_move,
        move0=body["move_min_week"],
        sleep_hours=new_sleep,
        sleep0=body["sleep_hours"],
        sugary_drinks_week=new_drinks,
        drinks0=body["sugary_drinks_week"],
    )
    whatif["active"] = bool(whatif.get("active") or extras_on)
    whatif["overlay"] = "mock_lifestyle"
    return updated


def template_reply(question: str, payload: dict[str, Any]) -> str:
    q = (question or "").lower()
    interventions = payload.get("interventions") or []
    theme_hits = {
        "sport": (
            "walk",
            "wandel",
            "sport",
            "beweeg",
            "beweg",
            "fiets",
            "move",
            "activ",
            "cycl",
            "bike",
            "exercise",
        ),
        "food": (
            "eat",
            "eet",
            "eten",
            "voeding",
            "maaltijd",
            "suiker",
            "food",
            "meal",
            "sugar",
            "diet",
            "plate",
        ),
        "sleep": ("sleep", "slaap", "bed", "avondritueel", "wind-down", "insomnia"),
        "smoking": ("smok", "rook", "roken", "sigaret", "cigarette", "vape"),
        "alcohol": ("alcohol", "bier", "wijn", "beer", "wine"),
    }
    for intervention in interventions:
        theme = intervention.get("theme")
        needles = theme_hits.get(theme, ())
        if any(n in q for n in needles):
            return (
                f"{intervention['title']}: {intervention['summary']} "
                "Dit is coaching, geen medisch advies."
            )
    coaching = (payload.get("coaching") or {}).get("template")
    if coaching:
        return coaching
    return (
        "Houd het klein: kies deze week één bewegingsgewoonte en één eetgewoonte "
        "die je kunt herhalen. Voor medicijnen of klachten blijf je bij je zorgverlener."
    )


OPENAI_MODEL = "gpt-4o-mini"
OPENAI_AUTH_MESSAGE = (
    "Die OpenAI-sleutel wordt niet geaccepteerd. Plak een geldige key "
    "(begint meestal met sk-) in de sidebar of in .streamlit/secrets.toml."
)


def resolve_openai_api_key(*candidates: str | None) -> str:
    """First non-empty candidate, then OPENAI_API_KEY from the environment."""
    for raw in candidates:
        if raw and str(raw).strip():
            return str(raw).strip()
    return os.environ.get("OPENAI_API_KEY", "").strip()


def openai_key_configured(*candidates: str | None) -> bool:
    return bool(resolve_openai_api_key(*candidates))


def load_default_system_prompt() -> str:
    return SYSTEM_PROMPT_FILE.read_text(encoding="utf-8")


def build_session_context(payload: dict[str, Any]) -> str:
    """Facts-only block for the current persona / what-if / tiles."""
    patient = payload.get("patient") or {}
    name = patient.get("display_name") or "daar"
    persona_id = patient.get("persona_id") or ""
    source = payload.get("source") or "mock"
    risks = {r.get("id"): r for r in payload.get("risks") or []}
    short = risks.get("t1_t2") or {}
    factor_lines = [
        f"- {factor_display_label(factor)}: {factor_direction_nl(factor.get('direction'))}"
        for factor in top_local_factors(payload, 3)
    ] or ["- (geen lokale factoren)"]
    tile_lines = [
        f"- {item.get('title')}"
        for item in interventions_for_local_factors(payload, 3)
    ] or ["- (geen tegels)"]
    whatif = payload.get("whatif") or {}
    body = persona_body(payload)
    weight = whatif.get("weight_kg", patient.get("weight_kg", body["weight_kg"]))
    waist = whatif.get("waist_cm", patient.get("waist_cm", body["waist_cm"]))
    bri = whatif.get("bri", body.get("bri"))
    move = whatif.get("move_min_week", patient.get("move_min_week", body["move_min_week"]))
    sleep = whatif.get("sleep_hours", patient.get("sleep_hours", body["sleep_hours"]))
    drinks = whatif.get(
        "sugary_drinks_week",
        patient.get("sugary_drinks_week", body["sugary_drinks_week"]),
    )
    if weight is not None and waist is not None:
        bri_txt = f"{float(bri):.2f}" if bri is not None else "—"
        whatif_line = (
            f"What-if: {float(weight):.1f} kg · BRI {bri_txt} · "
            f"taille {float(waist):.0f} cm · {float(move):.0f} min/week · "
            f"{float(sleep):.1f} uur slaap · {float(drinks):.0f} suikerdranken/week"
        )
    else:
        whatif_line = "What-if: (geen gewicht)"
    disclaimer = payload.get("disclaimer") or "Demo-proxy, geen diagnose."
    return "\n".join(
        [
            f"Persona: {name} ({persona_id})",
            f"Bron: {source}",
            f"Risico over 5 jaar: {pct(short.get('risk_score') or 0)} "
            f"({risk_band_nl(short.get('risk_label') or 'medium')})",
            "Voor jou:",
            *factor_lines,
            "Doe dit:",
            *tile_lines,
            whatif_line,
            f"Disclaimer: {disclaimer}",
        ]
    )


def render_system_prompt(
    payload: dict[str, Any],
    template: str | None = None,
) -> str:
    """Static character prompt + current demo card. Barbecue Bob split."""
    raw = template.strip() if template and template.strip() else load_default_system_prompt()
    context = build_session_context(payload)
    if SESSIE_CONTEXT_TOKEN in raw:
        return raw.replace(SESSIE_CONTEXT_TOKEN, context)
    return raw.rstrip() + "\n\n## Sessie-context\n\n" + context


def _coach_system_prompt(payload: dict[str, Any], template: str | None = None) -> str:
    return render_system_prompt(payload, template)


def optional_llm_reply(
    question: str,
    payload: dict[str, Any],
    fallback: str,
    *,
    api_key: str | None = None,
    history: list[tuple[str, str]] | None = None,
    system_prompt: str | None = None,
) -> tuple[str, str]:
    """Return (text, source). Uses the official OpenAI client when a key is present."""
    key = resolve_openai_api_key(api_key)
    if not key:
        return fallback, "template"

    try:
        from openai import OpenAI
    except ImportError:
        return fallback, "template"

    messages: list[dict[str, str]] = [
        {"role": "system", "content": render_system_prompt(payload, system_prompt)}
    ]
    for prior_q, prior_a in (history or [])[-6:]:
        if prior_q:
            messages.append({"role": "user", "content": prior_q})
        if prior_a:
            messages.append({"role": "assistant", "content": prior_a})
    messages.append({"role": "user", "content": question})

    try:
        client = OpenAI(api_key=key, timeout=12.0)
        response = client.chat.completions.create(
            model=os.environ.get("OPENAI_MODEL", OPENAI_MODEL),
            temperature=0.4,
            messages=messages,
        )
        text = ((response.choices[0].message.content) or "").strip()
        return text or fallback, "openai"
    except Exception as exc:
        blob = f"{type(exc).__name__} {exc}".lower()
        if any(token in blob for token in ("auth", "401", "invalid_api_key", "incorrect api key")):
            return OPENAI_AUTH_MESSAGE, "openai-auth"
        return fallback, "openai-error"


# Output filter: real medical advice only. Bare start/neem/stop/take are
# normal walk/food Dutch ("Start bij het plantsoen", "Neem de gracht").
_MEDICAL_ADVICE_OUT = re.compile(
    r"\b("
    r"dose|dosering|mg\b|prescribe|voorschrijf\w*|"
    r"diagnos\w*|"
    r"metformin\w*|insulin\w*|"
    r"medicijn\w*|geneesmiddel\w*|prescription"
    r")\b",
    re.IGNORECASE,
)


def _looks_like_medical_advice(text: str) -> bool:
    return bool(_MEDICAL_ADVICE_OUT.search(text or ""))


def answer_question(
    question: str,
    payload: dict[str, Any],
    *,
    api_key: str | None = None,
    history: list[tuple[str, str]] | None = None,
    system_prompt: str | None = None,
) -> tuple[str, str]:
    text = (question or "").strip()
    if not text:
        return EMPTY_QUESTION_MESSAGE, "empty"
    if is_medical_or_triage(text):
        return DEFLECT_MESSAGE, "guardrail"
    fallback = template_reply(text, payload)
    reply, source = optional_llm_reply(
        text,
        payload,
        fallback,
        api_key=api_key,
        history=history,
        system_prompt=system_prompt,
    )
    if source == "openai" and _looks_like_medical_advice(reply):
        return DEFLECT_MESSAGE, "guardrail-post"
    return reply, source
