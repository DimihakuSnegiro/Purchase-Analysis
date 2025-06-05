set -e

spark-submit \
  --jars /opt/spark-apps/jars/postgresql-42.6.0.jar,/opt/spark-apps/jars/clickhouse-jdbc-0.4.6.jar \
  /opt/spark-apps/postgres_batch.py
