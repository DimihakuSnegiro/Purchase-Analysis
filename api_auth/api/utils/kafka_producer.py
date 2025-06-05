from confluent_kafka import Producer, KafkaException
import json

producer = Producer({
    'bootstrap.servers': 'kafka:9092',
    'message.timeout.ms': 5000,
    'retries': 3
})

def delivery_report(err, msg):
    if err:
        print(f"Ошибка доставки: {err}")
    else:
        print(f"Доставлено в {msg.topic()} [{msg.partition()}]")

def send_purchase(data):
    try:
        producer.produce(
            topic='purchases',
            value=json.dumps(data).encode('utf-8'),
            callback=delivery_report
        )
        producer.flush(timeout=5)
    except KafkaException as e:
        print(f"Фатальная ошибка Kafka: {e}")
        raise