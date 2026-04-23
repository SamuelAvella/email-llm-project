"""
Lógica reusable de limpieza de mails
"""

from __future__ import annotations

import html
import json
import logging
import re
from dataclasses import asdict, dataclass
from pathlib import Path

RAW_DIR = Path("data/raw")
CLEAN_DIR = Path("data/clean")
DEFAULT_REPORT_NAME = "_cleaning_report.json"

HTML_BREAK_RE = re.compile(
    r"(?i)<\s*/?\s*(?:div|p|br|li|ul|ol|tr|td|table|h[1-6])\b[^>]*>"
)
HTML_TAG_RE = re.compile(r"(?is)<[^>]+>")
MARKDOWN_BOLD_RE = re.compile(r"\*\*(.+?)\*\*")
MULTISPACE_RE = re.compile(r"[ \t]+")
MULTIBLANK_RE = re.compile(r"\n{3,}")
QUOTE_PREFIX_RE = re.compile(r"^\s*>")
REPLY_HEADER_RE = re.compile(r"^\s*On .+ wrote:\s*$", re.IGNORECASE)
FORWARDED_RE = re.compile(
    r"^\s*-{2,}\s*Forwarded message\s*-{2,}\s*$",
    re.IGNORECASE,
)
SIGNOFF_RE = re.compile(
    r"^\s*(?:best regards|kind regards|regards|best|thanks|thank you|cheers|sincerely)[\s,!.]*$",
    re.IGNORECASE,
)
MOBILE_SIGNATURE_RE = re.compile(
    r"^\s*(?:sent from my iphone|sent from outlook for ios)\s*$",
    re.IGNORECASE,
)
DISCLAIMER_RE = re.compile(
    r"^\s*(?:"
    r"confidential(?:ity notice)?\b|"
    r"disclaimer:\b|"
    r"this email and any attachments are confidential\b|"
    r"this e-mail is intended only\b"
    r").*$",
    re.IGNORECASE,
)
UNSUBSCRIBE_RE = re.compile(r"^\s*to unsubscribe:.*$", re.IGNORECASE)
SEPARATOR_RE = re.compile(r"^\s*(?:[_=-]{2,})\s*$")
EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
PHONE_RE = re.compile(r"(?<!\w)\+?\d[\d\s().-]{7,}\d")
URL_RE = re.compile(r"\b(?:https?://|www\.)\S+\b")


@dataclass(slots=True)
class CleaningStats:
    raw_chars: int
    clean_chars: int = 0
    chars_removed: int = 0
    html_break_tags_removed: int = 0
    html_tags_removed: int = 0
    markdown_markers_removed: int = 0
    quoted_blocks_removed: int = 0
    forwarded_blocks_removed: int = 0
    signature_blocks_removed: int = 0
    disclaimer_blocks_removed: int = 0
    footer_blocks_removed: int = 0
    separator_lines_removed: int = 0
    email_redactions: int = 0
    phone_redactions: int = 0
    url_redactions: int = 0
    truncated_by: str | None = None


def _sub_and_count(pattern: re.Pattern[str], replacement: str, text: str) -> tuple[str, int]:
    updated_text, count = pattern.subn(replacement, text)
    return updated_text, count


def _normalize_markup(text: str, stats: CleaningStats) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = html.unescape(text).replace("\xa0", " ")

    text, count = _sub_and_count(HTML_BREAK_RE, "\n", text)
    stats.html_break_tags_removed += count

    text, count = _sub_and_count(HTML_TAG_RE, "", text)
    stats.html_tags_removed += count

    text, count = _sub_and_count(MARKDOWN_BOLD_RE, r"\1", text)
    stats.markdown_markers_removed += count
    return text


def _redact_pii(line: str, stats: CleaningStats) -> str:
    line, count = _sub_and_count(URL_RE, "<URL>", line)
    stats.url_redactions += count

    line, count = _sub_and_count(EMAIL_RE, "<EMAIL>", line)
    stats.email_redactions += count

    line, count = _sub_and_count(PHONE_RE, "<PHONE>", line)
    stats.phone_redactions += count
    return line


