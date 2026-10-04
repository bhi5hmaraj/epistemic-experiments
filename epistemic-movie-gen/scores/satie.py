"""In the manner of Erik Satie's Gymnopedies: one piano, a small dry room, a slow lilting left hand and a plain,
floating tune. Intimate, unhurried, a little melancholy. D major.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import score as E
from score import T, note, piano
from common import ch, root, line, ping_map, field_beds, coda_fire

HARMONY = {**{b: ('Gmaj7' if b % 2 == 0 else 'Dmaj7') for b in range(-2, 9)},
           **dict(zip(range(9, 17), ['Em7', 'A7sus4', 'Dmaj7', 'Bm7', 'Gmaj7', 'F#m7', 'Em7', 'A7sus4'])),
           **dict(zip(range(17, 25), ['Gmaj7', 'Dmaj7', 'Em7', 'Gmaj7', 'F#m7', 'Em7', 'A7', 'A7sus4']))}
# the tune, four bars: (beat, midi, beats) - rises a little, settles on A and waits
TUNE = [(1.5, 76, 1.5), (3, 78, 1), (4, 74, 2), (6, 71, 1), (7, 73, 1), (8, 74, 1.5), (9.5, 76, 0.5), (10, 69, 6)]

def lilt(bar, sym, vel, full=False):
    """Bass on the downbeat, the chord a beat and a half later: long-short, like a slow waltz folded into four."""
    r = root(sym, 2)
    note(piano, 'piano', r, E.T(bar), 1.4 * E.BEAT, vel, rel=1.2)
    if full:
        note(piano, 'piano', r - 12, E.T(bar), 1.4 * E.BEAT, vel * 0.7, rel=1.2)
    for m in ch(sym, 3)[1:]:
        note(piano, 'piano', m + 12 if m < 55 else m, E.T(bar, 1.5), 2.3 * E.BEAT, vel * 0.8, rel=1.0)

def main():
    ping_map(piano, 'piano', [86, 90, 93, 81, 88, 95, 86, 90, 98, 93, 88, 100], vel=0.18)
    for b in range(0, 25):
        lilt(b, HARMONY[b], 0.28 + (0.08 if 20 <= b < 25 else 0) + (0.03 if 9 <= b < 17 else 0), full=20 <= b < 25)
    line(piano, 'piano', 4, TUNE, 0.32)
    for b in (9, 13):
        line(piano, 'piano', b, TUNE, 0.36)
    line(piano, 'piano', 20, TUNE, 0.44, octave=1)
    for i, m in enumerate(ch('Dmaj9', 2) + ch('Dmaj9', 4)):   # the title: a slow rolled chord
        note(piano, 'piano', m, T(25) + i * 0.09, 3.5, 0.34, rel=2.5)
    field_beds()

def coda():
    coda_fire()
    for b, sym in zip(range(26, 31), ['Gmaj7', 'Dmaj7', 'Gmaj7', 'Dmaj7', 'Em7']):
        lilt(b, sym, 0.24)
    line(piano, 'piano', 28, TUNE[:5], 0.28)
    for m in ch('Gmaj9', 2) + [81]:
        note(piano, 'piano', m, T(31), 5.5, 0.26, rel=3.0)

if __name__ == '__main__':
    E.render(sys.argv[1] if len(sys.argv) > 1 else 'satie.wav', [main], [coda], rt=1.5, calm=True)
