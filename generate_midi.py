import mido

###############################################################################
# GLOBAL SETTINGS & HELPER FUNCTIONS
###############################################################################
def set_bpm(track, bpm):
    track.append(mido.MetaMessage('set_tempo', tempo=mido.bpm2tempo(bpm)))

TICKS_PER_BEAT = 480

# Create a Type 1 MIDI file with three tracks:
#   - music_track: our layered rock/orchestral parts (saw lead, strings, guitar, bass, choir, synth brass)
#   - drum_track: percussion
#   - piano_track: additional piano counter–melody and arpeggios
mid = mido.MidiFile(type=1)
music_track = mido.MidiTrack()
drum_track = mido.MidiTrack()
piano_track = mido.MidiTrack()
mid.tracks.extend([music_track, drum_track, piano_track])

def note_on(channel, note, velocity, time=0):
    return mido.Message('note_on', channel=channel, note=note, velocity=velocity, time=time)

def note_off(channel, note, velocity, time=0):
    return mido.Message('note_off', channel=channel, note=note, velocity=velocity, time=time)

def program_change(track, channel, program):
    track.append(mido.Message('program_change', channel=channel, program=program))

def add_tempo_change(track, bpm):
    track.append(mido.MetaMessage('set_tempo', tempo=mido.bpm2tempo(bpm)))

###############################################################################
# INSTRUMENT SETUP
###############################################################################
# music_track channels:
#   0: Saw Lead
#   1: Strings
#   2: Distortion Guitar
#   3: Electric Bass
#   4: Choir
#   5: Synth Brass
program_change(music_track, 0, 81)  # Saw Lead (Lead 2 – sawtooth)
program_change(music_track, 1, 48)  # Strings
program_change(music_track, 2, 30)  # Distortion Guitar
program_change(music_track, 3, 33)  # Electric Bass
program_change(music_track, 4, 52)  # Choir Aahs
program_change(music_track, 5, 62)  # Synth Brass

# piano_track: channel 6 – Acoustic Grand Piano for counter melodies & arpeggios
program_change(piano_track, 6, 0)

# drum_track: Drums on channel 9
program_change(drum_track, 9, 0)

###############################################################################
# SECTION 1: PRELUDE – ARPEGGIO & BUILD–UP (80 BPM)
###############################################################################
# A soft, arpeggiated introduction with gentle string support.
prelude_measures = 4
PRELUDE_TEMPO = 80
MEASURE_PRELUDE = 4 * TICKS_PER_BEAT

add_tempo_change(music_track, PRELUDE_TEMPO)
add_tempo_change(drum_track, PRELUDE_TEMPO)
add_tempo_change(piano_track, PRELUDE_TEMPO)

# Chord progression in A minor for a dramatic mood
prelude_progression = [
    [57, 60, 64],  # A minor: A, C, E
    [55, 59, 62],  # G major: G, B, D
    [53, 57, 60],  # F major: F, A, C
    [55, 59, 62],  # G major
]

def add_arpeggio_prelude(piano_track, music_track, chord, measure_length, start_velocity):
    # Arpeggiate the chord over the measure on the piano track.
    note_duration = measure_length // (len(chord) * 2)  # each note played twice
    current_time = 0
    # Ascending then descending arpeggio
    arpeggio_sequence = chord + chord[::-1]
    for note in arpeggio_sequence:
        piano_track.append(note_on(6, note, start_velocity, time=current_time))
        piano_track.append(note_off(6, note, start_velocity, time=note_duration))
        current_time = 0  # subsequent events use 0 since time is in the note_off above

    # Meanwhile, add a soft sustained chord on Strings (channel 1) as background
    for note in chord:
        music_track.append(note_on(1, note, start_velocity - 10))
    music_track.append(note_off(1, chord[0], start_velocity - 10, time=measure_length))
    for note in chord[1:]:
        music_track.append(note_off(1, note, start_velocity - 10, time=0))

for chord in prelude_progression:
    add_arpeggio_prelude(piano_track, music_track, chord, MEASURE_PRELUDE, 50)

###############################################################################
# SECTION 2: DRAMATIC INTRO PROGRESSION (100 BPM)
###############################################################################
# Increase the tempo and layer in sustained chords plus a piano scale run.
add_tempo_change(music_track, 100)
add_tempo_change(drum_track, 100)
add_tempo_change(piano_track, 100)

MEASURE_INTRO = 4 * TICKS_PER_BEAT

intro_progression = [
    [54, 57, 61],  # F# minor
    [50, 54, 57],  # D major
    [47, 50, 54],  # B minor
    [52, 56, 59],  # E major
]

def add_intro_chords(track, chord, measure_length, velocity):
    # Sustain the chord on Strings (1), Distortion Guitar (2), and Choir (4)
    for note in chord:
        track.append(note_on(1, note, velocity))
        track.append(note_on(2, note, velocity + 10))
        track.append(note_on(4, note, velocity))
    track.append(note_off(1, chord[0], velocity, time=measure_length))
    track.append(note_off(2, chord[0], velocity + 10, time=0))
    track.append(note_off(4, chord[0], velocity, time=0))
    for n in chord[1:]:
        track.append(note_off(1, n, velocity, time=0))
        track.append(note_off(2, n, velocity + 10, time=0))
        track.append(note_off(4, n, velocity, time=0))

