# Guía de entrenamiento Piper TTS (fine-tuning) — personal

Esta guía recopila los pasos que funcionan para entrenar una voz personalizada con Piper TTS en Arch Linux (Python 3.10, GPU NVIDIA), desde el dataset hasta el modelo ONNX para Orange Pi.

---

## Requisitos previos

- **Sistema:** Arch Linux (o similar)
- **GPU:** NVIDIA (probado con RTX 3060 12 GB)
- **Dataset:** carpeta con WAVs (22050 Hz, mono, 16-bit) y `metadata.csv` con formato `nombre|texto` (sin cabecera, una línea por archivo). Las transcripciones deben coincidir con el audio; se pueden verificar con el script `verificar_transcripciones.py` y Whisper.

---

## 1. Dependencias del sistema

Instalar espeak-ng, Python y Git:

```bash
sudo pacman -S espeak-ng python git
```

Opcional: para descargar checkpoints desde Hugging Face sin Git LFS se puede usar `huggingface_hub`. Instalarlo más adelante desde el venv de Piper (recomendado) o desde el sistema:

- **Desde el venv de Piper:** activar el venv y ejecutar `python -m pip install huggingface_hub`.
- **Desde el sistema:** `python -m pip install huggingface_hub --break-system-packages`.

---

## 2. Entorno Python 3.10 y Piper

Piper y sus dependencias funcionan de forma estable con **Python 3.10**. Con 3.11 o superior suelen aparecer incompatibilidades (piper-phonemize, pytorch-lightning, torch<2).

### 2.1 Instalar Python 3.10 con uv

Instalar uv si no está disponible (`sudo pacman -S uv`) y luego descargar Python 3.10:

```bash
uv python install 3.10
```

### 2.2 Clonar Piper y crear el venv

Clonar el repositorio, entrar en `piper/src/python`, eliminar un `.venv` previo si existe, y crear un venv con Python 3.10:

```bash
cd ~/Downloads
git clone https://github.com/rhasspy/piper.git
cd piper/src/python
rm -rf .venv
uv venv --python 3.10 .venv
source .venv/bin/activate
python --version   # debe mostrar Python 3.10.x
```

### 2.3 Instalar pip y dependencias compatibles

Dentro del venv activado:

```bash
python -m ensurepip --upgrade
python -m pip install "pip<24.1" "numpy<2" wheel setuptools
```

- `pip<24.1`: evita errores de metadata con pytorch-lightning 1.7.x.
- `numpy<2`: evita fallos con módulos compilados contra NumPy 1.x.

### 2.4 Instalar PyTorch 1.x con CUDA

Piper requiere `torch<2`. Usar el índice oficial de PyTorch:

```bash
python -m pip install --index-url https://download.pytorch.org/whl/cu117 "torch==1.13.1+cu117"
```

### 2.5 Instalar piper-phonemize y pytorch-lightning

```bash
python -m pip install "piper-phonemize==1.1.0" "pytorch-lightning==1.7.7"
python -m pip install "torchmetrics<1.0"
python -m pip install six
```

- `torchmetrics<1.0`: compatible con pytorch-lightning 1.7.
- `six`: requerido por `torch.utils.tensorboard`.

### 2.6 Instalar Piper en modo editable

Desde `piper/src/python` con el venv activado:

```bash
cd ~/Downloads/piper/src/python
python -m pip install -e .
```

### 2.7 Compilar la extensión de alineamiento

Ejecutar el script incluido en el repo:

```bash
bash build_monotonic_align.sh
```

---

## 3. Preparar el dataset

### 3.1 Estructura

Piper espera un directorio que contenga `metadata.csv` y una carpeta `wav/` con los archivos de audio. El `metadata.csv` tiene una línea por archivo con formato `nombre|texto` (sin cabecera); el nombre corresponde al WAV sin extensión (ej. `clip_0001` → `wav/clip_0001.wav`).

Si los audios están en una carpeta llamada `wavs/`, se puede crear un enlace simbólico:

```bash
cd /ruta/al/dataset
ln -s wavs wav
```

### 3.2 Preprocesamiento

Con el venv activado, ejecutar el módulo de preprocesamiento sustituyendo `/ruta/al/dataset` por la ruta real del dataset:

