# Dockerfile for SrBoy Delivery API - Google Cloud Platform
# Multi-stage build for production optimization

# ============================================
# BACKEND BUILD STAGE
# ============================================
FROM python:3.11-slim as backend-build

# Set working directory
WORKDIR /app/backend

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    libffi-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# ============================================
# FRONTEND BUILD STAGE
# ============================================
FROM node:18-alpine as frontend-build

# Set working directory
WORKDIR /app/frontend

# Copy package files
COPY frontend/package.json frontend/yarn.lock ./

# Install dependencies
RUN yarn install --frozen-lockfile

# Copy source code
COPY frontend/ .

# Build frontend for production
RUN yarn build

# ============================================
# PRODUCTION STAGE
# ============================================
FROM python:3.11-slim as production

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app/backend
ENV PORT=8080

# Install system dependencies for production
RUN apt-get update && apt-get install -y \
    libpq5 \
    nginx \
    supervisor \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create app user
RUN useradd --create-home --shell /bin/bash app

# Set working directory
WORKDIR /app

# Copy Python dependencies from build stage
COPY --from=backend-build /root/.local /home/app/.local

# Copy backend source code
COPY backend/ ./backend/

# Copy built frontend
COPY --from=frontend-build /app/frontend/build ./frontend/build

# Copy configuration files
COPY docker-config/ ./config/

# Create necessary directories
RUN mkdir -p /tmp/srboy_uploads \
    && mkdir -p /app/credentials \
    && mkdir -p /var/log/supervisor \
    && mkdir -p /var/log/nginx

# Set permissions
RUN chown -R app:app /app \
    && chown -R app:app /tmp/srboy_uploads \
    && chown -R app:app /var/log/supervisor

# Configure Nginx
COPY docker-config/nginx.conf /etc/nginx/sites-available/default

# Configure Supervisor
COPY docker-config/supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Switch to app user
USER app

# Add local bin to PATH
ENV PATH=/home/app/.local/bin:$PATH

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8080/api/health || exit 1

# Expose port
EXPOSE 8080

# Start supervisor
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]