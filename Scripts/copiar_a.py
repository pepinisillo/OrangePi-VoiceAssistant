import shutil
from pathlib import Path

root_in = Path(r"C:\ruta1")      # donde están las subcarpetas
root_out = Path(r"C:\ruta2")        # carpeta destino
root_out.mkdir(parents=True, exist_ok=True)

counter = 1

for ogg in root_in.rglob("*.ogg"):
    txt = ogg.with_suffix(".txt")
    if not txt.exists():
        continue

    base = f"clip_{counter:04d}"
    dest_ogg = root_out / f"{base}.ogg"
    dest_txt = root_out / f"{base}.txt"

    shutil.copy2(ogg, dest_ogg)
    shutil.copy2(txt, dest_txt)
    counter += 1

print("Copiados", counter - 1, "pares .ogg + .txt")