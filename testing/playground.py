from data.loaders.rule_loader import load_rules
from data.loaders.example_loader import load_examples
from testing.embedder.impl.sentence_transform_embedder_impl import SentenceTransformerEmbedderImpl
from testing.store.vector_store_factory import VectorStoreFactory

# 1. Cargar datos
rules = load_rules()
examples = load_examples()
print(f"Reglas cargadas: {len(rules)}")
print(f"Ejemplos cargados: {len(examples)}")

# 2. Crear embedder
embedder = SentenceTransformerEmbedderImpl()
print(f"Dimensión del modelo: {embedder.dimension}")

# 3. Crear vector store
store = VectorStoreFactory.create('faiss', dimension=embedder.dimension)

# 4. Vectorizar y guardar reglas
print("\nGuardando reglas...")
for rule in rules:
    vector = embedder.embed_rule(rule)
    metadata = {
        "tipo": "regla",
        "typeC": rule.typeC.value,
        "description": rule.description,
        "source": rule.source
    }
    store.saveV(vector, metadata)

# 5. Vectorizar y guardar ejemplos
print("Guardando ejemplos...")
for example in examples:
    vector = embedder.embed_example(example)
    metadata = {
        "tipo": "ejemplo",
        "text": example.text,
        "score": example.score,
        "tags": {k.value: v for k, v in example.tags.items()},
        "explanations": {k.value: v for k, v in example.explanations.items()}
    }
    store.saveV(vector, metadata)

print(f"\nTotal guardado: {len(store.listV())} items")

# 6. Prueba de búsqueda
requisito_prueba = "The system must be easy to use"
print(f"\nBuscando similares a: '{requisito_prueba}'")

from testing.models.Example import Example
from testing.models.Types import TypeC

ejemplo_prueba = Example(
    text=requisito_prueba,
    tags={t: 0 for t in TypeC},
    explanations={}
)

query_vector = embedder.embed_example(ejemplo_prueba)
resultados = store.searchV(query_vector, k=3)

print("\nTop 3 más similares:")
for metadata, score in resultados:
    print(f"\n  Score: {score:.3f}")
    print(f"  Tipo:  {metadata['tipo']}")
    if metadata['tipo'] == 'regla':
        print(f"  Criterio: {metadata['typeC']}")
        print(f"  Descripción: {metadata['description'][:80]}...")
    else:
        print(f"  Requisito: {metadata['text']}")
        print(f"  Puntaje: {metadata['score']}/10")