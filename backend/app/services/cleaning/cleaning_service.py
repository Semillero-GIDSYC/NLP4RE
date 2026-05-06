import re

NOISE_PATTERNS = [
    r"(?i)(page\s+\d+\s*(of\s*\d+)?)",
    r"(?i)(downloaded\s+from\s+\S+)",
    r"(?i)(authorized\s+licensed\s+use)",
    r"(?i)(restriction.*apply)",
    r"(?i)(all\s+rights\s+reserved)",
    r"(?i)(copyright\s*©?\s*\d{4})",
    r"https?://\S+",
    r"ISO/IEC/IEEE\s+29148:\d{4}\(E\)",
]

REQUIREMENT_SEPARATORS = [
    r"\n(?=\d+\.\d+)",           # Numeración tipo "3.1"
    r"\n(?=\d+\))",              # Numeración tipo "1)"
    r"\n(?=[A-Z]{2,}-\d+)",      # IDs tipo "REQ-001"
    r"\n(?=•|▪|►|○|●)",         # Bullet points
    r"\n(?=[-*]\s)",             # Listas markdown
    r"\n(?=shall\s|must\s|should\s|will\s)", # Verbos modales al inicio
    r"\n\n+",                    # Doble newline
]


def remove_noise(text: str) -> str:
    """
    Elimina ruido del texto: headers, footers, URLs, copyright notices.

    Args:
        text: Texto crudo.

    Returns:
        Texto limpio.
    """
    for pattern in NOISE_PATTERNS:
        text = re.sub(pattern, "", text)
    return text


def normalize_whitespace(text: str) -> str:
    """
    Normaliza espacios en blanco:
    - Reemplaza tabs por espacios.
    - Colapsa múltiples espacios en uno.
    - Elimina líneas vacías excesivas.
    - Trim al inicio y final.
    """
    text = text.replace("\t", " ")
    text = re.sub(r"[ ]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def normalize_unicode(text: str) -> str:
    """
    Normaliza caracteres unicode comunes:
    - Comillas inteligentes → rectas
    - Guiones decorativos → guión normal
    - Espacios especiales → espacio normal
    """
    replacements = {
        "\u2018": "'", "\u2019": "'",  # Comillas simples
        "\u201c": '"', "\u201d": '"',  # Comillas dobles
        "\u2013": "-", "\u2014": "-",  # Guiones
        "\u2026": "...",               # Puntos suspensivos
        "\u00a0": " ",                 # Non-breaking space
        "\u200b": "",                  # Zero-width space
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text


def clean_text(text: str) -> str:
    """
    Pipeline completa de limpieza de texto.

    Pasos:
    1. Normalizar unicode
    2. Eliminar ruido (headers/footers)
    3. Normalizar whitespace

    Args:
        text: Texto crudo.

    Returns:
        Texto limpio y normalizado.
    """
    text = normalize_unicode(text)
    text = remove_noise(text)
    text = normalize_whitespace(text)
    return text


def segment_requirements(text: str) -> list[str]:
    """
    Segmenta un bloque de texto en requisitos individuales.
    Usa múltiples estrategias: numeración, bullets, verbos modales.

    Args:
        text: Texto limpio con múltiples requisitos.

    Returns:
        Lista de textos, cada uno representando un requisito individual.
    """
    # Construir patrón combinado de separadores
    combined_pattern = "|".join(f"({sep})" for sep in REQUIREMENT_SEPARATORS)

    # Dividir por los separadores
    segments = re.split(combined_pattern, text)

    # Limpiar y filtrar segmentos válidos
    requirements = []
    for segment in segments:
        if segment is None:
            continue

        cleaned = normalize_whitespace(segment)

        # Filtrar segmentos muy cortos o que son solo separador
        if cleaned and len(cleaned) >= 10:
            requirements.append(cleaned)

    return requirements


def clean_pipeline(raw_texts: list[str]) -> list[str]:
    """
    Pipeline completa: limpieza + segmentación de una lista de textos.

    Args:
        raw_texts: Lista de textos crudos (ej. de PDF o scraping).

    Returns:
        Lista de requisitos limpios y segmentados.
    """
    all_requirements: list[str] = []

    for text in raw_texts:
        # Limpiar
        cleaned = clean_text(text)

        if not cleaned:
            continue

        # Segmentar si el texto es largo (probablemente contiene múltiples requisitos)
        if len(cleaned) > 200:
            segments = segment_requirements(cleaned)
            all_requirements.extend(segments)
        else:
            all_requirements.append(cleaned)

    # Deduplicar preservando orden
    seen: set[str] = set()
    unique_reqs = []
    for req in all_requirements:
        if req not in seen:
            seen.add(req)
            unique_reqs.append(req)

    return unique_reqs
