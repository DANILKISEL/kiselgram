FROM python:3.12-slim
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libjpeg62-turbo-dev libwebp-dev libz-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
COPY video_server/requirements.txt video_server/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt -r video_server/requirements.txt gunicorn

COPY . .

RUN mkdir -p logs status uploads/images uploads/documents uploads/media instance

EXPOSE 5000 5001
