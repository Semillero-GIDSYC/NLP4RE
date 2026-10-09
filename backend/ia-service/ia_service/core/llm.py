import os
from ia_service.core.config import get_settings


def get_llm(
    provider: str | None = None,
    model: str | None = None,
    api_key: str | None = None,
    base_url: str | None = None,
    temperature: float | None = None,
):
    """
    Retorna la instancia adecuada de ChatModel según el proveedor seleccionado.
    Aplica KISS y DRY centralizando la instanciación de LLMs multi-proveedor.
    """
    settings = get_settings()
    p = (provider or settings.GENERATION_LLM_PROVIDER or "gemini").lower().strip()
    temp = temperature if temperature is not None else settings.LLM_TEMPERATURE

    if p == "openai":
        from langchain_openai import ChatOpenAI

        key = api_key or settings.OPENAI_API_KEY or os.environ.get("OPENAI_API_KEY", "")
        m = model or settings.OPENAI_MODEL or "gpt-4o-mini"
        return ChatOpenAI(
            model=m,
            temperature=temp,
            openai_api_key=key,
        )

    elif p == "anthropic":
        from langchain_anthropic import ChatAnthropic

        key = api_key or getattr(settings, "ANTHROPIC_API_KEY", "") or os.environ.get("ANTHROPIC_API_KEY", "")
        m = model or getattr(settings, "ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022")
        return ChatAnthropic(
            model_name=m,
            temperature=temp,
            api_key=key,
        )

    elif p == "local":
        from langchain_openai import ChatOpenAI

        url = base_url or settings.LOCAL_MODELS_API or "http://host.docker.internal:1234/v1"
        if not url.endswith("/v1") and not url.endswith("/v1/"):
            url = f"{url.rstrip('/')}/v1"

        m = model or settings.LOCAL_MODEL or "google/gemma-3-4b"
        key = api_key or "lm-studio"
        return ChatOpenAI(
            model=m,
            temperature=temp,
            base_url=url,
            openai_api_key=key,
        )

    else:
        # Default: Google Gemini
        from langchain_google_genai import ChatGoogleGenerativeAI

        key = api_key or settings.GOOGLE_API_KEY or os.environ.get("GOOGLE_API_KEY", "")
        m = model or settings.GEMINI_MODEL or "gemini-2.5-flash"
        # Limpiar prefijo 'models/' si está presente para compatibilidad con google-genai
        if m.startswith("models/"):
            m = m.replace("models/", "")

        return ChatGoogleGenerativeAI(
            model=m,
            temperature=temp,
            google_api_key=key,
        )
