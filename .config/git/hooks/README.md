# Git Hooks - Architecture Modulaire pour Pre-commit

Configuration Git hooks globale avec architecture modulaire pour une meilleure maintenabilité.

## 📁 Structure du projet

```
~/.config/git/hooks/
├── pre-commit                            # Hook principal (orchestrateur)
├── README.md                             # Cette documentation
│
├── bin/                                  # Utilitaires exécutables
│   └── precommit-wrapper.sh              # Wrapper pour `pcr` command
│
├── configs/                              # Configurations
│   └── global-pre-commit-config.yaml     # Config pre-commit globale
│
├── lib/                                  # Bibliothèques partagées
│   ├── common.sh                         # Fonctions utilitaires
│   ├── quality_gate_dependency_utils.py  # Utilitaires dépendances modules (manifests + graphe)
│   ├── quality_gate_utils.py             # Utilitaires généraux quality gate
│   ├── reporting.sh                      # Formatage et affichage coloré
│   └── tool-resolution.sh                # Résolution des outils (python, pre-commit)
│
├── runners/                              # Runners modulaires (1 par étape)
│   ├── run-global-precommit.sh           # Étape 1: Pre-commit global
│   ├── run-quality-gate.sh               # Étape 2: Quality gate
│   ├── run-local-precommit.sh            # Étape 3: Pre-commit local (avec auto-fix retry)
│   └── run-odoo-tests.sh                 # Étape 4: Tests modules
│
└── tools/                                # Outils Python
    ├── detect_python_sources.py          # Détection automatique des sources
    └── quality_gate.py                   # Quality gate (complexité, coverage, etc.)
```

## 🎯 Flux d'exécution

### Lors d'un commit Git (ou `pcr`)

```
1. 🌍 STEP 1/4: Global pre-commit hooks
   ├─ Ruff (lint + format)
   ├─ Bandit (security)
   ├─ Vulture (dead code)
   ├─ Xenon (complexity)
   └─ File hygiene checks

### Fonctionnement du Quality Gate

Le quality gate affiche un **reporting détaillé** :

```
[quality-gate] mode=hybrid | targets=src, addons

[quality-gate] --- Complexité ---
  C src/file1.py (12:0 foo)
  B src/file2.py (9:0 bar)
  A src/file3.py (5:0 baz)

[quality-gate] --- Dead code ---
  src/utils.py:42: unused variable 'temp'

[quality-gate] --- Dépendances modules ---
  Addons détectés: 3
  Cycle: addon_a ↔ addon_b

[quality-gate] --- Coverage ---
  Name                      Stmts   Miss  Cover
  ──────────────────────────────────────────────
  src/__init__.py              2      0   100%
  src/core.py                 45      5    89%
  ──────────────────────────────────────────────
  TOTAL                       47      5    89%  (min 40%)

[quality-gate] Résultats:
  - complexity             PASS (blocking) :: A (max C)
  - dead code              PASS (blocking) :: 0 issues found
  - module dependencies    PASS (blocking) :: graphe sain
  - coverage               PASS (info)     :: 89.4% (min 40%)

[quality-gate] Tous les checks sont OK.
```3. 📁 STEP 3/4: Local project pre-commit hooks
   ├─ Hooks définis dans .pre-commit-config.yaml du projet
   ├─ Auto-fix detection & retry (jusqu'à 2 fois)
   └─ Auto-restaging des fichiers modifiés

4. 🧪 STEP 4/4: Module tests (si applicable)
  └─ test runner sur les modules modifiés
```

## 🚀 Utilisation

### Commande simple : `pcr`

```bash
# Dans n'importe quel projet
cd /votre/projet

# Exécuter tous les hooks
pcr -a

# Exécuter sur les fichiers staged uniquement
pcr

# Limiter l'exécution à certains répertoires (CSV)
pcr -a --include-dirs addons,src

# Exclure certains répertoires (CSV)
pcr -a --exclude-dirs .venv,addons/legacy

# Include + exclude (exclude est prioritaire)
pcr -a --include-dirs addons --exclude-dirs addons/legacy
```

### Centralisation des paths de recherche

Les chemins de recherche/exclusion sont centralisés dans :

`~/.config/git/hooks/configs/search-paths.conf`

Ce fichier pilote les répertoires source Python, les racines modules à manifest,
les dossiers de venv et les exclusions techniques (`.venv`, `.git`, caches, etc.).

### Via Git hook (automatique)

Les hooks s'exécutent automatiquement lors de `git commit` grâce à :

```bash
git config --global core.hooksPath ~/.config/git/hooks
```

### Exécuter un runner individuellement

