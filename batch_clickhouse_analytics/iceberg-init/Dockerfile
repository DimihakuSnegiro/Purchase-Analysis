FROM bitnami/spark:latest

USER root

RUN install_packages curl python3-pip
RUN pip3 install clickhouse-driver boto3

RUN mkdir -p /opt/bitnami/spark/jars

RUN curl -L -o /opt/bitnami/spark/jars/iceberg-spark-runtime-3.5_2.12.jar \
    https://repo1.maven.org/maven2/org/apache/iceberg/iceberg-spark-runtime-3.5_2.12/1.4.2/iceberg-spark-runtime-3.5_2.12-1.4.2.jar

COPY iceberg_init.py /opt/bitnami/spark/iceberg_init.py

RUN chmod +x /opt/bitnami/spark/iceberg_init.py

USER 1001

CMD ["spark-submit", \
    "--jars", "/opt/bitnami/spark/jars/iceberg-spark-runtime-3.5_2.12.jar", \
    "/opt/bitnami/spark/iceberg_init.py"]