FROM python:3.11-slim

WORKDIR /app

# Install dependencies first for layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# Run as non-root user
RUN useradd -m botuser
USER botuser

CMD ["python", "bot.py"]
