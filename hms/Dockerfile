FROM apache/hive:4.0.0

USER root

RUN apt-get update && \
    apt-get install -y curl && \
    rm -rf /var/lib/apt/lists/*

# PostgreSQL JDBC driver
RUN curl -fsSL https://jdbc.postgresql.org/download/postgresql-42.7.3.jar \
         -o /opt/hive/lib/postgresql-42.7.3.jar

# hadoop-aws + AWS SDK bundle for S3A → MinIO (Hadoop 3.3.6)
RUN curl -fsSL \
      https://repo1.maven.org/maven2/org/apache/hadoop/hadoop-aws/3.3.6/hadoop-aws-3.3.6.jar \
      -o /opt/hive/lib/hadoop-aws-3.3.6.jar && \
    curl -fsSL \
      https://repo1.maven.org/maven2/com/amazonaws/aws-java-sdk-bundle/1.12.367/aws-java-sdk-bundle-1.12.367.jar \
      -o /opt/hive/lib/aws-java-sdk-bundle-1.12.367.jar

COPY hive-site.xml /opt/hive/conf/hive-site.xml

USER hive
