def delete_file_from_drive(drive_service, file_id):
    try:
        drive_service.files().delete(fileId=file_id).execute()
        return True
    except Exception as e:
        print("❌ Delete error:", e)
        return False