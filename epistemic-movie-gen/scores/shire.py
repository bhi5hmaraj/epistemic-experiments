"""Pastoral, in the spirit of the Shire: a tin-whistle tune in a lilting 12/8 over harp, pizzicato and a soft frame
drum, with a clarinet answering and birds in the trees. D major with a Celtic flattened seventh.

Nothing builds to a climax: the tune just gets more voices, and the strings take it up near the end.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import score as E
from score import T, BEAT, note, vln, vla, vc, harp, horn
from common import (flute_nv, clar, glock, solo_vln, vc_pz, ch, root, chord, line, hit, field_beds, coda_fire,
                    grace, FRAME_DRUM, TRIP, D_MIXOLYDIAN)
from synth import birdsong

PROG = ['D', 'G', 'D', 'A', 'Bm', 'G', 'D', 'A']          # the tune's eight bars
# the tune: (beat, midi, beats), all on the triplet grid. Rises in skips, turns, settles home.
TUNE = [(0, 74, 2 * TRIP), (2 * TRIP, 76, TRIP), (1, 78, 1), (2, 81, 2 * TRIP), (2 + 2 * TRIP, 78, TRIP), (3, 76, 1),
        (4, 79, 1), (5, 78, 2 * TRIP), (5 + 2 * TRIP, 76, TRIP), (6, 74, 2),
        (8, 76, 2 * TRIP), (8 + 2 * TRIP, 78, TRIP), (9, 81, 1), (10, 83, 2 * TRIP), (10 + 2 * TRIP, 81, TRIP), (11, 78, 1),
        (12, 76, 2), (14, 74, 1), (15, 72, 1),                               # the C natural: the Celtic seventh
        (16, 78, 1), (17, 76, 2 * TRIP), (17 + 2 * TRIP, 74, TRIP), (18, 71, 2),
        (20, 74, 1), (21, 76, 1), (22, 79, 2),
        (24, 78, 2 * TRIP), (24 + 2 * TRIP, 76, TRIP), (25, 74, 1), (26, 76, 1), (27, 73, 1),
        (28, 74, 4)]

def harp_bar(bar, sym, vel):
    """Twelve triplet quavers rolling up and back through the chord."""
    tones = ch(sym, 3) + ch(sym, 4)
    shape = tones[:5] + tones[4:0:-1] + tones[:3]
    for j, m in enumerate(shape[:12]):
        note(harp, 'harp', m, T(bar, j * TRIP), 1.2, vel * (1.0 if j % 3 == 0 else 0.75), rel=1.5)

def pizz(bar, sym, vel):
    note(vc_pz, 'strings', root(sym, 2), T(bar), 0.4, vel)
    note(vc_pz, 'strings', root(sym, 2) + 7, T(bar, 2), 0.4, vel * 0.8)

def drum(bar, vel):
    """A frame drum's lilt: strong on 1, soft pickups on the triplet before 3."""
    for beat, dyn, g in [(0, 'mp_1', 1.0), (1 + 2 * TRIP, 'pp_1', 0.5), (2, 'p_1', 0.7), (3 + 2 * TRIP, 'pp_2', 0.5)]:
        hit(FRAME_DRUM.format(dyn), T(bar, beat), 0.22 * vel * g, -0.15)

def tune(inst, bus, bar0, vel, octave=0, ornament=True):
    for i, (off, m, beats) in enumerate(TUNE):
        if ornament and beats >= 1 and i % 3 == 0:
            grace(inst, bus, m + 12 * octave, T(bar0, off), beats * BEAT, vel, key=D_MIXOLYDIAN, atk=0.03, rel=0.4)
        else:
            note(inst, bus, m + 12 * octave, T(bar0, off), beats * BEAT, vel, atk=0.03, rel=0.4)

def main():
    for (bar, beat, _), m in zip(E.MAP_NODES, [86, 90, 93, 81, 88, 95, 86, 90, 98, 93, 88, 100]):
        note(glock, 'harp', m, T(bar, beat), 1.5, 0.22)
    note(vc, 'strings', 38, T(-1), 5 * E.BAR, 0.22, atk=3.0, rel=3.0)
    for b, sym in zip(range(0, 4), ['D', 'G', 'D', 'A']):
        harp_bar(b, sym, 0.28)
    birdsong(T(4), T(9), density=0.3, seed=1)
    for b in range(4, 17):
        sym = PROG[(b - 4) % 8]
        harp_bar(b, sym, 0.3)
        if b >= 6:
            pizz(b, sym, 0.4)
        if b >= 9:
            chord(vla, 'strings', b, ch(sym, 3)[1:], vel=0.22, atk=1.0, gain=0.7)
        if b >= 13:
            drum(b, 0.8)
    tune(flute_nv, 'winds', 4, 0.42, octave=1)                      # the whistle: flute without vibrato, up high
    line(clar, 'winds', 12, [(0, 66, 4), (4, 67, 4), (8, 66, 4), (12, 64, 4)], 0.3, atk=0.3)
    tune(flute_nv, 'winds', 12, 0.45, octave=1)
    birdsong(T(17), T(20), density=0.45, seed=2)
    for b, sym in [(17, 'G'), (18, 'D'), (19, 'A')]:                  # breath: the fiddle alone with the harp
        harp_bar(b, sym, 0.24)
    line(solo_vln, 'strings', 17, [(0, 74, 2), (2, 76, 1), (3, 78, 1), (4, 79, 3), (7, 78, 1), (8, 76, 4)], 0.4, atk=0.15)
    for b in range(20, 25):
        sym = PROG[(b - 20) % 8] if b < 24 else 'A'
        harp_bar(b, sym, 0.32); pizz(b, sym, 0.45); drum(b, 0.9)
        chord(vc, 'strings', b, [root(sym, 2)], vel=0.4)
        chord(horn, 'brass', b, ch(sym, 3)[:2], vel=0.28, atk=0.8, gain=0.7)
    tune(vln, 'strings', 20, 0.55, octave=1, ornament=False)            # the strings take the tune up
    tune(flute_nv, 'winds', 20, 0.35, octave=2, ornament=False)
    for inst, notes in [(vln, ch('D', 5)), (vla, ch('D', 4)), (vc, [38, 50])]:   # the title: a warm, open D - no hit
        chord(inst, 'strings', 25, notes, vel=0.5, atk=0.6, rel=1.5)
    for i, m in enumerate(ch('D', 3) + ch('D', 4) + ch('D', 5)):
        note(harp, 'harp', m, T(25) + i * 0.07, 2.0, 0.4)
    field_beds()

def coda():
    coda_fire()
    grace(flute_nv, 'winds', 86, T(26) + 0.35, 2.5, 0.3, key=D_MIXOLYDIAN)
    for b, sym in zip(range(27, 31), ['G', 'D', 'G', 'A']):
        harp_bar(b, sym, 0.24)
    line(flute_nv, 'winds', 28, [(o, m + 12, d) for o, m, d in TUNE[:11]], 0.3)
    for i, m in enumerate(ch('Gadd9', 3) + [79, 83]):                  # ends open, on the fourth
        note(harp, 'harp', m, T(31) + i * 0.12, 3.0, 0.3, rel=3.0)
    chord(vla, 'strings', 31, ch('G', 3)[1:], bars=1.6, vel=0.2, atk=1.5, rel=2.5)
    birdsong(T(31), T(31) + 5, density=0.5, seed=3)

if __name__ == '__main__':
    E.render(sys.argv[1] if len(sys.argv) > 1 else 'shire.wav', [main], [coda], rt=2.4, calm=True)
