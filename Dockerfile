FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application
COPY . .

# Create non-root user
RUN useradd --create-home --shell /bin/bash bot
RUN chown -R bot:bot /app
USER bot

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD python -c "import asyncio; import aiohttp; asyncio.run(aiohttp.ClientSession().get('http://localhost:8080/health').close())" || exit 1

# Run the bot
CMD ["python", "main.py"]
