FROM python:3.12-slim
WORKDIR /app

RUN adduser --disabled-password --gecos '' appuser

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN chown -R appuser:appuser /app

USER appuser

EXPOSE 5002
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5002/api/accounts', timeout=5)" 2>/dev/null || exit 1
CMD ["gunicorn", "-b", "0.0.0.0:5002", "-w", "2", "--timeout", "60", "app:app"]
