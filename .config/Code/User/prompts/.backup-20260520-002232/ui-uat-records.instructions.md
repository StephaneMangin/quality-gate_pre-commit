---
description: "UAT records harness standards: pytest-playwright, page objects, cursor overlay, MP4 artefacts, Odoo-version agnostic selectors. For UAT/ or any Playwright test against an Odoo web UI."
applyTo: "**/UAT/**"
---

# UI UAT Harness (Odoo, pytest-playwright)

Objective: drive an Odoo web UI as human operator (see, click, validate) and produce human-watchable evidence (MP4 videos, screenshots, filtered server log, trace.zip) per run. All guidance below is intentionally agnostic of the Odoo major version → never hard-code version number.

## Layout (MANDATORY)

```
UAT/
  conftest.py          # fixtures, hooks, webm→mp4 auto-convert, cursor injection
  pytest.ini           # isolates this suite from the parent odoo test config
  core/
    config.py          # UIConfig dataclass, env-driven
    waits.py           # Odoo-aware waits (DOM anchors, NOT networkidle)
    artifacts.py       # ArtifactRecorder (screenshots + summary.json)
    cursor_overlay.py  # JS init script — synthetic cursor for videos
    server_logs.py     # ServerLogCapture (filters Odoo log lines per test)
  pages/               # Page Object Model, one file per screen
  scenarios/           # Data seeders (Python scripts shelled out)
  tests/               # test_*.py (consume fixtures only)
  artifacts/           # gitignored — run_YYYYMMDD_HHMMSS/<nodeid>/…
```

Respect this layout when adding features. Never put business logic in tests.

## Non-negotiable rules

- **Never run pytest without `-p no:odoo`** when Odoo's pytest plugin is installed in same venv → it auto-loads module and corrupts collection. `pytest.ini` in this folder must keep `-p no:odoo` or run it explicitly.
- **Never use `page.wait_for_load_state("networkidle")`** against Odoo → bus/websocket long-poll prevents idle. Use DOM anchors: `.o_main_navbar`, `.o_action_manager`, `.o_barcode_client_action`, or screen-specific selector, via `wait_web_client_ready()` helper.
- **Never click invisible elements.** Always chain `button:visible` or use `.locator(...).filter(has_text=...).first` **only after** filtering by `:visible`. Multi-instance DOM (hidden duplicates) is common in Odoo's OWL views.
- **Never expose private RPC from JS.** If scenario requires server-side helper, add public method on the Odoo model and call it via public RPC. Document public alias.
- **Never commit `artifacts/`** → it's gitignored. Also ignore `__pycache__`, `.pytest_cache`.
- **Never keep `.webm`** in final run output → they are auto-converted to `.mp4` by session teardown in `conftest.py`. MP4 is only human-distributable format.

## Odoo-version agnosticism

harness **must** work across Odoo major versions without code change. Enforce this by:

1. **Detect the version dynamically** at fixture time. Preferred order:
- Read `odoo.release.version_info` when `odoo` Python package is importable in test venv.
- Else parse project's config (`odoo-ci.cfg` / `odoo.cfg`) and/or manifest of any addon (`__manifest__.py` `"version"` key: e.g. `"18.0.1.0.0"` → major `18`).
- Else fall back to `ODOO_VERSION` env var (int, e.g. `18`).

Expose it as `UIConfig.odoo_version: int` and as pytest fixture `odoo_version`.

2. **Branch selectors, not behaviour.** When selector changes across versions, create helper in `core/waits.py` or small `core/selectors.py` module:
   ```python
   def validate_button(odoo_version: int) -> str:
       if odoo_version >= 18:
           return 'button:has-text("Validate")'
       return '.o_statusbar_buttons button[name="button_validate"]'
   ```
Tests call helper; never inline version checks in `tests/`.

3. **Page objects receive `UIConfig`** (do). They must read `config.odoo_version` when building version-sensitive locators. Keep dispatch local to page object.

