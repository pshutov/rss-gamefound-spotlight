FROM python:3.12-slim

RUN apt-get update -y && apt-get install -y --no-install-recommends \
    git ca-certificates tzdata && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Uncomment if you have dependencies
# COPY requirements.txt .
# RUN pip install --no-cache-dir -r requirements.txt

COPY fetch_to_rss.py ./fetch_to_rss.py
COPY run_cron.sh ./run_cron.sh

RUN chmod +x /app/run_cron.sh

CMD ["/app/run_cron.sh"]
