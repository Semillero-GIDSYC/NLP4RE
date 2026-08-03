from fastapi import APIRouter, HTTPException, Query, WebSocket, WebSocketDisconnect

from ia_service.schemas.schemas import (
    AnalyzeRequest,
    AnalyzeResponse,
    RequirementResponse,
    RequirementListResponse,
    DocumentResponse,
    DocumentListResponse,
)
from ia_service.services.retriever.retriever_service import retrieve_context
from ia_service.services.evaluation.evaluation_service import evaluate_requirement
from ia_service.services.feedback.feedback_service import generate_feedback

router = APIRouter(tags=["Análisis"])


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
    Pipeline completo de análisis:
    1. Recuperar contexto normativo (retriever/pgvector).
    2. Evaluar requisito con LLM (5 dimensiones).
    3. Generar feedback y versión mejorada con LLM.
    """
    try:
        context_docs = retrieve_context(request.text, k=3)
        context_texts = [doc.page_content for doc in context_docs]

        evaluation = evaluate_requirement(
            requirement_text=request.text,
            context_docs=context_docs,
        )

        feedback = generate_feedback(
            requirement_text=request.text,
            evaluation=evaluation,
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
        
        try:
            import json
            js = json.loads(data)
            if isinstance(js, dict) and "text" in js:
                requirement_text = js["text"].strip()
        except Exception:
            pass

        if not requirement_text:
            await websocket.send_json({"type": "error", "content": "Requisito vacio"})
            await websocket.close()
            return

        # 1. Retrieve Context
        await websocket.send_json({"type": "status", "content": "Recuperando contexto normativo..."})
        context_docs = retrieve_context(requirement_text, k=3)
        context_texts = [doc.page_content for doc in context_docs]
        
        await websocket.send_json({
            "type": "context",
            "content": context_texts
        })

        # 2. Setup LLM and Evaluation Chain
        from ia_service.services.evaluation.evaluation_service import (
            _get_llm,
            _build_evaluation_prompt,
            _format_context,
            _format_db_examples
        )
        from ia_service.services.retriever.retriever_service import retrieve_examples
        from langchain_core.output_parsers import StrOutputParser

        await websocket.send_json({"type": "status", "content": "Generando evaluacion (en tiempo real)..."})
        
        examples_list = retrieve_examples(requirement_text, k=4)
        examples_str = _format_db_examples(examples_list)
        
        llm = _get_llm()
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

