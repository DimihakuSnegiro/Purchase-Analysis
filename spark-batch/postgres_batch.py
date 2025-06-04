import logging
from clickhouse_driver import Client
import os
from pyspark.sql import SparkSession
from pyspark.sql.functions import max as spark_max, lit
from datetime import datetime

logging.basicConfig(level=logging.INFO)

spark = SparkSession.builder \
    .appName("postgres-batch") \
    .config(
        "spark.jars",
        "/opt/spark-apps/jars/postgresql-42.6.0.jar,/opt/spark-apps/jars/clickhouse-jdbc-0.4.6.jar"
    ) \
    .getOrCreate()

postgres_url = f"jdbc:postgresql://postgres:5432/{os.getenv('POSTGRES_DB')}"
postgres_properties = {
    "user": os.getenv("POSTGRES_USER"),
    "password": os.getenv("POSTGRES_PASSWORD"),
    "driver": "org.postgresql.Driver"
}

clickhouse_url = "jdbc:clickhouse://clickhouse:8123/default"
clickhouse_properties = {
    "user": os.getenv("CLICKHOUSE_USER"),
    "password": os.getenv("CLICKHOUSE_PASSWORD"),
    "driver": "com.clickhouse.jdbc.ClickHouseDriver"
}

def optimize_clickhouse_table(table_name):
    try:
        logging.info(f"Optimizing ClickHouse table {table_name}...")
        client = Client(
            host='clickhouse',
            user=os.getenv('CLICKHOUSE_USER'),
            password=os.getenv('CLICKHOUSE_PASSWORD'),
            database='default'
        )
        client.execute(f"OPTIMIZE TABLE {table_name} FINAL")
        logging.info(f"OPTIMIZE TABLE FINAL executed for {table_name}")
    except Exception as e:
        logging.error(f"Failed to optimize ClickHouse table {table_name}: {e}")


def sync_table(table_name, batch_time):
    logging.info(f"Start syncing table: {table_name}")
    try:
        ch_df = spark.read.jdbc(clickhouse_url, table_name, properties=clickhouse_properties)

        if ch_df.rdd.isEmpty():
            last_batch_time = "1970-01-01 00:00:00"
            logging.info(f"ClickHouse table {table_name} is empty. Using default last_batch_time.")
        else:
            last_batch_time = ch_df.agg(spark_max("batch_time")).collect()[0][0]
            if last_batch_time is None:
                last_batch_time = "1970-01-01 00:00:00"
            logging.info(f"Last batch_time from ClickHouse: {last_batch_time}")

        query = f"(SELECT * FROM {table_name} WHERE created_at > TIMESTAMP '{last_batch_time}') AS src"
        pg_df = spark.read.jdbc(postgres_url, query, properties=postgres_properties)

        if pg_df.rdd.isEmpty():
            logging.info(f"No new records to sync for {table_name}.")
        else:
            count = pg_df.count()
            logging.info(f"Found {count} new records to sync for {table_name}.")

            enriched_df = pg_df.withColumn("batch_time", lit(batch_time))
            enriched_df.write \
                .mode("append") \
                .jdbc(clickhouse_url, table_name, properties=clickhouse_properties)

            logging.info(f"Inserted {count} records into {table_name}.")

        logging.info(f"Finished syncing table: {table_name} ---\n")
    except Exception as e:
        logging.error(f"Error syncing table {table_name}: {e}")


if __name__ == "__main__":
    current_batch_time = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
    logging.info(f"Using common batch_time: {current_batch_time}")

    tables = ["customers", "sellers"]
    for table in tables:
        sync_table(table, current_batch_time)
        optimize_clickhouse_table(table)

    spark.stop()
    logging.info("Spark session stopped")