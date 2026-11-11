# Chat en tiempo real (Python + sockets TCP + hilos + Docker)

Servidor TCP en Docker y dos clientes en terminales de VS Code.
Los mensajes se identifican como `[CLIENTE 1]`, `[CLIENTE 2]` y `[SERVIDOR]`.

## Archivos
- `serverConjuntaP1.py`: servidor (un hilo por cliente + un hilo para el teclado del servidor).
- `clientConjuntaP1.py`: cliente (un hilo recibe, el principal envía: sin turnos).
- `Dockerfile` y `docker-compose.yml`: ejecutan el servidor y publican el puerto 5000.

## Cómo ejecutar
Requisitos: Docker Desktop en ejecución y Python 3.

### 1. Servidor (Docker)
```bash
docker compose up -d --build
docker logs -f chat_servidor      # ver la actividad del servidor
```
Para escribir como `[SERVIDOR]` desde el contenedor:
```bash
docker attach chat_servidor       # salir sin detenerlo: Ctrl+P, Ctrl+Q
```

### 2. Entorno virtual (para los clientes)
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```
(No hay dependencias externas, solo la librería estándar.)

### 3. Cliente 1 y Cliente 2
Abrir **dos terminales** en VS Code, activar el venv en cada una y ejecutar:
```powershell
python clientConjuntaP1.py
```
El primero en conectarse es `CLIENTE 1` y el segundo `CLIENTE 2`. Un tercero recibe "Chat lleno".
Escribir un mensaje y pulsar Enter; todos pueden escribir al mismo tiempo.

### 4. Detener
```bash
docker compose down
```
