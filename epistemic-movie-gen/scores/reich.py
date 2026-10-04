"""In the manner of Steve Reich / Philip Glass: interlocking marimbas, clarinets holding the harmony, layers joining
one at a time. Curious and bright, carried by pulse rather than drama. E major, leaning lydian.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import score as E
from score import T, BEAT, note
from common import marimba, clar, flute, glock, ch, root, chord, line, ping_map, field_beds, coda_fire

CYCLE = ['Eadd9', 'C#m7', 'Amaj7', 'Bsus4']                 # two bars each
SEQ = [0, 2, 5, 2, 1, 2, 5, 3]                              # indices into the chord's tones, one per eighth

def at(bar):
    return CYCLE[(bar // 2) % 4]

def tones(sym):
    return ch(sym, 4) + ch(sym, 5)

def pattern(bar, vel, shift=0.0, octave=0, halve=False):
    """Eight quavers of chord tones. A second marimba plays the same line one quaver late: the interlock."""
    ts = tones(at(bar))
    for j, idx in enumerate(SEQ[::2] if halve else SEQ):
        beat = (j * (1.0 if halve else 0.5) + shift) % 4
        note(marimba, 'harp', ts[idx % len(ts)] + 12 * octave, T(bar, beat), 0.6, vel * (1.0 if j % 4 == 0 else 0.8), rel=0.8)

def main():
    ping_map(marimba, 'harp', [88, 92, 83, 95, 90, 86, 88, 93, 97, 90, 95, 100], vel=0.3)
    for b in range(0, 4):
        pattern(b, 0.28, halve=True)
    for b in range(4, 17):
        pattern(b, 0.34 + 0.01 * (b - 4))
        note(marimba, 'harp', root(at(b), 2), T(b), 1.0, 0.3)
        if b >= 9:
            pattern(b, 0.3, shift=0.5, octave=1)             # the second marimba arrives with the questions
        if b >= 6 and b % 2 == 0:
            chord(clar, 'winds', b, ch(at(b), 3)[1:3], bars=2, vel=0.35, atk=0.8, rel=1.5)
    for b in range(17, 20):                                   # breath: only the clarinets and one soft marimba
        pattern(b, 0.24, halve=True)
        chord(clar, 'winds', b, ch(at(b), 3)[1:3], vel=0.3, atk=1.0)
    for b in range(20, 25):
        pattern(b, 0.42); pattern(b, 0.36, shift=0.5, octave=1)
        note(marimba, 'harp', root(at(b), 2), T(b), 1.0, 0.36); note(marimba, 'harp', root(at(b), 2), T(b, 2), 1.0, 0.3)
        if b % 2 == 0:
            chord(clar, 'winds', b, ch(at(b), 3)[1:3], bars=2, vel=0.4, atk=0.6)
    line(flute, 'winds', 20, [(0, 76, 4), (4, 78, 4), (8, 80, 6), (14, 78, 2), (16, 76, 4)], 0.42, atk=0.3)
    for i in range(12):                                        # the title: the patterns stop, one bright chord rings out
        note(marimba, 'harp', tones('Eadd9')[i % 5], T(25, i * 0.125), 0.5, 0.32 - 0.015 * i, rel=1.2)
    chord(clar, 'winds', 25, ch('Eadd9', 3)[1:4], vel=0.4, atk=0.3)
    for m in (88, 92, 95):
        note(glock, 'harp', m, T(25, 0.5), 2.0, 0.25)
    field_beds()

def coda():
    coda_fire()
    note(marimba, 'harp', 76, T(26) + 0.35, 1.0, 0.3)
    for b in (28, 29):
        pattern(b, 0.26, halve=True)
    chord(clar, 'winds', 27, ch('C#m7', 3)[1:3], bars=2, vel=0.28, atk=1.0)
    chord(clar, 'winds', 30, ch('Bsus4', 3)[1:3], vel=0.28, atk=1.0)
    for i in range(16):                                        # ends open, on the fourth: a soft marimba roll on A
        note(marimba, 'harp', tones('Amaj7')[i % 4], T(31, i * 0.2), 0.6, 0.26 - 0.012 * i, rel=1.5)
    chord(clar, 'winds', 31, ch('Amaj7', 3)[1:3], bars=1.6, vel=0.28, atk=1.0, rel=2.5)

if __name__ == '__main__':
    E.render(sys.argv[1] if len(sys.argv) > 1 else 'reich.wav', [main], [coda], rt=2.2, calm=True)
