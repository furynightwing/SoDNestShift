# Account Export Server for GPG-Encrypted SQL Dumps
#
# This Flask application exports user data from a PostgreSQL database, encrypts it with GPG,
# signs it with a detached signature, and packages it into a ZIP file for secure download.
# The output ZIP file (e.g., [USER]_account_export.zip) contains:
#   - [USER]_account_export.sql.gpg: The GPG-encrypted SQL dump.
#   - [USER]_account_export.sql.asc: The detached GPG signature for verification.
# The client-side `decrypter.py` script decrypts and verifies the ZIP file's contents.
#
# Prerequisites:
#   1. Install Python 3.6+ (https://www.python.org/downloads/).
#   2. Install required Python packages:
#      ```
#      pip install psycopg2 flask python-dotenv
#      ```
#      Note: On Ubuntu, install `libpq-dev` for `psycopg2`:
#      ```
#      sudo apt update && sudo apt install libpq-dev python3-dev
#      ```
#   3. Install GPG on the server:
#      - Ubuntu: `sudo apt install gnupg`
#      - Other platforms: Install GnuPG (e.g., `brew install gnupg` on macOS).
#   4. Set up the GPG key pair:
#      - Obtain the private key (e.g., `NestShift-private-key.asc`) for signing and encryption.
#      - Import the private key into the server's GPG keyring (e.g., /home/www-data/.gnupg):
#        ```
#        gpg --homedir /home/www-data/.gnupg --import /path/to/NestShiftr-private-key.asc
#        ```
#        - If the key is passphrase-protected, ensure the passphrase is available or remove it for automation:
#          ```
#          gpg --homedir /home/www-data/.gnupg --edit-key 7259399C6E32A514CD841DF75CFA1A902836CCDB
#          passwd
#          ```
#        - Verify the key import:
#          ```
#          gpg --homedir /home/www-data/.gnupg --list-keys
#          ```
#          Look for the key ID (e.g., 3314832A514CD871DF75CF9828436CCDB) and email (e.g., example@example.com).
#      - Ensure the GPG home directory (/home/www-data/.gnupg) has correct permissions:
#        ```
#        chown www-data:www-data /home/www-data/.gnupg
#        chmod 700 /home/www-data/.gnupg
#        ```
#   5. Create a `.env` file in the project root with the following variables:
#      ```
#      DATABASE_URL=postgresql://user:password@localhost:5432/dbname
#      SECRET_KEY=your_secure_random_key
#      GPG_USER=example@example.com
#      GPG_KEY_ID=(YOUR KEY))
#      ```
#      - Replace `DATABASE_URL` with your PostgreSQL connection string.
#      - Generate a secure `SECRET_KEY` (e.g., using `os.urandom(24).hex()`).
#      - Ensure `GPG_USER` and `GPG_KEY_ID` match the imported key.
#
# Usage:
#   1. Ensure the PostgreSQL database is accessible and the tables (e.g., Users, Vikings) exist.
#   2. Run the Flask application:
#      ```
#      python app.py
#      ```
#      Or, if in a Docker container:
#      ```
#      docker run -p 21121:21121 -v /path/to/.env:/app/.env -v /home/www-data/.gnupg:/home/www-data/.gnupg <image_name>
#      ```
#   3. Access the web interface at http://localhost:21121.
#   4. Submit a username and email to export the user’s data.
#   5. Download the resulting `[USER]_account_export.zip` file.
#
# Output:
#   - A ZIP file containing the encrypted SQL dump (`.gpg`) and signature (`.asc`).
#   - Logs show the export process, including any errors or skipped tables.
#
# Security Notes:
#   - Keep the private key (e.g., `NestShift-private-key.asc`) secure and delete after importing.
#   - The SQL dump includes sensitive data (e.g., password hashes). Consider excluding the `Password` column:
#     Modify `get_user_data` to select only needed columns:
#     ```python
#     cursor.execute('SELECT "Id", "Username", "Email" FROM "Users" WHERE "Username" = %s AND "Email" = %s', (username, email))
#     ```
#   - If automating, ensure the private key is not passphrase-protected or use a GPG agent.
#   - Secure the `.env` file (e.g., `chmod 600 .env`).
#
# Notes:
#   - The client must have the corresponding private key to decrypt the `.gpg` file (see `decrypter-tool.py` in NestShift-tools).
#   - Tables without `VikingId` or `UserId` columns are skipped. Modify `get_user_data` to include them if needed.
#   - Ensure the server has write access to the GPG home directory and temporary file locations.

import os
import psycopg2
import hmac
import logging
import subprocess
import zipfile
from flask import Flask, render_template, request, send_file
from dotenv import load_dotenv
from io import BytesIO
from datetime import datetime
import tempfile

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Initialize Flask app
app = Flask(__name__)
app.config['DATABASE_URL'] = os.getenv("DATABASE_URL")
app.config['SECRET_KEY'] = os.getenv("SECRET_KEY")

# GPG User
GPG_USER = os.getenv("GPG_USER", "simplexprogramming101@gmail.com")
GPG_KEY_ID = os.getenv("GPG_KEY_ID", "7259399C6E32A514CD841DF75CFA1A902836CCDB")

# Database connection function
def get_db_connection():
    return psycopg2.connect(app.config['DATABASE_URL'])

# Generate HMAC signature for data verification
def generate_signature(data, secret_key):
    return hmac.new(secret_key.encode(), data.encode(), digestmod='sha256').hexdigest()

