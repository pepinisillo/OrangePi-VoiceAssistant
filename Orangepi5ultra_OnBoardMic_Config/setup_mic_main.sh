#!/bin/bash
# Aplica la configuración del micrófono principal (main mic) en Orange Pi 5 Ultra (ES8388).
# Los cambios son volátiles; se pierden al reiniciar. Ver README.md para persistencia.

set -e

# Detectar tarjeta ES8388 (suele ser 2)
if command -v aplay &>/dev/null; then
	card=$(aplay -l 2>/dev/null | grep -i "es8388" | head -1 | sed -n 's/.*card \([0-9]*\):.*/\1/p')
fi
card=${card:-2}

echo "Configurando main mic en tarjeta $card (ES8388)..."

amixer -c "$card" cset name='ALC Capture Max PGA' 4
amixer -c "$card" cset name='ALC Capture Min PGA' 2
amixer -c "$card" cset name='Capture Digital Volume' 192
amixer -c "$card" cset name='Left Channel Capture Volume' 4
amixer -c "$card" cset name='Right Channel Capture Volume' 4
amixer -c "$card" cset name='Left PGA Mux' 1
amixer -c "$card" cset name='Right PGA Mux' 1
amixer -c "$card" cset name='Differential Mux' 1

echo "Listo. El micrófono principal queda configurado para esta sesión."
