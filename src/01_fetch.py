"""
01_fetch_emails.py
==================
Fase 1 — Ingesta de Datos

Consume la FastAPI simulada (email_api_server.py) y persiste cada email
en dos archivos dentro de data/raw/:

    data/raw/{id}.txt           → cuerpo bruto del email (para RegEx cleaner)
    data/raw/{id}.meta.json     → metadatos extraídos de los headers

Uso:
    pip install requests
    python 01_fetch_emails.py                        # usa defaults
    python 01_fetch_emails.py --limit 5 --skip 0
    python 01_fetch_emails.py --base-url http://localhost:9000
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

import requests

# ---------------------------------------------------------------------------
# Configuración
# ---------------------------------------------------------------------------

DEFAULT_BASE_URL = "http://localhost:8000"
RAW_DIR          = Path("data/raw")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Capa de red
# ---------------------------------------------------------------------------

def fetch_emails(base_url: str, limit: int, skip: int) -> list[dict]:
    """
    Llama a GET /emails y devuelve la lista de emails.
    Lanza requests.HTTPError si la respuesta no es 2xx.
    """
    url    = f"{base_url}/emails"
    params = {"limit": limit, "skip": skip}

    log.info("GET %s  params=%s", url, params)
    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()                      # → HTTPError si 4xx/5xx

    payload = response.json()
    emails  = payload.get("emails", [])
    log.info("Recibidos %d emails (total disponible: %d)", len(emails), payload.get("total", "?"))
    return emails

# ---------------------------------------------------------------------------
# Extracción de metadatos
# ---------------------------------------------------------------------------

def extract_metadata(email: dict) -> dict:
    """
    Extrae los campos de interés de un email y los devuelve como dict plano.
    Replica exactamente la estructura que usa master_notebook.py en meta_t:

        {
            "id":               str,
            "thread_id":        str,
            "from":             str,
            "subject":          str,
            "date":             str,
            "label_ids":        list[str],
            "internal_date_ms": int,
        }
    """
    headers: list[dict] = email.get("payload", {}).get("headers", [])
    # Indexamos headers por nombre para O(1) lookup
    header_map: dict[str, str] = {h["name"]: h["value"] for h in headers}

    return {
        "id":               email.get("id", ""),
        "thread_id":        email.get("threadId", ""),
        "from":             header_map.get("From", ""),
        "subject":          header_map.get("Subject", ""),
        "date":             header_map.get("Date", ""),
        "label_ids":        email.get("labelIds", []),
        "internal_date_ms": int(email.get("internalDate", 0)),
    }

# ---------------------------------------------------------------------------
# Persistencia
# ---------------------------------------------------------------------------

def save_email_files(email: dict, raw_dir: Path) -> tuple[Path, Path]:
    """
    Crea dos archivos para el email dado:
        <id>.txt          — body_text_content tal cual (ruido incluido)
        <id>.meta.json    — metadatos extraídos
    Devuelve (path_txt, path_meta).
    """
    email_id = email.get("id", "unknown")
    body     = email.get("body_text_content", email.get("snippet", ""))
    metadata = extract_metadata(email)

    # ── .txt ──────────────────────────────────────────────────────────────
    path_txt = raw_dir / f"{email_id}.txt"
    path_txt.write_text(body, encoding="utf-8")

    # ── .meta.json ────────────────────────────────────────────────────────
    path_meta = raw_dir / f"{email_id}.meta.json"
    path_meta.write_text(
        json.dumps(metadata, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    return path_txt, path_meta

# ---------------------------------------------------------------------------
# Orquestador principal
# ---------------------------------------------------------------------------

def run(base_url: str, limit: int, skip: int, raw_dir: Path) -> int:
    """
    Ejecuta el pipeline completo de ingesta.
    Devuelve el número de emails procesados con éxito.
    """
    # 1. Crear carpeta si no existe (equivale a mkdir -p)
    raw_dir.mkdir(parents=True, exist_ok=True)
    log.info("Directorio de salida: %s", raw_dir.resolve())

    # 2. Obtener emails de la API
    try:
        emails = fetch_emails(base_url, limit=limit, skip=skip)
    except requests.ConnectionError:
        log.error("No se pudo conectar con %s — ¿está el servidor arrancado?", base_url)
        return 0
    except requests.HTTPError as exc:
        log.error("Error HTTP: %s", exc)
        return 0

    if not emails:
        log.warning("La API devolvió 0 emails.")
        return 0

    # 3. Persistir cada email
    saved = 0
    for email in emails:
        email_id = email.get("id", "unknown")
        try:
            path_txt, path_meta = save_email_files(email, raw_dir)
            log.info(
                "  ✔  %s  →  %s  |  %s",
                email_id,
                path_txt.name,
                path_meta.name,
            )
            saved += 1
        except Exception as exc:                     # nunca detener el loop completo
            log.error("  ✘  %s  →  %s", email_id, exc)

    log.info("─" * 60)
    log.info("Ingesta completada: %d/%d emails guardados en '%s'", saved, len(emails), raw_dir)
    return saved

# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="01_fetch_emails · Fase 1 — Ingesta de emails desde la FastAPI simulada",
    )
    parser.add_argument(
        "--base-url",
        default=DEFAULT_BASE_URL,
        help=f"URL base de la API (default: {DEFAULT_BASE_URL})",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=50,
        help="Número máximo de emails a descargar (default: 50)",
    )
    parser.add_argument(
        "--skip",
        type=int,
        default=0,
        help="Emails a saltar — paginación (default: 0)",
    )
    parser.add_argument(
        "--output-dir",
        default=str(RAW_DIR),
        help=f"Carpeta de salida (default: {RAW_DIR})",
    )
    return parser


if __name__ == "__main__":
    args    = build_arg_parser().parse_args()
    n_saved = run(
        base_url=args.base_url,
        limit=args.limit,
        skip=args.skip,
        raw_dir=Path(args.output_dir),
    )
    sys.exit(0 if n_saved > 0 else 1)