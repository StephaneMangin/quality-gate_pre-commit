from __future__ import annotations

from pathlib import Path

from .config import Settings
from .output import log
from lib.utils.display import section_title
from lib.utils.process import run_cmd
from lib.utils.report import CheckResult
from lib.utils.tool import tool_cmd


def extract_coverage_percent(report_stdout: str, report_stderr: str) -> float | None:
    merged = report_stdout + "\n" + report_stderr
    for line in merged.splitlines():
        if "TOTAL" not in line or "%" not in line:
            continue
        for token in reversed(line.split()):
            if token.endswith("%"):
                try:
                    return float(token.rstrip("%"))
                except ValueError:
                    continue
    return None


def check_coverage(repo_root: Path, settings: Settings) -> CheckResult:
    if settings.report_level == "full":
        section_title("TEST COVERAGE  (minimum: 40%)")

    if not (repo_root / ".coverage").exists():
        if settings.report_level == "full":
            log("  coverage non lisible (skip)\n")
        return CheckResult("coverage", True, False, "pas de fichier .coverage")

    stdout, stderr, _ = run_cmd(
        [*tool_cmd("coverage", repo_root), "report", f"--fail-under={settings.coverage_min}"],
        repo_root,
    )

    if settings.report_level == "full":
        pct = extract_coverage_percent(stdout, stderr)
        if pct is not None:
            bar_width = 50
            filled = int((pct / 100) * bar_width)
            bar = "█" * filled + "░" * (bar_width - filled)
            marker = "▲" if pct < settings.coverage_min else "✓"
            log(f"  {bar}  {pct:.1f}%")
            if pct < settings.coverage_min:
                log(
                    f"  {' ' * (bar_width // 2)}{marker} {settings.coverage_min}% minimum required"
                )

            lines = [line for line in stdout.splitlines() if line.strip() and "%" in line]
            low_coverage = [
                (line.split()[0], float(line.split()[-1].rstrip("%")))
                for line in lines
                if float(line.split()[-1].rstrip("%")) < 50
            ]
            if low_coverage:
                log("\n  Lowest-coverage modules (< 50%):\n")
                for path, pct_value in low_coverage[:10]:
                    bar = "░" * 30
                    log(f"    {bar}   {pct_value:5.1f}%  {path}")
                if len(low_coverage) > 10:
                    log(f"    … and {len(low_coverage) - 10} more")
            log()

    pct = extract_coverage_percent(stdout, stderr)
    if pct is None:
        return CheckResult("coverage", True, False, "coverage non lisible")

    return CheckResult("coverage", True, False, f"{pct:.1f}% (min {settings.coverage_min}%)")
