FROM ubuntu:18.04
RUN apt-get update && apt-get install -y python3 \
    python3-pip \
    redis-server

ADD . /opt/mqtt
WORKDIR /opt/mqtt
RUN pip3 install -r requirements.txt

CMD ["python3", "-u", "/opt/mqtt/mqtt-ws.py"]