def add_piano_run(track, chord, measure_length):
    # Create a simple scale run based on the chord tones with a slight variation.
    run = chord + [n + 2 for n in chord]
    note_duration = measure_length // len(run)
    current_time = 0
    for note in run:
        track.append(note_on(6, note, 60, time=current_time))
        track.append(note_off(6, note, 60, time=note_duration))
        current_time = 0

def add_intro_drums(track, measure_length):
    # A dramatic crash and kick at the start of the measure.
    track.append(note_on(9, 49, 100, time=0))  # Crash
    track.append(note_on(9, 36, 100, time=0))  # Kick
    track.append(note_off(9, 36, 100, time=240))
    track.append(note_off(9, 49, 100, time=0))
    # Advance remaining time in the measure.
    track.append(note_off(9, 0, 0, time=measure_length - 240))

# Repeat the progression several times to build dramatic tension.
for _ in range(3):
    for chord in intro_progression:
        add_intro_chords(music_track, chord, MEASURE_INTRO, 60)
        add_piano_run(piano_track, chord, MEASURE_INTRO)
        add_intro_drums(drum_track, MEASURE_INTRO)

###############################################################################
# SECTION 3: MAIN SECTION – INFECTIOUS & SNAPPY GROOVE (160 BPM)
###############################################################################
# In this updated main section the beat is designed to be catchy and danceable.
# A bright, staccato keyboard hook (inspired by "Take on Me") is layered in.

add_tempo_change(music_track, 160)
add_tempo_change(drum_track, 160)
add_tempo_change(piano_track, 160)

MEASURE_MAIN = 4 * TICKS_PER_BEAT

main_progression = [
    [52, 55, 59],   # E minor
    [48, 52, 55],   # C major
    [55, 59, 62],   # G major
    [50, 54, 57],   # D major
]

