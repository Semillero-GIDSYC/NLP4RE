import json
import os
from pathlib import Path

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.documents import Document

from app.core.config import get_settings



def _get_llm():
    """
    Retorna el LLM según el proveedor configurado.

    Returns:
        Instancia de LLM (Gemini o OpenAI).
    """
    settings = get_settings()

    if settings.GENERATION_LLM_PROVIDER == "openai":
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(
            model=settings.OPENAI_MODEL,
            temperature=settings.LLM_TEMPERATURE,
            openai_api_key=settings.OPENAI_API_KEY,
        )
    elif settings.GENERATION_LLM_PROVIDER == "local":
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(
            model=settings.LOCAL_MODEL,
            temperature=settings.LLM_TEMPERATURE,
            openai_api_base=settings.LOCAL_MODELS_API,
            openai_api_key="lm-studio",  # LM Studio doesn't strictly need a real key but expects something
        )
    else:
        from langchain_google_genai import ChatGoogleGenerativeAI

        return ChatGoogleGenerativeAI(
            model=settings.GEMINI_MODEL,
            temperature=settings.LLM_TEMPERATURE,
            google_api_key=settings.GOOGLE_API_KEY,
        )


def _load_rules() -> str:
    """Carga y formatea las reglas de evaluación desde rules.json."""
    settings = get_settings()
    rules_path = Path(settings.DOCS_DIR) / "rules.json"

    if not rules_path.exists():
        return "No se encontraron reglas de evaluación."

    with open(rules_path, "r", encoding="utf-8") as f:
        rules_data = json.load(f)

    rules_str = ""
    for r in rules_data:
        rules_str += f"- {r['typeC']}: {r['description']}\n"
        for level, desc in r["criterion"].items():
            rules_str += f"  * Nivel {level}: {desc}\n"

    return rules_str


def _load_examples() -> str:
    """Carga y formatea los ejemplos de evaluación desde examples.json."""
    settings = get_settings()
    examples_path = Path(settings.DOCS_DIR) / "examples.json"

    if not examples_path.exists():
        return "No se encontraron ejemplos."

    with open(examples_path, "r", encoding="utf-8") as f:
        examples_data = json.load(f)

    examples_str = ""
    for idx, ex in enumerate(examples_data):
        examples_str += f"Ejemplo {idx + 1}:\nRequerimiento: {ex['text']}\nEvaluación:\n"
        for tag, score in ex["tags"].items():
            explanation = ex["explanations"].get(tag, "OK")
            examples_str += f" - {tag}: {score} ({explanation})\n"
        examples_str += "\n"

    return examples_str


def _build_evaluation_prompt() -> ChatPromptTemplate:
    """
    Construye el prompt de evaluación con reglas, ejemplos y contexto.
    Usa el mismo enfoque probado en rag.ipynb pero con output JSON estructurado.
    """
    rules_str = _load_rules()
    examples_str = _load_examples()

    template = f"""Eres un experto en Ingeniería de Requisitos.
Se te proporcionará contexto normativo basado en la ISO 29148.
Tu tarea es evaluar un requerimiento según las reglas y ejemplos proporcionados.

Reglas de evaluación:
{rules_str}

Ejemplos de referencia:
{examples_str}

Contexto normativo recuperado de la ISO:
{{context}}

Requerimiento a evaluar:
{{requirement}}

INSTRUCCIONES:
Analiza el requerimiento y devuelve EXACTAMENTE un JSON válido con la siguiente estructura:
{{{{
  "VERIFIABILITY": {{{{"score": <0|1|2>, "explanation": "<explicación concisa>"}}}},
  "ATOMICITY": {{{{"score": <0|1|2>, "explanation": "<explicación concisa>"}}}},
  "AMBIGUITY": {{{{"score": <0|1|2>, "explanation": "<explicación concisa>"}}}},
  "COMPLETENESS": {{{{"score": <0|1|2>, "explanation": "<explicación concisa>"}}}},
  "TRACEABLE": {{{{"score": <0|1|2>, "explanation": "<explicación concisa>"}}}}
}}}}

IMPORTANTE:
- Responde SOLO con el JSON, sin texto adicional, sin markdown, sin bloques de código.
- Cada score es un entero: 0, 1 o 2.
- Cada explanation es una cadena de texto concisa en español."""

    return ChatPromptTemplate.from_template(template)


def _format_context(docs: list[Document]) -> str:
    """Formatea los documentos de contexto como string."""
    if not docs:
        return "No se encontró contexto normativo relevante."

    context_parts = []
    for i, doc in enumerate(docs):
        source = doc.metadata.get("source_file", doc.metadata.get("source", "desconocido"))
        context_parts.append(f"[Contexto {i + 1} - {source}]\n{doc.page_content}")

    return "\n\n".join(context_parts)


def evaluate_requirement(
    requirement_text: str,
    context_docs: list[Document],
) -> dict:
    """
    Evalúa un requisito usando LLM con contexto del retriever.

    Args:
        requirement_text: Texto del requisito a evaluar.
        context_docs: Documentos de contexto del retriever.

    Returns:
        Diccionario con evaluación estructurada por dimensión.
    """

    llm = _get_llm()
    prompt = _build_evaluation_prompt()
    context_str = _format_context(context_docs)

    # Ejecutar cadena LLM
    chain = prompt | llm | StrOutputParser()
    raw_response = chain.invoke({
        "context": context_str,
        "requirement": requirement_text,
    })


    # Parsear JSON de la respuesta
    try:
        # Limpiar posibles artifacts de markdown
        cleaned = raw_response.strip()
        if cleaned.startswith("```"):
            # Remover bloques de código markdown
            cleaned = cleaned.split("\n", 1)[1] if "\n" in cleaned else cleaned
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
            cleaned = cleaned.strip()

        evaluation = json.loads(cleaned)

        # Validar estructura
        required_keys = {"VERIFIABILITY", "ATOMICITY", "AMBIGUITY", "COMPLETENESS", "TRACEABLE"}
        if not required_keys.issubset(evaluation.keys()):
            missing = required_keys - evaluation.keys()
            # Agregar dimensiones faltantes con score 0
            for key in missing:
                evaluation[key] = {"score": 0, "explanation": "No evaluado por el LLM."}

        return evaluation

    except json.JSONDecodeError as e:

        # Fallback: retornar evaluación vacía
        return {
            dim: {"score": 0, "explanation": "Error en la evaluación automática. Revisar manualmente."}
            for dim in ["VERIFIABILITY", "ATOMICITY", "AMBIGUITY", "COMPLETENESS", "TRACEABLE"]
        }