4. **Seeding scripts** under `scripts/<addon>/setup_*.py` must themselves be version-agnostic (use ORM APIs that are stable, avoid `new_api` vs `old_api` split by favouring `self.env` and `Command.*`). Seeders are Python scripts shelled out; they read the same `odoo-ci.cfg`.

5. **Document** any version-specific branch with a comment citing the Odoo release notes URL. No silent compat shims.

## Mandatory fixtures in new tests

- `ui_config` (session) — env-driven `UIConfig` incl. detected `odoo_version`.
- `authenticated_page` → returns logged-in Playwright `Page`.
- `recorder` → call `recorder.step("label")` at every meaningful UI checkpoint; it captures screenshot and appends to `summary.json`.
- `server_log` → filters the Odoo log to only lines emitted during test body (requires `ODOO_LOG_FILE` env).
- `odoo_version` — integer major version; inject it into page objects.

## Video quality (already configured)

- `UI_UAT_SLOWMO_MS` default = **400 ms** → gives watchable rhythm.
- Cursor overlay is auto-injected via `context.add_init_script(CURSOR_INIT_SCRIPT)` in `autouse` fixture. It draws red dot that follows `mousemove/down/up` with CSS transitions so cursor *glides* between targets and emits ripple on click.
- Session teardown transcodes every `*.webm` → `*.mp4` (H.264, yuv420p, faststart) via `ffmpeg`, then deletes source `.webm`. If `ffmpeg` is absent webm is kept; add `ffmpeg` to dev image.

## Environment variables

| Variable                 | Default                  | Purpose                                      |
| ------------------------ | ------------------------ | -------------------------------------------- |
| `ODOO_URL`               | `http://localhost:8069`  | Odoo base URL                                |
| `ODOO_DB`                | project-specific         | Database (read from `odoo-ci.cfg` if unset)  |
| `ODOO_LOGIN` / `_PASSWORD` | `admin`/`admin`        | Login used by `LoginPage`                    |
| `ODOO_RC`                | `odoo-ci.cfg`            | Config file consumed by seeders              |
| `ODOO_LOG_FILE`          | unset                    | Path to Odoo log for `server_log` fixture    |
| `ODOO_VERSION`           | auto-detect              | Force a major version (CI, edge cases)       |
| `UI_UAT_HEADED`    | `0`                      | `1` to show Chromium                         |
| `UI_UAT_SLOWMO_MS` | `400`                    | Delay between Playwright actions             |
| `UI_UAT_ARTIFACTS` | `artifacts/ui_uat` | Root dir for run artefacts                   |

## Scénario (narratif) — obligatoire avant tout code

Un test UAT records doit raconter une histoire métier cohérente, pas seulement vérifier un assert. Avant d'ouvrir Playwright, formaliser le scénario en haut du fichier de test (docstring de module ou de classe).

### Structure obligatoire d'un scénario

1. **Contexte métier** (1–2 phrases) — rôle de l'utilisateur, état initial du système, fonctionnalité visée. Vocabulaire fonctionnel, pas technique.
2. **Donnée seed** — liste des records préparés par le seeder (noms lisibles dans la vidéo, pas d'ids). Doivent permettre de rejouer le scénario.
3. **Étapes UI numérotées** — chaque étape = une action humaine atomique (« ouvre le menu Contacts », « sélectionne le groupe X », « valide »). Une étape = un `recorder.step("…")` dans le test.
4. **Vérifications visibles à l'écran** — ce que le viewer doit observer (badge, ligne ajoutée, valeur d'un champ). Pas d'assert sur des champs non visibles dans la vidéo : si c'est invisible, ouvrir la vue qui l'affiche dans une étape supplémentaire.
5. **État final attendu** — résumé en 1 phrase.

### Règles narratives

