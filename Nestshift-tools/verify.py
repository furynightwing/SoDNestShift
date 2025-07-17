import requests
import gnupg
import zipfile
import tempfile
import os

# URL to fetch the public key
PUBLIC_KEY_URL = "http://export.ridersguild.org/publickey"  # change to your real URL

# Path to your ZIP file to verify
ZIP_FILE_PATH = r"C:\Users\Jo\Downloads\RGNightWing_export-2.zip"  # change to your local file path

def download_public_key(url):
    resp = requests.get(url)
    resp.raise_for_status()
    return resp.text

def verify_zip_signature(public_key, zip_path):
    gpg = gnupg.GPG()
    import_result = gpg.import_keys(public_key)
    if import_result.count == 0:
        print("Failed to import public key")
        return False

    with tempfile.TemporaryDirectory() as tmpdir:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(tmpdir)

        json_file = None
        asc_file = None
        for fname in os.listdir(tmpdir):
            if fname.endswith(".json"):
                json_file = os.path.join(tmpdir, fname)
            elif fname.endswith(".asc"):
                asc_file = os.path.join(tmpdir, fname)

        if not json_file or not asc_file:
            print("ZIP missing required .json or .asc signature file")
            return False

        with open(asc_file, 'rb') as f_sig:
            verify = gpg.verify_file(f_sig, json_file)

        return verify.valid

if __name__ == "__main__":
    print("Downloading public key...")
    pubkey = download_public_key(PUBLIC_KEY_URL)

    print(f"Verifying signature of {ZIP_FILE_PATH}...")
    is_valid = verify_zip_signature(pubkey, ZIP_FILE_PATH)

    if is_valid:
        print("Signature verification succeeded! ✅")
    else:
        print("Signature verification failed! ❌")
