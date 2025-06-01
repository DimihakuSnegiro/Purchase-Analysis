FROM python:3.9-slim
RUN pip install --no-cache-dir confluent-kafka
WORKDIR /app
COPY create_topic.py producer.py clickhouse_consumer.py ./
ENTRYPOINT ["python"]