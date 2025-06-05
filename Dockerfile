# Gebruik een lichte Python image
FROM python:3.11-slim

# Zet werkdirectory
WORKDIR /app

# Vereisten kopiëren
COPY requirements.txt .

# Installeer vereisten
RUN PIP_NO_PROGRESS_BAR=off PIP_DISABLE_PIP_VERSION_CHECK=1 PYTHONWARNINGS=ignore pip install --no-cache-dir --progress-bar=off -r requirements.txt

# Kopieer de rest van de code
COPY shuffle_2.py .
COPY credentials.json .

# Maak output- en inputmappen aan (in container)
#RUN mkdir -p /data/repo_3_reduced_votes /data/repo_5_resultaat

# Standaard commando
CMD ["python", "shuffle_2.py"]
