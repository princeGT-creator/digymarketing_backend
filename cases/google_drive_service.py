import os
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

CREDENTIALS_FILE = os.path.join(os.path.dirname(__file__), 'credentials.json')

def get_drive_service():
    creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=['https://www.googleapis.com/auth/drive'])
    return build('drive', 'v3', credentials=creds)

def create_drive_folder(folder_name):
    service = get_drive_service()
    file_metadata = {
        'name': folder_name,
        'mimeType': 'application/vnd.google-apps.folder'
    }
    folder = service.files().create(body=file_metadata, fields='id').execute()
    return folder.get("id")

def upload_to_drive(file_path, file_name, folder_id):
    service = get_drive_service()
    
    file_metadata = {
        'name': file_name,
        'parents': [folder_id]  # Dynamic folder ID
    }
    
    media = MediaFileUpload(file_path, mimetype='application/octet-stream')
    uploaded_file = service.files().create(body=file_metadata, media_body=media, fields='id,webViewLink').execute()

    return uploaded_file.get("id"), uploaded_file.get("webViewLink")
