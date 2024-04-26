from pyspark.sql import SparkSession

from config.config import settings

host = getattr(settings, "kafka.host", None)
port = getattr(settings, "kafka.port", None)

kafka_server = f"{host}:{port}"

topic = getattr(settings, "kafka.spark.topic", None)
print(kafka_server)
print(topic)

spark = (
    SparkSession.builder
    .appName("TestKafka")
    .config('spark.jars.packages', 'org.apache.spark:spark-sql-kafka-0-10_2.13:3.5.0')
    .getOrCreate()
)

lines = spark \
    .readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", kafka_server) \
    .option("subscribe", topic) \
    .option("startingOffsets", "earliest") \
    .load()
