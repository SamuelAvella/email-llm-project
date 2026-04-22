"""
scoring.py — Paso 4a · Cálculo de urgencia
───────────────────────────────────────────
Fórmula:
  score = sentiment_w + topic_w + min(age_days × age_mult, max_age) − (1 − confidence) × 5

Tiers:
  🔴 CRITICAL  ≥ 70
  🟠 HIGH      ≥ 45
  🟡 MEDIUM    ≥ 25
  🟢 LOW       < 25
"""

import json
import os
import sys
from datetime import datetime, timezone

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ANALYSIS_PATH = os.path.join(BASE_DIR, "data", "analyzed_emails.json")
OUTPUT_PATH = os.path.join(BASE_DIR, "data", "scored_emails.json")

# ── Pesos por defecto ─────────────────────────────────────────────
DEFAULT_SENTIMENT_WEIGHTS = {
    "very_negative": 40,
    "negative": 25,
    "neutral": 10,
    "positive": 5,
    "very_positive": 0,
}

DEFAULT_TOPIC_WEIGHTS = {
    "Complaint": 30,
    "Bug": 25,
    "Sales": 20,
    "New Feature Request": 10,
    "Other": 5,
}

DEFAULT_AGE_MULT = 0.5
DEFAULT_MAX_AGE = 20
DEFAULT_THRESHOLDS = {"critical": 70, "high": 45, "medium": 25}


def compute_score(email, sentiment_w, topic_w, age_mult, max_age, thresholds, ref_date=None):
    """Calcula score y tier para un email analizado."""
    now = ref_date or datetime.now(tz=timezone.utc)

    sw = sentiment_w.get(email["sentiment"], 10)
    tw = topic_w.get(email["topic"], 5)

    date_parsed = datetime.fromisoformat(email["date_parsed"]).replace(tzinfo=timezone.utc)
    age_days = max(0.0, (now - date_parsed).total_seconds() / 86400)
    age_bonus = min(age_days * age_mult, max_age)

    conf_penalty = (1.0 - email["confidence"]) * 5

    score = sw + tw + age_bonus - conf_penalty

    if score >= thresholds["critical"]:
        tier = "CRITICAL"
    elif score >= thresholds["high"]:
        tier = "HIGH"
    elif score >= thresholds["medium"]:
        tier = "MEDIUM"
    else:
        tier = "LOW"

    return {
        **email,
        "score": round(score, 1),
        "tier": tier,
        "detail": {
            "sentiment_w": sw,
            "topic_w": tw,
            "age_days": round(age_days, 1),
            "age_bonus": round(age_bonus, 1),
            "conf_penalty": round(conf_penalty, 1),
        },
    }


def score_all(emails, sentiment_w=None, topic_w=None,
              age_mult=None, max_age=None, thresholds=None, ref_date=None):
    """Puntúa y ordena todos los emails de mayor a menor urgencia."""
    sw = sentiment_w or DEFAULT_SENTIMENT_WEIGHTS
    tw = topic_w or DEFAULT_TOPIC_WEIGHTS
    am = age_mult if age_mult is not None else DEFAULT_AGE_MULT
    ma = max_age if max_age is not None else DEFAULT_MAX_AGE
    th = thresholds or DEFAULT_THRESHOLDS

    scored = [compute_score(e, sw, tw, am, ma, th, ref_date) for e in emails]
    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored


def main():
    """Ejecuta el scoring con pesos por defecto y guarda el resultado."""
    sys.stdout.reconfigure(encoding="utf-8")
    with open(ANALYSIS_PATH, "r", encoding="utf-8") as f:
        emails = json.load(f)

    scored = score_all(emails)

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(scored, f, indent=2, ensure_ascii=False)

    print(f"✅ {len(scored)} emails puntuados → {OUTPUT_PATH}")
    for e in scored:
        icon = {"CRITICAL": "🔴", "HIGH": "🟠", "MEDIUM": "🟡", "LOW": "🟢"}[e["tier"]]
        print(f"  {icon} {e['score']:5.1f}  {e['tier']:<8}  {e['subject'][:50]}")


if __name__ == "__main__":
    main()
