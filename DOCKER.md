# PiControl en Docker — Raspberry Pi ARM64

Docker Compose es la instalación elegida para este proyecto. La configuración predeterminada ejecuta simulación. Para habilitar el control real desde /opt/pi_control, sigue REAL.md; incluye un archivo Compose adicional y comprobación SSH previa.

## Instalar desde GitHub en la Raspberry

Repositorio: https://github.com/davincirizo/pi_control

Ejecuta dentro de la Raspberry:

```bash
sudo apt install -y git
git clone https://github.com/davincirizo/pi_control.git ~/pi_control_github
cd ~/pi_control_github
sudo docker compose config --quiet
sudo docker compose up -d --build
sudo docker compose ps
sudo docker compose logs --tail=50
```

Se usa una carpeta nueva para conservar cualquier instalación previa en ~/pi_control. Si ~/pi_control_github ya existe, comprueba que sea este repositorio antes de reutilizarla.
Si el repositorio es privado, necesitarás autenticar Git en la Raspberry con acceso de lectura. No escribas tokens en la URL ni los compartas por chat.

La imagen Python 3.13 slim sobre Debian trixie admite ARM64. La construcción ejecuta las ocho pruebas y se detiene si fallan. No hace falta instalar Python ni sus dependencias en el host.

## Actualizar desde GitHub

```bash
cd ~/pi_control_github
git pull --ff-only
sudo docker compose up -d --build
sudo docker compose ps
```

Los datos del volumen se conservan al reconstruir. Si editaste archivos versionados en la Raspberry y Git informa de un conflicto, conserva tus cambios antes de continuar.

## Abrir desde Windows

En otra ventana PowerShell, abre este túnel y mantenlo funcionando:

```powershell
ssh -N -o ExitOnForwardFailure=yes -L 8081:127.0.0.1:8080 admin@raspberrypi
```

Abre http://127.0.0.1:8081. Este puerto distingue el panel de la Raspberry de la vista previa Windows en 8080.
Es normal que SSH no muestre texto mientras el túnel está activo. Ctrl+C cierra el túnel, pero el contenedor sigue ejecutándose.

El panel escucha solo en localhost. Con network_mode: host, comparte la red de la Raspberry, por lo que no se publican puertos en Compose. Esta red también prepara el envío de broadcast para el futuro Wake-on-LAN.
Todavía no hay acceso web directo por IP/Tailscale ni autenticación propia del panel; el acceso se realiza a través del túnel SSH.
El alias raspberrypi del PC usa la IP Tailscale 100.114.213.108.

## Persistencia y operación

Horarios e historial se guardan en el volumen picontrol_picontrol_data. No se migran los datos de prueba de Windows. La configuración se monta de solo lectura desde config.example.json. Tras cambiarla, reinicia el contenedor.

```bash
cd ~/pi_control_github
sudo docker compose ps
sudo docker compose logs --tail=50
sudo docker compose restart
```

Para detener sin borrar datos: `sudo docker compose down`. No añadas `-v` si quieres conservar horarios e historial.
El contenedor vuelve a arrancar tras reiniciar la Raspberry salvo que lo hayas detenido. Usa un usuario sin privilegios, no monta el socket Docker y limita memoria y tamaño de logs.

## Verificación pendiente

La configuración Compose se valida en Windows. Docker Desktop no está iniciado aquí, por lo que la construcción y el estado healthy deben confirmarse en la Raspberry.
La siguiente etapa es configurar SSH dedicado y probar Wake-on-LAN antes de implementar y habilitar acciones reales.

Referencias: [redes de Compose](https://docs.docker.com/compose/how-tos/networking/), [imagen Python](https://hub.docker.com/_/python/tags?name=3.13-slim).
