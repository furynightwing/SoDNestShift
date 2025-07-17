FROM python:3.11-slim

# Install gnupg for signing
RUN apt-get update && apt-get install -y gnupg && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy entire application including keys and templates
COPY . .


# Environment variable (loaded from .env)
ENV GPG_PASSPHRASE=changeme

EXPOSE 21121

CMD ["python", "app.py"]
