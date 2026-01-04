# DrivenByMoss OSC Protocol Learnings

## Volume/Pan/Parameter Control

### Touch Events Required
For reliable fader/parameter changes, you MUST send touch events:
```
/track/{N}/volume/touched 1    # Start touch
/track/{N}/volume {value}       # Set value (0-128)
/track/{N}/volume/touched 0    # End touch
```

Without touch events, value changes may be ignored due to "take-over" protection.

### Value Ranges
- DrivenByMoss uses **0-128** range by default (can be configured to 1024 or 16384)
- Linear value 0.0-1.0 maps to OSC value 0-128
- Formula: `osc_value = int(linear_value * 128)`

### dB to Linear Conversion
```python
linear = 10 ** (dB / 20)
```

| dB | Linear | OSC Value |
|----|--------|-----------|
| 0dB | 1.00 | 128 |
| -2dB | 0.79 | 101 |
| -3dB | 0.71 | 90 |
| -6dB | 0.50 | 64 |
| -8dB | 0.40 | 51 |
| -10dB | 0.32 | 41 |
| -12dB | 0.25 | 32 |
| -14dB | 0.20 | 25 |

### Pan Values
- Pan uses 0-128 range where 64 = center
- Formula: `pan_value = int((value + 1.0) * 64)` where value is -1.0 to 1.0

## Device Operations

### Adding Devices
- `/device/add "Device Name"` - Adds device at END of chain
- Note devices (Arpeggiator, Multi-Note) must be BEFORE instruments
- Use `/device/swap/previous` to move device left (requires DrivenByMoss extension)

### Loading Presets
- `/device/file "/path/to/preset.bwpreset"` - Inserts preset on current track
- Loading a preset also adds the device if not present

### Device Navigation
- `/device/+` - Select next device
- `/device/-` - Select previous device
- `/device/swap/previous` - Move current device left
- `/device/swap/next` - Move current device right

## Track Bank

### Flat Mode (previous)
- DrivenByMoss track window configured to 200 tracks
- `/track/1` through `/track/200` are directly addressable
- No need to scroll bank for typical projects
- Group tracks count as tracks in the numbering

### Hierarchical Mode (current)
- Group tracks appear at top level
- Track 1 = group track itself (can insert devices on it!)
- Track 2+ = children inside the group (after entering)
- `/track/{N}/enter 1` - enter a group to see its children
- `/track/parent` - exit group to parent level
- Selecting a group twice toggles its expanded/collapsed state
- Use `--debug` flag to see OSC messages: `bwctl --debug track list`

## Transport
- `/play 1` - Start playback
- `/stop 1` - Stop playback
- `/record 1` - Toggle recording
- `/tempo/raw {bpm}` - Set tempo (20-666)
- `/repeat -1` - Toggle loop

## Actions
- `/action/invoke "action_id"` - Invoke any Bitwig action by ID
- Example: `/action/invoke "group_selected_tracks"`

## Master Track
- `/device/master/add "Device Name"` - Add device to master
- `/device/master/file "/path/to/preset.bwpreset"` - Add preset to master

## Common Issues

### Volume not changing
1. Ensure touch events are sent before/after value
2. Verify track number is correct (group tracks shift numbering)
3. Check OSC connection (test with transport commands first)

### Group track volume not changing
**CONFIRMED LIMITATION**: Group/bus track volumes DO NOT respond to OSC commands.
- Neither `/track/{N}/volume` nor `/track/selected/volume` work for groups
- Touch events don't help
- **WORKAROUND**: Set group track volumes manually in Bitwig
- This appears to be a Bitwig Controller API limitation for group tracks

### Device added at wrong position
1. Note devices always add at end of chain
2. Must manually move or use swap commands
3. Use browser workflow for insert-before: `/browser/device/before`

### Track numbering with groups
When group tracks exist, they take up track slots:
- Track 1: First track
- Track 2: Could be a group track
- Tracks inside groups may not be directly addressable

## Files Modified

### DrivenByMoss Extensions
- `DeviceModule.java`: Added `/device/swap/previous` and `/device/swap/next`
- `DeviceModule.java`: Added `/device/master/add` and `/device/master/file`
- `ActionModule.java`: Added `/action/invoke` for arbitrary action invocation

### bwctl Bridge
- `bridge.py`: Added touch events to `set_track_volume()`, `set_track_pan()`, `set_device_param()`
- `bridge.py`: Added `swap_device_with_previous()`, `swap_device_with_next()`
- `bridge.py`: Added `select_next_device()`, `select_previous_device()`
