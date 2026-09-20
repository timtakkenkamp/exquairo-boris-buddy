"""Boris buddy — 3-step Streamlit demo (mock fixtures or final A/B models)."""

from __future__ import annotations

import base64
from pathlib import Path

import streamlit as st

from buddy_lib import (
    CHAT_PLACEHOLDER,
    OPENAI_MODEL,
    THEME_META,
    WAIST_CM_PER_KG,
    answer_question,
    apply_lifestyle_overlay,
    apply_weight_whatif,
    clip,
    factor_display_label,
    load_default_system_prompt,
    load_personas,
    openai_key_configured,
    pct,
    persona_body,
    advice_sets,
    factors_for_advice_card,
    patient_can_influence,
    resolve_openai_api_key,
    risk_band_nl,
    validate_payload,
)
from intervention_pages import get_intervention_page
from live_model import models_available, overlay_live_predictions
from model_adapter import body_roundness_index

PERSONA_ORDER = ["persona-river", "persona-sam", "persona-noor"]
ASSETS = Path(__file__).resolve().parent / "assets"
MASCOT_FILE = ASSETS / "boris-mascot.png"

THEME_COLORS = {
    "sport": {"bar": "#6FBF4B", "soft": "#E4F6D8", "ink": "#2F7A28"},
    "food": {"bar": "#3D8BBF", "soft": "#DCEAF6", "ink": "#1A4A6E"},
    "sleep": {"bar": "#7BA3C9", "soft": "#E6F0F8", "ink": "#2A5270"},
    "smoking": {"bar": "#5B7C99", "soft": "#E4EBF1", "ink": "#2C4256"},
    "alcohol": {"bar": "#4AA3C7", "soft": "#D9F0F7", "ink": "#1E5A70"},
}

RISK_COLORS = {
    "low": {"ink": "#2F8A4A", "badge_bg": "#DFF3D8", "badge_ink": "#1F6B34", "bar": "#6FBF4B"},
    "medium": {"ink": "#C9862A", "badge_bg": "#F8E6C6", "badge_ink": "#8A5A12", "bar": "#E0A84A"},
    "high": {"ink": "#C45B4A", "badge_bg": "#F8D9D4", "badge_ink": "#8A3328", "bar": "#D46B5A"},
}

st.set_page_config(
    page_title="Boris · kleine stappen",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded",
)


def audience_mode() -> bool:
    """Zaalweergave via ?demo=1 — hides workshop controls, keeps the 3-step UI."""
    tokens: list[str] = []
    try:
        raw = st.query_params.get("demo", "")
        if isinstance(raw, list):
            raw = raw[0] if raw else ""
        tokens.append(str(raw))
    except Exception:
        pass
    try:
        from urllib.parse import parse_qs, urlparse

        url = str(getattr(st.context, "url", "") or "")
        tokens.append((parse_qs(urlparse(url).query).get("demo") or [""])[0])
        if "demo=1" in url.lower() or "demo=true" in url.lower():
            tokens.append("1")
    except Exception:
        pass
    return any(str(token).strip().lower() in {"1", "true", "yes", "on"} for token in tokens)


AUDIENCE = audience_mode()
st.markdown(
    f"<style>{Path(__file__).with_name('styles.css').read_text(encoding='utf-8')}</style>",
    unsafe_allow_html=True,
)
if AUDIENCE:
    st.markdown(
        '<div class="buddy-audience-flag" aria-hidden="true"></div>',
        unsafe_allow_html=True,
    )


@st.cache_data
def personas() -> list[dict]:
    data = load_personas()
    problems = []
    for item in data:
        problems.extend(
            f"{item.get('patient', {}).get('persona_id')}: {e}" for e in validate_payload(item)
        )
    if problems:
        st.warning("Fixture checks:\n- " + "\n- ".join(problems))
    by_id = {p["patient"]["persona_id"]: p for p in data}
    return [by_id[pid] for pid in PERSONA_ORDER if pid in by_id]


def _mascot_data_uri() -> str:
    if not MASCOT_FILE.exists():
        return ""
    encoded = base64.b64encode(MASCOT_FILE.read_bytes()).decode("ascii")
    return f"data:image/png;base64,{encoded}"


def _go_home() -> None:
    st.session_state.buddy_view = "home"
    st.session_state.detail_theme = None
    st.rerun()


