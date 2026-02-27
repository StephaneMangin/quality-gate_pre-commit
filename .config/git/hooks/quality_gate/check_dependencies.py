from __future__ import annotations

from pathlib import Path

from .config import Settings
from .output import log
from lib.utils.dependency import (
    build_dependency_graph,
    compute_dependency_metrics,
    load_module_manifests,
)
from lib.utils.display import section_title
from lib.utils.report import CheckResult, is_blocking


def check_module_dependencies(repo_root: Path, settings: Settings) -> CheckResult:
    manifests = load_module_manifests(
        repo_root,
        progress_enabled=settings.progress_enabled and settings.report_level == "full",
        progress_every=settings.progress_every,
    )

    if not manifests:
        if settings.report_level == "full":
            section_title("MODULE DEPENDENCY GRAPH COMPLEXITY")
            log("  ⚠  No manifest-based modules found\n")
        return CheckResult("module dependencies", True, False, "no module manifests")

    graph = build_dependency_graph(manifests)
    metrics = compute_dependency_metrics(manifests, graph)

    if settings.report_level == "full":
        section_title("MODULE DEPENDENCY GRAPH COMPLEXITY")
        log("  📦 Graph Overview:")
        log(f"    • Modules:            {metrics['num_nodes']:>3d}")
        log(f"    • Dependencies:       {metrics['num_edges']:>3d}")
        log(f"    • Density:            {metrics['density']:>6.2%}")
        log(f"    • Avg dependencies:   {metrics['avg_in_degree']:>6.2f}")
        log(f"    • Avg dependents:     {metrics['avg_out_degree']:>6.2f}")
        log()

        log("  🏗  Dependency Architecture:")
        log(f"    • Root modules:       {len(metrics['roots']):>3d} (with no dependencies)")
        log(f"    • Leaf modules:       {len(metrics['leaves']):>3d} (with no dependents)")
        log()

        if metrics["max_centrality_nodes"]:
            log("  🎯 Most Critical Modules (betweenness centrality):\n")
            for index, (node, score) in enumerate(metrics["max_centrality_nodes"], 1):
                bar_width = 30
                filled = int(score * bar_width)
                bar = "█" * filled + "░" * (bar_width - filled)
                log(f"    {index}. {node:<25s} {bar} {score:.3f}")
            log()

        if metrics["roots"]:
            log("  📍 Root Modules (no dependencies):\n")
            for root in sorted(metrics["roots"])[:5]:
                dependents_count = sum(
                    1
                    for _, info in manifests.items()
                    if root in info.get("depends", [])
                )
                log(f"    • {root:<30s} ({dependents_count:3d} dependents)")
            if len(metrics["roots"]) > 5:
                log(f"    • ... and {len(metrics['roots']) - 5} more")
            log()

        issues_count = len(metrics["circular_deps"]) + len(metrics["missing_deps"])
        if issues_count > 0:
            log("  ⚠  Issues Detected:\n")
            for cycle in metrics["circular_deps"][:3]:
                cycle_str = " → ".join(cycle) + f" → {cycle[0]}"
                log(f"    ✗ Cycle: {cycle_str}")
            for addon, missing_dep in metrics["missing_deps"][:3]:
                log(f"    ✗ Missing: {addon} → {missing_dep}")
            if issues_count > 6:
                log(f"    … and {issues_count - 6} more issue(s)")
            log()
        else:
            log("  ✓ PASS — clean dependency graph\n")

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
        issue_types: list[str] = []
        if metrics["circular_deps"]:
            issue_types.append(f"{len(metrics['circular_deps'])} cycle(s)")
        if metrics["missing_deps"]:
            issue_types.append(f"{len(metrics['missing_deps'])} missing")
        details = ", ".join(issue_types)

    return CheckResult(
        "module dependencies",
        passed,
        is_blocking(settings.mode, "module dependencies"),
        details,
    )