- **Une histoire, un test.** Si le scénario contient « ET ALORS … ET ALORS … » qui changent de sujet métier, splitter en deux tests.
- **Étapes nommées avec verbe métier**, pas technique. `recorder.step("Assign customer group APL Pro")` plutôt que `recorder.step("click_button_2")`.
- **Pas de raccourci ORM dans le corps du test** pour préparer un état que l'utilisateur final atteindrait via l'UI : ce raccourci appartient au seeder. Le test ne fait que jouer le parcours.
- **Rythme.** Insérer un `recorder.step()` au moins toutes les 2 actions Playwright pour que la vidéo reste lisible et que `summary.json` soit une vraie timeline.
- **Cohérence avec la spec fonctionnelle** : si la demande dit « lorsqu'on assigne le groupe → la pricelist se remplit », le scénario doit *montrer* la pricelist se remplir à l'écran (ouvrir l'onglet Sales / Vente après l'assignation), pas seulement l'asserter en back-office.

### Squelette de docstring de test

```python
"""Customer group default pricelist propagation.

Contexte: un opérateur APL crée/édite un contact et lui assigne un
groupe client; la pricelist du groupe doit se reporter par défaut.

Seed:
  - Customer group "APL Pro" with pricelist "EUR Pro Tier"
  - Customer group "APL Standard" without pricelist
  - Partner "John Doe" without pricelist

Steps:
  1. Open Contacts → John Doe form view.
  2. Set Customer Group = "APL Pro".
  3. Save → observe Pricelist field auto-filled to "EUR Pro Tier".
  4. Change Customer Group to "APL Standard".
  5. Save → observe Pricelist unchanged ("EUR Pro Tier" preserved).

Expected: explicit pricelist on the partner is never silently erased.
"""
```

## Adding a scenario — implementation steps

> Le scénario narratif (cf. section précédente) doit être figé avant l'étape 1.

1. Write or extend a **page object** under `pages/` with `:visible`-filtered locators and a version-aware helper when needed.
2. Add a **seeder** under `scenarios/` (or thin wrapper shelling out to `scripts/<addon>/setup_*.py`). Return frozen dataclass with ids + names.
3. Write `tests/test_<feature>.py` — first failing. Consume: `authenticated_page, ui_config, recorder, server_log, odoo_version`, plus your seed fixture.
4. Implement page object method until test passes.
5. Run suite: `pytest -p no:odoo UAT -q`. Watch generated MP4 to validate rhythm and click targets.
6. Pre-commit: suite: ruff/black/isort clean. Per-file ignores for harness live in project `pyproject.toml`.

## Artefact layout (per run)

```
artifacts/ui_uat/run_YYYYMMDD_HHMMSS/
  <test-node-id>/
    step_01_<label>.png, step_02_<label>.png, …
    summary.json                 # steps + status + error
    server_log_filtered.log      # Odoo lines during test body only
    videos/*.mp4                 # auto-converted from webm
    trace.zip                    # present only with --tracing=on
```

## Common pitfalls (learned)

- `networkidle` blocks forever → use DOM anchors.
- `button` locator matching both visible and invisible → always add `:visible`.
- `pytest-odoo` eager-loading → `-p no:odoo` in CLI or `pytest.ini`.
- Playwright downloading `chromium-headless-shell` fails with `ENOSPC` → install full Chromium (`playwright install chromium`) and rely on its headless mode; avoid `channel="chromium"` hacks once disk is OK.
- `.mp4` not produced → `ffmpeg` missing on host; install it.
- Cursor invisible in video → overlay fixture not autoused; keep `_inject_cursor_overlay` `autouse=True`.

## Reviewing a UAT run

- Open `summary.json` to understand step timeline and failure reason.
- Watch the MP4 in VLC / browser at real speed → if any action is inaudible/invisible, bump slowmo or add `recorder.step()` right before it.
- Correlate with `server_log_filtered.log` for backend errors (AccessError, ValidationError, private-method RPC rejection).

## Reference implementation skeleton

This is **single source of truth** for harness internals. Any new workspace must reproduce these contracts byte-for-byte (module names, fixture names, return types). Deviations break rest of instructions.

### `pytest.ini` (harness-local)

```ini
[pytest]
addopts = -p no:odoo --strict-markers
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
```

### `.gitignore` entries (repo root)

