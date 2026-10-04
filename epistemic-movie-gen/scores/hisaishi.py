"""In the manner of Joe Hisaishi's Ghibli scores: D major, warm and a little whimsical.

A flute melody over pizzicato strings, harp and glockenspiel. Lush strings and horns when the title arrives.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import score as E
from score import T, BEAT, note, piano, vln, vla, vc, cb, horn, harp
from common import flute, oboe, glock, vln_pz, vla_pz, vc_pz, ch, root, chord, line, ping_map, field_beds, coda_fire

CYCLE = ['Dmaj7', 'Bm7', 'Gmaj7', 'A7sus4']
# the melody over one cycle: (beat, midi, beats) - a dotted lilt, a leap of a sixth, then home
TUNE = [(0, 78, 1.5), (1.5, 76, 0.5), (2, 74, 1), (3, 69, 1),
        (4, 71, 1.5), (5.5, 73, 0.5), (6, 74, 1), (7, 78, 1),
        (8, 79, 1.5), (9.5, 78, 0.5), (10, 76, 1), (11, 74, 1),
        (12, 76, 2), (14, 74, 1), (15, 73, 1)]

def at(bar):
    return CYCLE[bar % 4]

def oompah(bar, sym, vel):
    """Cello pizz on the beat, upper pizz chords off it."""
    r = root(sym, 2)
    for beat in (0, 2):
        note(vc_pz, 'strings', r + (0 if beat == 0 else 7), T(bar, beat), 0.4, vel)
    for beat in (1, 3):
        for m in ch(sym, 4)[1:3]:
            note(vla_pz, 'strings', m, T(bar, beat), 0.3, vel * 0.8)

def harp_run(bar, sym, vel, up=True):
    tones = ch(sym, 3) + ch(sym, 4)
    for j, m in enumerate(tones if up else tones[::-1]):
        note(harp, 'harp', m, T(bar, j * 0.25), 1.5, vel, rel=2.0)

def intro():
    ping_map(glock, 'harp', [86, 90, 93, 83, 88, 95, 90, 86, 98, 93, 88, 102], vel=0.3, gain=0.9)
    for b in range(0, 4):
        harp_run(b, at(b), 0.28 + 0.03 * b)
    for t, m in [(T(1, 2), 74), (T(3, 2), 76)]:
        note(piano, 'piano', m, t, 2.0, 0.26, rel=2.5)

def arrival():
    for b in range(4, 9):
        sym = at(b) if b < 8 else 'A7'
        oompah(b, sym, 0.4)
        if b in (4, 6, 8):
            harp_run(b, sym, 0.25)
    line(flute, 'winds', 4, TUNE, 0.5, atk=0.05)

def questions():
    for i, b in enumerate(range(9, 17)):
        ramp = i / 7
        sym = at(b) if b < 16 else 'A7'
        oompah(b, sym, 0.45 + 0.2 * ramp)
        chord(vc, 'strings', b, [root(sym, 2)], vel=0.35 + 0.25 * ramp)
        chord(vla, 'strings', b, ch(sym, 4)[:2], vel=0.3 + 0.25 * ramp, atk=0.6)
        if b >= 13:
            chord(vln, 'strings', b, ch(sym, 5)[1:3], vel=0.3 + 0.3 * ramp, atk=0.6)
            chord(cb, 'strings', b, [root(sym, 1)], vel=0.4 + 0.3 * ramp)
    line(oboe, 'winds', 9, TUNE, 0.5, atk=0.05)
    line(flute, 'winds', 13, TUNE, 0.6, octave=1, atk=0.05)
    harp_run(16, 'A7', 0.45)
    for j in range(8):
        E.timp(T(16, 2 + j * 0.25), 0.2 + 0.03 * j)
    E.riser(T(17), 4.0, 0.5)

def breath():
    """Flute alone in the rain, with the harp."""
    for b, sym in [(17, 'Gmaj7'), (18, 'F#m7'), (19, 'Em7')]:
        for k, m in enumerate(ch(sym, 3)):
            note(harp, 'harp', m, T(b, k), 2.0, 0.35, rel=2.5)
    line(flute, 'winds', 17, [(0, 83, 3), (3, 81, 1), (4, 78, 4), (8, 79, 2), (10, 76, 2)], 0.45, atk=0.1)
    field_beds()

def summit():
    for b in range(20, 24):
        sym = at(b)
        chord(vc, 'strings', b, [root(sym, 2), root(sym, 3)], vel=0.75)
        chord(cb, 'strings', b, [root(sym, 1)], vel=0.75)
        chord(vla, 'strings', b, ch(sym, 4), vel=0.65, atk=0.2)
        chord(horn, 'brass', b, ch(sym, 3)[:3], vel=0.6, atk=0.3)
        harp_run(b, sym, 0.45, up=b % 2 == 0)
        note(glock, 'harp', ch(sym, 5)[0] + 12, T(b), 1.5, 0.3)
        E.timp(T(b), 0.45)
    line(vln, 'strings', 20, TUNE, 0.85, octave=1, gain=1.1, atk=0.08)
    line(flute, 'winds', 20, TUNE, 0.7, octave=1, atk=0.05)
    chord(vln, 'strings', 24, ch('A7', 5), vel=0.8, atk=0.4)
    chord(horn, 'brass', 24, ch('A', 3), vel=0.75, atk=0.4)
    for j in range(8):
        note(harp, 'harp', ch('A7', 4)[j % 4] + 12 * (j // 4), T(24, 2 + j * 0.25), 1.0, 0.5)
    E.riser(T(25), 3.5, 0.9)
    E.boom(T(25), 0.55)                                          # the title: D major, everything warm at once
    for inst, bus, notes in [(vln, 'strings', ch('D', 5) + [86]), (vla, 'strings', ch('D', 4)), (vc, 'strings', [38, 50]),
                             (cb, 'strings', [38]), (horn, 'brass', ch('D', 3)), (flute, 'winds', [90])]:
        chord(inst, bus, 25, notes, vel=0.9, atk=0.05, rel=0.8)
    for m in (86, 90, 93, 98):
        note(glock, 'harp', m, T(25), 2.0, 0.45)

def coda():
    coda_fire()
    note(piano, 'piano', 78, T(26) + 0.35, 2.5, 0.28, rel=2.5)
    for m in ch('G', 3):
        note(piano, 'piano', m, T(27), 3.0, 0.24, rel=2.5)
    line(flute, 'winds', 28, TUNE[:8], 0.4, atk=0.08)
    for b, sym in [(28, 'Gmaj7'), (29, 'A/G'), (30, 'Em7')]:
        for m in ch(sym, 3):
            note(piano, 'piano', m, T(b), E.BAR, 0.22, rel=1.5)
    for m in ch('Gmaj9', 2) + [78]:                               # ends open, on the fourth
        note(piano, 'piano', m, T(31), 5.5, 0.28, rel=3.0)
    for i, m in enumerate([86, 90, 93, 97]):
        note(glock, 'harp', m, T(31) + 0.8 + i * 0.3, 2.0, 0.25)

if __name__ == '__main__':
    E.render(sys.argv[1] if len(sys.argv) > 1 else 'hisaishi.wav', [intro, arrival, questions, breath, summit], [coda], rt=2.6)
