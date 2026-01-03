# Bitwig Studio File Locations Guide

Reference for locating all Bitwig Studio devices, presets, samples, and content on macOS.

## Primary Storage Locations

### User Library (My Library)
```
~/Documents/Bitwig Studio/
├── Library/
│   ├── Presets/          # User-created presets by device type
│   ├── Templates/        # Project templates (.bwtemplate)
│   └── .settings/        # Device-specific settings
├── Projects/             # All project folders
├── Extensions/           # .bwextension files
├── Controller Scripts/   # Custom controller scripts
└── Color Palettes/       # Custom color palettes
```

### Application Support (System Data)
```
~/Library/Application Support/Bitwig/Bitwig Studio/
├── installed-packages/
│   └── 5.0/              # Version-specific packages
│       ├── Bitwig/       # Official Bitwig content packs
│       └── [Vendor]/     # Third-party sound packs
├── library/
│   ├── devices/          # Device collections & smart collections
│   ├── presets/          # Preset collections
│   └── favorites-*.collection
├── prefs/                # Application preferences
├── plugin-states/        # Saved plugin states
├── index/                # Browser search index
└── view-settings/        # UI state per project
```

### Plugin Locations

**User Plugins:**
```
~/Library/Audio/Plug-Ins/
├── VST3/                 # User VST3 plugins
├── VST/                  # User VST2 plugins (legacy)
└── CLAP/                 # User CLAP plugins
```

**System Plugins:**
```
/Library/Audio/Plug-Ins/
├── VST3/                 # System-wide VST3 plugins
├── VST/                  # System-wide VST2 plugins
└── CLAP/                 # System-wide CLAP plugins
```

**Bitwig CLAP Cache:**
```
~/Library/Application Support/Bitwig/CLAP/
```

## File Extensions

| Extension | Description | Location |
|-----------|-------------|----------|
| `.bwproject` | Project file | ~/Documents/Bitwig Studio/Projects/ |
| `.bwtemplate` | Project template | Library/Templates/ |
| `.bwpreset` | Device/plugin preset | Library/Presets/[DeviceName]/ |
| `.bwclip` | Audio or note clip | Packages or user library |
| `.bwcurve` | Curve file (envelopes, LFOs) | Packages/Essentials/Curves/ |
| `.bwimpulse` | Convolution impulse response | Packages/Essentials/Impulses/ |
| `.bwwavetable` | Wavetable file | Packages or user library |
| `.bwextension` | Controller extension | ~/Documents/Bitwig Studio/Extensions/ |
| `.multisample` | Multisample instrument | Packages or sound content locations |
| `.bwdevice` | Device definition | Internal to application |

## Installed Package Structure

Each package under `installed-packages/5.0/[Vendor]/[PackageName]/` contains:

```
[PackageName]/
├── Presets/              # Device presets organized by device
├── Clips/                # Instrument clips with embedded sounds
├── Samples/              # WAV audio samples
├── Multisamples/         # .multisample instruments
├── Impulses/             # Convolution IRs
├── Curves/               # Envelope/LFO shapes
└── Wavetables/           # Wavetable files
```

## Locating Content Programmatically

### Find All Presets
```bash
find "$HOME/Library/Application Support/Bitwig/Bitwig Studio/installed-packages" -name "*.bwpreset"
find "$HOME/Documents/Bitwig Studio/Library" -name "*.bwpreset"
```

### Find All Samples
```bash
find "$HOME/Library/Application Support/Bitwig/Bitwig Studio/installed-packages" -name "*.wav"
find "$HOME/Library/Application Support/Bitwig/Bitwig Studio/installed-packages" -name "*.multisample"
```

### Find All Clips
```bash
find "$HOME/Library/Application Support/Bitwig/Bitwig Studio/installed-packages" -name "*.bwclip"
```

### Find All Impulse Responses
```bash
find "$HOME/Library/Application Support/Bitwig/Bitwig Studio/installed-packages" -name "*.bwimpulse"
```

### Find All Curves
```bash
find "$HOME/Library/Application Support/Bitwig/Bitwig Studio/installed-packages" -name "*.bwcurve"
```

## Package Metadata

Package installation state is tracked in:
```
~/Library/Application Support/Bitwig/Bitwig Studio/installed-packages/5.0/.installed-packages
```

## Project Folder Structure

Each project creates a folder containing:
```
[ProjectName]/
├── [ProjectName].bwproject    # Main project file
├── auto-backups/              # Automatic backups
├── samples/                   # Project-local samples
├── plugin-states/             # Plugin state snapshots
├── recordings/                # Recorded audio
├── bounce/                    # Bounced audio
└── master-recordings/         # Master output recordings
```

## Settings Locations (In Bitwig Preferences)

These settings define additional content paths:

| Setting | Purpose |
|---------|---------|
| **My Library** | User presets and clips location |
| **My Projects** | Default project save location |
| **Sound Content Locations** | Additional sample/preset folders |
| **Music Locations** | Audio file folders for browser |
| **Plug-in Locations** | Plugin scan folders |

## Supported Audio Formats

**Import:** WAV, AIFF, MP3, FLAC, OGG, OPUS

**Multisample:** MULTISAMPLE, SFZ, SF2 (SoundFont 2)

**Wavetable:** WT

**Preset Formats:** BWPRESET, H2P, FXP, FXB, VSTPRESET, CLAP vendor-specific

## Sources

- [Bitwig Studio User Guide](https://downloads.bitwig.com/documentation/5.3/Bitwig%20Studio%20User%20Guide%20English.pdf)
- [Bitwig Browsers Documentation](https://www.bitwig.com/userguide/latest/browsers/)
- [KVR Forum: Location of downloaded packages](https://www.kvraudio.com/forum/viewtopic.php?t=524270)
- [KVR Forum: Clearer explanation of Bitwig Settings Locations](https://www.kvraudio.com/forum/viewtopic.php?t=548272)
