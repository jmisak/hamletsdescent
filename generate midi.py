import mido

# Create a new MIDI file and track
mid = mido.MidiFile()
track = mido.MidiTrack()
mid.tracks.append(track)

# Set tempo (BPM = 120, adjust as needed)
track.append(mido.MetaMessage('set_tempo', tempo=mido.bpm2tempo(120)))

# Instruments for a 16-bit, medieval, ominous theme
# Channel 1: Harpsichord (ID 6) for melody
# Channel 2: Church Organ (ID 19) for atmosphere
# Channel 3: Strings (ID 48) for depth

# Program changes (set instruments)
track.append(mido.Message('program_change', channel=0, program=6))  # Harpsichord
track.append(mido.Message('program_change', channel=1, program=19)) # Church Organ
track.append(mido.Message('program_change', channel=2, program=48)) # Strings

# Melody (Harpsichord) - Inspired by Castlevania style
melody_notes = [
    (60, 480), (62, 240), (64, 240), (65, 480), # C, D, E, F
    (64, 240), (62, 240), (60, 480), (55, 480), # E, D, C, G
    (57, 240), (59, 240), (60, 480), (62, 480), # A, B, C, D
    (64, 240), (65, 240), (67, 480), (65, 480)  # E, F, G, F
]

# Add melody
for note, duration in melody_notes:
    track.append(mido.Message('note_on', channel=0, note=note, velocity=80, time=0))
    track.append(mido.Message('note_off', channel=0, note=note, velocity=80, time=duration))

# Background Organ (slow chords)
chords = [(48, 52, 55, 960), (50, 53, 57, 960), (52, 55, 59, 960)]  # C minor, D minor, E minor

for chord in chords:
    for note in chord[:-1]:
        track.append(mido.Message('note_on', channel=1, note=note, velocity=60, time=0))
    track.append(mido.Message('note_off', channel=1, note=chord[0], velocity=60, time=chord[-1]))

# Save MIDI file
midi_file_path = "hamlet_opening_theme.mid"
mid.save(midi_file_path)

print(f"MIDI file saved: {midi_file_path}")
