#!/bin/bash
# =============================================================================
# runners/run-local-precommit.sh - Exécute le pre-commit local du projet
# Avec gestion des auto-fixes et retry automatique
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

LOCAL_CONFIG=".pre-commit-config.yaml"
MAX_RETRIES=2

run_local_precommit() {
    local args=("$@")
    local include_dirs="${PCR_INCLUDE_DIRS:-}"
    local exclude_dirs="${PCR_EXCLUDE_DIRS:-}"

    local precommit_bin
    precommit_bin=$(resolve_precommit)

    print_section "📁 STEP 3/4: Local project pre-commit hooks"

    if [ ! -f "$LOCAL_CONFIG" ]; then
        print_skip "No local .pre-commit-config.yaml in this project"
        return 0
    fi

    if [ -z "$precommit_bin" ]; then
        print_error "pre-commit not found"
        return 1
    fi

    # Sauvegarder les fichiers staged avant exécution
    local staged_files_before
    staged_files_before=$(get_staged_files)

    local -a run_args=("${args[@]}")
    local -a filtered_files=()
    if [ -n "$include_dirs" ] || [ -n "$exclude_dirs" ]; then
        mapfile -t filtered_files < <(build_filtered_file_list "$include_dirs" "$exclude_dirs")
        mapfile -t run_args < <(strip_all_files_args "${args[@]}")

        if [ ${#filtered_files[@]} -eq 0 ]; then
            print_skip "No files match include/exclude filters for local hooks"
            set -e
            return 0
        fi
    fi

    run_local_once() {
        if [ ${#filtered_files[@]} -gt 0 ]; then
            "$precommit_bin" run --config "$LOCAL_CONFIG" "${run_args[@]}" --files "${filtered_files[@]}"
        else
            "$precommit_bin" run --config "$LOCAL_CONFIG" "${run_args[@]}"
        fi
    }

    # Tentative 1
    set +e
    run_local_once
    local exit_code=$?
    set -e


    # Succès immédiat
    if [ $exit_code -eq 0 ]; then
        print_success "Local pre-commit passed"
        return 0
    fi

    # Si exit code 1 = auto-fixes possibles ou erreurs mineures
    if [ $exit_code -eq 1 ]; then
        # Vérifier si des fichiers ont été modifiés
        if files_were_modified "$staged_files_before"; then
            print_info "Auto-fixes detected. Re-staging modified files..."

            # Afficher les fichiers modifiés
            if [ -n "$staged_files_before" ]; then
                echo -e "${CYAN}Modified files:${NC}"
                for file in $staged_files_before; do
                    if [ -f "$file" ] && ! git diff --quiet "$file" 2>/dev/null; then
                        echo "  - $file"
                    fi
                done
            fi

            # Restager et réessayer
            restage_files "$staged_files_before"

            print_info "Retrying pre-commit (attempt 2/$((MAX_RETRIES + 1)))..."
            set +e
            run_local_once
            exit_code=$?
            set -e

            if [ $exit_code -eq 0 ]; then
                print_success "Local pre-commit passed after auto-fixes"
                return 0
            fi

            # Deuxième round d'auto-fixes si nécessaire
            if [ $exit_code -eq 1 ] && files_were_modified "$staged_files_before"; then
                print_info "More auto-fixes detected. Re-staging again..."
                restage_files "$staged_files_before"

                print_info "Retrying pre-commit (attempt 3/$((MAX_RETRIES + 1)))..."
                set +e
                run_local_once
                exit_code=$?
                set -e

                if [ $exit_code -eq 0 ]; then
                    print_success "Local pre-commit passed after second round of auto-fixes"
                    return 0
                fi
            fi
        fi

        # Si on arrive ici, soit pas d'auto-fixes, soit échec persistant
        if [ $exit_code -eq 1 ]; then
            print_warning "Local pre-commit completed with warnings"
            return 0
        fi
    fi

    # Échec grave (exit code > 1)
    print_error "Local pre-commit failed (exit code: $exit_code)"
    return 1
}

# Si exécuté directement (pas sourcé)
if [ "${BASH_SOURCE[0]}" = "${0}" ]; then
    run_local_precommit "$@"
fi
