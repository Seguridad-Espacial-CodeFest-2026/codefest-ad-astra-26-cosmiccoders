from pathlib import Path
import numpy as np
import faiss

INPUT_PATH = Path("data/embeddings")
OUTPUT_PATH = Path("data/indexes")


def main():
    if not INPUT_PATH.exists():
        print("ERROR: No existe la carpeta data/embeddings. Ejecuta primero embedder.py")
        return

    embeddings_path = INPUT_PATH / "embeddings.npy"
    if not embeddings_path.exists():
        print("ERROR: No existe data/embeddings/embeddings.npy. Ejecuta primero embedder.py")
        return

    embeddings = np.load(embeddings_path).astype("float32")
    print(f"Embeddings cargados: {embeddings.shape}")

    faiss.normalize_L2(embeddings)

    dimension = embeddings.shape[1]
    index = faiss.IndexFlatIP(dimension)
    index.add(embeddings)

    OUTPUT_PATH.mkdir(parents=True, exist_ok=True)
    faiss.write_index(index, str(OUTPUT_PATH / "index.faiss"))

    print("\nRESUMEN")
    print(f"Vectores indexados: {index.ntotal}")
    print(f"Dimension: {dimension}")
    print(f"Indice guardado en: {OUTPUT_PATH / 'index.faiss'}")


if __name__ == "__main__":
    main()
