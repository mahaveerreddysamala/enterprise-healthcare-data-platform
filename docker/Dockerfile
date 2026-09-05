FROM python:3.11-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY src ./src
COPY sql ./sql
COPY pipelines ./pipelines
RUN useradd --create-home appuser
USER appuser
CMD ["python", "-m", "src.models.train_readmission", "--help"]
