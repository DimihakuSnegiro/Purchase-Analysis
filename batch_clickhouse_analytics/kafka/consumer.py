import os
import time
import json
from clickhouse_driver import Client as CHClient
from confluent_kafka import Consumer, KafkaError, KafkaException

KAFKA_BOOTSTRAP_SERVERS = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
CLICKHOUSE_HOST = os.getenv('CLICKHOUSE_HOST', 'clickhouse')
CLICKHOUSE_PORT = int(os.getenv('CLICKHOUSE_PORT', '9000'))
CLICKHOUSE_DB = os.getenv('CLICKHOUSE_DB', 'default')
CLICKHOUSE_USER = os.getenv('CLICKHOUSE_USER', 'default')
CLICKHOUSE_PASSWORD = os.getenv('CLICKHOUSE_PASSWORD', '')

ch_client = CHClient(
    host=CLICKHOUSE_HOST,
    port=CLICKHOUSE_PORT,
    database=CLICKHOUSE_DB,
    user=CLICKHOUSE_USER,
    password=CLICKHOUSE_PASSWORD
)

print("=== CONSUMER STARTED ===")
print(f"ClickHouse host: {CLICKHOUSE_HOST}:{CLICKHOUSE_PORT}")
print(f"Kafka bootstrap servers: {KAFKA_BOOTSTRAP_SERVERS}")

def run_consumer(topic_name='purchases'):
    conf = {
        'bootstrap.servers': KAFKA_BOOTSTRAP_SERVERS,
        'group.id': 'clickhouse-consumer-group',
        'auto.offset.reset': 'earliest'
    }

    consumer = Consumer(conf)
    consumer.subscribe([topic_name])
    print(f"Подписка на топик: {topic_name}")

    try:
        while True:
            msg = consumer.poll(timeout=1.0)
            if msg is None:
                continue

            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    print(f"Конец партиции {msg.topic()} [{msg.partition()}] на offset {msg.offset()}")
                else:
                    print(f"Kafka ошибка: {msg.error()}")
                    raise KafkaException(msg.error())
                continue

            try:
                value_str = msg.value().decode('utf-8')
                print("Получено сообщение:", value_str)
                record = json.loads(value_str)
            except Exception as e:
                print(f"Ошибка при обработке сообщения: {e}")
                continue

            try:
                sell_id = record['sell_id']
                customer_id = record['customer_id']
                product_id = record['product_id']
                seller_id = record['seller_id']
                quantity = record['quantity']
                print("Данные для вставки:", sell_id, customer_id, product_id, seller_id, quantity)
            except KeyError as e:
                print(f"Пропущено поле в данных: {e}")
                continue

            try:
                ch_client.execute("""
                    INSERT INTO fact_sales (sale_id, customer_id, product_id, seller_id, quantity)
                    VALUES
                """, [(sell_id, customer_id, product_id, seller_id, quantity)])
                print("Вставлено сообщение в ClickHouse")
            except Exception as e:
                print(f"Ошибка при вставке в ClickHouse: {e}")

    except KeyboardInterrupt:
        print("Остановка консюмера вручную")
    finally:
        consumer.close()
        print("Консьюмер закрыт")

if __name__ == "__main__":
    time.sleep(3)
    run_consumer()
