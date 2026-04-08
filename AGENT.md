# Agent / boilerplate conventions

Use this file as project guidance for FastAPI + Motor (MongoDB) APIs. Keep rules **general** so they transfer to other services.

## Language

- User-facing API strings (`detail`, validation messages where exposed): **English**.
- Code comments and internal docs: **English** unless the product explicitly requires another language.

## HTTP routes (try / except)

- Wrap route handler bodies in `try` / `except`.
- **`except HTTPException: raise`** — never swallow intentional status codes (401, 409, etc.).
- **`except Exception`** — map to `HTTPException` with `status.HTTP_500_INTERNAL_SERVER_ERROR`, use `detail=str(e)` or a safe generic message, and chain with `from e` when re-raising.
- Prefer **`fastapi.status`** constants everywhere instead of raw integers (`201`, `401`, `500`, …).

## MongoDB document models (Pydantic, not ODM)

### Base document: `CustomDBDocument`

- Shared fields: `id` (alias **`_id`**), `created_at`, `updated_at`, soft-delete flags, etc.
- Set **`model_config = ConfigDict(populate_by_name=True)`** so Mongo dicts with `_id` validate correctly.

### Subclasses (e.g. `UserInDB`)

- **Do not redefine `id`** if the parent already maps `_id` → `id`. Redefining **replaces** the field and **drops** `alias="_id"`, which breaks `Model.model_validate(mongo_doc)`.
- Add only **domain-specific** fields on top of the base.
- For API responses, use separate **out** models (`UserOut`) that never include secrets (`hashed_password`, etc.).

### `_id` → `id` in JSON

- Responses should expose string **`id`**, not raw `ObjectId`. Handle conversion in serializers or explicit mapping; keep one convention project-wide.

## Security

### Passwords

- Enforce **bcrypt’s 72-byte UTF-8 limit** in Pydantic (`field_validator`) so hashing never raises at runtime.
- On login, when the user is **unknown**, still run **`verify_password(plain, DUMMY_HASH)`** once against a fixed dummy hash so timing does not leak whether the email exists (FastAPI security tutorial pattern).

### JWT (e.g. PyJWT + HS256)

- **`JWT_SECRET` must be at least 32 bytes** (RFC 7518 / PyJWT warnings). Validate in settings or document `openssl rand -hex 32`.
- Encode/decode with explicit **`algorithm=`** / **`algorithms=[...]`** (never typo kwargs).

## Layering

- **Routers**: thin — parse/validate input, call service, return models.
- **Services**: business rules, DB access, raise `HTTPException` for domain conflicts (e.g. duplicate email → 409) if that matches your style; keep routers free of heavy logic.

## Docker / local dev

- Package apps as **`app.main:app`** with **`PYTHONPATH`** pointing at the project root so relative imports (`from .core…`) work.
- If `docker compose watch` + `sync` causes host user/`getent` issues, prefer **bind mounts + reload** or run dev container as root only in dev — pick one pattern and document it.

---
