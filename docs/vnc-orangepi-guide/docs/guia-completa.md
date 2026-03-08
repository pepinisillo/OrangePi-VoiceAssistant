# Guía Completa: Configurar VNC en Orange Pi 5 Ultra

## Tabla de Contenidos

1. [Introducción](#introducción)
2. [Conceptos Clave](#conceptos-clave)
3. [Verificación del Sistema](#verificación-del-sistema)
4. [Instalación](#instalación)
5. [Configuración](#configuración)
6. [Inicio Automático](#inicio-automático)
7. [Conexión desde Clientes](#conexión-desde-clientes)
8. [Conexión por Nombre](#conexión-por-nombre)
9. [Seguridad](#seguridad)

---

## Introducción

Esta guía explica cómo configurar acceso remoto gráfico VNC en una **Orange Pi 5 Ultra** con Ubuntu 22.04 LTS, permitiendo controlar el dispositivo sin necesidad de monitor físico conectado.

### Sistema Probado

| Componente | Versión/Detalle |
|------------|-----------------|
| Dispositivo | Orange Pi 5 Ultra |
| Sistema Operativo | Ubuntu 22.04.5 LTS (arm64) |
| Kernel | 6.1.43-rockchip-rk3588 |
| Entorno de Escritorio | XFCE |
| Display Manager | LightDM |
| Servidor Gráfico | X11 (Xorg) |

> **Nota:** Esta guía puede funcionar en otros modelos de Orange Pi o SBCs con Ubuntu/Debian, pero fue probada específicamente en Orange Pi 5 Ultra.

### Caso de Uso

- Controlar el dispositivo desde un celular o laptop
- Usar el dispositivo en modo "headless" (sin monitor)
- Acceder al escritorio gráfico de forma remota

---

## Conceptos Clave

### ¿Qué es VNC?

VNC (Virtual Network Computing) es un protocolo que permite ver y controlar el escritorio de una computadora remotamente a través de la red.

```
┌─────────────────┐         Red Local          ┌─────────────────┐
│   Orange Pi     │◄─────────────────────────►│ Cliente (móvil/ │
│  (Servidor VNC) │                            │     laptop)     │
└─────────────────┘                            └─────────────────┘
```

### Display y Puertos

VNC usa "displays" numerados que corresponden a puertos TCP:

| Display | Puerto | Cálculo |
|---------|--------|---------|
| :0 | 5900 | 5900 + 0 |
| :1 | 5901 | 5900 + 1 |
| :2 | 5902 | 5900 + 2 |

**Fórmula:** `Puerto = 5900 + número_de_display`

### Tipos de Servidores VNC

| Servidor | Función |
|----------|---------|
| **TigerVNC** | Crea sesión X11 nueva e independiente |
| **x11vnc** | Comparte la sesión X11 existente (la del monitor) |

---

## Verificación del Sistema

Antes de configurar, verificar el sistema:

```bash
# Ver versión del sistema operativo
lsb_release -a

# Ver display manager
systemctl status display-manager

# Ver entorno de escritorio
echo $XDG_CURRENT_DESKTOP
echo $XDG_SESSION_TYPE

# Ver usuario actual
whoami

# Ver hostname
hostname

# Ver IP actual
ip addr show | grep "inet " | grep -v 127.0.0.1

# Ver si VNC está instalado
dpkg -l | grep -i vnc
```

---

## Instalación

### Instalar TigerVNC

```bash
sudo apt update
sudo apt install tigervnc-standalone-server tigervnc-common
```

### Verificar instalación

```bash
vncserver -version
```

---

## Configuración

### Paso 1: Crear contraseña VNC

```bash
vncpasswd
```

Este comando:
- Solicita una contraseña (no se muestra al escribir)
- Pide confirmación
- Pregunta si crear contraseña de solo vista (opcional)
- Guarda la contraseña encriptada en `~/.vnc/passwd`

### Paso 2: Crear script de inicio

```bash
mkdir -p ~/.vnc
nano ~/.vnc/xstartup
```

Contenido para **XFCE**:

```bash
#!/bin/bash
xrdb $HOME/.Xresources
startxfce4 &
```

Contenido para **GNOME**:

```bash
#!/bin/bash
xrdb $HOME/.Xresources
gnome-session &
```

Contenido para **LXDE**:

```bash
#!/bin/bash
xrdb $HOME/.Xresources
startlxde &
```

Hacer ejecutable:

```bash
chmod +x ~/.vnc/xstartup
```

### Paso 3: Iniciar servidor VNC

```bash
vncserver :1
```

Opciones adicionales:

```bash
# Con resolución específica
vncserver :1 -geometry 1920x1080

# Con profundidad de color
vncserver :1 -depth 24

# Combinado
vncserver :1 -geometry 1920x1080 -depth 24
```

### Paso 4: Verificar funcionamiento

```bash
# Ver puertos en escucha
ss -tlnp | grep 590

# Salida esperada:
# LISTEN 0 5 0.0.0.0:5901 0.0.0.0:* users:(("Xtigervnc",...))
```

**Importante:** Si aparece `127.0.0.1:5901` en lugar de `0.0.0.0:5901`, el servidor solo acepta conexiones locales.

---

## Inicio Automático

### Método 1: Servicio systemd (Recomendado)

Crear archivo de servicio:

```bash
sudo nano /etc/systemd/system/vncserver@.service
```

Contenido:

```ini
[Unit]
Description=TigerVNC Server for display %i
After=syslog.target network-online.target
Wants=network-online.target

[Service]
Type=forking
User=USUARIO
Group=USUARIO
WorkingDirectory=/home/USUARIO

ExecStartPre=/bin/sh -c '/usr/bin/vncserver -kill :%i > /dev/null 2>&1 || :'
ExecStart=/usr/bin/vncserver :%i -geometry 1920x1080 -depth 24
ExecStop=/usr/bin/vncserver -kill :%i

[Install]
WantedBy=multi-user.target
```

**Nota:** Reemplazar `USUARIO` por el nombre de usuario real.

Activar servicio:

```bash
sudo systemctl daemon-reload
sudo systemctl enable vncserver@1
sudo systemctl start vncserver@1
sudo systemctl status vncserver@1
```

### Método 2: Crontab

```bash
crontab -e
```

Agregar línea:

```
@reboot /usr/bin/vncserver :1 -geometry 1920x1080
```

---

## Conexión desde Clientes

### Android

1. Instalar cliente VNC (VNC Viewer, bVNC, AVNC)
2. Nueva conexión
3. Dirección: `<IP>:5901`
4. Conectar e ingresar contraseña

### Linux

```bash
# Instalar cliente (Debian/Ubuntu)
sudo apt install tigervnc-viewer

# Instalar cliente (Arch)
sudo pacman -S tigervnc

# Conectar
vncviewer <IP>:5901
```

O usar **Remmina** (interfaz gráfica):

```bash
# Debian/Ubuntu
sudo apt install remmina remmina-plugin-vnc

# Arch
sudo pacman -S remmina
```

### Windows

1. Descargar RealVNC Viewer: https://www.realvnc.com/download/viewer/
2. Nueva conexión: `<IP>:5901`
3. Conectar

### macOS

1. Finder → Ir → Conectar al servidor
2. Dirección: `vnc://<IP>:5901`

---

## Conexión por Nombre

Para conectarse usando nombre de host en lugar de IP:

### Instalar Avahi

```bash
sudo apt install avahi-daemon
sudo systemctl enable avahi-daemon
sudo systemctl start avahi-daemon
```

### Conectar

Ahora se puede usar `<hostname>.local`:

```bash
vncviewer orangepi.local:5901
```

### Configurar cliente Linux

En sistemas Arch/Linux, editar `/etc/nsswitch.conf`:

```bash
sudo nano /etc/nsswitch.conf
```

La línea `hosts:` debe incluir `mdns_minimal`:

```
hosts: mymachines mdns_minimal [NOTFOUND=return] resolve [!UNAVAIL=return] files dns
```

Instalar soporte mDNS:

```bash
# Arch
sudo pacman -S avahi nss-mdns

# Debian/Ubuntu
sudo apt install avahi-daemon libnss-mdns
```

---

## Seguridad

### Túnel SSH

VNC transmite datos sin encriptar. Para conexiones seguras, usar túnel SSH:

```bash
# Desde el cliente, crear túnel
ssh -L 5901:localhost:5901 usuario@<IP>

# En otra terminal, conectar VNC a localhost
vncviewer localhost:5901
```

### Firewall

Abrir puerto en el firewall:

```bash
# UFW (Ubuntu)
sudo ufw allow 5901/tcp

# Firewalld (Fedora/CentOS)
sudo firewall-cmd --permanent --add-port=5901/tcp
sudo firewall-cmd --reload
```

### Cambiar contraseña

```bash
vncpasswd
```

---

## Gestión de Servidores

### Comandos básicos

```bash
# Iniciar
vncserver :1

# Detener específico
vncserver -kill :1

# Detener todos
vncserver -kill :*

# Ver activos
ss -tlnp | grep 590

# Ver procesos
ps aux | grep vnc

# Ver logs
cat ~/.vnc/*.log
```

### Estructura de archivos

```
~/.vnc/
├── passwd           # Contraseña encriptada
├── xstartup         # Script de inicio del escritorio
├── <hostname>:1.log # Logs del display :1
└── <hostname>:1.pid # PID del proceso
```
