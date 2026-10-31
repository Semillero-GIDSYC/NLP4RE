from fastapi import APIRouter, HTTPException, Query, WebSocket, WebSocketDisconnect

from ia_service.schemas.schemas import (
    AnalyzeRequest,
    AnalyzeResponse,
    RequirementResponse,
    RequirementListResponse,
    DocumentResponse,
    DocumentListResponse,
    ModelInfo,
)
from ia_service.services.retriever.retriever_service import retrieve_context
from ia_service.services.evaluation.evaluation_service import evaluate_requirement
from ia_service.services.feedback.feedback_service import generate_feedback
from ia_service.core.llm import get_llm
from ia_service.core.config import get_settings

router = APIRouter(tags=["Análisis"])


@router.get(
    "/models",
    response_model=list[ModelInfo],
    summary="Listar modelos de LLM disponibles",
    description="Retorna la lista de modelos de texto soportados (locales y nube: Gemini, OpenAI, Anthropic).",
)
async def list_available_models():
    """Retorna los modelos disponibles agrupados por familias."""
    settings = get_settings()
    models = [
        # Familia Google Gemini
        ModelInfo(
            id="gemini-3.5-flash-lite",
            name="Gemini 3.5 Flash Lite",
            provider="gemini",
            description="Google - Rápido, preciso y multimodal (Recomendado)",
            is_local=False,
            requires_key=True,
        ),
        ModelInfo(
            id="gemini-2.5-pro",
            name="Gemini 2.5 Pro",
            provider="gemini",
            description="Google - Mayor profundidad analítica",
            is_local=False,
            requires_key=True,
        ),
        ModelInfo(
            id="gemini-1.5-flash",
            name="Gemini 1.5 Flash",
            provider="gemini",
            description="Google - Balance económico y veloz",
            is_local=False,
            requires_key=True,
        ),
        # Familia OpenAI
        ModelInfo(
            id="gpt-4o-mini",
            name="GPT-4o Mini",
            provider="openai",
            description="OpenAI - Ligero, veloz y económico",
            is_local=False,
            requires_key=True,
        ),
        ModelInfo(
            id="gpt-4o",
            name="GPT-4o",
            provider="openai",
            description="OpenAI - Modelo insignia multimodal de alta gama",
            is_local=False,
            requires_key=True,
        ),
        ModelInfo(
            id="gpt-3.5-turbo",
            name="GPT-3.5 Turbo",
            provider="openai",
            description="OpenAI - Estándar clásico eficiente",
            is_local=False,
            requires_key=True,
        ),
        # Familia Anthropic
        ModelInfo(
            id="claude-3-5-sonnet-20241022",
            name="Claude 3.5 Sonnet",
            provider="anthropic",
            description="Anthropic - Excelente razonamiento y calidad de código",
            is_local=False,
            requires_key=True,
        ),
        ModelInfo(
            id="claude-3-5-haiku-20241022",
            name="Claude 3.5 Haiku",
            provider="anthropic",
            description="Anthropic - Ultrarrápido y conciso",
            is_local=False,
            requires_key=True,
        ),
    ]

    # Intentar descubrir modelos de servidor local (LM Studio u Ollama)
    import httpx
    local_urls = [
        settings.LOCAL_MODELS_API,
        "http://host.docker.internal:1234/v1",
        "http://localhost:1234/v1",
    ]
    local_detected = False
    for b_url in local_urls:
        if not b_url:
            continue
        try:
            url_clean = b_url if b_url.endswith("/v1") or b_url.endswith("/v1/") else f"{b_url.rstrip('/')}/v1"
            async with httpx.AsyncClient(timeout=1.0) as client:
                res = await client.get(f"{url_clean.rstrip('/')}/models")
                if res.status_code == 200:
                    data = res.json()
                    for item in data.get("data", []):
                        m_id = item.get("id")
                        if m_id:
                            models.insert(0, ModelInfo(
                                id=m_id,
                                name=f"Local: {m_id}",
                                provider="local",
                                description="Modelo local activo en LM Studio / Ollama (Sin Internet)",
                                is_local=True,
                                requires_key=False,
                            ))
                            local_detected = True
                    if local_detected:
                        break
        except Exception:
            pass

    if not local_detected:
        models.insert(0, ModelInfo(
            id=settings.LOCAL_MODEL or "google/gemma-3-4b",
            name=f"Local: {settings.LOCAL_MODEL or 'google/gemma-3-4b'}",
            provider="local",
            description="Modelo local (LM Studio / Ollama en puerto 1234)",
            is_local=True,
            requires_key=False,
        ))

    return models