```bash
cd ~/Downloads/piper/src/python
source .venv/bin/activate

python3 -m piper_train.preprocess \
  --language es \
  --input-dir /ruta/al/dataset \
  --output-dir /ruta/al/dataset/training \
  --dataset-format ljspeech \
  --single-speaker \
  --sample-rate 22050
```

Se generan `training/config.json`, `training/dataset.jsonl` y los archivos `.pt` necesarios.

---

## 4. Descargar checkpoint base (español, single-speaker)

Git LFS del repositorio de checkpoints en Hugging Face puede dar errores por objetos faltantes. Es más fiable usar la API de Python (`huggingface_hub`):

```bash
cd ~/Downloads/piper/src/python
source .venv/bin/activate
python -c "
from huggingface_hub import snapshot_download
snapshot_download(
    repo_id='rhasspy/piper-checkpoints',
    repo_type='dataset',
    local_dir='/home/pepin/Downloads/piper-checkpoint',
    allow_patterns=['es/es_ES/davefx/medium/*']
)
"
```

Ajustar `local_dir` a la ruta de destino. **davefx** es single-speaker; **sharvard** es multi-speaker y produce error al cargar si el dataset es single-speaker.

Comprobar el nombre del archivo `.ckpt` generado:

```bash
ls /home/pepin/Downloads/piper-checkpoint/es/es_ES/davefx/medium/
```

Suele ser de la forma `epoch=5629-step=1605020.ckpt`. Esa ruta completa se usará en el paso de entrenamiento.

---

## 5. Entrenar (fine-tuning)

### 5.1 Comando base

El valor de `max_epochs` debe ser **mayor** que la época del checkpoint que se carga (p. ej. davefx está en época 5629; usar 7000 permite entrenar unas ~1400 épocas más):

```bash
cd ~/Downloads/piper/src/python
source .venv/bin/activate

python3 -m piper_train \
  --dataset-dir /ruta/al/dataset/training \
  --accelerator gpu \
  --devices 1 \
  --batch-size 16 \
  --validation-split 0.0 \
  --num-test-examples 0 \
  --max_epochs 7000 \
  --resume_from_checkpoint /ruta/completa/al/checkpoint.ckpt \
  --checkpoint-epochs 50 \
  --precision 32
```

Sustituir:

- `--dataset-dir`: carpeta `training` generada en el preprocesamiento.
- `--resume_from_checkpoint`: ruta completa al `.ckpt` descargado (ej. `.../piper-checkpoint/es/es_ES/davefx/medium/epoch=5629-step=1605020.ckpt`).

### 5.2 Si al reanudar aparece “CUDA out of memory”

Si el entrenamiento se interrumpe y al reanudar con el mismo comando aparece OOM, reducir el batch size a 8 y usar como checkpoint el **último guardado** en la carpeta de entrenamiento:

```bash
ls /ruta/al/dataset/training/lightning_logs/version_1/checkpoints/
```

Reanudar indicando ese checkpoint:

```bash
  --batch-size 8 \
  --resume_from_checkpoint /ruta/al/dataset/training/lightning_logs/version_1/checkpoints/epoch=XXXX-step=YYYYYY.ckpt \
```

### 5.3 Monitorear con TensorBoard

En otra terminal, con el mismo venv activado, instalar tensorboard si falta y lanzarlo sobre la carpeta de logs:

```bash
source ~/Downloads/piper/src/python/.venv/bin/activate
pip install tensorboard   # si no está instalado
tensorboard --logdir /ruta/al/dataset/training/lightning_logs
```

Abrir `http://localhost:6006` → pestaña **Scalars** y revisar `loss_disc_all` y `loss_gen_all`. Cuando las curvas se estabilicen (sobre todo la del generador), se puede detener el entrenamiento (Ctrl+C) o dejarlo hasta `max_epochs`; no es obligatorio llegar a 7000.

### 5.4 Gestión de los checkpoints (.ckpt) — conservar todos sin sobrescribir

Con `--checkpoint-epochs 50` el entrenamiento escribe un nuevo archivo `.ckpt` cada 50 épocas en `training/lightning_logs/version_1/checkpoints/`. El objetivo aquí es **conservar todos** esos checkpoints (sin sobrescribir), sin importar el espacio en disco.

**Comportamiento por defecto**

