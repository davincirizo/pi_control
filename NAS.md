# Añadir nas-server desde GitHub

El perfil versionado está en servers/nas-server.json. La configuración real, claves y horarios permanecen solo en la Raspberry.

Preparación ya realizada por el usuario: Wake-on-LAN activado y persistido con Netplan en enp2s0; clave de PiControl autorizada para david; conexión SSH desde Raspberry comprobada; sudoers poweroff/reboot validado.

En la Raspberry:

```bash
cd /opt/pi_control
git pull --ff-only
bash add-nas.sh
```

El script comprueba hostname y permisos sudo desde el contenedor solo para el NAS. No envía órdenes de energía. Si falla, no añade el servidor ni reinicia el panel. Si pasa, guarda una copia de config.real.json, añade el NAS sin modificar otros equipos y recrea únicamente PiControl conservando sus datos. Puede repetirse sin duplicar el NAS. Una entrada existente con valores distintos requiere revisión manual.

La dirección 10.0.0.224 fue obtenida por DHCP. Reserva esa dirección para la MAC 00:e0:4c:79:95:e5 en el router para evitar que cambie. La prueba real de encendido remoto sigue pendiente; la compatibilidad y configuración de la tarjeta no prueban por sí solas el arranque desde apagado.

Las copias config.real.json.bak-* y archivos temporales .picontrol-add.* están excluidos de Git. No se modifican los contenedores ni el token de Cloudflare.