def render_audience_pills(personas_by_id: dict) -> None:
    st.markdown('<div class="buddy-pills-flag" aria-hidden="true"></div>', unsafe_allow_html=True)
    st.pills(
        "Wie ben jij?",
        options=list(personas_by_id),
        format_func=lambda pid: personas_by_id[pid]["patient"]["display_name"],
        key="audience_persona_pills",
        label_visibility="collapsed",
        on_change=_sync_audience_persona,
    )


def render_header(*, audience: bool = False) -> None:
    uri = _mascot_data_uri()
    if uri:
        face = (
            f'<img class="buddy-hero-face" src="{uri}" alt="Boris" width="128" '
            f'style="width:128px;max-width:none;height:auto;display:block;" />'
        )
    else:
        face = '<div class="buddy-hero-face buddy-hero-fallback" aria-hidden="true"></div>'
    band = "buddy-hero buddy-hero--zaal" if audience else "buddy-hero"
    st.markdown(
        f"""
<div class="{band}">
  <div class="buddy-hero-mark">{face}</div>
  <div class="buddy-hero-copy">
    <div class="buddy-hero-name">Boris</div>
    <div class="buddy-hero-line">Je elektronische gezondheidsbuddy</div>
  </div>
</div>
""",
        unsafe_allow_html=True,
    )


def render_risk(risk: dict) -> None:
    label = risk["risk_label"]
    colors = RISK_COLORS[label]
    score_pct = pct(risk["risk_score"])
    width = max(4, round(float(risk["risk_score"]) * 100))
    st.markdown(
        f"""
<div class="buddy-risk-hero">
  <div class="buddy-risk-title">Risico op diabetes <span>over 5 jaar</span></div>
  <div class="buddy-risk-num" style="color:{colors["ink"]};">{score_pct}</div>
  <span class="buddy-risk-band" style="background:{colors["badge_bg"]};color:{colors["badge_ink"]};">{risk_band_nl(label)}</span>
  <div class="buddy-risk-track">
    <div style="width:{width}%;background:{colors["bar"]};"></div>
  </div>
</div>
""",
        unsafe_allow_html=True,
    )


def format_factor_value(factor: dict) -> str:
    """Patient-facing value: Ja/Nee for 0/1 flags, no raw 1.0."""
    raw = factor.get("patient_value")
    unit = str(factor.get("unit") or "").strip()
    if raw is None or raw == "" or raw == "—":
        return ""
    try:
        number = float(raw)
    except (TypeError, ValueError):
        return f"{raw} {unit}".strip()
    if abs(number - 0.0) < 1e-9 or abs(number - 1.0) < 1e-9:
        if not unit or unit.lower() in {"flag", "ja/nee", "0/1"}:
            return "Ja" if abs(number - 1.0) < 1e-9 else "Nee"
    if number == int(number):
        pretty = str(int(number))
    else:
        pretty = f"{number:.1f}".rstrip("0").rstrip(".")
    return f"{pretty} {unit}".strip()


TILE_CTA = {
    "activity-walks": "Open de Groninger wandeling",
    "keep-cycling": "Bescherm je fietsrit",
    "keep-training": "Houd je training vast",
    "food-pattern": "Wissel één suikerdrank",
    "food-maintain": "Neem lunch mee op drukke dagen",
    "sleep-wind-down": "Zet de telefoon uit de kamer",
    "sleep-keep": "Houd je bedtijd vast",
    "smoke-free-days": "Kies twee rookvrije dagen",
    "alcohol-free-evenings": "Kies twee avonden zonder alcohol",
}
THEME_CTA = {
    "sport": "Open de wandeling",
    "food": "Wissel één suikerdrank",
    "sleep": "Zet de telefoon uit de kamer",
    "smoking": "Kies twee rookvrije dagen",
    "alcohol": "Kies twee avonden zonder alcohol",
}


def _tile_cta(item: dict, theme: str) -> str:
    return TILE_CTA.get(str(item.get("id") or "")) or THEME_CTA.get(theme, "Open de stap")


