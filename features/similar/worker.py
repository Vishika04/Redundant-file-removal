"""
features/similar/worker.py
Perceptual similarity scanning for images and audio files.
"""

from __future__ import annotations

import concurrent.futures
import math
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, cast

from PyQt6.QtCore import QThread, pyqtSignal

from features.core.constants import SKIP_DIR_NAMES
from features.core.models import DuplicateGroup, FileEntry
from features.core.utils import is_protected_path

try:
    import numpy as np
except Exception:  # pragma: no cover - optional dependency fallback
    np = None  # type: ignore[assignment]

try:
    import cv2
except Exception:  # pragma: no cover - optional dependency fallback
    cv2 = None  # type: ignore[assignment]

try:
    import librosa
except Exception:  # pragma: no cover - optional dependency fallback
    librosa = None  # type: ignore[assignment]

try:
    from pydub import AudioSegment
except Exception:  # pragma: no cover - optional dependency fallback
    AudioSegment = None  # type: ignore[assignment]


IMAGE_EXTS = {
    ".jpg", ".jpeg", ".png", ".bmp", ".gif", ".webp", ".tif", ".tiff", ".heic"
}
AUDIO_EXTS = {
    ".mp3", ".wav", ".flac", ".ogg", ".m4a", ".aac", ".opus", ".wma", ".aiff", ".aif"
}


@dataclass(slots=True)
class _Fingerprint:
    entry: FileEntry
    kind: str
    vector: object
    duration: float = 0.0
    algorithm: str = ""


ImageSignature = tuple[int, int, tuple[float, float, float]]


