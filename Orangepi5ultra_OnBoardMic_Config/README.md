# Micrófono interno (main mic) – Orange Pi 5 Ultra

Configuración del **micrófono principal** en la Orange Pi 5 Ultra con codec **ES8388**. Por defecto la captura puede usar la entrada «Line 1», que en esta placa no corresponde al micrófono interno y produce solo ruido o estático. El main mic va por **Line 2** y **PGA Mux** en valor 1; la documentación oficial de Orange Pi usa el script `/usr/local/bin/test_record.sh main` para aplicar estos ajustes.

Los valores del mezclador ALSA son volátiles: se pierden al reiniciar. Puede aplicarse la configuración una vez por sesión o dejarla persistente al arranque.

## Requisitos

- Orange Pi 5 Ultra con kernel Rockchip (p. ej. `6.1.43-rockchip-rk3588`).
- Tarjeta de sonido ES8388 detectada (comprobar con `arecord -l`; suele ser la tarjeta `2`).

## 1. Ajustes de mezclador (main mic)

Ejecutar con la tarjeta del codec ES8388 (normalmente `2`):

```bash
card=2   # Ajustar si la tarjeta del codec es otra (arecord -l)

amixer -c $card cset name='ALC Capture Max PGA' 4
amixer -c $card cset name='ALC Capture Min PGA' 2
amixer -c $card cset name='Capture Digital Volume' 192
amixer -c $card cset name='Left Channel Capture Volume' 4
amixer -c $card cset name='Right Channel Capture Volume' 4
amixer -c $card cset name='Left PGA Mux' 1
amixer -c $card cset name='Right PGA Mux' 1
amixer -c $card cset name='Differential Mux' 1
```

Equivalente usando el script oficial del sistema (si existe): `test_record.sh main`. Tras ello el micrófono queda listo para grabar o para aplicaciones que usen ALSA (p. ej. openWakeWord).

## 2. Script incluido (una vez por sesión)

En esta carpeta se incluye `setup_mic_main.sh`, que aplica los comandos anteriores. Ejecutar antes de usar el micrófono en esa sesión:

```bash
cd /ruta/a/OrangePi-VoiceAssistant/Orangepi5ultra_OnBoardMic_Config
chmod +x setup_mic_main.sh   # solo la primera vez si sale «Permission denied»
./setup_mic_main.sh
```

Puede invocarse desde otro directorio pasando la ruta al script. No requiere permisos de root salvo que se quiera guardar el estado para persistencia (sección 3). Si al copiar el repo el archivo pierde el bit de ejecución, usar `chmod +x setup_mic_main.sh` o ejecutar `bash setup_mic_main.sh`.

## 3. Persistencia al arranque

Tras aplicar los ajustes de la sección 1 (o ejecutar `setup_mic_main.sh`) una vez, se guarda el estado de la tarjeta y se restaura en cada arranque:

```bash
# Guardar estado (ejecutar con los ajustes ya aplicados)
sudo alsactl store -f /etc/asound.state.card2

# Crear servicio para restaurar al arranque
sudo tee /etc/systemd/system/restore-es8388-mic.service << 'EOF'
[Unit]
Description=Restore ES8388 main mic settings (Orange Pi 5 Ultra)
After=sound.target

[Service]
Type=oneshot
ExecStart=/usr/sbin/alsactl restore -f /etc/asound.state.card2
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable restore-es8388-mic.service
```

Tras reiniciar, el micrófono principal queda configurado sin ejecutar nada más. Si la tarjeta del codec no es la 2, sustituir `card2` y el número de tarjeta en los comandos por el valor correcto.

## 4. Comprobar que el micrófono funciona

Grabar unos segundos y reproducir:

```bash
arecord -D plughw:2,0 -f S16_LE -r 16000 -c 1 -d 5 /tmp/prueba_mic.wav
aplay /tmp/prueba_mic.wav
```

O usar el script oficial:

```bash
test_record.sh main
```

## 5. Referencia (script oficial)

La configuración coincide con la usada en `/usr/local/bin/test_record.sh main` de la imagen oficial Orange Pi 5 Ultra (bloque para `main` cuando `BOARD` no es `orangepi900`): ALC Capture Max/Min PGA, Capture Digital Volume, Left/Right Channel Capture Volume, Left/Right PGA Mux = 1, Differential Mux = 1.

## 6. Si algo falla

- **Solo se escucha ruido o estático:** asegurarse de que se han aplicado los ajustes de la sección 1 (o `setup_mic_main.sh`) en la misma sesión, o que el servicio de persistencia está habilitado y el estado se guardó con el main mic ya configurado.
- **Tarjeta distinta:** comprobar con `arecord -l` y `cat /proc/asound/cards`; usar el índice correcto en `card=...` y en el nombre del archivo de estado (`asound.state.cardN`).
