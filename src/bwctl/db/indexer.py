"""Content indexer for Bitwig Studio files."""

import hashlib
import os
import re
import wave
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import Iterator

from rich.progress import Progress, TaskID

from bwctl.config import settings
from bwctl.db.connection import get_connection
from bwctl.db.models import Content, ContentType, DeviceType, Package

# File extension to content type mapping
EXTENSION_MAP: dict[str, ContentType] = {
    ".bwpreset": ContentType.PRESET,
    ".bwclip": ContentType.CLIP,
    ".wav": ContentType.SAMPLE,
    ".aif": ContentType.SAMPLE,
    ".aiff": ContentType.SAMPLE,
    ".flac": ContentType.SAMPLE,
    ".ogg": ContentType.SAMPLE,
    ".mp3": ContentType.SAMPLE,
    ".multisample": ContentType.MULTISAMPLE,
    ".bwimpulse": ContentType.IMPULSE,
    ".bwcurve": ContentType.CURVE,
    ".bwwavetable": ContentType.WAVETABLE,
    ".bwtemplate": ContentType.TEMPLATE,
    ".bwproject": ContentType.PROJECT,
}

# Device name to type mapping (common patterns)
DEVICE_TYPE_PATTERNS: dict[str, DeviceType] = {
    r"(?i)(polymer|phase-4|fm-4|polysynth|sampler|organ|piano|synth|instrument)": DeviceType.INSTRUMENT,
    r"(?i)(eq|filter|comp|reverb|delay|chorus|flanger|phaser|distort|amp|fx)": DeviceType.AUDIO_FX,
    r"(?i)(arpeggiator|note|chord|scale|transpose|velocity|midi)": DeviceType.NOTE_FX,
    r"(?i)(lfo|adsr|envelope|steps|curve|macro|modulator)": DeviceType.MODULATOR,
    r"(?i)(layer|chain|selector|container|rack|split)": DeviceType.CONTAINER,
    r"(?i)(meter|tool|utility|audio receiver|note receiver)": DeviceType.UTILITY,
}


def get_content_type(path: Path) -> ContentType | None:
    """Get the content type for a file."""
    ext = path.suffix.lower()
    return EXTENSION_MAP.get(ext)


def get_device_type(device_name: str) -> DeviceType | None:
    """Infer device type from device name."""
    for pattern, device_type in DEVICE_TYPE_PATTERNS.items():
        if re.search(pattern, device_name):
            return device_type
    return None


def compute_file_hash(path: Path) -> str:
    """Compute SHA-256 hash of a file."""
    hasher = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def get_wav_info(path: Path) -> dict:
    """Get audio info from a WAV file."""
    try:
        with wave.open(str(path), "rb") as wav:
            return {
                "sample_rate": wav.getframerate(),
                "channels": wav.getnchannels(),
                "duration_ms": int(wav.getnframes() / wav.getframerate() * 1000),
            }
    except Exception:
        return {}


def parse_preset_name(name: str) -> dict:
    """Parse preset name to extract category and tags.

    Many presets follow naming conventions like:
    - "Bass - Analog Warmth"
    - "Pad_Ambient_Dark"
    - "[Bass] Deep Sub"
    """
    result: dict = {"category": None, "tags": []}

    # Check for category prefix patterns
    # Pattern: "Category - Name"
    if " - " in name:
        parts = name.split(" - ", 1)
        result["category"] = parts[0].strip()
        name = parts[1].strip()

    # Pattern: "[Category] Name"
    bracket_match = re.match(r"\[([^\]]+)\]\s*(.+)", name)
    if bracket_match:
        result["category"] = bracket_match.group(1)
        name = bracket_match.group(2)

    # Extract tags from common keywords in name
    tag_patterns = [
        r"(?i)\b(analog|digital|fm|wavetable|sample|granular)\b",
        r"(?i)\b(warm|cold|dark|bright|soft|hard|aggressive)\b",
        r"(?i)\b(ambient|cinematic|vintage|modern|classic)\b",
        r"(?i)\b(bass|lead|pad|pluck|keys|strings|brass|perc)\b",
    ]

    for pattern in tag_patterns:
        matches = re.findall(pattern, name)
        result["tags"].extend([m.lower() for m in matches])

    return result


def discover_packages(base_path: Path) -> list[dict]:
    """Discover Bitwig packages in a directory."""
    packages = []

    # Pattern: installed-packages/5.0/Vendor/PackageName/
    installed_packages = base_path / "installed-packages"
    if installed_packages.exists():
        for version_dir in installed_packages.iterdir():
            if not version_dir.is_dir():
                continue
            for vendor_dir in version_dir.iterdir():
                if not vendor_dir.is_dir():
                    continue
                vendor = vendor_dir.name
                for package_dir in vendor_dir.iterdir():
                    if not package_dir.is_dir():
                        continue
                    packages.append({
                        "name": package_dir.name,
                        "vendor": vendor,
                        "version": version_dir.name,
                        "path": str(package_dir),
                        "is_factory": vendor == "Bitwig",
                    })

    return packages


def discover_content(package_path: Path) -> Iterator[Path]:
    """Discover all content files in a package directory."""
    for ext in EXTENSION_MAP:
        yield from package_path.rglob(f"*{ext}")


