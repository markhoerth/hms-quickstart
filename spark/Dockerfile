FROM apache/spark:3.5.1-scala2.12-java17-python3-ubuntu

USER root

# apache/spark:3.5.1 bundles Hadoop 3.3.4 internally.
# hadoop-aws and aws-java-sdk-bundle MUST match that version exactly
# or you get NoClassDefFoundError at runtime.
RUN wget -q -P /opt/spark/jars/ \
      "https://repo1.maven.org/maven2/org/apache/iceberg/iceberg-spark-runtime-3.5_2.12/1.6.1/iceberg-spark-runtime-3.5_2.12-1.6.1.jar" && \
    wget -q -P /opt/spark/jars/ \
      "https://repo1.maven.org/maven2/org/apache/hadoop/hadoop-aws/3.3.4/hadoop-aws-3.3.4.jar" && \
    wget -q -P /opt/spark/jars/ \
      "https://repo1.maven.org/maven2/com/amazonaws/aws-java-sdk-bundle/1.12.262/aws-java-sdk-bundle-1.12.262.jar" && \
    ls -lh /opt/spark/jars/iceberg* /opt/spark/jars/hadoop-aws* /opt/spark/jars/aws-java*

COPY query.py /opt/spark/work-dir/query.py

USER spark

CMD ["/opt/spark/bin/spark-submit", \
     "--master", "local[2]", \
     "/opt/spark/work-dir/query.py"]
