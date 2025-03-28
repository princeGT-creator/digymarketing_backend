import os.path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError

# Scopes for Google Drive API (including upload permissions)
SCOPES = ["https://www.googleapis.com/auth/drive.file"]

def get_google_drive_service():
    """Authenticate and return the Google Drive API service"""
    creds = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "client_secret_290053304181-fd48j6ollj2s8eae2ckmsp1j3bn96s7e.apps.googleusercontent.com.json", SCOPES)
            creds = flow.run_local_server(port=8001)
        
        with open("token.json", "w") as token:
            token.write(creds.to_json())

    service = build("drive", "v3", credentials=creds)
    return service

def upload_to_drive(folder_id, file_path, file_name):
    """Upload a file to Google Drive"""
    service = get_google_drive_service()

    # Create a media file upload object
    media = MediaFileUpload(file_path, resumable=True)

    # Create the file metadata
    file_metadata = {
        'name': file_name,
        'parents': [folder_id],  # Place the file inside the specified folder
    }

    try:
        # Upload the file
        file = service.files().create(body=file_metadata, media_body=media, fields="id, webViewLink").execute()

        # Return the file ID and link
        return file['id'], file['webViewLink']

    except HttpError as error:
        print(f"An error occurred: {error}")
        return None, None