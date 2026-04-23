"""
Paso 3 · Análisis con LLM local (Ollama)
==================
Lee los emails limpios de data/clean/*.txt (salida del Paso 2),
llama al modelo local para extraer características estructuradas y
guarda el resultado en data/analyzed_emails.json con esta estructura:

{
  "id": "msg_001",
  "sentiment": "very_negative",
  "sentiment_score": 0.95,
  "topic": "Complaint",
  "confidence": 0.96,
  "date_parsed": "2026-02-20T09:15:00",
  "subject": "URGENT: REFUND REQUEST - ORDER #998822",
  "from_addr": "angry.customer@example.com",
  "summary": "Customer demands refund after repeated ignored requests."
}
"""

import json
import time
import requests
from pathlib import Path
from datetime import datetime
from email.utils import parsedate_to_datetime

# ── Configuración ──────────────────────────────────────────────────────────────
OLLAMA_URL  = "http://localhost:11434/api/generate"
MODEL       = "gemma3:1b"
CLEAN_DIR   = Path("data/clean")
META_DIR    = Path("data/raw")
OUTPUT_FILE = Path("data/analyzed_emails.json")
TIMEOUT     = 60

# Sentimientos válidos ordenados de más negativo a más positivo
VALID_SENTIMENTS = ["very_negative", "negative", "neutro", "positive", "very_positive"]


# ── Prompt ─────────────────────────────────────────────────────────────────────
def build_prompt(subject: str, sender: str, body: str) -> str:
    return f"""Analiza el siguiente email de empresa y extrae información estructurada.

EMAIL:
De: {sender}
Asunto: {subject}
Cuerpo:
{body}

Responde ÚNICAMENTE con un objeto JSON válido (sin texto adicional, sin bloques de código) con exactamente estas claves:
{{
  "sentiment": "<very_negative|negative|neutro|positive|very_positive>",
  "sentiment_score": <número entre 0.0 y 1.0 que indica la intensidad del sentimiento>,
  "topic": "<una de estas categorías exactas: Complaint, Refund, Bug, Feature Request, Question, Praise, Other>",
  "confidence": <número entre 0.0 y 1.0 que indica tu confianza en el análisis>,
  "summary": "<resumen de 1-2 frases en inglés>"
}}"""


# ── Llamada a Ollama ───────────────────────────────────────────────────────────
def call_ollama(prompt: str) -> dict:
    payload = {
        "model": MODEL,
        "prompt": prompt,
        "stream": False,
        "format": "json",
    }
    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=TIMEOUT)
        response.raise_for_status()
        raw_text = response.json().get("response", "").strip()

        if raw_text.startswith("```"):
            raw_text = raw_text.split("```")[1]
            if raw_text.startswith("json"):
                raw_text = raw_text[4:]

        result = json.loads(raw_text)

        sentiment = str(result.get("sentiment", "neutro")).lower()
        if sentiment not in VALID_SENTIMENTS:
            sentiment = "neutro"

        return {
            "sentiment":       sentiment,
            "sentiment_score": round(float(result.get("sentiment_score", 0.5)), 2),
            "topic":           str(result.get("topic", "Other")),
            "confidence":      round(float(result.get("confidence", 0.5)), 2),
            "summary":         str(result.get("summary", "")),
        }

    except requests.exceptions.ConnectionError:
        print("  ⚠️  No se puede conectar con Ollama. Ejecuta: ollama serve")
        return _default_analysis()
    except requests.exceptions.Timeout:
        print("  ⚠️  Timeout al llamar a Ollama.")
        return _default_analysis()
    except (json.JSONDecodeError, KeyError, ValueError) as exc:
        print(f"  ⚠️  Error parseando respuesta del modelo: {exc}")
        return _default_analysis()


def _default_analysis() -> dict:
    return {
        "sentiment":       "neutro",
        "sentiment_score": 0.0,
        "topic":           "Other",
        "confidence":      0.0,
        "summary":         "No se pudo analizar.",
    }


