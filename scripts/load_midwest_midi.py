#!/usr/bin/env python3
"""
Load Midwest Meridian MIDI files into Bitwig tracks.

Inserts each MIDI file into clip slot 1 of its corresponding track.
"""

import time
import sys
sys.path.insert(0, '/Users/bedwards/find-all-bitwig/src')

from bwctl.osc.bridge import BitwigOSCBridge

MIDI_DIR = '/Users/bedwards/concept-albums/midwest-meridian/01-midwest-meridian/midi'

# Track number -> MIDI file mapping
MIDI_FILES = {
    1: 'acoustic-guitar.mid',
    2: 'pedal-steel.mid',
    3: 'fiddle.mid',
    4: 'electric-guitar.mid',
    5: 'upright-bass.mid',
    6: 'drum-kick.mid',
    7: 'drum-snare.mid',
    8: 'vocal.mid',
}

def main():
    print("""
╔══════════════════════════════════════════════════════════════╗
║         LOADING MIDI INTO BITWIG - MIDWEST MERIDIAN          ║
╚══════════════════════════════════════════════════════════════╝
""")

    bridge = BitwigOSCBridge()

    for track_num, midi_file in MIDI_FILES.items():
        midi_path = f"{MIDI_DIR}/{midi_file}"
        print(f"Track {track_num}: {midi_file}")

        # Insert MIDI file into clip slot 1
        bridge.insert_clip_file(track_num, 1, midi_path)
        time.sleep(0.5)

    print("""
╔══════════════════════════════════════════════════════════════╗
║                    MIDI LOADED                                ║
╚══════════════════════════════════════════════════════════════╝

All 8 MIDI files inserted into clip slot 1 of each track.

Next steps:
1. Select all clips and drag to arranger (or use "Consolidate")
2. Create group tracks manually (Instruments Bus, Rhythm Bus)
3. Listen and adjust levels

"Let the song breathe."
""")


if __name__ == "__main__":
    main()
