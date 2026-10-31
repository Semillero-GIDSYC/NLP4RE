import json

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from ia_service.core.llm import get_llm


def _build_classifier_prompt() -> ChatPromptTemplate:
    """
    Construye el prompt que decide si el mensaje es un requisito o una conversación casual.
    """
    template = """Eres el asistente de una herramienta que evalúa requisitos de software según la norma ISO 29148.
Tu tarea es decidir si el mensaje del usuario es un requisito de software que se debe evaluar, o si es otra cosa (un saludo, una pregunta, una conversación casual, etc.).

Mensaje del usuario:
{message}

Responde EXACTAMENTE con un JSON válido con esta estructura:
{{
  "is_requirement": <true o false>,
  "reply": "<respuesta para el usuario si NO es un requisito; cadena vacía si lo es>"
}}

REGLAS:
- Considera requisito cualquier enunciado que describa algo que un sistema, software o usuario debe o puede hacer o cumplir, aunque esté mal escrito, incompleto o sea ambiguo (por ejemplo: "el sistema debe ser rápido").
- Si tienes dudas, considera que SÍ es un requisito.
- Si NO es un requisito:
  - Si es un saludo o conversación casual, responde breve y amablemente e invita al usuario a escribir un requisito de software.
  - Si es una pregunta sobre ingeniería de requisitos o la norma ISO 29148 (por ejemplo, qué significa una dimensión de calidad), respóndela de forma breve y clara.
  - Si es una pregunta sobre cualquier otro tema, NO la respondas; explica amablemente que solo puedes ayudar con requisitos de software.
- Responde SOLO con el JSON, sin texto adicional, sin markdown, sin bloques de código.
- Escribe en español."""

    return ChatPromptTemplate.from_template(template)


async def classify_message(
    message: str,
    provider: str | None = None,
    model: str | None = None,
    api_key: str | None = None,
    base_url: str | None = None,
) -> dict:
    """
    Clasifica el mensaje del usuario.

    Returns:
        Diccionario con 'is_requirement' (bool) y 'reply' (str).
    """
    llm = get_llm(provider=provider, model=model, api_key=api_key, base_url=base_url)
    chain = _build_classifier_prompt() | llm | StrOutputParser()
    raw_response = await chain.ainvoke({"message": message})

    cleaned = raw_response.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("\n", 1)[1] if "\n" in cleaned else cleaned
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()

    try:
        result = json.loads(cleaned)
    except json.JSONDecodeError:
        # Si no se puede interpretar, se evalúa como requisito para no bloquear el análisis
        return {"is_requirement": True, "reply": ""}

    return {
        "is_requirement": bool(result.get("is_requirement", True)),
        "reply": result.get("reply", ""),
    }
