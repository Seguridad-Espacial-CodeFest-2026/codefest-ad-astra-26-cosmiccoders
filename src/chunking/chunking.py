from pathlib import Path
import json


INPUT_PATH = Path("data/processed")
OUTPUT_PATH = Path("data/chunks")
MAX_PALABRAS = 200

#separar oraciones
def separar_oraciones(texto):
    oraciones = []
    oracion = ""
    for caracter in texto:
        oracion = oracion + caracter
        if caracter == "." or caracter == "?" or caracter == "!" or caracter == "\n":
            if oracion.strip():
                oraciones.append(oracion.strip())
            oracion = ""

    if oracion.strip():
        oraciones.append(oracion.strip())
    return oraciones
#Se recorre el texto carácter por carácter y se va formando cada oración.
#Cuando aparece ".", "?" o "!", se guarda la oración completa en una lista.


#creación de chunks
def crear_chunks(texto):
    oraciones = separar_oraciones(texto)
    chunks = []
    chunk_actual = ""
    for oracion in oraciones:
        texto_prueba = chunk_actual + " " + oracion
        cantidad_palabras = len(texto_prueba.split())
        if cantidad_palabras <= MAX_PALABRAS:
            chunk_actual = texto_prueba.strip()
        else:
            if chunk_actual:
                chunks.append(chunk_actual)
            chunk_actual = oracion
    if chunk_actual:
        chunks.append(chunk_actual)
    return chunks
#se recorren las oraciones y se van agregando a un chunk mientras no supere 200 palabras.
#si supera el límite, se guarda el chunk y se empieza uno nuevo sin cortar ninguna oración.


#procesar un documento
def procesar_documento(path):
    file = open(path, "r", encoding="utf-8")
    documento = json.load(file)
    file.close()
    texto = documento["texto"]
    resultado = []
    if texto != "":
        textos_chunks = crear_chunks(texto)
        posicion = 0
        for texto_chunk in textos_chunks:
            chunk_id = documento["doc_id"] + "-chunk-" + str(posicion)
            chunk = {"doc_id": documento["doc_id"],"chunk_id": chunk_id, "fuente": documento["fuente"],
                     "formato": documento["formato"], "fenomeno": documento["fenomeno"], "posicion": posicion, 
                     "num_palabras": len(texto_chunk.split()),"texto": texto_chunk}
            resultado.append(chunk)
            posicion = posicion + 1
    return resultado
#se abre cada documento JSON y se toma el texto que generó el extractor. Este texto se divide en chunks y cada uno se guarda con su identificador y datos del documento original.


#procesar todos los documentos.
def main():
    if not INPUT_PATH.exists():
        print("ERROR: No existe la carpeta data/processed")
        return
    if not OUTPUT_PATH.exists():
        OUTPUT_PATH.mkdir(parents=True)
    archivos = []
    for path in INPUT_PATH.glob("*.json"):
        archivos.append(path)
    archivos.sort()
    print("Documentos encontrados:", len(archivos))

    ruta_salida = OUTPUT_PATH / "chunks.jsonl"
    archivo_salida = open(ruta_salida, "w", encoding="utf-8")
    documentos_procesados = 0
    documentos_vacios = 0
    total_chunks = 0
    for path in archivos:
        chunks = procesar_documento(path)
        if len(chunks) > 0:
            documentos_procesados = documentos_procesados + 1
            for chunk in chunks:
                json.dump(chunk, archivo_salida, ensure_ascii=False)
                archivo_salida.write("\n")
                total_chunks = total_chunks + 1
        else:
            documentos_vacios = documentos_vacios + 1
    archivo_salida.close()

    print("\nRESUMEN")
    print("Documentos procesados:", documentos_procesados)
    print("Documentos vacios:", documentos_vacios)
    print("Chunks creados:", total_chunks)
    print("Archivo creado:", ruta_salida)

if __name__ == "__main__":
    main()
#se recorren todos los documentos procesados y cada uno se divide en chunks.Estos chunks se guardan en chunks.jsonl y al final se muestra un resumen.
