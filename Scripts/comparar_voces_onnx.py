#!/usr/bin/env python3
"""
Compara varias voces ONNX de Piper entre sí y con los audios originales.

Edita la sección "Configuración" al inicio del script para poner tus rutas
(WAVs, CSV, ONNX, salida). Luego puedes ejecutar solo:

  python comparar_voces_onnx.py

y opcionalmente  --merge  o  --solo-entre-voces  por terminal.

Genera:
  - Por cada frase: WAV original + un WAV por cada ONNX con el mismo texto.
  - Opcional (--merge): un WAV concatenado por frase (original + cada voz).
  - index.html para escuchar y comparar en el navegador.
"""

import argparse
import random
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


# ─── Configuración (edita aquí las rutas; la terminal puede sobreescribirlas) ───
RUTA_WAVS = Path("/home/pepin/Downloads/mercy/wav")
RUTA_CSV = Path("/home/pepin/Downloads/mercy/metadata.csv")

# O una sola carpeta donde estén todos los .onnx (usa esto o RUTAS_ONNX, no ambos):
RUTA_CARPETA_ONNX = Path("/home/pepin/Downloads/piper/src/python/mercy")
RUTA_SALIDA = Path("/home/pepin/Downloads/piper/src/python/mercy/RES")
MAX_FRASES = 15
FRASES_ALEATORIAS = False  # True = elegir frases al azar; False = usar las primeras N
GENERAR_MERGE = True  # True = genera además un WAV concatenado por frase (original + cada voz)
# Para modo solo-entre-voces:
FRASE_ENTRE_VOCES = "Hola, hasta luego."
COMANDO_PIPER = "python3 -m piper"
# ───────────────────────────────────────────────────────────────────────────────


def cargar_metadata(csv_path: Path) -> list[tuple[str, str]]:
    """Lee metadata.csv (nombre|texto) y devuelve lista (nombre, texto)."""
    entradas = []
    with open(csv_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split("|", 1)
            if len(parts) != 2:
                continue
            nombre, texto = parts[0].strip(), parts[1].strip()
            entradas.append((nombre, texto))
    return entradas


def encontrar_wavs(wav_dir: Path, nombres: list[str]) -> dict[str, Path]:
    """Para cada nombre, busca nombre.wav en wav_dir (o wavs/)."""
    resultado = {}
    for nombre in nombres:
        for sub in ("", "wav", "wavs"):
            d = wav_dir / sub if sub else wav_dir
            wav = d / f"{nombre}.wav"
            if wav.exists():
                resultado[nombre] = wav
                break
    return resultado


def sintetizar_piper(texto: str, onnx_path: Path, out_wav: Path, piper_cmd: list[str], mostrar_error: bool = True) -> bool:
    """Genera un WAV con Piper desde texto. Usa archivo temporal para el texto."""
    onnx_path = Path(onnx_path).resolve()
    if not onnx_path.exists():
        if mostrar_error:
            print(f" (modelo no existe: {onnx_path})", end="")
        return False
    out_wav = Path(out_wav).resolve()
    out_wav.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".txt", delete=False, encoding="utf-8"
    ) as f:
        f.write(texto)
        f.flush()
        tmp = f.name
    try:
        cmd = [
            *piper_cmd,
            "-m", str(onnx_path),
            "-f", str(out_wav),
            "--input-file", tmp,
        ]
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if r.returncode != 0 and mostrar_error and r.stderr:
            print(f" (piper: {r.stderr.strip()[:120]})", end="")
        return r.returncode == 0 and out_wav.exists()
    except Exception as e:
        if mostrar_error:
            print(f" ({e})", end="")
        return False
    finally:
        Path(tmp).unlink(missing_ok=True)


def nombre_voz(onnx_path: Path) -> str:
    """Nombre corto para etiquetar la voz (stem del .onnx)."""
    return Path(onnx_path).stem


