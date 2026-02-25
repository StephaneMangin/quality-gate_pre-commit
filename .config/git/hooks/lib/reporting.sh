#!/bin/bash
# =============================================================================
# lib/reporting.sh - Fonctions de reporting et affichage
# =============================================================================

# Couleurs
export RED='\033[0;31m'
export GREEN='\033[0;32m'
export YELLOW='\033[1;33m'
export BLUE='\033[0;34m'
export CYAN='\033[0;36m'
export MAGENTA='\033[0;35m'
export NC='\033[0m' # No Color

# Symboles
export SYMBOL_SUCCESS="✓"
export SYMBOL_ERROR="✗"
export SYMBOL_SKIP="⊘"
export SYMBOL_INFO="ℹ"
export SYMBOL_WARNING="⚠"

# Affiche une section avec titre
print_section() {
    local title="$1"
    echo -e "\n${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}${title}${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"
}

# Messages de succès
print_success() {
    echo -e "${GREEN}${SYMBOL_SUCCESS} $1${NC}"
}

# Messages d'erreur
print_error() {
    echo -e "${RED}${SYMBOL_ERROR} $1${NC}"
}

# Messages de skip
print_skip() {
    echo -e "${YELLOW}${SYMBOL_SKIP} $1${NC}"
}

# Messages d'info
print_info() {
    echo -e "${CYAN}${SYMBOL_INFO} $1${NC}"
}

# Messages de warning
print_warning() {
    echo -e "${YELLOW}${SYMBOL_WARNING} $1${NC}"
}

# Affiche un résumé final
print_final_summary() {
    local success="$1"
    local message="$2"

    echo ""
    if [ "$success" = "true" ]; then
        echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        echo -e "${GREEN}${SYMBOL_SUCCESS} ${message:-All checks passed! Ready to commit.} 🎉${NC}"
        echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    else
        echo -e "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        echo -e "${RED}${SYMBOL_ERROR} ${message:-Checks failed. Commit aborted.}${NC}"
        echo -e "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    fi
    echo ""
}

# Affiche un compteur de progression
print_progress() {
    local current="$1"
    local total="$2"
    local label="$3"
    echo -e "${CYAN}[${current}/${total}] ${label}${NC}"
}
