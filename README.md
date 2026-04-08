# 2ème Main — API

Clone Vinted. API REST construite avec FastAPI + MongoDB.

## Stack

| Couche          | Techno                          |
| --------------- | ------------------------------- |
| Framework       | FastAPI                         |
| Base de données | MongoDB (Motor async)           |
| Auth            | JWT — python-jose + passlib     |
| Upload          | AWS S3 + presigned URLs (boto3) |
| Config          | pydantic-settings + .env        |

## Lancer le projet

```bash
cp .env.example .env
# remplir les variables dans .env
uvicorn app.main:app --reload
```

## Variables d'environnement

```env
MONGODB_URI=mongodb://localhost:27017
MONGODB_DB_NAME=deuxieme_main
JWT_SECRET=change_me_in_production
JWT_JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=60
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_S3_BUCKET=
AWS_REGION=eu-west-3
```

## Endpoints

### Auth

| Méthode | Route          | Description     | Auth |
| ------- | -------------- | --------------- | ---- |
| POST    | /auth/register | Créer un compte | ❌   |
| POST    | /auth/login    | Connexion → JWT | ❌   |

### Articles _(à venir — Sprint 2)_

| Méthode | Route          | Description          | Auth |
| ------- | -------------- | -------------------- | ---- |
| GET     | /articles      | Lister les articles  | ❌   |
| GET     | /articles/{id} | Détail d'un article  | ❌   |
| POST    | /articles      | Créer un article     | ✅   |
| PATCH   | /articles/{id} | Modifier un article  | ✅   |
| DELETE  | /articles/{id} | Supprimer un article | ✅   |

### Upload _(à venir — Sprint 3)_

| Méthode | Route           | Description               | Auth |
| ------- | --------------- | ------------------------- | ---- |
| POST    | /upload/presign | Générer une presigned URL | ✅   |

## Structure du projet

```
app/
├── main.py
├── core/
│   ├── config.py         # Settings pydantic
│   ├── security.py       # JWT + hash password
│   └── database.py       # Connexion Motor
├── modules/
│   ├── user/
│   │   ├── model.py      # Pydantic models
│   │   ├── service.py    # Logique métier
│   │   └── router.py     # Routes /auth
│   ├── article/          # Sprint 2
│   └── upload/           # Sprint 3
└── dependencies.py       # Guards (get_current_user)
```
