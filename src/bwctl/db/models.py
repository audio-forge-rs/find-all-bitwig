"""Database models for bwctl."""

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class ContentType(str, Enum):
    """Types of content in the database."""

    PRESET = "preset"
    CLIP = "clip"
    SAMPLE = "sample"
    MULTISAMPLE = "multisample"
    IMPULSE = "impulse"
    CURVE = "curve"
    WAVETABLE = "wavetable"
    DEVICE = "device"
    PLUGIN = "plugin"
    TEMPLATE = "template"
    PROJECT = "project"


class DeviceType(str, Enum):
    """Types of Bitwig devices."""

    INSTRUMENT = "instrument"
    AUDIO_FX = "audio_fx"
    NOTE_FX = "note_fx"
    MODULATOR = "modulator"
    CONTAINER = "container"
    UTILITY = "utility"


class Package(BaseModel):
    """A Bitwig sound pack or content package."""

    id: int | None = None
    name: str
    vendor: str
    version: str | None = None
    path: str
    installed_at: datetime | None = None
    is_factory: bool = False


class Content(BaseModel):
    """A piece of Bitwig content (preset, sample, etc.)."""

    id: int | None = None

    # Identity
    name: str
    file_path: str
    content_type: ContentType

    # Relationships
    package_id: int | None = None
    parent_device: str | None = None

    # Metadata
    description: str | None = None
    category: str | None = None
    subcategory: str | None = None
    tags: list[str] = Field(default_factory=list)
    creator: str | None = None

    # Technical Details
    device_type: DeviceType | None = None
    device_uuid: UUID | None = None
    plugin_id: str | None = None

    # Audio Properties
    sample_rate: int | None = None
    channels: int | None = None
    duration_ms: int | None = None
    bpm: float | None = None
    key_signature: str | None = None

    # File Info
    file_size: int | None = None
    file_hash: str | None = None
    modified_at: datetime | None = None
    indexed_at: datetime | None = None


class SearchResult(BaseModel):
    """A search result with relevance score."""

    id: int
    name: str
    content_type: ContentType
    category: str | None = None
    parent_device: str | None = None
    file_path: str
    package_name: str | None = None
    relevance: float = 0.0

    @classmethod
    def from_row(cls, row: dict[str, Any]) -> "SearchResult":
        """Create a SearchResult from a database row."""
        return cls(
            id=row["id"],
            name=row["name"],
            content_type=ContentType(row["content_type"]),
            category=row.get("category"),
            parent_device=row.get("parent_device"),
            file_path=row["file_path"],
            package_name=row.get("package_name"),
            relevance=row.get("relevance", 0.0),
        )
