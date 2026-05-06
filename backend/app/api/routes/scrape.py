from fastapi import APIRouter, HTTPException

from app.schemas.schemas import ScrapeRequest, ScrapeResponse
from app.services.ingestion.scraper_service import scrape_requirements
from app.services.cleaning.cleaning_service import clean_pipeline
from app.services.retriever.retriever_service import index_requirements

router = APIRouter(prefix="/scrape", tags=["Scraping"])


@router.post(
    "",
    response_model=ScrapeResponse,
    summary="Scrapear requisitos de una URL",
    description=(
        "Extrae requisitos de software de una página web. "
        "Opcionalmente se puede especificar un selector CSS para dirigir la extracción."
    ),
)
async def scrape_url(request: ScrapeRequest):
    """
    Pipeline de scraping:
    1. Descargar y parsear la página web.
    2. Extraer textos que parecen requisitos.
    3. Limpiar y normalizar.
    4. Indexar en pgvector.
    """
    try:
        scraped = scrape_requirements(
            url=request.url,
            css_selector=request.css_selector,
        )

        if not scraped:
            return ScrapeResponse(
                url=request.url,
                requirements_found=0,
                requirements_saved=0,
                requirements=[],
            )

        raw_texts = [r.text for r in scraped]
        clean_reqs = clean_pipeline(raw_texts)

        saved_count = index_requirements(
            texts=clean_reqs,
            source="scrape",
            source_name=request.url,
        )

        return ScrapeResponse(
            url=request.url,
            requirements_found=len(scraped),
            requirements_saved=saved_count,
            requirements=clean_reqs[:50],
        )

    except ConnectionError as e:
        raise HTTPException(status_code=502, detail=f"Error conectando a la URL: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en scraping: {str(e)}")


@router.get(
    "/sources",
    summary="Fuentes de scraping sugeridas",
    description="Retorna una lista de fuentes públicas sugeridas para scraping de requisitos.",
)
async def get_suggested_sources():
    """Retorna fuentes públicas conocidas para scraping de requisitos."""
    return {
        "sources": [
            {
                "name": "ReqView - ISO/IEC/IEEE 29148 SRS Example",
                "url": "https://www.reqview.com/doc/iso-iec-ieee-29148-srs-example",
                "description": "Ejemplo de SRS basado en ISO 29148 de ReqView.",
            },
            {
                "name": "ReqView - ISO/IEC/IEEE 29148 SyRS Example",
                "url": "https://www.reqview.com/doc/iso-iec-ieee-29148-syrs-example",
                "description": "Ejemplo de SyRS (System Requirements) basado en ISO 29148.",
            },
            {
                "name": "PURE Dataset (Zenodo)",
                "url": "https://zenodo.org/records/1414117",
                "description": (
                    "PUblic REquirements dataset: 79 documentos de requisitos públicos "
                    "con ~34,268 sentencias. Referencia académica en RE."
                ),
            },
        ],
        "tip": (
            "Puedes usar POST /scrape con cualquier URL. "
            "El sistema detecta automáticamente texto que parece un requisito. "
            "Usa css_selector si necesitas precisión."
        ),
    }
