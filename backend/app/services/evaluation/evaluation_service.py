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


def _format_db_examples(examples: list[dict]) -> str:
    """Formatea los requerimientos de ejemplo recuperados de la DB."""
    if not examples:
        return "No se encontraron ejemplos de requerimientos en la base de datos."

    examples_str = ""
    for idx, ex in enumerate(examples):
        text = ex["text"]
        meta = ex["metadata"] or {}
        tag_str = meta.get("tags", "")

        # Parse tags like "VERIFIABILITY:1;ATOMICITY:0;AMBIGUITY:1;COMPLETENESS:1;TRACEABLE:1"
        tags = {}
        if isinstance(tag_str, str):
            for pair in tag_str.split(';'):
                if ':' in pair:
                    k, v = pair.split(':')
                    try:
                        tags[k.strip().upper()] = int(v.strip())
                    except ValueError:
                        pass

        examples_str += f"Ejemplo {idx + 1}:\nRequerimiento: {text}\nEvaluación:\n"
        for dim in ["VERIFIABILITY", "ATOMICITY", "AMBIGUITY", "COMPLETENESS", "TRACEABLE"]:
            score = tags.get(dim, 0)
            examples_str += f" - {dim}: {score}\n"
        examples_str += "\n"

    return examples_str


def _build_evaluation_prompt(examples_str: str) -> ChatPromptTemplate:
    """
    Construye el prompt de evaluación con reglas del sistema (ISO 29148),
    ejemplos recuperados de la DB y contexto normativo.
    """
    # Definición estática de las reglas basadas en la ISO 29148
    rules_str = """1. VERIFIABILITY (Verificabilidad): Mide si existe un proceso finito y costo-efectivo para comprobar que el sistema cumple el requisito. Evitar términos subjetivos como 'rápido', 'fácil', 'seguro'.
   - Nivel 0: El requisito usa términos subjetivos o no medibles sin ninguna métrica. No se puede probar.
   - Nivel 1: El requisito intenta incluir una métrica pero es incompleta, imprecisa o carece de contexto.
   - Nivel 2: El requisito incluye una métrica concreta, medible y objetiva bajo condiciones de prueba claras.

2. ATOMICITY (Atomicidad): Mide si el requisito expresa una única idea o función. No debe contener conjunciones que unan dos o más requisitos independientes.
   - Nivel 0: Expresa dos o más ideas independientes unidas por conjunciones como 'y', 'o', 'además'.
   - Nivel 1: Es mayormente atómico pero contiene una idea secundaria que podría separarse.
   - Nivel 2: Expresa exactamente una única idea y no puede dividirse más.

3. CLARITY / UNAMBIGUITY (Ambigüedad/Claridad): Mide si el requisito tiene una sola interpretación posible para todos los interesados.
   - Nivel 0: Usa términos sumamente ambiguos o vagos con múltiples interpretaciones. (Altamente Ambiguo - Calidad Mala).
   - Nivel 1: Es mayormente claro pero tiene al menos un término que podría malinterpretarse.
   - Nivel 2: Tiene una única interpretación posible. Todos los términos son precisos y el contexto está definido. (Libre de Ambigüedades - Calidad Óptima).

4. COMPLETENESS (Completitud): Mide si contiene toda la información necesaria para implementarlo y verificarlo (condición bajo la que aplica, acción del sistema y resultado esperado).
   - Nivel 0: Faltan dos o más elementos clave (condición, acción o resultado esperado).
   - Nivel 1: Incluye parte de la información pero carece de un elemento clave (por ejemplo, la condición de activación).
   - Nivel 2: Declara claramente la condición, la acción del sistema y el resultado esperado.

5. TRACEABLE (Trazabilidad): Mide si el requisito se puede vincular a su origen (necesidad de un stakeholder, caso de uso, rol, regla de negocio).
   - Nivel 0: No hace referencia a ningún origen, stakeholder, rol, caso de uso (UC) o regla de negocio.
   - Nivel 1: Referencia parcial o incompleta a su origen.
   - Nivel 2: Referencia de manera clara y explícita su origen (por ejemplo: "El administrador...", "Basado en el caso de uso UC-04...")."""

    template = f"""Eres un experto en Ingeniería de Requisitos.
Se te proporcionará contexto normativo basado en la ISO 29148.
Tu tarea es evaluar un requerimiento según las reglas y ejemplos de referencia proporcionados.

Reglas de evaluación (ISO 29148):
{rules_str}

Ejemplos de referencia recuperados dinámicamente de la base de datos (con sus puntajes reales del dataset):
{examples_str}

Contexto normativo recuperado de la ISO:
{{context}}

Requerimiento a evaluar:
{{requirement}}

INSTRUCCIONES DE PUNTUACIÓN GENERALES:
1. Para todas las dimensiones, incluyendo "AMBIGUITY" (Claridad) y "TRACEABLE" (Trazabilidad):
   - Un puntaje de 0 es el PEOR caso (defecto completo: altamente ambiguo / nula trazabilidad / no verificable / no atómico).
   - Un puntaje de 1 es el caso PARCIAL o intermedio.
   - Un puntaje de 2 es el MEJOR caso (calidad óptima: nula ambigüedad o total claridad / excelente trazabilidad / totalmente verificable / totalmente atómico).
2. Para la dimensión "AMBIGUITY" (Claridad / No ambigüedad):
   - Mide la CLARIDAD del requerimiento. Un requerimiento sin ambigüedad debe evaluarse con puntaje 2 (Excelente calidad).
   - ¡CUIDADO! No asignes 0 para significar "cero ambigüedades". 0 significa "Altamente Ambiguo" (Malo). Para indicar "Sin ambigüedad" debes asignar 2.
3. Para la dimensión "TRACEABLE":
   - Mide si hay referencia explícita al origen.
   - REGLA ESTRICTA: Si el requerimiento no menciona explícitamente a un actor, stakeholder, rol, caso de uso (UC) o regla de negocio de origen, el puntaje de TRACEABLE debe ser 0. No alucines trazabilidad implícita basada únicamente en que el requerimiento parece correcto o alineado con la seguridad. Debe haber mención textual y explícita del actor o stakeholder.

INSTRUCCIONES DE SALIDA:
Analiza el requerimiento y devuelve EXACTAMENTE un JSON válido con la siguiente estructura (conservando la clave "AMBIGUITY" para compatibilidad con la base de datos):
{{{{
  "VERIFIABILITY": {{{{"score": <0|1|2>, "explanation": "<explicación concisa en español>"}}}},
  "ATOMICITY": {{{{"score": <0|1|2>, "explanation": "<explicación concisa en español>"}}}},
  "AMBIGUITY": {{{{"score": <0|1|2>, "explanation": "<explicación concisa en español de la claridad o falta de ambigüedad del requisito>"}}}},
  "COMPLETENESS": {{{{"score": <0|1|2>, "explanation": "<explicación concisa en español>"}}}},
  "TRACEABLE": {{{{"score": <0|1|2>, "explanation": "<explicación concisa en español>"}}}}
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
    from app.services.retriever.retriever_service import retrieve_examples

    # 1. Recuperar 15 ejemplos dinámicos de requerimientos
    examples_list = retrieve_examples(requirement_text, k=15)
    examples_str = _format_db_examples(examples_list)

    llm = _get_llm()
    prompt = _build_evaluation_prompt(examples_str)
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
