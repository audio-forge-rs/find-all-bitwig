#!/usr/bin/env python3
"""
MIDWEST MERIDIAN - Bitwig Production Setup
Producer: Rick Rubin approach
Artist: Son Volt style

This script sets up all 8 tracks with proper instrument and effect chains.
Run with: python scripts/midwest_meridian_production.py

Philosophy:
- Strip it down to the essence
- Let the song breathe
- The room is an instrument
- Dynamics over loudness
- Honesty over polish
"""

import time
import sys
sys.path.insert(0, '/Users/bedwards/find-all-bitwig/src')

from bwctl.osc.bridge import BitwigOSCBridge

# Preset paths (found via database search)
PRESETS = {
    # Instruments
    'old_nylon': '/Users/bedwards/Library/Application Support/Bitwig/Bitwig Studio/installed-packages/5.0/Bitwig/Essentials/Presets/Poly Grid/Old Nylon.bwpreset',
    'ambient_strings': '/Users/bedwards/Library/Application Support/Bitwig/Bitwig Studio/installed-packages/5.0/Bitwig/Essentials/Presets/Phase-4/Ambient Strings.bwpreset',
    'fm_violin': '/Users/bedwards/Library/Application Support/Bitwig/Bitwig Studio/installed-packages/5.0/Bitwig/Essentials/Presets/FM-4/FM Violin.bwpreset',
    'jazz_guitar': '/Users/bedwards/Library/Application Support/Bitwig/Bitwig Studio/installed-packages/5.0/Bitwig/Essentials/Presets/Poly Grid/Jazz Guitar.bwpreset',
    'acoustic_bass': '/Users/bedwards/Library/Application Support/Bitwig/Bitwig Studio/installed-packages/5.0/Bitwig/Essentials/Presets/Poly Grid/Acoustic Bass.bwpreset',
    'bob_kick': '/Users/bedwards/Library/Application Support/Bitwig/Bitwig Studio/installed-packages/5.0/Bitwig/Essentials/Presets/E-Kick/BOB Kick.bwpreset',
    'dark_snare': '/Users/bedwards/Library/Application Support/Bitwig/Bitwig Studio/installed-packages/5.0/Bitwig/Essentials/Presets/E-Snare/Dark Snare.bwpreset',

    # Effects
    'room_one': '/Users/bedwards/Library/Application Support/Bitwig/Bitwig Studio/installed-packages/5.0/Bitwig/Essentials/Presets/Reverb/Room One.bwpreset',
    'room_two': '/Users/bedwards/Library/Application Support/Bitwig/Bitwig Studio/installed-packages/5.0/Bitwig/Essentials/Presets/Reverb/Room Two.bwpreset',
    'clean_amp': '/Users/bedwards/Library/Application Support/Bitwig/Bitwig Studio/installed-packages/5.0/Bitwig/Essentials/Presets/Amp/Clean Guitar.bwpreset',
    'guitar_comp': '/Users/bedwards/Library/Application Support/Bitwig/Bitwig Studio/installed-packages/5.0/Bitwig/Essentials/Presets/Compressor+/Guitar Compressor.bwpreset',
    'soft_comp': '/Users/bedwards/Library/Application Support/Bitwig/Bitwig Studio/installed-packages/5.0/Bitwig/Essentials/Presets/Compressor/Soft Compression.bwpreset',
    'mono_chorus': '/Users/bedwards/Library/Application Support/Bitwig/Bitwig Studio/installed-packages/5.0/Bitwig/Essentials/Presets/Chorus+/Mono K-Chorus.bwpreset',
    'low_cut_eq': '/Users/bedwards/Library/Application Support/Bitwig/Bitwig Studio/installed-packages/5.0/Bitwig/Essentials/Presets/EQ-5/Low Cut EQ.bwpreset',
}

# Volume levels in dB -> linear (0-1)
# Formula: linear = 10^(dB/20)
VOLUMES = {
    'acoustic_guitar': 0.50,  # -6dB
    'pedal_steel': 0.32,      # -10dB
    'fiddle': 0.32,           # -10dB
    'electric_guitar': 0.40,  # -8dB
    'upright_bass': 0.50,     # -6dB
    'kick': 0.40,             # -8dB
    'snare': 0.32,            # -10dB
    'vocal': 0.71,            # -3dB
}

# Pan values (-1 = full left, 0 = center, 1 = full right)
PANS = {
    'acoustic_guitar': -0.15,  # 15% left
    'pedal_steel': 0.25,       # 25% right
    'fiddle': -0.20,           # 20% left
    'electric_guitar': 0.20,   # 20% right
    'upright_bass': 0.00,      # center
    'kick': 0.00,              # center
    'snare': 0.00,             # center
    'vocal': 0.00,             # center
}


def wait(seconds: float = 0.5):
    """Wait between operations for Bitwig to process."""
    time.sleep(seconds)


def setup_track(bridge: BitwigOSCBridge, track_num: int, name: str,
                instrument_preset: str, effect_presets: list[str],
                volume: float, pan: float):
    """Set up a single track with instrument and effects.

    Order matters:
    1. Add instrument preset (includes the instrument device)
    2. Add effect presets in order
    """
    print(f"\n{'='*60}")
    print(f"Track {track_num}: {name}")
    print(f"{'='*60}")

    # Select the track
    bridge.select_track(track_num)
    wait(0.3)

    # Add instrument preset
    print(f"  + Instrument: {instrument_preset.split('/')[-1]}")
    bridge.insert_preset(PRESETS[instrument_preset])
    wait(0.5)

    # Add effect presets
    for effect in effect_presets:
        print(f"  + Effect: {effect.split('/')[-1]}")
        bridge.insert_preset(PRESETS[effect])
        wait(0.3)

    # Set volume and pan
    bridge.set_track_volume(track_num, volume)
    wait(0.2)
    bridge.set_track_pan(track_num, pan)
    wait(0.2)

    print(f"  Volume: {volume:.2f} | Pan: {pan:+.2f}")


