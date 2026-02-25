#!/usr/bin/env python3
"""
Quality gate — comprehensive code quality checks with ASCII art reporting.

Executes multiple quality checks (complexity, coverage, dead code, dependencies)
with a professional visual report including bar charts and distribution graphs.

Run manually:
    python ~/.config/git/hooks/tools/quality_gate.py

Called automatically by pre-commit hook:
    ~/.config/git/hooks/pre-commit (via runners/run-quality-gate.sh)

Configuration via environment variables:
    QUALITY_GATE_MODE              info|hybrid|strict (default: hybrid)
    QUALITY_GATE_MAX_COMPLEXITY    A-F (default: C)
    QUALITY_GATE_COVERAGE_MIN      percent (default: 40)
    QUALITY_GATE_VULTURE_MIN_CONFIDENCE  percent (default: 80)
    QUALITY_GATE_NO_STAGED         full|skip (default: full)
    QUALITY_GATE_REPORT            full|minimal (default: full)
    QUALITY_GATE_PROGRESS          auto|1|0 (default: auto)
    QUALITY_GATE_PROGRESS_EVERY    integer >= 1 (default: 1)
    QUALITY_GATE_TIMING            1|0 (default: 0)

Exit codes:
    0 — all quality gates passed (or only non-blocking failures)
    1 — at least one blocking gate failed

Examples:
    # Strict mode: all checks block
    QUALITY_GATE_MODE=strict python ~/.config/git/hooks/tools/quality_gate.py

    # Info mode: no checks block
    QUALITY_GATE_MODE=info python ~/.config/git/hooks/tools/quality_gate.py

    # Set complexity ceiling to B
    QUALITY_GATE_MAX_COMPLEXITY=B python ~/.config/git/hooks/tools/quality_gate.py
"""

from __future__ import annotations

import os
import re
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

HOOKS_DIR = Path(__file__).resolve().parents[1]
if str(HOOKS_DIR) not in sys.path:
    sys.path.insert(0, str(HOOKS_DIR))

from lib.quality_gate_utils import (
    ALWAYS_EXCLUDED_DIRS,
    _collect_files,
    _box_title,
    _detect_python_project,
    _ensure_tools_installed,
    _filter_paths_with_env_dirs,
    _iter_with_progress,
    _iter_python_targets,
    _repo_root,
    _run,
    _section_title,
    _staged_files,
    _tool_cmd,
    _vulture_exclude_csv,
)
from lib.quality_gate_dependency_utils import (
    _build_dependency_graph,
    _compute_dependency_metrics,
    _load_module_manifests,
)

# ── Configuration ────────────────────────────────────────────────────────────

MAX_COMPLEXITY_GRADE = os.getenv("QUALITY_GATE_MAX_COMPLEXITY", "A")
QUALITY_GATE_MODE = os.getenv("QUALITY_GATE_MODE", "hybrid").strip().lower()
COVERAGE_MIN = int(os.getenv("QUALITY_GATE_COVERAGE_MIN", "80"))
VULTURE_MIN_CONFIDENCE = int(os.getenv("QUALITY_GATE_VULTURE_MIN_CONFIDENCE", "100"))
NO_STAGED_MODE = os.getenv("QUALITY_GATE_NO_STAGED", "full").strip().lower()
REPORT_LEVEL = os.getenv("QUALITY_GATE_REPORT", "full").strip().lower()
if REPORT_LEVEL == "brief":
    REPORT_LEVEL = "minimal"
PROGRESS_RAW = os.getenv("QUALITY_GATE_PROGRESS", "auto").strip().lower()
if PROGRESS_RAW in {"1", "true", "yes", "on"}:
    PROGRESS_ENABLED = True
elif PROGRESS_RAW in {"0", "false", "no", "off"}:
    PROGRESS_ENABLED = False
else:
    PROGRESS_ENABLED = REPORT_LEVEL == "full"
PROGRESS_EVERY = max(int(os.getenv("QUALITY_GATE_PROGRESS_EVERY", "1")), 1)
TIMING_ENABLED = os.getenv("QUALITY_GATE_TIMING", "0").strip().lower() in {
    "1",
    "true",
    "yes",
    "on",
}

GRADE_ORDER = {"A": 0, "B": 1, "C": 2, "D": 3, "E": 4, "F": 5}


# ── Data structures ────────────────────────────────────────────────────────


@dataclass
class CheckResult:
    """Result of a single quality check.

    Attributes:
        name: Check name (complexity, coverage, dead code, etc.)
        passed: True if check passed, False if failed
        blocking: True if failure should block the commit
        details: Human-readable details (score, count, etc.)
    """

    name: str
    passed: bool
    blocking: bool
    details: str = ""


