# Development

## Prérequis

- Python **3.13** (aligné sur la CI)
- MongoDB accessible (local ou conteneur)

## Installation locale

```bash
cd 2_main_api
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r app/requirements.txt
cp .env.example .env
```

Lancer l’API :

```bash
export PYTHONPATH=app:.
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Variables d’environnement

Le code utilise **`MONGODB_DB`** (et non `MONGODB_DB_NAME`). Exemple minimal :

```env
MONGODB_URI=mongodb://localhost:27017
MONGODB_DB=deuxieme_main
JWT_SECRET=change-me-in-dev-use-a-long-random-secret
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=1440
ENVIRONMENT=development
```

Pour Cloudflare R2 / upload, compléter les variables storage de `.env.example`:

```env
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
AWS_S3_BUCKET=...
AWS_REGION=auto
R2_ACCOUNT_ID=<account_id>   # ou AWS_S3_ENDPOINT_URL=https://<account_id>.r2.cloudflarestorage.com
```

Flow recommande pour les images article:
1. Uploader chaque image via `POST /storage/upload`.
2. Recuperer la `key` retournee.
3. Envoyer ces `key` dans `POST /articles` -> champ `images`.

## Docker

Fichiers à la racine : `docker-compose.yml`, `docker-compose.dev.yml`. Adapte les ports et volumes selon ton environnement, puis :

```bash
docker compose -f docker-compose.dev.yml up -d
```

## Données de démo (seed)

Script : `scripts/seed.py` (après configuration `.env` et API joignable / Mongo prêt).

```bash
export PYTHONPATH=app:.
python scripts/seed.py
```

## Qualité & tests (local)

```bash
flake8 app tests
black --check app tests
bandit -r app -c pyproject.toml -f txt
pytest
```

La couverture et les options strictes sont définies dans `pytest.ini` ; la CI GitHub peut surcharger certaines options tant que la suite de tests est vide ou minimale.

## Documentation statique

```bash
mkdocs serve    # http://127.0.0.1:8000 (port par défaut MkDocs)
mkdocs build --strict
```

Le dossier de sortie est **`public/`** (voir `mkdocs.yml`).
