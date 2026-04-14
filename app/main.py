from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

from .core.database import shutdown_mongodb, start_up_mongodb
from .modules.article.router import router as article_router
from .modules.offer.router import router as offer_router
from .modules.order.router import router as order_router
from .modules.storage.router import router as storage_router
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
app.include_router(article_router)
app.include_router(offer_router, prefix="/offers", tags=["Offers"])
app.include_router(order_router, prefix="/orders", tags=["Orders"])
app.include_router(storage_router)


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


@app.get("/", response_class=HTMLResponse)
async def root():
    return """<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Second Hand API</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,400;0,600;1,400&family=Outfit:wght@300;500&display=swap" rel="stylesheet">
  <style>
    :root {
      --ink: #1a1a1c;
      --paper: #f7f5f0;
      --accent: #8b7355;
      --muted: #6b6560;
      --line: rgba(26, 28, 28, 0.08);
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    html { font-size: 16px; -webkit-font-smoothing: antialiased; }
    body {
      min-height: 100dvh;
      display: flex;
      align-items: center;
      justify-content: center;
      padding: 2rem;
      font-family: "Outfit", system-ui, sans-serif;
      font-weight: 300;
      color: var(--ink);
      background:
        radial-gradient(ellipse 120% 80% at 50% -20%, rgba(139, 115, 85, 0.12), transparent 55%),
        linear-gradient(180deg, var(--paper) 0%, #ebe8e1 100%);
    }
    main {
      max-width: 32rem;
      text-align: center;
      animation: rise 1s ease-out both;
    }
    @keyframes rise {
      from { opacity: 0; transform: translateY(12px); }
      to { opacity: 1; transform: translateY(0); }
    }
    .mark {
      width: 3px;
      height: 2.5rem;
      margin: 0 auto 1.75rem;
      background: linear-gradient(180deg, var(--accent), transparent);
      border-radius: 2px;
    }
    h1 {
      font-family: "Cormorant Garamond", Georgia, serif;
      font-size: clamp(2rem, 6vw, 2.75rem);
      font-weight: 400;
      letter-spacing: 0.02em;
      line-height: 1.15;
      margin-bottom: 0.75rem;
    }
    h1 span { font-style: italic; font-weight: 400; color: var(--accent); }
    p.lead {
      font-size: 1rem;
      color: var(--muted);
      line-height: 1.65;
      margin-bottom: 2rem;
    }
    nav {
      display: flex;
      flex-wrap: wrap;
      gap: 0.75rem;
      justify-content: center;
    }
    a {
      display: inline-flex;
      align-items: center;
      gap: 0.35rem;
      padding: 0.55rem 1.1rem;
      font-size: 0.875rem;
      font-weight: 500;
      text-decoration: none;
      color: var(--ink);
      border: 1px solid var(--line);
      border-radius: 999px;
      background: rgba(255, 255, 255, 0.45);
      backdrop-filter: blur(8px);
      transition: border-color 0.2s, background 0.2s, transform 0.2s;
    }
    a:hover {
      border-color: rgba(139, 115, 85, 0.35);
      background: rgba(255, 255, 255, 0.75);
      transform: translateY(-1px);
    }
    a.primary {
      background: var(--ink);
      color: var(--paper);
      border-color: var(--ink);
    }
    a.primary:hover {
      background: #2d2d30;
      border-color: #2d2d30;
    }
    footer {
      margin-top: 2.5rem;
      font-size: 0.75rem;
      letter-spacing: 0.12em;
      text-transform: uppercase;
      color: var(--muted);
      opacity: 0.85;
    }
  </style>
</head>
<body>
  <main>
    <div class="mark" aria-hidden="true"></div>
    <h1>Second Hand <span>API</span></h1>
    <p class="lead">Vous êtes sur la racine du service. L’interface utile, c’est plutôt la doc OpenAPI — ou vos clients qui appellent les routes métier.</p>
    <nav>
      <a class="primary" href="/docs">Documentation</a>
      <a href="/redoc">ReDoc</a>
      <a href="/health">Santé</a>
    </nav>
    <footer>Marketplace · v0.1</footer>
  </main>
</body>
</html>"""
