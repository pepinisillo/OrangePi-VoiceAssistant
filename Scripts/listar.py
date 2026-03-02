from pathlib import Path

root = Path(r"C:\ruta1")  # carpeta raíz
b = 0
c = 0

for ogg in root.rglob("*.ogg"):
    txt = ogg.with_suffix(".txt")
    if txt.exists():
        b = b + 1
        print("PAR:", ogg, " <-> ", txt, )
    else:
        c = c + 1
        print("SIN TXT:", ogg, )

print("PAR:", b, "SIN TXT:", c)