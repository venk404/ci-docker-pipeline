FROM python:3.13-alpine AS builder

WORKDIR /app

# Install build dependencies
RUN apk add --no-cache \
    gcc=14.2.0-r6 \
    musl-dev=1.2.5-r10 \
    postgresql17-dev=17.6-r0
# Create a virtual environment
RUN python -m venv /app/venv
ENV PATH="/app/venv/bin:$PATH"

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# SIMPLE CLEANUP - Remove Python cache files
RUN find /app/venv -name "*.pyc" -delete && \
    find /app/venv -type d -name "__pycache__" -exec rm -rf {} +

# Final stage
FROM python:3.13-alpine

WORKDIR /app

# Copy only the necessary files from the builder stage
COPY --from=builder /app/venv /app/venv

COPY ./code/ /app/code/
COPY ./DB/Schemas/migrations /app/migrations/

# Set environment variables
ENV PATH="/app/venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1

# Install runtime dependencies
RUN apk add --no-cache libpq=17.6-r0 curl
    
# Expose port 8000
EXPOSE 8000

# Use exec form for CMD
CMD ["python", "code/Main.py"]