NestShift: Secure Player Data Export for School of Dragons Emulators
Note on Placeholders: This README uses placeholders for sensitive information (e.g., YOUR_GPG_KEY_ID, YOUR_GPG_EMAIL, YOUR_USERNAME, YOUR_USER_ID, YOUR_DATABASE_URL, YOUR_SECRET_KEY). Replace these with your actual values when setting up the project. For example, YOUR_GPG_KEY_ID should be your GPG key ID (e.g., a 40-character hexadecimal string), and YOUR_GPG_EMAIL should be the email associated with your GPG key.
NestShift is a toolset designed to securely export and decrypt player data from School of Dragons emulators such as Riders Guild and SoDOff. It consists of two components:

NestShift: A Flask-based server (in the NestShift folder) that extracts player data from a PostgreSQL database, encrypts it with GPG, signs it for authenticity, and packages it into a ZIP file for secure delivery.
NestShift-tools: A set of scripts to help users understand how to decrypt and verify the signature of the exported files.
decrypt-tool.py: A standalone script that demonstrates how to unzip, decrypt, and verify the GPG-encrypted SQL dump, allowing users to integrate decryption into their own importer or tools.



Developed for the School of Dragons emulator community, NestShift enables secure export of player data, such as user profiles, Viking statistics, and achievement points, from emulators like Riders Guild and SoDOff. This README explains how to set up and use both components to manage player data securely.
How It Works
NestShift uses GPG (GNU Privacy Guard) to ensure player data is both confidential and authentic:

Server (NestShift):
Connects to a PostgreSQL database to retrieve player data (e.g., Users, Vikings, AchievementPoints) based on a username and email.
Generates a SQL dump containing the player’s game progress.
Signs the dump with a private key to verify its source.
Encrypts the dump with the corresponding public key to protect its contents.
Packages the encrypted file (.gpg) and signature (.asc) into a [USER]_account_export.zip file.


Decryption Script (decrypt-tool.py):
Extracts the ZIP file to access the encrypted .gpg file and .asc signature.
Decrypts the .gpg file using the private key (same key used on the server).
Verifies the signature with the public key to confirm the data’s integrity.
Produces a raw SQL file that users can import into another emulator or process with their own tools.



This process ensures that only authorized users with the private key can access the data, and the signature confirms it originates from the emulator server without alteration. The decrypt-tool.py script serves as a reference for users to understand the decryption and verification process, enabling integration into custom importers or workflows.
🛠️ Prerequisites
To use NestShift with Riders Guild or SoDOff, you’ll need to set up the server (NestShift) and the decryption script (decrypt-tool.py). Here’s what you need:
Server (NestShift)

Python 3.6+: Download from python.org.
Python Packages:pip install psycopg2 flask python-dotenv


On Ubuntu, install dependencies for psycopg2:sudo apt update && sudo apt install libpq-dev python3-dev




GPG: Install GnuPG:
Ubuntu: sudo apt install gnupg
macOS: brew install gnupg


GPG Key Pair:
Obtain the private key (e.g., NestShift-private-key.asc) for signing and encryption, typically provided by the Riders Guild or SoDOff server admin.
Import it into the server’s GPG keyring (e.g., /home/www-data/.gnupg):gpg --homedir /home/www-data/.gnupg --import /path/to/NestShift-private-key.asc


Verify the key:gpg --homedir /home/www-data/.gnupg --list-keys

Look for the key ID (e.g., YOUR_GPG_KEY_ID) and email (e.g., YOUR_GPG_EMAIL).
Set permissions:chown www-data:www-data /home/www-data/.gnupg
chmod 700 /home/www-data/.gnupg


If the key is passphrase-protected, remove the passphrase for automation (optional):gpg --homedir /home/www-data/.gnupg --edit-key YOUR_GPG_KEY_ID
passwd




Environment File: Create a .env file in the NestShift folder:DATABASE_URL=YOUR_DATABASE_URL
SECRET_KEY=YOUR_SECRET_KEY
GPG_USER=YOUR_GPG_EMAIL
GPG_KEY_ID=YOUR_GPG_KEY_ID


