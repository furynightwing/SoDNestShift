# 🪶 NestShift: Riders Guild/SoDOff Export Tool

NestShift is a secure and user-friendly tool designed for Riders Guild users to export their profile data as a **signed ZIP archive**, verifiable with GPG. Built with Flask and packaged with a seamless Docker setup, it ensures simplicity, security, and authenticity for data exports.

## ✨ Features

- 🔐 **Secure Data Export**: Authenticate with Riders Guild credentials to download your profile data.
- 🧹 **Data Privacy**: Excludes sensitive fields like `Password`, `Sessions`, and `MMORoles`.
- 🔏 **Tamper-Proof**: Exports are signed with a GPG key for authenticity.
- 🔓 **Public Key Access**: Retrieve the public key via `/publickey` for verification.
- 🖥️ **Clean UI**: Google-inspired, intuitive web interface.
- 🐳 **Dockerized**: Easy setup with Docker Compose.


## Api Endpoint

To use this project, you will need SoDOff-master installed and running. 
You will need to place **ExportController.cs** in the `Controllers` directory and configure the server to run.
Then start SoDOff.

## 🚀 Flask Server Quick Start (with Docker Compose)

### 1. Clone the Repository

```bash
git clone https://github.com/furynightwing/SoDNestShift.git
cd nestshift
```

### 2. Add Your GPG Private Key

Place your GPG private & public key in the project root as `private-key.asc, yourname.asc`.

> **⚠️ Important**: Keep your private key secure and never share it.

### 3. Configure the GPG Passphrase

Create a `.env` file in the project root:

```
GPG_PASSPHRASE=your-secret-passphrase
```

### 4. Run the Application

```bash
docker-compose up --build
```

Visit `http://localhost:21121` in your browser to access the app.

## 🧪 Verifying a ZIP Export

Use the provided `verify.py` script in NestShift-tools to verify the authenticity of your exported ZIP archive.

### 1. Install Dependencies

```bash
pip install requests python-gnupg
```

### 2. Update the Script

Edit `verify.py` to set the path to your downloaded ZIP file:

```python
ZIP_FILE_PATH = "path/to/your/export.zip"
```

> **Note**: On Windows, use double backslashes (`C:\\path\\to\\your\\export.zip`).

### 3. Run the Verification

```bash
python verify.py
```

Expected output:

```
✅ Signature verification succeeded!
```

## 🔧 File Structure

```
nestshift/
├── app.py                  # Core Flask application
├── private-key.asc         # GPG private key (not committed)
├── .env                    # GPG passphrase (not committed)
├── Dockerfile              # Docker configuration
├── docker-compose.yml      # Docker Compose setup
├── templates/
│   └── index.html          # Web UI template
└── README.md               # This file
```

## 🔐 Security

- ✅ **Public Key**: Safe to share, accessible at `/publickey`.
- ❌ **Private Key**: Used server-side only for signing; never expose it.
- 🛡️ **Signed Exports**: Cryptographically signed to ensure data integrity and authenticity.

## 🧰 Running Locally (Without Docker)

1. Install dependencies:

   ```bash
   pip install flask python-gnupg requests
   ```
2. Ensure `private-key.asc` is in the project root and `gnupg` is installed.
3. Set the passphrase:

   ```bash
   export GPG_PASSPHRASE=your-secret-passphrase
   ```
4. Run the app:

   ```bash
   python app.py
   ```

Visit `http://localhost:21121`.

## 🪪 License

NestShift is licensed under the MIT License.

## 🛠 Built With

- Flask - Web framework
- GnuPG - Cryptographic signing
- Docker & Docker Compose - Containerization
- Python 3.10+

## 🙌 Credits

Built with ❤️ by furynightwing with contributions from RPaciorek