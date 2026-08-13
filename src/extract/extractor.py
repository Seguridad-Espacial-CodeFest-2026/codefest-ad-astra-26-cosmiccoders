from pathlib import Path
import pymupdf
import pandas as pd
import json
import hashlib

OUTPUT_PATH = Path("data/processed")

FENOMENOS = {
    "F1_IA_y_Capacidades_Estrategicas": 1,
    "F2_Seguridad_Entorno_Espacial": 2,
    "F3_Dinamicas_Territoriales": 3,
}


def crear_id_documento(relative_path):
    codigo = hashlib.sha1(str(relative_path).encode("utf-8")).hexdigest()[:10]
    return f"DOC-{codigo}"


def limpiar_texto(text):
    if not text:
        return ""
    text = text.replace("\x00", "")
    text = text.replace("\r\n", "\n")
    text = text.replace("\r", "\n")
    paragraphs = []
    for paragraph in text.split("\n\n"):
        paragraph = " ".join(paragraph.split())
        if paragraph:
            paragraphs.append(paragraph)
    return "\n\n".join(paragraphs)


def extraer_pdf(path):
    pages = []
    with pymupdf.open(path) as doc:
        total_pages = len(doc)
        for page in doc:
            text = page.get_text("text")
            if text:
                pages.append(text)
    text = "\n\n".join(pages)
    metadata = {"num_pages": total_pages}
    return text, metadata


def extraer_json(path):
    with open(path, "r", encoding="utf-8") as file:
        data = json.load(file)
        if not isinstance(data, dict):
            text = json.dumps(data, ensure_ascii=False)
            return text, {}
        title = data.get("title", "")
        paragraphs = data.get("body_paragraphs", [])
        if isinstance(paragraphs, list) and paragraphs:
            body = "\n\n".join(str(paragraph) for paragraph in paragraphs if paragraph)
        else:
            body = data.get("body_text", "")
            if not body:
                body = data.get("excerpt", "")
        pieces = []
        if title:
            pieces.append(str(title))
        if body:
            pieces.append(str(body))
        text = "\n\n".join(pieces)
        metadata = {
            "title": title, "url": data.get("url"), "date": data.get("date"),
            "authors": data.get("authors", []), "topics": data.get("topics", []),
            "pdf_links": data.get("pdf_links", []), "images": data.get("images", [])}
        return text, metadata


def extraer_csv(path):
    dataframe = pd.read_csv(path, encoding="utf-8", encoding_errors="replace")
    rows = []
    for _, row in dataframe.iterrows():
        values = []
        for column in dataframe.columns:
            value = row[column]
            if pd.notna(value):
                values.append(f"{column}: {value}")
        rows.append(" | ".join(values))
    text = "\n".join(rows)
    metadata = {
        "columns": list(dataframe.columns),
        "num_rows": len(dataframe)
    }
    return text, metadata


def extraer_txt(path):
    with open(path, "r", encoding="utf-8", errors="replace") as file:
        text = file.read()
        return text, {}


def procesar_documento(path, corpus_path, fenomeno):
    relative_path = path.relative_to(corpus_path)
    extension = relative_path.suffix.lower()
    if extension == ".pdf":
        text, metadata = extraer_pdf(path)
    elif extension == ".json":
        text, metadata = extraer_json(path)
    elif extension == ".csv":
        text, metadata = extraer_csv(path)
    elif extension == ".txt":
        text, metadata = extraer_txt(path)
    else:
        return None
    text = limpiar_texto(text)
    doc_id = crear_id_documento(relative_path.as_posix())
    return {
        "doc_id": doc_id,
        "fuente": relative_path.as_posix(),
        "formato": extension.replace(".", ""),
        "fenomeno": fenomeno,
        "texto": text,
        "metadata": metadata
    }


def guardar_documento(documento):
    OUTPUT_PATH.mkdir(parents=True, exist_ok=True)
    nombre_archivo = documento["doc_id"] + ".json"
    ruta_archivo = OUTPUT_PATH / nombre_archivo
    with open(ruta_archivo, "w", encoding="utf-8") as file:
        json.dump(documento, file, ensure_ascii=False, indent=2)


def procesar_fenomeno(corpus_path, fenomeno, modo_prueba):
    formatos_soportados = {".pdf", ".json", ".csv", ".txt"}
    extensiones_imagen = {".jpg", ".jpeg", ".png", ".avif"}

    archivos = sorted([p for p in corpus_path.rglob("*") if p.is_file()])
    print(f"\nArchivos encontrados: {len(archivos)}")

    if modo_prueba:
        archivos = [p for p in archivos if p.suffix.lower() in formatos_soportados][:3]

    procesados = 0
    vacios = 0
    errores = 0
    imagenes_pendientes = 0

    for path in archivos:
        extension = path.suffix.lower()
        if path.name == ".DS_Store":
            continue
        if extension in extensiones_imagen:
            imagenes_pendientes += 1
        elif extension in formatos_soportados:
            try:
                documento = procesar_documento(path, corpus_path, fenomeno)
                if documento is not None:
                    guardar_documento(documento)
                    if not documento["texto"].strip():
                        vacios += 1
                        print(f"[vacio] {path.relative_to(corpus_path)}")
                    else:
                        procesados += 1
                        print(f"[procesado] {path.relative_to(corpus_path)}")
            except Exception as error:
                errores += 1
                print(f"[error] {path.relative_to(corpus_path)}")
                print(error)

    return procesados, vacios, errores, imagenes_pendientes


def main():
    ruta_corpus = input("Pega la ruta de la carpeta raiz del Corpus (CORPUS CODEFEST AD ASTRA 2026): ").strip().strip('"')
    corpus_raiz = Path(ruta_corpus)

    if not corpus_raiz.exists() or not corpus_raiz.is_dir():
        print("\nERROR: La ruta del corpus no existe o no es una carpeta.")
        return

    prueba = input("¿Procesar solo 3 archivos de prueba por fenomeno? (s/n): ").strip().lower()
    modo_prueba = prueba == "s"

    total_procesados = 0
    total_vacios = 0
    total_errores = 0
    total_imagenes = 0

    for nombre_carpeta, numero_fenomeno in FENOMENOS.items():
        corpus_path = corpus_raiz / nombre_carpeta
        if not corpus_path.exists():
            print(f"\n[AVISO] No se encontro la carpeta: {nombre_carpeta}")
            continue

        print(f"\n{'=' * 50}")
        print(f"Procesando F{numero_fenomeno}: {nombre_carpeta}")
        print("=" * 50)

        procesados, vacios, errores, imagenes = procesar_fenomeno(corpus_path, numero_fenomeno, modo_prueba)
        total_procesados += procesados
        total_vacios += vacios
        total_errores += errores
        total_imagenes += imagenes

    print("\n" + "=" * 50)
    print("RESUMEN TOTAL")
    print("=" * 50)
    print(f"Documentos procesados: {total_procesados}")
    print(f"Documentos vacios:     {total_vacios}")
    print(f"Errores:               {total_errores}")
    print(f"Imagenes pendientes:   {total_imagenes}")


if __name__ == "__main__":
    main()
