"""In the manner of Hans Zimmer's Interstellar: pipe organ, a clock that never stops ticking, a two-note piano figure.

The clock is the idea: 'the future is already here'. It ticks from the first frame, doubles when the questions press,
and stops dead in the rain. Same bar grid as the film, so every cut still lands.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import score as E
from score import T, BEAT, note, piano, vln, vla, vc, cb, horn
from common import organ_loud, organ_soft, pedal, pedal_soft, ch, root, chord, line, hit, ping_map, field_beds, coda_fire

CYCLE = ['Am', 'Em/G', 'F', 'C']                        # i - v - VI - III, one chord a bar
LOW = {'Am': 69, 'Em/G': 71, 'F': 72, 'C': 67}          # the piano figure's moving lower note under a fixed E5
CLICK = 'VSCO 1 Percussion/varWood/wood_click_{}.wav'

def at(bar):
    return CYCLE[bar % 4]

def tick(t0, t1, every=1.0, gain=0.18):
    t = t0
    i = 0
    while t < t1 - 1e-6:
        hit(CLICK.format('mp' if i % 4 else 'f'), t, gain * (1.0 if i % 4 == 0 else 0.7), 0.25 if i % 2 else -0.25)
        t += every * BEAT
        i += 1

def figure(bar, vel):
    """The Interstellar-style two-note pulse: lower note moves with the harmony, E5 never does."""
    for j in range(8):
        note(piano, 'piano', LOW[at(bar)] if j % 2 == 0 else 76, T(bar, j * 0.5), 0.5, vel * (1.0 if j % 2 == 0 else 0.85), rel=0.8)

def organ(bar, loud=False, vel=0.5, bars=1):
    inst, ped = (organ_loud, pedal) if loud else (organ_soft, pedal_soft)
    chord(inst, 'organ', bar, ch(at(bar), 4), bars=bars, vel=vel, atk=0.6 if not loud else 0.2, rel=2.0)
    note(ped, 'organ', root(at(bar), 2 if loud else 3), T(bar) - 0.05, bars * E.BAR, vel, atk=0.5, rel=2.0)

def intro():
    tick(T(-2), T(17))                                    # the clock runs from the very first frame
    ping_map(piano, 'piano', [81, 88, 84, 76, 93, 83, 86, 88, 91, 84, 81, 96], vel=0.2)
    note(pedal_soft, 'organ', 45, T(-1), 5 * E.BAR, 0.35, atk=3.0, rel=3.0)
    for b in range(0, 4):
        organ(b, vel=0.25 + 0.04 * b)
    for t, m in [(T(0, 1), 76), (T(1, 1), 74), (T(2, 1), 72), (T(3, 1), 71)]:
        note(piano, 'piano', m, t, 2.5, 0.28, rel=2.5)

def arrival():
    for b in range(4, 9):
        figure(b, 0.3 + 0.03 * (b - 4))
        organ(b, vel=0.32)

def questions():
    tick(T(13), T(17), every=0.5, gain=0.14)              # the pressure doubles
    for i, b in enumerate(range(9, 17)):
        ramp = i / 7
        figure(b, 0.45 + 0.25 * ramp)
        organ(b, loud=b >= 13, vel=0.4 + 0.3 * ramp)
        chord(vc, 'strings', b, [root(at(b), 2), root(at(b), 3)], vel=0.4 + 0.3 * ramp)
        if b >= 11:
            chord(vla, 'strings', b, ch(at(b), 4)[:2], vel=0.35 + 0.3 * ramp)
            chord(cb, 'strings', b, [root(at(b), 1)], vel=0.45 + 0.3 * ramp)
    line(organ_loud, 'organ', 13, [(0, 88, 4), (4, 86, 2), (6, 84, 2), (8, 84, 4), (12, 83, 4)], 0.7)
    line(horn, 'brass', 15, [(0, 60, 4), (4, 59, 4)], 0.55)
    for j in range(16):
        E.timp(T(16, j * 0.25), 0.25 + 0.04 * j)
    E.riser(T(17), 4.0, 0.9)

def breath():
    """The clock has stopped. Just the piano, slow, and the organ breathing."""
    for b, sym in [(17, 'F'), (18, 'C'), (19, 'G')]:
        for k, m in enumerate(ch(sym, 4)):
            note(piano, 'piano', m, T(b, k * 1.3), 2.5, 0.3, rel=2.5)
        chord(organ_soft, 'organ', b, ch(sym, 3), vel=0.28, atk=1.0)
    field_beds()

def summit():
    for i, b in enumerate(range(20, 24)):
        figure(b, 0.7)
        organ(b, loud=True, vel=0.85)
        chord(vc, 'strings', b, [root(at(b), 2), root(at(b), 3)], vel=0.8)
        chord(cb, 'strings', b, [root(at(b), 1)], vel=0.8)
        chord(vla, 'strings', b, ch(at(b), 4), vel=0.7, atk=0.1)
        chord(vln, 'strings', b, ch(at(b), 5)[1:], vel=0.7, atk=0.1)
        E.timp(T(b), 0.8); E.timp(T(b, 2), 0.6)
    line(horn, 'brass', 20, [(0, 64, 4), (4, 62, 2), (6, 60, 2), (8, 60, 4), (12, 59, 4)], 0.8)
    line(vln, 'strings', 20, [(0, 88, 4), (4, 86, 2), (6, 84, 2), (8, 84, 4), (12, 83, 4)], 0.85, gain=1.1)
    chord(organ_loud, 'organ', 24, ch('G', 4), vel=0.9, atk=0.3)       # the build: dominant, the roll, the swell
    chord(vc, 'strings', 24, [43, 55], vel=0.85); chord(vln, 'strings', 24, [83, 86], vel=0.85)
    for j in range(16):
        E.timp(T(24, j * 0.25), 0.4 + 0.035 * j)
    E.riser(T(25), 3.5, 1.2)
    E.boom(T(25), 1.0)                                     # the title: A major, full organ, everything
    chord(organ_loud, 'organ', 25, ch('A', 4) + ch('A', 5), vel=1.0, atk=0.02, rel=0.8)
    note(pedal, 'organ', 33, T(25), E.BAR, 1.0, rel=0.8)
    chord(vln, 'strings', 25, ch('A', 5), vel=0.9, atk=0.02, rel=0.6)
    chord(vc, 'strings', 25, [45, 57], vel=0.9, atk=0.02, rel=0.6)
    chord(horn, 'brass', 25, ch('A', 3), vel=0.9, atk=0.02, rel=0.6)

def coda():
    coda_fire()
    note(piano, 'piano', 76, T(26) + 0.35, 2.5, 0.28, rel=2.5)
    chord(organ_soft, 'organ', 27, ch('F', 3), vel=0.25, atk=1.0)
    tick(T(28), T(31), every=1.0, gain=0.1)               # the clock again, softly: time moves on
    for b, sym in [(28, 'Am'), (29, 'F')]:
        for j in range(8):
            note(piano, 'piano', {'Am': 69, 'F': 72}[sym] if j % 2 == 0 else 76, T(b, j * 0.5), 0.5, 0.26, rel=0.8)
        chord(organ_soft, 'organ', b, ch(sym, 4), vel=0.25, atk=1.0)
    chord(organ_soft, 'organ', 30, ch('G', 3), vel=0.25, atk=1.0)
    chord(organ_soft, 'organ', 31, ch('Fmaj7', 3) + [79], bars=1.8, vel=0.28, atk=1.2, rel=3.0)
    note(pedal_soft, 'organ', 41, T(31), 1.8 * E.BAR, 0.3, atk=1.0, rel=3.0)
    for i, m in enumerate([77, 81, 84, 88]):
        note(piano, 'piano', m, T(31) + 0.6 + i * 0.4, 3.0, 0.24, rel=3.0)

if __name__ == '__main__':
    E.render(sys.argv[1] if len(sys.argv) > 1 else 'zimmer.wav', [intro, arrival, questions, breath, summit], [coda], rt=3.4)
