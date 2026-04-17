# syntax=docker/dockerfile:1
FROM python:3.12-slim

# Install Node.js (required by the MCP servers launched via npx)
RUN apt-get update && apt-get install -y --no-install-recommends \
        curl \
        ca-certificates \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY pyproject.toml .
RUN pip install -e .

# Copy source code
COPY src/ ./src/

CMD ["python", "-m", "src.main"]
