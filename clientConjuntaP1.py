# ---------------------------------------------------------------------------
# CLIENTE DE CHAT (TCP + hilos)
#
# Funcionamiento general:
#   - Se conecta al servidor (que corre en Docker) por el puerto 5000.
#   - Un HILO recibe e imprime los mensajes que llegan del servidor.
#   - El HILO PRINCIPAL lee el teclado y envía lo que se escribe.
#   - Como son dos hilos distintos, se puede escribir y recibir al mismo
#     tiempo, sin esperar turnos.
#
# Uso:  python clientConjuntaP1.py            (servidor en esta misma PC)
#       python clientConjuntaP1.py <ip>       (servidor en otra PC)
# ---------------------------------------------------------------------------
import socket      # comunicación por red (sockets TCP)
import sys         # para leer argumentos de la línea de comandos
import threading   # hilo que recibe mensajes

# Si se pasa una IP como argumento se usa esa; si no, el servidor local
HOST = sys.argv[1] if len(sys.argv) > 1 else "127.0.0.1"
PORT = 5000    # puerto que Docker publica en la computadora anfitriona


def recibir(canal, terminado):
    # Hilo que escucha mensajes del servidor en cualquier momento
    # 'terminado' es una señal compartida: cuando se activa, todo debe cerrarse
    try:
        while not terminado.is_set():
            # readline() espera una línea completa; solo bloquea a este hilo
            datos = canal.readline()

            # Sin datos = el servidor cerró la conexión
            if not datos:
                print("\r\x1b[KServidor desconectado")
                break

            respuesta = datos.decode("utf-8").rstrip("\r\n")
            # \r vuelve al inicio y \x1b[K borra la línea del "Yo: " pendiente,
            # así el mensaje no queda mezclado con lo que se está escribiendo
            print("\r\x1b[K" + respuesta)
            print("Yo: ", end="", flush=True)    # vuelve a mostrar el prompt
    except (OSError, ValueError):
        pass
    finally:
        # Avisa al hilo principal que debe terminar
        terminado.set()


# ---------------------------------------------------------------------------
# PROGRAMA PRINCIPAL: conectar, lanzar el hilo receptor y enviar mensajes
# ---------------------------------------------------------------------------
cliente = socket.socket(socket.AF_INET, socket.SOCK_STREAM)   # TCP sobre IPv4
cliente.connect((HOST, PORT))    # se conecta al servidor

print("Cliente de chat")
print("Conectado al servidor")
print("Escribe 'salir' para terminar")

# Convierte el socket en un archivo de lectura/escritura en bytes
canal = cliente.makefile("rwb")

# Event: bandera compartida entre el hilo principal y el hilo receptor
terminado = threading.Event()
# daemon=True: si el programa principal termina, este hilo se cierra solo
hilo = threading.Thread(target=recibir, args=(canal, terminado), daemon=True)
hilo.start()

try:
    # El hilo principal envía mensajes cuando el usuario quiera
    while not terminado.is_set():
        mensaje = input("Yo: ")

        # Sale si el servidor se cayó o si el usuario escribió 'salir'
        if terminado.is_set() or mensaje.lower() == "salir":
            break

        # Cada mensaje termina en "\n" para que el servidor sepa dónde acaba
        canal.write((mensaje + "\n").encode("utf-8"))
        canal.flush()    # envío inmediato
except (EOFError, KeyboardInterrupt, OSError):
    pass
finally:
    # Limpieza: avisa al otro hilo y cierra la conexión
    terminado.set()
    try:
        cliente.shutdown(socket.SHUT_RDWR)
    except OSError:
        pass
    cliente.close()
