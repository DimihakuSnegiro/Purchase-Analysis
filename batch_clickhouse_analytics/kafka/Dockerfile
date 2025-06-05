FROM python:3.11-slim

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
      gcc \
      librdkafka-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY consumer.py /app/consumer.py

RUN pip install --no-cache-dir confluent-kafka clickhouse-driver

CMD ["python", "/app/consumer.py"]
