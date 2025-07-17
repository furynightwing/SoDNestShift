from flask import Flask, request, render_template, send_file
import requests
import json
import os
import zipfile
import gnupg
import tempfile

app = Flask(__name__)

# Configuration
API_URL = "https://api.ridersguild.org/ProfileWebService.asmx/Export"
GPG_PASSPHRASE = os.getenv("GPG_PASSPHRASE")
PRIVATE_GPG_KEY_PATH = "/app/private-key.asc"   # Mounted inside container

# Initialize GPG and import private key once at startup
gpg = gnupg.GPG()

with open(PRIVATE_GPG_KEY_PATH, "r") as keyfile:
    key_data = keyfile.read()

import_result = gpg.import_keys(key_data)
if not import_result.count:
    raise RuntimeError("Failed to import GPG private key")

for fingerprint in import_result.fingerprints:
    gpg.trust_keys(fingerprint, 'TRUST_ULTIMATE')


def remove_sensitive_keys(obj, keys_to_remove):
    if isinstance(obj, dict):
        return {
            k: remove_sensitive_keys(v, keys_to_remove)
            for k, v in obj.items()
            if k not in keys_to_remove
        }
    elif isinstance(obj, list):
        return [remove_sensitive_keys(item, keys_to_remove) for item in obj]
    else:
        return obj


@app.route("/", methods=["GET", "POST"])
def export_form():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        try:
            response = requests.post(API_URL, data={"username": username, "password": password})
            if response.status_code != 200:
                error_messages = {
                    401: "Unauthorized: Invalid username or password.",
                    500: "Server Error: Something went wrong on the server."
                }
                error_message = error_messages.get(response.status_code, f"API Error: Received status code {response.status_code}")
                return render_template("index.html", error=error_message), response.status_code

            data = response.json()

            # Remove sensitive keys recursively
            keys_to_remove = ["Password", "Sessions", "MMORoles"]
            data = remove_sensitive_keys(data, keys_to_remove)

            with tempfile.TemporaryDirectory() as temp_dir:
                json_file = os.path.join(temp_dir, f"{username}_export.json")
                sig_file = os.path.join(temp_dir, f"{username}_export.json.asc")
                zip_file = os.path.join(temp_dir, f"{username}_export.zip")

                with open(json_file, "w") as f:
                    json.dump(data, f, indent=2)

                with open(json_file, "rb") as f:
                    signed_data = gpg.sign_file(
                        f,
                        keyid=None,
                        passphrase=GPG_PASSPHRASE,
                        detach=True,
                        output=sig_file,
                    )

                if not signed_data:
                    return render_template("index.html", error="Failed to sign the export file."), 500

                with zipfile.ZipFile(zip_file, "w", zipfile.ZIP_DEFLATED) as zipf:
                    zipf.write(json_file, os.path.basename(json_file))
                    zipf.write(sig_file, os.path.basename(sig_file))

                return send_file(
                    zip_file,
                    as_attachment=True,
                    download_name=f"{username}_export.zip",
                    mimetype="application/zip",
                )

        except Exception as e:
            return render_template("index.html", error=f"Error: {str(e)}"), 500

    return render_template("index.html", error=None)


@app.route("/publickey")
def public_key():
    # Serve the public key so clients can verify signatures easily
    return send_file("/app/ridersguild.asc", mimetype="text/plain")


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=21121)
