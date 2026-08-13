from pathlib import Path
import json
import numpy as np
from sentence_transformers import SentenceTransformer

INPUT_PATH = Path("data/chunks")
OUTPUT_PATH = Path("data/embeddings")
MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"
BATCH_SIZE = 64


def cargar_chunks():
    chunks_path = INPUT_PATH / "chunks.jsonl"
    chunks = []
    with open(chunks_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                chunks.append(json.loads(line))
    return chunks


def main():
    if not INPUT_PATH.exists():
        print("ERROR: No existe la carpeta data/chunks. Ejecuta primero chunking.py")
        return

    chunks_path = INPUT_PATH / "chunks.jsonl"
    if not chunks_path.exists():
        print("ERROR: No existe data/chunks/chunks.jsonl. Ejecuta primero chunking.py")
        return

    chunks = cargar_chunks()
    print(f"Chunks cargados: {len(chunks)}")

    model = SentenceTransformer(MODEL_NAME)

    textos = [chunk["texto"] for chunk in chunks]

    print("Generando embeddings...")
    embeddings = model.encode(
        textos,
        batch_size=BATCH_SIZE,
        show_progress_bar=True,
        convert_to_numpy=True
    )

    OUTPUT_PATH.mkdir(parents=True, exist_ok=True)

    np.save(OUTPUT_PATH / "embeddings.npy", embeddings)

    with open(OUTPUT_PATH / "metadata.jsonl", "w", encoding="utf-8") as f:
        for chunk in chunks:
            json.dump({
                "chunk_id": chunk["chunk_id"],
                "doc_id": chunk["doc_id"],
                "fuente": chunk["fuente"],
                "fenomeno": chunk["fenomeno"],
                "posicion": chunk["posicion"],
                "texto": chunk["texto"]
            }, f, ensure_ascii=False)
            f.write("\n")

    print("\nRESUMEN")
    print(f"Embeddings generados: {len(embeddings)}")
    print(f"Dimension: {embeddings.shape[1]}")
    print(f"Guardados en: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
