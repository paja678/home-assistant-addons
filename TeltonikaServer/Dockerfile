FROM ghcr.io/home-assistant/base-python:3.11

RUN mkdir -p /data

WORKDIR /app

COPY main.py tcp_server.py web_server.py run.sh ./

RUN chmod +x run.sh

CMD ["./run.sh"]
