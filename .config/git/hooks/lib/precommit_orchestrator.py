#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import os
from pathlib import Path

from .utils.display import BLUE, GREEN, NC, RED
from .utils.env import activate_repo_venv, load_env_overrides, repo_root
from .utils.path import PathPolicy


def _load_runner_class(script: Path, class_name: str):
    module_name = f"runner_{script.stem.replace('-', '_')}_{class_name}"
    spec = importlib.util.spec_from_file_location(module_name, script)
    if spec is None or spec.loader is None:
        return None

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return getattr(module, class_name, None)


class RunnerManager:
    def __init__(self, hooks_dir: Path, env: dict[str, str]) -> None:
        self.hooks_dir = hooks_dir
        self.env = env

    def run(
        self, runner_specs: list[tuple[str, Path, str, list[str], dict[str, str]]]
    ) -> list[str]:
        failures: list[str] = []

        for label, script, class_name, runner_args, runner_kwargs in runner_specs:
            if not script.is_file():
                print(f"{BLUE}ℹ Runner script missing, skip: {script}{NC}")
                continue

            runner_class = _load_runner_class(script, class_name)
            if runner_class is None:
                failures.append(label)
                continue

            runner = runner_class(
                self.hooks_dir,
                runner_args,
                self.env.copy(),
                **runner_kwargs,
            )
            if int(runner.run()) != 0:
                failures.append(label)

        return failures


class PrecommitOrchestrator:
    def __init__(self, hooks_dir: Path, args: list[str], base_env: dict[str, str] | None = None) -> None:
        self.hooks_dir = hooks_dir
        self.args = list(args)
        self.env = dict(base_env or os.environ)

        self.repo_root = repo_root()
        load_env_overrides(self.env, self.repo_root)
        activate_repo_venv(self.env, self.repo_root)

        self.path_policy = PathPolicy.from_env(self.hooks_dir, self.env)
        self.path_policy.apply(self.env)

    def _runner_specs(self) -> list[tuple[str, Path, str, list[str], dict[str, str]]]:
        include_dirs = self.path_policy.include_dirs
        exclude_dirs = self.path_policy.exclude_dirs

        return [
            (
                "Global pre-commit hooks",
                self.hooks_dir / "runners" / "run-global-precommit.py",
                "GlobalPrecommitRunner",
                self.args,
                {"include_dirs": include_dirs, "exclude_dirs": exclude_dirs},
            ),
            (
                "Quality gate",
                self.hooks_dir / "runners" / "run-quality-gate.py",
                "QualityGateRunner",
                [],
                {"include_dirs": include_dirs, "exclude_dirs": exclude_dirs},
            ),
            (
                "Local pre-commit hooks",
                self.hooks_dir / "runners" / "run-local-precommit.py",
                "LocalPrecommitRunner",
                self.args,
                {"include_dirs": include_dirs, "exclude_dirs": exclude_dirs},
            ),
            (
                "Module tests",
                self.hooks_dir / "runners" / "run-odoo-tests.py",
                "OdooTestsRunner",
                [],
                {"include_dirs": include_dirs, "exclude_dirs": exclude_dirs},
            ),
        ]

    def run(self) -> int:
        failures = RunnerManager(self.hooks_dir, self.env).run(self._runner_specs())

        print()
        if failures:
            print(f"{RED}✗ Some checks failed:{NC}")
            for label in failures:
                print(f"  - {label}")
            print(
                f"\n{RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{NC}"
            )
            print(f"{RED}✗ Checks failed. Please fix the issues before committing.{NC}")
            print(
                f"{RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{NC}\n"
            )
            return 1

        print(f"{GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{NC}")
        print(f"{GREEN}✓ All checks passed! Ready to commit. 🎉{NC}")
        print(f"{GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{NC}\n")
        return 0


def run_precommit_pipeline(hooks_dir: Path, args: list[str]) -> int:
    return PrecommitOrchestrator(hooks_dir, args).run()
