from __future__ import annotations

from pathlib import Path

from .config import Settings
from .output import log
from lib.utils.display import section_title
from lib.utils.process import run_cmd
from lib.utils.quality import vulture_exclude_csv
from lib.utils.report import CheckResult, is_blocking
from lib.utils.tool import tool_cmd


def check_dead_code(repo_root: Path, targets: list[str], settings: Settings) -> CheckResult:
    cmd = [
        *tool_cmd("vulture", repo_root),
        *targets,
        "--exclude",
        vulture_exclude_csv(),
        "--min-confidence",
        str(settings.vulture_min_confidence),
    ]

    whitelist = repo_root / "vulture_whitelist.py"
    if whitelist.exists():
        cmd.insert(2, str(whitelist.relative_to(repo_root)))

    stdout, _, _ = run_cmd(cmd, repo_root)
    findings = [line for line in stdout.splitlines() if line.strip() and ":" in line]
    passed = len(findings) == 0

    if settings.report_level == "full":
        section_title("DEAD CODE DETECTION  (vulture ≥80% confidence)")
        if findings:
            for line in findings[:5]:
                log(f"  {line}")
            if len(findings) > 5:
                log(f"  … and {len(findings) - 5} more")
            log(f"\n  ✗ FAIL — {len(findings)} dead code finding(s)\n")
        else:
            log("  ✓ PASS — no dead code detected\n")

    details = "aucun code mort détecté" if passed else f"{len(findings)} finding(s)"
    return CheckResult(
        "dead code",
        passed,
        is_blocking(settings.mode, "dead code"),
        details,
    )
