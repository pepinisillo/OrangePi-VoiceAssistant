#!/usr/bin/env python3
"""
Verificador de transcripciones para Piper TTS.

Usa Whisper para transcribir cada WAV y lo compara con el metadata.csv.
Genera un reporte de discrepancias y permite revisión interactiva.

Uso:
    python verificar_transcripciones.py --wavs /ruta/a/wavs --csv /ruta/a/metadata.csv
    python verificar_transcripciones.py --wavs /ruta/a/wavs --csv /ruta/a/metadata.csv --revisar
"""

import argparse
import csv
import json
import os
import platform
import subprocess
import sys
import tempfile
from difflib import SequenceMatcher
from pathlib import Path

try:
    from faster_whisper import WhisperModel
except ImportError:
    print("ERROR: faster-whisper no está instalado.")
    sys.exit(1)


# ── Configuración ───────────────────────────────────────────────────────────

WHISPER_MODEL = "medium"
WHISPER_LANG = "es"
SIMILARITY_THRESHOLD = 0.85  # por debajo de esto se marca como discrepancia
REPORT_FILE = "reporte_verificacion.json"

# Colores ANSI
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
CYAN = "\033[96m"
BOLD = "\033[1m"
DIM = "\033[2m"
RESET = "\033[0m"


# ── Utilidades ──────────────────────────────────────────────────────────────

def normalizar(texto: str) -> str:
    """Normaliza texto para comparación: minúsculas, sin puntuación extra."""
    import re
    texto = texto.lower().strip()
    texto = re.sub(r"[¿¡.,;:!?\"'()\[\]{}\-–—…]", "", texto)
    texto = re.sub(r"\s+", " ", texto)
    return texto.strip()


def similitud(a: str, b: str) -> float:
    return SequenceMatcher(None, normalizar(a), normalizar(b)).ratio()


def colorear_similitud(score: float, umbral: float = SIMILARITY_THRESHOLD) -> str:
    if score >= umbral:
        return f"{GREEN}{score:.1%}{RESET}"
    elif score >= 0.6:
        return f"{YELLOW}{score:.1%}{RESET}"
    else:
        return f"{RED}{score:.1%}{RESET}"


def reproducir_wav(wav_path: str):
    """Reproduce un WAV usando lo que esté disponible en el sistema."""
    sistema = platform.system()
    try:
        if sistema == "Linux":
            for player in ["paplay", "aplay", "ffplay", "mpv"]:
                if subprocess.run(["which", player], capture_output=True).returncode == 0:
                    args = [player, str(wav_path)]
                    if player == "ffplay":
                        args = [player, "-nodisp", "-autoexit", str(wav_path)]
                    elif player == "mpv":
                        args = [player, "--no-video", str(wav_path)]
                    subprocess.run(args, capture_output=True)
                    return
        elif sistema == "Darwin":
            subprocess.run(["afplay", str(wav_path)], capture_output=True)
            return
        elif sistema == "Windows":
            os.startfile(str(wav_path))
            return
        print(f"  {YELLOW}No se encontró reproductor de audio. Instala paplay, aplay, ffplay o mpv.{RESET}")
    except Exception as e:
        print(f"  {RED}Error reproduciendo audio: {e}{RESET}")


# ── Carga de datos ──────────────────────────────────────────────────────────

def cargar_metadata(csv_path: Path) -> dict[str, str]:
    """Lee metadata.csv (formato: nombre|transcripción) y devuelve dict."""
    entries = {}
    with open(csv_path, "r", encoding="utf-8") as f:
        for lineno, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            parts = line.split("|", 1)
            if len(parts) != 2:
                print(f"  {YELLOW}Línea {lineno} ignorada (formato inválido): {line[:60]}{RESET}")
                continue
            nombre, texto = parts
            entries[nombre.strip()] = texto.strip()
    return entries


# ── Transcripción ───────────────────────────────────────────────────────────

