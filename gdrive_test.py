from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/drive.metadata.readonly']

flow = InstalledAppFlow.from_client_secrets_file(
    'credentials.json', SCOPES
)

creds = flow.run_local_server(port=0)

service = build('drive', 'v3', credentials=creds)

results = service.files().list(
    pageSize=10,
    fields="files(id, name, size, md5Checksum)"
).execute()

files = results.get('files', [])

for f in files:
    print(f["name"], f.get("size"), f.get("md5Checksum"))