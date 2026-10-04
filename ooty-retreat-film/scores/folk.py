"""Campfire folk, in the manner of Jose Gonzalez: a fingerpicked nylon guitar, a shaker, a hand drum and a
whistled tune. Warm and human, like the bonfire footage. G major.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import score as E
from score import T, BEAT
from common import flute_nv, ch, root, line, hit, ping_map, field_beds, coda_fire, BONGO, SHAKE
from synth import pluck, strum

CYCLE = ['G', 'Em', 'C', 'D']
TUNE = [(0, 74, 1.5), (1.5, 76, 0.5), (2, 79, 2), (4, 78, 1), (5, 76, 1), (6, 74, 2),
        (8, 72, 1.5), (9.5, 74, 0.5), (10, 76, 2), (12, 74, 3), (15, 71, 1)]

def at(bar):
    return CYCLE[bar % 4]

def picking(bar, sym, vel):
    """Travis picking: the thumb alternates root and fifth on the beats, the fingers answer on the offbeats."""
    r = root(sym, 2) + (12 if root(sym, 2) < 43 else 0)
    treble = ch(sym, 4)
    for beat in range(4):
        pluck(r + (7 if beat % 2 else 0), T(bar, beat), 1.2 * BEAT, vel, bright=0.35, pan=-0.1)
        pluck(treble[(beat + 1) % len(treble)], T(bar, beat + 0.5), 0.8 * BEAT, vel * 0.8, bright=0.55, pan=0.1)

def shaker(bar, v):
    for j in range(8):
        hit(SHAKE.format(1 + j % 8), T(bar, j * 0.5), (0.1 if j % 2 else 0.06) * v, 0.3)

def hand_drum(bar, v):
    hit(BONGO.format('LowBongo1'), T(bar), 0.25 * v, -0.2)
    hit(BONGO.format('HighBongo1'), T(bar, 1.5), 0.15 * v, -0.2)
    hit(BONGO.format('LowBongo2'), T(bar, 2.5), 0.2 * v, -0.2)

def main():
    for (bar, beat, _), m in zip(E.MAP_NODES, [79, 83, 86, 74, 81, 88, 79, 83, 91, 86, 81, 93]):
        pluck(m, T(bar, beat), 1.5, 0.35, bright=0.6)
    for b in range(0, 4):
        strum(ch(at(b), 3), T(b), 0.3, dur=3.0)
    for b in range(4, 17):
        picking(b, at(b), 0.5 + 0.1 * (b >= 9))
        if b >= 6:
            shaker(b, 0.8)
        if b >= 11:
            hand_drum(b, 0.8)
    line(flute_nv, 'winds', 5, TUNE, 0.4, atk=0.04)
    line(flute_nv, 'winds', 13, TUNE, 0.45, atk=0.04)
    for b, sym in [(17, 'C'), (18, 'G/B'), (19, 'D')]:         # breath: the guitar alone, slower
        strum(ch(sym, 3), T(b), 0.3, dur=3.0)
        strum(ch(sym, 3), T(b, 2), 0.22, dur=1.6, down=False)
    for b in range(20, 25):
        sym = at(b) if b < 24 else 'D'
        picking(b, sym, 0.65)
        strum(ch(sym, 3), T(b), 0.3, dur=1.5); strum(ch(sym, 3), T(b, 2), 0.25, dur=1.5, down=False)
        shaker(b, 1.0); hand_drum(b, 1.0)
    line(flute_nv, 'winds', 20, TUNE, 0.5, octave=1, atk=0.04)
    line(flute_nv, 'winds', 20, [(o, m - 4, d) for o, m, d in TUNE], 0.35, octave=1, atk=0.04)   # a second voice, a third below
    strum(ch('G', 2) + ch('G', 3), T(25), 0.5, dur=3.2)          # the title: one big open G
    line(flute_nv, 'winds', 25, [(0.5, 86, 3)], 0.4)
    field_beds()

def coda():
    coda_fire()
    pluck(74, T(26) + 0.35, 2.0, 0.35)
    for b, sym in zip(range(27, 31), ['C', 'G', 'C', 'D']):
        picking(b, sym, 0.35)
    line(flute_nv, 'winds', 28, TUNE[:6], 0.3, atk=0.05)
    strum(ch('Cadd9', 3) + [76], T(31), 0.32, dur=5.0, down=True)   # ends open, on the fourth

if __name__ == '__main__':
    E.render(sys.argv[1] if len(sys.argv) > 1 else 'folk.wav', [main], [coda], rt=2.0, calm=True)
