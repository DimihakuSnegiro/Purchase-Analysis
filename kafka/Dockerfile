FROM python:3.9-slim
RUN pip install --upgrade pip && \
    pip install --no-cache-dir confluent-kafka clickhouse-driver
WORKDIR /app
COPY . /app