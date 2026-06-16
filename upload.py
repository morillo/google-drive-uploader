#!/usr/bin/env python3
import os
import sys
import argparse
import mimetypes
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
import google.auth
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload

# We request 'https://www.googleapis.com/auth/drive.file' scope,
# which allows creating new files and modifying files created by this app.
SCOPES = ["https://www.googleapis.com/auth/drive.file"]

# Common mapping for Google Workspace conversions
GOOGLE_MIME_TYPES = {
    "text/csv": "application/vnd.google-apps.spreadsheet",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": "application/vnd.google-apps.spreadsheet",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "application/vnd.google-apps.document",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation": "application/vnd.google-apps.presentation",
    "text/plain": "application/vnd.google-apps.document",
}

def authenticate(credentials_path="credentials.json", token_path="token.json"):
    """
    Authenticate with Google Drive API.
    Attempts Desktop OAuth flow if credentials_path exists.
    Otherwise, falls back to Google Application Default Credentials (ADC).
    """
    creds = None
    
    # 1. Try Desktop OAuth flow using local token/credentials
    if os.path.exists(credentials_path) or os.path.exists(token_path):
        print("Attempting authentication via OAuth 2.0 flow...")
        if os.path.exists(token_path):
            try:
                creds = Credentials.from_authorized_user_file(token_path, SCOPES)
            except Exception as e:
                print(f"Warning: Could not load token from {token_path}: {e}")
        
        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    print("Refreshing expired access token...")
                    creds.refresh(Request())
                except Exception as e:
                    print(f"Warning: Token refresh failed: {e}")
                    creds = None
            
            if not creds:
                if not os.path.exists(credentials_path):
                    print(f"Error: {credentials_path} not found. Please download OAuth client credentials from Google Cloud Console.")
                    sys.exit(1)
                print(f"Starting authentication flow using {credentials_path}...")
                flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
                creds = flow.run_local_server(port=0)
                
            # Save the credentials for the next run
            with open(token_path, "w") as token:
                token.write(creds.to_json())
                print(f"Saved token to {token_path}")
                
        return creds

    # 2. Fall back to Application Default Credentials
    print("No OAuth credentials found. Falling back to Application Default Credentials...")
    try:
        creds, project = google.auth.default(scopes=SCOPES)
        print("Authenticated successfully using Default Credentials.")
        return creds
    except google.auth.exceptions.DefaultCredentialsError:
        print("\nError: Authentication failed.")
        print("Please provide OAuth client secrets as 'credentials.json' or set up Google Application Default Credentials (e.g. export GOOGLE_APPLICATION_CREDENTIALS=...).")
        print("See the README.md for detailed setup instructions.")
        sys.exit(1)

def get_mimetype(file_path):
    """Detect MIME type of file, fallback to octet-stream."""
    mime_type, _ = mimetypes.guess_type(file_path)
    if mime_type is None:
        mime_type = "application/octet-stream"
    return mime_type

def upload_file(file_path, folder_id=None, drive_filename=None, convert=False, description=None, credentials_path="credentials.json", token_path="token.json"):
    if not os.path.exists(file_path):
        print(f"Error: Local file '{file_path}' does not exist.")
        return False

    if not drive_filename:
        drive_filename = os.path.basename(file_path)

    creds = authenticate(credentials_path, token_path)
    
    try:
        service = build("drive", "v3", credentials=creds)
        
        # Determine source MIME type
        src_mimetype = get_mimetype(file_path)
        print(f"Detected MIME type: {src_mimetype}")

        # Set up file metadata
        file_metadata = {
            "name": drive_filename,
        }
        
        if description:
            file_metadata["description"] = description

        if folder_id:
            file_metadata["parents"] = [folder_id]

        # Handle file conversion to Google Docs/Sheets/Slides if requested
        dest_mimetype = None
        if convert:
            if src_mimetype in GOOGLE_MIME_TYPES:
                dest_mimetype = GOOGLE_MIME_TYPES[src_mimetype]
                file_metadata["mimeType"] = dest_mimetype
                print(f"Converting file to Google Workspace type: {dest_mimetype}")
            else:
                print(f"Warning: No automatic conversion mapped for MIME type {src_mimetype}. Uploading as standard file.")

        print(f"Preparing upload for '{file_path}' to Google Drive...")
        
        # Create media upload object
        # Using resumable=True to support large files and progress monitoring
        media = MediaFileUpload(file_path, mimetype=src_mimetype, resumable=True)
        
        request = service.files().create(
            body=file_metadata,
            media_body=media,
            fields="id, name, mimeType, webViewLink"
        )
        
        # Execute the upload with progress status
        response = None
        print("Uploading...")
        while response is None:
            status, response = request.next_chunk()
            if status:
                progress = int(status.progress() * 100)
                print(f"\rProgress: {progress}% ({status.resumed_bytes}/{status.total_size} bytes)", end="", flush=True)
        
        print("\nUpload completed successfully!")
        print("-" * 50)
        print(f"File Name:     {response.get('name')}")
        print(f"File ID:       {response.get('id')}")
        print(f"MIME Type:     {response.get('mimeType')}")
        print(f"Web View Link: {response.get('webViewLink')}")
        print("-" * 50)
        return True

    except HttpError as error:
        print(f"\nAPI Error: {error}")
        return False
    except Exception as e:
        print(f"\nUnexpected Error: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Upload files to Google Drive using the Drive API v3.")
    parser.add_argument("file", help="Path to the local file to upload")
    parser.add_argument("-n", "--name", help="Name to give the file in Google Drive (defaults to local filename)")
    parser.add_argument("-f", "--folder-id", help="Google Drive folder ID to upload the file into")
    parser.add_argument("-d", "--description", help="Description for the file in Google Drive")
    parser.add_argument("-c", "--convert", action="store_true", help="Convert document to Google Workspace format (e.g. CSV to Sheets)")
    parser.add_argument("--credentials", default="credentials.json", help="Path to credentials.json file (default: credentials.json)")
    parser.add_argument("--token", default="token.json", help="Path to token.json file (default: token.json)")
    
    args = parser.parse_args()
    
    upload_file(
        file_path=args.file,
        folder_id=args.folder_id,
        drive_filename=args.name,
        convert=args.convert,
        description=args.description,
        credentials_path=args.credentials,
        token_path=args.token
    )

if __name__ == "__main__":
    main()
