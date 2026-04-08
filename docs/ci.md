# CI — GitHub Actions

Le fichier `.github/workflows/ci.yml` (à la racine du dépôt) reproduit les parties **quality**, **tests** et **pages** de l’ancienne chaîne GitLab.

## Déclencheurs

- **Push** et **pull_request** sur les branches `main` et `master`
- **`workflow_dispatch`** (lancement manuel)

## Jobs

### Quality

- Image : Ubuntu + Python **3.13**
- `pip install -r app/requirements.txt`
- `flake8 app tests`
- `black --check app tests`
- `bandit -r app -c pyproject.toml -f txt`

### Tests

- Même installation Python
- `PYTHONPATH=app:.`
- `pytest` avec rapports JUnit (`report.xml`) et couverture XML (`coverage.xml`)
- Tant qu’aucun test n’est collecté, le workflow accepte le **code de sortie 5** de pytest et force **`--cov-fail-under=0`** via `--override-ini` pour ne pas bloquer la CI

Artefacts : **junit-report**, **coverage-xml**.

### GitHub Pages

- Exécuté **uniquement** sur **push** vers `main` ou `master`, après succès de quality + test
- `mkdocs build --strict` → dossier `public/`
- Déploiement via les actions officielles `upload-pages-artifact` et `deploy-pages`

**Prérequis côté GitHub** : dans **Settings → Pages**, choisir la source **GitHub Actions** (et non « Deploy from a branch »).

## Équivalence GitLab

| GitLab (`.gitlab/ci/`) | GitHub Actions |
|------------------------|----------------|
| `quality.yml` | Job `quality` |
| `tests.yml` | Job `test` (+ artefacts) |
| `pages.yml` | Job `pages` (branches `main`/`master` au lieu de `prod`/`staging` uniquement) |

Tu peux ajuster la condition `if:` du job `pages` dans le workflow si tu veux limiter le déploiement à une branche nommée comme en GitLab.
