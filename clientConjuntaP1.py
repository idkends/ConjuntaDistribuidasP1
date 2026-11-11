import socket
import sys
import threading

HOST = sys.argv[1] if len(sys.argv) > 1 else "127.0.0.1"
PORT = 5000


def recibir(canal, terminado):
    # Hilo que escucha mensajes del servidor en cualquier momento
    try:
        while not terminado.is_set():
            datos = canal.readline()

            if not datos:
                print("\r\x1b[KServidor desconectado")
                break

            respuesta = datos.decode("utf-8").rstrip("\r\n")
            # \r vuelve al inicio y \x1b[K borra la línea del "Yo: " pendiente
            print("\r\x1b[K" + respuesta)
            print("Yo: ", end="", flush=True)
    except (OSError, ValueError):
        pass
    finally:
        terminado.set()


cliente = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
cliente.connect((HOST, PORT))

print("Cliente de chat")
print("Conectado al servidor")
print("Escribe 'salir' para terminar")

canal = cliente.makefile("rwb")

terminado = threading.Event()
hilo = threading.Thread(target=recibir, args=(canal, terminado), daemon=True)
hilo.start()

try:
    # El hilo principal envía mensajes cuando el usuario quiera
    while not terminado.is_set():
        mensaje = input("Yo: ")

        if terminado.is_set() or mensaje.lower() == "salir":
            break

        canal.write((mensaje + "\n").encode("utf-8"))
        canal.flush()
except (EOFError, KeyboardInterrupt, OSError):
    pass
finally:
    terminado.set()
    try:
        cliente.shutdown(socket.SHUT_RDWR)
    except OSError:
        pass
    cliente.close()