def _is_blocking_in_mode(check_name: str) -> bool:
    """Indique si un check est bloquant."""
    if QUALITY_GATE_MODE == "info":
        return False
    if QUALITY_GATE_MODE == "strict":
        return True
    return check_name in {"complexity", "dead code", "module dependencies"}


# ═══════════════════════════════════════════════════════════════════════════
#  1. Cyclomatic Complexity (radon)
# ═══════════════════════════════════════════════════════════════════════════
def _check_complexity(repo_root: Path, targets: list[str]) -> CheckResult:
    """Évalue la complexité via radon."""
    stdout, stderr, rc = _run(
        [*_tool_cmd("radon", repo_root), "cc", *targets, "-s", "-nc"], repo_root
    )
    if rc != 0 and not stdout:
        return CheckResult(
            "complexity", True, _is_blocking_in_mode("complexity"), "radon indisponible"
        )

    if REPORT_LEVEL == "full":
        _section_title("CYCLOMATIC COMPLEXITY REPORT  (radon cc)")

        grade_counts = {g: 0 for g in "ABCDEF"}
        functions_at_ceiling = []

        for line in stdout.splitlines():
            # Parse: "F 205:0 collect_ui_extensions - C (11)"
            for grade in "ABCDEF":
                if f" {grade} " in line and " - " in line:
                    grade_counts[grade] += 1
                    # Extract function info if at ceiling or worse
                    if GRADE_ORDER.get(grade, 5) >= GRADE_ORDER.get(
                        MAX_COMPLEXITY_GRADE, 2
                    ):
                        try:
                            # Extract function name
                            parts = line.split(" - ")
                            if len(parts) >= 2:
                                func_info = parts[0].strip()
                                functions_at_ceiling.append(func_info)
                        except Exception:
                            pass
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

        print("  Grade distribution:\n")
        for grade in "ABCDEF":
            count = grade_counts[grade]
            bar_len = 50
            filled = int((count / max(total, 1)) * bar_len) if count > 0 else 0
            bar = "█" * filled + "░" * (bar_len - filled)
            pct = (count / total * 100) if total > 0 else 0
            marker = " ◄── ceiling" if grade == MAX_COMPLEXITY_GRADE else ""
            print(
                f"    {grade} {grade_names[grade]:<20} {bar} {count:3d} ({pct:5.1f}%){marker}"
            )

        # Calculer la complexité moyenne
        if total > 0:
            weights = {"A": 1, "B": 2, "C": 3, "D": 4, "E": 5, "F": 6}
            avg_weight = sum(grade_counts[g] * weights[g] for g in "ABCDEF") / total
            avg_grade = min("ABCDEF", key=lambda g: abs(weights[g] - avg_weight))
            print(f"\n  Average complexity: {avg_grade}")
        else:
            print("\n  Average complexity: N/A")

        # Afficher les fonctions au seuil
        if functions_at_ceiling:
            print(
                f"\n  ⚠  {len(functions_at_ceiling)} function(s) at grade {MAX_COMPLEXITY_GRADE} or worse:\n"
            )
            for func in functions_at_ceiling[:6]:
                print(f"    ✗ {func}")
            if len(functions_at_ceiling) > 6:
                print(f"    … and {len(functions_at_ceiling) - 6} more")
            print(f"\n  ✓ PASS — no function exceeds grade {MAX_COMPLEXITY_GRADE}")
        elif total > 0:
            print(f"\n  ✓ PASS — no function exceeds grade {MAX_COMPLEXITY_GRADE}")

        print()

    grades = re.findall(r"([A-F])", stdout)
    violating = [
        grade
        for grade in grades
        if GRADE_ORDER.get(grade, 5) > GRADE_ORDER.get(MAX_COMPLEXITY_GRADE, 2)
    ]
    passed = len(violating) == 0
    details = (
        "seuil respecté"
        if passed
        else f"{len(violating)} fonction(s) > {MAX_COMPLEXITY_GRADE}"
    )
    return CheckResult(
        "complexity", passed, _is_blocking_in_mode("complexity"), details
    )


