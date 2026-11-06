# NLP4RE — Análisis Inteligente de Requisitos

Sistema que evalúa requisitos de software usando NLP y LLMs, basado en la norma **ISO/IEC/IEEE 29148**.

Recibe un requisito, lo evalúa en 5 dimensiones de calidad y genera sugerencias de mejora. No entrega el requisito corregido: el objetivo es que el estudiante lo reescriba a partir de las sugerencias.

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
Frontend (Angular) ──REST──► users-service (Spring Boot) ──► users-db (PostgreSQL)
        │
        └──WebSocket──► ia-service (FastAPI) ──► rag-db (pgvector)
                              │
                              └──► Redis (caché)
```

Flujo de un análisis en `ia-service`:

```
Caché → Clasificador → Retriever (pgvector) → LLM Evaluación → LLM Feedback → Response
```

- **Caché**: si el mismo requisito ya se evaluó con el mismo modelo en las últimas 24 horas, responde desde Redis
- **Clasificador**: decide si el mensaje es un requisito o un saludo/pregunta
- **Retriever**: busca contexto relevante de la ISO 29148 y requisitos de ejemplo en pgvector
- **Evaluación**: LLM puntúa el requisito en las 5 dimensiones
- **Feedback**: LLM genera sugerencias de mejora

| Servicio | Puerto |
|----------|--------|
| Frontend | 4200 |
| ia-service | 8001 |
| users-service | 8081 |
| rag-db | 5433 |
| users-db | 5434 |

## Requisitos previos

- Docker y Docker Compose
- Node.js y npm (frontend)
- API key de Google Gemini

## Setup

1. Configura las variables de entorno y reemplaza los valores de ejemplo:

```bash
cp example.env .env
```

2. Levanta los servicios:

```bash
docker compose up -d --build
```

3. Carga la base vectorial restaurando el dump (o vectoriza desde cero con [upload-data.ipynb](./client/upload-data.ipynb)):

```bash
docker cp data/requirements_db_dump.sql rag-db:/tmp/dump.sql
docker exec rag-db sh -c 'psql -U $POSTGRES_USER -d $POSTGRES_DB -f /tmp/dump.sql'
```

4. Levanta el frontend:

```bash
cd frontend
npm install
npm start
```

5. Abre la aplicación en **http://localhost:4200** y el Swagger UI de ia-service en **http://localhost:8001/docs**

## Endpoints (ia-service)

| Método | Ruta | Descripción |
|--------|------|-------------|
| `GET` | `/` | Health check y bienvenida |
| `GET` | `/health` | Estado detallado del sistema |
| `GET` | `/models` | Listar modelos de LLM disponibles |
| `WS` | `/ws/analyze` | Evaluar un requisito con streaming (lo usa el frontend) |
| `POST` | `/analyze` | Evaluar un requisito (pipeline RAG + LLM) |
| `GET` | `/requirements` | Listar requisitos almacenados en base de datos |
| `GET` | `/documents` | Listar chunks de documentos de referencia (ISO 29148) |

## Ejemplo rápido

```bash
curl -X POST http://localhost:8001/analyze \
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
    "suggestions": ["Reemplazar 'fast' por una métrica cuantificable..."]
  }
}
```

## Modelos y Configuración LLM

El sistema cuenta con soporte multi-proveedor y permite configurar diferentes modelos para las tareas de **Embeddings** y **Generación/Evaluación** en el archivo `.env`:

### 1. Modelos en Uso
*   **Modelo de Generación / Evaluación**: `gemini-3.5-flash-lite` (por defecto en la nube, usando `GOOGLE_API_KEY`) o localmente `google/gemma-3-4b:2` mediante LM Studio.
*   **Modelo de Embeddings**: `models/gemini-embedding-001` (por defecto para Gemini) o localmente `text-embedding-embeddinggemma-300m` mediante LM Studio.
*   **Modelo de Juez Evaluador**: Gemini en el notebook de pruebas [LLM-as-a-judge.ipynb](./client/LLM-as-a-judge.ipynb) para calcular métricas como *Context Relevance*, *Faithfulness* y *Answer Relevance*.

### 2. Configuración de Variables de Entorno (`.env`)
La lista completa de variables, con valores de ejemplo, está en [example.env](./example.env). Las principales:

```env
# Proveedor principal de embeddings (gemini, openai, local)
LLM_PROVIDER=gemini

# Proveedor principal de generación y evaluación
GENERATION_LLM_PROVIDER=gemini

# Claves de API
GOOGLE_API_KEY=tu-key-gemini

# Vigencia de las respuestas en caché (segundos)
CACHE_TTL_SECONDS=86400
```

---

## Estado Actual del Proyecto

1. **Evaluación del pipeline**: se utiliza el enfoque de **LLM-as-a-judge** en [LLM-as-a-judge.ipynb](./client/LLM-as-a-judge.ipynb) para medir de forma automatizada la calidad del sistema frente al dataset base.
2. **Control de Rate Limits**: los notebooks incorporan retrasos base (`time.sleep`) y reintentos automáticos con respaldo exponencial ante errores HTTP `429 (Resource Exhausted)` de las APIs de la nube.
3. **Módulo de Usuarios**: implementado en `users-service` (registro, login con JWT, perfil y conversaciones).

---

## Estructura del proyecto

```
backend/
├── ia-service/          # Servicio de IA (FastAPI)
│   └── ia_service/
│       ├── main.py
│       ├── api/routes/
│       ├── services/
│       │   ├── cache/
│       │   ├── classifier/
│       │   ├── retriever/
│       │   ├── evaluation/
│       │   └── feedback/
│       ├── schemas/
│       ├── db/
│       └── core/
└── nlp4re/              # Servicio de usuarios (Spring Boot)
frontend/                # Aplicación web (Angular)
client/                  # Notebooks de carga de datos y evaluación
data/                    # Dataset de requisitos, norma ISO y dumps de las bases
docs/
├── estado-del-arte/
└── seguimiento/
testing/                 # Experimentos previos
```

## Stack

Python · FastAPI · LangChain · Java · Spring Boot · Angular · PostgreSQL · pgvector · Redis · Google Gemini / OpenAI · Docker