def transcribir_wavs(model: WhisperModel, wavs_dir: Path, nombres: list[str]) -> dict[str, str]:
    """Transcribe cada WAV con Whisper y devuelve dict nombre->transcripción."""
    resultados = {}
    total = len(nombres)

    for i, nombre in enumerate(nombres, 1):
        wav_file = wavs_dir / f"{nombre}.wav"
        if not wav_file.exists():
            print(f"  {RED}[{i}/{total}] {nombre}.wav NO ENCONTRADO{RESET}")
            resultados[nombre] = ""
            continue

        print(f"  {DIM}[{i}/{total}] Transcribiendo {nombre}.wav ...{RESET}", end="", flush=True)
        try:
            segments, info = model.transcribe(
                str(wav_file),
                language=WHISPER_LANG,
                beam_size=5,
                vad_filter=True,
            )
            texto = " ".join(seg.text.strip() for seg in segments)
            resultados[nombre] = texto.strip()
            print(f"\r  {GREEN}[{i}/{total}] {nombre}.wav ✓{RESET}                    ")
        except Exception as e:
            print(f"\r  {RED}[{i}/{total}] {nombre}.wav ERROR: {e}{RESET}                    ")
            resultados[nombre] = ""

    return resultados


# ── Comparación ─────────────────────────────────────────────────────────────

def comparar(metadata: dict[str, str], transcripciones: dict[str, str], umbral: float = SIMILARITY_THRESHOLD) -> list[dict]:
    """Compara metadata vs transcripciones y devuelve lista de resultados."""
    resultados = []
    for nombre, texto_csv in metadata.items():
        texto_whisper = transcripciones.get(nombre, "")
        score = similitud(texto_csv, texto_whisper) if texto_whisper else 0.0
        resultados.append({
            "nombre": nombre,
            "csv": texto_csv,
            "whisper": texto_whisper,
            "similitud": score,
            "ok": score >= umbral,
        })
    resultados.sort(key=lambda x: x["similitud"])
    return resultados


# ── Reportes ────────────────────────────────────────────────────────────────

def mostrar_resumen(resultados: list[dict], umbral: float = SIMILARITY_THRESHOLD):
    total = len(resultados)
    ok = sum(1 for r in resultados if r["ok"])
    mal = total - ok

    print(f"\n{'═' * 70}")
    print(f"{BOLD}  RESUMEN DE VERIFICACIÓN{RESET}")
    print(f"{'═' * 70}")
    print(f"  Total archivos:  {total}")
    print(f"  {GREEN}Coinciden:       {ok}{RESET}")
    print(f"  {RED}Discrepancias:   {mal}{RESET}")
    print(f"  Umbral:          {umbral:.0%}")
    print(f"{'═' * 70}\n")

    if mal > 0:
        print(f"{BOLD}  DISCREPANCIAS (ordenadas por similitud):{RESET}\n")
        for r in resultados:
            if r["ok"]:
                continue
            print(f"  {BOLD}{r['nombre']}.wav{RESET}  {colorear_similitud(r['similitud'])}")
            print(f"    CSV:     {CYAN}{r['csv'][:100]}{RESET}")
            print(f"    Whisper: {YELLOW}{r['whisper'][:100]}{RESET}")
            print()


def guardar_reporte(resultados: list[dict], output_path: Path):
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(resultados, f, ensure_ascii=False, indent=2)
    print(f"  Reporte guardado en: {output_path}")


# ── Modo interactivo ────────────────────────────────────────────────────────