Replace YOUR_DATABASE_URL with your PostgreSQL connection string (e.g., postgresql://user:password@localhost:5432/dbname).
Generate a secure YOUR_SECRET_KEY (e.g., python -c "import os; print(os.urandom(24).hex())").
Replace YOUR_GPG_USER and YOUR_GPG_KEY_ID with the email and ID of the imported key.


Docker (Optional): To run the server in a Docker container, you’ll need Docker installed. See the Docker Setup section below.

Decryption Script (NestShift-tools/decrypt-tool.py)

Python 3.6+: Download from python.org.
Python Package:pip install python-gnupg


GPG:
Windows: Install Gpg4win (version 2.4.0+ recommended).
Linux/macOS: Install GnuPG (e.g., sudo apt install gnupg or brew install gnupg).


Private Key:
Obtain the same private key used by the server (e.g., NestShift-private-key.asc) from the Riders Guild or SoDOff server admin.
Import it:gpg --import /path/to/NestShift-private-key.asc


Verify:gpg --list-keys

Look for the key ID (e.g., YOUR_GPG_KEY_ID) and email (e.g., YOUR_GPG_EMAIL).
Set the key’s trust level to “Ultimate” to avoid verification warnings:
Use Kleopatra (included with Gpg4win):
Open Kleopatra, find the key, right-click > Change Owner Trust > Ultimate > OK.


Or use the command line (Windows Command Prompt):echo YOUR_GPG_KEY_ID:6: > trust.txt
gpg --import-ownertrust trust.txt
del trust.txt







🚀 Usage
Server (NestShift)

Ensure your PostgreSQL database (used by Riders Guild or SoDOff) is running and contains tables like Users, Vikings, AchievementPoints, etc.
Navigate to the NestShift folder and run the Flask application locally:cd NestShift
python app.py

Or use Docker (see Docker Setup below).
Open your browser and go to http://localhost:21121.
Enter your School of Dragons username and email (e.g., YOUR_USERNAME, YOUR_GPG_EMAIL).
Download the [USER]_account_export.zip file, which contains:
[USER]_account_export.sql.gpg: Encrypted SQL dump of your player data.
[USER]_account_export.sql.asc: Signature to verify authenticity.



Docker Setup
To run the server in a Docker container:

Ensure Docker is installed (Docker Installation Guide).
Create a Dockerfile in the repository root based on the example below:FROM python:3.11-slim

WORKDIR /app

# Install dependencies
RUN apt-get update && apt-get install -y gcc libpq-dev postgresql-client gnupg && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Create www-data user and set up GPG home directory
RUN mkdir -p /home/www-data/.gnupg && \
    chown -R www-data:www-data /home/www-data && \
    chmod 700 /home/www-data/.gnupg

# Copy application files
COPY NestShift/requirements.txt ./
COPY NestShift/.env ./
COPY NestShift/app.py ./
COPY NestShift/templates ./templates

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Run as www-data
USER www-data
CMD ["python", "app.py"]

Security Warning: Do not include the private key (e.g., NestShift-private-key.asc) in the Docker image or repository. Import the key manually inside the container:docker cp /path/to/NestShift-private-key.asc <container_id>:/app/NestShift-private-key.asc
docker exec -u www-data <container_id> gpg --homedir /home/www-data/.gnupg --import /app/NestShift-private-key.asc
docker exec -u www-data <container_id> bash -c "echo YOUR_GPG_KEY_ID:6: | gpg --homedir /home/www-data/.gnupg --import-ownertrust"
docker exec <container_id> rm /app/NestShift-private-key.asc


Build and run the Docker container from the repository root:docker build -t nestshift .
docker run -p 21121:21121 -v $(pwd)/NestShift/.env:/app/.env nestshift



Decryption Script (NestShift-tools/decrypt-tool.py)

Save the downloaded [USER]_account_export.zip file from the emulator server.
Run the decryption script to obtain the raw SQL dump:python NestShift-tools/decrypt-tool.py [USER]_account_export.zip

If the private key requires a passphrase:python NestShift-tools/decrypt-tool.py [USER]_account_export.zip --passphrase "your_passphrase"


Check the output:
Decrypted SQL file: [USER]_account_export.sql (in the current directory), which can be imported into another emulator or processed with custom tools.
Signature file: [USER]_account_export.sql.asc (saved for inspection).
Logs showing decryption status and the first 5 lines of the SQL file.


Use the decrypted SQL file with your own importer or tools, referring to decrypt-tool.py for guidance on GPG decryption and verification.

📊 Outputs

Server:
A ZIP file ([USER]_account_export.zip) with encrypted SQL data and a signature.
Logs detailing the export process, including any skipped tables (e.g., those without VikingId or UserId).


Decryption Script:
A decrypted SQL file (e.g., [USER]_account_export.sql) with data like:INSERT INTO "Users" ("Id", "Username", "Email", "Password") VALUES ('YOUR_USER_ID', 'YOUR_USERNAME', 'YOUR_GPG_EMAIL', '...');
INSERT INTO "Vikings" ("Id", "UserId", "Uid") VALUES ('4349', 'YOUR_USER_ID', 'YOUR_USERNAME');
INSERT INTO "AchievementPoints" (VikingId, Type, Value) VALUES ('4349', '1', '3090');


Logs confirming decryption and signature verification, e.g.:gpg: Good signature from "YOUR_NAME <YOUR_GPG_EMAIL>" [ultimate]





🔒 Security Notes

Private Key: Keep NestShift-private-key.asc secure and delete it after importing:rm /path/to/NestShift-private-key.asc  # Server
del path\to\NestShift-private-key.asc  # Windows

Warning: Do not include the private key in the GitHub repository or Docker image. Share it securely (e.g., via encrypted channels).
SQL Data: The SQL dump includes sensitive data (e.g., password hashes). To exclude the Password column, modify NestShift/app.py:cursor.execute('SELECT "Id", "Username", "Email" FROM "Users" WHERE "Username" = %s AND "Email" = %s', (username, email))


Passphrase: If the private key is passphrase-protected, provide it or use a GPG agent for automation.
Environment File: Secure the .env file in the NestShift folder:chmod 600 NestShift/.env
chown www-data:www-data NestShift/.env



⚠️ Notes

Skipped Tables: Tables without VikingId or UserId columns (e.g., Groups, Pairs) are skipped. To include them, modify get_user_data in NestShift/app.py with custom queries.
Key Distribution: Share the private key securely (e.g., via encrypted channels) between the server and users.
Permissions: Ensure the server has write access to /home/www-data/.gnupg and temporary file locations.
Decryption Script: Use decrypt-tool.py from the NestShift-tools directory as a reference to process the exported ZIP file from Riders Guild or SoDOff, integrating the decryption logic into your own tools as needed.

🛠️ Troubleshooting

GPG Errors: Check the GPG key import and trust settings. Use gpg --list-keys to verify keys.
Database Issues: Ensure the YOUR_DATABASE_URL matches your emulator’s PostgreSQL server.
Missing Tables: If tables like Groups or Pairs are skipped, check their schema:docker exec -it <container_id> psql YOUR_DATABASE_URL -c "\d Groups"



📜 License
This project is licensed under the MIT License. See the LICENSE file for details.
Thank you for using NestShift to keep your School of Dragons emulator data secure! If you have questions or need help, open an issue on GitHub.