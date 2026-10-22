# Control real en /opt/pi_control

Requiere los permisos sudo ya preparados para poweroff/reboot y la clave dedicada que ya funciona desde admin en la Raspberry.
El script no envía órdenes de apagado, reinicio ni Wake-on-LAN durante la preparación: comprueba hostname y lista permisos sudo desde el contenedor.

```bash
cd /opt/pi_control
git pull --ff-only
bash enable-real.sh
```

La comprobación SSH usa verificación estricta y las identidades de servidor previamente aceptadas por admin. Si la prueba falla, se detiene antes de cambiar el servicio en ejecución. Revisa el error y vuelve a ejecutar el script tras corregirlo.

La clave original se conserva en ssh/. Una copia local con permisos para UID 10001 se monta de solo lectura desde runtime-ssh/. Nunca se suben esas carpetas a Git. No se monta el socket Docker.
Configuración real: config.real.json (ignorada por Git). Datos reales: data-real/real.sqlite3, también ignorados. Todos están bajo /opt/pi_control. El volumen anterior de simulación se conserva y no se migra: los horarios reales comienzan vacíos.
El script añade COMPOSE_FILE a .env para que los siguientes comandos docker compose utilicen ambos archivos. Los datos de configuración se conservan en futuras ejecuciones del script.

El acceso sigue siendo por el túnel SSH existente a http://127.0.0.1:8081. Recarga la página después de actualizar (la sesión anterior caduca).

## Qué confirma el panel

- Accesible: el puerto SSH responde, no es una comprobación de todos los servicios.
- No accesible: puede estar apagado o existir un fallo de red.
- Wake-on-LAN enviado: no garantiza que el hardware arranque. La primera prueba real desde Raspberry sigue pendiente.
- Orden aceptada por SSH: no garantiza que el apagado/reinicio haya terminado.
- Un cierre SSH inesperado o timeout se registra como resultado no confirmado, sin reintentos automáticos.

Los botones de apagar/reiniciar piden confirmación. Guardar un horario lo activa, tal como indica el formulario.
Las acciones reales se registran antes de enviarse. Si se interrumpe el contenedor, las pendientes quedan con resultado desconocido y no se repiten. Esto evita repetir apagados, pero requiere revisión manual cuando un proceso se interrumpe.

## Actualización y diagnóstico

```bash
cd /opt/pi_control
git pull --ff-only
sudo docker compose up -d --build
sudo docker compose ps
sudo docker compose logs --tail=50
```

No publiques el puerto 8080 directamente: esta versión confía en el túnel SSH para autenticar el acceso y escucha solamente en localhost.
No se ha ejecutado ninguna prueba de apagado/reinicio en los servidores desde el desarrollo. Las pruebas automatizadas simulan las llamadas SSH y UDP.

Referencia de verificación de claves: https://man.openbsd.org/ssh_config
