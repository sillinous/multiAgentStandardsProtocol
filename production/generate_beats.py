#!/usr/bin/env python3
"""
SUPERSTANDARD BEAT GENERATOR
Generate actual MIDI files and audio for the Rap Anthology!

Requirements:
    pip install midiutil pydub numpy

Optional for audio generation:
    pip install pyo soundfile librosa
"""

from midiutil import MIDIFile
import random

def create_superstandard_anthem():
    """Generate MIDI for Track 01: SuperStandard Anthem"""
    track = 0
    channel = 0
    tempo = 140  # BPM

    # Create MIDI file with 4 tracks
    midi = MIDIFile(4)

    # Track 0: Kick Drum
    midi.addTrackName(track, 0, "Kick")
    midi.addTempo(track, 0, tempo)

    # Track 1: 808 Bass
    midi.addTrackName(1, 0, "808 Bass")
    midi.addTempo(1, 0, tempo)

    # Track 2: Hi-Hats
    midi.addTrackName(2, 0, "Hi-Hats")
    midi.addTempo(2, 0, tempo)

    # Track 3: Synth Pad
    midi.addTrackName(3, 0, "Synth Pad")
    midi.addTempo(3, 0, tempo)

    # C Minor scale notes
    c_minor_scale = [60, 62, 63, 65, 67, 68, 70, 72]  # C D Eb F G Ab Bb C

    # Pattern length in beats
    pattern_length = 16
    num_patterns = 8  # 8 bars

    # KICK DRUM PATTERN (GM Drum: Bass Drum 1 = note 36)
    kick_note = 36
    for bar in range(num_patterns):
        time = bar * 4
        # Kick on 1 and 3, with syncopation
        midi.addNote(0, 9, kick_note, time, 0.5, 100)      # Beat 1
        midi.addNote(0, 9, kick_note, time + 2, 0.5, 100)  # Beat 3
        midi.addNote(0, 9, kick_note, time + 3.5, 0.25, 80)  # Syncopation

    # 808 BASS PATTERN
    bass_notes = [48, 48, 51, 51, 53, 53, 55, 55]  # C C Eb Eb F F G G
    for bar in range(num_patterns):
        note = bass_notes[bar % len(bass_notes)]
        time = bar * 4
        midi.addNote(1, 0, note, time, 3.5, 90)  # Long bass notes

    # HI-HAT PATTERN (Closed Hi-Hat = note 42)
    hihat_note = 42
    for bar in range(num_patterns):
        for beat in range(16):  # 16th notes
            time = bar * 4 + beat * 0.25
            velocity = 100 if beat % 4 == 0 else 60  # Accent on quarter notes
            midi.addNote(2, 9, hihat_note, time, 0.2, velocity)

    # SYNTH PAD CHORD PROGRESSION
    # Cm - Ab - Eb - Bb
    chord_progression = [
        [60, 63, 67],  # C minor (C Eb G)
        [68, 60, 63],  # Ab major (Ab C Eb)
        [63, 67, 70],  # Eb major (Eb G Bb)
        [70, 62, 65],  # Bb major (Bb D F)
    ]

    for bar in range(num_patterns):
        chord = chord_progression[bar % len(chord_progression)]
        time = bar * 4
        for note in chord:
            midi.addNote(3, 0, note, time, 4, 70)

    # Save MIDI file
    with open("01_SuperStandard_Anthem.mid", "wb") as f:
        midi.writeFile(f)

    print("✅ Created: 01_SuperStandard_Anthem.mid")
    return "01_SuperStandard_Anthem.mid"