def add_catchy_measure_music(track, chord, measure_length):
    """
    Break the measure into 8 segments with percussive chord stabs and a driving bass.
    This version uses slightly altered stab positions to keep the groove infectious.
    """
    eighth = measure_length // 8
    chord_stab_positions = [0, 2, 4, 6]
    bass_positions = [0, 4]  # Bass hits on beats 1 and 3.
    for i in range(8):
        delta_time = eighth if i > 0 else 0
        # Advance time with a dummy event.
        track.append(note_off(0, 0, 0, time=delta_time))
        # Bass line (one octave below the chord’s root)
        if i in bass_positions:
            bass_note = chord[0] - 12
            track.append(note_on(3, bass_note, 110))
            track.append(note_off(3, bass_note, 110, time=eighth // 2))
        # Chord stabs on selected beats.
        if i in chord_stab_positions:
            for note_val in chord:
                track.append(note_on(2, note_val, 100))
                track.append(note_on(5, note_val, 90))
            track.append(note_off(2, chord[0], 100, time=eighth // 2))
            for n in chord[1:]:
                track.append(note_off(2, n, 100, time=0))
                track.append(note_off(5, n, 90, time=0))

def add_catchy_measure_drums(track, measure_length):
    """
    A lively drum pattern with crisp hi–hats on every 8th note,
    kick on beats 1 & 3, snare on beats 2 & 4, plus an extra rim click for snap.
    """
    eighth = measure_length // 8
    for i in range(8):
        delta_time = eighth if i > 0 else 0
        track.append(note_off(9, 0, 0, time=delta_time))
        # Hi–hat on every 8th.
        track.append(note_on(9, 42, 75))
        track.append(note_off(9, 42, 75, time=30))
        # Kick on beats 1 and 3.
        if i in [0, 4]:
            track.append(note_on(9, 36, 110))
            track.append(note_off(9, 36, 110, time=30))
        # Snare on beats 2 and 4.
        if i in [2, 6]:
            track.append(note_on(9, 38, 120))
            track.append(note_off(9, 38, 120, time=30))
        # Extra rim click at the end of the measure for added snap.
        if i == 7:
            track.append(note_on(9, 37, 90))
            track.append(note_off(9, 37, 90, time=30))

def add_infectious_keyboard_hook(track, measure_length):
    """
    A bright, staccato keyboard hook on the piano track (channel 6) designed to be
    catchy and memorable—echoing the synth sound of "Take on Me".
    """
    # Define an 8–note hook pattern.
    hook_pattern = [64, 67, 69, 71, 69, 67, 64, 62]
    note_duration = measure_length // len(hook_pattern)
    current_time = 0
    for note in hook_pattern:
        track.append(note_on(6, note, 110, time=current_time))
        track.append(note_off(6, note, 110, time=note_duration))
        current_time = 0

def add_catchy_piano_counter(track, chord, measure_length):
    """
    A rhythmic counter–melody using passing tones. This secondary piano line
    supports the hook and adds to the infectious quality.
    """
    quarter = measure_length // 4
    notes = [chord[0] + 4, chord[1] + 3, chord[2] + 5, chord[0] + 7]
    for note in notes:
        track.append(note_on(6, note, 80, time=0))
        track.append(note_off(6, note, 80, time=quarter // 2))

main_cycles = 4
for _ in range(main_cycles):
    for chord in main_progression:
        add_catchy_measure_music(music_track, chord, MEASURE_MAIN)
        add_catchy_measure_drums(drum_track, MEASURE_MAIN)
        add_infectious_keyboard_hook(piano_track, MEASURE_MAIN)
        # Optionally, add a secondary counter melody.
        add_catchy_piano_counter(piano_track, chord, MEASURE_MAIN)

###############################################################################
# SECTION 4: SOLILOQUY – EXPRESSION & IMPROVISATION (140 BPM)
###############################################################################
# A free–form section where the saw lead and piano trade reflective phrases.
add_tempo_change(music_track, 140)
add_tempo_change(drum_track, 140)
add_tempo_change(piano_track, 140)

MEASURE_SOLILOQUY = 4 * TICKS_PER_BEAT

# Define two contrasting melodic lines for the soliloquy.
soliloquy_lead = [66, 64, 62, 64, 66, 67, 69, 67, 66, 64, 62, 60]
soliloquy_piano = [60, 62, 63, 65, 63, 62, 60, 58, 60, 62, 63, 65]

def add_soliloquy_measure(music_track, piano_track, lead_melody, piano_melody, measure_length, start_idx):
    beat = measure_length // 4
    idx = start_idx
    # Saw Lead soliloquy on music_track (channel 0)
    for i in range(4):
        note = lead_melody[(idx + i) % len(lead_melody)]
        music_track.append(note_on(0, note, 100))
        music_track.append(note_off(0, note, 100, time=beat))
    # Parallel reflective piano line on piano_track (channel 6)
    for i in range(4):
        note = piano_melody[(idx + i) % len(piano_melody)]
        piano_track.append(note_on(6, note, 80))
        piano_track.append(note_off(6, note, 80, time=beat))
    return start_idx + 4

sol_idx = 0
for _ in range(6):  # 6 measures of introspective soliloquy
    sol_idx = add_soliloquy_measure(music_track, piano_track, soliloquy_lead, soliloquy_piano, MEASURE_SOLILOQUY, sol_idx)
    # Add a subtle drum brush using hi–hat on the drum track.
    drum_track.append(note_on(9, 42, 50, time=0))
    drum_track.append(note_off(9, 42, 50, time=MEASURE_SOLILOQUY // 2))
    drum_track.append(note_on(9, 42, 50, time=0))
    drum_track.append(note_off(9, 42, 50, time=MEASURE_SOLILOQUY // 2))

###############################################################################
# SECTION 5: FINALE – BIG FINISH (80 BPM)
###############################################################################
add_tempo_change(music_track, 80)
add_tempo_change(drum_track, 80)
add_tempo_change(piano_track, 80)

final_chord = [52, 55, 59]  # E minor for a somber yet epic resolution
final_hold = 2 * 4 * TICKS_PER_BEAT  # hold for 2 measures

# Strike a bombastic chord across multiple layers:
for n in final_chord:
    music_track.append(note_on(2, n, 120))  # Distortion Guitar
    music_track.append(note_on(5, n, 110))  # Synth Brass
    music_track.append(note_on(1, n, 90))   # Strings
    music_track.append(note_on(4, n, 80))   # Choir
    music_track.append(note_on(0, n, 100))  # Saw Lead
    piano_track.append(note_on(6, n, 100))  # Piano

music_track.append(note_off(2, final_chord[0], 120, time=final_hold))
music_track.append(note_off(5, final_chord[0], 110, time=0))
music_track.append(note_off(1, final_chord[0], 90, time=0))
music_track.append(note_off(4, final_chord[0], 80, time=0))
music_track.append(note_off(0, final_chord[0], 100, time=0))
piano_track.append(note_off(6, final_chord[0], 100, time=0))
for n in final_chord[1:]:
    music_track.append(note_off(2, n, 120, time=0))
    music_track.append(note_off(5, n, 110, time=0))
    music_track.append(note_off(1, n, 90, time=0))
    music_track.append(note_off(4, n, 80, time=0))
    music_track.append(note_off(0, n, 100, time=0))
    piano_track.append(note_off(6, n, 100, time=0))

# Conclude with a final drum explosion.
drum_track.append(note_on(9, 36, 127, time=0))  # Kick
drum_track.append(note_on(9, 38, 127, time=0))  # Snare
drum_track.append(note_on(9, 49, 127, time=0))  # Crash
drum_track.append(note_off(9, 36, 127, time=final_hold))
drum_track.append(note_off(9, 38, 127, time=0))
drum_track.append(note_off(9, 49, 127, time=0))

###############################################################################
# SAVE MIDI FILE
###############################################################################
output_path = "complex_jim_steinman_hamlet.mid"
mid.save(output_path)
print(f"MIDI file saved: {output_path}")
