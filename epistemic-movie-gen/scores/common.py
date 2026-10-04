"""Shared by every alternative score: the instruments, and the sounds that are locked to the picture."""
import glob, json, os
import librosa
import score as E
from score import T, BAR, BEAT, SR, S, note, sustain, MAP_NODES, Inst, load

ORGAN_MAP = {E.S + k[len('samples/'):]: v for k, v in json.load(open('data/organ_map.json')).items()}
organ_loud = Inst('Keys/Organ/Loud/Rode_Man3*.wav', pan=0.0, gain=0.5, pitch=ORGAN_MAP)
organ_soft = Inst('Keys/Organ/Quiet/NT5_Man3*.wav', pan=0.0, gain=0.6, pitch=ORGAN_MAP)
pedal = Inst('Keys/Organ/Loud/Rode_Pedal*.wav', pan=0.0, gain=0.55, pitch=ORGAN_MAP)
pedal_soft = Inst('Keys/Organ/Quiet/NT5_Pedal*.wav', pan=0.0, gain=0.6, pitch=ORGAN_MAP)
solo_vln = Inst('Strings/Solo Violin/Arco Vib/*.wav', 0, 0.1, 0.55)
vln_pz = Inst('Strings/Violin Section/Pizz/*.wav', 1, -0.3, 0.45)
vla_pz = Inst('Strings/Viola Section/pizz/*.wav', 1, 0.1, 0.45)
vc_pz = Inst('Strings/Cello Section/pizzT/*.wav', 1, 0.3, 0.5)
flute = Inst('Woodwinds/Flute/susvib/*.wav', 1, -0.15, 0.5)
oboe = Inst('Woodwinds/Oboe/Vib/*.wav', 1, 0.15, 0.45)
clar = Inst('Woodwinds/Clarinet/susLong/*.wav', 1, 0.2, 0.45)
GLOCK_MAP = {g: librosa.note_to_midi(os.path.basename(g)[len('glock_medium_'):-4]) + 12
             for g in glob.glob(S + 'Percussion/Glock/glock_medium_*.wav')}
glock = Inst('Percussion/Glock/glock_medium_*.wav', pan=-0.2, gain=0.3, pitch=GLOCK_MAP)

def ch(symbol, octave=3):
    """Chord symbol -> midi notes, root in the given octave (pychord does the theory)."""
    from pychord import Chord
    return [int(librosa.note_to_midi(n)) for n in Chord(symbol).components_with_pitch(root_pitch=octave)]

def root(symbol, octave=2):
    return ch(symbol, octave)[0]

def hit(path, t, gain, pan=0.0):
    E.mix.add('perc', load(S + path), t, gain, pan)

def ping_map(inst, bus, notes, vel=0.22, gain=0.8, rel=2.5):
    """One soft note per node as the opening world map fills in (film.py draws them on these beats)."""
    for (bar, beat, _), m in zip(MAP_NODES, notes):
        note(inst, bus, m, T(bar, beat), 1.5, vel, rel=rel, gain=gain)

def field_beds():
    """Rain under the breath, the hillside clip's sound, the bonfire under the night."""
    E.rain(T(17) - 0.2, T(20) + 1.0, 0.07)
    E.field('clips/IMG_1296.wav', T(19) - 0.2, 3.6, 1.2, seed=2)
    E.field('clips/IMG_1289.wav', T(20) - 0.3, 7.5, 0.25, seed=1)

def coda_fire():
    E.field('clips/IMG_1289.wav', T(26), 6.0, 0.07, seed=3)

def chord(inst, bus, bar, notes, bars=1, vel=0.5, atk=0.3, rel=1.5, gain=1.0):
    sustain(inst, bus, bar, notes, bars=bars, vel=vel, atk=atk, rel=rel, gain=gain)

def line(inst, bus, bar0, phrase, vel, octave=0, gain=1.0, atk=0.06, rel=0.5, legato=1.0):
    """phrase: (beat offset from bar0, midi, beats)."""
    for off, m, beats in phrase:
        note(inst, bus, m + 12 * octave, T(bar0, off), beats * BEAT * legato, vel, atk=atk, rel=rel, gain=gain)

marimba = Inst('Percussion/Marimba/*.wav', 1, -0.2, 0.55)
flute_nv = Inst('Woodwinds/Flute/susNV/*.wav', 1, -0.1, 0.45)       # no vibrato: closest thing to a whistle
BONGO = 'VSCO 1 Percussion/drums/other/Bongos/{}.wav'
SHAKE = "VSCO 1 Percussion/varWood/Camo's Shaker/shake{}.wav"
FRAME_DRUM = 'VSCO 1 Percussion/drums/other/ethnic/giant/hand/EthnicLargeHand_hit_{}.wav'

def grace(inst, bus, m, t, dur, vel, up=2, key=None, **kw):
    """A folk ornament: a quick flick from the next note up in the key (or `up` semitones) just before the main note."""
    flick = next(p for p in range(m + 1, m + 4) if p % 12 in key) if key else m + up
    note(inst, bus, flick, t - 0.07, 0.06, vel * 0.6, rel=0.05)
    note(inst, bus, m, t, dur, vel, **kw)

TRIP = 1 / 3                                             # one triplet quaver, in beats: 12/8 on the film's 4/4 grid

def third_below(m, key_pcs):
    """The note two scale steps under m in the given key (a diatonic third), for a harmony voice."""
    below = [p for p in range(m - 5, m) if p % 12 in key_pcs]
    return below[-2] if len(below) >= 2 else m - 3

G_MAJOR = {7, 9, 11, 0, 2, 4, 6}
D_MIXOLYDIAN = {2, 4, 6, 7, 9, 11, 0}                    # D major with the Celtic C natural
