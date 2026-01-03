# Bitwig Controller System Design

A comprehensive system for managing Bitwig Studio content with a searchable PostgreSQL database, CLI interface, and controller extension for programmatic DAW control.

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [PostgreSQL Database Schema](#postgresql-database-schema)
3. [CLI Interface Design](#cli-interface-design)
4. [Controller Extension Architecture](#controller-extension-architecture)
5. [API Reference](#api-reference)
6. [Implementation Plan](#implementation-plan)

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           Bitwig Controller System                       │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────────────────┐ │
│  │     CLI      │────▶│   REST API   │────▶│    PostgreSQL + pgvector │ │
│  │  (bwctl)     │     │   (FastAPI)  │     │    Full-text + Fuzzy     │ │
│  └──────────────┘     └──────────────┘     └──────────────────────────┘ │
│         │                    │                                           │
│         │                    │                                           │
│         ▼                    ▼                                           │
│  ┌─────────────────────────────────────────┐                            │
│  │           OSC Bridge                     │                            │
│  │     (UDP localhost:8000 ↔ 9000)         │                            │
│  └─────────────────────────────────────────┘                            │
│                        │                                                 │
│                        ▼                                                 │
│  ┌─────────────────────────────────────────┐                            │
│  │        DrivenByMoss Extension           │                            │
│  │     (Bitwig Controller Extension)       │                            │
│  └─────────────────────────────────────────┘                            │
│                        │                                                 │
│                        ▼                                                 │
│  ┌─────────────────────────────────────────┐                            │
│  │           Bitwig Studio                  │                            │
│  │      (Control Surface API)              │                            │
│  └─────────────────────────────────────────┘                            │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### Components

| Component | Technology | Purpose |
|-----------|------------|---------|
| CLI (`bwctl`) | Python/Typer | User interface for searching/controlling |
| REST API | FastAPI | HTTP interface for database and OSC bridge |
| Database | PostgreSQL 16 + pg_trgm | Content storage with fuzzy search |
| OSC Bridge | Python/python-osc | Translates commands to DrivenByMoss OSC |
| Controller | DrivenByMoss | Bitwig extension receiving OSC commands |

---

## PostgreSQL Database Schema

### Extensions Required

```sql
CREATE EXTENSION IF NOT EXISTS pg_trgm;      -- Fuzzy text matching
CREATE EXTENSION IF NOT EXISTS unaccent;     -- Accent-insensitive search
CREATE EXTENSION IF NOT EXISTS btree_gin;    -- GIN index support
```

### Core Tables

```sql
-- Content Types Enum
CREATE TYPE content_type AS ENUM (
    'preset',      -- .bwpreset
    'clip',        -- .bwclip
    'sample',      -- .wav, .aif, .flac
    'multisample', -- .multisample
    'impulse',     -- .bwimpulse
    'curve',       -- .bwcurve
    'wavetable',   -- .bwwavetable
    'device',      -- Bitwig native devices
    'plugin',      -- VST/CLAP plugins
    'template',    -- .bwtemplate
    'project'      -- .bwproject
);

-- Device Type Enum
CREATE TYPE device_type AS ENUM (
    'instrument',
    'audio_fx',
    'note_fx',
    'modulator',
    'container',
    'utility'
);

-- Packages (Sound Packs)
CREATE TABLE packages (
    id              SERIAL PRIMARY KEY,
    name            VARCHAR(255) NOT NULL,
    vendor          VARCHAR(255) NOT NULL,
    version         VARCHAR(50),
    path            TEXT NOT NULL UNIQUE,
    installed_at    TIMESTAMP DEFAULT NOW(),
    is_factory      BOOLEAN DEFAULT FALSE,

    -- Search optimization
    search_vector   TSVECTOR GENERATED ALWAYS AS (
        setweight(to_tsvector('english', name), 'A') ||
        setweight(to_tsvector('english', vendor), 'B')
    ) STORED
);

-- Main Content Table
CREATE TABLE content (
    id              SERIAL PRIMARY KEY,

    -- Identity
    name            VARCHAR(500) NOT NULL,
    file_path       TEXT NOT NULL UNIQUE,
    content_type    content_type NOT NULL,

    -- Relationships
    package_id      INTEGER REFERENCES packages(id),
    parent_device   VARCHAR(255),           -- For presets: which device they belong to

    -- Metadata
    description     TEXT,
    category        VARCHAR(255),           -- e.g., "Bass", "Pad", "Drums"
    subcategory     VARCHAR(255),           -- e.g., "Analog", "FM", "Sampled"
    tags            TEXT[],                 -- ["dark", "ambient", "cinematic"]
    creator         VARCHAR(255),

    -- Technical Details
    device_type     device_type,
    device_uuid     UUID,                   -- Bitwig device UUID for insertion
    plugin_id       VARCHAR(255),           -- VST3/CLAP plugin identifier

    -- Audio Properties (for samples)
    sample_rate     INTEGER,
    channels        SMALLINT,
    duration_ms     INTEGER,
    bpm             DECIMAL(6,2),
    key_signature   VARCHAR(10),            -- e.g., "C major", "F# minor"

    -- File Info
    file_size       BIGINT,
    file_hash       VARCHAR(64),            -- SHA-256 for deduplication
    modified_at     TIMESTAMP,
    indexed_at      TIMESTAMP DEFAULT NOW(),

    -- Full-text Search
    search_vector   TSVECTOR GENERATED ALWAYS AS (
        setweight(to_tsvector('english', coalesce(name, '')), 'A') ||
        setweight(to_tsvector('english', coalesce(description, '')), 'B') ||
        setweight(to_tsvector('english', coalesce(category, '')), 'C') ||
        setweight(to_tsvector('english', array_to_string(tags, ' ')), 'C') ||
        setweight(to_tsvector('english', coalesce(creator, '')), 'D')
    ) STORED
);

-- Device Parameters (for presets)
CREATE TABLE preset_parameters (
    id              SERIAL PRIMARY KEY,
    content_id      INTEGER REFERENCES content(id) ON DELETE CASCADE,
    param_name      VARCHAR(255) NOT NULL,
    param_value     DECIMAL(20,10),
    param_text      VARCHAR(500),

    UNIQUE(content_id, param_name)
);

-- User Collections
CREATE TABLE collections (
    id              SERIAL PRIMARY KEY,
    name            VARCHAR(255) NOT NULL UNIQUE,
    description     TEXT,
    is_smart        BOOLEAN DEFAULT FALSE,  -- Smart collection with query
    query           JSONB,                  -- Filter criteria for smart collections
    created_at      TIMESTAMP DEFAULT NOW()
);

CREATE TABLE collection_items (
    collection_id   INTEGER REFERENCES collections(id) ON DELETE CASCADE,
    content_id      INTEGER REFERENCES content(id) ON DELETE CASCADE,
    added_at        TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (collection_id, content_id)
);

-- Usage History (for recommendations)
CREATE TABLE usage_history (
    id              SERIAL PRIMARY KEY,
    content_id      INTEGER REFERENCES content(id) ON DELETE CASCADE,
    action          VARCHAR(50) NOT NULL,   -- 'inserted', 'previewed', 'favorited'
    context         JSONB,                  -- Additional context (track type, project, etc.)
    used_at         TIMESTAMP DEFAULT NOW()
);
```

### Indexes for Fast Search

```sql
-- Full-text search indexes
CREATE INDEX idx_content_search ON content USING GIN(search_vector);
CREATE INDEX idx_packages_search ON packages USING GIN(search_vector);

-- Fuzzy search with trigrams
CREATE INDEX idx_content_name_trgm ON content USING GIN(name gin_trgm_ops);
CREATE INDEX idx_content_category_trgm ON content USING GIN(category gin_trgm_ops);
CREATE INDEX idx_content_tags ON content USING GIN(tags);

-- Filter indexes
CREATE INDEX idx_content_type ON content(content_type);
CREATE INDEX idx_content_device_type ON content(device_type);
CREATE INDEX idx_content_package ON content(package_id);
CREATE INDEX idx_content_parent_device ON content(parent_device);

-- Composite indexes for common queries
CREATE INDEX idx_content_type_category ON content(content_type, category);
CREATE INDEX idx_content_device_category ON content(device_type, category);
```

### Search Functions

```sql
-- Fuzzy search with ranking
CREATE OR REPLACE FUNCTION search_content(
    query_text TEXT,
    filter_type content_type DEFAULT NULL,
    filter_device_type device_type DEFAULT NULL,
    filter_category TEXT DEFAULT NULL,
    limit_results INTEGER DEFAULT 50
)
RETURNS TABLE (
    id INTEGER,
    name VARCHAR,
    content_type content_type,
    category VARCHAR,
    file_path TEXT,
    relevance REAL
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        c.id,
        c.name,
        c.content_type,
        c.category,
        c.file_path,
        (
            -- Combine full-text and trigram similarity
            ts_rank(c.search_vector, websearch_to_tsquery('english', query_text)) * 0.6 +
            similarity(c.name, query_text) * 0.4
        )::REAL as relevance
    FROM content c
    WHERE
        (filter_type IS NULL OR c.content_type = filter_type)
        AND (filter_device_type IS NULL OR c.device_type = filter_device_type)
        AND (filter_category IS NULL OR c.category ILIKE '%' || filter_category || '%')
        AND (
            c.search_vector @@ websearch_to_tsquery('english', query_text)
            OR c.name % query_text  -- Trigram similarity
            OR c.name ILIKE '%' || query_text || '%'
        )
    ORDER BY relevance DESC
    LIMIT limit_results;
END;
$$ LANGUAGE plpgsql;

-- Autocomplete function
CREATE OR REPLACE FUNCTION autocomplete_content(
    partial_text TEXT,
    limit_results INTEGER DEFAULT 10
)
RETURNS TABLE (
    suggestion TEXT,
    content_type content_type,
    match_count BIGINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        c.name::TEXT as suggestion,
        c.content_type,
        COUNT(*)::BIGINT as match_count
    FROM content c
    WHERE c.name ILIKE partial_text || '%'
    GROUP BY c.name, c.content_type
    ORDER BY match_count DESC, c.name
    LIMIT limit_results;
END;
$$ LANGUAGE plpgsql;
```

---

## CLI Interface Design

### Command Structure

```
bwctl - Bitwig Controller CLI

USAGE:
    bwctl <COMMAND> [OPTIONS]

COMMANDS:
    search      Search for content (presets, samples, devices)
    insert      Insert content into Bitwig
    track       Track operations (create, select, modify)
    clip        Clip operations (create, launch, edit)
    device      Device operations (add, remove, parameter control)
    transport   Transport controls (play, stop, record)
    index       Index/reindex content database
    sync        Sync database with file system

OPTIONS:
    -v, --verbose    Verbose output
    -j, --json       JSON output format
    --config PATH    Config file path
```

### Search Command

```
bwctl search [OPTIONS] <QUERY>

Search for Bitwig content with fuzzy matching.

ARGUMENTS:
    <QUERY>          Search query (supports fuzzy matching)

OPTIONS:
    -t, --type TYPE      Filter by type: preset, sample, device, clip, plugin
    -c, --category CAT   Filter by category
    -d, --device DEV     Filter by parent device name
    -p, --package PKG    Filter by package/vendor
    --tags TAGS          Filter by tags (comma-separated)
    -n, --limit N        Max results (default: 20)
    --offset N           Skip first N results
    -o, --output FORMAT  Output: table, json, paths
    --preview            Preview audio samples

EXAMPLES:
    bwctl search "analog bass"
    bwctl search "pad" -t preset -c "Synth"
    bwctl search "kick" -t sample --tags "punchy,808"
    bwctl search "polymer" -d "Polymer" -t preset
```

### Insert Command

```
bwctl insert [OPTIONS] <CONTENT_ID|PATH|QUERY>

Insert content into Bitwig at the current or specified location.

ARGUMENTS:
    <CONTENT_ID>     Database content ID
    <PATH>           Direct file path
    <QUERY>          Search query (uses first result)

OPTIONS:
    --track N        Insert on track N (1-indexed)
    --slot N         Clip launcher slot (for clips)
    --after          Insert after current device
    --before         Insert before current device
    --replace        Replace current device
    --dry-run        Show what would be inserted

EXAMPLES:
    bwctl insert 1234
    bwctl insert "~/presets/my-bass.bwpreset"
    bwctl insert --query "warm pad" --track 2
```

### Track Command

```
bwctl track <SUBCOMMAND> [OPTIONS]

Track operations in Bitwig.

SUBCOMMANDS:
    add         Create new track
    select      Select track by number or name
    rename      Rename current/specified track
    delete      Remove track
    list        List all tracks
    arm         Arm track for recording
    mute        Toggle mute
    solo        Toggle solo

OPTIONS (add):
    --type TYPE      Track type: audio, instrument, effect, group
    --name NAME      Track name
    --color COLOR    Track color (hex or name)
    --position N     Insert position

EXAMPLES:
    bwctl track add --type instrument --name "Synth Lead"
    bwctl track select 3
    bwctl track arm 1 2 3  # Arm tracks 1, 2, 3
    bwctl track mute --all
```

### Clip Command

```
bwctl clip <SUBCOMMAND> [OPTIONS]

Clip operations in Bitwig.

SUBCOMMANDS:
    create      Create new empty clip
    launch      Launch clip(s)
    stop        Stop clip(s)
    record      Start recording into clip
    duplicate   Duplicate clip
    delete      Remove clip
    note        Note editing operations

OPTIONS (create):
    --track N        Track number
    --slot N         Slot number
    --length BEATS   Clip length in beats (default: 4)
    --name NAME      Clip name

OPTIONS (note):
    --add            Add note(s)
    --remove         Remove note(s)
    --pitch N        Note pitch (0-127 or note name)
    --start BEAT     Start position in beats
    --length BEAT    Note length in beats
    --velocity N     Note velocity (0-127)

EXAMPLES:
    bwctl clip create --track 1 --slot 1 --length 8
    bwctl clip launch 1:1  # Track 1, Slot 1
    bwctl clip note --add --pitch C3 --start 0 --length 1 --velocity 100
```

### Device Command

```
bwctl device <SUBCOMMAND> [OPTIONS]

Device operations in Bitwig.

SUBCOMMANDS:
    add         Add device to track
    remove      Remove device
    bypass      Toggle bypass
    select      Select device
    param       Control device parameters
    preset      Load/save device presets
    list        List devices on track

OPTIONS (add):
    --name NAME      Device name (fuzzy search)
    --id UUID        Bitwig device UUID
    --vst3 ID        VST3 plugin ID
    --clap ID        CLAP plugin ID
    --track N        Target track
    --position N     Chain position

OPTIONS (param):
    --name NAME      Parameter name
    --value VALUE    New value (0.0-1.0 or %)
    --page N         Remote control page

EXAMPLES:
    bwctl device add --name "Polymer" --track 1
    bwctl device add --vst3 "com.u-he.Diva" --track 2
    bwctl device param --name "Cutoff" --value 0.75
    bwctl device bypass --toggle
```

### Index Command

```
bwctl index [OPTIONS]

Index Bitwig content into the database.

OPTIONS:
    --full           Full reindex (drop and rebuild)
    --incremental    Only index new/modified files
    --path PATH      Index specific path
    --type TYPE      Only index specific content type
    --dry-run        Show what would be indexed
    --workers N      Parallel indexing workers (default: 4)

EXAMPLES:
    bwctl index --full
    bwctl index --incremental
    bwctl index --path "~/Library/Application Support/Bitwig"
```

---

## Controller Extension Architecture

### Communication Protocol

The system uses OSC (Open Sound Control) via DrivenByMoss extension for bidirectional communication with Bitwig.

```
CLI/API  ──UDP:8000──▶  OSC Bridge  ──UDP:9000──▶  DrivenByMoss  ──▶  Bitwig
                             ◀──UDP:8001──          ◀──UDP:9001──
```

### OSC Command Mapping

| CLI Command | OSC Path | Parameters |
|-------------|----------|------------|
| `track add --type instrument` | `/track/add/instrument` | - |
| `track add --type audio` | `/track/add/audio` | - |
| `track select N` | `/track/{N}/select` | - |
| `track mute N` | `/track/{N}/mute` | `{0,1,-}` toggle |
| `device add --name X` | `/browser/device` then navigate | - |
| `clip create --length N` | `/clip/create` | `{beats}` |
| `clip launch T:S` | `/track/{T}/clip/{S}/launch` | `{0,1}` |
| `transport play` | `/play` | - |
| `transport stop` | `/stop` | - |

### OSC Bridge Implementation

```python
# osc_bridge.py
import asyncio
from pythonosc import udp_client, dispatcher, osc_server

class BitwigOSCBridge:
    """Bridge between REST API and DrivenByMoss OSC."""

    def __init__(self,
                 send_host="127.0.0.1", send_port=8000,
                 receive_port=9000):
        self.client = udp_client.SimpleUDPClient(send_host, send_port)
        self.dispatcher = dispatcher.Dispatcher()
        self.state = BitwigState()

        # Register handlers for incoming OSC messages
        self._setup_handlers()

    def _setup_handlers(self):
        """Set up OSC message handlers for state updates."""
        self.dispatcher.map("/track/*/name", self._on_track_name)
        self.dispatcher.map("/track/*/volume", self._on_track_volume)
        self.dispatcher.map("/device/name", self._on_device_name)
        self.dispatcher.map("/device/param/*/name", self._on_param_name)
        self.dispatcher.map("/device/param/*/value", self._on_param_value)

    # Track Operations
    def add_track(self, track_type: str) -> None:
        """Add a new track."""
        self.client.send_message(f"/track/add/{track_type}", [])

    def select_track(self, index: int) -> None:
        """Select track by index (1-indexed)."""
        self.client.send_message(f"/track/{index}/select", [])

    def set_track_mute(self, index: int, mute: bool) -> None:
        """Set track mute state."""
        self.client.send_message(f"/track/{index}/mute", [1 if mute else 0])

    # Device Operations
    def open_device_browser(self) -> None:
        """Open the device browser."""
        self.client.send_message("/browser/device", [])

    def navigate_browser(self, direction: int) -> None:
        """Navigate browser results (+1 or -1)."""
        path = "/browser/result/+" if direction > 0 else "/browser/result/-"
        self.client.send_message(path, [])

    def commit_browser(self) -> None:
        """Commit browser selection (insert device)."""
        self.client.send_message("/browser/commit", [])

    def set_device_param(self, index: int, value: float) -> None:
        """Set device parameter value (0.0-1.0)."""
        self.client.send_message(f"/device/param/{index}/value", [value])

    # Clip Operations
    def create_clip(self, track: int, slot: int, length_beats: int) -> None:
        """Create a new clip."""
        self.select_track(track)
        self.client.send_message(f"/track/{track}/clip/{slot}/create", [length_beats])

    def launch_clip(self, track: int, slot: int) -> None:
        """Launch a clip."""
        self.client.send_message(f"/track/{track}/clip/{slot}/launch", [1])

    def stop_clip(self, track: int, slot: int) -> None:
        """Stop a clip."""
        self.client.send_message(f"/track/{track}/clip/{slot}/launch", [0])

    # Note Operations
    def set_note(self, channel: int, step: int, key: int,
                 velocity: int = 100, duration: float = 1.0) -> None:
        """Add a note to the current clip."""
        self.client.send_message("/clip/setStep", [channel, step, key, velocity, duration])

    def clear_note(self, channel: int, step: int, key: int) -> None:
        """Remove a note from the current clip."""
        self.client.send_message("/clip/clearStep", [channel, step, key])
```

### Custom Extension (Optional)

For operations not supported by DrivenByMoss, a custom Bitwig extension can be created:

```java
// BitwigControllerExtension.java
package com.example.bitwigcontroller;

import com.bitwig.extension.controller.ControllerExtension;
import com.bitwig.extension.controller.api.*;
import com.bitwig.extension.api.opensoundcontrol.*;

public class BitwigControllerExtension extends ControllerExtension {
    private OscModule oscModule;
    private OscServer oscServer;
    private ControllerHost host;
    private TrackBank trackBank;
    private CursorTrack cursorTrack;
    private CursorDevice cursorDevice;

    @Override
    public void init() {
        host = getHost();
        oscModule = host.getOscModule();

        // Create OSC server on custom port
        oscServer = oscModule.createUdpServer(9100);

        // Set up track bank
        trackBank = host.createMainTrackBank(8, 8, 8);
        cursorTrack = host.createCursorTrack(8, 8);
        cursorDevice = cursorTrack.createCursorDevice();

        // Register OSC handlers
        registerHandlers();
    }

    private void registerHandlers() {
        OscAddressSpace addressSpace = oscServer.getAddressSpace();

        // Insert device by UUID
        addressSpace.registerMethod("/device/insert/uuid", "*",
            (source, message) -> {
                String uuidString = message.getString(0);
                UUID uuid = UUID.fromString(uuidString);
                InsertionPoint insertion = cursorDevice.afterDeviceInsertionPoint();
                insertion.insertBitwigDevice(uuid);
            });

        // Insert file (preset, sample, etc.)
        addressSpace.registerMethod("/insert/file", "*",
            (source, message) -> {
                String path = message.getString(0);
                InsertionPoint insertion = cursorDevice.afterDeviceInsertionPoint();
                insertion.insertFile(path);
            });

        // Insert VST3 plugin
        addressSpace.registerMethod("/device/insert/vst3", "*",
            (source, message) -> {
                String pluginId = message.getString(0);
                InsertionPoint insertion = cursorDevice.afterDeviceInsertionPoint();
                insertion.insertVST3Device(pluginId);
            });

        // Insert CLAP plugin
        addressSpace.registerMethod("/device/insert/clap", "*",
            (source, message) -> {
                String pluginId = message.getString(0);
                InsertionPoint insertion = cursorDevice.afterDeviceInsertionPoint();
                insertion.insertCLAPDevice(pluginId);
            });
    }
}
```

---

## API Reference

### REST API Endpoints

```
Base URL: http://localhost:8080/api/v1

# Search
GET  /search?q={query}&type={type}&category={cat}&limit={n}
GET  /autocomplete?q={partial}

# Content
GET  /content/{id}
GET  /content?type={type}&package={pkg}
POST /content/index              # Trigger indexing

# Packages
GET  /packages
GET  /packages/{id}
GET  /packages/{id}/content

# Collections
GET  /collections
POST /collections
GET  /collections/{id}
POST /collections/{id}/items
DELETE /collections/{id}/items/{content_id}

# Bitwig Control (via OSC bridge)
POST /bitwig/track/add           {"type": "instrument", "name": "..."}
POST /bitwig/track/{n}/select
POST /bitwig/device/add          {"name": "Polymer"}
POST /bitwig/device/insert       {"uuid": "...", "path": "..."}
POST /bitwig/clip/create         {"track": 1, "slot": 1, "length": 8}
POST /bitwig/clip/{t}/{s}/launch
POST /bitwig/transport/play
POST /bitwig/transport/stop
```

### Response Format

```json
{
  "success": true,
  "data": { ... },
  "meta": {
    "total": 150,
    "limit": 20,
    "offset": 0,
    "query_time_ms": 12
  }
}
```

---

## Implementation Plan

### Phase 1: Database & Indexer (Week 1-2)

1. Set up PostgreSQL with extensions
2. Create database schema
3. Build content indexer
   - Parse Bitwig package structure
   - Extract metadata from .bwpreset files
   - Hash files for deduplication
4. Implement search functions

### Phase 2: CLI Foundation (Week 2-3)

1. Create Python CLI with Typer
2. Implement search command
3. Add index command
4. Set up configuration management

### Phase 3: OSC Bridge (Week 3-4)

1. Implement OSC client/server
2. Map CLI commands to OSC messages
3. Handle bidirectional state sync
4. Add track/device/clip commands

### Phase 4: REST API (Week 4-5)

1. Create FastAPI application
2. Implement search endpoints
3. Add Bitwig control endpoints
4. WebSocket for live state updates

### Phase 5: Custom Extension (Week 5-6)

1. Create Bitwig extension project
2. Implement InsertionPoint operations
3. Add advanced device insertion
4. Test with CLI integration

### Phase 6: Polish & Documentation (Week 6+)

1. Error handling and edge cases
2. Performance optimization
3. User documentation
4. Example workflows

---

## Sources

- [Bitwig Control Surface API](file:///Applications/Bitwig%20Studio.app/Contents/Resources/Documentation/control-surface/api/index.html)
- [DrivenByMoss GitHub](https://github.com/git-moss/DrivenByMoss)
- [DrivenByMoss OSC Documentation](https://github.com/git-moss/DrivenByMoss-Documentation/blob/master/Generic-Tools-Protocols/Open-Sound-Control-(OSC).md)
- [Bitwig Browsers Documentation](https://www.bitwig.com/userguide/latest/browsers/)
