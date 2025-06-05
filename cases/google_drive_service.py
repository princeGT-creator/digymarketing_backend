import os.path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError
import os

# Scopes for Google Drive API (upload + folder create permission)
SCOPES = ["https://www.googleapis.com/auth/drive.file"]


def get_google_drive_service():
    creds = None
    token_path = "token.json"
    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)

    if not creds or not creds.valid:
        try:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                raise Exception("Require manual auth")
        except Exception as e:
            # Token is invalid or revoked, delete and re-auth
            if os.path.exists(token_path):
                os.remove(token_path)
            flow = InstalledAppFlow.from_client_secrets_file(
                "client_secret_963292558056-lk9kmqt60c3o85er2o9c2hmggftm4j9j.apps.googleusercontent.com.json",
                SCOPES,
            )
            creds = flow.run_local_server(port=8001)

        with open(token_path, "w") as token:
            token.write(creds.to_json())

    return build("drive", "v3", credentials=creds)


def create_drive_folder(folder_name, parent_id=None):
    """Create a folder in Google Drive and return its ID"""
    service = get_google_drive_service()

    folder_metadata = {
        'name': folder_name,
        'mimeType': 'application/vnd.google-apps.folder',
    }

    if parent_id:
        folder_metadata['parents'] = [parent_id]

    try:
        folder = service.files().create(
            body=folder_metadata, fields="id"
        ).execute()
        return folder.get("id")
    except HttpError as error:
        print(f"An error occurred while creating folder: {error}")
        return None


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
    print('file_metadata: ', file_metadata)

    try:
        # Upload the file
        file = service.files().create(body=file_metadata, media_body=media, fields="id, webViewLink").execute()
        print('file: ', file)

        # Return the file ID and link
        return file['id'], file['webViewLink']

    except HttpError as error:
        print(f"An error occurred: {error}")
        return None, None

def ensure_case_drive_folder(case):
    if not case.drive_folder_id:
        folder_id = create_drive_folder(case.name)
        if folder_id:
            case.drive_folder_id = folder_id
            case.save()
    return case.drive_folder_id

def upload_appellant_file_to_case_drive(case, file_path, file_name):
    folder_id = ensure_case_drive_folder(case)
    file_id, view_link = upload_to_drive(folder_id, file_path, file_name)
    return file_id, view_link

def upload_existing_appellant_files_to_case(appellant):
    from cases.models import AppellantFile  # <== move import here

    case = appellant.case
    if not case:
        return

    folder_id = ensure_case_drive_folder(case)
    files = AppellantFile.objects.filter(appellant=appellant)

    for file_obj in files:
        if not file_obj.file:
            continue

        file_path = file_obj.file.path
        # file_name = file_obj.file.name.split("/")[-1]
        file_name = os.path.basename(file_obj.file.name)

        file_id, web_view_link = upload_to_drive(folder_id, file_path, file_name)

        if file_id:
            file_obj.drive_file_id = file_id
            file_obj.drive_file_link = web_view_link
            file_obj.save()


def copy_file_to_folder(file_id, destination_folder_id):
    """Copy a file using service account credentials to a destination folder."""
    service = get_google_drive_service()
    try:
        copied_file = service.files().copy(
            fileId=file_id,
            body={'parents': [destination_folder_id]}
        ).execute()
        copied_file_id = copied_file['id']
        if copied_file and copied_file_id:
            # 3. Delete the original file
            service.files().delete(fileId=file_id).execute()
        copied_file_link = f"https://drive.google.com/file/d/{copied_file_id}/view"
        return copied_file_id, copied_file_link
    except HttpError as error:
        print(f"An error occurred while copying file: {error}")
        return None, None