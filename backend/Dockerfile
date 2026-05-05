FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ .

# Create a writable directory for the SQLite database
RUN mkdir -p /data

ENV DB_DIR=/data

EXPOSE 5000

CMD ["python", "main.py"]
