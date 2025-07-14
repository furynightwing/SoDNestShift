FROM python:3.11-slim

WORKDIR /app

# Install dependencies
RUN apt-get update && apt-get install -y gcc libpq-dev postgresql-client gnupg && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Create www-data user and set up GPG home directory
RUN mkdir -p /home/www-data/.gnupg && \
    chown -R www-data:www-data /home/www-data && \
    chmod 700 /home/www-data/.gnupg && \
    echo "Created /home/www-data/.gnupg with correct permissions"

# Copy application files
COPY requirements.txt ./
COPY .env ./
COPY app.py ./
COPY templates ./templates
COPY rg-exporter-key.asc ./

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Import GPG key as www-data and set trust
USER www-data
RUN gpg --homedir /home/www-data/.gnupg --import /app/rg-exporter-key.asc && \
    echo "7259399C6E32A514CD841DF75CFA1A902836CCDB:6:" | gpg --homedir /home/www-data/.gnupg --import-ownertrust && \
    gpg --homedir /home/www-data/.gnupg --list-secret-keys && \
    echo "GPG key imported successfully for www-data"

# Switch back to root for cleanup
USER root
RUN rm /app/rg-exporter-key.asc

# Run as www-data
USER www-data
CMD ["python", "app.py"]