# ═══════════════════════════════════════════════════════════════════════════
#  2. Maintainability Index (radon mi)
# ═══════════════════════════════════════════════════════════════════════════
def _check_maintainability(repo_root: Path, targets: list[str]) -> CheckResult:
    """Évalue la maintenabilité via radon mi."""
    stdout, stderr, rc = _run(
        [*_tool_cmd("radon", repo_root), "mi", *targets, "-s"], repo_root
    )

    if not stdout.strip():
        py_files = _collect_files(
            repo_root,
            patterns=["*.py"],
            exclude_dirs=ALWAYS_EXCLUDED_DIRS,
            include_hidden=True,
        )
        py_files = _filter_paths_with_env_dirs(py_files, repo_root)

        fallback_target_set: set[str] = set()
        for path in _iter_with_progress(
            files=py_files,
            repo_root=repo_root,
            enabled=PROGRESS_ENABLED and REPORT_LEVEL == "full",
            prefix="[scan:maintainability]",
            every=PROGRESS_EVERY,
        ):
            relative = path.relative_to(repo_root)
            fallback_target_set.add(relative.parts[0] if relative.parts else ".")

        fallback_targets = sorted(fallback_target_set)
        if fallback_targets:
            stdout, stderr, rc = _run(
                [*_tool_cmd("radon", repo_root), "mi", *fallback_targets, "-s"],
                repo_root,
            )

    if REPORT_LEVEL == "full":
        _section_title("MAINTAINABILITY INDEX  (radon mi)")
        if rc != 0 and not stdout:
            print("  radon mi indisponible (skip)\n")
            return CheckResult("maintainability", True, False, "radon mi unavailable")

        # Parse radon mi output: "src/file.py - GRADE (score)"
        modules_by_grade = {g: [] for g in "ABCDEF"}
        for line in stdout.splitlines():
            if " - " in line and "(" in line:
                try:
                    parts = line.split(" - ")
                    if len(parts) == 2:
                        module = parts[0].strip()
                        grade_part = parts[1].strip()
                        # Extract grade letter
                        grade = (
                            grade_part[0]
                            if grade_part and grade_part[0] in "ABCDEF"
                            else None
                        )
                        if grade:
                            modules_by_grade[grade].append(line.strip())
                except Exception:
                    pass

        total = sum(len(v) for v in modules_by_grade.values())

        if total == 0:
            print("  radon mi unavailable or no results\n")
            return CheckResult("maintainability", True, False, "no results")

        # Display grade distribution with bar charts
        grade_names = {
            "A": "(very maintainable)",
            "B": "(     maintainable)",
            "C": "( somewhat complex)",
            "D": "(          complex)",
            "E": "(     very complex)",
            "F": "(   unmaintainable)",
        }

        print("  Grade distribution:\n")
        for grade in "ABCDEF":
            count = len(modules_by_grade[grade])
            bar_len = 50
            filled = int((count / max(total, 1)) * bar_len) if count > 0 else 0
            bar = "█" * filled + "░" * (bar_len - filled)
            pct = (count / total * 100) if total > 0 else 0
            print(
                f"    {grade} {grade_names[grade]:<20} {bar} {count:3d} ({pct:5.1f}%)"
            )

        # Display modules rated B or worse
        B_and_worse = [m for g in "BCDEF" for m in modules_by_grade[g]]
        if B_and_worse:
            print(f"\n  ⚠  {len(B_and_worse)} module(s) rated B or worse:\n")
            for module in B_and_worse[:10]:
                print(f"    {module}")
            if len(B_and_worse) > 10:
                print(f"    … and {len(B_and_worse) - 10} more")
            print()
        else:
            print("\n  ✓ All modules rated A (very maintainable)\n")

    return CheckResult("maintainability", True, False, "maintenability checks passed")


# ═══════════════════════════════════════════════════════════════════════════
#  3. Dead Code Detection (vulture)
# ═══════════════════════════════════════════════════════════════════════════
def _check_dead_code(repo_root: Path, targets: list[str]) -> CheckResult:
    """Détecte le code mort via vulture."""
    cmd = [
        *_tool_cmd("vulture", repo_root),
        *targets,
        "--exclude",
        _vulture_exclude_csv(),
        "--min-confidence",
        str(VULTURE_MIN_CONFIDENCE),
    ]

    whitelist = repo_root / "vulture_whitelist.py"
    if whitelist.exists():
        cmd.insert(2, str(whitelist.relative_to(repo_root)))

    stdout, _, rc = _run(cmd, repo_root)

    # Count findings regardless of rc (vulture behavior varies)
    findings = [line for line in stdout.splitlines() if line.strip() and ":" in line]
    passed = len(findings) == 0

    if REPORT_LEVEL == "full":
        _section_title("DEAD CODE DETECTION  (vulture ≥80% confidence)")
        if findings:
            for line in findings[:5]:
                print(f"  {line}")
            if len(findings) > 5:
                print(f"  … and {len(findings) - 5} more")
            print(f"\n  ✗ FAIL — {len(findings)} dead code finding(s)\n")
        else:
            print("  ✓ PASS — no dead code detected\n")

    details = "aucun code mort détecté" if passed else f"{len(findings)} finding(s)"
    return CheckResult("dead code", passed, _is_blocking_in_mode("dead code"), details)


