def download_and_hash(drive_service, file_id, mime_type):
    import os
    from googleapiclient.http import MediaIoBaseDownload
    from features.core.utils import sha256

    temp_path = "temp_download"

    # HANDLE GOOGLE DOCS
    if mime_type.startswith("application/vnd.google-apps"):
        print("⚠ Skipping Google Docs file")
        return None

    request = drive_service.files().get_media(fileId=file_id)

    with open(temp_path, "wb") as f:
        downloader = MediaIoBaseDownload(f, request)
        done = False
        while not done:
            status, done = downloader.next_chunk()

    file_hash = sha256(temp_path)
    os.remove(temp_path)

    return file_hash