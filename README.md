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
| `GET` | `/` | Health check y bienvenida |
| `GET` | `/health` | Estado detallado del sistema |
| `POST` | `/analyze` | Evaluar un requisito (pipeline RAG + LLM) |
| `GET` | `/requirements` | Listar requisitos almacenados en base de datos |
| `GET` | `/documents` | Listar chunks de documentos de referencia (ISO 29148) |

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

## Modelos y Configuración LLM

El sistema cuenta con soporte multi-proveedor y permite configurar diferentes modelos para las tareas de **Embeddings** y **Generación/Evaluación** en el archivo `.env`:

### 1. Modelos en Uso
*   **Modelo de Generación / Evaluación**: `models/gemini-2.5-flash` (por defecto en la nube, usando `GOOGLE_API_KEY`) o localmente `google/gemma-3-4b:2` mediante LM Studio.
*   **Modelo de Embeddings**: `models/gemini-embedding-001` (por defecto para Gemini) o localmente `text-embedding-embeddinggemma-300m` mediante LM Studio.
*   **Modelo de Juez Evaluador**: `models/gemini-2.5-flash` en el notebook de pruebas [LLM-as-a-judge.ipynb](./client/LLM-as-a-judge.ipynb) para calcular métricas como *Context Relevance*, *Faithfulness* y *Answer Relevance*.

### 2. Configuración de Variables de Entorno (`.env`)
```env
# Proveedor principal de embeddings (gemini, openai, local)
LLM_PROVIDER=gemini

# Proveedor principal de generación y evaluación
GENERATION_LLM_PROVIDER=gemini

# Claves de API
GOOGLE_API_KEY=tu-key-gemini
OPENAI_API_KEY=tu-key-openai

# Configuración del recuperador (Retriever)
# Se recuperan 5 chunks de la norma ISO 29148 para proveer mayor contexto normativo al LLM.
RETRIEVER_K=5
```

---

##  Estado Actual del Proyecto y Próximos Pasos

1. **Fase de Evaluación (Activa)**: Actualmente el proyecto se encuentra en la fase de evaluación del pipeline RAG y del retriever. Se utiliza el enfoque de **LLM-as-a-judge** en [LLM-as-a-judge.ipynb](./client/LLM-as-a-judge.ipynb) para iterar y medir de forma automatizada la calidad del sistema frente al dataset base.
2. **Control de Rate Limits**: El notebook de evaluación incorpora mecanismos de retraso base (`time.sleep`) y reintentos automáticos con respaldo exponencial ante errores HTTP `429 (Resource Exhausted)` de las APIs de la nube.
3. **Módulo de Usuarios (Pendiente)**: Tras estabilizar la fase de evaluación, se implementará el backend de usuarios, autenticación y base de datos para guardar sesiones, historiales de análisis de requisitos y trazabilidad de consultas.

---

## Estructura del proyecto

```
backend/
├── app/
│   ├── main.py
│   ├── api/routes/
│   ├── services/
│   │   ├── retriever/
│   │   ├── evaluation/
│   │   └── feedback/
│   ├── schemas/
│   ├── db/
│   └── core/
├── nlp4re/
docs/
├── estado-del-arte/
├── seguimiento/
└── informe-final/
```

## Stack

Python · FastAPI · LangChain · PostgreSQL · pgvector · Google Gemini / OpenAI · Docker · FAISS (Local Test)
