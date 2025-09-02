FROM python:3.13.7-slim

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    wget xz-utils fonts-liberation calibre-bin && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY kindler ./kindler

EXPOSE 8181

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:8181", "kindler.wsgi:app"]
