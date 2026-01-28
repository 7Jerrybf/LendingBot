
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY zenith_engine ./zenith_engine

# Set Python path
ENV PYTHONPATH=/app

# Run the engine
CMD ["python", "-m", "zenith_engine.main"]
