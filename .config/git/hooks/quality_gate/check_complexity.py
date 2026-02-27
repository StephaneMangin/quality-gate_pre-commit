from __future__ import annotations

import re
from pathlib import Path

from .config import Settings
from .output import log
from lib.utils.display import section_title
from lib.utils.process import run_cmd
from lib.utils.report import CheckResult, is_blocking
from lib.utils.tool import tool_cmd


def check_complexity(repo_root: Path, targets: list[str], settings: Settings) -> CheckResult:
    stdout, _, rc = run_cmd(
        [*tool_cmd("radon", repo_root), "cc", *targets, "-s", "-nc"],
        repo_root,
    )
    if rc != 0 and not stdout:
        return CheckResult(
            "complexity",
            True,
            is_blocking(settings.mode, "complexity"),
            "radon indisponible",
        )

    if settings.report_level == "full":
        section_title("CYCLOMATIC COMPLEXITY REPORT  (radon cc)")
        grade_counts = {g: 0 for g in "ABCDEF"}
        functions_at_ceiling: list[str] = []

        for line in stdout.splitlines():
            for grade in "ABCDEF":
                if f" {grade} " in line and " - " in line:
                    grade_counts[grade] += 1
                    if settings.grade_order.get(grade, 5) >= settings.grade_order.get(
                        settings.max_complexity_grade,
                        2,
                    ):
                        parts = line.split(" - ")
                        if len(parts) >= 2:
                            functions_at_ceiling.append(parts[0].strip())
                    break

        total = sum(grade_counts.values())
        grade_names = {
            "A": "(               simple)",
            "B": "(      well structured)",
            "C": "(     slightly complex)",
            "D": "(         more complex)",
            "E": "(      high complexity)",
            "F": "( very high complexity)",
        }

        log("  Grade distribution:\n")
        for grade in "ABCDEF":
            count = grade_counts[grade]
            bar_len = 50
            filled = int((count / max(total, 1)) * bar_len) if count > 0 else 0
            bar = "█" * filled + "░" * (bar_len - filled)
            pct = (count / total * 100) if total > 0 else 0
            marker = " ◄── ceiling" if grade == settings.max_complexity_grade else ""
            log(
                f"    {grade} {grade_names[grade]:<20} {bar} {count:3d} ({pct:5.1f}%){marker}"
            )

        if total > 0:
            weights = {"A": 1, "B": 2, "C": 3, "D": 4, "E": 5, "F": 6}
            avg_weight = sum(grade_counts[g] * weights[g] for g in "ABCDEF") / total
            avg_grade = min("ABCDEF", key=lambda grade: abs(weights[grade] - avg_weight))
            log(f"\n  Average complexity: {avg_grade}")
        else:
            log("\n  Average complexity: N/A")

        if functions_at_ceiling:
            log(
                f"\n  ⚠  {len(functions_at_ceiling)} function(s) at grade {settings.max_complexity_grade} or worse:\n"
            )
            for func in functions_at_ceiling[:6]:
                log(f"    ✗ {func}")
            if len(functions_at_ceiling) > 6:
                log(f"    … and {len(functions_at_ceiling) - 6} more")
            log(f"\n  ✓ PASS — no function exceeds grade {settings.max_complexity_grade}")
        elif total > 0:
            log(f"\n  ✓ PASS — no function exceeds grade {settings.max_complexity_grade}")
        log()

    grades = re.findall(r"([A-F])", stdout)
    violating = [
        grade
        for grade in grades
        if settings.grade_order.get(grade, 5)
        > settings.grade_order.get(settings.max_complexity_grade, 2)
    ]
    passed = len(violating) == 0
    details = (
        "seuil respecté"
        if passed
        else f"{len(violating)} fonction(s) > {settings.max_complexity_grade}"
    )
    return CheckResult(
        "complexity",
        passed,
        is_blocking(settings.mode, "complexity"),
        details,
    )