```
UAT/artifacts/
UAT/.pytest_cache/
UAT/**/__pycache__/
```

### `pyproject.toml` snippets (parent project)

```toml
[project.optional-dependencies]
test = [
  "pytest-playwright>=0.5",
  # plus project-specific test deps
]

[tool.ruff.lint.per-file-ignores]
"UAT/**" = ["S101", "S603", "E501"]
```

### `core/config.py`

```python
"""UIConfig: env-driven, Odoo-version aware."""
from __future__ import annotations
import configparser
import os
import re
from dataclasses import dataclass
from pathlib import Path

def _env_bool(k: str, d: bool = False) -> bool:
    v = os.environ.get(k)
    return d if v is None else v.lower() in {"1", "true", "yes", "on"}

def _env_int(k: str, d: int) -> int:
    v = os.environ.get(k)
    return d if v in (None, "") else int(v)

def _detect_odoo_version(config_path: Path) -> int:
    # 1. env override
    env = os.environ.get("ODOO_VERSION")
    if env:
        return int(env)
    # 2. importable odoo package
    try:
        import odoo.release as _rel  # type: ignore
        return int(_rel.version_info[0])
    except Exception:
        pass
    # 3. any __manifest__.py in the workspace (first match wins)
    root = Path.cwd()
    for manifest in root.rglob("__manifest__.py"):
        try:
            txt = manifest.read_text(encoding="utf-8", errors="ignore")
            m = re.search(r'"version"\s*:\s*"(\d+)\.', txt)
            if m:
                return int(m.group(1))
        except Exception:
            continue
    # 4. parse odoo-ci.cfg / odoo.cfg — no version key, so give up
    _ = configparser.ConfigParser()  # placeholder, kept for future heuristics
    raise RuntimeError("Cannot detect Odoo version; set ODOO_VERSION env var.")

@dataclass(frozen=True)
class UIConfig:
    base_url: str
    db_name: str
    login: str
    password: str
    headed: bool
    slowmo_ms: int
    artifacts_root: Path
    odoo_log_file: Path | None
    odoo_config: Path
    odoo_version: int

    @classmethod
    def from_env(cls) -> "UIConfig":
        artifacts = Path(
            os.environ.get("UI_UAT_ARTIFACTS", "artifacts/ui_uat")
        ).resolve()
        log_file = os.environ.get("ODOO_LOG_FILE") or None
        config = Path(os.environ.get("ODOO_RC", "odoo-ci.cfg"))
        return cls(
            base_url=os.environ.get("ODOO_URL", "http://localhost:8069").rstrip("/"),
            db_name=os.environ.get("ODOO_DB", "odoo"),
            login=os.environ.get("ODOO_LOGIN", "admin"),
            password=os.environ.get("ODOO_PASSWORD", "admin"),
            headed=_env_bool("UI_UAT_HEADED", False),
            slowmo_ms=_env_int("UI_UAT_SLOWMO_MS", 400),
            artifacts_root=artifacts,
            odoo_log_file=Path(log_file).resolve() if log_file else None,
            odoo_config=config,
            odoo_version=_detect_odoo_version(config),
        )
```

### `core/cursor_overlay.py`

