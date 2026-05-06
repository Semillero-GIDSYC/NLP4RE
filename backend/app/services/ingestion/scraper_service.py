import re
from dataclasses import dataclass

import requests
from bs4 import BeautifulSoup

# Timeout para requests HTTP
REQUEST_TIMEOUT = 30

# User-Agent para evitar bloqueos
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9",
    "Accept-Language": "en-US,en;q=0.9,es;q=0.8",
}


@dataclass
class ScrapedRequirement:
    """Requisito extraído por web scraping."""

    text: str
    source_url: str
    metadata: dict


def _fetch_page(url: str) -> BeautifulSoup:
    """
    Descarga una página web y retorna el objeto BeautifulSoup.

    Args:
        url: URL de la página.

    Returns:
        BeautifulSoup parsed object.

    Raises:
        ConnectionError: Si la página no se puede descargar.
    """
    try:
        response = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        return BeautifulSoup(response.text, "lxml")
    except requests.RequestException as e:
        raise ConnectionError(f"No se pudo descargar la página: {url}") from e


def _clean_requirement_text(text: str) -> str:
    """
    Limpieza básica de texto extraído por scraping.

    - Elimina whitespace excesivo
    - Elimina caracteres especiales de control
    - Normaliza espacios
    """
    # Eliminar caracteres de control
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)
    # Normalizar whitespace
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _is_valid_requirement(text: str) -> bool:
    """
    Verifica si un texto parece ser un requisito válido.

    Filtros:
    - Mínimo 10 caracteres
    - No es puro whitespace
    - Contiene al menos un verbo modal o palabra clave de requisito
    """
    if len(text) < 10:
        return False

    # Patrones comunes en requisitos
    requirement_patterns = [
        r"\b(shall|must|should|will|may|can)\b",
        r"\b(the system|the software|the application|the platform)\b",
        r"\b(require|need|support|provide|allow|enable|ensure)\b",
        r"\b(user|admin|system|service|interface|data|process)\b",
    ]

    text_lower = text.lower()
    return any(re.search(pattern, text_lower) for pattern in requirement_patterns)


def scrape_generic(url: str, css_selector: str | None = None) -> list[ScrapedRequirement]:
    """
    Scraper genérico que extrae texto de una página web usando selectores CSS.

    Si no se proporciona selector, intenta detectar listas y párrafos
    que contengan patrones de requisitos.

    Args:
        url: URL de la página.
        css_selector: Selector CSS opcional para los elementos a extraer.

    Returns:
        Lista de requisitos extraídos.
    """

    soup = _fetch_page(url)
    requirements: list[ScrapedRequirement] = []

    if css_selector:
        # Usar selector proporcionado
        elements = soup.select(css_selector)
    else:
        # Auto-detección: buscar en listas y párrafos
        elements = []

        # Buscar en listas ordenadas y no ordenadas
        for li in soup.find_all("li"):
            text = _clean_requirement_text(li.get_text())
            if _is_valid_requirement(text):
                elements.append(li)

        # Buscar en párrafos
        for p in soup.find_all("p"):
            text = _clean_requirement_text(p.get_text())
            if _is_valid_requirement(text):
                elements.append(p)

        # Buscar en celdas de tabla (muchos SRS usan tablas)
        for td in soup.find_all("td"):
            text = _clean_requirement_text(td.get_text())
            if _is_valid_requirement(text):
                elements.append(td)


    # Procesar elementos encontrados
    seen_texts: set[str] = set()  # Para deduplicar
    for element in elements:
        text = _clean_requirement_text(element.get_text())

        if text and text not in seen_texts and _is_valid_requirement(text):
            seen_texts.add(text)
            requirements.append(
                ScrapedRequirement(
                    text=text,
                    source_url=url,
                    metadata={
                        "tag": element.name,
                        "css_class": element.get("class", []),
                    },
                )
            )

    return requirements


def scrape_reqview_examples() -> list[ScrapedRequirement]:
    """
    Scraper para ReqView: herramienta profesional de gestión de requisitos
    que publica ejemplos de SRS basados en IEEE/ISO en su sitio web.

    URL: https://www.reqview.com/doc/iso-iec-ieee-29148-srs-example

    Returns:
        Lista de requisitos del ejemplo SRS de ReqView.
    """
    url = "https://www.reqview.com/doc/iso-iec-ieee-29148-srs-example"

    try:
        soup = _fetch_page(url)
    except ConnectionError:
        return []

    requirements: list[ScrapedRequirement] = []

    # ReqView organiza requisitos en divs con clase específica
    # Buscar en elementos de contenido principal
    content_area = soup.find("main") or soup.find("article") or soup.find("div", class_="content")

    if not content_area:
        content_area = soup

    # Buscar textos que contengan patrones de requisitos
    for element in content_area.find_all(["p", "li", "td", "div"]):
        text = _clean_requirement_text(element.get_text())
        if text and _is_valid_requirement(text) and len(text) < 2000:
            requirements.append(
                ScrapedRequirement(
                    text=text,
                    source_url=url,
                    metadata={"source_type": "reqview_srs_example"},
                )
            )

    # Deduplicar
    seen: set[str] = set()
    unique_reqs = []
    for req in requirements:
        if req.text not in seen:
            seen.add(req.text)
            unique_reqs.append(req)

    return unique_reqs


def scrape_srs_document(url: str) -> list[ScrapedRequirement]:
    """
    Scraper optimizado para documentos SRS publicados en web.
    Busca patrones como "REQ-xxx", "shall", "must" en el contenido.

    Args:
        url: URL del documento SRS online.

    Returns:
        Lista de requisitos extraídos.
    """

    try:
        soup = _fetch_page(url)
    except ConnectionError:
        return []

    requirements: list[ScrapedRequirement] = []
    seen: set[str] = set()

    # Patrones para identificar IDs de requisitos
    req_id_pattern = re.compile(
        r"(REQ[-_]\w+|FR[-_]?\d+|NFR[-_]?\d+|SR[-_]?\d+|UC[-_]?\d+)",
        re.IGNORECASE,
    )

    for element in soup.find_all(["p", "li", "td", "tr", "div", "span"]):
        text = _clean_requirement_text(element.get_text())

        if not text or text in seen or len(text) < 15 or len(text) > 2000:
            continue

        # Verificar si parece un requisito
        has_req_id = bool(req_id_pattern.search(text))
        is_valid = _is_valid_requirement(text)

        if has_req_id or is_valid:
            seen.add(text)

            # Extraer ID del requisito si existe
            req_id_match = req_id_pattern.search(text)

            requirements.append(
                ScrapedRequirement(
                    text=text,
                    source_url=url,
                    metadata={
                        "requirement_id": req_id_match.group(0) if req_id_match else None,
                        "has_formal_id": has_req_id,
                    },
                )
            )

    return requirements

def scrape_requirements(
    url: str,
    css_selector: str | None = None,
) -> list[ScrapedRequirement]:
    """
    Punto de entrada principal para scraping.
    Selecciona el scraper adecuado según la URL o usa el genérico.

    Args:
        url: URL a scrapear.
        css_selector: Selector CSS opcional.

    Returns:
        Lista de requisitos extraídos.
    """
    url_lower = url.lower()

    # Seleccionar scraper según la URL
    if "reqview.com" in url_lower:
        return scrape_reqview_examples()
    else:
        # Intentar primero el scraper SRS, luego el genérico
        results = scrape_srs_document(url)
        if not results:
            results = scrape_generic(url, css_selector)
        return results
