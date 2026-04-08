# API & modules

Les schémas détaillés et exemples de requêtes sont disponibles dans la **doc interactive** FastAPI : `/docs` (Swagger UI) et `/redoc`.

## Endpoints transverses

| Méthode | Chemin | Description |
|---------|--------|-------------|
| GET | `/health` | Vérifie l'API et MongoDB |

## Authentification (`app/modules/user`)

| Méthode | Chemin | Auth | Description |
|---------|--------|------|-------------|
| POST | `/auth/register` | Non | Création de compte |
| POST | `/auth/login` | Non | Obtention d'un JWT |
| GET | `/auth/me` | Oui | Profil de l'utilisateur connecté |

Les routes protégées attendent un header `Authorization: Bearer` suivi du jeton JWT.

## Articles (`app/modules/article`)

| Méthode | Chemin | Auth | Description |
|---------|--------|------|-------------|
| GET | `/articles` | Non | Liste / filtre |
| GET | `/articles/{id}` | Non | Détail |
| POST | `/articles` | Oui | Création |
| PATCH | `/articles/{id}` | Oui | Mise à jour |
| DELETE | `/articles/{id}` | Oui | Suppression |

## Offres (`app/modules/offer`)

Préfixe : `/offers`. Les réponses enrichies peuvent inclure les informations de l'article associé (agrégations MongoDB côté service).

## Commandes (`app/modules/order`)

Préfixe : `/orders`. Même principe d'enrichissement avec le détail article.

## Configuration runtime

Les paramètres sont lus depuis l'environnement (voir [Development](development.md)). Le fichier `app/core/config.py` définit notamment :

- `MONGODB_URI`, `MONGODB_DB`
- `JWT_SECRET`, `JWT_ALGORITHM`, `JWT_EXPIRE_MINUTES`
- `ENVIRONMENT` (development, staging, production)
