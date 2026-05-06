import json

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from app.core.config import get_settings


def _get_llm():
    """
    Retorna el LLM según el proveedor configurado.
    """
    settings = get_settings()

    if settings.LLM_PROVIDER == "openai":
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(
            model=settings.OPENAI_MODEL,
            temperature=settings.LLM_TEMPERATURE,
            openai_api_key=settings.OPENAI_API_KEY,
        )
    else:
        from langchain_google_genai import ChatGoogleGenerativeAI

        return ChatGoogleGenerativeAI(
            model=settings.GEMINI_MODEL,
            temperature=settings.LLM_TEMPERATURE,
            google_api_key=settings.GOOGLE_API_KEY,
        )


def _build_feedback_prompt() -> ChatPromptTemplate:
    """
    Construye el prompt de feedback basado en la evaluación del requisito.
    """
    template = """Eres un experto en Ingeniería de Requisitos con experiencia en ISO 29148.
Basándote en la evaluación proporcionada, genera feedback concreto y accionable.

Requerimiento original:
{requirement}

Evaluación previa (JSON):
{evaluation}

INSTRUCCIONES:
1. Analiza cada dimensión evaluada y las puntuaciones.
2. Genera sugerencias específicas y concretas para mejorar el requisito.
3. Escribe una versión mejorada y optimizada del requisito.

Responde EXACTAMENTE con un JSON válido con esta estructura:
{{
  "suggestions": [
    "<sugerencia específica 1>",
    "<sugerencia específica 2>",
    "<sugerencia específica 3>"
  ],
  "improved_requirement": "<versión reescrita y mejorada del requisito>"
}}

REGLAS:
- Las sugerencias deben ser concretas y accionables (no genéricas).
- Para cada dimensión con score < 2, incluye al menos una sugerencia.
- El requisito mejorado debe intentar lograr score 2 en todas las dimensiones.
- Si el requisito original tiene todos los scores en 2, sugiere mejoras menores o confirma su calidad.
- Responde SOLO con el JSON, sin texto adicional, sin markdown, sin bloques de código.
- Escribe en español."""

    return ChatPromptTemplate.from_template(template)


def generate_feedback(
    requirement_text: str,
    evaluation: dict,
) -> dict:
    """
    Genera feedback de mejora para un requisito basándose en su evaluación.

    Args:
        requirement_text: Texto original del requisito.
        evaluation: Resultado de la evaluación (dict con 5 dimensiones).

    Returns:
        Diccionario con 'suggestions' (list[str]) e 'improved_requirement' (str).
    """

    llm = _get_llm()
    prompt = _build_feedback_prompt()

    # Ejecutar cadena LLM
    chain = prompt | llm | StrOutputParser()
    raw_response = chain.invoke({
        "requirement": requirement_text,
        "evaluation": json.dumps(evaluation, ensure_ascii=False, indent=2),
    })

    # Parsear JSON de la respuesta
    try:
        cleaned = raw_response.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("\n", 1)[1] if "\n" in cleaned else cleaned
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
            cleaned = cleaned.strip()

        feedback = json.loads(cleaned)

        # Validar estructura
        if "suggestions" not in feedback:
            feedback["suggestions"] = ["No se generaron sugerencias específicas."]

        if "improved_requirement" not in feedback:
            feedback["improved_requirement"] = requirement_text

        # Asegurar que suggestions es una lista
        if isinstance(feedback["suggestions"], str):
            feedback["suggestions"] = [feedback["suggestions"]]

        return feedback

    except json.JSONDecodeError as e:

        # Fallback: retornar el texto crudo como sugerencia
        return {
            "suggestions": [
                "Error generando feedback estructurado. Respuesta del LLM:",
                raw_response[:500],
            ],
            "improved_requirement": requirement_text,
        }
