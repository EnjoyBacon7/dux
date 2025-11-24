# Use Python 3.12 slim image
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies
RUN uv sync --frozen --no-dev

# Copy application code
COPY server ./server
COPY static ./static

# Create uploads directory
RUN mkdir -p /app/uploads

# Run the application
CMD ["sh", "-c", "uv run uvicorn server.app:app --host 0.0.0.0 --port 8080"]
