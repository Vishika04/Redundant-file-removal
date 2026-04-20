from PyQt6.QtCore import QObject, pyqtSignal
from features.core.models import FileEntry

class GoogleDriveWorker(QObject):
    finished = pyqtSignal(list)
    error = pyqtSignal(str)
    progress = pyqtSignal(int)

    def __init__(self, drive_service):
        super().__init__()
        self.drive_service = drive_service

    def run(self):
        try:
            files = self._fetch_files()
            self.finished.emit(files)
        except Exception as e:
            self.error.emit(str(e))
            
    def _fetch_files(self):
        results = []
        page_token = None
        
        count = 0
        total_est = 1

        while True:
            response = self.drive_service.files().list(
                pageSize=100,
                fields="nextPageToken, files(id, name, size, modifiedTime, mimeType)",
                pageToken=page_token
            ).execute()

            files = response.get("files", [])


            for f in files:

                # skip folders
                if "size" not in f:
                    continue

                count += 1

                progress = min(50, int(count ** 0.7))
                self.progress.emit(progress)   # adjust speed here
                

                name = f["name"]

                entry = FileEntry(
                    path=f"gdrive://{f['id']}",
                    size=int(f.get("size", 0)),
                    name=name,
                    extension=name.split('.')[-1] if '.' in name else "",

                    source="cloud",
                    file_id=f["id"],
                    modified_time=f.get("modifiedTime", ""),
                    mime_type=f.get("mimeType", "")
                )

                results.append(entry)

            page_token = response.get("nextPageToken")
            if not page_token:
                break


        return results