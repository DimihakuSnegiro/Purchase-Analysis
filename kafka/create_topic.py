from confluent_kafka.admin import AdminClient, NewTopic
import os

bootstrap_servers = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')

def create_topic():
    admin_conf = {
        'bootstrap.servers': bootstrap_servers,
        'client.id': 'admin'
    }
    admin_client = AdminClient(admin_conf)

    topic_name = 'purchases'
    new_topic = NewTopic(
        topic=topic_name,
        num_partitions=1,
        replication_factor=1
    )