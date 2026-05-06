from fastapi import APIRouter, UploadFile, File, HTTPException

from app.schemas.schemas import UploadResponse
from app.services.ingestion.pdf_service import extract_from_pdf, save_uploaded_pdf
from app.services.cleaning.cleaning_service import clean_pipeline
from app.services.retriever.retriever_service import index_documents, index_requirements


router = APIRouter(prefix="/upload", tags=["Upload"])


@router.post(
    "/pdf",
    response_model=UploadResponse,
    summary="Subir y procesar un PDF",
    description=(
        "Sube un archivo PDF, extrae texto, lo divide en chunks, "
        "limpia el contenido e indexa todo en pgvector."
    ),
)
async def upload_pdf(
    file: UploadFile = File(..., description="Archivo PDF a procesar"),
):
    """
    Pipeline completo de ingesta de PDF:
    1. Guardar archivo temporalmente.
    2. Extraer chunks con PDFPlumber.
    3. Indexar chunks en pgvector (colección ISO).
    4. Limpiar y segmentar requisitos.
    5. Indexar requisitos limpios en pgvector (colección requirements).
    """

    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="El archivo debe ser un PDF.")

    if file.size and file.size > 50 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="El archivo es demasiado grande (máx. 50MB).")

    try:
        # 1. Guardar archivo
        content = await file.read()
        file_path = await save_uploaded_pdf(content, file.filename)

        # 2. Extraer chunks
        chunks = extract_from_pdf(file_path)

        if not chunks:
            raise HTTPException(
                status_code=422,
                detail="No se pudo extraer texto del PDF. Verifica que no esté vacío o protegido.",
            )

        # 3. Indexar chunks crudos (contexto para retriever)
        chunks_indexed = index_documents(chunks, collection_name="iso_standards")

        # 4. Limpiar y segmentar requisitos
        raw_texts = [chunk.page_content for chunk in chunks]
        clean_reqs = clean_pipeline(raw_texts)

        # 5. Indexar requisitos limpios
        reqs_indexed = index_requirements(
            texts=clean_reqs,
            source="pdf",
            source_name=file.filename,
        )

        return UploadResponse(
            filename=file.filename,
            chunks_extracted=len(chunks),
            requirements_indexed=reqs_indexed,
            message=(
                f"PDF procesado exitosamente. "
                f"Se extrajeron {len(chunks)} chunks y se indexaron "
                f"{reqs_indexed} requisitos."
            ),
        )

    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error procesando PDF: {str(e)}")
