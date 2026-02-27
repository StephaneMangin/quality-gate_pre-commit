#!/usr/bin/env python3
"""Détecte automatiquement les sources Python du projet courant.

Utilisé par les hooks pre-commit pour éviter de coder en dur les chemins.
Retourne une liste de chemins séparés par des espaces.
"""

import sys
from pathlib import Path

HOOKS_DIR = Path(__file__).resolve().parents[1]
if str(HOOKS_DIR) not in sys.path:
    sys.path.insert(0, str(HOOKS_DIR))

from lib.quality_gate_utils import (  # noqa: E402
    ALWAYS_EXCLUDED_DIRS,
    PYTHON_SOURCE_DIRS,
    _collect_files,
    _collect_python_files,
    _filter_paths_with_env_dirs,
)


def _is_excluded(path: Path, repo_root: Path) -> bool:
    """Return True if path is inside technical/cache directories."""
    try:
        parts = path.relative_to(repo_root).parts
    except ValueError:
        parts = path.parts
    return any(part in ALWAYS_EXCLUDED_DIRS or part.startswith(".") for part in parts)


def detect_python_sources(repo_root: Path) -> list[str]:
    """Détecte les dossiers de sources Python dans le repo.

    Priorité:
    1. src/ (convention moderne Python)
    2. app/ (convention FastAPI/Flask)
    3. Modules à manifest (dossiers contenant des __manifest__.py)
    4. Racine du projet (.) si fichiers Python trouvés
    """
    sources = []

    for dirname in PYTHON_SOURCE_DIRS:
        if (repo_root / dirname).is_dir():
            sources.append(dirname)

    # Détecter les modules à manifest (dossiers avec __manifest__.py)
    manifest_dirs = set()
    manifest_count_at_root = 0

    manifest_files = _collect_files(
        repo_root,
        patterns=["__manifest__.py"],
        exclude_dirs=ALWAYS_EXCLUDED_DIRS,
        include_hidden=False,
    )
    manifest_files = _filter_paths_with_env_dirs(manifest_files, repo_root)

    for manifest in manifest_files:
        if _is_excluded(manifest, repo_root):
            continue

        addon_dir = manifest.parent

        # Si l'addon est directement à la racine
        if addon_dir.parent == repo_root:
            manifest_count_at_root += 1
        else:
            # Prendre le parent qui contient les modules
            # Typically: modules_dir/module_name/__manifest__.py -> modules_dir
            relative = addon_dir.parent.relative_to(repo_root)
            manifest_dirs.add(str(relative))

    # Si plusieurs addons à la racine (pattern OCA), utiliser "."
    if manifest_count_at_root >= 2:
        sources.append(".")
    elif manifest_dirs:
        sources.extend(sorted(manifest_dirs))

    # Fallback: si aucune source détectée, chercher des fichiers Python
    if not sources:
        # Vérifier s'il y a des fichiers Python à la racine ou dans des sous-dossiers
        py_files = _collect_python_files(repo_root, include_hidden=True)
        if any("setup" not in py_file.name.lower() for py_file in py_files):
            sources.append(".")

    # Dédupliquer
    return list(dict.fromkeys(sources))


def main():
    """Point d'entrée: affiche les sources, une par ligne ou séparées par espace."""
    repo_root = Path.cwd()
    sources = detect_python_sources(repo_root)

    # Mode: si --space, séparer par espace, sinon par ligne
    if "--space" in sys.argv:
        print(" ".join(sources))
    else:
        for source in sources:
            print(source)


if __name__ == "__main__":
    main()