def setup_audio_track(bridge: BitwigOSCBridge, track_num: int, name: str,
                      effect_presets: list[str], volume: float, pan: float):
    """Set up an audio track (no instrument, just effects)."""
    print(f"\n{'='*60}")
    print(f"Track {track_num}: {name} (Audio)")
    print(f"{'='*60}")

    # Select the track
    bridge.select_track(track_num)
    wait(0.3)

    # Add effect presets
    for effect in effect_presets:
        print(f"  + Effect: {effect.split('/')[-1]}")
        bridge.insert_preset(PRESETS[effect])
        wait(0.3)

    # Set volume and pan
    bridge.set_track_volume(track_num, volume)
    wait(0.2)
    bridge.set_track_pan(track_num, pan)
    wait(0.2)

    print(f"  Volume: {volume:.2f} | Pan: {pan:+.2f}")


def setup_master(bridge: BitwigOSCBridge):
    """Set up the master track with gentle processing."""
    print(f"\n{'='*60}")
    print("MASTER TRACK")
    print("{'='*60}")

    # Add EQ-5 (default, for gentle high-shelf air)
    bridge.add_master_device("EQ-5")
    wait(0.3)
    print("  + EQ-5 (gentle high-shelf air)")

    # Add Peak Limiter
    bridge.add_master_device("Peak Limiter")
    wait(0.3)
    print("  + Peak Limiter (-1dB ceiling)")

    print("\n  Philosophy: Warm, not loud. Preserve dynamics.")


def main():
    print("""
╔══════════════════════════════════════════════════════════════╗
║            MIDWEST MERIDIAN - BITWIG PRODUCTION              ║
║                   Producer: Rick Rubin                       ║
║                   Artist: Son Volt Style                     ║
╚══════════════════════════════════════════════════════════════╝

Creating 8 tracks. Ensure Bitwig has a clean project with 8 empty
instrument tracks already created.

Tempo should be set to 95 BPM.
""")

    bridge = BitwigOSCBridge()

    # Set tempo
    print("Setting tempo to 95 BPM...")
    bridge.set_tempo(95.0)
    wait(0.5)

    # Track 1: Acoustic Guitar
    setup_track(bridge, 1, "Acoustic Guitar",
                instrument_preset='old_nylon',
                effect_presets=['room_one'],
                volume=VOLUMES['acoustic_guitar'],
                pan=PANS['acoustic_guitar'])

    # Track 2: Pedal Steel
    setup_track(bridge, 2, "Pedal Steel",
                instrument_preset='ambient_strings',
                effect_presets=['mono_chorus', 'room_two', 'low_cut_eq'],
                volume=VOLUMES['pedal_steel'],
                pan=PANS['pedal_steel'])

    # Track 3: Fiddle
    setup_track(bridge, 3, "Fiddle",
                instrument_preset='fm_violin',
                effect_presets=['room_one'],
                volume=VOLUMES['fiddle'],
                pan=PANS['fiddle'])

    # Track 4: Electric Guitar
    setup_track(bridge, 4, "Electric Guitar",
                instrument_preset='jazz_guitar',
                effect_presets=['clean_amp', 'room_two'],
                volume=VOLUMES['electric_guitar'],
                pan=PANS['electric_guitar'])

    # Track 5: Upright Bass
    setup_track(bridge, 5, "Upright Bass",
                instrument_preset='acoustic_bass',
                effect_presets=['soft_comp'],
                volume=VOLUMES['upright_bass'],
                pan=PANS['upright_bass'])

    # Track 6: Kick
    setup_track(bridge, 6, "Kick",
                instrument_preset='bob_kick',
                effect_presets=[],  # Keep it simple
                volume=VOLUMES['kick'],
                pan=PANS['kick'])

    # Track 7: Snare
    setup_track(bridge, 7, "Snare",
                instrument_preset='dark_snare',
                effect_presets=['room_one'],
                volume=VOLUMES['snare'],
                pan=PANS['snare'])

    # Track 8: Vocal (audio track placeholder)
    # For now, just set up effects chain - user will record audio
    setup_audio_track(bridge, 8, "Vocal",
                      effect_presets=['low_cut_eq', 'soft_comp', 'room_one'],
                      volume=VOLUMES['vocal'],
                      pan=PANS['vocal'])

    # Master track
    setup_master(bridge)

    print("""
╔══════════════════════════════════════════════════════════════╗
║                    PRODUCTION COMPLETE                        ║
╚══════════════════════════════════════════════════════════════╝

MANUAL STEPS REQUIRED:

1. GROUP TRACKS (OSC cannot set group volumes):
   - Select Tracks 1-4 → Group → "Instruments Bus" → Volume: -3dB
   - Select Tracks 5-7 → Group → "Rhythm Bus" → Volume: -4dB

2. ADJUST DRUM CHARACTER:
   - Track 6 (Kick): Soften attack for jazz feel
   - Track 7 (Snare): Add brush character manually if needed

3. IMPORT MIDI FILES:
   From: ~/concept-albums/midwest-meridian/01-midwest-meridian/midi/
   - acoustic-guitar.mid → Track 1
   - pedal-steel.mid → Track 2
   - fiddle.mid → Track 3
   - electric-guitar.mid → Track 4
   - upright-bass.mid → Track 5
   - drum-kick.mid → Track 6
   - drum-snare.mid → Track 7
   - vocal.mid → Track 8

4. REMEMBER:
   "Let the song breathe. Less is more."
   - Rick Rubin
""")


if __name__ == "__main__":
    main()
