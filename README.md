# quality-gate_pre-commit

Pack d’intégration Git hooks pour environnement utilisateur Ubuntu.

Ce dépôt sert à déployer une chaîne de contrôle qualité globale dans `~/.config/git/hooks` :
- pre-commit global
- quality gate Python
- pre-commit local par projet
- tests de modules (si applicable)

`pcr` et `git commit` utilisent le même orchestrateur : `~/.config/git/hooks/pre-commit`.

La documentation technique détaillée des hooks est dans :
`~/.config/git/hooks/README.md` (dans ce dépôt : `.config/git/hooks/README.md`).

## Prérequis (Ubuntu)

- Git
- Bash
- Python 3
- `pre-commit`

Installation minimale suggérée :

```bash
sudo apt update
sudo apt install -y git python3 python3-venv python3-pip
pipx install pre-commit || python3 -m pip install --user pre-commit
```

## Installation (répertoire utilisateur)

Depuis la racine du dépôt :

```bash
# 1) Déployer les hooks dans la config utilisateur
mkdir -p "$HOME/.config/git"
rsync -a --delete .config/git/hooks/ "$HOME/.config/git/hooks/"

# 2) S'assurer que les scripts sont exécutables
chmod +x "$HOME/.config/git/hooks/pre-commit"
find "$HOME/.config/git/hooks/bin" "$HOME/.config/git/hooks/runners" -type f -name "*.sh" -exec chmod +x {} \;

# 3) Activer ce chemin de hooks globalement
git config --global core.hooksPath "$HOME/.config/git/hooks"

# 4) Vérifier
git config --global --get core.hooksPath
```

Résultat attendu :

```text
/home/<utilisateur>/.config/git/hooks
```

## Commande pratique `pcr`

Le binaire fourni par ce dépôt est :
`bin/pcr`

Utilisation directe depuis la racine du dépôt :

```bash
./bin/pcr
./bin/pcr -a
```

Pour l'utiliser globalement sans alias, installe-le dans `~/.local/bin` :

```bash
mkdir -p "$HOME/.local/bin"
install -m 755 bin/pcr "$HOME/.local/bin/pcr"

# Vérifier que ~/.local/bin est dans PATH (Ubuntu le fait généralement)
command -v pcr
```

Si tu utilises ce dépôt pour centraliser tes personnalisations shell, ajoute aussi ce chargement dans `~/.bashrc` :

```bash
grep -qxF 'source "$HOME/.bashrc.custom"' ~/.bashrc || echo 'source "$HOME/.bashrc.custom"' >> ~/.bashrc
source ~/.bashrc
```

## Utilisation

Dans un projet Git :

```bash
# Sur les fichiers staged
pcr

# Sur tout le repo
pcr -a

# Limiter aux répertoires indiqués (CSV)
pcr -a --include-dirs addons,src

# Exclure des répertoires (CSV)
pcr -a --exclude-dirs .venv,addons/legacy

# Combine include + exclude (exclude prioritaire)
pcr -a --include-dirs addons --exclude-dirs addons/legacy
```

Par défaut, `pcr` initialise aussi :
- `PCR_DEFAULT_INCLUDE_DIRS` (union des includes du hook)
- `PCR_DEFAULT_EXCLUDE_DIRS` (exclusions techniques du hook)

Ces valeurs viennent de `~/.config/git/hooks/configs/search-paths.conf`.

Ou simplement via commit Git (automatique) :

```bash
git commit -m "test hooks"
```

Les chemins de recherche/exclusion des outils sont centralisés dans :

`~/.config/git/hooks/configs/search-paths.conf`

## Mise à jour

Après modification de ce dépôt, redéployer :

```bash
cd /chemin/vers/quality-gate_pre-commit
rsync -a --delete .config/git/hooks/ "$HOME/.config/git/hooks/"
```

## Désinstallation

```bash
git config --global --unset core.hooksPath
rm -rf "$HOME/.config/git/hooks"
```