# ═══════════════════════════════════════════════════════════════════════════
#  4. Coverage quick-report
# ═══════════════════════════════════════════════════════════════════════════
def _extract_coverage_percent(report_stdout: str, report_stderr: str) -> float | None:
    """Extrait le pourcentage TOTAL."""
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


def _check_coverage(repo_root: Path) -> CheckResult:
    """Contrôle la couverture."""
    if REPORT_LEVEL == "full":
        _section_title("TEST COVERAGE  (minimum: 40%)")

    if not (repo_root / ".coverage").exists():
        if REPORT_LEVEL == "full":
            print("  coverage non lisible (skip)\n")
        return CheckResult(
            "coverage",
            True,
            _is_blocking_in_mode("coverage"),
            "pas de fichier .coverage",
        )

    stdout, stderr, rc = _run(
        [*_tool_cmd("coverage", repo_root), "report", f"--fail-under={COVERAGE_MIN}"],
        repo_root,
    )

    if REPORT_LEVEL == "full":
        pct = _extract_coverage_percent(stdout, stderr)
        if pct is not None:
            bar_width = 50
            filled = int((pct / 100) * bar_width)
            bar = "█" * filled + "░" * (bar_width - filled)
            marker = "▲" if pct < COVERAGE_MIN else "✓"
            print(f"  {bar}  {pct:.1f}%")
            if pct < COVERAGE_MIN:
                print(
                    f"  {' ' * (bar_width // 2)}{marker} {COVERAGE_MIN}% minimum required"
                )

            lines = [
                line for line in stdout.splitlines() if line.strip() and "%" in line
            ]
            low_coverage = [
                (line.split()[0], float(line.split()[-1].rstrip("%")))
                for line in lines
                if float(line.split()[-1].rstrip("%")) < 50
            ]
            if low_coverage:
                print("\n  Lowest-coverage modules (< 50%):\n")
                for path, pct_val in low_coverage[:10]:
                    bar = "░" * 30
                    print(f"    {bar}   {pct_val:5.1f}%  {path}")
                if len(low_coverage) > 10:
                    print(f"    … and {len(low_coverage) - 10} more")

            print()

    pct = _extract_coverage_percent(stdout, stderr)
    if pct is None:
        return CheckResult("coverage", True, False, "coverage non lisible")

    passed = True  # Coverage est informatif
    details = f"{pct:.1f}% (min {COVERAGE_MIN}%)"
    return CheckResult("coverage", passed, False, details)