class SimilarityWorker(QThread):
    progress = pyqtSignal(int, str)
    finished = pyqtSignal(list)
    error = pyqtSignal(str)

    def __init__(
        self,
        root: str,
        threshold: int,
        workers: int = 8,
    ) -> None:
        super().__init__()
        self.root = root
        self.threshold = threshold
        self.workers = workers
        self._abort = False

    def abort(self) -> None:
        self._abort = True

    def run(self) -> None:
        try:
            self._do_scan()
        except Exception as exc:  # pragma: no cover - surfaced through UI
            self.error.emit(str(exc))

    def _do_scan(self) -> None:
        self.progress.emit(2, "Collecting media files...")
        media_paths = self._collect_media_paths()
        if not media_paths:
            self.finished.emit([])
            return

        self.progress.emit(8, f"{len(media_paths)} media files found - fingerprinting...")
        fingerprints = self._fingerprint_paths(media_paths)
        if self._abort:
            return

        image_items = [fp for fp in fingerprints if fp.kind == "image" and fp.vector is not None]
        audio_items = [fp for fp in fingerprints if fp.kind == "audio" and fp.vector is not None]

        self.progress.emit(78, "Comparing perceptual signatures...")
        groups: list[DuplicateGroup] = []
        gid = 0

        for kind, items in (("image", image_items), ("audio", audio_items)):
            if self._abort or len(items) < 2:
                continue
            found, gid = self._build_groups(kind, items, gid)
            groups.extend(found)

        self.progress.emit(100, f"Done - {len(groups)} similar group(s)")
        self.finished.emit(groups)

    def _collect_media_paths(self) -> list[Path]:
        media_paths: list[Path] = []
        for dirpath, dirs, filenames in os.walk(self.root):
            if self._abort:
                return []
            dirs[:] = [
                d for d in dirs
                if d.lower() not in SKIP_DIR_NAMES and not d.startswith("$")
            ]
            for filename in filenames:
                if self._abort:
                    return []
                path = Path(dirpath) / filename
                if is_protected_path(str(path)):
                    continue
                if path.suffix.lower() in IMAGE_EXTS | AUDIO_EXTS:
                    media_paths.append(path)
        return media_paths

    def _fingerprint_paths(self, paths: Iterable[Path]) -> list[_Fingerprint]:
        items: list[_Fingerprint] = []
        path_list = list(paths)
        total = len(path_list)
        if total == 0:
            return items

        with concurrent.futures.ThreadPoolExecutor(max_workers=self.workers) as pool:
            future_map = {pool.submit(self._fingerprint_file, path): path for path in path_list}
            done = 0
            for fut in concurrent.futures.as_completed(future_map):
                if self._abort:
                    return []
                done += 1
                pct = 8 + int(done / total * 60)
                path = future_map[fut]
                self.progress.emit(pct, f"Fingerprinting: {path.name}")
                fingerprint = fut.result()
                if fingerprint is not None:
                    items.append(fingerprint)
        return items

    def _fingerprint_file(self, path: Path) -> _Fingerprint | None:
        suffix = path.suffix.lower()
        try:
            entry = FileEntry(
                path=str(path),
                size=path.stat().st_size,
                name=path.name,
                extension=suffix,
                protected=False,
            )
        except (OSError, PermissionError):
            return None

        if suffix in IMAGE_EXTS:
            image_data = self._image_signature(path)
            if image_data is None:
                return None
            phash, dhash, color = image_data
            entry.media_kind = "image"
            entry.fingerprint = (
                f"{phash:016x}:{dhash:016x}:"
                f"{int(round(color[0])):03d}-{int(round(color[1])):03d}-{int(round(color[2])):03d}"
            )
            return _Fingerprint(entry=entry, kind="image", vector=image_data, algorithm="OpenCV pHash + dHash + color")

        if suffix in AUDIO_EXTS:
            audio_data = self._audio_signature(path)
            if audio_data is None:
                return None
            vector, duration, algorithm = audio_data
            entry.media_kind = "audio"
            entry.fingerprint = algorithm
            return _Fingerprint(entry=entry, kind="audio", vector=vector, duration=duration, algorithm=algorithm)

        return None

    def _image_signature(self, path: Path):
        if cv2 is None or np is None:
            return None
        image = cv2.imread(str(path), cv2.IMREAD_UNCHANGED)
        if image is None:
            return None
        image_array = np.asarray(image)

        if image_array.ndim == 2:
            gray = image_array
            color = np.asarray([float(image_array.mean())] * 3, dtype=np.float32)
        else:
            bgr = image_array[:, :, :3]
            if image_array.shape[2] >= 4:
                alpha = image_array[:, :, 3]
                mask = alpha > 0
                if mask.any():
                    visible_pixels = bgr[mask]
                    color = np.asarray(visible_pixels.mean(axis=0), dtype=np.float32)
                else:
                    color = np.asarray(bgr.reshape(-1, 3).mean(axis=0), dtype=np.float32)
                gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
                gray = np.where(mask, gray, 0).astype(np.uint8)
            else:
                color = np.asarray(bgr.reshape(-1, 3).mean(axis=0), dtype=np.float32)
                gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)

        return _image_phash(gray), _image_dhash(gray), tuple(float(value) for value in color)

    def _audio_signature(self, path: Path):
        if np is None:
            return None

        y = None
        sr = None
        algorithm = "librosa fingerprint"
        if librosa is not None:
            try:
                y, sr = librosa.load(str(path), sr=22050, mono=True, res_type="kaiser_fast")
            except Exception:
                y = None
        if y is None or sr is None:
            if AudioSegment is None:
                return None
            try:
                seg = AudioSegment.from_file(str(path))
                sr = seg.frame_rate
                sample_width = max(seg.sample_width, 1)
                raw = np.array(seg.get_array_of_samples()).astype(np.float32)
                if seg.channels > 1:
                    raw = raw.reshape((-1, seg.channels)).mean(axis=1)
                scale = float(1 << (8 * sample_width - 1))
                y = raw / max(scale, 1.0)
                algorithm = "pydub fallback fingerprint"
            except Exception:
                return None

        if y is None or sr is None:
            return None

        y = np.asarray(y, dtype=np.float32)
        if y.size == 0:
            return None

        duration = float(len(y) / float(sr))
        if librosa is not None:
            vector = _librosa_audio_vector(y, sr)
        else:
            vector = _fallback_audio_vector(y, sr)
        if vector is None:
            return None
        return vector, duration, algorithm

    def _build_groups(self, kind: str, items: list[_Fingerprint], gid_start: int) -> tuple[list[DuplicateGroup], int]:
        if self._abort:
            return [], gid_start

        threshold = float(self.threshold) / 100.0
        parents = list(range(len(items)))
        sizes = [fp.entry.size for fp in items]
        durations = [fp.duration for fp in items]
        buckets: dict[int, list[int]] = {}
        for idx, fp in enumerate(items):
            if kind == "image":
                bucket = max(1, sizes[idx] // (256 * 1024))
            else:
                bucket = max(1, int(math.ceil(max(durations[idx], 0.01) * 2.0)))
            buckets.setdefault(bucket, []).append(idx)

        candidate_pairs: set[tuple[int, int]] = set()
        for bucket, indices in buckets.items():
            for idx in indices:
                for neighbor in (bucket - 1, bucket, bucket + 1):
                    for j in buckets.get(neighbor, []):
                        if idx < j:
                            candidate_pairs.add((idx, j))

        total_pairs = max(len(candidate_pairs), 1)
        done_pairs = 0
        pair_scores: dict[tuple[int, int], float] = {}

        for i, j in sorted(candidate_pairs):
            if self._abort:
                return [], gid_start
            done_pairs += 1
            if done_pairs % 10 == 0 or done_pairs == total_pairs:
                pct = 78 + int(done_pairs / total_pairs * 15)
                self.progress.emit(pct, f"Comparing {kind} files...")
            score = _compare_fingerprints(kind, items[i], items[j])
            if score >= threshold:
                _union(parents, i, j)
                pair_scores[(i, j)] = score

        components: dict[int, list[int]] = {}
        for idx in range(len(items)):
            root = _find(parents, idx)
            components.setdefault(root, []).append(idx)

        groups: list[DuplicateGroup] = []
        gid = gid_start
        for member_ids in components.values():
            if len(member_ids) < 2:
                continue
            members = [items[idx].entry for idx in member_ids]

            member_scores: list[float] = []
            for idx in member_ids:
                scores = [
                    pair_scores.get((min(idx, other), max(idx, other)), 0.0)
                    for other in member_ids
                    if other != idx
                ]
                score = max(scores) if scores else threshold
                items[idx].entry.similarity_score = round(score * 100.0, 1)
                member_scores.append(score)

            for member in members:
                member.group_id = gid

            group_score = sum(member_scores) / len(member_scores) if member_scores else threshold
            group = DuplicateGroup(
                gid,
                files=members,
                match_type=kind,
                algorithm="OpenCV pHash + dHash" if kind == "image" else (
                    "librosa fingerprint" if librosa is not None else "pydub fallback fingerprint"
                ),
                similarity_score=round(group_score * 100.0, 1),
            )
            groups.append(group)
            gid += 1

        return groups, gid


def _find(parents: list[int], idx: int) -> int:
    while parents[idx] != idx:
        parents[idx] = parents[parents[idx]]
        idx = parents[idx]
    return idx


def _union(parents: list[int], a: int, b: int) -> None:
    ra = _find(parents, a)
    rb = _find(parents, b)
    if ra != rb:
        parents[rb] = ra


def _image_phash(img):
    if cv2 is None or np is None:
        return 0
    resized = cv2.resize(img, (32, 32), interpolation=cv2.INTER_AREA)
    dct = cv2.dct(resized.astype(np.float32))
    block = dct[:8, :8]
    median = float(np.median(block[1:, 1:]))
    bits = block > median
    return _bits_to_int(bits)


def _image_dhash(img):
    if cv2 is None or np is None:
        return 0
    resized = cv2.resize(img, (9, 8), interpolation=cv2.INTER_AREA)
    diff = resized[:, 1:] > resized[:, :-1]
    return _bits_to_int(diff)


def _bits_to_int(bits) -> int:
    value = 0
    flat = bits.astype(bool).ravel()
    for bit in flat[:64]:
        value = (value << 1) | int(bool(bit))
    return value


def _hamming_similarity(a: int, b: int) -> float:
    distance = (a ^ b).bit_count()
    return 1.0 - (distance / 64.0)


def _color_similarity(left_color: tuple[float, float, float], right_color: tuple[float, float, float]) -> float:
    distance = math.sqrt(sum((float(left) - float(right)) ** 2 for left, right in zip(left_color, right_color)))
    max_distance = math.sqrt(3.0 * (255.0 ** 2))
    return max(0.0, min(1.0, 1.0 - (distance / max_distance)))


def _compare_fingerprints(kind: str, left: _Fingerprint, right: _Fingerprint) -> float:
    if kind == "image":
        left_phash, left_dhash, left_color = cast(ImageSignature, left.vector)
        right_phash, right_dhash, right_color = cast(ImageSignature, right.vector)
        phash_sim = _hamming_similarity(int(left_phash), int(right_phash))
        dhash_sim = _hamming_similarity(int(left_dhash), int(right_dhash))
        shape_sim = phash_sim * 0.7 + dhash_sim * 0.3
        color_sim = _color_similarity(left_color, right_color)
        return max(0.0, min(1.0, shape_sim * 0.7 + color_sim * 0.3))

    if np is None:
        return 0.0

    left_vec = np.asarray(left.vector, dtype=np.float32)
    right_vec = np.asarray(right.vector, dtype=np.float32)
    if left_vec.size == 0 or right_vec.size == 0:
        return 0.0
    size = min(left_vec.size, right_vec.size)
    left_vec = left_vec[:size]
    right_vec = right_vec[:size]
    denom = float(np.linalg.norm(left_vec) * np.linalg.norm(right_vec))
    if denom <= 1e-12:
        return 0.0
    similarity = float(np.dot(left_vec, right_vec) / denom)
    return max(0.0, min(1.0, similarity))


def _librosa_audio_vector(y, sr):
    if np is None or librosa is None:
        return None
    y = np.asarray(y, dtype=np.float32)
    if y.size == 0:
        return None

    features = [
        librosa.feature.mfcc(y=y, sr=sr, n_mfcc=20),
        librosa.feature.chroma_stft(y=y, sr=sr),
        librosa.feature.spectral_centroid(y=y, sr=sr),
        librosa.feature.spectral_bandwidth(y=y, sr=sr),
        librosa.feature.spectral_rolloff(y=y, sr=sr),
        librosa.feature.zero_crossing_rate(y),
    ]

    vector = []
    for feat in features:
        vector.append(float(np.mean(feat)))
        vector.append(float(np.std(feat)))
    return np.asarray(vector, dtype=np.float32)


def _fallback_audio_vector(y, sr):
    if np is None:
        return None
    y = np.asarray(y, dtype=np.float32)
    if y.size == 0:
        return None

    window = y[: min(y.size, sr * 30)]
    spectrum = np.abs(np.fft.rfft(window))
    if spectrum.size == 0:
        return None
    bins = np.array_split(np.log1p(spectrum), 32)
    vector = [float(np.mean(chunk)) for chunk in bins if chunk.size]
    vector.extend([
        float(np.mean(np.abs(y))),
        float(np.std(y)),
        float(len(y) / float(sr)),
    ])
    return np.asarray(vector, dtype=np.float32)