def revisar_interactivo(resultados: list[dict], wavs_dir: Path, csv_path: Path, metadata: dict[str, str]):
    """Modo interactivo para revisar discrepancias una por una."""
    discrepancias = [r for r in resultados if not r["ok"]]

    if not discrepancias:
        print(f"\n  {GREEN}¡No hay discrepancias! Todas las transcripciones coinciden.{RESET}\n")
        return

    print(f"\n{'═' * 70}")
    print(f"{BOLD}  REVISIÓN INTERACTIVA — {len(discrepancias)} discrepancias{RESET}")
    print(f"{'═' * 70}")
    print(f"  Comandos: {CYAN}[Enter]{RESET} reproducir  {CYAN}[e]{RESET} editar  {CYAN}[w]{RESET} usar Whisper  {CYAN}[s]{RESET} saltar  {CYAN}[q]{RESET} salir")
    print(f"{'─' * 70}\n")

    cambios = {}

    for idx, r in enumerate(discrepancias):
        nombre = r["nombre"]
        wav_file = wavs_dir / f"{nombre}.wav"

        print(f"  {BOLD}[{idx + 1}/{len(discrepancias)}] {nombre}.wav{RESET}  {colorear_similitud(r['similitud'])}")
        print(f"    CSV actual: {CYAN}{r['csv']}{RESET}")
        print(f"    Whisper:    {YELLOW}{r['whisper']}{RESET}")

        while True:
            opcion = input(f"\n    ▸ Acción (Enter=oír / e=editar / w=usar whisper / s=saltar / q=salir): ").strip().lower()

            if opcion == "":
                if wav_file.exists():
                    print(f"    {DIM}Reproduciendo...{RESET}")
                    reproducir_wav(wav_file)
                else:
                    print(f"    {RED}Archivo no encontrado: {wav_file}{RESET}")

            elif opcion == "e":
                nuevo = input(f"    Nuevo texto: ").strip()
                if nuevo:
                    cambios[nombre] = nuevo
                    metadata[nombre] = nuevo
                    print(f"    {GREEN}✓ Guardado{RESET}")
                    break
                else:
                    print(f"    {YELLOW}Texto vacío, no se guardó{RESET}")

            elif opcion == "w":
                cambios[nombre] = r["whisper"]
                metadata[nombre] = r["whisper"]
                print(f"    {GREEN}✓ Usando transcripción de Whisper{RESET}")
                break

            elif opcion == "s":
                print(f"    {DIM}Saltado{RESET}")
                break

            elif opcion == "q":
                print(f"\n  Saliendo de revisión...")
                if cambios:
                    _guardar_csv(metadata, csv_path)
                    print(f"  {GREEN}Se actualizaron {len(cambios)} líneas en {csv_path}{RESET}")
                return

            else:
                print(f"    {YELLOW}Opción no válida{RESET}")

        print()

    if cambios:
        _guardar_csv(metadata, csv_path)
        print(f"\n  {GREEN}✓ Se actualizaron {len(cambios)} líneas en {csv_path}{RESET}")
    else:
        print(f"\n  {DIM}No se hicieron cambios.{RESET}")


def _guardar_csv(metadata: dict[str, str], csv_path: Path):
    """Reescribe el metadata.csv con los valores actualizados."""
    backup = csv_path.with_suffix(".csv.bak")
    if not backup.exists():
        import shutil
        shutil.copy2(csv_path, backup)
        print(f"  {DIM}Backup creado: {backup}{RESET}")

    lines = [f"{nombre}|{texto}" for nombre, texto in metadata.items()]
    csv_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


