"""
features/core/models.py
Pure data models — no Qt dependency.
"""

from dataclasses import dataclass, field


@dataclass
class FileEntry:
    """Represents a single file found during a scan."""
    path:       str
    size:       int
    name:       str
    extension:  str
    hash_sha256: str  = ""
    group_id:   int  = -1
    protected:  bool = False
    source:     str = "local"
    cloud_id:   str = ""
    hash_md5:   str | None = None
    confidence: str = "LOW"


@dataclass
class DuplicateGroup:
    """A collection of files that are considered duplicates of each other."""
    group_id:   int
    files:      list = field(default_factory=list)
    match_type: str  = "hash"   # "hash" | "name" | "both"
