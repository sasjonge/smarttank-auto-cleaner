FROM python:3.12-slim

# cron  +  envsubst (gettext-base)
RUN apt-get update && apt-get install -y --no-install-recommends \
        cron gettext-base tzdata \
    && rm -rf /var/lib/apt/lists/*

# set default zone in the image (can be overridden by env)
ENV TZ=Europe/Berlin
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone
    
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY smarttankclean.py entrypoint.sh ./
RUN chmod +x entrypoint.sh

ENTRYPOINT ["./entrypoint.sh"]
