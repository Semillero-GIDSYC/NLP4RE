from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/export", tags=["Exportación"])


@router.get(
    "/dataset",
    summary="Exportar todos los requisitos",
    description=(
        "Exporta todos los requisitos almacenados como JSON. "
        "Incluye texto, fuente, metadata y timestamp. No incluye embeddings."
    ),
)
async def export_dataset():
    """Exporta todos los requisitos sin embeddings."""
    try:
        from app.db.session import SessionLocal
        from app.db.models import Requirement

        db = SessionLocal()
        try:
            requirements = db.query(Requirement).order_by(Requirement.created_at.desc()).all()

            data = [
                {
                    "id": str(r.id),
                    "text": r.text,
                    "source": r.source,
                    "source_name": r.source_name,
                    "metadata": r.metadata_,
                    "created_at": r.created_at.isoformat() if r.created_at else None,
                }
                for r in requirements
            ]


            return JSONResponse(
                content={
                    "total": len(data),
                    "requirements": data,
                },
                headers={
                    "Content-Disposition": "attachment; filename=requirements_dataset.json"
                },
            )
        finally:
            db.close()

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.get(
    "/chunks",
    summary="Exportar chunks de documentos",
    description=(
        "Exporta todos los chunks almacenados en pgvector como JSON. "
        "Útil para ver cómo se seccionaron los documentos. No incluye embeddings."
    ),
)
async def export_chunks():
    """Exporta todos los chunks de documentos sin embeddings."""
    try:
        from app.db.session import SessionLocal
        from app.db.models import Document

        db = SessionLocal()
        try:
            documents = db.query(Document).order_by(Document.created_at.desc()).all()

            data = [
                {
                    "id": str(d.id),
                    "content": d.content,
                    "source": d.source,
                    "page": d.page,
                    "chunk_index": d.chunk_index,
                    "metadata": d.metadata_,
                    "created_at": d.created_at.isoformat() if d.created_at else None,
                }
                for d in documents
            ]


            return JSONResponse(
                content={
                    "total": len(data),
                    "chunks": data,
                },
                headers={
                    "Content-Disposition": "attachment; filename=chunks_export.json"
                },
            )
        finally:
            db.close()

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
