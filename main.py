"""
main.py
=======
Punto de entrada único del pipeline de clasificación de emails.

Ejecuta las 4 fases en orden:
    1. Ingesta    — descarga emails de la API mock y los guarda en data/raw/
    2. Limpieza   — aplica RegEx a data/raw/ y escribe en data/clean/
    3. Análisis   — llama al LLM y genera data/analyzed_emails.json
    4. Scoring    — calcula urgencia y genera data/scored_emails.json

Uso:
    uv run python main.py                  # pipeline completo
    uv run python main.py --only fetch     # solo fase 1
    uv run python main.py --only clean     # solo fase 2
    uv run python main.py --only analyze   # solo fase 3
    uv run python main.py --only score     # solo fase 4
    uv run python main.py --skip fetch     # todas menos la fase 1

Nota: el servidor FastAPI debe estar corriendo antes de ejecutar este script.
    uv run uvicorn src.email_api_server:app --reload
"""

from __future__ import annotations

import argparse
import logging
import subprocess
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Definición del pipeline
# ---------------------------------------------------------------------------

ROOT = Path(__file__).parent

STAGES: list[dict] = [
    {
        "name":   "fetch",
        "label":  "Fase 1 · Ingesta de datos",
        "script": ROOT / "src" / "01_fetch.py",
    },
    {
        "name":   "clean",
        "label":  "Fase 2 · Limpieza RegEx",
        "script": ROOT / "src" / "02_clean.py",
    },
    {
        "name":   "analyze",
        "label":  "Fase 3 · Análisis LLM",
        "script": ROOT / "src" / "03_analyze.py",
    },
    {
        "name":   "score",
        "label":  "Fase 4 · Scoring y priorización",
        "script": ROOT / "src" / "scoring.py",
    },
]

# ---------------------------------------------------------------------------
# Ejecución de cada fase
# ---------------------------------------------------------------------------

def run_stage(stage: dict) -> bool:
    """
    Ejecuta un script Python como subproceso.
    Devuelve True si terminó con éxito, False si falló.
    """
    log.info("─" * 60)
    log.info("Iniciando %s", stage["label"])
    log.info("─" * 60)

    result = subprocess.run(
        [sys.executable, str(stage["script"])],
        cwd=ROOT,
    )

    if result.returncode != 0:
        log.error("✘  %s falló con código %d", stage["label"], result.returncode)
        return False

    log.info("✔  %s completada", stage["label"])
    return True

# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Pipeline de clasificación de emails — ejecuta todas las fases en orden.",
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--only",
        choices=[s["name"] for s in STAGES],
        help="Ejecutar únicamente esta fase.",
    )
    group.add_argument(
        "--skip",
        choices=[s["name"] for s in STAGES],
        help="Saltar esta fase y ejecutar el resto.",
    )
    parser.add_argument(                              
        "--dashboard",
        action="store_true",
        help="Lanzar el dashboard Streamlit al finalizar el pipeline.",
    )
    return parser

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    args = build_parser().parse_args()

    # filtrar fases según los flags
    if args.only:
        stages = [s for s in STAGES if s["name"] == args.only]
    elif args.skip:
        stages = [s for s in STAGES if s["name"] != args.skip]
    else:
        stages = STAGES

    log.info("Pipeline de emails — %d fase(s) a ejecutar", len(stages))

    for stage in stages:
        success = run_stage(stage)
        if not success:
            log.error("Pipeline detenido en '%s'. Corrige el error y vuelve a ejecutar.", stage["name"])
            return 1

    log.info("═" * 60)
    log.info("Pipeline completado con éxito — %d fases ejecutadas", len(stages))
    log.info("═" * 60)

    if args.dashboard:
        log.info("Lanzando dashboard Streamlit...")
        subprocess.run(
            ["uv", "run", "streamlit", "run", "src/dashboard.py"],
            cwd=ROOT,
        )
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
