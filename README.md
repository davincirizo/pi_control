# PiControl

Panel local para preparar el control de dos servidores Ubuntu desde una Raspberry Pi 3B+ con Debian 13.

## Estado de esta versión

**Simulación por defecto y control real opcional.** Para activar SSH y Wake-on-LAN en Docker bajo /opt/pi_control, sigue [REAL.md](REAL.md). El modo real utiliza una base de datos independiente y requiere configuración y clave SSH locales. En simulación no se contacta a los equipos. Incluye panel adaptable a móvil, acciones manuales simuladas, horarios semanales persistentes, pausa/eliminación de horarios y los últimos 100 eventos.

Configuración: `config.example.json`. Los equipos son `server1@server1` y `david@servidorIA` (IP local conocida: `10.0.0.245`). Controlador previsto: `admin@raspberrypi`. Los tres comparten red Ethernet y tienen Tailscale. Zona horaria: **America/Chicago**, con cambios de horario de verano.

## Instalación elegida: Docker Compose

Para desplegar en la Raspberry, sigue [DOCKER.md](DOCKER.md). Los pasos con venv de abajo quedan como alternativa de desarrollo local.

## Ejecutar

En este PC se incluye `preview.ps1` y las dependencias locales en `.deps` para abrir la vista previa con el Python integrado de Codex. Desde PowerShell: `& C:\IT\pi_control\preview.ps1`. Este acceso depende del runtime de Codex de este PC; la instalación portable se describe a continuación.

Requiere Python 3.10 o posterior. Desde la carpeta del proyecto, en Windows:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe app.py
```

En Debian, cuando se decida copiar el proyecto a la Raspberry:

```bash
sudo apt install python3-venv
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python app.py
```

Abrir http://127.0.0.1:8080. Cambiar puerto con `python app.py --port 8081`.

La escucha se limita a localhost; esta versión no tiene inicio de sesión y todavía no se publica en la red. Para revisar un panel que ya se esté ejecutando en la Raspberry, puede usarse un túnel SSH desde el PC:

```powershell
ssh -L 8081:127.0.0.1:8080 admin@raspberrypi
```

En ese caso se abre http://127.0.0.1:8081 en el PC. No es necesario copiar claves privadas al proyecto.

## Persistencia y horarios

- SQLite en `data/picontrol.sqlite3`, creada en el primer inicio. No se incluye en el código fuente.
- Un proceso integrado revisa los horarios cada cinco segundos mientras `app.py` está ejecutándose. Cerrar el navegador no detiene el proceso; cerrar el proceso sí.
- Un horario actúa en su minuto exacto. Se omiten los minutos perdidos mientras el proceso estaba detenido. Si se inicia dentro del minuto programado, la acción sí puede ejecutarse.
- Una transacción SQLite registra la ejecución y su resultado simulado conjuntamente; reiniciar o ejecutar dos revisiones no duplica la misma regla en el mismo minuto local.
- En otoño, la hora repetida se ejecuta una sola vez; en primavera, una hora inexistente se omite.
- Las acciones simuladas y las reglas persisten al reiniciar. El estado inicial es «Sin simular», no un estado real inventado.
- El historial se muestra en Chicago. No hay política de limpieza automática de la base de datos en esta primera versión.

## Verificación

```powershell
.\.venv\Scripts\python.exe -m unittest -v
```

Las pruebas cubren validación, CSRF, restricción del host, confirmación de apagado, persistencia, pausa/eliminación, horarios perdidos, ambos cambios de hora de Chicago y rechazo del modo real.

## Siguiente etapa: conectar los equipos

1. Completado por el usuario: probar SSH desde la Raspberry con una clave dedicada para automatización y órdenes limitadas. Las claves personales existentes usan frase de contraseña; no se necesitan para desarrollar el panel.
2. Obtener la MAC e interfaz Ethernet de cada Ubuntu y verificar Wake-on-LAN en sistema, tarjeta y BIOS/UEFI.
3. Añadir comprobación real de disponibilidad y distinguir «no accesible» de «apagado».
4. Añadir autenticación, permisos y pruebas del ejecutor antes de habilitar acciones reales.
5. Preparar servicio systemd y acceso privado por Tailscale.

El usuario ya instaló Docker y el panel en simulación en la Raspberry, y verificó SSH y los permisos sudo en los servidores. La actualización real requiere ejecutar los pasos de REAL.md. No se han probado apagados o reinicios reales desde el panel.

Referencias: [Flask](https://flask.palletsprojects.com/en/stable/), [zoneinfo de Python](https://docs.python.org/3/library/zoneinfo.html).
