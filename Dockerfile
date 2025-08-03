# Use official Python base image (Linux avoids Windows async issues)
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /app

# Install required system packages for Playwright
RUN apt-get update && apt-get install -y \
    wget \
    curl \
    gnupg \
    ca-certificates \
    fonts-liberation \
    libnss3 \
    libatk-bridge2.0-0 \
    libx11-xcb1 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    libgbm1 \
    libgtk-3-0 \
    libasound2 \
    libxss1 \
    libxtst6 \
    libcurl4 \
    libdrm2 \
    libpci3 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy all project files into container
COPY . .

# Install Python dependencies
RUN pip install --upgrade pip \
    && pip install -r requirements.txt \
    && playwright install chromium

# Expose FastAPI port
EXPOSE 8000

# Default command (adjust if needed)
CMD ["uvicorn", "app.api.app:app", "--host", "0.0.0.0", "--port", "8000"]
