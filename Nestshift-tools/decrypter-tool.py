# Decrypter Tool for GPG-Encrypted SQL Dumps
#
# This script decrypts and verifies a GPG-encrypted SQL dump contained in a ZIP file.
# The ZIP file (e.g., [USER]_account_export.zip) contains two files:
#   - [USER]_account_export.sql.gpg: The encrypted SQL dump.
#   - [USER]_account_export.sql.asc: The detached GPG signature for verification.
#
# Prerequisites:
#   1. Install Python 3.6+ (https://www.python.org/downloads/).
#   2. Install the python-gnupg package:
#      ```
#      pip install python-gnupg
#      ```
#   3. Install GPG:
#      - Windows: Install Gpg4win (https://www.gpg4win.org/, version 2.4.0 or later recommended).
#      - Linux/Mac: Install GnuPG (e.g., `sudo apt install gnupg` on Ubuntu or `brew install gnupg` on macOS).
#   4. Obtain the private key from the exporter machine:
#      - The exporter machine (running the server) uses a GPG key pair to sign and encrypt the SQL dump.
#      - You need the private key (e.g., rg-exporter-private-key.asc) used by the server for encryption.
#      - Contact the server administrator to securely obtain this key file.
#   5. Import the private key into your local GPG keyring:
#      ```
#      gpg --import path/to/rg-exporter-private-key.asc
#      ```
#      - If the key is passphrase-protected, you’ll need the passphrase.
#      - Verify the key import:
#        ```
#        gpg --list-keys
#        ```
#        Look for the key ID (e.g., 7259399C6E32A514CD841DF75CFA1A902836CCDB) and its email (e.g., simplexprogramming101@gmail.com).
#   6. (Optional) Set the key’s trust level to avoid verification warnings:
#      - Use Kleopatra (included with Gpg4win) to set the trust to "Ultimate":
#        - Open Kleopatra, find the key, right-click > Change Owner Trust > Ultimate > OK.
#      - Or use the command line (Windows Command Prompt, not PowerShell):
#        ```
#        echo 7259399C6E32A514CD841DF75CFA1A902836CCDB:6: > trust.txt
#        gpg --import-ownertrust trust.txt
#        del trust.txt
#        ```
#
# Usage:
#   Run the script with the path to the ZIP file:
#   ```
#   python decrypter.py [USER]_account_export.zip
#   ```
#   If the private key requires a passphrase, provide it:
#   ```
#   python decrypter.py [USER]_account_export.zip --passphrase "your_passphrase"
#   ```
#
# Output:
#   - The decrypted SQL file (e.g., [USER]_account_export.sql) is saved in the current directory.
#   - The signature file ([USER]_account_export.sql.asc) is saved for inspection.
#   - Logs show the decryption status, first 5 lines of the decrypted file, and signature verification results.
#
# Security Notes:
#   - Keep the private key (e.g., rg-exporter-private-key.asc) secure and delete it after importing.
#   - The decrypted SQL file may contain sensitive data (e.g., password hashes). Handle it carefully.
#   - If the private key is not passphrase-protected, consider adding a passphrase for security.

import os
import zipfile
import tempfile
import gnupg
import subprocess
import argparse
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def normalize_line_endings(file_path):
    """Normalize line endings to LF (\n) in the given file."""
    with open(file_path, 'r', newline='') as f:
        content = f.read()
    with open(file_path, 'w', newline='\n') as f:
        f.write(content.replace('\r\n', '\n'))

def decrypt_and_verify(zip_path, passphrase=None):
    """
    Decrypt the .gpg file and verify the .asc signature from the ZIP archive.
    
    Args:
        zip_path (str): Path to the ZIP file containing .gpg and .asc files.
        passphrase (str): Passphrase for the private key (optional).
    """
    try:
        # Initialize GPG (using default keyring)
        gpg = gnupg.GPG()
        logging.info("GPG initialized successfully")
    except Exception as e:
        logging.error(f"Failed to initialize GPG: {str(e)}")
        return

    # Create a temporary directory for extracted files
    with tempfile.TemporaryDirectory() as temp_dir:
        # Extract the ZIP file
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_file:
                extracted_files = zip_file.namelist()
                logging.info(f"Extracted files from ZIP: {extracted_files}")
                zip_file.extractall(temp_dir)
        except Exception as e:
            logging.error(f"Failed to extract ZIP file: {str(e)}")
            return
        
        # Find .gpg and .asc files
        gpg_file = None
        asc_file = None
        for file in extracted_files:
            if file.endswith('.sql.gpg'):
                gpg_file = os.path.join(temp_dir, file)
            elif file.endswith('.sql.asc'):
                asc_file = os.path.join(temp_dir, file)
        
        if not gpg_file or not asc_file:
            logging.error(f"ZIP file missing required files. Found .gpg: {gpg_file}, .asc: {asc_file}")
            return

        # Save .asc file for manual inspection
        saved_asc = os.path.join(os.getcwd(), os.path.basename(asc_file))
        with open(asc_file, 'r') as src, open(saved_asc, 'w') as dst:
            dst.write(src.read())
        logging.info(f"Saved .asc file for inspection: {saved_asc}")

        # Check .asc file contents
        try:
            with open(asc_file, 'r') as sig_file:
                sig_content = sig_file.read()
                logging.info(f"Signature file contents:\n{sig_content}")
        except Exception as e:
            logging.error(f"Failed to read .asc file: {str(e)}")
            return

        # Decrypt the .gpg file
        output_sql = os.path.splitext(os.path.basename(gpg_file))[0]  # e.g., <username>_account_export.sql
        try:
            with open(gpg_file, 'rb') as f:
                decrypt_result = gpg.decrypt_file(f, passphrase=passphrase, output=output_sql)
            logging.info(f"Decryption status: {decrypt_result.status}")
            if decrypt_result.ok:
                logging.info(f"Decryption successful. Decrypted file saved as: {output_sql}")
                # Normalize line endings in the decrypted file
                normalize_line_endings(output_sql)
                logging.info(f"Normalized line endings in {output_sql}")
                # Log the first few lines of the decrypted file
                with open(output_sql, 'r') as sql_file:
                    sql_content = sql_file.readlines()[:5]  # Log first 5 lines
                    logging.info(f"Decrypted file contents (first 5 lines):\n{''.join(sql_content)}")
            else:
                logging.error(f"Decryption failed: {decrypt_result.status}")
                return
        except Exception as e:
            logging.error(f"Decryption failed: {str(e)}")
            return

        # Verify the signature using subprocess
        try:
            result = subprocess.run(
                ['gpg', '--verify', asc_file, output_sql],
                capture_output=True,
                text=True,
                check=True
            )
            logging.info(f"Verification successful. GPG output:\n{result.stdout}\nGPG stderr:\n{result.stderr}")
        except subprocess.CalledProcessError as e:
            logging.error(f"Signature verification failed: {e.stderr}")
            return

def main():
    parser = argparse.ArgumentParser(description="Decrypt and verify a GPG-encrypted SQL dump from a ZIP file.")
    parser.add_argument("zip_file", help="Path to the ZIP file containing .gpg and .asc files")
    parser.add_argument("--passphrase", help="Passphrase for the private key (optional)", default=None)
    args = parser.parse_args()

    decrypt_and_verify(args.zip_file, args.passphrase)

if __name__ == "__main__":
    main()