# Fetch user data from the database
def get_user_data(username, email):
    conn = get_db_connection()
    cursor = conn.cursor()

    logging.debug(f"Account export requested for {username} ({email})")

    # Validate user based on username and email
    cursor.execute('SELECT "Id", "Username", "Email", "Password" FROM "Users" WHERE "Username" = %s AND "Email" = %s', (username, email))
    user = cursor.fetchone()

    if not user:
        logging.warning(f"No user found with username: {username} and email: {email}")
        return None

    user_id, user_email, user_password = user

    # Get the Viking associated with the user
    cursor.execute('SELECT "Id" FROM "Vikings" WHERE "UserId" = %s', (user_id,))
    viking = cursor.fetchone()
    if not viking:
        logging.warning(f"No Viking found for user {username}")
        return None

    viking_id = viking[0]
    logging.debug(f"UserId = {user_id}, VikingId = {viking_id}")

    # Tables to be exported
    tables = [
        'AchievementPoints', 'AchievementTaskState', 'Dragons', 'GameData', 'GameDataPairs', 'GroupViking',
        'Groups', 'Images', 'InventoryItems', 'MMORoles', 'MissionStates', 'Neighborhoods', 'PairData', 'Pairs',
        'Parties', 'ProfileAnswers', 'RatingRanks', 'Ratings', 'RoomItems', 'Rooms', 'SavedData', 'SceneData',
        'Sessions', 'TaskStatuses', 'UserBadgesCompleted', 'UserMissionData', 'Users', 'Vikings'
    ]

    sql_dump = []
    # Adding user and Viking insert statements
    sql_dump.append(f"INSERT INTO \"Users\" (\"Id\", \"Username\", \"Email\", \"Password\") VALUES ('{user_id}', '{username}', '{user_email}', '{user_password}');")
    sql_dump.append(f"INSERT INTO \"Vikings\" (\"Id\", \"UserId\", \"Uid\") VALUES ('{viking_id}', '{user_id}', '{username}');")

    for table in tables:
        try:
            cursor.execute(f'SELECT * FROM "{table}" LIMIT 1')
            columns = [desc[0] for desc in cursor.description]

            if "VikingId" in columns:
                cursor.execute(f'SELECT * FROM "{table}" WHERE "VikingId" = %s', (viking_id,))
            elif "UserId" in columns:
                cursor.execute(f'SELECT * FROM "{table}" WHERE "UserId" = %s', (user_id,))
            else:
                logging.warning(f"No VikingId or UserId in table {table}, skipping...")
                continue

            rows = cursor.fetchall()

            for row in rows:
                values = ["'{0}'".format(str(value).replace("'", "''")) if value is not None else 'NULL' for value in row]
                sql_dump.append(f"INSERT INTO \"{table}\" ({', '.join(columns)}) VALUES ({', '.join(values)});")

        except Exception as e:
            logging.exception(f"Failed to export from {table}")
            sql_dump.append(f"-- Error exporting from {table}: {str(e)}")
            conn.rollback()  # Reset the transaction so the next table can be queried

    cursor.close()
    conn.close()

    return sql_dump

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/export', methods=['POST'])
def export():
    username = request.form['username']
    email = request.form['email']

    user_data = get_user_data(username, email)

    if not user_data:
        return "Invalid username or email", 400

    sql_dump = '\n'.join(user_data)

    # Create a temporary file to hold the SQL dump
    with tempfile.NamedTemporaryFile(delete=False, mode='w+', suffix='.sql') as temp_sql_file:
        temp_sql_file.write(sql_dump)
        temp_sql_file.flush()

        # Sign the file with GPG
        sig_path = temp_sql_file.name + '.asc'
        enc_path = temp_sql_file.name + '.gpg'
        try:
            # Create detached signature
            subprocess.run([
                'gpg', '--homedir', '/home/www-data/.gnupg', '--armor', '--output', sig_path,
                '--local-user', GPG_KEY_ID, '--detach-sign', temp_sql_file.name
            ], check=True)

            # Encrypt the SQL file
            subprocess.run([
                'gpg', '--homedir', '/home/www-data/.gnupg', '--armor', '--output', enc_path,
                '--encrypt', '--recipient', GPG_KEY_ID, '--batch', '--yes', temp_sql_file.name
            ], check=True)

            # Create a ZIP file containing the encrypted SQL file and its signature
            zip_buffer = BytesIO()
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                # Add the encrypted file
                with open(enc_path, 'r') as enc_file:
                    zip_file.writestr(f'{username}_account_export.sql.gpg', enc_file.read())
                # Add the signature file
                with open(sig_path, 'r') as sig_file:
                    zip_file.writestr(f'{username}_account_export.sql.asc', sig_file.read())

            # Reset buffer position to the beginning
            zip_buffer.seek(0)

            # Clean up temporary files
            os.unlink(temp_sql_file.name)
            os.unlink(sig_path)
            os.unlink(enc_path)

            return send_file(
                zip_buffer,
                as_attachment=True,
                download_name=f'{username}_account_export.zip',
                mimetype='application/zip'
            )

        except subprocess.CalledProcessError as e:
            logging.error("GPG processing failed", exc_info=True)
            os.unlink(temp_sql_file.name)  # Clean up SQL file
            if os.path.exists(sig_path):
                os.unlink(sig_path)  # Clean up signature if created
            if os.path.exists(enc_path):
                os.unlink(enc_path)  # Clean up encrypted file if created
            return "Export succeeded, but GPG processing failed", 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=21121)