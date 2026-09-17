FROM apache/airflow:2.9.3-python3.11

USER airflow

RUN pip install --no-cache-dir \
    requests beautifulsoup4 pandas lxml \
    psycopg2-binary python-dotenv playwright

USER root
RUN apt-get update && apt-get install -y --no-install-recommends \
    libglib2.0-0 \
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libpango-1.0-0 \
    libcairo2 \
    libasound2 \
    libxshmfence1 \
    libx11-xcb1 \
    && rm -rf /var/lib/apt/lists/*

USER airflow
RUN playwright install chromium
