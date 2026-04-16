from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from features.core.models import FileEntry
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
import os


SCOPES = ['https://www.googleapis.com/auth/drive.metadata.readonly']

def get_drive_service():
    creds = None

    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())   # 🔥 auto refresh
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES
            )
            creds = flow.run_local_server(port=0)

        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    return build('drive', 'v3', credentials=creds)


def fetch_drive_files():
    service = get_drive_service()

    files_data = []
    page_token = None

    while True:
        results = service.files().list(
            pageSize=100,
            pageToken=page_token,
            fields="nextPageToken, files(id, name, size, md5Checksum, mimeType)"
        ).execute()

        for f in results.get('files', []):
            if not f.get("size") or f.get("mimeType") == "application/vnd.google-apps.folder":
                continue

            files_data.append({
                "name": f["name"],
                "size": int(f["size"]),
                "hash": f.get("md5Checksum"),
                "source": "gdrive",
                "id": f["id"]
            })

        page_token = results.get("nextPageToken")
        if not page_token:
            break

    return files_data

def get_cloud_entries():
    raw_files = fetch_drive_files()  # your API function

    entries = []

    for f in raw_files:
        entry = FileEntry(
            path=f["id"],
            size=f["size"],
            name=f["name"],
            extension="",
            protected=False,
            source="cloud",
            cloud_id=f["id"]
        )

        # 🔥 ADD THIS
        entry.hash_md5 = f.get("hash")

        entries.append(entry)

    return entries