```python
CURSOR_INIT_SCRIPT = r"""
(() => {
    if (window.__uiUatCursorInstalled) return;
    window.__uiUatCursorInstalled = true;
    const install = () => {
        if (!document.body) return requestAnimationFrame(install);
        const cursor = document.createElement('div');
        cursor.id = '__ui-UAT-cursor';
        Object.assign(cursor.style, {
            position: 'fixed', top: '0', left: '0',
            width: '22px', height: '22px', borderRadius: '50%',
            background: 'rgba(220,38,38,0.55)',
            border: '2px solid rgba(220,38,38,0.95)',
            boxShadow: '0 0 0 2px rgba(255,255,255,0.9)',
            pointerEvents: 'none', zIndex: '2147483647',
            transform: 'translate(-50%,-50%)',
            transition: 'left 180ms ease-out, top 180ms ease-out, '
                      + 'background 120ms ease, transform 80ms ease',
        });
        document.body.appendChild(cursor);
        const move = e => { cursor.style.left = e.clientX+'px';
                            cursor.style.top  = e.clientY+'px'; };
        const press = () => { cursor.style.background='rgba(250,204,21,0.85)';
                              cursor.style.transform='translate(-50%,-50%) scale(0.7)'; };
        const release = () => { cursor.style.background='rgba(220,38,38,0.55)';
                                cursor.style.transform='translate(-50%,-50%) scale(1)'; };
        addEventListener('mousemove', move, true);
        addEventListener('mousedown', press, true);
        addEventListener('mouseup', release, true);
        addEventListener('click', () => {
            const r = cursor.cloneNode();
            r.style.background='transparent';
            r.style.border='2px solid rgba(220,38,38,0.9)';
            r.style.transition='all 400ms ease-out';
            document.body.appendChild(r);
            requestAnimationFrame(() => {
                r.style.width='60px'; r.style.height='60px'; r.style.opacity='0';
            });
            setTimeout(() => r.remove(), 450);
        }, true);
    };
    install();
})();
"""
```

### `core/artifacts.py` (contract)

```python
@dataclass
class ArtifactRecorder:
    page: Page
    output_dir: Path          # per-test dir under run_root
    test_name: str            # pytest nodeid
    steps: list[StepRecord] = field(default_factory=list)

    def step(self, label: str) -> None: ...        # screenshot + append
    def dump_summary(self, status: str, error: str | None = None) -> None: ...
```

`summary.json` shape:

```json
{"test": "...", "status": "passed|failed|skipped", "error": null,
 "steps": [{"index": 1, "label": "...", "screenshot": "step_01_...png", "ts": 0.0}]}
```

### `core/server_logs.py` (contract)

```python
class ServerLogCapture:
    def __init__(self, path: Path | None) -> None: ...
    def __enter__(self) -> "ServerLogCapture": ...   # records file size
    def __exit__(self, *exc) -> bool: ...            # returns False
    def dump(self, output_file: Path) -> None: ...   # writes filtered slice
```

`filter_lines()` applies `|`-joined regex against each line. Default patterns: `Traceback`, `\bERROR\b`, `Access Error`, plus project-specific keywords (pass custom tuple if needed).

### `core/waits.py` (Odoo-version aware)

```python
from playwright.sync_api import Page

DEFAULT_WEB_CLIENT_ANCHORS = (
    ".o_action_manager, .o_main_navbar, .o_barcode_client_action"
)

def wait_web_client_ready(page: Page, timeout: int = 30000) -> None:
    page.wait_for_load_state("domcontentloaded", timeout=timeout)
    page.wait_for_selector(DEFAULT_WEB_CLIENT_ANCHORS, timeout=timeout)
    page.wait_for_function(
        "document.querySelectorAll('.o_loading').length === 0",
        timeout=timeout,
    )

def wait_no_error_dialog(page: Page) -> None:
    if page.locator(".o_dialog .modal-title.text-danger").count() > 0:
        title = page.locator(".o_dialog .modal-title").first.inner_text()
        raise AssertionError(f"Odoo error dialog detected: {title}")
```

### `core/selectors.py` (version dispatch)

One location for every known selector divergence across Odoo versions. Add function when you hit real divergence; do **not** preempt with speculative versioning.

```python
"""Version-aware selectors. Add entries only when a divergence is observed."""

def validate_button(odoo_version: int) -> str:
    # Odoo 17+: OWL web client exposes the label, Odoo 16- used legacy JS view
    if odoo_version >= 17:
        return 'button:visible:has-text("Validate")'
    return '.o_statusbar_buttons button[name="button_validate"]:visible'

def url_for_client_action(base_url: str, picking_id: int, xmlid: str,
                           odoo_version: int) -> str:
    # Odoo 18+: /odoo/<id>/action-<xmlid>
    # Odoo 16-17: /web#action=<xmlid>&id=<id>
    if odoo_version >= 18:
        return f"{base_url}/odoo/{picking_id}/action-{xmlid}"
    return f"{base_url}/web#action={xmlid}&id={picking_id}"

def login_url(base_url: str, odoo_version: int) -> str:  # noqa: ARG001
    # Stable across versions — kept here for future-proofing.
    return f"{base_url}/web/login"
```

