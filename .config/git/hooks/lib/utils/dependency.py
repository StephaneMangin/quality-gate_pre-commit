from __future__ import annotations

import ast
from pathlib import Path

from .file import collect_files
from .path import ALWAYS_EXCLUDED_DIRS, MODULE_SEARCH_DIRS, filter_paths_with_env_dirs
from .quality import iter_with_progress

try:
    import networkx as nx
except ImportError:
    nx = None


def load_module_manifests(
    repo_root: Path,
    progress_enabled: bool = False,
    progress_every: int = 1,
) -> dict[str, dict]:
    graph = {}
    max_modules = 2000

    search_dirs = []
    for dirname in MODULE_SEARCH_DIRS:
        search_path = repo_root / dirname
        if search_path.exists():
            search_dirs.append(search_path)

    if not search_dirs:
        search_dirs = [repo_root]

    manifest_files: list[Path] = []
    for search_dir in search_dirs:
        try:
            manifest_files.extend(
                collect_files(
                    search_dir,
                    patterns=["__manifest__.py"],
                    exclude_dirs=ALWAYS_EXCLUDED_DIRS,
                    include_hidden=False,
                )
            )
        except Exception:
            pass

    manifest_files = filter_paths_with_env_dirs(manifest_files, repo_root)

    for manifest_path in iter_with_progress(
        files=manifest_files,
        repo_root=repo_root,
        enabled=progress_enabled,
        prefix="[scan:manifests]",
        every=progress_every,
    ):
        if len(graph) >= max_modules:
            break

        module_dir = manifest_path.parent
        module_name = module_dir.name
        try:
            manifest = ast.literal_eval(manifest_path.read_text(encoding="utf-8"))
            graph[module_name] = {
                "name": manifest.get("name", module_name),
                "depends": manifest.get("depends", []),
                "version": manifest.get("version", "?"),
            }
        except Exception:
            graph[module_name] = {
                "name": module_name,
                "depends": [],
                "version": "?",
            }

    return graph


def build_dependency_graph(manifests: dict[str, dict]):
    if nx is None:
        return None

    graph = nx.DiGraph()

    for module_name in manifests.keys():
        graph.add_node(module_name)

    for module_name, info in manifests.items():
        for dep in info.get("depends", []):
            if dep in manifests:
                graph.add_edge(module_name, dep)

    return graph


def compute_dependency_metrics(manifests: dict[str, dict], graph=None) -> dict:
    metrics = {
        "num_nodes": len(manifests),
        "num_edges": sum(len(info.get("depends", [])) for info in manifests.values()),
        "roots": [],
        "leaves": [],
        "max_centrality_nodes": [],
        "circular_deps": [],
        "missing_deps": [],
        "density": 0.0,
        "avg_in_degree": 0.0,
        "avg_out_degree": 0.0,
    }

    if graph is not None and nx is not None:
        try:
            metrics["density"] = nx.density(graph)

            in_degree = dict(graph.in_degree())
            out_degree = dict(graph.out_degree())

            metrics["roots"] = [node for node, deg in in_degree.items() if deg == 0]
            metrics["leaves"] = [node for node, deg in out_degree.items() if deg == 0]

            in_degrees = list(in_degree.values())
            out_degrees = list(out_degree.values())
            metrics["avg_in_degree"] = (
                sum(in_degrees) / len(in_degrees) if in_degrees else 0
            )
            metrics["avg_out_degree"] = (
                sum(out_degrees) / len(out_degrees) if out_degrees else 0
            )

            try:
                cycles = list(nx.simple_cycles(graph))
                metrics["circular_deps"] = cycles[:10]
            except Exception:
                pass

            try:
                centrality = nx.betweenness_centrality(graph)
                top_5 = sorted(
                    centrality.items(),
                    key=lambda item: item[1],
                    reverse=True,
                )[:5]
                metrics["max_centrality_nodes"] = [
                    (node, float(score)) for node, score in top_5
                ]
            except Exception:
                pass
        except Exception:
            pass

    if metrics["num_nodes"] > 0:
        all_deps = set()
        all_dependents = set()
        for module_name, info in manifests.items():
            deps = info.get("depends", [])
            for dep in deps:
                if dep in manifests:
                    all_deps.add(dep)
                    all_dependents.add(module_name)

        if not metrics["roots"]:
            metrics["roots"] = [m for m in manifests.keys() if m not in all_deps]
        if not metrics["leaves"]:
            metrics["leaves"] = [m for m in manifests.keys() if m not in all_dependents]

        in_degrees = [len(manifests[module].get("depends", [])) for module in manifests]
        out_degrees = [
            sum(1 for _, info in manifests.items() if module in info.get("depends", []))
            for module in manifests
        ]

        if not metrics["avg_in_degree"]:
            metrics["avg_in_degree"] = (
                sum(in_degrees) / metrics["num_nodes"]
                if metrics["num_nodes"] > 0
                else 0
            )
        if not metrics["avg_out_degree"]:
            metrics["avg_out_degree"] = (
                sum(out_degrees) / metrics["num_nodes"]
                if metrics["num_nodes"] > 0
                else 0
            )

        if not metrics["density"] and metrics["num_nodes"] > 1:
            max_edges = metrics["num_nodes"] * (metrics["num_nodes"] - 1)
            metrics["density"] = (
                metrics["num_edges"] / max_edges if max_edges > 0 else 0
            )

    all_module_names = set(manifests.keys())
    missing = []
    for module_name, info in manifests.items():
        for dep in info.get("depends", []):
            if dep not in all_module_names:
                missing.append((module_name, dep))
    metrics["missing_deps"] = missing

    return metrics
