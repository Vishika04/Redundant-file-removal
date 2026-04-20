import sqlite3

def get_db():
    return sqlite3.connect("file_cache.db")

def init_db():
    conn = get_db()
    conn.execute("""
    CREATE TABLE IF NOT EXISTS file_cache (
        file_path TEXT PRIMARY KEY,
        size INTEGER,
        mtime REAL,
        sha256 TEXT
    )
    """)
    conn.commit()
    conn.close()

def is_modified(file_path, size, mtime):
    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT size, mtime FROM file_cache WHERE file_path=?", (file_path,))
    row = cur.fetchone()

    conn.close()

    if row is None:
        return True

    return not (row[0] == size and row[1] == mtime)


def update_cache(file_path, size, mtime, sha256):
    conn = get_db()
    conn.execute("""
    INSERT INTO file_cache (file_path, size, mtime, sha256)
    VALUES (?, ?, ?, ?)
    ON CONFLICT(file_path) DO UPDATE SET
        size=excluded.size,
        mtime=excluded.mtime,
        sha256=excluded.sha256
    """, (file_path, size, mtime, sha256))

    conn.commit()
    conn.close()