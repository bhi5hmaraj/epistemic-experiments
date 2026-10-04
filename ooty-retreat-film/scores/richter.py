"""In the manner of Max Richter (On the Nature of Daylight): a string chorale in G minor over a slowly falling bass.
No pulse anywhere. The film's cuts ride chord changes instead of beats.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import score as E
from score import T, note, vln, vla, vc, cb, horn, harp, piano
from common import ch, root, chord, line, ping_map, field_beds, coda_fire

# the falling bass: G F Eb D C Bb A D, one chord per bar, and the violins' long top line above it
WALK = [('Gm', 43, 74), ('F', 41, 72), ('Eb', 39, 70), ('D', 38, 69),
        ('Cm', 36, 67), ('Bb', 34, 65), ('Am7b5', 33, 67), ('D', 38, 66)]

def chorale(bar, i, vel, top=True, octave_top=0, atk=1.2, bars=1):
    sym, bass, sop = WALK[i % 8]
    chord(cb, 'strings', bar, [bass - 12 if bass >= 36 else bass], bars=bars, vel=vel, atk=atk, rel=2.5)
    chord(vc, 'strings', bar, [bass, ch(sym, 3)[1]], bars=bars, vel=vel, atk=atk, rel=2.5)
    chord(vla, 'strings', bar, ch(sym, 4)[:2], bars=bars, vel=vel * 0.9, atk=atk, rel=2.5)
    if top:
        chord(vln, 'strings', bar, [sop + 12 * octave_top], bars=bars, vel=vel, atk=atk * 1.3, rel=3.0)

def intro():
    ping_map(harp, 'harp', [79, 82, 86, 74, 91, 84, 89, 79, 94, 86, 82, 98], vel=0.3)
    note(vc, 'strings', 43, T(-2) + 0.5, 6 * E.BAR, 0.28, atk=4.0, rel=3.0)
    for i, b in enumerate(range(0, 4)):
        chord(vla, 'strings', b, ch(WALK[i][0], 4)[:2], vel=0.25 + 0.03 * i, atk=1.5, rel=2.5)
        chord(vc, 'strings', b, [WALK[i][1]], vel=0.28, atk=1.5, rel=2.5)

def arrival():
    for i, b in enumerate(range(4, 9)):
        chorale(b, i + 4, 0.32 + 0.03 * i, top=b >= 6)

def questions():
    for i, b in enumerate(range(9, 17)):
        ramp = i / 7
        chorale(b, i, 0.42 + 0.35 * ramp, octave_top=1 if b >= 13 else 0)
        if b >= 13:
            chord(horn, 'brass', b, [WALK[i][2] - 12], vel=0.35 + 0.3 * ramp, atk=0.8)
    for j in range(8):
        E.timp(T(16, 2 + j * 0.25), 0.2 + 0.04 * j)
    E.riser(T(17), 4.0, 0.5)

def breath():
    """Everything drops away but one high violin line and a low cello."""
    line(vln, 'strings', 17, [(0, 82, 4), (4, 79, 4), (8, 78, 4)], 0.4, atk=1.2, rel=2.0)
    for b, bass in [(17, 39), (18, 36), (19, 38)]:
        chord(vc, 'strings', b, [bass], vel=0.35, atk=1.2)
    field_beds()

def summit():
    for i, b in enumerate(range(20, 24)):
        chorale(b, i, 0.85, octave_top=1, atk=0.4)
        chord(vln, 'strings', b, [WALK[i][2]], vel=0.8, atk=0.4)
        chord(horn, 'brass', b, ch(WALK[i][0], 3), vel=0.75, atk=0.4)
        E.timp(T(b), 0.5)
    chorale(24, 7, 0.9, octave_top=1, atk=0.3)
    for j in range(16):
        E.timp(T(24, j * 0.25), 0.35 + 0.035 * j)
    E.riser(T(25), 3.5, 1.0)
    E.boom(T(25), 0.8)                                       # the title: G major, the minor opened into light
    for inst, notes in [(vln, ch('G', 5) + [86]), (vla, ch('G', 4)), (vc, [31 + 12, 43 + 12]), (cb, [31]), (horn, ch('G', 3))]:
        chord(inst, 'brass' if inst is horn else 'strings', 25, notes, vel=0.95, atk=0.05, rel=0.8)

def coda():
    coda_fire()
    note(vla, 'strings', 62, T(26) + 0.35, 2.5, 0.3, atk=0.8, rel=2.5)
    for b, i in [(27, 2), (28, 4), (29, 3), (30, 2)]:
        chorale(b, i, 0.3, top=b in (28, 29), atk=1.0)
    for m in ch('Ebmaj7', 3) + [74]:                          # ends open, on the sixth degree
        note(vla if m > 50 else vc, 'strings', m, T(31), 1.8 * E.BAR, 0.3, atk=1.5, rel=3.0)
    note(piano, 'piano', 79, T(31) + 1.0, 3.0, 0.22, rel=3.0)

if __name__ == '__main__':
    E.render(sys.argv[1] if len(sys.argv) > 1 else 'richter.wav', [intro, arrival, questions, breath, summit], [coda], rt=3.8)
