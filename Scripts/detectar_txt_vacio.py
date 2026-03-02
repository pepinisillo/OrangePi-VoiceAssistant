from pathlib import Path

# CARPETA DONDE ESTAN LOS .txt
TXT_DIR = r"C:\ruta"

def main():
    base = Path(TXT_DIR)
    txt_files = sorted(base.glob("*.txt"))

    if not txt_files:
        print(f"No se encontraron .txt en {base}")
        return

    vacios = []

    for txt in txt_files:
        try:
            contenido = txt.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            contenido = txt.read_text(encoding="latin-1")

        if not contenido.strip():  # vacio o solo espacios/saltos de línea
            vacios.append(txt)

    print(f"Total .txt: {len(txt_files)}")
    print(f"Vacios (o solo espacios): {len(vacios)}")

    if vacios:
        print("\nLista de .txt vacíos:")
        for f in vacios:
            print(" -", f)

if __name__ == "__main__":
    main()