def render_advice_tile(factors: list[dict], item: dict, theme: str) -> None:
    """One column card: theme, action, chips, one sentence, attached CTA."""
    meta = THEME_META.get(theme, {"label": "Stap"})
    colors = THEME_COLORS.get(theme, THEME_COLORS["sport"])
    blurb = item.get("summary") or item.get("explanation") or ""
    chips = []
    for factor in factors_for_advice_card(item, factors):
        label = factor_display_label(factor)
        shown = format_factor_value(factor)
        chip = f"{label} {shown}".strip() if shown else label
        chips.append(f'<span class="buddy-chip">{chip}</span>')
    chips_html = f'<div class="buddy-chips buddy-tile-chips">{"".join(chips)}</div>' if chips else ""
    st.markdown(
        f"""
<div class="buddy-tile" style="--buddy-tile-bar:{colors["bar"]};--buddy-tile-ink:{colors["ink"]};background:#fff;border:1px solid #d5e6f2;border-top:8px solid {colors["bar"]};border-radius:20px 20px 0 0;padding:18px 16px 28px;">
  <div class="buddy-tile-kicker" style="font-size:0.75rem;font-weight:750;letter-spacing:0.06em;text-transform:uppercase;color:{colors["ink"]};">{meta["label"]}</div>
  <div class="buddy-tile-title" style="font-size:1.15rem;font-weight:750;color:#1A4A6E;margin:8px 0 10px;">{item["title"]}</div>
  {chips_html}
  <div class="buddy-tile-blurb" style="color:#3d5a70;font-size:0.94rem;line-height:1.45;padding-bottom:1.35rem;">{blurb}</div>
  <div class="buddy-tile-spacer" aria-hidden="true"></div>
</div>
""",
        unsafe_allow_html=True,
    )
    cta = _tile_cta(item, theme)
    if st.button(
        cta,
        key=f"open_{item.get('id', theme)}",
        type="primary",
        use_container_width=True,
    ):
        st.session_state.buddy_view = "detail"
        st.session_state.detail_theme = theme
        st.rerun()


def _advice_chips(theme: str, payload: dict) -> list[dict]:
    """Factors from the matching advice set; body chips stay BMI / BRI / taille first."""
    group: list[dict] = []
    for factors, _item, set_theme in advice_sets(payload, limit=3):
        if set_theme == theme:
            group = list(factors)
            break
    if theme == "sport":
        rank = {"bmi": 0, "bri": 1, "waist": 2, "weight": 3}
        group.sort(key=lambda factor: rank.get(str(factor.get("id") or ""), 9))
    return group


def _step_card(kicker: str, title: str, body: str, steps: list[str] | None, colors: dict) -> None:
    steps_html = ""
    if steps:
        items = "".join(f"<li>{step}</li>" for step in steps)
        steps_html = f'<ol class="buddy-route">{items}</ol>'
    title_html = f'<div class="buddy-step-title">{title}</div>' if title else ""
    wide = " buddy-step-card--wide" if steps else ""
    st.markdown(
        f"""
<div class="buddy-step-card{wide}" style="--buddy-tile-bar:{colors["bar"]};--buddy-tile-ink:{colors["ink"]};background:#fff;border:1px solid #d5e6f2;border-top:8px solid {colors["bar"]};border-radius:20px;padding:16px 16px 14px;">
  <div class="buddy-step-kicker">{kicker}</div>
  {title_html}
  <div class="buddy-step-body">{body}</div>
  {steps_html}
</div>
""",
        unsafe_allow_html=True,
    )


def render_detail_page(
    theme: str,
    patient_name: str,
    payload: dict,
) -> None:
    page = get_intervention_page(theme)
    colors = THEME_COLORS.get(theme, THEME_COLORS["sport"])
    meta = THEME_META.get(theme, {"label": "Stap"})
    render_header(audience=AUDIENCE)

    st.markdown(
        f'<div class="buddy-detail-flag buddy-detail--{theme}" style="--buddy-tile-bar:{colors["bar"]};--buddy-tile-ink:{colors["ink"]};"></div>',
        unsafe_allow_html=True,
    )

    chips = []
    for factor in _advice_chips(theme, payload):
        label = factor_display_label(factor)
        shown = format_factor_value(factor)
        chip = f"{label} {shown}".strip() if shown else label
        chips.append(f'<span class="buddy-chip">{chip}</span>')
    chips_html = f'<div class="buddy-chips">{"".join(chips)}</div>' if chips else ""
    st.markdown(
        f"""
<div class="buddy-detail-hero" style="--buddy-tile-bar:{colors["bar"]};--buddy-tile-ink:{colors["ink"]};border-top:8px solid {colors["bar"]};">
  <div class="buddy-detail-kicker">{meta["label"]}</div>
  <div class="buddy-detail-title">{page["title"]}</div>
  <div class="buddy-detail-lead">{page["coach"]}</div>
  {chips_html}
</div>
""",
        unsafe_allow_html=True,
    )

    when_col, long_col = st.columns(2)
    with when_col:
        _step_card("Wanneer", "", page["when"], None, colors)
    with long_col:
        _step_card("Hoe lang", "", page["duration"], None, colors)
    steps_kicker = "De wandeling" if theme == "sport" else "Zo doe je het"
    route_title = page.get("route_name") or "" if theme == "sport" else ""
    _step_card(steps_kicker, route_title, "", list(page.get("route_steps") or []), colors)

    if st.button("Terug naar de tegels", key="back_home", type="primary", use_container_width=True):
        _go_home()


