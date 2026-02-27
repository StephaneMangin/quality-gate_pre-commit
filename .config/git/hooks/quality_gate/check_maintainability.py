from __future__ import annotations

from pathlib import Path

from .config import Settings
from .output import log
from lib.utils.display import iter_with_progress, section_title
from lib.utils.file import collect_python_files
from lib.utils.process import run_cmd
from lib.utils.report import CheckResult
from lib.utils.tool import tool_cmd


def check_maintainability(repo_root: Path, targets: list[str], settings: Settings) -> CheckResult:
    stdout, _, rc = run_cmd([*tool_cmd("radon", repo_root), "mi", *targets, "-s"], repo_root)

    if not stdout.strip():
        py_files = collect_python_files(repo_root, include_hidden=True)
        fallback_target_set: set[str] = set()
        for path in iter_with_progress(
            files=py_files,
            repo_root=repo_root,
            enabled=settings.progress_enabled and settings.report_level == "full",
            prefix="[scan:maintainability]",
            every=settings.progress_every,
        ):
            relative = path.relative_to(repo_root)
            fallback_target_set.add(relative.parts[0] if relative.parts else ".")

        fallback_targets = sorted(fallback_target_set)
        if fallback_targets:
            stdout, _, rc = run_cmd(
                [*tool_cmd("radon", repo_root), "mi", *fallback_targets, "-s"],
                repo_root,
            )

    if settings.report_level == "full":
        section_title("MAINTAINABILITY INDEX  (radon mi)")
        if rc != 0 and not stdout:
            log("  radon mi indisponible (skip)\n")
            return CheckResult("maintainability", True, False, "radon mi unavailable")

        modules_by_grade = {grade: [] for grade in "ABCDEF"}
        for line in stdout.splitlines():
            if " - " in line and "(" in line:
                parts = line.split(" - ")
                if len(parts) == 2:
                    grade_part = parts[1].strip()
                    grade = grade_part[0] if grade_part and grade_part[0] in "ABCDEF" else None
                    if grade:
                        modules_by_grade[grade].append(line.strip())

        total = sum(len(values) for values in modules_by_grade.values())
        if total == 0:
            log("  radon mi unavailable or no results\n")
            return CheckResult("maintainability", True, False, "no results")

        grade_names = {
            "A": "(very maintainable)",
            "B": "(     maintainable)",
            "C": "( somewhat complex)",
            "D": "(          complex)",
            "E": "(     very complex)",
            "F": "(   unmaintainable)",
        }

        log("  Grade distribution:\n")
        for grade in "ABCDEF":
            count = len(modules_by_grade[grade])
            bar_len = 50
            filled = int((count / max(total, 1)) * bar_len) if count > 0 else 0
            bar = "█" * filled + "░" * (bar_len - filled)
            pct = (count / total * 100) if total > 0 else 0
            log(f"    {grade} {grade_names[grade]:<20} {bar} {count:3d} ({pct:5.1f}%)")

        b_and_worse = [module for grade in "BCDEF" for module in modules_by_grade[grade]]
        if b_and_worse:
            log(f"\n  ⚠  {len(b_and_worse)} module(s) rated B or worse:\n")
            for module in b_and_worse[:10]:
                log(f"    {module}")
            if len(b_and_worse) > 10:
                log(f"    … and {len(b_and_worse) - 10} more")
            log()
        else:
            log("\n  ✓ All modules rated A (very maintainable)\n")

    return CheckResult("maintainability", True, False, "maintainability checks passed")
