#!/usr/bin/env python3
"""
Script para probar modelos Open Wake Word (.tflite o .onnx) en Orange Pi.

Uso básico:
  python test_wakeword_orangepi.py --model ruta/modelo.onnx --framework onnx
  python test_wakeword_orangepi.py --model ruta/modelo.onnx --framework onnx --wav audio.wav

En Orange Pi 5 Ultra suele ser necesario indicar el dispositivo de entrada con --device N
(primero ejecutar con --list-devices para ver el índice del micrófono ES8388; a menudo es 1).

Opciones:
  --model RUTA         (obligatorio) Ruta al modelo .onnx o .tflite.
  --framework {onnx|tflite}
                        Motor de inferencia. Por defecto: onnx.
  --wav RUTA           Usar archivo WAV en lugar del micrófono. Se convierte a 16 kHz mono 16-bit si hace falta.
  --chunk_size N       Muestras por frame (80 ms = 1280 a 16 kHz). Por defecto: 1280.
  --threshold X        Umbral de detección entre 0 y 1. Por defecto: 0.5.
  --speex              Activar supresión de ruido Speex (solo con micrófono; requiere speexdsp_ns en ARM64).
  --test               En modo micrófono: guardar lo capturado en /tmp/test_audio.wav al salir (Ctrl+C).
  --list-devices       Listar dispositivos de entrada y salir. Usar el índice mostrado con --device.
  --device N           Índice del dispositivo de entrada (micrófono). En Orange Pi 5 Ultra el main mic suele ser 1.
"""
import argparse
import sys

try:
    import numpy as np
    from openwakeword.model import Model
