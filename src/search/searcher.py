from pathlib import Path
import json
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer

INDEX_PATH = Path("data/indexes/index.faiss")
METADATA_PATH = Path("data/embeddings/metadata.jsonl")
MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"
TOP_K = 5


def cargar_metadata():
    metadata = []
    with open(METADATA_PATH, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                metadata.append(json.loads(line))
    return metadata


def buscar(query, index, metadata, model, top_k=TOP_K):
    vector = model.encode([query], convert_to_numpy=True).astype("float32")
    faiss.normalize_L2(vector)
    distancias, indices = index.search(vector, top_k)

    resultados = []
    for i, idx in enumerate(indices[0]):
        if idx != -1:
            resultado = metadata[idx].copy()
            resultado["score"] = float(distancias[0][i])
            resultados.append(resultado)

    return resultados


def main():
    if not INDEX_PATH.exists():
        print("ERROR: No existe el indice. Ejecuta primero indexer.py")
        return
    if not METADATA_PATH.exists():
        print("ERROR: No existe la metadata. Ejecuta primero embedder.py")
        return

    print("Cargando modelo e indice...")
    model = SentenceTransformer(MODEL_NAME)
    index = faiss.read_index(str(INDEX_PATH))
    metadata = cargar_metadata()

    print(f"Indice cargado: {index.ntotal} vectores")
    print(f"Metadata cargada: {len(metadata)} chunks\n")

    while True:
        query = input("Pregunta (o 'salir'): ").strip()
        if query.lower() == "salir":
            break
        if not query:
            continue

        resultados = buscar(query, index, metadata, model)

        print(f"\n--- Top {len(resultados)} resultados ---")
        for i, r in enumerate(resultados, 1):
            print(f"\n[{i}] Score: {r['score']:.4f}")
            print(f"    Fuente:   {r['fuente']}")
            print(f"    Fenomeno: {r['fenomeno']}")
            print(f"    Texto:    {r['texto'][:400]}")
        print()


if __name__ == "__main__":
    main()