@router.post(
    "/analyze",
    response_model=AnalyzeResponse,
    summary="Analizar un requisito",
    description=(
        "Evalúa un requisito de software en 5 dimensiones (ISO 29148): "
        "verificabilidad, atomicidad, ambigüedad, completitud y trazabilidad. "
        "Genera sugerencias de mejora y una versión optimizada del requisito."
    ),
)
async def analyze_requirement(request: AnalyzeRequest):
    """
    Pipeline completo de análisis con soporte multi-modelo y clave API personalizada.
    """
    try:
        context_docs = retrieve_context(request.text, k=3)
        context_texts = [doc.page_content for doc in context_docs]

        evaluation = evaluate_requirement(
            requirement_text=request.text,
            context_docs=context_docs,
            provider=request.provider,
            model=request.model,
            api_key=request.api_key,
            base_url=request.base_url,
        )

        feedback = generate_feedback(
            requirement_text=request.text,
            evaluation=evaluation,
            provider=request.provider,
            model=request.model,
            api_key=request.api_key,
            base_url=request.base_url,
        )

        return AnalyzeResponse(
            original_text=request.text,
            evaluation=evaluation,
            feedback=feedback,
            context_used=context_texts,
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error analizando el requisito: {str(e)}",
        )


@router.get(
    "/requirements",
    response_model=RequirementListResponse,
    summary="Listar requisitos almacenados",
    description="Retorna los requisitos almacenados en la base de datos, con paginación.",
)
async def list_requirements(
    page: int = Query(default=1, ge=1, description="Número de página"),
    page_size: int = Query(default=20, ge=1, le=100, description="Requisitos por página"),
):
    """Lista paginada de requisitos del vector store."""
    try:
        from ia_service.db.session import SessionLocal
        from ia_service.db.models import Requirement
        from sqlalchemy import func

        db = SessionLocal()
        try:
            # Total de requisitos
            total = db.query(func.count(Requirement.id)).scalar() or 0

            # Paginación
            offset = (page - 1) * page_size
            requirements = (
                db.query(Requirement)
                .order_by(Requirement.created_at.desc())
                .offset(offset)
                .limit(page_size)
                .all()
            )

            return RequirementListResponse(
                total=total,
                page=page,
                page_size=page_size,
                requirements=[
                    RequirementResponse(
                        id=r.id,
                        text=r.text,
                        source=r.source,
                        source_name=r.source_name,
                        metadata=r.metadata_,
                        created_at=r.created_at,
                    )
                    for r in requirements
                ],
            )
        finally:
            db.close()

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.get(
    "/documents",
    response_model=DocumentListResponse,
    summary="Listar documentos (chunks) almacenados",
    description="Retorna los chunks de documentos almacenados en la base de datos, con paginación.",
)
async def list_documents(
    page: int = Query(default=1, ge=1, description="Número de página"),
    page_size: int = Query(default=20, ge=1, le=100, description="Documentos por página"),
):
    """Lista paginada de chunks de documentos del vector store."""
    try:
        from ia_service.db.session import SessionLocal
        from ia_service.db.models import Document as DBDocument
        from sqlalchemy import func

        db = SessionLocal()
        try:
            # Total de documentos
            total = db.query(func.count(DBDocument.id)).scalar() or 0

            # Paginación
            offset = (page - 1) * page_size
            documents = (
                db.query(DBDocument)
                .order_by(DBDocument.created_at.desc())
                .offset(offset)
                .limit(page_size)
                .all()
            )

            return DocumentListResponse(
                total=total,
                page=page,
                page_size=page_size,
                documents=[
                    DocumentResponse(
                        id=d.id,
                        content=d.content,
                        source=d.source,
                        page=d.page,
                        chunk_index=d.chunk_index,
                        metadata=d.metadata_,
                        created_at=d.created_at,
                    )
                    for d in documents
                ],
            )
        finally:
            db.close()

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.websocket("/ws/analyze")
async def websocket_analyze(websocket: WebSocket):
    await websocket.accept()
    try:
        data = await websocket.receive_text()
        requirement_text = data.strip()
        provider = None
        model = None
        api_key = None
        base_url = None
        
        try:
            import json
            js = json.loads(data)
            if isinstance(js, dict):
                requirement_text = js.get("text", "").strip()
                provider = js.get("provider")
                model = js.get("model")
                api_key = js.get("apiKey") or js.get("api_key")
                base_url = js.get("localUrl") or js.get("base_url")
        except Exception:
            pass

        if not requirement_text:
            await websocket.send_json({"type": "error", "content": "Requisito vacío"})
            await websocket.close()
            return

        # 1. Retrieve Context
        await websocket.send_json({"type": "status", "content": "Recuperando contexto normativo ISO 29148..."})
        context_docs = retrieve_context(requirement_text, k=3)
        context_texts = [doc.page_content for doc in context_docs]
        
        await websocket.send_json({
            "type": "context",
            "content": context_texts
        })

        # 2. Setup LLM and Evaluation Chain
        from ia_service.services.evaluation.evaluation_service import (
            _build_evaluation_prompt,
            _format_context,
            _format_db_examples
        )
        from ia_service.services.retriever.retriever_service import retrieve_examples
        from langchain_core.output_parsers import StrOutputParser

        await websocket.send_json({"type": "status", "content": "Evaluando calidad del requisito (en tiempo real)..."})
        
        examples_list = retrieve_examples(requirement_text, k=4)
        examples_str = _format_db_examples(examples_list)
        
        llm = get_llm(provider=provider, model=model, api_key=api_key, base_url=base_url)
        eval_prompt = _build_evaluation_prompt(examples_str)
        context_str = _format_context(context_docs)
        
        eval_chain = eval_prompt | llm | StrOutputParser()
        
        raw_eval_response = ""
        async for chunk in eval_chain.astream({
            "context": context_str,
            "requirement": requirement_text
        }):
            raw_eval_response += chunk
            await websocket.send_json({"type": "evaluation_chunk", "content": chunk})

        # Parse evaluation JSON
        import json
        cleaned_eval = raw_eval_response.strip()
        if cleaned_eval.startswith("```"):
            cleaned_eval = cleaned_eval.split("\n", 1)[1] if "\n" in cleaned_eval else cleaned_eval
            if cleaned_eval.endswith("```"):
                cleaned_eval = cleaned_eval[:-3]
            cleaned_eval = cleaned_eval.strip()

        try:
            evaluation = json.loads(cleaned_eval)
        except Exception:
            evaluation = {
                dim: {"score": 0, "explanation": "Error de parseo de JSON en streaming. Usando fallback."}
                for dim in ["VERIFIABILITY", "ATOMICITY", "AMBIGUITY", "COMPLETENESS", "TRACEABLE"]
            }

        required_keys = {"VERIFIABILITY", "ATOMICITY", "AMBIGUITY", "COMPLETENESS", "TRACEABLE"}
        if not required_keys.issubset(evaluation.keys()):
            for key in (required_keys - evaluation.keys()):
                evaluation[key] = {"score": 0, "explanation": "No evaluado."}

        await websocket.send_json({"type": "evaluation_result", "content": evaluation})

        # 3. Setup Feedback Chain
        await websocket.send_json({"type": "status", "content": "Generando sugerencias y version mejorada..."})
        
        from ia_service.services.feedback.feedback_service import _build_feedback_prompt
        feedback_prompt = _build_feedback_prompt()
        feedback_chain = feedback_prompt | llm | StrOutputParser()
        
        raw_feedback_response = ""
        async for chunk in feedback_chain.astream({
            "requirement": requirement_text,
            "evaluation": json.dumps(evaluation, ensure_ascii=False, indent=2)
        }):
            raw_feedback_response += chunk
            await websocket.send_json({"type": "feedback_chunk", "content": chunk})

        # Parse feedback JSON
        cleaned_feedback = raw_feedback_response.strip()
        if cleaned_feedback.startswith("```"):
            cleaned_feedback = cleaned_feedback.split("\n", 1)[1] if "\n" in cleaned_feedback else cleaned_feedback
            if cleaned_feedback.endswith("```"):
                cleaned_feedback = cleaned_feedback[:-3]
            cleaned_feedback = cleaned_feedback.strip()

        try:
            feedback = json.loads(cleaned_feedback)
        except Exception:
            feedback = {
                "suggestions": ["Error de parseo del feedback en streaming."],
                "improved_requirement": requirement_text
            }

        if "suggestions" not in feedback:
            feedback["suggestions"] = ["Sugerencias no disponibles."]
        if "improved_requirement" not in feedback:
            feedback["improved_requirement"] = requirement_text

        await websocket.send_json({"type": "feedback_result", "content": feedback})
        await websocket.send_json({"type": "done"})

    except WebSocketDisconnect:
        pass
    except Exception as e:
        try:
            await websocket.send_json({"type": "error", "content": f"Error en procesamiento: {str(e)}"})
        except Exception:
            pass
    finally:
        try:
            await websocket.close()
        except Exception:
            pass

