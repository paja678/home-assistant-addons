FROM python:3.11-slim

RUN mkdir /data

WORKDIR /app

COPY tcp_server.py run.sh ./

RUN chmod +x run.sh

CMD ["./run.sh"]
