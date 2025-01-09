# Verwende das Python-Slim-Image als Basis
FROM python:3.10-slim

# Arbeitsverzeichnis setzen
WORKDIR /app

# Kopiere die requirements.txt und installiere die Abhängigkeiten
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Kopiere den gesamten Quellcode in das Container-Verzeichnis
COPY . /app/

# Standard-Befehl, um die Flask-Anwendung zu starten
CMD ["python", "app.py"]