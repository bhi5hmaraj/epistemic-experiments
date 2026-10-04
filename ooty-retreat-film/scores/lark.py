"""After Vaughan Williams's The Lark Ascending: a solo violin climbing in free pentatonic runs over hushed, held strings.
No pulse at all, only air. E major.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import score as E
from score import T, BEAT, note, vln, vla, vc, cb, harp
from common import solo_vln, flute, ch, root, chord, field_beds, coda_fire
from synth import birdsong

PENTA = [p for p in range(52, 101) if p % 12 in (4, 6, 8, 11, 1)]   # E F# G# B C#: the lark's scale
HARMONY = [('E', 2), ('A/E', 2), ('C#m7', 2), ('Bsus4', 1), ('B', 1), ('E', 2), ('F#m7', 2), ('Aadd9', 2), ('Bsus4', 2)]

def flight(bar, beat, low, steps, vel, hold=2.0, fall=2):
    """One ascent: quick notes up the pentatonic scale, a long held note at the top, a small turn back down."""
    i = min(range(len(PENTA)), key=lambda k: abs(PENTA[k] - low))
    steps = min(steps, max(k for k in range(len(PENTA) - i) if PENTA[i + k] <= solo_vln.keys.max()))   # stay in range
    t = T(bar, beat)
    for s in range(steps):
        note(solo_vln, 'strings', PENTA[i + s], t, 0.3 * BEAT, vel * (0.8 + 0.2 * s / steps), atk=0.02, rel=0.2)
        t += (0.25 if s < steps - 3 else 0.4) * BEAT                     # the run slows as it arrives
    top = PENTA[i + steps]
    note(solo_vln, 'strings', top, t, hold * BEAT, vel, atk=0.1, rel=0.8)
    t += hold * BEAT
    for d in range(1, fall + 1):
        note(solo_vln, 'strings', PENTA[i + steps - d], t, 0.6 * BEAT, vel * 0.8, atk=0.05, rel=0.4)
        t += 0.6 * BEAT

def bed(first_bar, last_bar, vel, octave_up=False):
    """Held string chords, changing slowly."""
    b = first_bar
    for sym, bars in HARMONY * 3:
        if b >= last_bar:
            break
        bars = min(bars, last_bar - b)
        chord(vc, 'strings', b, [root(sym.split('/')[-1] if '/' in sym else sym, 2)], bars=bars, vel=vel, atk=1.5, rel=2.5)
        chord(vla, 'strings', b, ch(sym.split('/')[0], 3)[1:3], bars=bars, vel=vel * 0.9, atk=1.5, rel=2.5)
        if octave_up:
            chord(vln, 'strings', b, ch(sym.split('/')[0], 4)[1:3], bars=bars, vel=vel * 0.8, atk=1.8, rel=2.5)
        b += bars

def main():
    for (bar, beat, _), m in zip(E.MAP_NODES, [88, 92, 83, 95, 90, 85, 88, 92, 97, 90, 95, 100]):
        note(harp, 'harp', m, T(bar, beat), 1.5, 0.3, rel=2.5)
    note(cb, 'strings', 40, T(-1), 5 * E.BAR, 0.2, atk=3.0, rel=3.0)
    bed(0, 9, 0.22)
    birdsong(T(2), T(9), density=0.25, seed=4)
    for bar, beat, low, steps in [(1, 0, 64, 5), (3, 1, 66, 6), (5, 0, 68, 7), (7, 0, 71, 7)]:
        flight(bar, beat, low, steps, 0.34)
    bed(9, 17, 0.3, octave_up=True)
    for bar, beat, low, steps in [(9, 0, 71, 6), (10, 2, 73, 7), (12, 0, 76, 7), (13, 2, 78, 8), (15, 0, 80, 8)]:
        flight(bar, beat, low, steps, 0.4)
    birdsong(T(17), T(20), density=0.4, seed=5)
    for bar, low in [(17, 83), (18, 85), (19, 88)]:                    # breath: the lark alone, very high
        flight(bar, 0.5, low, 3, 0.3, hold=2.2, fall=1)
    bed(20, 25, 0.4, octave_up=True)
    for bar, beat, low, steps in [(20, 0, 76, 8), (21, 2, 78, 8), (23, 0, 80, 7)]:
        flight(bar, beat, low, steps, 0.46)
    for b, m in [(20, 76), (22, 78), (24, 80)]:
        note(flute, 'winds', m, T(b), 2 * E.BAR, 0.3, atk=1.0, rel=1.5)
    for inst, notes in [(vln, ch('E', 5)), (vla, ch('E', 4)), (vc, [40, 52])]:   # the title: a soft E major chord
        chord(inst, 'strings', 25, notes, vel=0.45, atk=0.8, rel=2.0)
    note(solo_vln, 'strings', 88, T(25, 0.5), 3.0, 0.35, atk=0.5, rel=2.0)
    field_beds()

def coda():
    coda_fire()
    chord(vla, 'strings', 26, ch('A', 3)[1:3], bars=2, vel=0.2, atk=1.5, rel=2.5)
    flight(27, 0, 71, 5, 0.3)
    chord(vc, 'strings', 28, [40], bars=3, vel=0.22, atk=1.5, rel=2.5)
    chord(vla, 'strings', 28, ch('Eadd9', 3)[1:3], bars=3, vel=0.2, atk=1.5, rel=2.5)
    flight(29, 0, 76, 7, 0.28, hold=3.0)
    for m in ch('Aadd9', 3):                                             # ends open, on the fourth, the lark still up there
        note(vla if m > 50 else vc, 'strings', m, T(31), 1.8 * E.BAR, 0.2, atk=1.5, rel=3.0)
    note(solo_vln, 'strings', 92, T(31, 1), 5.0, 0.22, atk=1.0, rel=3.0)
    birdsong(T(31), T(31) + 5, density=0.5, seed=6)

if __name__ == '__main__':
    E.render(sys.argv[1] if len(sys.argv) > 1 else 'lark.wav', [main], [coda], rt=3.2, calm=True)
