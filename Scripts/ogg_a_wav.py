from pathlib import Path
from pydub import AudioSegment

# CARPETAS
INPUT_DIR = r"C:\Users\pc perrona\Downloads\mercy2"          # .ogg
OUTPUT_DIR = r"C:\Users\pc perrona\Downloads\mercy\wavs"    # .wav

TARGET_SR = 22050
TARGET_CHANNELS = 1
TARGET_WIDTH = 2  # bytes (16‑bit)

def main():
    in_path = Path(INPUT_DIR)
    out_path = Path(OUTPUT_DIR)
    out_path.mkdir(parents=True, exist_ok=True)

    # carpeta plana
    ogg_files = sorted(in_path.glob("*.ogg"))

    if not ogg_files:
        print(f"No se encontraron .ogg en {in_path}")
        return

    print(f"Encontrados {len(ogg_files)} .ogg en {in_path}")

    for ogg in ogg_files:
        rel = ogg.relative_to(in_path)
        out_file = out_path / f"{ogg.stem}.wav"  # mismo nombre que el .txt/.ogg

        try:
            audio = AudioSegment.from_ogg(str(ogg))
        except Exception as e:
            print(f"ERROR al leer {rel}: {e}")
            continue

        # Formato Piper
        audio = audio.set_frame_rate(TARGET_SR)
        audio = audio.set_channels(TARGET_CHANNELS)
        audio = audio.set_sample_width(TARGET_WIDTH)

        audio.export(
            str(out_file),
            format="wav",
            parameters=["-acodec", "pcm_s16le", "-ar", str(TARGET_SR), "-ac", "1"],
        )

        print(f"OK: {rel} -> {out_file.name}")

if __name__ == "__main__":
    main()