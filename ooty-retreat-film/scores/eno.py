"""In the manner of Brian Eno's ambient records: short glass-bell phrases looping at different lengths, drifting in and
out of phase over a soft drone, in a very large space. No piano. Nothing builds, layers simply accumulate. D-flat major.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import score as E
from score import T, BEAT
from common import ch, field_beds, coda_fire
from synth import pad, bell

# (period in beats, first bar, last bar, phrase of (beat, midi, velocity)) - the periods never line up the same way twice
LOOPS = [(11.0, -2, 26, [(0, 68, 0.3), (1.5, 65, 0.25)]),
         (13.5, 0, 26, [(0, 73, 0.28), (2, 75, 0.24)]),
         (17.0, -1, 26, [(0, 58, 0.3)]),
         (9.5, 9, 26, [(0, 77, 0.22), (1, 80, 0.2)]),
         (7.0, 20, 26, [(0, 61, 0.26), (0.5, 68, 0.22)])]
DRONE = [(-2, 11, 'Dbmaj9'), (9, 4, 'Gbmaj7'), (13, 4, 'Dbmaj9'), (17, 3, 'Bbm7'), (20, 4, 'Gbmaj7'), (24, 2, 'Dbmaj9')]

def loop(period, first, last, phrase, start=None):
    t, end = start if start is not None else T(first), T(last)
    while t < end:
        for off, m, v in phrase:
            bell(m, t + off * BEAT, 3.0, v * 2.2, pan=((m % 5) - 2) * 0.15)
        t += period * BEAT

def main():
    for (bar, beat, _), m in zip(E.MAP_NODES, [85, 89, 92, 80, 87, 94, 85, 89, 97, 92, 87, 99]):
        bell(m, T(bar, beat), 2.0, 0.4)
    for spec in LOOPS:
        loop(*spec)
    for bar, bars, sym in DRONE:
        pad(ch(sym, 2)[:1] + ch(sym, 3), T(bar), bars * E.BAR, 0.9, cutoff=900)
    for i, m in enumerate(ch('Dbmaj9', 3) + [80]):             # the title: a chord, gently rolled, nothing more
        bell(m, T(25) + i * 0.12, 4.0, 0.8)
    field_beds()

def coda():
    coda_fire()
    pad(ch('Dbmaj9', 3), T(26), 6 * E.BAR, 0.7, cutoff=800)
    loop(11.0, 26, 33, LOOPS[0][3], start=T(26) + 0.4)
    loop(13.5, 26, 33, LOOPS[1][3], start=T(27))
    for i, m in enumerate(ch('Gbmaj7', 3) + [82]):
        bell(m, T(31) + i * 0.2, 5.0, 0.6)

if __name__ == '__main__':
    E.render(sys.argv[1] if len(sys.argv) > 1 else 'eno.wav', [main], [coda], rt=5.5, calm=True)
