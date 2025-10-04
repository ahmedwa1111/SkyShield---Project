FROM python:3.11-slim

# Set workdir
WORKDIR /app

# Install dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy source
COPY ../ .

ENV PYTHONUNBUFFERED=1

EXPOSE 5000

CMD ["uvicorn", "api_server:app", "--host", "0.0.0.0", "--port", "5000", "--workers", "1"]
