#!/usr/bin/env python3
"""
Set mix levels and panning for Midwest Meridian.

Track layout with group buses:
- Track 1: Instruments Bus (group)
- Track 2: Acoustic Guitar
- Track 3: Pedal Steel
- Track 4: Fiddle
- Track 5: Electric Guitar
- Track 6: Rhythm Bus (group)
- Track 7: Upright Bass
- Track 8: Kick
- Track 9: Snare
- Track 10: Vocal
"""

import time
import sys
sys.path.insert(0, '/Users/bedwards/find-all-bitwig/src')

from bwctl.osc.bridge import BitwigOSCBridge


# dB to linear: linear = 10^(dB/20)
# -3dB = 0.71, -4dB = 0.63, -6dB = 0.50, -8dB = 0.40, -10dB = 0.32

# Group tracks - OSC cannot set these (manual adjustment required)
GROUP_TRACKS = {1, 6}

MIX_SETTINGS = {
    # Track: (volume_linear, pan)
    1: (0.71, 0.00),   # Instruments Bus: -3dB, center [GROUP - MANUAL]
    2: (0.50, -0.15),  # Acoustic Guitar: -6dB, 15% left
    3: (0.32, 0.25),   # Pedal Steel: -10dB, 25% right
    4: (0.32, -0.20),  # Fiddle: -10dB, 20% left
    5: (0.40, 0.20),   # Electric Guitar: -8dB, 20% right
    6: (0.63, 0.00),   # Rhythm Bus: -4dB, center [GROUP - MANUAL]
    7: (0.50, 0.00),   # Upright Bass: -6dB, center
    8: (0.40, 0.00),   # Kick: -8dB, center
    9: (0.32, 0.00),   # Snare: -10dB, center
    10: (0.71, 0.00),  # Vocal: -3dB, center
}

TRACK_NAMES = {
    1: "Instruments Bus",
    2: "Acoustic Guitar",
    3: "Pedal Steel",
    4: "Fiddle",
    5: "Electric Guitar",
    6: "Rhythm Bus",
    7: "Upright Bass",
    8: "Kick",
    9: "Snare",
    10: "Vocal",
}


def linear_to_db(linear: float) -> float:
    """Convert linear volume to dB."""
    import math
    if linear <= 0:
        return float('-inf')
    return 20 * math.log10(linear)


def main():
    print("""
+--------------------------------------------------------------+
|         MIDWEST MERIDIAN - SETTING MIX LEVELS                |
+--------------------------------------------------------------+
""")

    bridge = BitwigOSCBridge()

    for track_num, (volume, pan) in MIX_SETTINGS.items():
        name = TRACK_NAMES[track_num]
        db = linear_to_db(volume)
        pan_str = "center" if pan == 0 else f"{abs(pan)*100:.0f}% {'left' if pan < 0 else 'right'}"

        # Skip group tracks - OSC cannot set their volumes
        if track_num in GROUP_TRACKS:
            print(f"Track {track_num:2d}: {name:20s} | {db:+.0f}dB | {pan_str} [SKIP - set manually]")
            continue

        print(f"Track {track_num:2d}: {name:20s} | {db:+.0f}dB | {pan_str}")

        # Set volume
        bridge.set_track_volume(track_num, volume)
        time.sleep(0.2)

        # Set pan
        bridge.set_track_pan(track_num, pan)
        time.sleep(0.2)

    print("""
+--------------------------------------------------------------+
|                    MIX LEVELS SET                            |
+--------------------------------------------------------------+

"When you listen back, close your eyes.
If you don't feel something, the mix isn't done."
                                        - Rick Rubin
""")


if __name__ == "__main__":
    main()
