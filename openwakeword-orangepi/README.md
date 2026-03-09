# Probar modelos Open Wake Word (TFLite / ONNX) en Orange Pi

Guía para ejecutar modelos entrenados con **openWakeWord** en una Orange Pi (RK3588).

## Requisitos

- Orange Pi con RK3588 (el kernel `6.1.43-rockchip-rk3588`).
- Python 3.8+.
- Modelos exportados: `.tflite` y/o `.onnx` (generados en el entrenamiento).

## 1. Entorno e instalación

En la Orange Pi. Los comandos pueden ejecutarse desde **cualquier directorio**; la carpeta actual no afecta al resultado.

- **Recomendado para este proyecto:** venv **dentro del repositorio** (opción B). El entorno queda junto al código, se puede versionar la lista de dependencias (`pip freeze > requirements.txt`) y al clonar el repo basta con `python3 -m venv .venv` y `pip install -r requirements.txt`.
- **Alternativa:** venv en **home** (`~/oww-venv`, opción A). Útil si se usa el mismo entorno desde varios proyectos o si se prefiere no tocar el repo.

```bash
# Dependencias del sistema (audio para micrófono)
sudo apt update
sudo apt install -y python3-pip python3-venv portaudio19-dev libspeexdsp-dev

# Crear y activar entorno virtual
# Opción A: en home (desde cualquier carpeta)
python3 -m venv ~/oww-venv
source ~/oww-venv/bin/activate

# Opción B: dentro del repositorio (ejecutar desde la raíz del repo)
# python3 -m venv .venv
# source .venv/bin/activate

# Instalar openWakeWord (trae onnxruntime; en Linux también tflite-runtime)
pip install --upgrade pip
pip install openwakeword pyaudio

# Supresión de ruido Speex (recomendado en entornos con ruido de fondo).
# En ARM64 (Orange Pi) hay que instalar el .whl del release; para Python 3.10:
# pip install https://github.com/dscripka/openWakeWord/releases/download/v0.1.1/speexdsp_ns-0.1.2-cp310-cp310-linux_aarch64.whl
# Otras versiones de Python: ver assets en https://github.com/dscripka/openWakeWord/releases/tag/v0.1.1 (cp37, cp38, cp39, cp310).

# Si tflite-runtime falla en ARM (algunas versiones), usar solo ONNX:
# pip install openwakeword onnxruntime pyaudio
```

En las secciones siguientes los ejemplos usan `source ~/oww-venv/bin/activate` (opción A). Si se eligió la opción B, activar el entorno con `source .venv/bin/activate` en su lugar.

**Nota:** En ARM64 (Orange Pi 5/5+), `onnxruntime` suele ir bien. Si `tflite-runtime` da problemas de versión o arquitectura, utilizar solo el modelo ONNX.

## 2. Descargar modelos de recursos (preprocesador)

El paquete openWakeWord no incluye en pip el modelo de preprocesado de audio (`melspectrogram.onnx`). Hay que descargarlo **una vez** después de instalar:

```bash
source ~/oww-venv/bin/activate   # o source .venv/bin/activate si se usó opción B
python3 -c "import openwakeword; openwakeword.utils.download_models()"
```

Se descargan los recursos en `openwakeword/resources/models/`. Sin este paso, la inferencia falla con un error del tipo «melspectrogram.onnx failed. File doesn't exist».

## 3. Micrófono en Orange Pi 5 Ultra (main mic)

En la Orange Pi 5 Ultra el micrófono interno requiere una configuración concreta del mezclador ALSA (Line 2 / PGA Mux 1); si no, la captura suele ser solo ruido. La documentación y el script de configuración están en:

**→ [Orangepi5ultra_OnBoardMic_Config](../Orangepi5ultra_OnBoardMic_Config/README.md)**

Resumen rápido (una vez por sesión, o configurar persistencia según el README de esa carpeta):

1. Ejecutar `../Orangepi5ultra_OnBoardMic_Config/setup_mic_main.sh`.
2. Listar dispositivos de entrada y anotar el índice del ES8388 (main mic):  
   `python3 test_wakeword_orangepi.py --model path/to/modelo.onnx --framework onnx --list-devices`
3. Usar ese índice con `--device N` (en muchas instalaciones el main mic es el índice **1**).

```bash
python3 test_wakeword_orangepi.py --model path/to/modelo.onnx --framework onnx --device 1 --speex
```

## 4. Opciones del script test_wakeword_orangepi.py