```bash
# Uniquement le pre-commit global
~/.config/git/hooks/runners/run-global-precommit.sh -a

# Uniquement le quality gate
~/.config/git/hooks/runners/run-quality-gate.sh

# Uniquement le pre-commit local
~/.config/git/hooks/runners/run-local-precommit.sh -a

# Uniquement les tests modules
~/.config/git/hooks/runners/run-odoo-tests.sh
```

## 🔧 Configuration du Quality Gate

Le quality gate se configure via des **variables d'environnement** :

```bash
# Mode d'exécution
export QUALITY_GATE_MODE=hybrid
  # info   : aucun check n'est bloquant (informatif seulement)
  # hybrid : bloque sur complexité, dead code, dépendances modules (défaut)
  # strict : tous les checks sont bloquants

# Seuil de complexité maximale autorisée
export QUALITY_GATE_MAX_COMPLEXITY=C
  # A (1-5)  B (6-10)  C (11-15)  D (16-20)  E (21-25)  F (26+)

# Coverage minimale requise
export QUALITY_GATE_COVERAGE_MIN=40       # Pourcentage

# Confiance minimale pour vulture (dead code)
export QUALITY_GATE_VULTURE_MIN_CONFIDENCE=80  # 0-100

# Comportement si aucun fichier staged
export QUALITY_GATE_NO_STAGED=full
  # full : scan complet du repo (défaut)
  # skip : sortie immédiate sans scan

# Niveau de reporting
export QUALITY_GATE_REPORT=full
  # full    : reporting détaillé (défaut)
  # minimal : seulement les résultats
```

### Exemples d'utilisation

```bash
# Mode informatif (non-bloquant)
QUALITY_GATE_MODE=info pcr -a

# Mode strict (tous les checks bloquants)
QUALITY_GATE_MODE=strict pcr -a

# Coverage plus strict
QUALITY_GATE_COVERAGE_MIN=85 pcr -a

# Reporting minimal
QUALITY_GATE_REPORT=minimal pcr -a
```

### Checks exécutés par le quality gate

| Check | Outil | Détails | Bloquant (hybrid) |
|-------|-------|---------|------------------|
| **Complexité** | radon | Grade min A-F par fonction/module | ✅ Oui |
| **Dead code** | vulture | Code inutilisé | ✅ Oui |
| **Dépendances modules** | ast | Cycles + imports manquants | ✅ Oui |
| **Coverage** | coverage | Couverture de tests (%) | ❌ Non (info) |

### Configuration par projet

Chaque projet peut avoir sa propre `.pre-commit-config.yaml` qui est exécutée à l'étape 3.

**Exemple de hooks projet :**

```yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v0.0.33
    hooks:
      - id: check-yaml
      - id: end-of-file-fixer
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.13.2
    hooks:
      - id: ruff
```

## 📚 Architecture des composants

### Bibliothèques (lib/)

#### reporting.sh
Gestion de l'affichage coloré et formaté :

- `print_section()` : Affiche une section avec titre
- `print_success()`, `print_error()`, `print_warning()`, `print_skip()`, `print_info()`
- `print_final_summary()` : Résumé final coloré

**Couleurs disponibles :** RED, GREEN, YELLOW, BLUE, CYAN, MAGENTA, NC

**Symboles :** ✓ (success), ✗ (error), ⊘ (skip), ℹ (info), ⚠ (warning)

#### tool-resolution.sh
Résolution intelligente des outils (priorité: venv > mise > pipx > PATH) :

- `resolve_python()` : Trouve l'interpréteur Python
- `resolve_precommit()` : Trouve pre-commit
- `resolve_tool()` : Résolution générique d'outil
- `activate_repo_venv()` : Active le venv du projet

#### common.sh
Fonctions utilitaires :

- `is_odoo_project()` : Détecte la présence de modules à manifest
- `get_staged_files()` : Liste les fichiers staged
- `files_were_modified()` : Vérifie si des fichiers ont été modifiés
- `restage_files()` : Restage des fichiers après auto-fix
- `get_odoo_module_from_file()` : Extrait le nom d'un module à manifest
- `get_modified_odoo_modules()` : Liste les modules à manifest modifiés

#### quality_gate_utils.py
Utilitaires Python partagés pour la quality gate :

- `_run()` : Exécution de commandes subprocess
- `_tool_cmd()` : Résolution des binaires (venv > PATH > `python -m`)
- `_repo_root()`, `_staged_files()` : Contexte Git
- `_detect_python_project()`, `_iter_python_targets()` : Détection des cibles Python
- `_box_title()`, `_section_title()`, `_bar_chart()` : Helpers d'affichage texte

