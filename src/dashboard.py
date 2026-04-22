"""
dashboard.py — Paso 4b · Dashboard Streamlit
─────────────────────────────────────────────
Cola de priorización con sliders interactivos.
Al mover los pesos, el ranking se recalcula en tiempo real.

Ejecutar:  streamlit run src/dashboard.py
"""

import json
import os
import sys
import pandas as pd
import streamlit as st

# Añadir el directorio raíz al path para importar scoring
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.scoring import (
    score_all,
    DEFAULT_SENTIMENT_WEIGHTS,
    DEFAULT_TOPIC_WEIGHTS,
    DEFAULT_AGE_MULT,
    DEFAULT_MAX_AGE,
    DEFAULT_THRESHOLDS,
)

# ── Config ────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(BASE_DIR, "data", "analyzed_emails.json")

st.set_page_config(page_title="📧 Email Priority Queue", layout="wide")
st.title("📧 Email Priority Queue")
st.caption("Mueve los sliders y observa cómo cambia la priorización en tiempo real")

# ── Cargar datos ──────────────────────────────────────────────────
@st.cache_data
def load_emails():
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

emails = load_emails()

# ══════════════════════════════════════════════════════════════════
# SIDEBAR — Controles de pesos
# ══════════════════════════════════════════════════════════════════
st.sidebar.header("⚙️ Parámetros de scoring")

# — Sentimiento —
st.sidebar.subheader("Peso por sentimiento")
sw = {}
for key, default in DEFAULT_SENTIMENT_WEIGHTS.items():
    label = key.replace("_", " ").title()
    sw[key] = st.sidebar.slider(f"🎭 {label}", 0, 80, default, step=5)

st.sidebar.divider()

# — Tema —
st.sidebar.subheader("Peso por tema")
tw = {}
for key, default in DEFAULT_TOPIC_WEIGHTS.items():
    tw[key] = st.sidebar.slider(f"📂 {key}", 0, 60, default, step=5)

st.sidebar.divider()

# — Edad y umbrales —
st.sidebar.subheader("Edad y umbrales")
age_mult = st.sidebar.slider("📅 Multiplicador edad (pts/día)", 0.0, 2.0, DEFAULT_AGE_MULT, step=0.1)
max_age = st.sidebar.slider("📅 Bonus máximo edad", 0, 50, DEFAULT_MAX_AGE, step=5)

st.sidebar.divider()
st.sidebar.subheader("Umbrales de tier")
thr_crit = st.sidebar.slider("🔴 CRITICAL ≥", 0, 150, DEFAULT_THRESHOLDS["critical"], step=5)
thr_high = st.sidebar.slider("🟠 HIGH ≥", 0, 100, DEFAULT_THRESHOLDS["high"], step=5)
thr_med = st.sidebar.slider("🟡 MEDIUM ≥", 0, 70, DEFAULT_THRESHOLDS["medium"], step=5)

thresholds = {"critical": thr_crit, "high": thr_high, "medium": thr_med}

# ══════════════════════════════════════════════════════════════════
# SCORING EN TIEMPO REAL
# ══════════════════════════════════════════════════════════════════
scored = score_all(emails, sw, tw, age_mult, max_age, thresholds)

# ── Métricas resumen ─────────────────────────────────────────────
tier_icons = {"CRITICAL": "🔴", "HIGH": "🟠", "MEDIUM": "🟡", "LOW": "🟢"}
tier_counts = {}
for e in scored:
    tier_counts[e["tier"]] = tier_counts.get(e["tier"], 0) + 1

cols = st.columns(4)
for i, tier in enumerate(["CRITICAL", "HIGH", "MEDIUM", "LOW"]):
    count = tier_counts.get(tier, 0)
    cols[i].metric(f"{tier_icons[tier]} {tier}", count)

st.divider()

# ── Tabla principal ───────────────────────────────────────────────
st.subheader("📋 Cola de priorización")

df = pd.DataFrame([
    {
        "#": idx + 1,
        "Tier": f"{tier_icons[e['tier']]} {e['tier']}",
        "Score": e["score"],
        "Subject": e["subject"],
        "From": e["from_addr"],
        "Sentiment": e["sentiment"],
        "Topic": e["topic"],
        "Summary": e["summary"],
    }
    for idx, e in enumerate(scored)
])

st.dataframe(
    df,
    use_container_width=True,
    hide_index=True,
    column_config={
        "Score": st.column_config.ProgressColumn(
            "Score", min_value=0, max_value=max(e["score"] for e in scored) * 1.1,
            format="%.1f",
        ),
    },
)

# ── Detalle por email ─────────────────────────────────────────────
st.divider()
st.subheader("🔍 Desglose de un email")

email_options = {f"{e['id']} — {e['subject'][:40]}": e for e in scored}
selected_label = st.selectbox("Selecciona un email", list(email_options.keys()))
sel = email_options[selected_label]

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Sentimiento", f"+{sel['detail']['sentiment_w']}")
c2.metric("Tema", f"+{sel['detail']['topic_w']}")
c3.metric("Edad", f"+{sel['detail']['age_bonus']}", f"{sel['detail']['age_days']:.0f} días")
c4.metric("Penaliz. confianza", f"-{sel['detail']['conf_penalty']}")
c5.metric("TOTAL", sel["score"], sel["tier"])

# ── Fórmula explicada ────────────────────────────────────────────
st.divider()
st.subheader("📐 Fórmula de scoring")
st.code(
    "score = sentiment_w + topic_w + min(age_days × age_mult, max_age) − (1 − confidence) × 5",
    language="text",
)
st.markdown(f"""
| Componente | Descripción | Valor actual |
|---|---|---|
| `sentiment_w` | Peso según el sentimiento del email | `{sel['detail']['sentiment_w']}` (← {sel['sentiment']}) |
| `topic_w` | Peso según el tema/categoría | `{sel['detail']['topic_w']}` (← {sel['topic']}) |
| `age_bonus` | Antigüedad: {sel['detail']['age_days']:.0f} días × {age_mult} (cap {max_age}) | `{sel['detail']['age_bonus']}` |
| `conf_penalty` | Penalización: (1 − {sel['confidence']:.2f}) × 5 | `{sel['detail']['conf_penalty']}` |
| **TOTAL** | | **{sel['score']}** → **{sel['tier']}** |
""")