except ImportError:
    print("Instala dependencias: pip install openwakeword pyaudio numpy")
    sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Probar wake word en Orange Pi")
    parser.add_argument("--model", required=True, help="Ruta al modelo .onnx o .tflite")
    parser.add_argument(
        "--framework",
        choices=["onnx", "tflite"],
        default="onnx",
        help="Motor de inferencia (default: onnx)",
    )
    parser.add_argument(
        "--wav",
        default="",
        help="Si se indica, se usa este WAV en lugar del micrófono (16kHz mono 16-bit)",
    )
    parser.add_argument(
        "--chunk_size",
        type=int,
        default=1280,
        help="Muestras por frame (80ms = 1280 a 16kHz)",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.5,
        help="Umbral de detección (0-1)",
    )
    parser.add_argument(
        "--speex",
        action="store_true",
        help="Activar supresión de ruido Speex (recomendado con micrófono)",
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="En modo micrófono: guardar el audio capturado en /tmp/test_audio.wav al salir (Ctrl+C)",
    )
    parser.add_argument(
        "--list-devices",
        action="store_true",
        help="Listar dispositivos de entrada (micrófonos) y salir; usar el índice con --device",
    )
    parser.add_argument(
        "--device",
        type=int,
        default=None,
        metavar="N",
        help="Índice del dispositivo de entrada (ver --list-devices). En Orange Pi 5 Ultra el main mic suele ser el de la tarjeta ES8388.",
    )
    args = parser.parse_args()

    # Listar dispositivos y salir
    if args.list_devices:
        try:
            import pyaudio
            pa = pyaudio.PyAudio()
            print("Dispositivos de entrada (micrófonos):")
            for i in range(pa.get_device_count()):
                info = pa.get_device_info_by_index(i)
                if info.get("maxInputChannels", 0) > 0:
                    default = " (default)" if i == pa.get_default_input_device_info().get("index") else ""
                    print(f"  [{i}] {info.get('name', '?')} (inputs={info.get('maxInputChannels')}, rate={info.get('defaultSampleRate', '?')}){default}")
            pa.terminate()
        except Exception as e:
            print(f"Error: {e}")
        return

    print(f"Cargando modelo: {args.model} (framework={args.framework})")
    model = Model(
        wakeword_models=[args.model],
        inference_framework=args.framework,
        enable_speex_noise_suppression=args.speex,
    )

    if args.wav:
        # Inferencia sobre archivo WAV (se convierte a mono 16-bit 16 kHz si hace falta)
        try:
            import wave
        except ImportError:
            print("Para --wav se necesita el módulo wave (incluido en Python estándar).")
            sys.exit(1)
        try:
            with wave.open(args.wav, "rb") as wf:
                nch = wf.getnchannels()
                sampwidth = wf.getsampwidth()
                sr = wf.getframerate()
                nframes = wf.getnframes()
                data = wf.readframes(nframes)
        except Exception as e:
            print(f"Error leyendo WAV: {e}")
            sys.exit(1)
        # Decodificar según ancho de muestra
        if sampwidth == 2:
            audio = np.frombuffer(data, dtype=np.int16)
        elif sampwidth == 1:
            audio = (np.frombuffer(data, dtype=np.uint8).astype(np.int16) - 128) * 256
        elif sampwidth == 4:
            raw = np.frombuffer(data, dtype=np.int32)
            audio = (np.clip(raw, -2**31, 2**31 - 1) // 65536).astype(np.int16)
        else:
            print(f"Ancho de muestra no soportado: {sampwidth} bytes.")
            sys.exit(1)
        # Estéreo → mono (promedio de canales)
        if nch == 2:
            audio = audio.reshape(-1, 2).mean(axis=1).astype(np.int16)
        elif nch > 2:
            audio = audio.reshape(-1, nch).mean(axis=1).astype(np.int16)
        # Resamplear a 16 kHz si hace falta
        if sr != 16000:
            try:
                import resampy
                audio = resampy.resample(audio.astype(np.float64) / 32768.0, sr, 16000)
                audio = (np.clip(audio, -1.0, 1.0) * 32767).astype(np.int16)
            except ImportError:
                print("Para resamplear a 16 kHz instalar: pip install resampy")
                sys.exit(1)
        # Procesar en chunks
        step = args.chunk_size
        for i in range(0, len(audio) - step, step):
            chunk = audio[i : i + step]
            pred = model.predict(chunk)
            for name, score in pred.items():
                if score >= args.threshold:
                    print(f"[WAV] Wake word detectada: {name} = {score:.3f} (t={i/16000:.2f}s)")
        print("Fin del archivo WAV.")
        return

    # Modo micrófono
    try:
        import pyaudio
    except ImportError:
        print("Para usar micrófono: pip install pyaudio")
        sys.exit(1)

    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 16000
    CHUNK = args.chunk_size

    pa = pyaudio.PyAudio()
    try:
        open_kw = dict(
            format=FORMAT,
            channels=CHANNELS,
            rate=RATE,
            input=True,
            frames_per_buffer=CHUNK,
        )
        if args.device is not None:
            open_kw["input_device_index"] = args.device
        stream = pa.open(**open_kw)
    except Exception as e:
        print(f"No se pudo abrir el micrófono: {e}")
        print("Ejecutar con --list-devices para ver índices; probar --device N (p. ej. ES8388 suele ser otro índice que el default).")
        pa.terminate()
        sys.exit(1)

    print("Escuchando... (Ctrl+C para salir)")
    if args.test:
        print("Modo test: el audio se guardará en /tmp/test_audio.wav al salir.")
    print(f"Umbral: {args.threshold}")
    recorded = []
    try:
        while True:
            buf = stream.read(CHUNK)
            audio = np.frombuffer(buf, dtype=np.int16)
            if args.test:
                recorded.append(audio.copy())
            pred = model.predict(audio)
            for name, score in pred.items():
                if score >= args.threshold:
                    print(f"Wake word detectada: {name} = {score:.3f}")
    except KeyboardInterrupt:
        print("\nDetenido.")
    finally:
        if args.test and recorded:
            import wave
            out_path = "/tmp/test_audio.wav"
            full = np.concatenate(recorded)
            with wave.open(out_path, "wb") as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(RATE)
                wf.writeframes(full.tobytes())
            print(f"Audio guardado en {out_path} ({len(full)/RATE:.1f} s)")
        stream.stop_stream()
        stream.close()
        pa.terminate()


if __name__ == "__main__":
    main()
