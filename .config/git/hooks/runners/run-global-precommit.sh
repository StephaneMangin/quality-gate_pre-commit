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
    run_precommit_with_optional_filters \
        "$precommit_bin" \
        "$GLOBAL_CONFIG" \
        "$include_dirs" \
        "$exclude_dirs" \
        "${args[@]}"
    local exit_code=$?
    set -e

    if [ $exit_code -eq 10 ]; then
        print_skip "No files match include/exclude filters for global hooks"
        return 0
    fi

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