Según la versión de Piper y de PyTorch Lightning, el callback de checkpoints puede:
- **Acumular**: cada guardado crea un archivo nuevo (p. ej. `epoch=50-step=….ckpt`, `epoch=100-step=….ckpt`, …) y todos permanecen en la carpeta.
- **Sobrescribir**: cada nuevo guardado reemplaza al anterior y solo queda un `.ckpt`.

Conviene comprobar en la primera corrida: listar la carpeta `checkpoints/` cada cierto tiempo (`ls -la .../checkpoints/`) y ver si aparecen varios `.ckpt` o solo uno que se actualiza.

**Garantizar que se conserven todos (sin sobrescribir)**

- No borrar la carpeta `checkpoints/` durante el entrenamiento.
- Si la instalación sobrescribe (solo se mantiene el último), hay que cambiar la configuración del callback en el código de Piper. En `piper/src/python/piper_train/__main__.py` (o donde se configure el `Trainer`), localizar el `ModelCheckpoint` de PyTorch Lightning y asegurarse de que **no** use `save_top_k=1`. Para conservar todos los checkpoints, usar `save_top_k=-1` (en Lightning, -1 significa «guardar todos»). Si el callback no tiene `save_top_k`, añadir `save_top_k=-1`. Con eso, cada 50 épocas se escribe un `.ckpt` nuevo y ninguno se elimina.
- Alternativa si no se quiere tocar el código: un script externo que vigile la carpeta `checkpoints/` y, cada vez que aparezca o se modifique un `.ckpt`, lo copie a una carpeta de respaldo (p. ej. `checkpoints_backup/`) con un nombre único (p. ej. añadiendo timestamp). Así se conservan copias de todos aunque Piper sobrescriba el archivo en su carpeta.


---

## 6. Exportar a ONNX

Para usar el modelo en el Orange Pi, exportar el checkpoint elegido a ONNX y copiar el `config.json` con el mismo nombre base:

```bash
cd ~/Downloads/piper/src/python
source .venv/bin/activate

python3 -m piper_train.export_onnx \
  /ruta/al/dataset/training/lightning_logs/version_1/checkpoints/MEJOR_CHECKPOINT.ckpt \
  /ruta/al/dataset/mi_voz.onnx

cp /ruta/al/dataset/training/config.json /ruta/al/dataset/mi_voz.onnx.json
```

Sustituir `MEJOR_CHECKPOINT.ckpt` por el checkpoint que se quiera usar (p. ej. el último o el que suene mejor en pruebas). Son necesarios los dos archivos: `mi_voz.onnx` y `mi_voz.onnx.json`.

---

## 7. Uso en Orange Pi

Copiar `mi_voz.onnx` y `mi_voz.onnx.json` al Orange Pi. Instalar `piper-tts` y sintetizar desde texto:

```bash
pip install piper-tts
echo "Texto de prueba." | piper -m /ruta/a/mi_voz.onnx --output_file salida.wav
```

---

## Resumen de versiones que funcionan

| Componente        | Versión que funciona |
|-------------------|----------------------|
| Python            | 3.10                 |
| pip               | <24.1                |
| numpy             | <2                   |
| torch             | 1.13.1+cu117         |
| piper-phonemize   | 1.1.0                |
| pytorch-lightning | 1.7.7                |
| torchmetrics      | <1.0                 |
| Checkpoint base   | single-speaker (ej. davefx) |
| max_epochs        | Mayor que la época del checkpoint (ej. 7000) |
| batch_size        | 16; si OOM al reanudar, 8 |

---

## Si algo falla

- **“piper-phonemize no encontrado”** → Usar Python 3.10 e instalar `piper-phonemize==1.1.0` antes de `pip install -e .`.
- **“Unexpected key(s) in state_dict”** → El checkpoint es multi-speaker; usar uno single-speaker (davefx o ald).
- **“current_epoch=XXXX, but Trainer(max_epochs=YYYY)”** → Usar `--max_epochs` mayor que XXXX.
- **CUDA OOM al reanudar** → Usar `--batch-size 8` y `--resume_from_checkpoint` con el último `.ckpt` de la carpeta `checkpoints/`.
- **NumPy / torchmetrics** → Mantener `numpy<2` y `torchmetrics<1.0` en el venv de Piper.
