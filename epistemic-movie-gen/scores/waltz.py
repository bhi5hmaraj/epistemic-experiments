"""A little waltz, in the spirit of Giacchino's 'Married Life': piano, clarinet and pizzicato, a sprinkle of glockenspiel.
Warm and a bit whimsical. F major.

The waltz lives on the film's grid: each 4-beat bar holds two waltz bars of three quick beats (triplet crotchets),
so every cut still lands.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import score as E
from score import T, BEAT, note, piano, vln, vla, vc
from common import clar, flute, glock, vc_pz, vla_pz, ch, root, chord, field_beds, coda_fire

Q = 2 / 3                                                  # one waltz beat, in film beats
PROG = ['F', 'Dm', 'Gm7', 'C7', 'F', 'Am', 'Bb', 'C7']     # one chord per film bar (two waltz bars)
# the tune over two film bars: (waltz beat index 0-11, midi, waltz beats)
TUNE_A = [(0, 72, 2), (2, 74, 1), (3, 76, 3), (6, 77, 2), (8, 76, 1), (9, 72, 3)]
TUNE_B = [(0, 70, 2), (2, 72, 1), (3, 74, 2), (5, 72, 1), (6, 70, 3), (9, 67, 3)]

def oompah(bar, sym, vel):
    """Bass on one, chord on two and three - twice per film bar."""
    tones = [m for m in ch(sym, 3) if m >= 53][:3] or ch(sym, 4)[:3]
    for half in (0, 3):
        note(piano, 'piano', root(sym, 2), T(bar, (half + 0) * Q), Q * BEAT * 0.9, vel, rel=0.5)
        for k in (1, 2):
            for m in tones:
                note(piano, 'piano', m, T(bar, (half + k) * Q), Q * BEAT * 0.6, vel * 0.6, rel=0.3)

def pizz(bar, sym, vel):
    for half in (0, 3):
        note(vc_pz, 'strings', root(sym, 2), T(bar, half * Q), 0.4, vel)
        note(vla_pz, 'strings', ch(sym, 4)[1], T(bar, (half + 1) * Q), 0.3, vel * 0.7)

def sing(inst, bus, bar0, phrase, vel, octave=0):
    for idx, m, beats in phrase:
        note(inst, bus, m + 12 * octave, T(bar0, idx * Q), beats * Q * BEAT, vel, atk=0.04, rel=0.4)

def main():
    for (bar, beat, _), m in zip(E.MAP_NODES, [84, 88, 91, 79, 86, 93, 84, 88, 96, 91, 86, 98]):
        note(glock, 'harp', m, T(bar, beat), 1.5, 0.22)
    for b, sym in zip(range(0, 4), ['F', 'Dm', 'Gm7', 'C7']):
        for i, m in enumerate(ch(sym, 3)):
            note(piano, 'piano', m, T(b, i * 0.5), 2.5, 0.24, rel=2.0)
    for b in range(4, 17):
        sym = PROG[(b - 4) % 8]
        oompah(b, sym, 0.3 + 0.05 * (b >= 9))
        if b >= 9:
            pizz(b, sym, 0.4)
        if b >= 13:
            chord(vla, 'strings', b, ch(sym, 3)[1:3], vel=0.22, atk=0.8, gain=0.7)
    for b0, phrase in [(4, TUNE_A), (6, TUNE_B), (9, TUNE_A), (11, TUNE_B), (13, TUNE_A), (15, TUNE_B)]:
        sing(clar, 'winds', b0, phrase, 0.42)
    for b0 in (13, 15):                                                      # the flute joins, an octave up
        sing(flute, 'winds', b0, TUNE_A if b0 == 13 else TUNE_B, 0.3, octave=1)
    for b, sym in [(17, 'Bb'), (18, 'F'), (19, 'C7')]:                       # breath: the piano alone, slower
        for i, m in enumerate(ch(sym, 3) + [ch(sym, 4)[1]]):
            note(piano, 'piano', m, T(b, i * 0.75), 2.0, 0.26, rel=1.5)
    for b in range(20, 25):
        sym = PROG[(b - 20) % 8] if b < 24 else 'C7'
        oompah(b, sym, 0.36); pizz(b, sym, 0.45)
        chord(vc, 'strings', b, [root(sym, 2)], vel=0.35, atk=0.5)
        note(glock, 'harp', ch(sym, 5)[0] + 12, T(b), 1.5, 0.2)
    for b0, phrase in [(20, TUNE_A), (22, TUNE_B)]:
        sing(vln, 'strings', b0, phrase, 0.5, octave=1)                       # the strings take the waltz
        sing(clar, 'winds', b0, phrase, 0.35)
    for m in ch('F', 2) + ch('F', 4):                                        # the title: a warm F, lightly rolled
        note(piano, 'piano', m, T(25) + 0.05 * (m % 5), 3.0, 0.4, rel=2.0)
    chord(vln, 'strings', 25, ch('F', 5), vel=0.4, atk=0.6, rel=1.5)
    for m in (84, 88, 91):
        note(glock, 'harp', m, T(25, 0.5), 2.0, 0.25)
    field_beds()

def coda():
    coda_fire()
    note(clar, 'winds', 72, T(26) + 0.35, 2.5, 0.3, atk=0.1, rel=1.0)
    for b, sym in zip(range(27, 31), ['Bb', 'F', 'Gm7', 'C7']):
        oompah(b, sym, 0.24)
    sing(clar, 'winds', 28, TUNE_A, 0.32)
    for m in ch('Bbmaj7', 2) + [77, 81]:                                      # ends open, on the fourth
        note(piano, 'piano', m, T(31), 5.0, 0.26, rel=3.0)
    note(glock, 'harp', 93, T(31, 1), 2.0, 0.2)

if __name__ == '__main__':
    E.render(sys.argv[1] if len(sys.argv) > 1 else 'waltz.wav', [main], [coda], rt=2.0, calm=True)
