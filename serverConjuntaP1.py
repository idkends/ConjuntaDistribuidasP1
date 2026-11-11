import socket
import threading

HOST = "0.0.0.0"
PORT = 5000
MAX_CLIENTES = 2

# Canales de los clientes conectados: {1: canal, 2: canal}
clientes = {}
# Lock para que los hilos no modifiquen 'clientes' al mismo tiempo
lock = threading.Lock()


def enviar(canal, texto):
    # Envía una línea a un cliente; si ya se cayó, se ignora
    try:
        canal.write((texto + "\n").encode("utf-8"))
        canal.flush()
    except (OSError, ValueError):
        pass


def difundir(texto, excepto=None):
    # Muestra el mensaje en el servidor y lo manda a todos menos al emisor
    # \r\x1b[K borra el "Servidor: " pendiente y luego se vuelve a mostrar
    print("\r\x1b[K" + texto)
    print("Servidor: ", end="", flush=True)
    with lock:
        for numero, canal in clientes.items():
            if numero != excepto:
                enviar(canal, texto)


def recibir(numero, conexion, canal):
    # Hilo que escucha mensajes de un cliente en cualquier momento
    etiqueta = "CLIENTE " + str(numero)
    enviar(canal, "[SERVIDOR]: Conectado como " + etiqueta)
    difundir("[SERVIDOR]: " + etiqueta + " se unió al chat", excepto=numero)
    try:
        while True:
            datos = canal.readline()

            if not datos:
                break

            mensaje = datos.decode("utf-8").rstrip("\r\n")
            difundir("[" + etiqueta + "]: " + mensaje, excepto=numero)
    except (OSError, ValueError):
        pass
    finally:
        with lock:
            clientes.pop(numero, None)
        conexion.close()
        difundir("[SERVIDOR]: " + etiqueta + " salió del chat")


def teclado():
    # Hilo para que el servidor también escriba sin esperar turnos
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


servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
servidor.bind((HOST, PORT))
servidor.listen()

print("Servidor de chat con 2 clientes", flush=True)
print("Esperando conexiones en el puerto", PORT, flush=True)

print("Servidor: ", end="", flush=True)
hilo_teclado = threading.Thread(target=teclado, daemon=True)
hilo_teclado.start()

try:
    while True:
        conexion, direccion = servidor.accept()
        canal = conexion.makefile("rwb")

        with lock:
            libres = [n for n in range(1, MAX_CLIENTES + 1) if n not in clientes]
            if libres:
                numero = libres[0]
                clientes[numero] = canal
            else:
                numero = None

        if numero is None:
            enviar(canal, "[SERVIDOR]: Chat lleno (máximo 2 clientes)")
            conexion.close()
            continue

        print("Cliente conectado desde:", direccion, "-> CLIENTE", numero, flush=True)
        hilo = threading.Thread(target=recibir, args=(numero, conexion, canal), daemon=True)
        hilo.start()
except KeyboardInterrupt:
    pass
finally:
    servidor.close()
