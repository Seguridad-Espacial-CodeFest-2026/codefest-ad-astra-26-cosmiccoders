# codefest-ad-astra-26-cosmiccoders

Implementación de una base de conocimiento vectorial con FAISS para el análisis de fenómenos aeroespaciales y estratégicos. Proyecto para la Etapa 1 del CODEFEST AD ASTRA 2026 (Fenómeno 2 — Seguridad Espacial y Órbita Baja Terrestre).

## Requisitos

- Python 3.11+ (probado con 3.14).
- Conexión a internet la primera vez que se corre `embedder.py` o `searcher.py`: descargan el modelo `paraphrase-multilingual-MiniLM-L12-v2` desde Hugging Face (~470 MB) y lo cachean en `~/.cache/huggingface`. Las siguientes ejecuciones no vuelven a descargarlo.
- El corpus del CODEFEST descargado localmente, con esta estructura de carpetas exacta dentro de la carpeta raíz que se te pida:

```
<carpeta_raiz_corpus>/
├── F1_IA_y_Capacidades_Estrategicas/
├── F2_Seguridad_Entorno_Espacial/
└── F3_Dinamicas_Territoriales/
```

## Instalación

```bash
git clone https://github.com/Seguridad-Espacial-CodeFest-2026/codefest-ad-astra-26-cosmiccoders.git
cd codefest-ad-astra-26-cosmiccoders

python3 -m venv .venv
source .venv/bin/activate   # en Windows: .venv\Scripts\activate

pip install -r requirements.txt
```

Todos los comandos siguientes se corren desde la raíz del repo, con el entorno virtual activado.

## Dependencias

Todo lo que se necesita está en `requirements.txt` y se instala con el comando de arriba. Esto es lo que trae cada una y para qué se usa:

| Paquete | Para qué se usa |
|---|---|
| `pymupdf` | Extraer texto de los PDF del corpus (`extractor.py`) |
| `pandas` | Leer y procesar los archivos `.csv` del corpus (`extractor.py`) |
| `numpy` | Manejo de los vectores de embeddings (`embedder.py`, `indexer.py`, `searcher.py`) |
| `sentence-transformers` | Generar los embeddings de cada chunk y de cada consulta (`embedder.py`, `searcher.py`) |
| `faiss-cpu` | Construir y consultar el índice vectorial (`indexer.py`, `searcher.py`) |
| `python-dateutil`, `pytz`, `six`, `tzdata` | Dependencias internas de `pandas` |

**Importante:** `sentence-transformers` instala automáticamente `torch` (PyTorch) como dependencia — no está en `requirements.txt` como línea aparte, pero `pip install` lo baja solo. Es el paquete más pesado de la instalación (varios cientos de MB), así que la primera instalación puede tardar unos minutos según tu conexión.

No hace falta instalar nada a nivel de sistema operativo (no se usa OCR/Tesseract en esta versión, solo librerías de Python).

## Pipeline: cómo ejecutar todo en orden

El proyecto está dividido en 4 etapas independientes. Cada una lee lo que dejó la anterior en la carpeta `data/` y escribe su propio resultado ahí. Hay que correrlas en este orden:

### 1. Extracción — `src/extract/extractor.py`

Lee los documentos crudos del corpus (`.pdf`, `.json`, `.csv`, `.txt`) y los convierte a texto plano limpio.

```bash
python src/extract/extractor.py
```

Es interactivo: te va a pedir

- la ruta de la carpeta raíz del corpus (la que contiene `F1_...`, `F2_...`, `F3_...`)
- si quieres modo prueba (solo 3 archivos por fenómeno, útil para verificar que todo corre antes de procesar el corpus completo)

Salida: un `.json` por documento en `data/processed/`, con `doc_id`, `fuente`, `formato`, `fenomeno` y `texto`.

> Nota: los formatos `.jpg`, `.jpeg`, `.png`, `.avif` se cuentan como "imágenes pendientes" pero todavía no se procesan (no hay OCR implementado en esta versión).

### 2. Chunking — `src/chunking/chunking.py`

Divide el texto de cada documento en fragmentos (chunks) de máximo 200 palabras, sin cortar oraciones.

```bash
python src/chunking/chunking.py
```

Requiere que `data/processed/` ya exista (paso 1). Salida: `data/chunks/chunks.jsonl`, con un chunk por línea (`chunk_id`, `doc_id`, `fuente`, `formato`, `fenomeno`, `posicion`, `num_palabras`, `texto`).

### 3. Embeddings — `src/embed/embedder.py`

Genera el vector de cada chunk usando el modelo `paraphrase-multilingual-MiniLM-L12-v2` (sentence-transformers).

```bash
python src/embed/embedder.py
```

Requiere `data/chunks/chunks.jsonl` (paso 2). Salida:
- `data/embeddings/embeddings.npy` — matriz de vectores
- `data/embeddings/metadata.jsonl` — metadata de cada chunk, en el mismo orden que la matriz

### 4. Indexación — `src/index/indexer.py`

Construye el índice FAISS a partir de los embeddings.

```bash
python src/index/indexer.py
```

Requiere `data/embeddings/embeddings.npy` (paso 3). Normaliza los vectores (L2) y crea un `IndexFlatIP` (equivalente a similitud coseno). Salida: `data/indexes/index.faiss`.

### 5. Búsqueda / prueba — `src/search/searcher.py`

Consola interactiva para probar el índice con preguntas en lenguaje natural.

```bash
python src/search/searcher.py
```

Carga el índice y la metadata, y te deja escribir preguntas; devuelve el top 5 de chunks más similares con su score, fuente y fenómeno. Escribe `salir` para terminar.

## Resumen rápido (todo en una corrida)

```bash
python src/extract/extractor.py
python src/chunking/chunking.py
python src/embed/embedder.py
python src/index/indexer.py
python src/search/searcher.py
```

## Estructura de `data/` generada (no se versiona, está en `.gitignore`)

```
data/
├── raw/            (opcional, no usado por el pipeline)
├── processed/       ← salida de extractor.py
├── chunks/          ← salida de chunking.py
├── embeddings/       ← salida de embedder.py
└── indexes/          ← salida de indexer.py
```

## Pendiente frente al enunciado oficial

Esta versión cubre la extracción, el chunking y la búsqueda vectorial básicas, pero todavía faltan piezas exigidas por las bases del CODEFEST para la entrega final de Etapa 1:

- `doc_id` oficial tomado de `Indice_Datos_Codefest.xlsx` (ahora mismo se genera con un hash propio).
- Un script `generador.py` con la interfaz de línea de comandos exacta que pide el enunciado (`--consultas`, `--base-vectorial`, `--salida`) que devuelva, por cada consulta, exactamente 3 documentos y 10 fragmentos (≤250 palabras) en el formato de salida oficial.
- Carpeta final `base_vectorial/` con el índice y metadata empaquetados según el esquema pedido.
- `informe_tecnico.pdf`.
