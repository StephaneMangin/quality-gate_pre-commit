#!/bin/bash
# =============================================================================
# lib/tool-resolution.sh - Résolution des outils (python, pre-commit, etc.)
# =============================================================================

# Résout l'interpréteur Python du repo
resolve_python() {
    # Priorité 1: venv actif
    if [ -n "$VIRTUAL_ENV" ] && [ -x "$VIRTUAL_ENV/bin/python" ]; then
        echo "$VIRTUAL_ENV/bin/python"
        return 0
    fi

    # Priorité 2: venv local du projet
    if [ -x "./.venv/bin/python" ]; then
        echo "./.venv/bin/python"
        return 0
    fi
    if [ -x "./venv/bin/python" ]; then
        echo "./venv/bin/python"
        return 0
    fi

    # Prioritéé 3: mise
    if command -v mise >/dev/null 2>&1; then
        local mise_py
        mise_py=$(mise which python 2>/dev/null || mise which python3 2>/dev/null || true)
        if [ -n "$mise_py" ] && [ -x "$mise_py" ]; then
            echo "$mise_py"
            return 0
        fi
    fi

    # Priorité 4: PATH
    if command -v python3 >/dev/null 2>&1; then
        echo "python3"
        return 0
    elif command -v python >/dev/null 2>&1; then
        echo "python"
        return 0
    fi

    return 1
}

# Résout la commande pre-commit
resolve_precommit() {
    # Priorité 1: venv actif
    if [ -n "$VIRTUAL_ENV" ] && [ -x "$VIRTUAL_ENV/bin/pre-commit" ]; then
        echo "$VIRTUAL_ENV/bin/pre-commit"
        return 0
    fi

    # Priorité 2: venv local du projet
    if [ -x "./.venv/bin/pre-commit" ]; then
        echo "./.venv/bin/pre-commit"
        return 0
    fi
    if [ -x "./venv/bin/pre-commit" ]; then
        echo "./venv/bin/pre-commit"
        return 0
    fi

    # Priorité 3: mise
    if command -v mise >/dev/null 2>&1; then
        local mise_pc
        mise_pc=$(mise which pre-commit 2>/dev/null || true)
        if [ -n "$mise_pc" ] && [ -x "$mise_pc" ]; then
            echo "$mise_pc"
            return 0
        fi
    fi

    # Priorité 4: pipx
    if [ -x "$HOME/.local/bin/pre-commit" ]; then
        echo "$HOME/.local/bin/pre-commit"
        return 0
    fi

    # Priorité 5: PATH (éviter les shims pyenv)
    local pc_path
    pc_path=$(which pre-commit 2>/dev/null || true)
    if [ -n "$pc_path" ] && [ -x "$pc_path" ]; then
        if [[ "$pc_path" != *"pyenv/shims"* ]]; then
            echo "$pc_path"
            return 0
        fi
    fi

    return 1
}

# Résout un outil générique
resolve_tool() {
    local tool="$1"

    # Priorité 1: venv actif
    if [ -n "$VIRTUAL_ENV" ] && [ -x "$VIRTUAL_ENV/bin/$tool" ]; then
        echo "$VIRTUAL_ENV/bin/$tool"
        return 0
    fi

    # Priorité 2: venv local
    local candidates=(
        "./.venv/bin/$tool"
        "./venv/bin/$tool"
        "./env/bin/$tool"
    )

    for candidate in "${candidates[@]}"; do
        if [ -x "$candidate" ]; then
            echo "$candidate"
            return 0
        fi
    done

    # Priorité 3: mise
    if command -v mise >/dev/null 2>&1; then
        local mise_tool
        mise_tool=$(mise which "$tool" 2>/dev/null || true)
        if [ -n "$mise_tool" ] && [ -x "$mise_tool" ]; then
            echo "$mise_tool"
            return 0
        fi
    fi

    # Priorité 4: PATH
    if command -v "$tool" >/dev/null 2>&1; then
        echo "$tool"
        return 0
    fi

    return 1
}

# Active le venv du repo courant si nécessaire
activate_repo_venv() {
    local activate_script
    local current_repo
    current_repo=$(pwd)

    # Si un venv est actif et c'est celui du repo, ne rien faire
    if [ -n "$VIRTUAL_ENV" ] && [ -f "$VIRTUAL_ENV/bin/activate" ]; then
        case "$VIRTUAL_ENV" in
            "$current_repo"/*)
                return 0
                ;;
            *)
                # Désactiver le venv étranger
                deactivate >/dev/null 2>&1 || true
                unset VIRTUAL_ENV
                ;;
        esac
    fi

    # Chercher et activer le venv local
    for activate_script in \
        "./.venv/bin/activate" \
        "./venv/bin/activate" \
        "./env/bin/activate"
    do
        if [ -f "$activate_script" ]; then
            # shellcheck disable=SC1090
            source "$activate_script"
            return 0
        fi
    done

    # Essayer avec mise
    if command -v mise >/dev/null 2>&1; then
        eval "$(mise env -s bash 2>/dev/null || true)"
    fi

    return 0
}