def create_protocol_flow():
    """Generate MIDI for Track 02: Protocol Flow"""
    track = 0
    tempo = 128  # BPM

    midi = MIDIFile(3)

    midi.addTrackName(0, 0, "Drums")
    midi.addTempo(0, 0, tempo)

    midi.addTrackName(1, 0, "Liquid Bass")
    midi.addTempo(1, 0, tempo)

    midi.addTrackName(2, 0, "Lead")
    midi.addTempo(2, 0, tempo)

    # A Minor pentatonic scale
    a_minor_pent = [57, 60, 62, 64, 67, 69]  # A C D E G A

    num_bars = 16

    # Drums - cleaner pattern
    kick = 36
    snare = 38
    hihat = 42

    for bar in range(num_bars):
        time = bar * 4
        # Four-on-floor kick
        for beat in range(4):
            midi.addNote(0, 9, kick, time + beat, 0.5, 100)
        # Snare on 2 and 4
        midi.addNote(0, 9, snare, time + 1, 0.5, 95)
        midi.addNote(0, 9, snare, time + 3, 0.5, 95)
        # Fast hi-hats
        for beat in range(16):
            midi.addNote(0, 9, hihat, time + beat * 0.25, 0.2, 70)

    # Liquid bass - flowing melody
    for bar in range(num_bars):
        time = bar * 4
        # Melodic bassline using pentatonic scale
        pattern = [0, 2, 3, 1, 4, 2, 1, 0]
        note_idx = pattern[bar % len(pattern)]
        bass_note = a_minor_pent[note_idx] - 12  # One octave down
        midi.addNote(1, 0, bass_note, time, 3.5, 80)

    # Lead melody
    for bar in range(num_bars):
        time = bar * 4
        if bar % 4 == 0:  # Play melody every 4 bars
            melody = [0, 2, 3, 5, 3, 2, 1, 0]
            for i, note_idx in enumerate(melody):
                note = a_minor_pent[note_idx]
                midi.addNote(2, 0, note, time + i * 0.5, 0.4, 85)

    with open("02_Protocol_Flow.mid", "wb") as f:
        midi.writeFile(f)

    print("✅ Created: 02_Protocol_Flow.mid")
    return "02_Protocol_Flow.mid"


def create_consciousness_rising():
    """Generate MIDI for Track 05: Consciousness Rising (LEAD SINGLE)"""
    track = 0
    tempo = 75  # Slow, ethereal

    midi = MIDIFile(4)

    midi.addTrackName(0, 0, "Ambient Pad")
    midi.addTempo(0, 0, tempo)

    midi.addTrackName(1, 0, "Minimal Drums")
    midi.addTempo(1, 0, tempo)

    midi.addTrackName(2, 0, "Evolving Synth")
    midi.addTempo(2, 0, tempo)

    midi.addTrackName(3, 0, "Bass")
    midi.addTempo(3, 0, tempo)

    # F# Minor scale
    f_sharp_minor = [54, 56, 57, 59, 61, 62, 64, 66]

    num_bars = 24  # Long track

    # Ambient pad - sustained chords
    for bar in range(num_bars):
        time = bar * 4
        # F#m chord
        for note in [54, 57, 61]:  # F# A C#
            midi.addNote(0, 0, note + 12, time, 8, 50)  # Long, quiet notes

    # Minimal drums (start at bar 8)
    kick = 36
    for bar in range(8, num_bars):
        time = bar * 4
        midi.addNote(1, 9, kick, time, 0.5, 70)
        midi.addNote(1, 9, kick, time + 2.5, 0.5, 60)

    # Evolving synth melody
    for bar in range(num_bars):
        if bar >= 4:  # Start later
            time = bar * 4
            # Random evolution
            note_idx = (bar * 3) % len(f_sharp_minor)
            note = f_sharp_minor[note_idx]
            duration = 2.0 + random.random() * 2.0
            midi.addNote(2, 0, note + 12, time, duration, 65)

    # Deep bass
    for bar in range(num_bars):
        if bar >= 8:
            time = bar * 4
            bass_note = 54 - 12  # F# one octave down
            midi.addNote(3, 0, bass_note, time, 3.5, 75)

    with open("05_Consciousness_Rising.mid", "wb") as f:
        midi.writeFile(f)

    print("✅ Created: 05_Consciousness_Rising.mid")
    return "05_Consciousness_Rising.mid"


def create_blockchain_bars():
    """Generate MIDI for Track 06: Blockchain Bars"""
    track = 0
    tempo = 150  # Fast trap

    midi = MIDIFile(3)

    midi.addTrackName(0, 0, "Trap Drums")
    midi.addTempo(0, 0, tempo)

    midi.addTrackName(1, 0, "808 Bass")
    midi.addTempo(1, 0, tempo)

    midi.addTrackName(2, 0, "Hi-Hats")
    midi.addTempo(2, 0, tempo)

    num_bars = 16

    # Trap kick pattern
    kick = 36
    snare = 38

    for bar in range(num_bars):
        time = bar * 4
        # Kick pattern
        midi.addNote(0, 9, kick, time, 0.5, 100)
        midi.addNote(0, 9, kick, time + 1, 0.5, 100)
        midi.addNote(0, 9, kick, time + 2.5, 0.5, 90)

        # Snare on 2 and 4
        midi.addNote(0, 9, snare, time + 1, 0.5, 95)
        midi.addNote(0, 9, snare, time + 3, 0.5, 95)

    # Heavy 808 bass
    b_minor_notes = [47, 50, 54]  # B D F#
    for bar in range(num_bars):
        time = bar * 4
        note = b_minor_notes[bar % len(b_minor_notes)]
        midi.addNote(1, 0, note - 12, time, 3.5, 95)  # Very low

    # Trap hi-hats with rolls
    hihat_closed = 42
    hihat_open = 46

    for bar in range(num_bars):
        time = bar * 4
        # 16th note pattern
        for beat in range(16):
            t = time + beat * 0.25
            vel = 90 if beat % 4 == 0 else 60
            midi.addNote(2, 9, hihat_closed, t, 0.15, vel)

        # Hi-hat roll at end of every other bar
        if bar % 2 == 1:
            for i in range(8):
                t = time + 3.5 + i * 0.0625  # 32nd notes
                midi.addNote(2, 9, hihat_closed, t, 0.05, 80)

    with open("06_Blockchain_Bars.mid", "wb") as f:
        midi.writeFile(f)

    print("✅ Created: 06_Blockchain_Bars.mid")
    return "06_Blockchain_Bars.mid"


