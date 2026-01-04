# Plugin Performance Guides

Expert documentation for professional-sounding performances with third-party instruments.

---

## Electric Sunburst Deluxe (Native Instruments)

### Overview
Session guitarist instrument with recorded patterns, strumming, picking, and melody capabilities. Kontakt-based.

### Key Ranges
- **C1-D#1**: Melody articulation keyswitches (yellow)
  - C1: Open
  - C#1: Muted
  - D1: Flageolet
  - D#1: Tremolo
- **E1-G1**: Pattern keyswitches (red) - 3 pattern slots in melody instrument
- **G#1-B1**: Endings and slides (purple/green)
  - G#1: Long ending / Slide up
  - A1: Slide down
  - Bb1: Mute strings / Hit body / Slap
  - B1: Pickup slide / Slide modifier (hold while playing)
- **C2 and up**: Playable range (~4 octaves)

### MIDI Controls
| Control | Function |
|---------|----------|
| Pitch Wheel | Impact slider (pattern dynamics) / Pitch bend (melody mode) |
| Mod Wheel | Vibrato intensity |
| Velocity > 110 | Triggers slide transitions on chord changes |

### Playing Techniques

#### Hammer-Ons and Pull-Offs (Automatic)
- **Trigger condition**: Overlapping (legato) notes
- **Velocity**: Following note must be significantly softer than previous
- **Interval limit**: Up to a minor third (3 semitones)
- **Example MIDI**: Note 1 at velocity 100, Note 2 (overlapping, +2 semitones) at velocity 60

#### Slides
- Hold B1 while playing melody notes to add slides
- Velocity > 110 on chord changes triggers slide transitions in patterns
- G#1/A1 for ending slides

#### Pattern vs Melody Mode
- Default: Melody mode
- Hold E1-G1 to temporarily switch to pattern mode
- Release pattern keyswitch to return to melody mode

### Recommended Note Device Presets (Before)
| Preset | Purpose |
|--------|---------|
| **Arpeggiator - Simple Up** | Create arpeggiated patterns from held chords |
| **Multi-Note - Octave Up** | Double melody lines an octave up |
| **Note Velocity - Humanize** | Add velocity variation for realism |
| **Note Length - Legato** | Ensure notes overlap for hammer-on triggers |

### Recommended Audio Effect Presets (After)
| Preset | Purpose |
|--------|---------|
| **Amp - Clean Guitar** | Warm clean tone |
| **Amp - AC Crunch 1** | Light overdrive for rock |
| **Delay - Slapback** | Rockabilly/country feel |
| **Reverb - Small Room** | Intimate acoustic sound |
| **Compressor - Soft Compression** | Even out dynamics |
| **EQ - Guitar Presence** | Cut mud, add clarity |

---

## M-Tron Pro IV (GForce)

### Overview
Virtual Mellotron with authentic tape-based sounds. Dual-layer architecture with extensive sound library.

### Key Ranges
- **Standard**: 35 notes (G2-F5)
- **Extended**: 49 notes (available via Layer Range sliders)
- Extended notes use digital pitch shifting

### MIDI Controls
| Control | Function |
|---------|----------|
| Mod Wheel (CC1) | Brake effect (when Brake button enabled) - slows tape for pitch drop |
| Pitch Bend | Pitch bend per layer (0-12 semitones configurable) |
| Velocity | Controls volume (Velocity to Amp) and filter (Velocity to Filter) |

### Layer Controls
- **Layer A (Green)**: Independent controls
- **Layer B (Red)**: Independent controls
- **Both (Blue)**: Linked controls
- Layer Range sliders set keyboard split/range per layer

### Playing Techniques

#### Tape Brake Effect
- Enable Brake button in top bar
- Mod wheel controls flywheel pressure
- Subtle movements = pitch fluctuation
- Full down = extreme tape stop effect

#### Velocity Dynamics
- Velocity to Amp: 0% = static volume, 100% = full dynamic range
- Velocity to Filter: Controls brightness based on how hard you play

#### Reverse Playback
- Available per layer
- Note: Takes time for reversed sound to become audible
- Plan ahead in arrangements

### Recommended Note Device Presets (Before)
| Preset | Purpose |
|--------|---------|
| **Note Velocity - Compress** | Even out Mellotron's natural volume variations |
| **Note Length - Sustain** | Extend notes for pad-like sounds |
| **Arpeggiator - Chord** | Trigger full chords from single notes |

### Recommended Audio Effect Presets (After)
| Preset | Purpose |
|--------|---------|
| **Compressor - Soft Compression** | Tame tape volume fluctuations |
| **EQ - Tape Warmth** | Enhance vintage character |
| **Reverb - Large Hall** | Classic Mellotron sound |
| **Chorus - Vintage** | Add movement, emulate tape wow |
| **Delay - Analog** | Warm delays complement tape sounds |
| **Saturator - Tape** | Add harmonic richness |

