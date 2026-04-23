"""
02_clean.py
==================
Fase 2 - Limpieza de mails con expresiones regulares.

Lee los emails sin procesar de data/raw/, elimina ruido, y escribe el contenido limpio
en data/clean/ con un reporte de los resultados.
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

try:
    from src.cleaning import CLEAN_DIR, DEFAULT_REPORT_NAME, RAW_DIR, clean_directory
except ImportError:
    from cleaning import CLEAN_DIR, DEFAULT_REPORT_NAME, RAW_DIR, clean_directory

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="02_clean - Step 2 - Clean raw emails before LLM processing",
    )
    parser.add_argument(
        "--input-dir",
        default=str(RAW_DIR),
        help=f"Raw email directory (default: {RAW_DIR})",
    )
    parser.add_argument(
        "--output-dir",
        default=str(CLEAN_DIR),
        help=f"Clean output directory (default: {CLEAN_DIR})",
    )
    parser.add_argument(
        "--report-path",
        default=None,
        help=(
            "Optional JSON report path "
            f"(default: <output-dir>/{DEFAULT_REPORT_NAME})"
        ),
    )
    return parser


if __name__ == "__main__":
    args = build_arg_parser().parse_args()

    try:
        cleaned = clean_directory(
            input_dir=Path(args.input_dir),
            output_dir=Path(args.output_dir),
            report_path=Path(args.report_path) if args.report_path else None,
            logger=log,
        )
    except FileNotFoundError as exc:
        log.error("%s", exc)
        sys.exit(1)

    sys.exit(0 if cleaned > 0 else 1)
