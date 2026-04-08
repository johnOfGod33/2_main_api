# 2ème Main API

API marketplace **seconde main** (type Vinted) : annonces, offres, commandes et authentification JWT. Cette documentation est générée avec [MkDocs Material](https://squidfunk.github.io/mkdocs-material/) et peut être publiée sur **GitHub Pages**.

## En bref

| Élément | Détail |
|--------|--------|
| Framework | [FastAPI](https://fastapi.tiangolo.com/) |
| Base de données | MongoDB via [Motor](https://motor.readthedocs.io/) (async) |
| Auth | JWT (`python-jose`, `passlib`) |
| Config | `pydantic-settings` + fichier `.env` |
| Docs | MkDocs + thème Material, plugin Mermaid |

## Démarrage rapide

```bash
cp .env.example .env   # puis éditer les variables
pip install -r app/requirements.txt
export PYTHONPATH=app:.
uvicorn app.main:app --reload
```

- **OpenAPI / Swagger** : `http://127.0.0.1:8000/docs`
- **Santé** : `GET /health` (vérifie MongoDB)

## Pages de cette doc

- [**Architecture**](architecture.md) — couches, modules, flux.
- [**API & modules**](technical.md) — routes principales et responsabilités.
- [**Development**](development.md) — Docker, seed, variables d’environnement.
- [**CI / GitHub Actions**](ci.md) — quality, tests, déploiement Pages.

## GitHub Pages

1. Dans le dépôt GitHub : **Settings → Pages** — source **GitHub Actions**.
2. Dans `mkdocs.yml`, remplace `site_url` par l’URL réelle du site (ex. `https://<org>.github.io/<repo>/`) pour les liens canoniques et le plugin search.

Après un push sur `main` (ou `master`), le workflow **CI** construit le site avec `mkdocs build --strict` et le déploie.
