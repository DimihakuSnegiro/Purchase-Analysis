import os
import datetime
import logging
from pyspark.sql import SparkSession
from pyspark.sql.functions import lit

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

def create_spark_session(bucket_name, minio_endpoint, minio_user, minio_password):
    logging.info("Создаём SparkSession...")
    spark = SparkSession.builder \
        .appName("iceberg-batch") \
        .config("spark.jars", "/opt/spark-apps/jars/postgresql-42.6.0.jar," +
                "/opt/spark-apps/jars/clickhouse-jdbc-0.4.6.jar," +
                "/opt/spark-apps/jars/iceberg-spark-runtime-3.5_2.12.jar") \
        .config("spark.sql.extensions", "org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions") \
        .config("spark.sql.catalog.spark_catalog", "org.apache.iceberg.spark.SparkCatalog") \
        .config("spark.sql.catalog.spark_catalog.type", "hadoop") \
        .config("spark.sql.catalog.spark_catalog.warehouse", f"s3a://{bucket_name}/warehouse") \
        .config("spark.hadoop.fs.s3a.endpoint", minio_endpoint) \
        .config("spark.hadoop.fs.s3a.access.key", minio_user) \
        .config("spark.hadoop.fs.s3a.secret.key", minio_password) \
        .config("spark.hadoop.fs.s3a.path.style.access", "true") \
        .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem") \
        .config("spark.hadoop.fs.s3a.connection.ssl.enabled", "false") \
        .getOrCreate()
    logging.info("SparkSession создан.")
    return spark

def get_latest_batch_time(spark, clickhouse_url, clickhouse_user, clickhouse_password):
    logging.info("Получаем последний batch_time из ClickHouse...")
    query = "(SELECT max(batch_time) AS max_batch_time FROM products) AS t"
    df = spark.read.format("jdbc") \
        .option("url", clickhouse_url) \
        .option("dbtable", query) \
        .option("user", clickhouse_user) \
        .option("password", clickhouse_password) \
        .option("driver", "com.clickhouse.jdbc.ClickHouseDriver") \
        .load()
    row = df.collect()[0]
    max_batch_time = row["max_batch_time"]
    if max_batch_time is None:
        max_batch_time = datetime.datetime(1970, 1, 1)
        logging.info("batch_time в ClickHouse не найден, установлено значение по умолчанию 1970-01-01.")
    else:
        logging.info(f"Последний batch_time в ClickHouse: {max_batch_time}")
    return max_batch_time

def read_new_records(spark, max_batch_time):
    logging.info(f"Читаем данные из Iceberg с created_at > {max_batch_time}...")
    query = f"""
        SELECT
            product_id,
            product_name,
            product_description,
            category,
            price,
            seller_id,
            created_at,
            updated_at
        FROM spark_catalog.db.products
        WHERE created_at > TIMESTAMP('{max_batch_time.strftime('%Y-%m-%d %H:%M:%S')}')
    """
    df = spark.sql(query)
    count = df.count()
    logging.info(f"Найдено новых записей: {count}")
    return df

def write_to_clickhouse(df, clickhouse_url, clickhouse_user, clickhouse_password, batch_time):
    logging.info(f"Добавляем batch_time = {batch_time} к данным...")
    df_with_batch = df.withColumn("batch_time", lit(batch_time))
    logging.info(f"Записываем данные в ClickHouse...")
    df_with_batch.write.format("jdbc") \
        .option("url", clickhouse_url) \
        .option("dbtable", "products") \
        .option("user", clickhouse_user) \
        .option("password", clickhouse_password) \
        .option("driver", "ru.yandex.clickhouse.ClickHouseDriver") \
        .mode("append") \
        .save()
    logging.info(f"Записано {df_with_batch.count()} строк в ClickHouse.")

def main():
    bucket_name = os.getenv("MINIO_BUCKET_NAME")
    minio_user = os.getenv("MINIO_ROOT_USER")
    minio_password = os.getenv("MINIO_ROOT_PASSWORD")
    minio_endpoint = os.getenv("MINIO_ENDPOINT", "http://minio:9000")
    clickhouse_url = os.getenv("CLICKHOUSE_URL", "jdbc:clickhouse://clickhouse:8123/default")
    clickhouse_user = os.getenv("CLICKHOUSE_USER")
    clickhouse_password = os.getenv("CLICKHOUSE_PASSWORD")

    spark = create_spark_session(bucket_name, minio_endpoint, minio_user, minio_password)

    try:
        max_batch_time = get_latest_batch_time(spark, clickhouse_url, clickhouse_user, clickhouse_password)
        df_new = read_new_records(spark, max_batch_time)
        batch_start_time = datetime.datetime.now()
        if df_new.count() > 0:
            write_to_clickhouse(df_new, clickhouse_url, clickhouse_user, clickhouse_password, batch_start_time)
        else:
            logging.info("Нет новых данных для загрузки.")
    finally:
        spark.stop()
        logging.info("SparkSession остановлен.")

if __name__ == "__main__":
    main()
