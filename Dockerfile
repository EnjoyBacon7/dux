
# Build frontend
FROM node:20 AS frontend-build
WORKDIR /frontend
COPY dux-front/package.json dux-front/package-lock.json ./
RUN npm ci
COPY dux-front .
RUN npm run build

# Backend and final image
FROM python:3.12-slim
WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    UPLOAD_DIR=/app/uploads

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies
RUN uv sync --frozen --no-dev

# Copy backend code
COPY server ./server

# Copy frontend build to static
COPY --from=frontend-build /frontend/dist ./static

# Create uploads directory
RUN mkdir -p /app/uploads

# Run the application
CMD ["uv", "run", "uvicorn", "server.app:app", "--host", "0.0.0.0", "--port", "8080"]