#### quality_gate_dependency_utils.py
Utilitaires Python dédiés à l'analyse des dépendances de modules :

- `_load_addon_manifests()` : Chargement des `__manifest__.py`
- `_build_dependency_graph()` : Construction du graphe de dépendances
- `_compute_graph_metrics()` : Calcul des métriques (cycles, densité, dépendances manquantes)

### Runners (runners/)

Chaque runner est **autonome** et peut être :
- Exécuté individuellement pour debugging
- Sourcé depuis le hook principal
- Testé indépendamment

**Caractéristiques communes :**
- Chargent les bibliothèques nécessaires
- Affichent des sections formatées avec `print_section()`
- Retournent 0 (succès) ou 1 (échec)
- Gèrent gracieusement les cas de configuration manquante

**Template pour créer un nouveau runner :**

```bash
#!/bin/bash
set -e
HOOKS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

source "$HOOKS_DIR/lib/reporting.sh"
source "$HOOKS_DIR/lib/tool-resolution.sh"
source "$HOOKS_DIR/lib/common.sh"

run_my_check() {
    print_section "🎯 STEP X/Y: My Check Description"

    # Votre logique ici

    if [[ condition_success ]]; then
        print_success "My check passed"
        return 0
    else
        print_error "My check failed"
        return 1
    fi
}

# Permet l'exécution directe ET le sourcing
if [ "${BASH_SOURCE[0]}" = "${0}" ]; then
    run_my_check "$@"
fi
```

### Outils (tools/)

#### detect_python_sources.py
Détecte automatiquement les sources Python du projet :
- `src/` (convention moderne)
- `app/` (FastAPI/Flask)
- Modules à manifest (dossiers avec `__manifest__.py`)
- Racine en fallback

```bash
# Utilisation
python3 ~/.config/git/hooks/tools/detect_python_sources.py              # Une ligne par source
python3 ~/.config/git/hooks/tools/detect_python_sources.py --space      # Séparé par espaces (pour bash)
```

#### quality_gate.py
Analyse de qualité avancée :
- Complexité cyclomatique (radon)
- Dead code detection (vulture)
- Validation des dépendances de modules
- Coverage checks

Le script s'appuie sur les utilitaires Python sous `lib/` (`quality_gate_utils.py` et `quality_gate_dependency_utils.py`) pour séparer la logique métier des fonctions utilitaires.

Configuré via variables d'environnement (voir section Configuration).

## 🔄 Auto-fix et Retry

Le runner `run-local-precommit.sh` implémente une logique sophistiquée d'auto-fix :

1. **Première exécution** : Lance pre-commit sur les fichiers staged
2. **Si exit code = 1** ET **fichiers modifiés détectés** :
   - Affiche les fichiers modifiés
   - Restage automatiquement les fichiers
   - **Retry 1** : Relance pre-commit
3. **Si exit code = 1** à nouveau ET **nouveaux fichiers modifiés** :
   - Restage à nouveau
   - **Retry 2** : Relance pre-commit une dernière fois
4. **Maximum 2 retries** pour éviter les boucles infinies

Cette logique permet aux hooks qui font de l'auto-formatting (ruff, prettier, etc.) de fonctionner sans intervention manuelle.

## 🛠️ Maintenance

### Ajouter un nouveau hook global

1. Éditer `configs/global-pre-commit-config.yaml`
```yaml
repos:
  - repo: https://github.com/mon-nouveau/hook
    rev: v1.0.0
    hooks:
      - id: mon-hook
```

2. Tester :
```bash
~/.config/git/hooks/runners/run-global-precommit.sh -a
```

### Ajouter une nouvelle étape

1. Créer un nouveau runner dans `runners/run-my-step.sh`
2. Le sourcer depuis `pre-commit` :
```bash
source "$HOOKS_DIR/runners/run-my-step.sh"
if ! run_my_step; then
    MY_STEP_FAILED=true
fi
```

3. Ajouter à la vérification finale :
```bash
if [ "$GLOBAL_FAILED" = "true" ] || [ "$MY_STEP_FAILED" = "true" ] || ...; then
    # Échec
fi
```

### Désactiver temporairement une étape

Commenter la section correspondante dans `pre-commit` :

```bash
# =============================================================================
# Étape 2: Quality gate
# =============================================================================
# source "$HOOKS_DIR/runners/run-quality-gate.sh"
# if ! run_quality_gate; then
#     QUALITY_GATE_FAILED=true
# fi
```

### Debugging

