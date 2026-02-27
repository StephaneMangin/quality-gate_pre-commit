#!/usr/bin/env python3
"""Compatibility wrapper delegating to the canonical orchestrator core."""

from __future__ import annotations

import sys
from pathlib import Path

HOOKS_DIR = Path(__file__).resolve().parents[1]
if str(HOOKS_DIR) not in sys.path:
    sys.path.insert(0, str(HOOKS_DIR))

from lib.precommit_orchestrator import run_precommit_pipeline  # noqa: E402


def main() -> int:
    return run_precommit_pipeline(HOOKS_DIR, sys.argv[1:])


if __name__ == "__main__":
    raise SystemExit(main())
