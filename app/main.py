from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware

from .core.database import shutdown_mongodb, start_up_mongodb
from .modules.user.router import router as auth_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    await start_up_mongodb(app)
    yield
    await shutdown_mongodb(app)


app = FastAPI(
    title="Second Hand API",
    description="Marketplace API (Vinted-like)",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)


@app.get("/health", status_code=status.HTTP_200_OK)
async def health(request: Request):
    """Health check endpoint."""
    try:
        mongo_health = await request.app.client.admin.command("ping")

        if mongo_health["ok"] == 1:
            return {"status": "ok", "mongo_health": mongo_health}
        else:
            raise RuntimeError("MongoDB is not healthy")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        ) from e
