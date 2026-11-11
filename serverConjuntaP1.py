# ---------------------------------------------------------------------------
# SERVIDOR DE CHAT (TCP + hilos)
#
# Funcionamiento general:
#   - El servidor escucha en el puerto 5000 y acepta hasta 2 clientes a la vez.
#   - Cada cliente que se conecta recibe un número: CLIENTE 1 o CLIENTE 2.
#   - Hay UN HILO POR CLIENTE que lee sus mensajes y los reenvía al otro.
#   - Hay un hilo más para el teclado del servidor, así el servidor también
#     puede escribir ([SERVIDOR]) sin esperar turnos.
#   - Corre dentro de Docker (ver Dockerfile y docker-compose.yml).
# ---------------------------------------------------------------------------
import socket      # comunicación por red (sockets TCP)
import threading   # hilos para atender a varios participantes a la vez

# "0.0.0.0" = escuchar en todas las interfaces. Es necesario dentro de Docker,
# si fuera "127.0.0.1" el contenedor no aceptaría conexiones desde afuera.
HOST = "0.0.0.0"
PORT = 5000          # puerto publicado en docker-compose.yml (5000:5000)
MAX_CLIENTES = 2     # el examen pide exactamente dos clientes

# Canales de los clientes conectados: {1: canal, 2: canal}
clientes = {}
# Lock para que los hilos no modifiquen 'clientes' al mismo tiempo
# (por ejemplo, uno entra mientras el otro sale).
lock = threading.Lock()


def enviar(canal, texto):
    # Envía una línea a un cliente; si ya se cayó, se ignora
    try:
        # Cada mensaje termina en "\n": así el receptor sabe dónde acaba (readline)
        canal.write((texto + "\n").encode("utf-8"))
        canal.flush()    # fuerza el envío inmediato, sin esperar a llenar el buffer
    except (OSError, ValueError):
        pass


def difundir(texto, excepto=None):
    # Muestra el mensaje en el servidor y lo manda a todos menos al emisor
    # \r\x1b[K borra el "Servidor: " pendiente y luego se vuelve a mostrar
    # (\r = volver al inicio de la línea, \x1b[K = borrar hasta el final)
    print("\r\x1b[K" + texto)
    print("Servidor: ", end="", flush=True)
    # Se bloquea mientras se recorre el diccionario porque otro hilo podría
    # agregar o quitar clientes al mismo tiempo.
    with lock:
        for numero, canal in clientes.items():
            if numero != excepto:    # el emisor ya ve lo que escribió
                enviar(canal, texto)


def recibir(numero, conexion, canal):
    # Hilo que escucha mensajes de un cliente en cualquier momento
    # (se crea uno por cada cliente conectado)
    etiqueta = "CLIENTE " + str(numero)
    # Le avisa al cliente quién es, y a los demás que alguien entró
    enviar(canal, "[SERVIDOR]: Conectado como " + etiqueta)
    difundir("[SERVIDOR]: " + etiqueta + " se unió al chat", excepto=numero)
    try:
        while True:
            # readline() espera hasta recibir una línea completa; este hilo
            # queda bloqueado aquí sin frenar a los demás.
            datos = canal.readline()

            # Si no llegan datos, el cliente cerró la conexión
            if not datos:
                break

            mensaje = datos.decode("utf-8").rstrip("\r\n")
            # Reenvía el mensaje con la etiqueta de quien lo escribió
            difundir("[" + etiqueta + "]: " + mensaje, excepto=numero)
    except (OSError, ValueError):
        pass
    finally:
        # Al salir se libera el número, así otro cliente puede usarlo
        with lock:
            clientes.pop(numero, None)
        conexion.close()
        difundir("[SERVIDOR]: " + etiqueta + " salió del chat")


def teclado():
    # Hilo para que el servidor también escriba sin esperar turnos
    # Lo que se escribe aquí se envía a todos los clientes
    while True:
        try:
            mensaje = input()
        except EOFError:
            # Docker sin terminal adjunta: no hay teclado, solo se atiende a los clientes
            break

        if mensaje.lower() == "salir":
            break

        if mensaje:
            # \x1b[F sube una línea y \x1b[K la borra: quita el texto que se acaba de escribir
            print("\x1b[F\x1b[K", end="")
            difundir("[SERVIDOR]: " + mensaje)


# ---------------------------------------------------------------------------
# PROGRAMA PRINCIPAL: crea el socket y acepta conexiones
# ---------------------------------------------------------------------------
servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)   # TCP sobre IPv4
# Permite reiniciar el servidor enseguida sin el error "puerto en uso"
servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
servidor.bind((HOST, PORT))   # asocia el socket a la dirección y puerto
servidor.listen()             # queda a la espera de conexiones

# flush=True: en Docker la salida debe verse enseguida en 'docker logs'
print("Servidor de chat con 2 clientes", flush=True)
print("Esperando conexiones en el puerto", PORT, flush=True)

# Hilo del teclado: daemon=True para que no impida cerrar el programa
print("Servidor: ", end="", flush=True)
hilo_teclado = threading.Thread(target=teclado, daemon=True)
hilo_teclado.start()

try:
    while True:
        # accept() espera hasta que un cliente se conecte
        conexion, direccion = servidor.accept()
        # Convierte el socket en un archivo de lectura/escritura en bytes
        canal = conexion.makefile("rwb")

        # Busca el primer número libre (1 o 2) bajo el lock
        with lock:
            libres = [n for n in range(1, MAX_CLIENTES + 1) if n not in clientes]
            if libres:
                numero = libres[0]
                clientes[numero] = canal
            else:
                numero = None

        # Si no hay lugar, se avisa y se cierra esa conexión
        if numero is None:
            enviar(canal, "[SERVIDOR]: Chat lleno (máximo 2 clientes)")
            conexion.close()
            continue

        print("Cliente conectado desde:", direccion, "-> CLIENTE", numero, flush=True)
        # Un hilo atiende a este cliente mientras el bucle sigue aceptando otros
        hilo = threading.Thread(target=recibir, args=(numero, conexion, canal), daemon=True)
        hilo.start()
except KeyboardInterrupt:
    pass
finally:
    servidor.close()
