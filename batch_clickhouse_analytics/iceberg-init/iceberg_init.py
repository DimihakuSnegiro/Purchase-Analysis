from pyspark.sql import SparkSession
import os
import boto3
from botocore.exceptions import ClientError
import time
from datetime import datetime

bucket_name = os.getenv("MINIO_BUCKET_NAME")
minio_user = os.getenv("MINIO_ROOT_USER")
minio_password = os.getenv("MINIO_ROOT_PASSWORD")
minio_endpoint = os.getenv("MINIO_ENDPOINT", "http://minio:9000")

def wait_for_bucket(bucket_name, endpoint_url, access_key, secret_key):
    s3 = boto3.client(
        's3',
        endpoint_url=endpoint_url,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
    )
    while True:
        try:
            s3.head_bucket(Bucket=bucket_name)
            print(f"Бакет '{bucket_name}' найден в MinIO.")
            return True
        except ClientError as e:
            print(f"Ожидание бакета '{bucket_name}'... ({e.response['Error']['Message']})")
            time.sleep(3)

wait_for_bucket(bucket_name, minio_endpoint, minio_user, minio_password)

spark = SparkSession.builder \
    .appName("IcebergInit") \
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

try:
    spark.sql("CREATE NAMESPACE IF NOT EXISTS spark_catalog.db")

    spark.sql("""
        CREATE TABLE IF NOT EXISTS spark_catalog.db.products (
            product_id BIGINT,
            product_name STRING,
            product_description STRING,
            category STRING,
            price DOUBLE,
            seller_id INT,
            created_at TIMESTAMP,
            updated_at TIMESTAMP
        )
        USING iceberg
        PARTITIONED BY (category)
    """)
    print("Таблица 'products' успешно создана в каталоге Iceberg!")
finally:
    spark.stop()
