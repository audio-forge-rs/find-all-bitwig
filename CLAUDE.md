# Bitwig Controller System (bwctl)

## Project Overview

This project provides CLI control of Bitwig Studio through OSC (Open Sound Control)
using the DrivenByMoss extension. It's used in conjunction with other projects for
full music production workflow.

## Related Projects

### ~/find-all-bitwig (this project)
- **Purpose**: Search for Bitwig built-in presets, implement everything in Bitwig through OSC
- **Tools**:
  - `bwctl` CLI for searching presets in PostgreSQL database
  - OSC bridge for controlling Bitwig via DrivenByMoss
- **Key Commands**:
  ```bash
  bwctl search "Old Nylon"     # Search presets
  bwctl track add              # Add track via OSC
  bwctl track list             # List tracks with names and devices
  bwctl device add "FM-4"      # Add device to track
  bwctl clip insert file.mid -t 3 -s 1  # Insert MIDI into track 3, slot 1
  ```

### ~/concept-albums
- **Purpose**: Compose songs and write lyrics using ABC notation framework
- **Workflow**:
  1. Write `song.yaml` with structure, lyrics, chords, and ABC notation
  2. Run `python scripts/generate_song.py song-directory/`
  3. Generates MIDI files, lyrics.txt, chords.txt, arrangement.txt
  4. Use `bwctl clip insert` to load MIDI into Bitwig
- **Key Commands**:
  ```bash
  cd ~/concept-albums
  python scripts/generate_song.py album/song-directory/
  ```
- **Example**: Create album with single instrument:
  ```bash
  mkdir -p ~/concept-albums/my-album/01-song/midi
  # Create song.yaml with ABC notation
  python scripts/generate_song.py my-album/01-song/
  bwctl clip insert ~/concept-albums/my-album/01-song/midi/bass.mid -t 1 -s 1
  ```

### ~/jeannie
- **Purpose**: Search for Kontakt 8 and M-Tron Pro IV instruments/presets
- **API**: REST API at localhost:3000
- **Key Commands**:
  ```bash
  jeannie content search "acoustic guitar" --type Preset
  curl -s "http://localhost:3000/api/content/search?q=piano&type=Preset" | jq
  ```

## OSC Learnings

### Two-Way Communication
OSC is bidirectional:
- **Send to Bitwig**: Port 8000 (commands like select, volume, insert)
- **Receive from Bitwig**: Port 9000 (track names, device info, transport state)

Use `bridge.start_server()` to listen for responses. Example messages received:
- `/track/selected/name` - Current track name
- `/device/name` - Current device name
- `/tempo/raw` - Current tempo

### Touch Events Required
Volume/pan changes require touch events:
```python
send("/track/{N}/volume/touched", 1)
send("/track/{N}/volume", value)
send("/track/{N}/volume/touched", 0)
```

### Volume Conversion
dB to linear: `linear = 10^(dB/20)`
| dB | Linear | OSC (0-128) |
|----|--------|-------------|
| -6 | 0.50   | 64          |
| -10| 0.32   | 41          |
| -3 | 0.71   | 91          |

### Track Bank
- OSC controller configured for 200 tracks (no bank scrolling needed)
- `/track/1` through `/track/200` directly addressable

### Limitations
- Group track volumes CANNOT be set via OSC (manual adjustment required)
- Note devices add at end of chain (must be moved manually)
- Device chain order: Note devices -> Instrument -> Audio Effects

### Loading Third-Party Plugins via Presets
To load Kontakt/M-Tron instruments via OSC:
1. In Bitwig, load the plugin with desired preset (e.g., M-Tron Pro IV with "Hofner Bass Wah")
2. Right-click the device → "Save Preset As..."
3. Save to `~/Documents/Bitwig Studio/Library/Presets/{Plugin Name}/`
4. Run `bwctl index` to add to database
5. Search: `bwctl search "Hofner Bass"`
6. Load: `bwctl insert preset "Hofner Bass Wah (M-Tron)"`

Preset metadata returned from search:
- `name`: Preset name
- `content_type`: "preset"
- `category`: Plugin category (e.g., "M-Tron Pro IV")
- `parent_device`: Plugin name
- `file_path`: Full path to .bwpreset file

## Current Project: Midwest Meridian

Son Volt-style acoustic folk song, Rick Rubin production philosophy.

**Track Layout (with group buses)**:
1. Instruments Bus (group) - -3dB, center [MANUAL - OSC can't set group volumes]
2. Acoustic Guitar (Poly Grid - Old Nylon) - -6dB, 15% left
3. Pedal Steel (Phase-4 - Ambient Strings) - -10dB, 25% right
4. Fiddle (FM-4 - FM Violin) - -10dB, 20% left
5. Electric Guitar (Poly Grid - Jazz Guitar) - -8dB, 20% right
6. Rhythm Bus (group) - -4dB, center [MANUAL - OSC can't set group volumes]
7. Upright Bass (Poly Grid - Acoustic Bass) - -6dB, center
8. Kick (E-Kick) - -8dB, center
9. Snare (E-Snare - brush) - -10dB, center
10. Vocal (Audio placeholder) - -3dB, center

**MIDI files**: `~/concept-albums/midwest-meridian/01-midwest-meridian/midi/`

**Scripts**:
- `scripts/midwest_meridian_production.py` - Set up instruments and effects
- `scripts/load_midwest_midi.py` - Load MIDI into clip slots
- `scripts/set_mix_levels.py` - Set volume and pan (skips group tracks)
