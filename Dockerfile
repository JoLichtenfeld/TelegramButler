# Minimal production image for the TelegramButler bot
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY requirements.txt ./
RUN apt-get update \
    && apt-get install -y --no-install-recommends tzdata \
    && pip install -r requirements.txt \
    && rm -rf /var/lib/apt/lists/*

# Copy source code; configuration and data files are mounted at runtime
COPY bot.py utils.py camera.py /app/
COPY example_config.yaml /app/

# The bot expects config.yaml, watchlist.yaml, and waste_calendar.ics to exist in /app
# Provide them via a bind mount or Docker secrets.

ENTRYPOINT ["python", "bot.py"]
