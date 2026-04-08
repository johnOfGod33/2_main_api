# 2ème Main — API

2ème Main is a marketplace API for buying and selling second-hand items.
It lets individuals list their pre-owned goods, connect with potential buyers,
and close deals in a simple, trusted environment.
Built with performance and scalability in mind from day one.

## Stack

| Layer     | Technology                      |
| --------- | ------------------------------- |
| Framework | FastAPI                         |
| Database  | MongoDB (Motor async)           |
| Auth      | JWT — python-jose + passlib     |
| Upload    | AWS S3 + presigned URLs (boto3) |
| Config    | pydantic-settings + .env        |

## Getting started

```bash
cp .env.example .env
# fill in your environment variables
uvicorn app.main:app --reload
```

## Environment variables

```env
MONGODB_URI=mongodb://localhost:27017
MONGODB_DB_NAME=deuxieme_main
JWT_SECRET=change_me_in_production
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=60
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_S3_BUCKET=
AWS_REGION=eu-west-3
```

## Endpoints

### Auth

| Method | Route          | Description         | Auth |
| ------ | -------------- | ------------------- | ---- |
| POST   | /auth/register | Create an account   | ❌   |
| POST   | /auth/login    | Sign in → JWT token | ❌   |

### Articles _(Sprint 2)_

| Method | Route          | Description        | Auth |
| ------ | -------------- | ------------------ | ---- |
| GET    | /articles      | List articles      | ❌   |
| GET    | /articles/{id} | Get article detail | ❌   |
| POST   | /articles      | Create an article  | ✅   |
| PATCH  | /articles/{id} | Update an article  | ✅   |
| DELETE | /articles/{id} | Delete an article  | ✅   |

### Upload _(Sprint 3)_

| Method | Route           | Description            | Auth |
| ------ | --------------- | ---------------------- | ---- |
| POST   | /upload/presign | Get a S3 presigned URL | ✅   |

## Project structure

```
app/
├── main.py
├── core/
│   ├── config.py         # pydantic settings
│   ├── security.py       # JWT + password hashing
│   └── database.py       # Motor connection
├── modules/
│   ├── user/
│   │   ├── model.py      # Pydantic models
│   │   ├── service.py    # Business logic
│   │   └── router.py     # /auth routes
│   ├── article/          # Sprint 2
│   └── upload/           # Sprint 3
└── dependencies.py       # Guards (get_current_user)
```

## Roadmap

- [x] Sprint 1 — User & Authentication
- [ ] Sprint 2 — Article CRUD
- [ ] Sprint 3 — Image upload (S3)
- [ ] Sprint 4 — Messaging between users
- [ ] Sprint 5 — Orders & transactions
