#!/bin/bash
# =============================================================================
# Wrapper Pre-commit - Compatible avec `pre-commit run -a` et `pcr`
# =============================================================================
# Orchestre l'exécution des hooks dans l'ordre:
# 1. Global pre-commit
# 2. Quality gate
# 3. Local pre-commit
# =============================================================================

set -e

HOOKS_DIR="$HOME/.config/git/hooks"

# Charger les bibliothèques
# shellcheck disable=SC1091
source "$HOOKS_DIR/lib/reporting.sh"
# shellcheck disable=SC1091
source "$HOOKS_DIR/lib/tool-resolution.sh"
# shellcheck disable=SC1091
source "$HOOKS_DIR/lib/common.sh"

# Activer le venv
activate_repo_venv

# Collecter les arguments
ARGS=("$@")

# Variables de suivi
FAILED=false

# =============================================================================
# Étape 1: Pre-commit global
# =============================================================================
# shellcheck disable=SC1091
source "$HOOKS_DIR/runners/run-global-precommit.sh"
if ! run_global_precommit "${ARGS[@]}"; then
    FAILED=true
fi

# =============================================================================
# Étape 2: Quality gate
# =============================================================================
# shellcheck disable=SC1091
source "$HOOKS_DIR/runners/run-quality-gate.sh"
if ! run_quality_gate; then
    FAILED=true
fi

# =============================================================================
# Étape 3: Pre-commit local
# =============================================================================
# shellcheck disable=SC1091
source "$HOOKS_DIR/runners/run-local-precommit.sh"
if ! run_local_precommit "${ARGS[@]}"; then
    FAILED=true
fi

# =============================================================================
# Résultat
# =============================================================================
if [ "$FAILED" = "true" ]; then
    print_final_summary false "Some checks failed"
    exit 1
else
    print_final_summary true "All checks passed!"
    exit 0
fi
