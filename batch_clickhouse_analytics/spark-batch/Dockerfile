FROM bitnami/spark:latest
USER root
RUN install_packages curl python3-pip

RUN mkdir -p /opt/spark-apps/jars

COPY postgres_batch.py /opt/spark-apps/postgres_batch.py
COPY iceberg_batch.py  /opt/spark-apps/iceberg_batch.py

RUN pip3 install --no-cache-dir clickhouse-driver boto3 psycopg2-binary

RUN curl -L -o /opt/spark-apps/jars/iceberg-spark-runtime-3.5_2.12.jar \
    https://repo1.maven.org/maven2/org/apache/iceberg/iceberg-spark-runtime-3.5_2.12/1.4.2/iceberg-spark-runtime-3.5_2.12-1.4.2.jar && \
    curl -L -o /opt/spark-apps/jars/postgresql-42.6.0.jar \
    https://repo1.maven.org/maven2/org/postgresql/postgresql/42.6.0/postgresql-42.6.0.jar && \
    curl -L -o /opt/spark-apps/jars/clickhouse-jdbc-0.4.6.jar \
    https://repo1.maven.org/maven2/com/clickhouse/clickhouse-jdbc/0.4.6/clickhouse-jdbc-0.4.6-all.jar && \
    chown 1001:1001 /opt/spark-apps/jars/*.jar


RUN mkdir -p /tmp/.ivy2/local && chmod -R 777 /tmp/.ivy2
WORKDIR /opt/spark-apps