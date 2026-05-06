import os
import tempfile
from pathlib import Path

from langchain_community.document_loaders import PDFPlumberLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

def extract_from_pdf(
    file_path: str,
    chunk_size: int = 1000,
    chunk_overlap: int = 100,
) -> list[Document]:
    """
    Extrae texto de un PDF y lo divide en chunks.

    Args:
        file_path: Ruta al archivo PDF.
        chunk_size: Tamaño máximo de cada chunk en caracteres.
        chunk_overlap: Superposición entre chunks consecutivos.

    Returns:
        Lista de Documents de LangChain con page_content y metadata.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Archivo PDF no encontrado: {file_path}")

    # Cargar PDF con PDFPlumber (mejor para tablas y layout complejo)
    loader = PDFPlumberLoader(file_path)
    documents = loader.load()

    # Dividir en chunks
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    chunks = text_splitter.split_documents(documents)

    # Enriquecer metadata
    filename = Path(file_path).name
    for i, chunk in enumerate(chunks):
        chunk.metadata["source_file"] = filename
        chunk.metadata["chunk_index"] = i

    return chunks


async def save_uploaded_pdf(file_content: bytes, filename: str) -> str:
    """
    Guarda un archivo PDF subido en un directorio temporal.

    Args:
        file_content: Contenido binario del PDF.
        filename: Nombre original del archivo.

    Returns:
        Ruta al archivo guardado.
    """
    # Crear directorio para uploads si no existe
    upload_dir = Path("/tmp/nlp4re_uploads")
    upload_dir.mkdir(parents=True, exist_ok=True)

    file_path = upload_dir / filename
    with open(file_path, "wb") as f:
        f.write(file_content)
    return str(file_path)
