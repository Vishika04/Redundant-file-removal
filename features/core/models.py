"""
features/core/models.py
Pure data models — no Qt dependency.
"""

from dataclasses import dataclass, field


@dataclass
class FileEntry:
    """Represents a single file found during a scan."""
    path:             str
    size:             int
    name:             str
    extension:        str
    hash_sha256:      str   = ""
    media_kind:       str   = ""
    fingerprint:      str   = ""
    similarity_score: float = 0.0
    group_id:         int   = -1
    protected:        bool  = False
    source:           str   = "local"   # "local" or "cloud"
    file_id:          str   = None      # Google Drive file ID
    modified_time:    str   = None
    mime_type:        str   = ""


@dataclass
class DuplicateGroup:
    """A collection of files that are considered duplicates of each other."""
    group_id:         int
    files:            list  = field(default_factory=list)
    match_type:       str   = "hash"    # "hash" | "name" | "both"
    algorithm:        str   = ""
    similarity_score: float = 100.0
