# Scripts — Orange Pi Voice Assistant

Scripts de apoyo para preparar datasets de voz (Piper TTS), verificar transcripciones y comparar modelos ONNX.

---

## Índice

| Script | Descripción |
|--------|-------------|
| [verificar_transcripciones.py](#verificar_transcripcionespy) | Verifica que el texto del CSV coincida con el audio (Whisper) |
| [comparar_voces_onnx.py](#comparar_voces_onnxpy) | Compara voces ONNX entre sí y con los WAV originales |
| [ogg_a_wav.py](#ogg_a_wavpy) | Convierte OGG a WAV (formato Piper: 22050 Hz, mono, 16-bit) |
| [txt_csv.py](#txt_csvpy) | Genera `metadata.csv` desde una carpeta de archivos .txt |
| [listar.py](#listarpy) | Lista pares .ogg + .txt en una carpeta |
| [detectar_txt_vacio.py](#detectar_txt_vaciopy) | Detecta archivos .txt vacíos |
| [copiar_a.py](#copiar_apy) | Copia pares .ogg + .txt renombrados (clip_0001, clip_0002…) |
| [main.py](#mainpy) | Plantilla de PyCharm (sin uso en el flujo del proyecto) |

---

## verificar_transcripciones.py

**Archivo:** [verificar_transcripciones.py](verificar_transcripciones.py)

Verifica que el texto de `metadata.csv` coincida con lo que dice el audio. Usa **Whisper** (faster-whisper) para transcribir cada WAV y compara con el CSV. Genera un reporte JSON de discrepancias y permite modo interactivo para escuchar y corregir.

**Requisitos:** `faster-whisper` (y dependencias de Whisper).

**Uso básico:**

```bash
python verificar_transcripciones.py --wavs /ruta/a/wavs --csv /ruta/a/metadata.csv
```

**Opciones útiles:**

| Opción | Descripción |
|--------|-------------|
| `--wavs` | **(Requerido)** Carpeta con los archivos .wav |
| `--csv` | **(Requerido)** Archivo metadata.csv (formato: `nombre|texto`) |
| `--revisar` | Modo interactivo: escuchar y corregir discrepancias |
| `--modelo` | Modelo Whisper (default: `medium`) |
| `--idioma` | Código de idioma (default: `es`) |
| `--umbral` | Umbral de similitud 0–1 (default: 0.85) |
| `--reporte` | Nombre del archivo de reporte JSON (default: `reporte_verificacion.json`) |
| `--desde-reporte` | Usar un reporte ya generado (sin volver a transcribir) |
| `--device` | `cpu`, `cuda` o `auto` |

**Ejemplo con revisión interactiva:**

```bash
python verificar_transcripciones.py --wavs ./wavs --csv ./metadata.csv --revisar
```

---

## comparar_voces_onnx.py

**Archivo:** [comparar_voces_onnx.py](comparar_voces_onnx.py)

Compara varias voces ONNX de Piper entre sí y con los audios originales. Sintetiza las mismas frases con cada modelo y genera un `index.html` para escuchar y comparar en el navegador.

**Requisitos:** Piper instalado y accesible (`python3 -m piper` o `piper`), y que los modelos ONNX tengan su `.json` correspondiente.

**Configuración:** Editar la sección de configuración al inicio del script (rutas a WAVs, CSV, carpeta de ONNX, carpeta de salida, etc.). Luego se puede ejecutar sin argumentos:

```bash
python comparar_voces_onnx.py
```

**Opciones por terminal (sobrescriben la config del script):**

| Opción | Descripción |
|--------|-------------|
| `--wavs` | Carpeta con los WAV originales |
| `--csv` | Archivo metadata.csv (`nombre|texto`) |
| `--onnx` | Uno o más archivos .onnx |
| `--onnx-dir` | Carpeta con varios .onnx |
| `--output-dir` | Carpeta de salida |
| `--max-frases` | Número máximo de frases a comparar |
| `--aleatorio` | Elegir frases al azar en lugar de las primeras N |
| `--merge` | Generar un WAV concatenado por frase (original + cada voz) |
| `--solo-entre-voces` | Solo una misma frase con cada ONNX (sin WAVs originales) |
| `--frase` | Texto a sintetizar en modo `--solo-entre-voces` |
| `--piper-cmd` | Comando para invocar Piper |

**Salida:** Carpeta con WAVs por frase/voz y `index.html` para reproducir y comparar.

---

## ogg_a_wav.py

**Archivo:** [ogg_a_wav.py](ogg_a_wav.py)

Convierte archivos **.ogg** a **.wav** en el formato que espera Piper: 22050 Hz, mono, 16-bit. Útil cuando el dataset original está en OGG.

**Requisitos:** `pydub` (y ffmpeg en el sistema para que pydub pueda leer OGG).

**Uso:** Editar las constantes al inicio del script:

- `INPUT_DIR`: carpeta donde están los .ogg  
- `OUTPUT_DIR`: carpeta donde se escribirán los .wav  

Luego ejecutar:

```bash
python ogg_a_wav.py
```

Los archivos se generan con el mismo nombre base que el .ogg (solo cambia la extensión).

---

## txt_csv.py

**Archivo:** [txt_csv.py](txt_csv.py)

Genera un **metadata.csv** a partir de una carpeta llena de archivos **.txt**. Cada .txt se lee (varias codificaciones: UTF-8, UTF-16, latin-1), se limpia el texto y se escribe una línea `nombre|texto` en el CSV (sin cabecera), listo para Piper.

**Uso:** Editar al inicio del script:

- `INPUT_DIR`: carpeta que contiene los .txt  
- `OUTPUT_PATH`: ruta del archivo `metadata.csv` de salida  

Luego:

```bash
python txt_csv.py
```

---

## listar.py

**Archivo:** [listar.py](listar.py)

Recorre una carpeta (y subcarpetas) buscando archivos **.ogg** y comprueba si existe el **.txt** con el mismo nombre. Muestra cuántos tienen par .ogg+.txt y cuántos .ogg no tienen .txt.

**Uso:** Cambiar la variable `root` al inicio (ruta de la carpeta raíz) y ejecutar:

```bash
python listar.py
```

---

## detectar_txt_vacio.py

**Archivo:** [detectar_txt_vacio.py](detectar_txt_vacio.py)

Lista los archivos **.txt** que están vacíos (o solo con espacios/saltos de línea) en una carpeta. Útil para limpiar el dataset antes de generar el metadata.

**Uso:** Editar `TXT_DIR` al inicio con la ruta de la carpeta que contiene los .txt, luego:

```bash
python detectar_txt_vacio.py
```

---

## copiar_a.py

**Archivo:** [copiar_a.py](copiar_a.py)

Copia todos los pares **.ogg + .txt** desde una carpeta (y subcarpetas) a una carpeta destino, renombrando los archivos de forma secuencial: `clip_0001.ogg`, `clip_0001.txt`, `clip_0002.ogg`, etc.

**Uso:** Editar al inicio:

- `root_in`: carpeta donde están las subcarpetas con .ogg y .txt  
- `root_out`: carpeta destino  

Luego:

```bash
python copiar_a.py
```

Solo se copian los .ogg que tienen .txt asociado con el mismo nombre.

---

## main.py

**Archivo:** [main.py](main.py)

Plantilla por defecto de PyCharm (`print_hi('PyCharm')`). No forma parte del flujo de preparación de datos ni de Piper; se puede ignorar o eliminar.

---

## Flujo típico (dataset → Piper)

Orden sugerido para preparar un dataset y entrenar una voz:

1. **Origen en OGG + TXT:** usar [listar.py](listar.py) y [detectar_txt_vacio.py](detectar_txt_vacio.py) para revisar; [copiar_a.py](copiar_a.py) para unificar y renombrar si hace falta.
2. **Convertir a WAV:** [ogg_a_wav.py](ogg_a_wav.py).
3. **Generar metadata:** [txt_csv.py](txt_csv.py).
4. **Verificar transcripciones:** [verificar_transcripciones.py](verificar_transcripciones.py) (y opcionalmente `--revisar` para corregir).
5. **Entrenar** siguiendo la guía en [../docs/GUIA_ENTRENAMIENTO_PIPER.md](../docs/GUIA_ENTRENAMIENTO_PIPER.md).
6. **Comparar voces ONNX:** [comparar_voces_onnx.py](comparar_voces_onnx.py) para elegir el mejor checkpoint exportado.
