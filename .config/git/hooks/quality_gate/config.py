from __future__ import annotations

import logging
import os
from dataclasses import dataclass


def setup_logging() -> None:
    raw_level = os.getenv("QUALITY_GATE_LOG_LEVEL", "INFO").strip().upper()
    level = getattr(logging, raw_level, logging.INFO)
    logging.basicConfig(level=level, format="[quality-gate] %(levelname)s %(message)s")


@dataclass(frozen=True)
class Settings:
    max_complexity_grade: str
    mode: str
    coverage_min: int
    vulture_min_confidence: int
    no_staged_mode: str
    report_level: str
    progress_enabled: bool
    progress_every: int
    timing_enabled: bool
    grade_order: dict[str, int]


def load_settings() -> Settings:
    report_level = os.getenv("QUALITY_GATE_REPORT", "full").strip().lower()
    if report_level == "brief":
        report_level = "minimal"

    progress_raw = os.getenv("QUALITY_GATE_PROGRESS", "auto").strip().lower()
    if progress_raw in {"1", "true", "yes", "on"}:
        progress_enabled = True
    elif progress_raw in {"0", "false", "no", "off"}:
        progress_enabled = False
    else:
        progress_enabled = report_level == "full"

    return Settings(
        max_complexity_grade=os.getenv("QUALITY_GATE_MAX_COMPLEXITY", "A"),
        mode=os.getenv("QUALITY_GATE_MODE", "hybrid").strip().lower(),
        coverage_min=int(os.getenv("QUALITY_GATE_COVERAGE_MIN", "80")),
        vulture_min_confidence=int(
            os.getenv("QUALITY_GATE_VULTURE_MIN_CONFIDENCE", "100")
        ),
        no_staged_mode=os.getenv("QUALITY_GATE_NO_STAGED", "full").strip().lower(),
        report_level=report_level,
        progress_enabled=progress_enabled,
        progress_every=max(int(os.getenv("QUALITY_GATE_PROGRESS_EVERY", "1")), 1),
        timing_enabled=os.getenv("QUALITY_GATE_TIMING", "0").strip().lower()
        in {"1", "true", "yes", "on"},
        grade_order={"A": 0, "B": 1, "C": 2, "D": 3, "E": 4, "F": 5},
    )