**Rule:** every version branch must cite the Odoo release where change landed (commit, release notes, or forum post) in comment adjacent to `if odoo_version >= N:`.

### `conftest.py` (harness root)

```python
from __future__ import annotations
import shutil, subprocess, sys, time
from pathlib import Path
import pytest

HARNESS_ROOT = Path(__file__).resolve().parent
if str(HARNESS_ROOT) not in sys.path:
    sys.path.insert(0, str(HARNESS_ROOT))

from core.artifacts import ArtifactRecorder  # noqa: E402
from core.config import UIConfig  # noqa: E402
from core.cursor_overlay import CURSOR_INIT_SCRIPT  # noqa: E402
from core.server_logs import ServerLogCapture  # noqa: E402
from pages.login_page import LoginPage  # noqa: E402

@pytest.fixture(scope="session")
def ui_config() -> UIConfig:
    return UIConfig.from_env()

@pytest.fixture(scope="session")
def odoo_version(ui_config: UIConfig) -> int:
    return ui_config.odoo_version

@pytest.fixture(scope="session")
def run_root(ui_config: UIConfig):
    run_id = time.strftime("run_%Y%m%d_%H%M%S")
    root = ui_config.artifacts_root / run_id
    root.mkdir(parents=True, exist_ok=True)
    yield root
    _convert_webm_to_mp4(root)

def _convert_webm_to_mp4(root: Path) -> None:
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        return
    for webm in root.rglob("*.webm"):
        mp4 = webm.with_suffix(".mp4")
        cmd = [ffmpeg, "-y", "-loglevel", "error", "-i", str(webm),
               "-c:v", "libx264", "-pix_fmt", "yuv420p",
               "-preset", "fast", "-crf", "23",
               "-movflags", "+faststart", str(mp4)]
        r = subprocess.run(cmd, capture_output=True, text=True, check=False)
        if r.returncode == 0 and mp4.exists() and mp4.stat().st_size > 0:
            webm.unlink(missing_ok=True)

@pytest.fixture
def artifact_dir(run_root: Path, request) -> Path:
    safe = request.node.nodeid.replace("/", "_").replace("::", "__")
    for bad in "<>:\"\\|?*":
        safe = safe.replace(bad, "_")
    path = run_root / safe
    path.mkdir(parents=True, exist_ok=True)
    return path

@pytest.fixture(scope="session")
def browser_type_launch_args(ui_config: UIConfig, browser_type_launch_args: dict):
    args = dict(browser_type_launch_args)
    args["headless"] = not ui_config.headed
    args["slow_mo"] = ui_config.slowmo_ms
    extra = list(args.get("args", []))
    extra.append("--disable-notifications")
    args["args"] = extra
    return args

@pytest.fixture
def browser_context_args(browser_context_args: dict, artifact_dir: Path):
    args = dict(browser_context_args)
    args["permissions"] = []
    args["record_video_dir"] = str(artifact_dir / "videos")
    args.setdefault("viewport", {"width": 1280, "height": 900})
    return args

@pytest.fixture(autouse=True)
def _inject_cursor_overlay(context):
    context.add_init_script(CURSOR_INIT_SCRIPT)
    yield

@pytest.fixture
def recorder(page, artifact_dir: Path, request):
    rec = ArtifactRecorder(page=page, output_dir=artifact_dir,
                           test_name=request.node.nodeid)
    yield rec
    status = getattr(request.node, "_ui_status", "unknown")
    error = getattr(request.node, "_ui_error", None)
    rec.dump_summary(status=status, error=error)

@pytest.fixture
def server_log(ui_config: UIConfig, artifact_dir: Path):
    cap = ServerLogCapture(ui_config.odoo_log_file)
    with cap as handle:
        yield handle
    cap.dump(artifact_dir / "server_log_filtered.log")

@pytest.fixture
def authenticated_page(page, ui_config: UIConfig):
    LoginPage(page, ui_config).login()
    return page

@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()
    if report.when != "call":
        return
    if report.passed:
        item._ui_status = "passed"; item._ui_error = None
    elif report.failed:
        item._ui_status = "failed"; item._ui_error = str(report.longrepr)
    else:
        item._ui_status = report.outcome; item._ui_error = None
```