# ── Main ────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Verifica transcripciones de metadata.csv contra audio WAV usando Whisper"
    )
    parser.add_argument("--wavs", required=True, help="Carpeta con los archivos .wav")
    parser.add_argument("--csv", required=True, help="Archivo metadata.csv (formato: nombre|texto)")
    parser.add_argument("--modelo", default=WHISPER_MODEL,
                        help=f"Modelo Whisper a usar (default: {WHISPER_MODEL})")
    parser.add_argument("--idioma", default=WHISPER_LANG,
                        help=f"Idioma de los audios (default: {WHISPER_LANG})")
    parser.add_argument("--umbral", type=float, default=SIMILARITY_THRESHOLD,
                        help=f"Umbral de similitud 0-1 (default: {SIMILARITY_THRESHOLD})")
    parser.add_argument("--revisar", action="store_true",
                        help="Entrar en modo interactivo para corregir discrepancias")
    parser.add_argument("--desde-reporte", action="store_true",
                        help="Usar un reporte JSON existente y saltar la transcripción con Whisper")
    parser.add_argument("--reporte", default=REPORT_FILE,
                        help=f"Archivo de salida del reporte JSON (default: {REPORT_FILE})")
    parser.add_argument("--device", default="auto",
                        help="Dispositivo para Whisper: cpu, cuda, auto (default: auto)")
    args = parser.parse_args()

    umbral = args.umbral

    wavs_dir = Path(args.wavs)
    csv_path = Path(args.csv)

    if not wavs_dir.is_dir():
        print(f"{RED}ERROR: No se encontró la carpeta de WAVs: {wavs_dir}{RESET}")
        sys.exit(1)
    if not csv_path.is_file():
        print(f"{RED}ERROR: No se encontró el CSV: {csv_path}{RESET}")
        sys.exit(1)

    # 1. Cargar metadata
    print(f"\n{BOLD}[1/4] Cargando metadata...{RESET}")
    metadata = cargar_metadata(csv_path)
    print(f"  {len(metadata)} entradas cargadas desde {csv_path}")

    wav_count = len(list(wavs_dir.glob("*.wav")))
    print(f"  {wav_count} archivos .wav encontrados en {wavs_dir}")

    nombres_sin_wav = [n for n in metadata if not (wavs_dir / f"{n}.wav").exists()]
    if nombres_sin_wav:
        print(f"  {YELLOW}⚠ {len(nombres_sin_wav)} entradas del CSV sin WAV correspondiente:{RESET}")
        for n in nombres_sin_wav[:10]:
            print(f"    - {n}")
        if len(nombres_sin_wav) > 10:
            print(f"    ... y {len(nombres_sin_wav) - 10} más")

    # Si se indica --desde-reporte, saltamos Whisper y usamos el JSON existente
    if args.desde_reporte:
        reporte_path = Path(args.reporte)
        if not reporte_path.is_file():
            print(f"{RED}ERROR: No se encontró el reporte JSON: {reporte_path}{RESET}")
            sys.exit(1)

        print(f"\n{BOLD}[2/2] Cargando resultados desde reporte JSON...{RESET}")
        with open(reporte_path, "r", encoding="utf-8") as f:
            resultados = json.load(f)

        mostrar_resumen(resultados, umbral)

        if args.revisar:
            revisar_interactivo(resultados, wavs_dir, csv_path, metadata)
    else:
        # 2. Cargar Whisper
        print(f"\n{BOLD}[2/4] Cargando modelo Whisper ({args.modelo})...{RESET}")
        compute_type = "float16" if args.device == "cuda" else "int8"
        if args.device == "auto":
            try:
                import torch
                if torch.cuda.is_available():
                    args.device = "cuda"
                    compute_type = "float16"
                else:
                    args.device = "cpu"
                    compute_type = "int8"
            except ImportError:
                args.device = "cpu"
                compute_type = "int8"

        model = WhisperModel(args.modelo, device=args.device, compute_type=compute_type)
        print(f"  Modelo cargado en {args.device} ({compute_type})")

        # 3. Transcribir
        nombres = [n for n in metadata if (wavs_dir / f"{n}.wav").exists()]
        print(f"\n{BOLD}[3/4] Transcribiendo {len(nombres)} archivos...{RESET}")
        transcripciones = transcribir_wavs(model, wavs_dir, nombres)

        # 4. Comparar
        print(f"\n{BOLD}[4/4] Comparando transcripciones...{RESET}")
        resultados = comparar(metadata, transcripciones, umbral)
        mostrar_resumen(resultados, umbral)

        reporte_path = Path(args.reporte)
        guardar_reporte(resultados, reporte_path)

        # Modo interactivo
        if args.revisar:
            revisar_interactivo(resultados, wavs_dir, csv_path, metadata)


if __name__ == "__main__":
    main()
