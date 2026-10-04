"""A fireside air: a solo fiddle playing a slow, ornamented tune over a fingerpicked guitar and a low cello drone.
Two players close up in a small warm room. G major.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import score as E
from score import T, BEAT, note, vc, vla
from common import solo_vln, flute_nv, ch, root, chord, grace, field_beds, coda_fire, third_below, G_MAJOR
from synth import pluck, strum

PROG = ['G', 'C/G', 'G', 'D/F#', 'Em', 'C', 'G/D', 'D']
# the air: long, singing notes; (beat, midi, beats)
AIR = [(0, 67, 1.5), (1.5, 71, 0.5), (2, 74, 2), (4, 72, 1), (5, 71, 1), (6, 69, 2),
       (8, 71, 1.5), (9.5, 74, 0.5), (10, 79, 2), (12, 78, 1), (13, 76, 1), (14, 74, 2),
       (16, 76, 1.5), (17.5, 74, 0.5), (18, 71, 2), (20, 72, 1), (21, 74, 1), (22, 76, 2),
       (24, 74, 1.5), (25.5, 71, 0.5), (26, 69, 1), (27, 66, 1), (28, 67, 4)]

def picking(bar, sym, vel):
    """Slow fingerpicking: bass on 1 and 3, the fingers walking the chord in between."""
    bass = root(sym.split('/')[-1] if '/' in sym else sym, 2)
    bass += 12 if bass < 40 else 0
    top = ch(sym.split('/')[0], 3)
    fifth = root(sym.split('/')[0], 2) + 7                             # the chord's own fifth, not the bass note's
    fifth += 12 if fifth < bass else 0
    for beat, m, v in [(0, bass, 1.0), (0.5, top[1], 0.7), (1, top[2], 0.75), (1.5, top[1] + 12, 0.65),
                       (2, fifth, 0.9), (2.5, top[2], 0.7), (3, top[1] + 12, 0.7), (3.5, top[2], 0.6)]:
        pluck(m, T(bar, beat), 1.4 * BEAT, vel * v, bright=0.4, pan=0.15)

def air(bar0, vel, octave=0, harmony=False):
    for i, (off, m, beats) in enumerate(AIR):
        target = m + 12 * octave
        if beats >= 2 and i % 2 == 0:
            grace(solo_vln, 'strings', target, T(bar0, off), beats * BEAT, vel, key=G_MAJOR, atk=0.08, rel=0.6)
        else:
            note(solo_vln, 'strings', target, T(bar0, off), beats * BEAT, vel, atk=0.08, rel=0.6)
        if harmony:
            note(flute_nv, 'winds', third_below(target, G_MAJOR), T(bar0, off), beats * BEAT, vel * 0.6, atk=0.1, rel=0.6)

def main():
    for (bar, beat, _), m in zip(E.MAP_NODES, [79, 83, 86, 74, 81, 88, 79, 83, 91, 86, 81, 93]):
        pluck(m, T(bar, beat), 1.5, 0.3, bright=0.6)
    note(vc, 'strings', 43, T(-1), 5 * E.BAR, 0.22, atk=3.0, rel=3.0)
    for b, sym in zip(range(0, 4), ['G', 'C/G', 'G', 'D']):
        strum(ch(sym.split('/')[0], 3), T(b), 0.25, dur=3.0)
    for b in range(4, 17):
        sym = PROG[(b - 4) % 8]
        picking(b, sym, 0.45 + 0.05 * (b >= 9))
        if b >= 9:
            chord(vc, 'strings', b, [root(sym.split('/')[-1] if '/' in sym else sym, 2)], vel=0.3, atk=0.8, gain=0.8)
    air(4, 0.42)
    air(12, 0.46)
    for b, sym in [(17, 'C'), (18, 'G'), (19, 'D')]:                  # breath: the guitar alone, strummed slowly
        strum(ch(sym, 3), T(b), 0.25, dur=3.0)
    for b in range(20, 25):
        sym = PROG[(b - 20) % 8] if b < 24 else 'D'
        picking(b, sym, 0.55)
        chord(vc, 'strings', b, [root(sym.split('/')[-1] if '/' in sym else sym, 2)], vel=0.4, atk=0.5)
        chord(vla, 'strings', b, ch(sym.split('/')[0], 3)[1:], vel=0.25, atk=1.0, gain=0.7)
    air(20, 0.5, harmony=True)                                          # a second voice joins, a third below
    strum(ch('G', 2) + ch('G', 3), T(25), 0.4, dur=3.2)                 # the title: one warm open G
    note(solo_vln, 'strings', 79, T(25, 0.5), 3.0, 0.4, atk=0.3, rel=1.5)
    field_beds()

def coda():
    coda_fire()
    grace(solo_vln, 'strings', 74, T(26) + 0.35, 2.5, 0.3, key=G_MAJOR, atk=0.1, rel=1.0)
    for b, sym in zip(range(27, 31), ['C', 'G', 'C', 'D']):
        picking(b, sym, 0.35)
    for o, m, d in AIR[:6]:
        note(solo_vln, 'strings', m, T(28, o), d * BEAT, 0.3, atk=0.1, rel=0.8)
    strum(ch('Cadd9', 3) + [76], T(31), 0.3, dur=5.0)                  # ends open, on the fourth
    note(solo_vln, 'strings', 76, T(31, 1), 5.0, 0.24, atk=0.8, rel=2.5)

if __name__ == '__main__':
    E.render(sys.argv[1] if len(sys.argv) > 1 else 'fireside.wav', [main], [coda], rt=1.6, calm=True)
