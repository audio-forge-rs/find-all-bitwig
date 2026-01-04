# bwctl - Bitwig Command Line Controller

**Your Bitwig Studio content at your fingertips.**

A powerful CLI and API for searching, managing, and controlling Bitwig Studio programmatically. Stop clicking through endless browser menus—find any preset, sample, or device instantly and insert it with a single command.

## Vision

Bitwig Studio ships with thousands of presets, samples, and devices spread across dozens of sound packs. Finding the right sound means navigating nested menus, remembering which pack contains what, and lots of clicking. **bwctl** changes that.

**We believe:**
- Your creative tools should work at the speed of thought
- Every sound in your library should be one command away
- Programmable music production unlocks new creative workflows
- AI assistants should be able to help you produce music

## What It Does

```bash
# Find that bass preset you vaguely remember
$ bwctl search "warm analog bass"
┌────┬──────────────────────────┬──────────┬─────────────┬────────────┐
│ ID │ Name                     │ Type     │ Category    │ Package    │
├────┼──────────────────────────┼──────────┼─────────────┼────────────┤
│ 42 │ Warm Analog Bass         │ preset   │ Bass        │ Essentials │
│ 89 │ Analog Warmth Bass       │ preset   │ Bass        │ Polymerics │
│ 17 │ Bass Warm Saw            │ preset   │ Bass > Synth│ Essentials │
└────┴──────────────────────────┴──────────┴─────────────┴────────────┘

# Insert it directly into Bitwig
$ bwctl insert 42

# Or do it all in one shot
$ bwctl insert --search "warm analog bass"

# Create a track with a device and clip, ready to go
$ bwctl track add --type instrument --name "Bass" \
    && bwctl device add --name "Polymer" \
    && bwctl clip create --length 8
```

## Features

### Instant Search
- **Fuzzy matching**: "ploymer pad" finds "Polymer" presets
- **Full-text search**: Search descriptions, tags, categories
- **Filters**: By type, device, package, tags, category
- **Autocomplete**: Tab completion for everything

### Direct Control
- **Insert anything**: Presets, samples, devices, clips
- **Track operations**: Create, select, arm, mute, solo
- **Device control**: Add, remove, bypass, tweak parameters
- **Clip operations**: Create, launch, stop, edit notes
- **Transport**: Play, stop, record, loop

### Searchable Database
- **PostgreSQL-powered**: Fast, reliable, scalable
- **5,000+ presets** indexed with full metadata
- **9,500+ samples** with audio properties
- **Smart collections**: Save searches as dynamic collections
- **Usage tracking**: Recommendations based on your workflow

### Programmable
- **REST API**: Integrate with any tool or script
- **JSON output**: Pipe to jq, scripts, or AI assistants
- **OSC bridge**: Direct communication with Bitwig
- **Extensible**: Add your own commands and workflows

## Use Cases

### For Producers
- Find sounds instantly without leaving your keyboard
- Build templates programmatically
- Batch operations on tracks and clips

### For Live Performers
- Script your set with precise clip launching
- Integrate with external controllers and sensors
- Automate complex scene changes

### For Developers
- Build custom Bitwig integrations
- Create AI-powered music tools
- Automate testing and demos

### For AI Assistants
- Claude, GPT, and other LLMs can use the API
- Natural language to Bitwig commands
- "Add a fat bass to track 1" just works

## Quick Start

### Prerequisites
- Bitwig Studio 5.0+
- Docker (for PostgreSQL)
- Python 3.11+
- DrivenByMoss extension (for OSC control)

### Installation

```bash
# Clone the repo
git clone https://github.com/yourusername/bwctl.git
cd bwctl

# Start the database
docker-compose up -d

# Install the CLI
pip install -e .

# Index your Bitwig content
bwctl index --full

# You're ready!
bwctl search "piano"
```

### DrivenByMoss Setup

1. Download [DrivenByMoss](https://www.mossgrabers.de/Software/Bitwig/Bitwig.html)
2. Copy `DrivenByMoss.bwextension` to `~/Documents/Bitwig Studio/Extensions/`
3. In Bitwig: Settings → Controllers → Add Controller → Open Sound Control
4. Configure: Send port 8000, Receive port 9000

## Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────────────┐
│   bwctl     │────▶│  REST API   │────▶│    PostgreSQL       │
│   (CLI)     │     │  (FastAPI)  │     │  + Full-text Search │
└─────────────┘     └─────────────┘     └─────────────────────┘
       │                   │
       │                   ▼
       │            ┌─────────────┐
       └───────────▶│ OSC Bridge  │
                    └─────────────┘
                           │
                           ▼
                    ┌─────────────┐
                    │DrivenByMoss │
                    │ Extension   │
                    └─────────────┘
                           │
                           ▼
                    ┌─────────────┐
                    │   Bitwig    │
                    │   Studio    │
                    └─────────────┘
```

## Project Structure

```
bwctl/
├── src/bwctl/              # Main package
│   ├── cli.py              # CLI entry point
│   ├── commands/           # CLI commands
│   ├── db/                 # Database layer
│   ├── osc/                # OSC bridge
│   └── api/                # REST API
├── docker-compose.yml
├── sql/schema.sql
├── tests/
└── pyproject.toml
```

## Commands Reference

See [BITWIG_CONTROLLER_DESIGN.md](./BITWIG_CONTROLLER_DESIGN.md) for full command reference.

### Quick Reference

```bash
# Search
bwctl search "query"              # Fuzzy search all content
bwctl search -t preset "bass"     # Filter by type
bwctl search -d Polymer "pad"     # Filter by device

# Insert
bwctl insert 42                   # Insert by ID
bwctl insert --search "warm pad"  # Search and insert first result

# Tracks
bwctl track add --type instrument --name "Lead"
bwctl track select 2

# Devices
bwctl device add --name "Polymer"
bwctl device param --name "Cutoff" --value 0.7

# Clips
bwctl clip create --track 1 --slot 1 --length 8
bwctl clip launch 1:1

# Index
bwctl index --full                # Full reindex
bwctl index --incremental         # Index new files only
```

## Roadmap

- [x] Design document
- [ ] Database schema and Docker setup
- [ ] Content indexer
- [ ] Search API
- [ ] CLI foundation
- [ ] OSC bridge
- [ ] Bitwig control commands
- [ ] REST API
- [ ] AI assistant integration examples

## License

MIT License

## Acknowledgments

- [DrivenByMoss](https://github.com/git-moss/DrivenByMoss) by Jürgen Moßgraber
- [Bitwig Studio](https://www.bitwig.com) Control Surface API
