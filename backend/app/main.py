from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.db.session import init_db

from app.api.routes import upload, scrape, analyze, export

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifecycle de la aplicación.
    - Startup: inicializa la base de datos.
    - Shutdown: cleanup.
    """
    try:
        init_db()
    except Exception as e:
        print(f"Error inicializando la base de datos: {e}")
        print("La API iniciará, pero las operaciones de DB podrían fallar.")

    yield

    print("Cerrando aplicación...")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "Sistema de análisis de requisitos de software basado en NLP y LLM. "
        "Evalúa requisitos en 5 dimensiones ISO 29148 (verificabilidad, atomicidad, "
        "ambigüedad, completitud, trazabilidad) y genera feedback de mejora."
    ),
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(upload.router)
app.include_router(scrape.router)
app.include_router(analyze.router)
app.include_router(export.router)


@app.get("/", tags=["Health"])
async def root():
    """Health check y bienvenida."""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "docs": "/docs",
        "llm_provider": settings.LLM_PROVIDER,
        "endpoints": {
            "upload_pdf": "POST /upload/pdf",
            "scrape": "POST /scrape",
            "analyze": "POST /analyze",
            "requirements": "GET /requirements",
            "export_dataset": "GET /export/dataset",
            "export_chunks": "GET /export/chunks",
            "scrape_sources": "GET /scrape/sources",
        },
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """Verificación detallada de salud del sistema."""
    health = {
        "api": "ok",
        "database": "unknown",
        "llm_provider": settings.LLM_PROVIDER,
    }

    try:
        from app.db.session import engine
        from sqlalchemy import text

        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        health["database"] = "ok"
    except Exception as e:
        health["database"] = f"error: {str(e)}"

    return health
