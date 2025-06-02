import os
import time
import uuid
import random
import json
from confluent_kafka import Producer

# Читаем адрес брокера из переменной среды
bootstrap_servers = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')

def delivery_report(err, msg):
    """
    Callback-функция, вызываемая при подтверждении доставки сообщения.
    Если err не None – произошла ошибка.
    """
    if err is not None:
        print(f"Ошибка при доставке сообщения: {err}")
    else:
        print(
            f"Доставлено: topic={msg.topic()}, partition={msg.partition()}, "
            f"offset={msg.offset()}, key={msg.key().decode('utf-8') if msg.key() else None}, "
            f"value={msg.value().decode('utf-8')}"
        )


def run_producer(topic_name='purchases'):
    conf = {
        'bootstrap.servers': bootstrap_servers,
        'client.id': 'sql-data-producer'
    }
    producer = Producer(conf)

    # Ждём, чтобы топик точно был создан
    print(f"Producer ждёт 5 секунд перед отправкой, чтобы топик '{topic_name}' точно существовал...")
    time.sleep(5)

    for i in range(10):
        # Формируем запись по схеме SQL таблицы:
        record = {
            'customer_id': random.randint(1, 2**63),  # Uint64
            'sell_id': str(uuid.uuid4()),              # UUID
            'product_id': str(uuid.uuid4()),           # UUID
            'price': round(random.uniform(1.0, 1000.0), 2),  # Float32
            'seller_id': random.randint(1, 2**63)       # UInt64
        }
        # Сериализуем в JSON
        value = json.dumps(record).encode('utf-8')
        # Ключ можно не передавать или использовать какую-то логику
        producer.produce(
            topic=topic_name,
            key=None,
            value=value,
            callback=delivery_report
        )
        # Обрабатываем callback-и доставки
        producer.poll(0)
        time.sleep(1)

    # Ждём, пока все сообщения будут отправлены
    producer.flush()

if __name__ == "__main__":
    run_producer()