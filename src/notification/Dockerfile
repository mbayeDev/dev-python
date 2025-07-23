# Stage 1: Builder
FROM python:3.13-slim-bookworm AS builder

# Install system dependencies (like for mysqlclient if needed)
RUN apt-get update && \
    apt-get install -y --no-install-recommends --no-install-suggests \
    python3-dev \
    build-essential ffmpeg \
    pkg-config && \
    rm -rf /var/lib/apt/lists/*

# Set working directory for the application
WORKDIR /app

# Set environment variables for uv and the virtual environment
ENV VIRTUAL_ENV=/app/.venv
ENV PATH="/app/.venv/bin:$PATH"

# Create the virtual environment using the system Python
RUN python3 -m venv "$VIRTUAL_ENV"

# Install uv into the virtual environment
RUN "$VIRTUAL_ENV/bin/pip" install --no-cache-dir uv

# Copy pyproject.toml and uv.lock first to leverage Docker cache
COPY pyproject.toml uv.lock ./

# Install dependencies using uv sync into the virtual environment
RUN "$VIRTUAL_ENV/bin/uv" sync --locked --no-dev --no-install-project

# Copy the rest of your application code
# THIS IS WHERE server.py IS COPIED
COPY . .

# Install your project in editable mode (or regular install if not editable)
RUN "$VIRTUAL_ENV/bin/uv" sync --locked --no-dev


# Stage 2: Final (Runtime) Image
FROM python:3.13-slim-bookworm

# Create a non-root user for security best practices
RUN adduser --system --group --no-create-home appuser
USER appuser

# Set working directory
WORKDIR /app

# Copy the virtual environment and application code from the builder stage
COPY --from=builder --chown=appuser:appuser /app /app

# Set the PATH to include the virtual environment's bin directory
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1

#CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8080"]
CMD ["python3", "consumer.py"]