def generar_html_index(
    output_dir: Path,
    frases: list[dict],
    nombres_voces: list[str],
    con_original: bool,
    titulo: str = "Comparación de voces Piper",
) -> None:
    """Escribe index.html con reproductores de audio por frase y por voz."""
    rows = []
    for f in frases:
        texto = f.get("texto", "")
        cells = [texto[:80] + ("..." if len(texto) > 80 else "")]
        if con_original and f.get("original_wav"):
            cells.append(
                f'<audio controls preload="none" src="{f["original_wav"]}"></audio>'
            )
        else:
            cells.append("—")
        for voz in nombres_voces:
            wav = f.get("voces", {}).get(voz)
            if wav:
                cells.append(f'<audio controls preload="none" src="{wav}"></audio>')
            else:
                cells.append("—")
        rows.append("<tr><td>" + "</td><td>".join(cells) + "</td></tr>")

    headers = ["Frase"]
    if con_original:
        headers.append("Original")
    headers.extend(nombres_voces)

    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <title>{titulo}</title>
  <style>
    body {{ font-family: sans-serif; margin: 1rem; background: #1a1a1a; color: #eee; }}
    table {{ border-collapse: collapse; width: 100%; }}
    th, td {{ border: 1px solid #444; padding: 0.5rem; vertical-align: top; }}
    th {{ background: #333; }}
    td audio {{ max-width: 100%; }}
  </style>
</head>
<body>
  <h1>{titulo}</h1>
  <p>Filas: frases. Columnas: original (si hay) + cada modelo ONNX. Reproduce y compara.</p>
  <table>
    <thead><tr><th>{'</th><th>'.join(headers)}</th></tr></thead>
    <tbody>
      {''.join(rows)}
    </tbody>
  </table>
</body>
</html>
"""
    (output_dir / "index.html").write_text(html, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Compara voces ONNX de Piper con originales y entre sí (rutas por defecto en el código)"
    )
    parser.add_argument("--wavs", type=Path, default=None, help="Carpeta con los WAV originales")
    parser.add_argument("--csv", type=Path, default=None, help="metadata.csv (nombre|texto)")
    parser.add_argument(
        "--onnx",
        type=Path,
        nargs="+",
        default=None,
        help="Rutas a archivos .onnx (si no se pasa, se usan las del código)",
    )
    parser.add_argument(
        "--onnx-dir",
        type=Path,
        default=None,
        help="Carpeta con varios .onnx (si no se pasa, se usa la del código)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Carpeta de salida",
    )
    parser.add_argument(
        "--max-frases",
        type=int,
        default=MAX_FRASES,
        help="Máximo de frases a comparar",
    )
    parser.add_argument(
        "--aleatorio",
        action="store_true",
        default=FRASES_ALEATORIAS,
        help="Elegir frases al azar en lugar de las primeras N",
    )
    parser.add_argument(
        "--merge",
        action="store_true",
        default=GENERAR_MERGE,
        help="Generar un WAV concatenado por frase (original + cada voz)",
    )
    parser.add_argument(
        "--piper-cmd",
        default=COMANDO_PIPER,
        help="Comando para invocar Piper",
    )
    parser.add_argument(
        "--solo-entre-voces",
        action="store_true",
        help="Solo generar la misma frase con cada ONNX (sin WAVs originales)",
    )
    parser.add_argument(
        "--frase",
        type=str,
        default=FRASE_ENTRE_VOCES,
        help="Texto a sintetizar en modo --solo-entre-voces",
    )
    args = parser.parse_args()

    # Aplicar valores por defecto del código si no se pasaron por terminal
    wavs = args.wavs if args.wavs is not None else RUTA_WAVS
    csv_path = args.csv if args.csv is not None else RUTA_CSV
    output_dir = Path(args.output_dir).resolve() if args.output_dir is not None else RUTA_SALIDA.resolve()
    max_frases = args.max_frases
    merge = args.merge
    piper_cmd_str = args.piper_cmd
    frase_entre_voces = args.frase

    onnx_list: list[Path] = []
    if args.onnx:
        for p in args.onnx:
            p = Path(p).resolve()
            if p.is_file() and p.suffix.lower() == ".onnx":
                onnx_list.append(p)
    if args.onnx_dir:
        args.onnx_dir = Path(args.onnx_dir).resolve()
        onnx_list.extend(sorted(args.onnx_dir.glob("*.onnx")))
    if not onnx_list:
        # Usar configuración del código
        if RUTA_CARPETA_ONNX and RUTA_CARPETA_ONNX.exists():
            onnx_list = sorted(Path(RUTA_CARPETA_ONNX).resolve().glob("*.onnx"))
        else:
            onnx_list = [Path(p).resolve() for p in RUTAS_ONNX if Path(p).exists() and Path(p).suffix.lower() == ".onnx"]
    if not onnx_list:
        print("ERROR: No hay ningún .onnx. Indica rutas en el código (RUTAS_ONNX o RUTA_CARPETA_ONNX) o usa --onnx / --onnx-dir.")
        sys.exit(1)
    output_dir.mkdir(parents=True, exist_ok=True)
    piper_cmd = piper_cmd_str.split()

    if args.solo_entre_voces:
        subdir = output_dir / "entre_voces"
        subdir.mkdir(parents=True, exist_ok=True)
        voces_dict = {}
        for onnx_path in onnx_list:
            nombre = nombre_voz(onnx_path)
            out_wav = subdir / f"{nombre}.wav"
            print(f"  Generando {nombre}...", end=" ", flush=True)
            if sintetizar_piper(frase_entre_voces, onnx_path, out_wav, piper_cmd):
                print("OK")
                voces_dict[nombre] = f"entre_voces/{out_wav.name}"
            else:
                print("ERROR")
        generar_html_index(
            output_dir,
            [{"texto": frase_entre_voces, "voces": voces_dict}],
            [nombre_voz(p) for p in onnx_list],
            con_original=False,
            titulo="Comparación entre voces (misma frase)",
        )
        print(f"\nSalida en {output_dir}. Abre index.html para escuchar.")
        return

    if not csv_path.exists():
        print("ERROR: CSV no encontrado:", csv_path)
        sys.exit(1)
    if not wavs.exists():
        print("ERROR: Carpeta WAVs no encontrada:", wavs)
        sys.exit(1)

    entradas = cargar_metadata(csv_path)
    if not entradas:
        print("ERROR: No se encontraron líneas en el CSV.")
        sys.exit(1)
    if args.aleatorio:
        entradas = random.sample(entradas, min(max_frases, len(entradas)))
    else:
        entradas = entradas[:max_frases]
    nombres = [e[0] for e in entradas]
    wav_map = encontrar_wavs(wavs, nombres)

    frases_para_html = []
    for idx, (nombre, texto) in enumerate(entradas):
        frase_dir = output_dir / f"frase_{idx+1:03d}_{nombre}"
        frase_dir.mkdir(parents=True, exist_ok=True)
        original_wav = None
        if nombre in wav_map:
            dest = frase_dir / "original.wav"
            shutil.copy2(wav_map[nombre], dest)
            original_wav = f"frase_{idx+1:03d}_{nombre}/original.wav"
        voces = {}
        for onnx_path in onnx_list:
            nombre_v = nombre_voz(onnx_path)
            out_wav = frase_dir / f"voz_{nombre_v}.wav"
            print(f"  [{idx+1}/{len(entradas)}] {nombre_v}: {nombre}...", end=" ", flush=True)
            if sintetizar_piper(texto, onnx_path, out_wav, piper_cmd):
                print("OK")
                voces[nombre_v] = f"frase_{idx+1:03d}_{nombre}/{out_wav.name}"
            else:
                print("ERROR")
        frases_para_html.append({
            "texto": texto,
            "original_wav": original_wav,
            "voces": voces,
        })

        if merge and (original_wav or voces):
            try:
                from pydub import AudioSegment
                silencio = AudioSegment.silent(duration=500)
                segmentos = []
                if original_wav:
                    segmentos.append(AudioSegment.from_wav(str(frase_dir / "original.wav")))
                    segmentos.append(silencio)
                for nombre_v in voces:
                    segmentos.append(AudioSegment.from_wav(str(frase_dir / f"voz_{nombre_v}.wav")))
                    segmentos.append(silencio)
                if segmentos:
                    merge = segmentos[0]
                    for s in segmentos[1:]:
                        merge += s
                    merge.export(str(frase_dir / "comparacion_todas.wav"), format="wav")
            except Exception as e:
                print(f"    (merge omitido: {e})")

    generar_html_index(
        output_dir,
        frases_para_html,
        [nombre_voz(p) for p in onnx_list],
        con_original=True,
        titulo="Comparación: original vs voces ONNX",
    )
    print(f"\nListo. Salida en {output_dir}. Abre index.html para comparar.")


if __name__ == "__main__":
    main()