def _nudge_waist_with_weight(old_weight: float, new_weight: float) -> None:
    """Keep hidden taille aligned with the 0.7 cm/kg mock track when gewicht moves."""
    if "whatif_waist" not in st.session_state:
        return
    delta = float(new_weight) - float(old_weight)
    if abs(delta) < 1e-9:
        return
    waist = float(st.session_state.whatif_waist)
    st.session_state.whatif_waist = round(clip(waist + WAIST_CM_PER_KG * delta, 60.0, 140.0), 0)


def _current_height_cm() -> float:
    return float(st.session_state.get("whatif_height_cm") or 170)


def _sync_bri_from_waist() -> None:
    height_cm = _current_height_cm()
    waist = float(st.session_state.get("whatif_waist") or 80)
    st.session_state.whatif_bri = round(clip(body_roundness_index(waist, height_cm), 1.0, 12.0), 2)


def _sync_weight_to_shape() -> None:
    """Gewicht nudges taille (0.7 cm/kg); BRI follows taille + height."""
    new_weight = float(st.session_state.whatif_weight)
    old_weight = float(st.session_state.get("_whatif_weight_for_waist") or new_weight)
    _nudge_waist_with_weight(old_weight, new_weight)
    st.session_state._whatif_weight_for_waist = new_weight
    _sync_bri_from_waist()


def _bri_sentence() -> str:
    bri = float(st.session_state.get("whatif_bri") or 0)
    return (
        f"BRI {bri:.1f} — de vorm van je taille, uit middelomvang en lengte."
    )


def _secrets_openai_key() -> str:
    try:
        return str(st.secrets.get("OPENAI_API_KEY", "") or "").strip()
    except Exception:
        return ""


def _sync_audience_persona() -> None:
    """Keep zaal pills as the source of truth without a mid-script rerun.

    Pietje is the pills default (`persona-river`). A form submit can remount
    pills back to that default for one run; a `st.rerun()` then aborted before
    the chat form was processed — so only Pietje's Vraag-click survived.
    """
    picked = st.session_state.get("audience_persona_pills")
    if picked in PERSONA_ORDER:
        st.session_state.audience_persona = picked


# Streamlit drops unused widget keys. Detail pages do not render sliders, so
# whatif_* is gone on the way back and the widgets remount at their min.
_WHATIF_SLIDER_KEYS = (
    "whatif_weight",
    "whatif_move",
    "whatif_sleep",
    "whatif_drinks",
)


def _keep_whatif_sliders() -> None:
    for key in _WHATIF_SLIDER_KEYS:
        if key in st.session_state:
            st.session_state[f"_keep_{key}"] = st.session_state[key]


def _reseed_whatif_sliders() -> None:
    for key in _WHATIF_SLIDER_KEYS:
        if key in st.session_state:
            continue
        kept = st.session_state.get(f"_keep_{key}")
        if kept is not None:
            st.session_state[key] = kept