| Opción | Descripción |
|--------|-------------|
| `--model RUTA` | **(Obligatorio)** Ruta al modelo `.onnx` o `.tflite`. |
| `--framework {onnx o tflite}` | Motor de inferencia. Por defecto: `onnx`. |
| `--wav RUTA` | Usar archivo WAV en lugar del micrófono; se convierte a 16 kHz mono 16-bit si hace falta. |
| `--chunk_size N` | Muestras por frame (80 ms = 1280 a 16 kHz). Por defecto: 1280. |
| `--threshold X` | Umbral de detección (0–1). Por defecto: 0.5. |
| `--speex` | Activar supresión de ruido Speex (solo con micrófono; en ARM64 requiere el .whl de speexdsp_ns). |
| `--test` | En modo micrófono: guardar el audio capturado en `/tmp/test_audio.wav` al salir (Ctrl+C). |
| `--list-devices` | Listar dispositivos de entrada (micrófonos) y salir; muestra el índice para usar con `--device`. |
| `--device N` | Índice del dispositivo de entrada. En Orange Pi 5 Ultra el micrófono interno (ES8388) suele ser **1**; si no se indica, se usa el dispositivo por defecto del sistema (que puede no ser el main mic). |

## 5. Probar con el modelo ONNX

```bash
source ~/oww-venv/bin/activate
python3 test_wakeword_orangepi.py \
  --model path/to/modelo.onnx \
  --framework onnx \
  --speex
```

## 6. Probar con el modelo TFLite

```bash
source ~/oww-venv/bin/activate
python3 test_wakeword_orangepi.py \
  --model path/to/modelo.tflite \
  --framework tflite \
  --speex
```

## 7. Probar con un WAV (sin micrófono)

El audio debe ser **16 kHz, mono, 16-bit PCM** (el script puede convertir otros formatos automáticamente):

```bash
python3 test_wakeword_orangepi.py \
  --model path/to/modelo.onnx \
  --framework onnx \
  --wav path/to/audio.wav
```

## 8. Uso desde Python (integrar en un proyecto)

```python
from openwakeword.model import Model
import numpy as np

# Con ONNX y supresión de ruido Speex (recomendado con micrófono)
model = Model(
    wakeword_models=["/ruta/al/modelo.onnx"],
    inference_framework="onnx",
    enable_speex_noise_suppression=True
)

# Con TFLite
# model = Model(
#     wakeword_models=["/ruta/al/modelo.tflite"],
#     inference_framework="tflite",
#     enable_speex_noise_suppression=True
# )

# Audio: 16-bit, 16 kHz, mono; trozos de 80 ms (1280 muestras) o múltiplos
frame = np.frombuffer(audio_chunk, dtype=np.int16)
prediction = model.predict(frame)

# prediction es un dict: nombre_modelo -> score (0–1)
for name, score in prediction.items():
    if score > 0.5:
        print(f"Wake word detectada: {name} = {score:.3f}")
```

## 9. Parámetros útiles

- **Supresión de ruido (Speex):** recomendada con micrófono en entornos con ruido. Disponible en Linux (x86_64 y Arm64). Requiere `libspeexdsp-dev` y, en su caso, el paquete Python del [release v0.1.1](https://github.com/dscripka/openWakeWord/releases/tag/v0.1.1). Se activa con:
  ```python
  model = Model(
      wakeword_models=["modelo.onnx"],
      inference_framework="onnx",
      enable_speex_noise_suppression=True
  )
  ```
- **Umbral:** por defecto 0.5; se puede probar 0.4–0.6 según falsos positivos/negativos.
- **VAD:** para reducir falsos positivos con ruido no vocal:
  ```python
  model = Model(wakeword_models=["modelo.onnx"], inference_framework="onnx", vad_threshold=0.5)
  ```
  Speex y VAD pueden combinarse:
  ```python
  model = Model(
      wakeword_models=["modelo.onnx"],
      inference_framework="onnx",
      enable_speex_noise_suppression=True,
      vad_threshold=0.5
  )
  ```

## 10. Si algo falla

- **«melspectrogram.onnx failed. File doesn't exist»:** ejecutar el paso 2 (descargar modelos de recursos) con `openwakeword.utils.download_models()`.
- **Error con tflite-runtime en ARM:** utilizar solo el `.onnx` y `--framework onnx`.
- **Micrófono no encontrado / no se escucha nada (Orange Pi 5 Ultra):** (1) Ejecutar `./setup_mic_main.sh` en [Orangepi5ultra_OnBoardMic_Config](../Orangepi5ultra_OnBoardMic_Config/) para configurar el main mic (PGA Mux 1). (2) Listar dispositivos con `--list-devices` y anotar el índice del ES8388. (3) Usar ese índice con `--device N` (p. ej. `--device 1`). Ver [Orangepi5ultra_OnBoardMic_Config](../Orangepi5ultra_OnBoardMic_Config/README.md).
- **El modelo no detecta:** comprobar que el WAV sea 16 kHz mono 16-bit y que el wake word coincida con el utilizado en el entrenamiento.

## 11. Referencias

- [openWakeWord](https://github.com/dscripka/openWakeWord)
- [Uso y recomendaciones](https://github.com/dscripka/openWakeWord#recommendations-for-usage)
- [Micrófonos alternativos para wake word y asistente de voz](../docs/microfonos-voice-assistant.md) (compactos, económicos, usados en Home Assistant y proyectos similares).
