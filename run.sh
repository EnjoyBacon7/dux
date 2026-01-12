#!/bin/bash

export UPLOAD_DIR="${UPLOAD_DIR:-./uploads}"
export HOST="${HOST:-0.0.0.0}"
export PORT="${PORT:-8000}"
export DATABASE_URL="${DATABASE_URL:-postgresql://dux_user:dux_password@localhost:5432/dux}"

# Check if PostgreSQL is installed
if ! command -v psql &> /dev/null; then
    echo "PostgreSQL is not installed. Installing via Homebrew..."
    if ! command -v brew &> /dev/null; then
        echo "Error: Homebrew is not installed. Please install Homebrew first:"
        echo "Visit https://brew.sh"
        exit 1
    fi
    brew install postgresql
    
    # Add PostgreSQL to PATH for this session
    export PATH="/opt/homebrew/opt/postgresql/bin:$PATH"
fi

# Ensure PostgreSQL is in PATH
if [ -d "/opt/homebrew/opt/postgresql/bin" ]; then
    export PATH="/opt/homebrew/opt/postgresql/bin:$PATH"
elif [ -d "/usr/local/opt/postgresql/bin" ]; then
    export PATH="/usr/local/opt/postgresql/bin:$PATH"
fi

# Check if PostgreSQL service is running
if ! pg_isready -h localhost -p 5432 &> /dev/null; then
    echo "Starting PostgreSQL service..."
    brew services start postgresql
    
    # Wait for PostgreSQL to be ready
    echo "Waiting for PostgreSQL to start..."
    for i in {1..30}; do
        if pg_isready -h localhost -p 5432 &> /dev/null; then
            echo "PostgreSQL is ready!"
            break
        fi
        sleep 1
    done
    
    if ! pg_isready -h localhost -p 5432 &> /dev/null; then
        echo "Warning: PostgreSQL failed to start. Database operations may fail."
    fi
fi

# Create database and user if they don't exist
if command -v psql &> /dev/null; then
    echo "Setting up database..."
    psql postgres -tc "SELECT 1 FROM pg_user WHERE usename = 'dux_user'" 2>/dev/null | grep -q 1 || \
        psql postgres -c "CREATE USER dux_user WITH PASSWORD 'dux_password';" 2>/dev/null
    
    psql postgres -tc "SELECT 1 FROM pg_database WHERE datname = 'dux'" 2>/dev/null | grep -q 1 || \
        psql postgres -c "CREATE DATABASE dux OWNER dux_user;" 2>/dev/null
    
    echo "Database setup complete!"
else
    echo "Warning: psql command not found. Skipping database setup."
    echo "PostgreSQL may not be installed correctly."
fi



# Build the frontend and copy to static
echo "Building frontend..."
cd dux-front
npm install
npm run build
cd ..
mkdir -p static
rm -rf static/*
cp -r dux-front/dist/* static/

uv run uvicorn server.app:app --reload --host "$HOST" --port "$PORT"