def apply_persona_state(persona_id: str, baseline: dict) -> None:
    body = persona_body(baseline)
    st.session_state.whatif_height_cm = body["height_cm"]
    defaults = {
        "whatif_weight": round(body["weight_kg"], 1),
        "whatif_waist": round(body["waist_cm"], 0),
        "whatif_bri": round(body["bri"], 2),
        "whatif_move": int(round(body["move_min_week"])),
        "whatif_sleep": round(body["sleep_hours"], 1),
        "whatif_drinks": int(round(body["sugary_drinks_week"])),
        "_whatif_weight_for_waist": round(body["weight_kg"], 1),
    }
    persona_changed = st.session_state.get("whatif_persona") != persona_id
    resetting = st.session_state.pop("whatif_reset", False)
    if persona_changed or resetting:
        st.session_state.whatif_persona = persona_id
        for key, value in defaults.items():
            st.session_state[key] = value
        _keep_whatif_sliders()
    else:
        _reseed_whatif_sliders()
        for key, value in defaults.items():
            st.session_state.setdefault(key, value)
    if persona_changed:
        st.session_state.chat = []
        st.session_state.chat_persona = persona_id
        st.session_state.buddy_view = "home"
        st.session_state.detail_theme = None


def payload_from_whatif(baseline: dict, use_live: bool) -> dict:
    weight_kg = float(st.session_state.whatif_weight)
    waist_cm = float(st.session_state.whatif_waist)
    move_min = float(st.session_state.whatif_move)
    sleep_h = float(st.session_state.whatif_sleep)
    drinks = float(st.session_state.whatif_drinks)
    if use_live:
        live = overlay_live_predictions(baseline, weight_kg=weight_kg, waist_cm=waist_cm)
        return apply_lifestyle_overlay(
            live,
            baseline,
            move_min_week=move_min,
            sleep_hours=sleep_h,
            sugary_drinks_week=drinks,
        )
    return apply_weight_whatif(
        baseline,
        weight_kg=weight_kg,
        waist_cm=waist_cm,
        move_min_week=move_min,
        sleep_hours=sleep_h,
        sugary_drinks_week=drinks,
    )


payloads = personas()
by_id = {p["patient"]["persona_id"]: p for p in payloads}
use_live_default = models_available()
if "system_prompt" not in st.session_state:
    st.session_state.system_prompt = load_default_system_prompt()
if st.session_state.pop("system_prompt_reset", False):
    st.session_state.system_prompt = load_default_system_prompt()

if AUDIENCE:
    use_live = use_live_default
    if st.session_state.get("audience_persona") not in by_id:
        st.session_state.audience_persona = PERSONA_ORDER[0]
    persona_id = st.session_state.audience_persona
    # Reassert before pills mount so a remount cannot snap back to Pietje.
    st.session_state.audience_persona_pills = persona_id
else:
    with st.sidebar:
        st.markdown("### Boris")
        use_live = st.toggle(
            "Live model (final A/B)",
            value=use_live_default,
            help="Aan: final model A (elastic-net, 5 jaar). Model B blijft in de repo, niet in beeld. Uit: mock fixtures.",
            disabled=not use_live_default,
        )
        st.caption("Small steps. Big impact.")
        st.markdown("**Wie ben jij?**")
        persona_id = st.radio(
            "Demo-persona",
            options=list(by_id),
            format_func=lambda pid: by_id[pid]["patient"]["display_name"],
            label_visibility="collapsed",
        )
        stored_key = _secrets_openai_key()
        st.caption(
            f"{by_id[persona_id]['patient']['display_name']}, "
            f"{by_id[persona_id]['patient'].get('age', '—')} · "
            f"start {persona_body(by_id[persona_id])['weight_kg']:.0f} kg"
        )
        with st.expander("OpenAI-sleutel", expanded=not openai_key_configured(stored_key)):
            st.text_input(
                "OpenAI API key",
                type="password",
                key="openai_api_key",
                placeholder="sk-…",
                help="Zelfde patroon als eerdere opdracht: plak hier, of zet OPENAI_API_KEY in .streamlit/secrets.toml. Wordt niet gecommit.",
            )
            st.caption("Of: omgeving OPENAI_API_KEY, of kopieer secrets.toml.example naar secrets.toml.")
        with st.expander("System prompt (demo)", expanded=False):
            st.caption(
                "Zoals bij Barbecue Bob: vaste rol-instructie voor OpenAI. "
                "Patiënten zien dit niet in de hoofdchat. Sessie-context van Pietje/Sam/Noor wordt eronder geplakt."
            )
            st.text_area("System prompt", key="system_prompt", height=280)
            if st.button("Herstel default"):
                st.session_state.system_prompt_reset = True
                st.rerun()
        if st.button("Zaalweergave"):
            st.query_params["demo"] = "1"
            st.rerun()
        st.caption("Of plak `?demo=1` achter de URL. Keuken (key, prompt, live-toggle) gaat dan weg.")

