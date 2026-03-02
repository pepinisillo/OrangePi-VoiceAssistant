from pathlib import Path
import re

# RUTAS
INPUT_DIR = r"C:\Users\pc perrona\Downloads\mercy2"   # carpeta con los .txt
OUTPUT_PATH = r"C:\Users\pc perrona\Downloads\mercy\metadata.csv"

def leer_txt(path: Path) -> str:
    """Intenta leer el .txt probando varias codificaciones (incluye UTF-16)."""
    for enc in ("utf-8-sig", "utf-16", "utf-16-le", "latin-1"):
        try:
            return path.read_text(encoding=enc)
        except UnicodeError:
            continue
    # Si ninguna funciona, lanza error claro
    raise UnicodeError(f"No se pudo leer {path} con utf-8/utf-16/latin-1")

def limpiar_texto(text: str) -> str:
    # Quitar posibles bytes nulos
    text = text.replace("\x00", "")
    # Colapsar espacios múltiples (incluye tabs, saltos de línea)
    text = re.sub(r"\s+", " ", text)
    # Quitar espacios al principio/final
    return text.strip()

def main(input_dir: str, output_path: str):
    input_path = Path(input_dir)
    metadata_path = Path(output_path)

    txt_files = sorted(input_path.glob("*.txt"))
    if not txt_files:
        print(f"No se encontraron .txt en {input_path}")
        return

    print(f"Encontrados {len(txt_files)} archivos .txt en {input_path}")
    lines = []

    for txt_file in txt_files:
        name = txt_file.stem  # sin extensión
        raw = leer_txt(txt_file)
        text = limpiar_texto(raw)

        lines.append(f"{name}|{text}")

    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    metadata_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"metadata.csv generado en: {metadata_path}")
    print(f"Total líneas: {len(lines)}")

if __name__ == "__main__":
    main(INPUT_DIR, OUTPUT_PATH)