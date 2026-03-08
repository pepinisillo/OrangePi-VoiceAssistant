# Solución de Problemas - Orange Pi 5 Ultra VNC

> Guía de solución de problemas para configuración VNC en Orange Pi 5 Ultra con Ubuntu 22.04 LTS.

## Errores Comunes

### Error: "Conexión rehusada" (Connection refused)

**Síntoma:**
```
Unable to connect to socket: Connection refused (111)
```

**Causas y soluciones:**

1. **El servidor VNC no está corriendo**
   ```bash
   # Verificar
   ss -tlnp | grep 590
   
   # Si no hay salida, iniciar
   vncserver :1
   ```

2. **Puerto incorrecto**
   ```bash
   # Verificar en qué puerto escucha
   ss -tlnp | grep 590
   
   # Conectar al puerto correcto
   vncviewer <IP>:<PUERTO>
   ```

3. **Firewall bloqueando**
   ```bash
   # Abrir puerto
   sudo ufw allow 5901/tcp
   ```

4. **Servidor escuchando solo en localhost**
   ```bash
   # Si aparece 127.0.0.1 en lugar de 0.0.0.0:
   ss -tlnp | grep 590
   # LISTEN 127.0.0.1:5901  # ← Solo local
   # LISTEN 0.0.0.0:5901    # ← Todas las interfaces
   ```

---

### Error: Pantalla negra al conectar

**Causas y soluciones:**

1. **Script xstartup no existe o no es ejecutable**
   ```bash
   # Verificar
   ls -la ~/.vnc/xstartup
   
   # Debe tener permisos de ejecución
   chmod +x ~/.vnc/xstartup
   ```

2. **Entorno de escritorio incorrecto en xstartup**
   ```bash
   # Verificar qué entorno está instalado
   which startxfce4
   which gnome-session
   which startlxde
   
   # Editar xstartup con el comando correcto
   nano ~/.vnc/xstartup
   ```

3. **Error en el script**
   ```bash
   # Ver logs
   cat ~/.vnc/*.log | tail -50
   ```

---

### Error: Puerto ya en uso

**Síntoma:**
```
vncserver: A VNC server is already running as :1
```

**Solución:**
```bash
# Matar el servidor existente
vncserver -kill :1

# O usar otro display
vncserver :2
```

---

### Error: Servidor escucha solo en localhost

**Síntoma:**
```bash
ss -tlnp | grep 590
# LISTEN 0 0 127.0.0.1:5900 ...
```

**Causa:** El servidor se inició con opción `-localhost`.

**Solución:**
```bash
# Matar servidor actual
vncserver -kill :1

# Reiniciar sin -localhost
vncserver :1
```

---

### Error: Servicio systemd no inicia

**Diagnóstico:**
```bash
sudo systemctl status vncserver@1
journalctl -u vncserver@1 --no-pager -n 50
```

**Causas comunes:**

1. **Usuario incorrecto en el archivo de servicio**
   - Verificar que `User=` y `Group=` tengan el usuario correcto
   - Verificar que `WorkingDirectory=` apunte al home correcto

2. **Ruta incorrecta al passwd**
   - Verificar que `~/.vnc/passwd` existe

3. **Permisos incorrectos**
   ```bash
   ls -la ~/.vnc/
   # passwd debe ser -rw-------
   # xstartup debe ser -rwx------
   ```

---

### Error: No se puede resolver hostname.local

**Causa:** Avahi no está instalado o configurado.

**Solución:**
```bash
# En el servidor
sudo apt install avahi-daemon
sudo systemctl enable avahi-daemon
sudo systemctl start avahi-daemon

# En el cliente Linux
sudo apt install libnss-mdns  # Debian/Ubuntu
sudo pacman -S nss-mdns       # Arch
```

---

## Comandos de Diagnóstico

```bash
# Ver servidores VNC activos
ps aux | grep -E "(Xtigervnc|x11vnc|Xvnc)"

# Ver puertos en escucha
ss -tlnp | grep 590

# Ver logs de VNC
cat ~/.vnc/*.log

# Ver estado del servicio
sudo systemctl status vncserver@1

# Ver logs del servicio
journalctl -u vncserver@1 --no-pager

# Verificar conectividad de red
ping <IP_SERVIDOR>

# Verificar puerto específico
nc -zv <IP> 5901

# Ver firewall
sudo ufw status
```

---

## Limpieza Completa

Si hay problemas persistentes, realizar limpieza completa:

```bash
# 1. Detener todos los servidores VNC
vncserver -kill :*

# 2. Matar procesos restantes
pkill -f Xtigervnc
pkill -f x11vnc

# 3. Limpiar archivos de bloqueo
rm -f /tmp/.X*-lock
rm -f /tmp/.X11-unix/X*

# 4. Verificar limpieza
ps aux | grep vnc
ss -tlnp | grep 590

# 5. Reiniciar desde cero
vncserver :1
```

---

## Verificación de Funcionamiento

Lista de verificación para confirmar que todo funciona:

```bash
# 1. Servidor corriendo
ps aux | grep Xtigervnc
# Debe mostrar proceso

# 2. Puerto escuchando en todas las interfaces
ss -tlnp | grep 5901
# Debe mostrar 0.0.0.0:5901

# 3. Firewall permite conexión
sudo ufw status | grep 5901
# Debe mostrar ALLOW

# 4. Contraseña existe
ls -la ~/.vnc/passwd
# Debe existir y tener permisos -rw-------

# 5. Script de inicio existe y es ejecutable
ls -la ~/.vnc/xstartup
# Debe tener permisos -rwx------
```
