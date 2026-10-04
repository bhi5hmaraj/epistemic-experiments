"""Lo-fi, in the manner of Nujabes: a warm electric piano on jazzy sevenths and ninths, a dusty swung beat, a round
bass, vinyl crackle all the way through. Bedroom-cosy, never dramatic. C major (ii - V - I - vi).
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import numpy as np
import score as E
from score import T, BEAT, END
from common import ch, root, field_beds, coda_fire
from synth import epiano, bass, crackle, dusty_kick, dusty_snare, dusty_hat

CYCLE = ['Dm9', 'G13', 'Cmaj9', 'Am9']
SWING = 0.09                                                 # offbeat eighths land late, in beats
rng = np.random.default_rng(3)

def at(bar):
    return CYCLE[bar % 4]

def human(t):
    return t + rng.uniform(-0.012, 0.012)

def keys(bar, sym, vel, stab=True, hook=False):
    voicing = [m for m in ch(sym, 3) if m >= 50][:5]
    for m in voicing:
        epiano(m, human(T(bar)), 1.6 * BEAT, vel, pan=-0.1)
    if stab:
        for m in voicing[1:4]:
            epiano(m, human(T(bar, 2.5 + SWING)), 0.6 * BEAT, vel * 0.7, pan=-0.1)
    if hook:
        top = ch(sym, 5)
        for beat, m in [(0.5 + SWING, top[2]), (1, top[1]), (2.5 + SWING, top[0])]:
            epiano(m, human(T(bar, beat)), 0.8 * BEAT, vel * 0.8, pan=0.15)

def groove(bar, v):
    dusty_kick(T(bar), v); dusty_kick(T(bar, 2.75), v * 0.8)
    dusty_snare(T(bar, 1), v); dusty_snare(T(bar, 3), v)
    for j in range(8):
        dusty_hat(human(T(bar, j * 0.5 + (SWING if j % 2 else 0))), v * (0.9 if j % 2 else 0.6))

def low(bar, sym, v):
    bass(root(sym, 2), T(bar), 1.5 * BEAT, v); bass(root(sym, 2) + 12, T(bar, 2.5 + SWING), 0.8 * BEAT, v * 0.7)

def main():
    crackle(0, T(26) + 0.5)
    for (bar, beat, _), m in zip(E.MAP_NODES, [84, 88, 81, 91, 86, 93, 84, 89, 96, 88, 91, 100]):
        epiano(m, T(bar, beat), 1.0, 0.3)
    for b in range(0, 4):
        keys(b, at(b), 0.4, stab=False)
    for b in range(4, 17):
        keys(b, at(b), 0.5 + 0.1 * (b >= 9))
        low(b, at(b), 0.8)
        groove(b, 0.5 if b < 9 else 0.7)
    for b, sym in [(17, 'Fmaj9'), (18, 'Em9'), (19, 'Am9')]:  # breath: the beat drops out
        keys(b, sym, 0.4, stab=False)
    for b in range(20, 25):
        sym = at(b) if b < 24 else 'G13'
        keys(b, sym, 0.6, hook=True)
        low(b, sym, 0.9)
        groove(b, 0.8)
    for m in ch('Cmaj9', 3):                                    # the title: the beat stops, one chord rings
        epiano(m, T(25), 3 * BEAT, 0.6)
    bass(36, T(25), 3 * BEAT, 0.9)
    field_beds()

def coda():
    coda_fire()
    crackle(T(26), END)
    for b, sym in zip(range(26, 31), ['Dm9', 'G13', 'Cmaj9', 'Am9', 'Dm9']):
        keys(b, sym, 0.35, stab=b in (28, 29))
    for m in ch('Fmaj9', 3):                                    # ends open, on the fourth
        epiano(m, T(31), 5.0, 0.35)

if __name__ == '__main__':
    E.render(sys.argv[1] if len(sys.argv) > 1 else 'lofi.wav', [main], [coda], rt=1.8, calm=True)
