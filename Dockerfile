FROM openjdk:11-jre-slim

# Install python3, pip, spark dependencies etc.
RUN apt-get update && apt-get install -y python3 python3-pip && \
    pip3 install pyspark

WORKDIR /app

COPY shuffle_2.py .

#COPY generated_votes.txt .  # als je een input sample mee wil geven

CMD ["python3", "shuffle_2.py"]
