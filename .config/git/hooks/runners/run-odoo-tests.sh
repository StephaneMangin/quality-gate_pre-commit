#!/bin/bash
# =============================================================================
# runners/run-odoo-tests.sh - Exécute les tests de modules sur les modules modifiés
# =============================================================================

set -e

HOOKS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Charger les bibliothèques
# shellcheck disable=SC1091
source "$HOOKS_DIR/lib/reporting.sh"
# shellcheck disable=SC1091
source "$HOOKS_DIR/lib/common.sh"

run_odoo_tests() {
    print_section "🧪 STEP 4/4: Module tests"

    if ! is_odoo_project; then
        print_skip "No manifest-based modules detected"
        return 0
    fi

    # Charger odoo_functions si disponible
    if [ -f ~/.odoo_functions ]; then
        # shellcheck disable=SC1090
        source ~/.odoo_functions
    fi

    # Vérifier disponibilité de odootest
    if ! type -t odootest >/dev/null 2>&1; then
        print_skip "odootest not available"
        return 0
    fi

    # Obtenir les modules modifiés
    local modules
    modules=$(get_modified_odoo_modules)
    modules=$(echo "$modules" | xargs)  # Trim whitespace

    if [ -z "$modules" ]; then
        print_skip "No changed modules to test"
        return 0
    fi

    print_info "Testing modules: $modules"

    # Exécuter les tests
    local test_output
    local exit_code

    set +e
    # shellcheck disable=SC2086
    test_output=$(odootest -op $modules 2>&1)
    exit_code=$?
    set -e

    if [ -n "$test_output" ]; then
        echo "$test_output"
    fi

    if [ "$exit_code" -eq 0 ]; then
        print_success "Module tests passed for all modules"
        return 0
    elif echo "$test_output" | grep -Eqi '(odoo(-bin)?|/odoo)[^[:cntrl:]]*(not found|command not found|introuvable)'; then
        print_skip "odoo not found in environment, skipping module tests"
        return 0
    else
        print_error "Module tests failed (exit code: $exit_code)"
        return 1
    fi
}

# Si exécuté directement (pas sourcé)
if [ "${BASH_SOURCE[0]}" = "${0}" ]; then
    run_odoo_tests "$@"
fi
