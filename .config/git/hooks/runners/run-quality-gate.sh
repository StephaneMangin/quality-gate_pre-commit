#!/bin/bash
# =============================================================================
# runners/run-quality-gate.sh - Exécute le quality gate global avec reporting
# =============================================================================
# Exécute le quality gate Python et affiche son reporting détaillé
# =============================================================================

set -e

HOOKS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Charger les bibliothèques
# shellcheck disable=SC1091
source "$HOOKS_DIR/lib/reporting.sh"
# shellcheck disable=SC1091
source "$HOOKS_DIR/lib/tool-resolution.sh"

QUALITY_GATE_SCRIPT="$HOOKS_DIR/tools/quality_gate.py"

run_quality_gate() {
    local python_bin
    local include_dirs="${QUALITY_GATE_INCLUDE_DIRS:-${PCR_INCLUDE_DIRS:-}}"
    local exclude_dirs="${QUALITY_GATE_EXCLUDE_DIRS:-${PCR_EXCLUDE_DIRS:-}}"

    print_section "🔍 STEP 2/4: Quality gate"

    if [ ! -f "$QUALITY_GATE_SCRIPT" ]; then
        print_skip "Quality gate script not found"
        return 0
    fi

    python_bin=$(resolve_python)
    if [ -z "$python_bin" ]; then
        print_skip "Python not found, skipping quality gate"
        return 0
    fi

    # Exécuter le quality gate et capturer sa sortie
    local output
    local exit_code

    set +e
    output=$(QUALITY_GATE_INCLUDE_DIRS="$include_dirs" QUALITY_GATE_EXCLUDE_DIRS="$exclude_dirs" "$python_bin" "$QUALITY_GATE_SCRIPT" 2>&1)
    exit_code=$?
    set -e

    # Afficher toute la sortie du quality gate (contient son propre reporting)
    echo "$output"
    echo ""

    # Décider du résultat
    if [ $exit_code -eq 0 ]; then
        print_success "Quality gate passed"
        return 0
    else
        # Quality gate retourne 1 en cas d'erreur bloquante
        # On regarde si c'est vraiment un échec ou juste des warnings
        if echo "$output" | grep -q "\[quality-gate\] ÉCHEC bloquant"; then
            print_error "Quality gate failed (blocking errors detected)"
            return 1
        else
            # Seulement des avertissements (mode non-bloquant)
            print_warning "Quality gate completed with warnings"
            return 0
        fi
    fi
}

# Si exécuté directement (pas sourcé)
if [ "${BASH_SOURCE[0]}" = "${0}" ]; then
    run_quality_gate "$@"
fi
