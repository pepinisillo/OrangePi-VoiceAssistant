# Guía VNC para Orange Pi 5 Ultra (Headless)

Configuración de acceso remoto gráfico VNC para **Orange Pi 5 Ultra** con Ubuntu 22.04, permitiendo control remoto sin monitor físico.

> **Nota:** Esta guía fue creada y probada específicamente en Orange Pi 5 Ultra con Ubuntu 22.04 LTS (arm64) y XFCE. Puede funcionar en otros modelos de Orange Pi o SBCs similares con ajustes menores.

## Características

- Acceso gráfico remoto desde Android, Linux, Windows o macOS
- Funciona sin monitor conectado (headless)
- Inicio automático al boot
- Conexión por nombre de host (sin necesidad de conocer la IP)

## Hardware y Software Probado

| Componente | Especificación |
|------------|----------------|
| Dispositivo | Orange Pi 5 Ultra |
| Sistema Operativo | Ubuntu 22.04.5 LTS (arm64) |
| Kernel | 6.1.43-rockchip-rk3588 |
| Entorno de Escritorio | XFCE |
| Display Manager | LightDM |
| Servidor Gráfico | X11 (Xorg) |

## Requisitos

- Orange Pi 5 Ultra
- Ubuntu 22.04 LTS (imagen oficial de Orange Pi)
- Entorno de escritorio XFCE (preinstalado en imagen oficial)
- Red WiFi o Ethernet

## Instalación Rápida

```bash
# 1. Instalar TigerVNC
sudo apt update
sudo apt install tigervnc-standalone-server tigervnc-common

# 2. Crear contraseña VNC
vncpasswd

# 3. Crear script de inicio
mkdir -p ~/.vnc
cat > ~/.vnc/xstartup << 'EOF'
#!/bin/bash
xrdb $HOME/.Xresources
startxfce4 &
EOF
chmod +x ~/.vnc/xstartup

# 4. Iniciar servidor VNC
vncserver :1

# 5. Conectar desde otro dispositivo
# Dirección: <IP_DEL_DISPOSITIVO>:5901
```

## Documentación

- [Guía Completa](docs/guia-completa.md) - Tutorial detallado paso a paso
- [Solución de Problemas](docs/troubleshooting.md) - Errores comunes y soluciones
- [Archivos de Configuración](config/) - Plantillas de configuración

## Conexión

| Display | Puerto | Dirección |
|---------|--------|-----------|
| :0 | 5900 | `<IP>:5900` |
| :1 | 5901 | `<IP>:5901` |
| :2 | 5902 | `<IP>:5902` |

### Clientes Recomendados

| Plataforma | Cliente |
|------------|---------|
| Android | VNC Viewer, bVNC, AVNC |
| Linux | TigerVNC, Remmina |
| Windows | RealVNC Viewer |
| macOS | RealVNC Viewer, Finder integrado |

## Inicio Automático

Para que VNC inicie automáticamente al encender el dispositivo:

```bash
# Copiar servicio de systemd
sudo cp config/vncserver@.service /etc/systemd/system/

# Editar el archivo y cambiar USUARIO por tu usuario
sudo nano /etc/systemd/system/vncserver@.service

# Activar servicio
sudo systemctl daemon-reload
sudo systemctl enable vncserver@1
sudo systemctl start vncserver@1
```

## Conexión por Nombre (sin IP)

Instalar Avahi para conectarse usando `<hostname>.local`:

```bash
sudo apt install avahi-daemon
sudo systemctl enable avahi-daemon
sudo systemctl start avahi-daemon

# Ahora se puede conectar usando:
# <hostname>.local:5901
# Ejemplo: orangepi.local:5901
```

## Comandos Útiles

```bash
# Iniciar VNC
vncserver :1

# Detener VNC
vncserver -kill :1

# Detener todos los servidores VNC
vncserver -kill :*

# Ver servidores activos
ss -tlnp | grep 590

# Ver logs
cat ~/.vnc/*.log
```

## Licencia

Este proyecto está bajo la licencia MIT. Ver [LICENSE](LICENSE) para más detalles.

## Contribuciones

Las contribuciones son bienvenidas. Por favor, abre un issue o pull request.
