import os
import time
import json
from clickhouse_driver import Client as CHClient
from confluent_kafka import Consumer, KafkaError, KafkaException

bootstrap_servers = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
CLICKHOUSE_HOST = os.getenv('CLICKHOUSE_HOST', 'clickhouse')
CLICKHOUSE_PORT = int(os.getenv('CLICKHOUSE_PORT', '9000'))
CLICKHOUSE_PORT = int(os.getenv('CLICKHOUSE_PORT', 9000))
CLICKHOUSE_DB = os.getenv('CLICKHOUSE_DB', 'default')

ch_client = CHClient(host=CLICKHOUSE_HOST, port=CLICKHOUSE_PORT, database=CLICKHOUSE_DB)

def run_consumer(topic_name='purchases'):
    conf = {
        'bootstrap.servers': bootstrap_servers,
        'group.id': 'clickhouse-consumer-group',
        'auto.offset.reset': 'earliest'
    }

    consumer = Consumer(conf)
    consumer.subscribe([topic_name])

    print("Консъюмер запущен (ClickHouse)")
    try:
        while True:
            msg = consumer.poll(timeout=1.0)
            if msg is None:
                continue
            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    print(
                        f"Конец партиции {msg.topic()} "
                        f"[{msg.partition()}] на offset {msg.offset()}"
                    )
                else:
                    raise KafkaException(msg.error())
            else:
                value_str = msg.value().decode('utf-8')
                try:
                    record = json.loads(value_str)
                except json.JSONDecodeError as e:
                    print(f"Ошибка декодирования JSON: {e}")
                    continue

                customer_id = record.get('customer_id')
                sell_id = record.get('sell_id')
                product_id = record.get('product_id')
                price = record.get('price')
                seller_id = record.get('seller_id')
                quantity = record.get('quantity')

                try:
                    ch_client.execute(
                        """
                        INSERT INTO fact_sales (sale_id, customer_id, product_id, seller_id, quantity, price)
                        VALUES
                    """,
                        [(sell_id, customer_id, product_id, seller_id, quantity, price)]
                    )
                    print("Вставлено сообщение в ClickHouse")
                except Exception as e:
                    print(f"Ошибка при вставке в ClickHouse: {e}")

    except KeyboardInterrupt:
        print("Остановка консюмера")
    finally:
        consumer.close()

if __name__ == "__main__":
    time.sleep(3)
    run_consumer()