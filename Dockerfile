FROM kasramp/calibre-docker:3.13.7-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY kindler ./kindler
COPY scripts/gutindex_aus_clean.csv ./scripts/

EXPOSE 8181

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:8181", "kindler.wsgi:app"]
