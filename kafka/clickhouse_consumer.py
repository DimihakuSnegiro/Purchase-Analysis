import os
import time
import json
from confluent_kafka import Consumer, KafkaError, KafkaException

bootstrap_servers = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')

def run_consumer(topic_name='purchases'):
    conf = {
        'bootstrap.servers': bootstrap_servers,
        'group.id': 'clickhouse-consumer-group',
        'auto.offset.reset': 'earliest'
    }

    consumer = Consumer(conf)
    consumer.subscribe([topic_name])

    print(f"Консъюмер запущен")
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

                # здесь должен быть запрос с обновлением бд clickhouse<------------------------------------------------------------!!!!!!!!!!

    except KeyboardInterrupt:
        print("Остановка консъюмера")
    finally:
        consumer.close()

if __name__ == "__main__":
    time.sleep(3)
    run_consumer()