### Authentic Performance Tips
- Rule 1: Preserve note attack (Mellotron has no volume envelope)
- Rule 2: Preserve note duration (8 second tape limit historically)
- Let notes breathe - don't over-sustain

---

## MOJO 2 (Vir2 Instruments)

### Overview
Big band horn section with multiple eras, articulations, and ensemble control. Kontakt-based.

### Key Ranges
- **RED/ORANGE keys**: Articulation triggers
  - Orange triggers: Can end sustains with release articulation (velocity > 110)
- **Light GREEN**: Natural legato mode toggle
- **GREEN**: Force keynoise overlay
- **BLUE**: Articulation samples (playable range)
- **PURPLE**: Release sample triggers (sustain mode only)
  - Order: Normal, Doits, Falls, Trills, Shakes

### MIDI Controls
| Control | Function |
|---------|----------|
| Mod Wheel | Pitch bend (configurable range) |
| Velocity | Dynamics (or switchable to CC control) |
| Customizable CCs | Various parameters assignable |

### Articulations
- **Sustains**: With legato, vibrato (real/simulated), attack accent
- **Staccato**: Short punchy notes
- **Stabs**: With legato bypass timing
- **Bend Down**: Pitch bend articulation
- **Octave Run Down/Up**: Chromatic runs
- **Doits**: Upward pitch bend at end
- **Rise to Hit**: Approach from below
- **Shakes**: Vibrato/shake effect
- **Trills**: Alternating notes
- **Falls**: Downward pitch at end

### Playing Techniques

#### Legato Mode
- Seamless transitions between notes
- Three control modes:
  - **Fixed**: Constant transition time
  - **MIDI CC**: CC controls transition length
  - **Velocity**: Hard = fast transition, soft = slow

#### Natural Legato Mode
- Toggle with light GREEN key (or latch)
- Omits "target" sample after transition
- More realistic connected lines

#### Release Articulations (Sustains only)
- Hold PURPLE key while releasing sustain to change release type
- Velocity > 110 on orange triggers finishes sustain with that articulation

#### Era Selection
- **Modern**: Full, current sound
- **Retro (60s-70s)**: Classic warmth
- **Vintage 1 (40s-50s)**: Big band tone
- **Vintage 2 (20s-30s)**: Early jazz character

### Recommended Note Device Presets (Before)
| Preset | Purpose |
|--------|---------|
| **Note Velocity - Humanize** | Natural dynamic variation |
| **Arpeggiator - Up** | Brass runs from chords |
| **Multi-Note - Octave** | Section doubling |
| **Note Echo - Rhythmic** | Brass stabs with rhythm |

### Recommended Audio Effect Presets (After)
| Preset | Purpose |
|--------|---------|
| **Compressor - Soft Compression** | Control brass dynamics |
| **EQ - Brass Presence** | Cut honk, add brilliance |
| **Reverb - Medium Hall** | Concert hall ambience |
| **Delay - Analog** | Warm echo for big band |
| **Saturator - Warm** | Add body without harshness |
| **Transient Shaper** | Enhance or soften attacks |

---

## Quick Reference: MIDI Techniques Summary

### Hammer-Ons/Pull-Offs (Electric Sunburst)
```
Note 1: C3, vel=100, start=0, end=480
Note 2: D3, vel=60, start=400, end=880  (overlapping, softer = hammer-on)
```

### Slide Transitions (Electric Sunburst)
```
Chord change with velocity > 110 triggers slide
```

### Tape Brake (M-Tron)
```
CC1 (Mod Wheel): 0=normal, 127=full brake/stop
```

### Natural Legato Toggle (MOJO 2)
```
Keyswitch: Light GREEN key (check Key Mapping for exact note)
```

### Release Articulation (MOJO 2)
```
While holding sustain, press PURPLE key with vel > 110 to end with that articulation
```

---

## Bitwig Integration Notes

### Loading These Instruments
1. Save plugin with desired preset as Bitwig preset
2. `bwctl index` to add to database
3. `bwctl search "preset name"` to find
4. `bwctl insert -s "preset name" -t N` to load on track N

### Note Device Chain Order
Bitwig chain: **Note Devices** -> **Instrument** -> **Audio Effects**

Add note devices BEFORE the instrument using:
```bash
bwctl device add "Arpeggiator"
bwctl device swap previous  # Move before instrument
```

### Recommended Chain Examples

#### Electric Sunburst Deluxe
```
Note Velocity (Humanize) -> Electric Sunburst -> Amp (Clean Guitar) -> Compressor -> Reverb
```

#### M-Tron Pro IV
```
Note Length (Sustain) -> M-Tron Pro IV -> Compressor -> Chorus -> Reverb -> EQ
```

#### MOJO 2
```
Note Velocity (Humanize) -> MOJO 2 -> Compressor -> EQ -> Reverb
```
