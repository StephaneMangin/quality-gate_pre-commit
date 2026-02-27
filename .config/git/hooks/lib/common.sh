#!/bin/bash
# =============================================================================
# lib/common.sh - Fonctions utilitaires communes
# =============================================================================

# Détecte si le projet contient des modules à manifest
is_odoo_project() {
    local found
    found=$(find . -maxdepth 4 -name "__manifest__.py" -type f 2>/dev/null | head -1)
    [ -n "$found" ]
}

# Obtient la racine du dépôt Git
get_repo_root() {
    local out
    out=$(git rev-parse --show-toplevel 2>/dev/null)
    if [ $? -eq 0 ]; then
        echo "$out"
    else
        pwd
    fi
}

# Liste les fichiers staged
get_staged_files() {
    git diff --cached --name-only --diff-filter=ACMRTUXB 2>/dev/null || true
}

# Vérifie si des fichiers ont été modifiés (working directory vs staged)
files_were_modified() {
    local files="$1"

    if [ -z "$files" ]; then
        return 1
    fi

    local file
    for file in $files; do
        if [ -f "$file" ] && ! git diff --quiet "$file" 2>/dev/null; then
            return 0
        fi
    done

    return 1
}

# Restage les fichiers fournis
restage_files() {
    local files="$1"

    if [ -n "$files" ]; then
        # shellcheck disable=SC2086
        git add $files 2>/dev/null || true
    fi
}

# Déduit le nom de module à manifest depuis un chemin de fichier
get_odoo_module_from_file() {
    local file_path="$1"
    local dir_path
    dir_path=$(dirname "$file_path")

    while [ "$dir_path" != "." ] && [ "$dir_path" != "/" ] && [ -n "$dir_path" ]; do
        if [ -f "$dir_path/__manifest__.py" ]; then
            basename "$dir_path"
            return 0
        fi
        dir_path=$(dirname "$dir_path")
    done

    return 1
}

# Liste les modules à manifest modifiés depuis les fichiers staged
get_modified_odoo_modules() {
    local staged_files
    staged_files=$(get_staged_files)

    if [ -z "$staged_files" ]; then
        return 0
    fi

    local modules=""
    local mod
    local file

    for file in $staged_files; do
        mod=$(get_odoo_module_from_file "$file")
        if [ -n "$mod" ]; then
            modules="$modules $mod"
        fi
    done

    # Dédupliquer et trier
    echo "$modules" | tr ' ' '\n' | sort -u | tr '\n' ' '
}

# Normalise une valeur CSV de répertoires (trim, suppression ./ et / final)
normalize_csv_dirs() {
    local csv="$1"
    echo "$csv" | tr ',' '\n' | while IFS= read -r raw; do
        local value="$raw"
        value="${value#./}"
        value="${value%/}"
        value="$(echo "$value" | xargs)"
        if [ -n "$value" ]; then
            echo "$value"
        fi
    done | sort -u
}

# Vérifie si un chemin appartient à un répertoire (exact ou sous-chemin)
path_matches_dir() {
    local path="$1"
    local dir="$2"
    [ "$path" = "$dir" ] || [[ "$path" == "$dir"/* ]]
}

# Construit une liste de fichiers tracked filtrée par include/exclude dirs (CSV)
build_filtered_file_list() {
    local include_csv="$1"
    local exclude_csv="$2"

    local -a include_dirs=()
    local -a exclude_dirs=()

    if [ -n "$include_csv" ]; then
        mapfile -t include_dirs < <(normalize_csv_dirs "$include_csv")
    fi
    if [ -n "$exclude_csv" ]; then
        mapfile -t exclude_dirs < <(normalize_csv_dirs "$exclude_csv")
    fi

    git ls-files | while IFS= read -r file; do
        local include_ok=true
        local exclude_hit=false
        local dir

        if [ ${#include_dirs[@]} -gt 0 ]; then
            include_ok=false
            for dir in "${include_dirs[@]}"; do
                if path_matches_dir "$file" "$dir"; then
                    include_ok=true
                    break
                fi
            done
        fi

        for dir in "${exclude_dirs[@]}"; do
            if path_matches_dir "$file" "$dir"; then
                exclude_hit=true
                break
            fi
        done

        if [ "$include_ok" = true ] && [ "$exclude_hit" = false ]; then
            echo "$file"
        fi
    done
}

# Supprime les flags --all-files/-a (incompatibles avec --files)
strip_all_files_args() {
    for arg in "$@"; do
        if [ "$arg" = "-a" ] || [ "$arg" = "--all-files" ]; then
            continue
        fi
        echo "$arg"
    done
}

# Exécute pre-commit avec filtres include/exclude optionnels.
# Retourne:
#   0..N code retour pre-commit
#   10 si aucun fichier ne matche les filtres
run_precommit_with_optional_filters() {
    local precommit_bin="$1"
    local config_path="$2"
    local include_dirs="$3"
    local exclude_dirs="$4"
    shift 4
    local args=("$@")

    if [ -n "$include_dirs" ] || [ -n "$exclude_dirs" ]; then
        local -a filtered_files=()
        local -a filtered_args=()

        mapfile -t filtered_files < <(build_filtered_file_list "$include_dirs" "$exclude_dirs")
        mapfile -t filtered_args < <(strip_all_files_args "${args[@]}")

        if [ ${#filtered_files[@]} -eq 0 ]; then
            return 10
        fi

        "$precommit_bin" run --config "$config_path" "${filtered_args[@]}" --files "${filtered_files[@]}"
        return $?
    fi

    "$precommit_bin" run --config "$config_path" "${args[@]}"
}