def clean_email_text(raw_text: str) -> tuple[str, dict[str, int | str | None]]:
    """Return cleaned text plus per-file cleaning stats."""
    stats = CleaningStats(raw_chars=len(raw_text))
    text = _normalize_markup(raw_text, stats)

    cleaned_lines: list[str] = []
    content_lines = 0

    for original_line in text.split("\n"):
        line = MULTISPACE_RE.sub(" ", original_line).strip()

        if not line:
            cleaned_lines.append("")
            continue

        if FORWARDED_RE.match(line):
            stats.forwarded_blocks_removed += 1
            stats.truncated_by = "forwarded_message"
            break

        if QUOTE_PREFIX_RE.match(line) or REPLY_HEADER_RE.match(line):
            stats.quoted_blocks_removed += 1
            stats.truncated_by = "quoted_thread"
            break

        if SIGNOFF_RE.match(line) and content_lines > 0:
            stats.signature_blocks_removed += 1
            stats.truncated_by = "signature"
            break

        if MOBILE_SIGNATURE_RE.match(line):
            stats.signature_blocks_removed += 1
            stats.truncated_by = "signature"
            break

        if DISCLAIMER_RE.match(line):
            stats.disclaimer_blocks_removed += 1
            stats.truncated_by = "disclaimer"
            break

        if UNSUBSCRIBE_RE.match(line):
            stats.footer_blocks_removed += 1
            stats.truncated_by = "unsubscribe"
            break

        if SEPARATOR_RE.match(line):
            stats.separator_lines_removed += 1
            continue

        cleaned_lines.append(_redact_pii(line, stats))
        content_lines += 1

    cleaned_text = "\n".join(cleaned_lines)
    cleaned_text = MULTIBLANK_RE.sub("\n\n", cleaned_text).strip()

    stats.clean_chars = len(cleaned_text)
    stats.chars_removed = max(stats.raw_chars - stats.clean_chars, 0)
    return cleaned_text, asdict(stats)


def clean_file(input_path: Path, output_dir: Path) -> dict[str, int | str | None]:
    """Clean a raw email file and write the cleaned output."""
    raw_text = input_path.read_text(encoding="utf-8")
    cleaned_text, stats = clean_email_text(raw_text)

    output_path = output_dir / input_path.name
    trailing_newline = "\n" if cleaned_text else ""
    output_path.write_text(f"{cleaned_text}{trailing_newline}", encoding="utf-8")

    return {
        "source_file": input_path.name,
        "output_file": output_path.name,
        **stats,
    }


def _build_summary(entries: list[dict[str, int | str | None]]) -> dict[str, object]:
    numeric_keys = [
        "raw_chars",
        "clean_chars",
        "chars_removed",
        "html_break_tags_removed",
        "html_tags_removed",
        "markdown_markers_removed",
        "quoted_blocks_removed",
        "forwarded_blocks_removed",
        "signature_blocks_removed",
        "disclaimer_blocks_removed",
        "footer_blocks_removed",
        "separator_lines_removed",
        "email_redactions",
        "phone_redactions",
        "url_redactions",
    ]
    totals = {
        key: sum(int(entry[key]) for entry in entries)
        for key in numeric_keys
    }
    return {
        "processed_files": len(entries),
        **totals,
        "files": entries,
    }


def clean_directory(
    input_dir: Path = RAW_DIR,
    output_dir: Path = CLEAN_DIR,
    report_path: Path | None = None,
    logger: logging.Logger | None = None,
) -> int:
    """Clean all raw email bodies from one directory into another."""
    log = logger or logging.getLogger(__name__)

    if not input_dir.exists():
        raise FileNotFoundError(f"Input directory not found: {input_dir}")

    raw_files = sorted(path for path in input_dir.glob("*.txt") if path.is_file())
    if not raw_files:
        raise FileNotFoundError(f"No raw email files found in: {input_dir}")

    output_dir.mkdir(parents=True, exist_ok=True)
    resolved_report = report_path or output_dir / DEFAULT_REPORT_NAME

    entries: list[dict[str, int | str | None]] = []
    for input_path in raw_files:
        entry = clean_file(input_path, output_dir)
        entries.append(entry)
        log.info(
            "  clean  %s -> %s (%d -> %d chars)",
            entry["source_file"],
            entry["output_file"],
            entry["raw_chars"],
            entry["clean_chars"],
        )

    summary = _build_summary(entries)
    resolved_report.write_text(
        json.dumps(summary, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    log.info("Cleaning report written to %s", resolved_report.resolve())
    log.info(
        "Cleaned %d email(s): %d -> %d chars",
        summary["processed_files"],
        summary["raw_chars"],
        summary["clean_chars"],
    )
    return len(entries)
