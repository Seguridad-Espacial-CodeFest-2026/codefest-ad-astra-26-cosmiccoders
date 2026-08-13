from pathlib import Path
import pymupdf
import pandas as pd
import json
import hashlib

#acá se pregunta cual es la ruta de cada uno cuando se ejecuta el programa. además los resultados se guardan en el repositorio en la carpeta data/processed
ruta = input("Pega la ruta de la carpeta F2_Seguridad_Entorno_Espacial: ").strip().strip('"')
CORPUS_PATH = Path(ruta)
OUTPUT_PATH = Path("data/processed")
FENOMENO = 2

#se crea el ID del documento, un ID único para cada documento. 
#si el documento sigue en la misma carpeta del Corpus, su id será el mismo, pero si se mueve a otra carpeta, su id cambiará.
def crear_id_documento(relative_path):
    codigo = hashlib.sha1(str(relative_path).encode("utf-8")).hexdigest()[:10]
    return f"DOC-{codigo}"
#se generó un doc_id por medio de la ruta de cada archivo usando sha1. Se tomaron los primeros 10 caracteres. Y se agregó "DOC-" al inicio para que se identifique más fácil.

#ahora realizamos la limpieza básica
def limpiar_texto(text):
    if not text:
        return ""
    text = text.replace("\x00", "")
    text = text.replace("\r\n", "\n")
    text = text.replace("\r", "\n")
    lineas = []
    for linea in text.split("\n"):
        linea = " ".join(linea.split())
        lineas.append(linea)
    return "\n".join(lineas)
#se limpia cada línea eliminando espacios innecesarios. se conservan los saltos de línea para mantener mejor la estructura original.


#Extraer el PDF
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
#Se abre el PDF con PyMuPDF, se recorre y se extrae texto con page.get_text("text"), y se guarda en una lista.
#Se unen los textos de todas las páginas y se devuelve con la metadata del número total de páginas.

#Extraer el JSON
def extraer_json(path):
    with open(path, "r", encoding="utf-8") as file:
        data = json.load(file)
        if not isinstance(data, dict):
            text = json.dumps(data, ensure_ascii=False)
            return text, {}
        title = data.get("title", "")
        paragraphs = data.get("body_paragraphs", [])
        if isinstance(paragraphs, list) and paragraphs:
            body = "\n\n".join(str(paragraph) for paragraph in paragraphs
            if paragraph)
        else:
            body = data.get("body_text", "")
            if not body:
                body = data.get( "excerpt", "")
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
# Se abre el JSON y se extrae primero el título y los párrafos.Pero si no hay párrafos, se usa body_text y, como última opción, excerpt.
# Los datos como URL, fecha, autores y temas se toman como metadata.

#Extraer CSV
def extraer_csv(path):

    dataframe = pd.read_csv(path,
        encoding="utf-8", encoding_errors="replace")
    rows = []
    for _, row in dataframe.iterrows():
        values = []
        for column in dataframe.columns:
            value = row[column]
            if pd.notna(value):
                values.append(
                    f"{column}: {value}")
        rows.append(" | ".join(values))
    text = "\n".join(rows)
    metadata = {
        "columns": list(dataframe.columns),
        "num_rows": len(dataframe)
    }
    return text, metadata
#se abre el CSV y se recorre fila por fila, convirtiendo cada dato en texto con el nombre de su columna.
#Con join() unen los datos en texto y metadata guarda los nombres de las columnas y la cantidad de filas.

#Extraer TXT
def extraer_txt(path):
    with open(path, "r", encoding="utf-8", errors="replace") as file:
        text = file.read()
        return text, {}
#se abre el archivo TXT, se lee todo su contenido.
#Y devuelve el texto extraído y una metadata vacía porque no hay datos adicionales que guardar.

#Precesar un documento
def procesar_documento(path):
    relative_path = path.relative_to(CORPUS_PATH)
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
        "fenomeno": FENOMENO,
        "texto": text,
        "metadata": metadata
    }
#se obtiene la ruta con relative_path obtiene la ruta interna y se identifica el tipo de archivo para usar su extractor con suffix.lower.
#Después se limpia el contenido, se genera el ID con crear_id_documento() y se organiza todo en un diccionario.

#Guardar documento
def guardar_documento(documento):
    OUTPUT_PATH.mkdir(parents=True, exist_ok=True)
    nombre_archivo = documento["doc_id"] + ".json"
    ruta_archivo = OUTPUT_PATH / nombre_archivo
    with open(ruta_archivo, "w", encoding="utf-8") as file:
        json.dump(documento, file, ensure_ascii=False, indent=2)
#Se crea la carpeta de salida y el archivo se nombra usando su doc_id. y json.dump() guarda toda la información del documento en JSON.

#main
def main():
    if not CORPUS_PATH.exists():
        print("\nERROR: La ruta del corpus no existe.")
        return
    if not CORPUS_PATH.is_dir():
        print("\nERROR: La ruta debe ser una carpeta.")
        return
    formatos_soportados = { ".pdf", ".json", ".csv", ".txt"}
    extensiones_imagen = {".jpg", ".jpeg", ".png", ".avif"}
    archivos = []
    for path in CORPUS_PATH.rglob("*"):
        if path.is_file():
            archivos.append(path)
    archivos.sort()
    print(f"\nArchivos encontrados: {len(archivos)}")
    prueba = input("¿Procesar solo 3 archivos de prueba? (s/n): ").strip().lower()
    if prueba == "s":
        archivos_prueba = []
        for path in archivos:
            if path.suffix.lower() in formatos_soportados:
                archivos_prueba.append(path)
        archivos = archivos_prueba[:3]
    procesados = 0
    vacios = 0
    errores = 0
    imagenes_pendientes = 0
    for path in archivos:
        extension = path.suffix.lower()
        if path.name !=".DS_Store":
            if extension in extensiones_imagen:
                imagenes_pendientes += 1
            elif extension in formatos_soportados:
                try:
                    documento = procesar_documento(path)
                    if documento is not None:
                        if not documento["texto"].strip():
                            vacios += 1
                            print( f"[vacio] {path.relative_to(CORPUS_PATH)}")
                        guardar_documento(documento)
                        procesados += 1
                        print(f"[procesado] {path.relative_to(CORPUS_PATH)}")
                except Exception as error:
                    errores += 1
                    print(f"[error] {path.relative_to(CORPUS_PATH)}")
                    print(error)
    print("\n" + "=" * 50)
    print("RESUMEN")
    print("=" * 50)
    print(f"Documentos procesados: {procesados}")
    print(f"Documentos vacios: {vacios}")
    print(f"Errores: {errores}")
    print(f"Imagenes pendientes: {imagenes_pendientes}")
if __name__ == "__main__":
    main()
#Se verifica que la ruta exista, busca todos los archivos del corpus y se hace un prueba pequeña con solo 3 archivos.
#Después identifica cuáles se pueden procesar, cuenta imágenes, vacíos y errores, guarda los documentos y muestra un resumen final.