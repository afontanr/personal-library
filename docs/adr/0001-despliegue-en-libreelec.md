# Despliegue en la Raspberry Pi (LibreELEC) sin compose ni registro

La app corre en una Raspberry Pi 5 con LibreELEC, cuyo add-on de Docker no trae `docker compose` ni `git` y cuyo sistema es de solo lectura salvo `/storage`. Por eso el `docker-compose.yml` de este repo es solo para el portátil, y en la Pi la app es un servicio más (`library`, con `caddy` delante para HTTPS) del repo `kodi-raspberrypi-mediacenter`, que ya gestiona el resto de contenedores con scripts POSIX `sh` y `docker run`. La imagen se construye en el portátil para arm64 y se envía con `docker save | ssh … docker load` (`scripts/deploy-pi.sh`) en lugar de publicarse en un registro.

## Considered Options

- **Instalar el binario de `docker-compose` en `/storage`**: un único fichero de despliegue, pero un binario más que mantener a mano en LibreELEC y una forma de gestión distinta a la del resto de servicios de la Pi.
- **Scripts propios en este repo**: duplicarían el patrón del mediacenter (red, `BASE_DIR`, arranque, actualización).
- **Publicar en GHCR**: `update.sh` funcionaría sin cambios, pero exige CI o push manual y una imagen pública o credenciales en la Pi, sin aportar nada para un único usuario.
- **Construir en la Pi**: sin `git` hay que copiar el código en cada actualización y depender del builder del add-on.

## Consequences

- `update.sh` del mediacenter no hace `docker pull` de `personal-library:latest` (imagen local): solo recrea el contenedor si la imagen cargada cambió.
- HTTPS (necesario para la cámara del escáner fuera de `localhost`) lo pone Caddy con `tls internal`; su CA raíz se persiste en el disco externo y hay que instalarla una vez en cada móvil.
- El contenedor corre sin privilegios: si el disco externo no está montado al arrancar, Docker crea el directorio de datos en la SD como root, la app no puede crear la BD y falla en vez de arrancar con una colección vacía.
