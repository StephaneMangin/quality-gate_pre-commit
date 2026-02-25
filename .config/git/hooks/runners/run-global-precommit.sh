#!/bin/bash
# =============================================================================
# runners/run-global-precommit.sh - Exécute les hooks pre-commit globaux
# =============================================================================

set -e

HOOKS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Charger les bibliothèques
# shellcheck disable=SC1091
source "$HOOKS_DIR/lib/reporting.sh"
# shellcheck disable=SC1091
source "$HOOKS_DIR/lib/tool-resolution.sh"
# shellcheck disable=SC1091
source "$HOOKS_DIR/lib/common.sh"

GLOBAL_CONFIG="$HOOKS_DIR/configs/global-pre-commit-config.yaml"

run_global_precommit() {
    local args=("$@")
    local include_dirs="${PCR_INCLUDE_DIRS:-}"
    local exclude_dirs="${PCR_EXCLUDE_DIRS:-}"

    print_section "🌍 STEP 1/4: Global pre-commit hooks"

    if [ ! -f "$GLOBAL_CONFIG" ]; then
        print_skip "No global pre-commit config found"
        return 0
    fi

    local precommit_bin
    precommit_bin=$(resolve_precommit)

    if [ -z "$precommit_bin" ]; then
        print_error "pre-commit not found"
        return 1
    fi

    # pre-commit peut retourner exit code 1 pour auto-fixes (non bloquant)
    set +e
    if [ -n "$include_dirs" ] || [ -n "$exclude_dirs" ]; then
        local -a filtered_files=()
        local -a filtered_args=()

        mapfile -t filtered_files < <(build_filtered_file_list "$include_dirs" "$exclude_dirs")
        mapfile -t filtered_args < <(strip_all_files_args "${args[@]}")

        if [ ${#filtered_files[@]} -eq 0 ]; then
            print_skip "No files match include/exclude filters for global hooks"
            set -e
            return 0
        fi

        "$precommit_bin" run --config "$GLOBAL_CONFIG" "${filtered_args[@]}" --files "${filtered_files[@]}"
    else
        "$precommit_bin" run --config "$GLOBAL_CONFIG" "${args[@]}"
    fi
    local exit_code=$?
    set -e

    if [ $exit_code -eq 0 ]; then
        print_success "Global pre-commit passed"
        return 0
    elif [ $exit_code -eq 1 ]; then
        print_warning "Global pre-commit completed (some files auto-fixed or minor issues)"
        return 0
    else
        print_error "Global pre-commit failed (exit code: $exit_code)"
        return 1
    fi
}

# Si exécuté directement (pas sourcé)
if [ "${BASH_SOURCE[0]}" = "${0}" ]; then
    run_global_precommit "$@"
fi