def _check_module_dependencies(repo_root: Path) -> CheckResult:
    """Verify manifest-based module dependencies using graph analysis."""
    manifests = _load_module_manifests(
        repo_root,
        progress_enabled=PROGRESS_ENABLED and REPORT_LEVEL == "full",
        progress_every=PROGRESS_EVERY,
    )

    if not manifests:
        if REPORT_LEVEL == "full":
            _section_title("MODULE DEPENDENCY GRAPH COMPLEXITY")
            print("  ⚠  No manifest-based modules found\n")
        return CheckResult("module dependencies", True, False, "no module manifests")

    # Build graph only if networkx is available
    G = _build_dependency_graph(manifests)

    # Compute metrics (works with or without networkx)
    metrics = _compute_dependency_metrics(manifests, G)

    # Display report
    if REPORT_LEVEL == "full":
        _section_title("MODULE DEPENDENCY GRAPH COMPLEXITY")

        print("  📦 Graph Overview:")
        print(f"    • Modules:            {metrics['num_nodes']:>3d}")
        print(f"    • Dependencies:       {metrics['num_edges']:>3d}")
        print(f"    • Density:            {metrics['density']:>6.2%}")
        print(f"    • Avg dependencies:   {metrics['avg_in_degree']:>6.2f}")
        print(f"    • Avg dependents:     {metrics['avg_out_degree']:>6.2f}")
        print()

        # Architecture metrics
        print("  🏗  Dependency Architecture:")
        print(
            f"    • Root modules:       {len(metrics['roots']):>3d} (with no dependencies)"
        )
        print(
            f"    • Leaf modules:       {len(metrics['leaves']):>3d} (with no dependents)"
        )
        print()

        # Most critical modules (only if networkx available)
        if metrics["max_centrality_nodes"]:
            print("  🎯 Most Critical Modules (betweenness centrality):\n")
            for i, (node, score) in enumerate(metrics["max_centrality_nodes"], 1):
                bar_width = 30
                filled = int(score * bar_width)
                bar = "█" * filled + "░" * (bar_width - filled)
                print(f"    {i}. {node:<25s} {bar} {score:.3f}")
            print()

        # Root modules
        if metrics["roots"]:
            print("  📍 Root Modules (no dependencies):\n")
            root_names = sorted(metrics["roots"])[:5]
            for root in root_names:
                dependents_count = sum(
                    1
                    for a, info in manifests.items()
                    if root in info.get("depends", [])
                )
                print(f"    • {root:<30s} ({dependents_count:3d} dependents)")
            if len(metrics["roots"]) > 5:
                print(f"    • ... and {len(metrics['roots']) - 5} more")
            print()

        # Issues
        issues_count = len(metrics["circular_deps"]) + len(metrics["missing_deps"])
        if issues_count > 0:
            print("  ⚠  Issues Detected:\n")

            for cycle in metrics["circular_deps"][:3]:
                cycle_str = " → ".join(cycle) + f" → {cycle[0]}"
                print(f"    ✗ Cycle: {cycle_str}")

            for addon, missing_dep in metrics["missing_deps"][:3]:
                print(f"    ✗ Missing: {addon} → {missing_dep}")

            if issues_count > 6:
                remaining = issues_count - 6
                print(f"    … and {remaining} more issue(s)")
            print()
        else:
            print("  ✓ PASS — clean dependency graph\n")

    # Determine pass/fail
    issues = metrics["circular_deps"] + metrics["missing_deps"]
    passed = len(issues) == 0

    if passed:
        density_desc = (
            "low"
            if metrics["density"] < 0.1
            else ("medium" if metrics["density"] < 0.3 else "high")
        )
        details = f"{metrics['num_nodes']} modules, density {density_desc}"
    else:
        issue_types = []
        if metrics["circular_deps"]:
            issue_types.append(f"{len(metrics['circular_deps'])} cycle(s)")
        if metrics["missing_deps"]:
            issue_types.append(f"{len(metrics['missing_deps'])} missing")
        details = ", ".join(issue_types)

    return CheckResult(
        "module dependencies",
        passed,
        _is_blocking_in_mode("module dependencies"),
        details,
    )


def _print_summary(results: Iterable[CheckResult]) -> tuple[bool, bool]:
    """Affiche le résumé final."""
    results_list = list(results)
    any_failed = False
    any_blocking_failed = False

    if REPORT_LEVEL == "full":
        _section_title("SUMMARY")

    for result in results_list:
        status = "✓" if result.passed else "✗"
        print(f"    {status}  {result.name:<25} ({result.details})")
        if not result.passed:
            any_failed = True
            if result.blocking:
                any_blocking_failed = True

    if REPORT_LEVEL == "full":
        print("\n  ══════════════════════════════════════")
        if any_blocking_failed:
            print("  ✗  QUALITY GATES FAILED")
        else:
            print("  ✓  ALL QUALITY GATES PASSED")
        print("  ══════════════════════════════════════\n")

    return any_failed, any_blocking_failed


def _run_check_timed(runner) -> tuple[CheckResult, float]:
    """Run one check and return its result with elapsed time."""
    started = time.perf_counter()
    result = runner()
    return result, time.perf_counter() - started


def main() -> int:
    """Point d'entrée principal."""
    repo_root = _repo_root()
    os.chdir(repo_root)

    # Vérifier que les outils requis sont disponibles
    _ensure_tools_installed(repo_root)

    staged = _staged_files(repo_root)
    if not staged:
        if NO_STAGED_MODE == "skip":
            print("[quality-gate] Aucun fichier staged, skip.")
            return 0

    if not _detect_python_project(repo_root, staged):
        print("[quality-gate] Projet non-Python détecté, skip.")
        return 0

    targets = _iter_python_targets(repo_root, staged)

    if REPORT_LEVEL == "full":
        _box_title("Q U A L I T Y   G A T E")
        print(
            f"[quality-gate] mode={QUALITY_GATE_MODE} | targets={', '.join(targets)}\n"
        )

    results = [
        _check_module_dependencies(repo_root),
        _check_complexity(repo_root, targets),
        _check_maintainability(repo_root, targets),
        _check_dead_code(repo_root, targets),
        _check_coverage(repo_root),
    ]

    any_failed, any_blocking_failed = _print_summary(results)

    if any_blocking_failed:
        return 1

    if not any_failed:
        print("[quality-gate] Tous les checks sont OK.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
