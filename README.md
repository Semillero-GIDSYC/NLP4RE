# NLP4RE — Análisis Inteligente de Requisitos

Sistema que evalúa requisitos de software usando NLP y LLMs, basado en la norma **ISO/IEC/IEEE 29148**.

Recibe un requisito, lo evalúa en 5 dimensiones de calidad, y genera sugerencias de mejora con una versión optimizada.

## ¿Qué evalúa?

| Dimensión | ¿Qué mide? |
|-----------|------------|
| **Verificabilidad** | ¿Se puede probar objetivamente? |
| **Atomicidad** | ¿Expresa una sola idea? |
| **Ambigüedad** | ¿Tiene una sola interpretación? |
| **Completitud** | ¿Tiene condición, acción y resultado? |
| **Trazabilidad** | ¿Se puede vincular a su origen? |

Cada dimensión recibe un score de **0** (malo), **1** (parcial) o **2** (bueno).

## Arquitectura

```
Usuario → FastAPI → Retriever (pgvector) → LLM Evaluación → LLM Feedback → Response
```

- **Retriever**: busca contexto relevante de la ISO 29148 en pgvector
- **Evaluación**: LLM puntúa el requisito en las 5 dimensiones
- **Feedback**: LLM genera sugerencias y reescribe el requisito

## Requisitos previos

- Docker y Docker Compose
- API key de Google Gemini (o OpenAI)

## Setup

1. Configura las variables de entorno:

```bash
cp example.env .env
```

2. Levanta los servicios:

```bash
docker compose up --build
```

3. Abre el Swagger UI: **http://localhost:8000/docs**

## Endpoints

| Método | Ruta | Descripción |
|--------|------|-------------|
| `POST` | `/analyze` | Evaluar un requisito |
| `POST` | `/upload/pdf` | Subir PDF y extraer requisitos |
| `POST` | `/scrape` | Scrapear requisitos de una URL |
| `GET` | `/requirements` | Listar requisitos almacenados |
| `GET` | `/export/dataset` | Exportar requisitos como JSON |
| `GET` | `/export/chunks` | Exportar chunks de pgvector |
| `GET` | `/scrape/sources` | Fuentes sugeridas para scraping |
| `GET` | `/health` | Estado del sistema |

## Ejemplo rápido

```bash
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{"text": "The system must be fast"}'
```

Respuesta (resumida):
```json
{
  "evaluation": {
    "VERIFIABILITY": {"score": 0, "explanation": "'fast' es subjetivo..."},
    "ATOMICITY": {"score": 2, "explanation": "Expresa una única idea"},
    "AMBIGUITY": {"score": 0, "explanation": "'fast' es ambiguo..."},
    "COMPLETENESS": {"score": 0, "explanation": "Falta condición..."},
    "TRACEABLE": {"score": 0, "explanation": "Sin referencia a origen..."}
  },
  "feedback": {
    "suggestions": ["Reemplazar 'fast' por una métrica cuantificable..."],
    "improved_requirement": "El sistema debe cargar la interfaz en menos de 2 segundos para el 95% de las solicitudes..."
  }
}
```

## Configuración LLM

El sistema soporta **Gemini** y **OpenAI**. Cambia el proveedor en `.env`:

```env
LLM_PROVIDER=gemini         # o openai
GOOGLE_API_KEY=tu-key       # para Gemini
OPENAI_API_KEY=tu-key       # para OpenAI
```

## Estructura del proyecto

```
backend/
├── app/
│   ├── main.py
│   ├── api/routes/
│   ├── services/
│   │   ├── ingestion/
│   │   ├── cleaning/
│   │   ├── retriever/
│   │   ├── evaluation/
│   │   └── feedback/
│   ├── schemas/
│   ├── db/
│   └── core/
docs/
├── rules.json
├── examples.json
└── iso_29148.pdf
```

## Stack

Python · FastAPI · LangChain · PostgreSQL · pgvector · Google Gemini / OpenAI · Docker
