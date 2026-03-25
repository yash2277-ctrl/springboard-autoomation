# ── Stage 1: Python base with Playwright ──────────────────────────────
FROM python:3.11-slim

# Install system deps needed by Playwright/Chromium
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    gnupg \
    ca-certificates \
    fonts-liberation \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libcups2 \
    libdbus-1-3 \
    libdrm2 \
    libgbm1 \
    libgtk-3-0 \
    libnspr4 \
    libnss3 \
    libx11-xcb1 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    xdg-utils \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers
RUN playwright install chromium && playwright install-deps chromium

# Copy the rest of the application
COPY . .

# Render assigns a PORT env var — Flask reads it at startup
ENV PORT=5000
EXPOSE ${PORT}

# Start the Flask web dashboard
CMD ["sh", "-c", "python app.py"]
