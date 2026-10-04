"""In the manner of Ramin Djawadi (Westworld, Game of Thrones): D minor, a rolling cello ostinato in a lilting 12/8,
a player piano, a solo violin that sings the theme, war drums at the summit.

12/8 on the film's grid: each beat splits into three, so the bar length (and every cut) stays exactly the same.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import score as E
from score import T, BEAT, note, piano, vln, vla, vc, cb, vc_sp, horn, harp
from common import solo_vln, ch, root, chord, line, hit, ping_map, field_beds, coda_fire

CYCLE = ['Dm', 'Bb', 'F', 'C']                             # i - VI - III - VII
DRUM = 'VSCO 1 Percussion/drums/other/ethnic/giant/mallet/EthnicLargeMallet_hit_{}.wav'
# the theme, 4 bars: (beat offset, midi, beats) - rises to F, sighs back down
THEME = [(0, 74, 1.5), (1.5, 77, 1.5), (3, 76, 1), (4, 74, 3), (7, 70, 1),
         (8, 72, 1.5), (9.5, 74, 1.5), (11, 77, 1), (12, 76, 4)]

def at(bar):
    return CYCLE[bar % 4]

def ostinato(bar, sym, vel):
    """Twelve triplet quavers: root, fifth, octave, third, octave, fifth - twice."""
    r = root(sym, 2)
    third = ch(sym, 2)[1]
    shape = [r, r + 7, r + 12, third + 12, r + 12, r + 7] * 2
    for j, m in enumerate(shape):
        note(vc_sp, 'strings', m, T(bar, j / 3), 0.3, vel * (1.0 if j % 3 == 0 else 0.8), rel=0.15)

def drums(bar, vel):
    for beat, v in [(0, 1.0), (1.5, 0.6), (2, 0.85), (3.5, 0.6)]:
        hit(DRUM.format('ff_1' if v > 0.9 else 'mf_1'), T(bar, beat), 0.45 * vel * v)

def intro():
    """The player piano: single high notes in a big room, as the map fills in."""
    ping_map(piano, 'piano', [86, 89, 81, 84, 93, 88, 86, 81, 89, 84, 93, 86], vel=0.24)
    note(vc, 'strings', 38, T(-1), 5 * E.BAR, 0.3, atk=3.0, rel=3.0)
    for t, m in [(T(0, 1), 74), (T(0, 2.5), 77), (T(1, 1), 76), (T(2), 74), (T(2, 3), 70), (T(3, 1), 69)]:
        note(piano, 'piano', m, t, 1.6, 0.3, rel=2.5)
    E.reverse_swell(62, T(4), 2.2, 0.3)

def arrival():
    for b in range(4, 9):
        sym = at(b) if b < 8 else 'A'
        ostinato(b, sym, 0.5 + 0.04 * (b - 4))
        chord(vla, 'strings', b, ch(sym, 3)[1:], vel=0.3, atk=0.8, gain=0.8)
    line(solo_vln, 'strings', 5, THEME[:5], 0.45, gain=0.9)

def questions():
    prog = ['Dm', 'Bb', 'F', 'C', 'Dm', 'Bb', 'Gm', 'A']
    for i, (b, sym) in enumerate(zip(range(9, 17), prog)):
        ramp = i / 7
        ostinato(b, sym, 0.45 + 0.3 * ramp)
        chord(cb, 'strings', b, [root(sym, 1)], vel=0.4 + 0.3 * ramp)
        chord(vla, 'strings', b, ch(sym, 4)[:2], vel=0.3 + 0.3 * ramp, atk=0.4)
        if b >= 13:
            drums(b, 0.5 + 0.4 * ramp)
            chord(vln, 'strings', b, ch(sym, 5)[1:], vel=0.35 + 0.3 * ramp, atk=0.5)
    line(solo_vln, 'strings', 9, THEME, 0.55, gain=1.0)
    line(solo_vln, 'strings', 13, THEME[:5], 0.7, octave=1, gain=1.0)
    line(horn, 'brass', 15, [(0, 55, 4), (4, 57, 4)], 0.6)
    for j in range(16):
        E.timp(T(16, j * 0.25), 0.25 + 0.045 * j)
    E.riser(T(17), 4.0, 0.9)

def breath():
    """The cellos stop. Solo violin and harp in the rain."""
    for b, sym in [(17, 'Bb'), (18, 'F'), (19, 'C')]:
        for k, m in enumerate(ch(sym, 3) + [ch(sym, 4)[1]]):
            note(harp, 'harp', m, T(b, k * 0.75), 2.0, 0.4, rel=2.5)
    line(solo_vln, 'strings', 17, [(0, 74, 3), (3, 72, 1), (4, 69, 4), (8, 67, 2), (10, 69, 2)], 0.45)
    field_beds()

def summit():
    for b, sym in zip(range(20, 24), CYCLE):
        ostinato(b, sym, 0.85)
        chord(cb, 'strings', b, [root(sym, 1)], vel=0.85)
        chord(vc, 'strings', b, [root(sym, 2) + 12], vel=0.7)
        chord(vla, 'strings', b, ch(sym, 4), vel=0.7, atk=0.1)
        drums(b, 1.0)
        E.timp(T(b), 0.8)
    line(vln, 'strings', 20, THEME, 0.85, octave=1, gain=1.1)
    line(horn, 'brass', 20, THEME, 0.8, octave=-1, gain=0.8)
    ostinato(24, 'A', 0.9)
    chord(horn, 'brass', 24, ch('A', 3), vel=0.8, atk=0.3)
    chord(vln, 'strings', 24, [85, 88], vel=0.85)
    for j in range(16):
        E.timp(T(24, j * 0.25), 0.4 + 0.035 * j)
        if j % 2 == 0:
            hit(DRUM.format('ff_1'), T(24, j * 0.25), 0.2 + 0.02 * j)
    E.riser(T(25), 3.5, 1.2)
    E.boom(T(25), 1.0)                                      # the title: D major, the minor finally resolved
    chord(vln, 'strings', 25, ch('D', 5) + [86], vel=0.95, atk=0.02, rel=0.6)
    chord(vla, 'strings', 25, ch('D', 4), vel=0.9, atk=0.02, rel=0.6)
    chord(vc, 'strings', 25, [38, 50], vel=0.95, atk=0.02, rel=0.6)
    chord(horn, 'brass', 25, ch('D', 3), vel=0.9, atk=0.02, rel=0.6)
    hit(DRUM.format('ff_2'), T(25), 0.6)

def coda():
    coda_fire()
    note(piano, 'piano', 86, T(26) + 0.35, 2.5, 0.3, rel=2.5)
    for m in ch('Bb', 3):
        note(piano, 'piano', m, T(27), 3.0, 0.24, rel=2.5)
    line(piano, 'piano', 28, THEME[:5], 0.32, octave=1)
    for b, sym in [(28, 'Dm'), (29, 'Bb')]:
        chord(vc, 'strings', b, [root(sym, 2)], vel=0.25, atk=0.8, gain=0.6)
    line(solo_vln, 'strings', 29, [(0, 74, 3), (3, 72, 1)], 0.35)
    for m in ch('C', 3):
        note(piano, 'piano', m, T(30), E.BAR, 0.26, rel=2.0)
    for m in ch('Bbmaj7', 2) + [74, 81]:                      # ends open, on the sixth degree
        note(piano, 'piano', m, T(31), 5.5, 0.28, rel=3.0)
    chord(vc, 'strings', 31, [46], bars=1.6, vel=0.28, atk=1.0, rel=2.5, gain=0.6)
    line(solo_vln, 'strings', 31, [(1, 81, 6)], 0.3)

if __name__ == '__main__':
    E.render(sys.argv[1] if len(sys.argv) > 1 else 'djawadi.wav', [intro, arrival, questions, breath, summit], [coda])
