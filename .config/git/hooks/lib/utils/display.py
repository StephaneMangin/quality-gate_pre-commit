from __future__ import annotations

import sys
from pathlib import Path

BLUE = "\033[0;34m"
GREEN = "\033[0;32m"
YELLOW = "\033[1;33m"
RED = "\033[0;31m"
CYAN = "\033[0;36m"
NC = "\033[0m"


def print_section(title: str) -> None:
    print(f"\n{BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{NC}")
    print(f"{BLUE}{title}{NC}")
    print(f"{BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{NC}\n")


def print_success(message: str) -> None:
    print(f"{GREEN}✓ {message}{NC}")


def print_error(message: str) -> None:
    print(f"{RED}✗ {message}{NC}")


def print_skip(message: str) -> None:
    print(f"{YELLOW}⊘ {message}{NC}")


def print_info(message: str) -> None:
    print(f"{CYAN}ℹ {message}{NC}")


def print_warning(message: str) -> None:
    print(f"{YELLOW}⚠ {message}{NC}")


def box_title(title: str) -> None:
    width = 70
    print(f"┌{'─' * width}┐")
    print(f"│ {title.center(width - 2)} │")
    print(f"└{'─' * width}┘\n")


def section_title(title: str) -> None:
    width = 70
    print(f"\n{'═' * width}")
    print(f"  {title}")
    print(f"{'═' * width}\n")


def bar_chart(label: str, count: int, total: int, width: int = 30) -> str:
    if total == 0:
        filled = 0
        pct = 0.0
    else:
        filled = int((count / total) * width)
        pct = count / total * 100
    bar = "█" * filled + "░" * (width - filled)
    return f"    {label:<20} {bar} {count:3d} ({pct:5.1f}%)"


class ProgressReporter:
    """Progress reporter for file scans."""

    def __init__(
        self,
        total: int,
        enabled: bool,
        prefix: str = "[scan]",
        every: int = 1,
    ) -> None:
        self.total = max(total, 0)
        self.enabled = bool(enabled) and self.total > 0
        self.prefix = prefix
        self.every = max(int(every), 1)
        self._is_tty = sys.stdout.isatty()
        self._last_len = 0

    def update(self, index: int, file_path: Path, repo_root: Path | None = None) -> None:
        if not self.enabled:
            return
        if index != self.total and index % self.every != 0:
            return

        shown = file_path
        if repo_root is not None:
            try:
                shown = file_path.relative_to(repo_root)
            except Exception:
                shown = file_path

        pct = (index / self.total) * 100
        msg = f"{self.prefix} {index}/{self.total} ({pct:5.1f}%) file: {shown}"

        if self._is_tty:
            padded = msg.ljust(max(self._last_len, len(msg)))
            print(f"\r{padded}", end="", flush=True)
            self._last_len = len(padded)
        else:
            print(msg)

    def close(self) -> None:
        if self.enabled and self._is_tty:
            print()


def iter_with_progress(
    files: list[Path],
    repo_root: Path,
    enabled: bool,
    prefix: str,
    every: int,
):
    reporter = ProgressReporter(
        total=len(files),
        enabled=enabled,
        prefix=prefix,
        every=every,
    )
    try:
        for index, file_path in enumerate(files, start=1):
            reporter.update(index, file_path, repo_root)
            yield file_path
    finally:
        reporter.close()