### `pages/login_page.py` (minimal reference)

```python
from playwright.sync_api import Page
from core.config import UIConfig
from core.selectors import login_url
from core.waits import wait_web_client_ready

class LoginPage:
    def __init__(self, page: Page, config: UIConfig) -> None:
        self.page = page
        self.config = config

    def login(self) -> None:
        self.page.goto(login_url(self.config.base_url, self.config.odoo_version))
        # Stable selectors: `name="login"` and `name="password"` have been
        # present since Odoo 10; no version dispatch needed yet.
        self.page.fill('input[name="login"]', self.config.login)
        self.page.fill('input[name="password"]', self.config.password)
        self.page.click('button[type="submit"]')
        wait_web_client_ready(self.page)
```

### Page object template (version-aware)

```python
from core.selectors import validate_button
from core.waits import wait_no_error_dialog

class SomeFeaturePage:
    def __init__(self, page, config):
        self.page = page
        self.config = config  # has .odoo_version

    def validate(self) -> None:
        self.page.locator(validate_button(self.config.odoo_version)).first.click()
        wait_no_error_dialog(self.page)
```

### Seeder contract

```python
@dataclass(frozen=True)
class SeedResult:
    # ids + display names created by the seeder
    ...

def seed_<scenario>(db: str, config_path: Path) -> SeedResult:
    # Shell out to scripts/<addon>/setup_<scenario>.py with the Odoo CLI runner
    # and parse stdout with a documented regex. Stdout lines the seeder MUST
    # emit (parseable by the harness):
    #   "Upstream picking: <name> (id=<N>)"
    #   "Downstream picking: <name> (id=<N>)"
    # The seeder itself must be Odoo-version agnostic: stick to stable ORM
    # (self.env, Command.create/set/link, no removed kwargs).
```

### Odoo-version dispatch matrix (living document)

When adding version branch, append row here **before** touching code.

| Concern                | Odoo 16            | Odoo 17            | Odoo 18+           | Helper                              |
| ---------------------- | ------------------ | ------------------ | ------------------ | ----------------------------------- |
| Client-action URL      | `/web#action=...`  | `/web#action=...`  | `/odoo/<id>/action-<xmlid>` | `selectors.url_for_client_action` |
| Validate button        | statusbar legacy   | OWL label          | OWL label          | `selectors.validate_button`         |
| Login page             | `/web/login`       | `/web/login`       | `/web/login`       | `selectors.login_url` (stable)      |
| Barcode picking anchor | `.o_barcode_client_action` | idem       | idem               | `DEFAULT_WEB_CLIENT_ANCHORS`        |

Keep matrix accurate; it's canonical changelog for harness version adapters.

## Checklist when porting the harness to a new workspace

1. Copy `UAT/` skeleton (`core/`, `pages/login_page.py`, `conftest.py`, `pytest.ini`, `README.md`).
2. Add `.gitignore` entries and `pyproject.toml` snippets above.
3. `pip install -e '.[test]' && playwright install chromium`; install `ffmpeg` on host.
4. Set `ODOO_LOG_FILE` in your Odoo runner to the file consumed by `server_log`.
5. Write the first seeder + test; run `pytest -p no:odoo UAT -q`.
6. Inspect the first MP4 to validate cursor visibility and rhythm; tune `UI_UAT_SLOWMO_MS` if needed.
7. Only introduce `core/selectors.py` branches when a real divergence is observed — never upfront.
