FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000 \
    DB_PATH=/app/data/restock.sqlite3
WORKDIR /app
COPY app.py ui.py ./
COPY static/ ./static/
RUN mkdir -p /app/data && useradd --create-home --shell /usr/sbin/nologin restock && chown -R restock:restock /app
USER restock
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:' + __import__('os').environ.get('PORT','8000') + '/healthz',timeout=2)" || exit 1
CMD ["python", "-u", "app.py"]
