# Google Drive File Uploader (Python)

A Python CLI tool to upload files to Google Drive using the Drive API v3. Features include progress tracking, folder destination selection, and optional conversion to Google Workspace document formats (e.g. CSV to Google Sheets).

## Prerequisites

- Python 3.11 (managed via `pyenv`)
- A Google Cloud Project
- Google Drive API enabled

## Setup Instructions


### 1. Enable Google Drive API & Download Credentials

To interact with Google Drive, you need to configure access in the Google Cloud Console:

1. Go to the [Google Cloud Console](https://console.cloud.google.com/).
2. Create a new project or select an existing one.
3. Enable the **Google Drive API**:
   - Navigate to **APIs & Services** > **Library**.
   - Search for **Google Drive API** and click **Enable**.
4. Configure the **OAuth Consent Screen**:
   - Go to **APIs & Services** > **OAuth consent screen**.
   - Set **User Type** to **External** (or **Internal** if using Google Workspace).
   - Enter your App name, user support email, and developer email, then click **Save and Continue**.
   - (Optional) Under **Scopes**, add `.../auth/drive.file`.
   - Add your Google Account as a **Test User** (required while in testing status).
5. Create **OAuth 2.0 Client ID** credentials:
   - Go to **APIs & Services** > **Credentials**.
   - Click **Create Credentials** > **OAuth client ID**.
   - Choose **Desktop App** as the Application Type, name it (e.g. `Drive Uploader CLI`), and click **Create**.
   - Click the **Download JSON** icon for the created client ID.
   - Save this file as `credentials.json` in the same directory as the script.

### 2. Configure Pyenv & Virtual Environment

Configure your local directory to use Python 3.11, create a virtual environment, and install the required Google client libraries:

```bash
# 1. Set local directory to Python 3.11 using pyenv
pyenv local 3.11.9

# 2. Create the virtual environment
python -m venv .venv

# 3. Activate the virtual environment
source .venv/bin/activate

# 4. Install dependencies
pip install -r requirements.txt
```

---

## Usage

Ensure your virtual environment is active, then run the script by passing the path to the local file you want to upload:

```bash
python upload.py <path-to-local-file>
```


### Options

| Option | Description |
| :--- | :--- |
| `-n`, `--name` | Specify a custom file name in Google Drive (defaults to the local filename). |
| `-f`, `--folder-id` | Upload the file into a specific Google Drive folder (must provide the Folder ID). |
| `-d`, `--description` | Add a description metadata for the file. |
| `-c`, `--convert` | Convert supported document formats (e.g. CSV, XLSX, DOCX) to Google Docs/Sheets formats. |
| `--credentials` | Path to the client secrets JSON file (default: `credentials.json`). |
| `--token` | Path to save the user session token (default: `token.json`). |

### Examples

**Basic Upload:**
```bash
python3 upload.py photo.jpg
```

**Upload to a Specific Folder:**
```bash
python3 upload.py photo.jpg --folder-id "1abc123xyz_folder_id"
```

**Upload and Convert a CSV to Google Sheets:**
```bash
python3 upload.py data.csv --convert
```

**Upload with Custom Name and Description:**
```bash
python3 upload.py doc.docx --name "Q3 Report" --description "Draft Q3 Financial Report"
```

---

## How Authentication Works

1. **OAuth 2.0 Flow**: On the first execution, if `credentials.json` is present, the script will open your web browser to authenticate your Google account and request permission to manage files created by the application (`drive.file` scope).
2. **Token Caching**: Once authorized, access credentials are saved locally to `token.json`. Subsequent runs will use this token automatically without prompting you in the browser.
3. **Application Default Credentials (ADC)**: If no `credentials.json` or `token.json` files are found, the script will fall back to using default credentials (e.g., from service accounts or environment variables).
