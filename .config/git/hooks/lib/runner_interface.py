#!/usr/bin/env python3
from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path


class RunnerInterface(ABC):
    """Abstract interface for all hook runners."""

    def __init__(
        self,
        hooks_dir: Path,
        args: list[str],
        env: dict[str, str],
        *,
        include_dirs: str = "",
        exclude_dirs: str = "",
    ) -> None:
        self.hooks_dir = hooks_dir
        self.args = list(args)
        self.env = dict(env)
        self.include_dirs = include_dirs
        self.exclude_dirs = exclude_dirs

    @abstractmethod
    def run(self) -> int:
        """Execute runner and return exit code."""
        raise NotImplementedError
