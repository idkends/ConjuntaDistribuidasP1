# Imagen ligera de Python para el servidor de chat
FROM python:3.12-slim
WORKDIR /app
COPY serverConjuntaP1.py .
EXPOSE 5000
# -u: salida sin buffer para ver los logs en tiempo real
CMD ["python", "-u", "serverConjuntaP1.py"]
