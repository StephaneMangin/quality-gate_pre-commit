# quality-gate_pre-commit

Hooks Git globaux simples pour lancer une pipeline qualité sur chaque commit.

## Ce que ça fait

`pcr` et `git commit` exécutent le même flux :
- pre-commit global
- quality gate Python
- pre-commit local du projet
- tests modules (si applicable)

## Prérequis

- Git
- Python 3
- pre-commit

```bash
sudo apt update
sudo apt install -y git python3 python3-venv python3-pip
pipx install pre-commit || python3 -m pip install --user pre-commit
```

## Installation

Depuis la racine du dépôt :

```bash
mkdir -p "$HOME/.config/git"
rsync -a --delete .config/git/hooks/ "$HOME/.config/git/hooks/"

chmod +x "$HOME/.config/git/hooks/pre-commit"
find "$HOME/.config/git/hooks/bin" "$HOME/.config/git/hooks/runners" -type f -name "*.py" -exec chmod +x {} \;

git config --global core.hooksPath "$HOME/.config/git/hooks"
git config --global --get core.hooksPath
```

## Commande `pcr`

```bash
./bin/pcr
./bin/pcr -a
```

Optionnel (install globale) :

```bash
mkdir -p "$HOME/.local/bin"
install -m 755 bin/pcr "$HOME/.local/bin/pcr"
command -v pcr
```

## Usage

Dans un projet Git :

```bash
pcr
pcr -a

QUALITY_GATE_INCLUDE_DIRS=addons,src pcr -a
QUALITY_GATE_EXCLUDE_DIRS=.venv,addons/legacy pcr -a
QUALITY_GATE_INCLUDE_DIRS=addons QUALITY_GATE_EXCLUDE_DIRS=addons/legacy pcr -a
```

Les chemins include/exclude se pilotent via variables d'environnement (`QUALITY_GATE_INCLUDE_DIRS`, `QUALITY_GATE_EXCLUDE_DIRS`).

## Mise à jour

```bash
rsync -a --delete .config/git/hooks/ "$HOME/.config/git/hooks/"
```

## Désinstallation

```bash
git config --global --unset core.hooksPath
rm -rf "$HOME/.config/git/hooks"
```