# ── Parseo de fecha ────────────────────────────────────────────────────────────
def parse_date(date_str: str) -> str:
    """Convierte fecha RFC 2822 a ISO 8601 sin timezone. Devuelve '' si falla."""
    if not date_str:
        return ""
    try:
        dt = parsedate_to_datetime(date_str)
        return dt.strftime("%Y-%m-%dT%H:%M:%S")
    except Exception:
        try:
            # Intento alternativo con formatos comunes
            for fmt in ("%a, %d %b %Y %H:%M:%S %z", "%d %b %Y %H:%M:%S %z"):
                try:
                    dt = datetime.strptime(date_str.strip(), fmt)
                    return dt.strftime("%Y-%m-%dT%H:%M:%S")
                except ValueError:
                    continue
        except Exception:
            pass
        return ""


# ── Carga de emails ────────────────────────────────────────────────────────────
def load_emails() -> list[dict]:
    if not CLEAN_DIR.exists():
        raise RuntimeError(
            f"No se encontró '{CLEAN_DIR}'. "
            "Ejecuta primero: uv run python src/01_fetch.py && uv run python src/02_clean.py"
        )

    txt_files = sorted(CLEAN_DIR.glob("*.txt"))
    txt_files = [f for f in txt_files if not f.name.startswith("_")]

    if not txt_files:
        raise RuntimeError(f"No hay ficheros .txt en '{CLEAN_DIR}'.")

    emails = []
    for txt_path in txt_files:
        msg_id = txt_path.stem
        body   = txt_path.read_text(encoding="utf-8")

        meta_path = META_DIR / f"{msg_id}.meta.json"
        meta = {}
        if meta_path.exists():
            with open(meta_path, encoding="utf-8") as f:
                meta = json.load(f)

        emails.append({
            "id":        msg_id,
            "from_addr": meta.get("from", "desconocido"),
            "subject":   meta.get("subject", "Sin asunto"),
            "date_raw":  meta.get("date", ""),
            "body":      body,
        })

    print(f"✅ Cargados {len(emails)} emails desde '{CLEAN_DIR}'")
    return emails


# ── Pipeline principal ─────────────────────────────────────────────────────────
def analyze_emails(emails: list[dict]) -> list[dict]:
    results = []
    total = len(emails)

    for i, email in enumerate(emails, start=1):
        print(f"  [{i}/{total}] Analizando: {email['subject']!r} …")
        t0 = time.time()

        prompt   = build_prompt(email["subject"], email["from_addr"], email["body"])
        analysis = call_ollama(prompt)

        elapsed = time.time() - t0
        print(f"         sentiment={analysis['sentiment']} ({analysis['sentiment_score']}), "
              f"topic={analysis['topic']}, "
              f"confidence={analysis['confidence']}, "
              f"tiempo={elapsed:.1f}s")

        results.append({
            "id":             email["id"],
            "sentiment":      analysis["sentiment"],
            "sentiment_score": analysis["sentiment_score"],
            "topic":          analysis["topic"],
            "confidence":     analysis["confidence"],
            "date_parsed":    parse_date(email["date_raw"]),
            "subject":        email["subject"],
            "from_addr":      email["from_addr"],
            "summary":        analysis["summary"],
        })

    return results


def save_results(emails: list[dict]) -> None:
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(emails, f, ensure_ascii=False, indent=2)
    print(f"\n💾 Resultados guardados en {OUTPUT_FILE}")


def main():
    print("=" * 55)
    print("  PASO 3 · Análisis con LLM local (Ollama)")
    print(f"  Modelo: {MODEL}")
    print("=" * 55)

    emails   = load_emails()
    analyzed = analyze_emails(emails)
    save_results(analyzed)

    print(f"\n✅ Paso 3 completado. {len(analyzed)} emails analizados.")
    return analyzed


if __name__ == "__main__":
    main()