def index_file(path: Path, package_id: int | None = None) -> Content | None:
    """Index a single file and return a Content object."""
    content_type = get_content_type(path)
    if content_type is None:
        return None

    name = path.stem
    stat = path.stat()

    # Parse metadata from name/path
    parsed = parse_preset_name(name)

    # Infer parent device from path
    # Pattern: .../Presets/DeviceName/preset.bwpreset
    parent_device = None
    parts = path.parts
    if "Presets" in parts:
        preset_idx = parts.index("Presets")
        if preset_idx + 1 < len(parts) - 1:
            parent_device = parts[preset_idx + 1]

    # Infer category from path if not parsed from name
    category = parsed.get("category")
    if not category and parent_device:
        # Use parent device as category for presets
        category = parent_device

    # Get device type
    device_type = None
    if parent_device:
        device_type = get_device_type(parent_device)

    # Get audio properties for samples
    audio_props = {}
    if content_type == ContentType.SAMPLE and path.suffix.lower() == ".wav":
        audio_props = get_wav_info(path)

    return Content(
        name=name,
        file_path=str(path),
        content_type=content_type,
        package_id=package_id,
        parent_device=parent_device,
        category=category,
        tags=parsed.get("tags", []),
        device_type=device_type,
        file_size=stat.st_size,
        modified_at=datetime.fromtimestamp(stat.st_mtime),
        **audio_props,
    )


def save_package(package: dict) -> int:
    """Save a package to the database and return its ID."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO packages (name, vendor, version, path, is_factory)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (path) DO UPDATE SET
                    name = EXCLUDED.name,
                    vendor = EXCLUDED.vendor,
                    version = EXCLUDED.version,
                    is_factory = EXCLUDED.is_factory
                RETURNING id
                """,
                (
                    package["name"],
                    package["vendor"],
                    package.get("version"),
                    package["path"],
                    package.get("is_factory", False),
                ),
            )
            result = cur.fetchone()
            conn.commit()
            return result["id"]


def save_content(content: Content) -> int | None:
    """Save content to the database and return its ID."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            try:
                cur.execute(
                    """
                    INSERT INTO content (
                        name, file_path, content_type, package_id, parent_device,
                        description, category, subcategory, tags, creator,
                        device_type, device_uuid, plugin_id,
                        sample_rate, channels, duration_ms, bpm, key_signature,
                        file_size, file_hash, modified_at
                    ) VALUES (
                        %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s,
                        %s, %s, %s,
                        %s, %s, %s, %s, %s,
                        %s, %s, %s
                    )
                    ON CONFLICT (file_path) DO UPDATE SET
                        name = EXCLUDED.name,
                        content_type = EXCLUDED.content_type,
                        package_id = EXCLUDED.package_id,
                        parent_device = EXCLUDED.parent_device,
                        category = EXCLUDED.category,
                        tags = EXCLUDED.tags,
                        device_type = EXCLUDED.device_type,
                        file_size = EXCLUDED.file_size,
                        modified_at = EXCLUDED.modified_at,
                        indexed_at = NOW()
                    RETURNING id
                    """,
                    (
                        content.name,
                        content.file_path,
                        content.content_type.value,
                        content.package_id,
                        content.parent_device,
                        content.description,
                        content.category,
                        content.subcategory,
                        content.tags or [],
                        content.creator,
                        content.device_type.value if content.device_type else None,
                        str(content.device_uuid) if content.device_uuid else None,
                        content.plugin_id,
                        content.sample_rate,
                        content.channels,
                        content.duration_ms,
                        content.bpm,
                        content.key_signature,
                        content.file_size,
                        content.file_hash,
                        content.modified_at,
                    ),
                )
                result = cur.fetchone()
                conn.commit()
                return result["id"] if result else None
            except Exception as e:
                conn.rollback()
                raise e


def clear_index() -> int:
    """Clear all indexed content. Returns number of rows deleted."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM content")
            cur.execute("DELETE FROM packages")
            count = cur.rowcount
            conn.commit()
            return count


def run_indexer(
    paths: list[str] | None = None,
    full: bool = False,
    workers: int = 4,
    progress: Progress | None = None,
) -> dict[str, int]:
    """Run the content indexer.

    Args:
        paths: Paths to index (defaults to configured paths)
        full: If True, clear existing index first
        workers: Number of parallel workers
        progress: Rich progress bar to update

    Returns:
        Dictionary with indexing statistics
    """
    if paths is None:
        paths = settings.bitwig.content_paths

    stats = {"packages": 0, "files": 0, "errors": 0}

    if full:
        clear_index()

    # Discover and index packages
    all_packages = []
    for path_str in paths:
        path = Path(path_str).expanduser()
        if path.exists():
            packages = discover_packages(path)
            all_packages.extend(packages)

    # Save packages first
    package_ids = {}
    for pkg in all_packages:
        pkg_id = save_package(pkg)
        package_ids[pkg["path"]] = pkg_id
        stats["packages"] += 1

    # Collect all files to index
    files_to_index: list[tuple[Path, int | None]] = []
    for pkg in all_packages:
        pkg_path = Path(pkg["path"])
        pkg_id = package_ids[pkg["path"]]
        for file_path in discover_content(pkg_path):
            files_to_index.append((file_path, pkg_id))

    # Also index user library (not in packages)
    for path_str in paths:
        path = Path(path_str).expanduser()
        if path.exists() and "installed-packages" not in str(path):
            for file_path in discover_content(path):
                files_to_index.append((file_path, None))

    # Index files in parallel
    task_id: TaskID | None = None
    if progress:
        task_id = progress.add_task("Indexing files...", total=len(files_to_index))

    def index_one(args: tuple[Path, int | None]) -> bool:
        file_path, pkg_id = args
        try:
            content = index_file(file_path, pkg_id)
            if content:
                save_content(content)
                return True
        except Exception:
            return False
        return False

    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = [executor.submit(index_one, args) for args in files_to_index]
        for future in as_completed(futures):
            if future.result():
                stats["files"] += 1
            else:
                stats["errors"] += 1
            if progress and task_id is not None:
                progress.advance(task_id)

    return stats