baseline = by_id[persona_id]
apply_persona_state(persona_id, baseline)

openai_key = resolve_openai_api_key(
    st.session_state.get("openai_api_key"),
    _secrets_openai_key(),
)

payload = payload_from_whatif(baseline, use_live)
patient = payload["patient"]

if st.session_state.get("buddy_view") == "detail":
    _keep_whatif_sliders()
    render_detail_page(
        st.session_state.get("detail_theme") or "sport",
        patient["display_name"],
        payload,
    )
    st.stop()

if AUDIENCE:
    render_header(audience=True)
    render_audience_pills(by_id)
else:
    render_header(audience=False)

payload = payload_from_whatif(baseline, use_live)
patient = payload["patient"]
risks = {r["id"]: r for r in payload["risks"]}
render_risk(risks["t1_t2"])

st.markdown('<div class="buddy-whatif-flag" aria-hidden="true"></div>', unsafe_allow_html=True)
with st.container(border=True):
    st.slider(
        "Gewicht (kg)",
        45.0,
        140.0,
        step=0.5,
        format="%.1f",
        key="whatif_weight",
        on_change=_sync_weight_to_shape,
    )
    st.markdown(f'<p class="buddy-bri-line">{_bri_sentence()}</p>', unsafe_allow_html=True)
    mcol, scol, dcol = st.columns(3, vertical_alignment="bottom")
    with mcol:
        st.slider("Beweegminuten per week", 0, 420, step=10, key="whatif_move")
    with scol:
        st.slider("Slaap (uur per nacht)", 4.0, 10.0, step=0.5, key="whatif_sleep")
    with dcol:
        st.slider("Suikerdranken per week", 0, 21, step=1, key="whatif_drinks")
    if not AUDIENCE:
        if st.button("Reset"):
            st.session_state.whatif_reset = True
            st.rerun()
_keep_whatif_sliders()

payload = payload_from_whatif(baseline, use_live)
patient = payload["patient"]
# Labs/meds may still sit on the live payload; never let them become their own card.
kept_factors = []
seen_ids: set[str] = set()
for factor in list(payload.get("top_factors") or []) + list(payload.get("persona_factors") or []):
    if not patient_can_influence(factor):
        continue
    fid = str(factor.get("id") or "")
    if not fid or fid in seen_ids:
        continue
    seen_ids.add(fid)
    kept_factors.append(factor)
payload["top_factors"] = kept_factors
st.markdown('<div class="buddy-voorjou-section buddy-tiles-flag">', unsafe_allow_html=True)
sets = [
    (factors, item, theme)
    for factors, item, theme in advice_sets(payload, limit=3)
    if any(patient_can_influence(factor) for factor in factors)
]
if sets:
    row = st.columns(len(sets))
    for col, (factors, item, theme) in zip(row, sets):
        with col:
            render_advice_tile(factors, item, theme)
st.markdown("</div>", unsafe_allow_html=True)

st.markdown('<div class="buddy-chat-section">', unsafe_allow_html=True)
st.markdown('<div class="buddy-chat-title">Vraag het aan Boris</div>', unsafe_allow_html=True)
if "chat" not in st.session_state or st.session_state.get("chat_persona") != persona_id:
    st.session_state.chat = []
    st.session_state.chat_persona = persona_id
if not AUDIENCE:
    if openai_key:
        st.caption(f"Verbonden met OpenAI · {OPENAI_MODEL}")
    else:
        st.caption("Geen API-sleutel. Plak er een in de sidebar — tot die tijd vaste teksten.")
with st.form(f"ask_buddy_{persona_id}", clear_on_submit=True):
    question = st.text_input(
        "Je vraag",
        placeholder=CHAT_PLACEHOLDER,
        label_visibility="collapsed",
        key=f"buddy_ask_{persona_id}",
    )
    asked = st.form_submit_button("Vraag", type="primary")
if asked:
    history = [(prev_q, prev_a) for prev_q, prev_a, _src in st.session_state.chat]
    reply, source = answer_question(
        question,
        payload,
        api_key=openai_key,
        history=history,
        system_prompt=st.session_state.get("system_prompt"),
    )
    st.session_state.chat.append((question, reply, source))
for q, reply, _source in st.session_state.chat:
    st.chat_message("user").write(q)
    st.chat_message("assistant").write(reply)
st.markdown("</div>", unsafe_allow_html=True)
