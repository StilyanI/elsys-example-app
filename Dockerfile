FROM python:3.11-slim

# Задаване на работна директория
WORKDIR /app

# Копиране на requirements файла
COPY requirements.txt .

# Инсталиране на зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копиране на приложението
COPY main.py .

# Създаване на storage директория
RUN mkdir -p storage

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD python -c "import requests; requests.get('http://localhost:8000/health')" || exit 1

# Стартиране на приложението
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]