```bash
# Activer le mode verbose bash
set -x

# Tester un runner individuellement avec trace
bash -x ~/.config/git/hooks/runners/run-global-precommit.sh -a

# Vérifier les variables d'environnement
env | grep QUALITY_GATE

# Tester la résolution des outils
source ~/.config/git/hooks/lib/tool-resolution.sh
resolve_python
resolve_precommit

# Vérifier les fichiers staged
source ~/.config/git/hooks/lib/common.sh
get_staged_files
```

## 📦 Installation

### Nouvelle machine

```bash
# 1. Configurer Git pour utiliser ces hooks
git config --global core.hooksPath ~/.config/git/hooks

# 2. Installer pre-commit globalement
pipx install pre-commit

# 3. Créer l'alias pcr (Pre-Commit Run)
mkdir -p ~/bin
cat > ~/bin/pcr << 'EOF'
#!/bin/bash
exec ~/.config/git/hooks/bin/precommit-wrapper.sh "$@"
EOF
chmod +x ~/bin/pcr

# 4. Ajouter ~/bin au PATH si nécessaire
echo 'export PATH="$HOME/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

### Mise à jour

Si les hooks sont versionnés dans un repo :

```bash
cd ~/.config/git/hooks
git pull
chmod +x lib/*.sh runners/*.sh pre-commit bin/*.sh
```

Sinon, copier manuellement les nouveaux fichiers et rendre exécutables.

## 🔍 Troubleshooting

### "pre-commit not found"

```bash
# Installation via pipx (recommandé)
pipx install pre-commit

# Ou via pip
pip install --user pre-commit

# Vérifier l'installation
which pre-commit
pre-commit --version
```

### "Python not found"

```bash
# Vérifier Python dans le PATH
which python3

# Ou installer dans le venv du projet
cd /votre/projet
python3 -m venv .venv
source .venv/bin/activate
pip install pre-commit
```

### Les hooks ne s'exécutent pas automatiquement

```bash
# Vérifier core.hooksPath
git config --get core.hooksPath
# Devrait afficher : /home/user/.config/git/hooks

# Si vide, configurer :
git config --global core.hooksPath ~/.config/git/hooks

# Vérifier les permissions
ls -la ~/.config/git/hooks/pre-commit
# Devrait commencer par -rwxr-xr-x

# Réparer les permissions si nécessaire
chmod +x ~/.config/git/hooks/pre-commit
chmod +x ~/.config/git/hooks/lib/*.sh
chmod +x ~/.config/git/hooks/runners/*.sh
chmod +x ~/.config/git/hooks/bin/*.sh
```

### Auto-fixes en boucle infinie

Le système a un maximum de 2 retries. Si ça continue :

1. **Identifier le hook problématique** :
```bash
# Exécuter avec verbose
pcr -a --verbose
```

2. **Désactiver temporairement le hook** :
Éditer `.pre-commit-config.yaml` et commenter le hook

3. **Fixer manuellement** puis committer

### Erreur "STEP X/4" ne s'affiche pas

Vérifier que `lib/reporting.sh` est bien sourcé :

```bash
grep "source.*reporting.sh" ~/.config/git/hooks/runners/run-*.sh
```

### Quality gate toujours en échec

```bash
# Vérifier les variables d'environnement
env | grep QUALITY_GATE

# Passer en mode non-bloquant temporairement
QUALITY_GATE_MODE=info pcr -a

# Voir les détails
QUALITY_GATE_REPORT=full pcr -a
```

## 🎨 Personnalisation

### Changer les couleurs

Éditer `lib/reporting.sh` :

```bash
export RED='\033[0;31m'
export GREEN='\033[0;32m'
# etc.
```

### Changer les symboles

```bash
export SYMBOL_SUCCESS="[OK]"
export SYMBOL_ERROR="[FAIL]"
# etc.
```

### Modifier le nombre de retries

Éditer `runners/run-local-precommit.sh` :

```bash
MAX_RETRIES=3  # Au lieu de 2
```

## 📊 Monitoring et Logs

Les logs de pre-commit sont dans :
```bash
~/.cache/pre-commit/
```

Pour activer le logging détaillé :
```bash
# Dans le hook ou runner
exec > >(tee -a ~/.config/git/hooks/pre-commit.log)
exec 2>&1
```

## 🤝 Contribution

Pour proposer des améliorations :

1. Tester en local
2. Vérifier que tous les runners fonctionnent individuellement
3. Vérifier que le flux complet fonctionne
4. Documenter les changements dans ce README

## 📄 Licence

MIT - Libre d'utilisation et modification

---

**Dernière mise à jour** : 25 février 2026
**Version** : 2.0 (architecture modulaire)
