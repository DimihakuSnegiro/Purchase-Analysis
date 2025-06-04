FROM bitnami/spark:latest

USER root

RUN install_packages curl python3-pip
RUN pip3 install clickhouse-driver boto3

RUN mkdir -p /opt/spark-apps/jars

RUN curl -L -o /opt/spark-apps/jars/iceberg-spark-runtime-3.5_2.12.jar \
    https://repo1.maven.org/maven2/org/apache/iceberg/iceberg-spark-runtime-3.5_2.12/1.4.2/iceberg-spark-runtime-3.5_2.12-1.4.2.jar && \
    curl -L -o /opt/spark-apps/jars/postgresql-42.6.0.jar \
    https://repo1.maven.org/maven2/org/postgresql/postgresql/42.6.0/postgresql-42.6.0.jar && \
    curl -L -o /opt/spark-apps/jars/clickhouse-jdbc-0.4.6.jar \
    https://repo1.maven.org/maven2/com/clickhouse/clickhouse-jdbc/0.4.6/clickhouse-jdbc-0.4.6-all.jar

COPY postgres_batch.py iceberg_batch.py start_spark.sh /opt/spark-apps/

RUN chmod +x /opt/spark-apps/*.py /opt/spark-apps/start_spark.sh

USER 1001

CMD ["/opt/spark-apps/start_spark.sh"]