def create_we_did_that():
    """Generate MIDI for Track 08: We Did That (Victory Lap)"""
    track = 0
    tempo = 160  # Fast and energetic

    midi = MIDIFile(4)

    midi.addTrackName(0, 0, "Drums")
    midi.addTempo(0, 0, tempo)

    midi.addTrackName(1, 0, "Bass")
    midi.addTempo(1, 0, tempo)

    midi.addTrackName(2, 0, "Brass")
    midi.addTempo(2, 0, tempo)

    midi.addTrackName(3, 0, "Chords")
    midi.addTempo(3, 0, tempo)

    num_bars = 16

    # Energetic drum pattern
    kick = 36
    snare = 38
    hihat = 42

    for bar in range(num_bars):
        time = bar * 4
        # Energetic kick pattern
        for beat in [0, 0.75, 1.5, 2, 3]:
            midi.addNote(0, 9, kick, time + beat, 0.5, 100)

        # Snare
        midi.addNote(0, 9, snare, time + 1, 0.5, 100)
        midi.addNote(0, 9, snare, time + 3, 0.5, 100)

        # Fast hi-hats
        for beat in range(16):
            midi.addNote(0, 9, hihat, time + beat * 0.25, 0.15, 85)

    # C Major bass
    c_major_notes = [48, 50, 52, 55]  # C D E G
    for bar in range(num_bars):
        time = bar * 4
        note = c_major_notes[bar % len(c_major_notes)]
        midi.addNote(1, 0, note, time, 3.5, 90)

    # Brass stabs (victory horns!)
    for bar in range(num_bars):
        if bar % 2 == 0:  # Every other bar
            time = bar * 4
            # C major chord in brass
            for note in [60, 64, 67]:  # C E G
                midi.addNote(2, 0, note + 12, time, 0.5, 100)
                midi.addNote(2, 0, note + 12, time + 2, 0.5, 100)

    # Power chords
    for bar in range(num_bars):
        time = bar * 4
        chord_root = c_major_notes[bar % len(c_major_notes)]
        for note in [chord_root, chord_root + 7]:  # Root and fifth
            midi.addNote(3, 0, note + 12, time, 4, 75)

    with open("08_We_Did_That.mid", "wb") as f:
        midi.writeFile(f)

    print("✅ Created: 08_We_Did_That.mid")
    return "08_We_Did_That.mid"


def main():
    """Generate all MIDI files"""
    print("🎵 SUPERSTANDARD RAP ANTHOLOGY - BEAT GENERATOR 🎵")
    print("=" * 60)
    print("\nGenerating MIDI files for all tracks...\n")

    tracks = []

    try:
        tracks.append(create_superstandard_anthem())
        tracks.append(create_protocol_flow())
        tracks.append(create_consciousness_rising())
        tracks.append(create_blockchain_bars())
        tracks.append(create_we_did_that())

        print("\n" + "=" * 60)
        print("🎉 SUCCESS! Generated MIDI files:")
        for track in tracks:
            print(f"   ✅ {track}")

        print("\n📝 NEXT STEPS:")
        print("   1. Open these MIDI files in any DAW (FL Studio, Ableton, etc.)")
        print("   2. Assign instruments to each track")
        print("   3. Add effects and mixing")
        print("   4. Export as WAV/MP3")
        print("\n   OR use free online converters:")
        print("   - https://www.zamzar.com/convert/mid-to-mp3/")
        print("   - https://online-audio-converter.com/")

        print("\n🔥 Let's make these beats REAL! 🔥")

    except Exception as e:
        print(f"❌ Error: {e}")
        print("Make sure you have installed: pip install midiutil")


if __name__ == "__main__":
    main()
