"""In the manner of Olafur Arnalds / Nils Frahm. F major, lydian-leaning.

Felt piano with tape-delay echoes. A warm analogue pad whose filter opens as the film climbs.
A soft electronic pulse that arrives with the questions.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import numpy as np, scipy.signal as ss
import score as E
from score import T, BEAT, SR, note, piano, vln, vla, vc
from common import ch, root, chord, line, ping_map, field_beds, coda_fire

CYCLE = ['Fmaj7', 'C/E', 'Dm7', 'Bbmaj7']
MOTIF = [(0, 0), (0.75, 2), (1.5, 1), (2.5, 3)]             # (beat, chord tone) - syncopated, lets the echoes fill in
ECHO = 0.75                                               # dotted-eighth tape delay, in beats

def at(bar):
    return CYCLE[bar % 4]

def keys(m, t, vel, dur=1.2, echoes=3):
    """A felt-piano note and its tape echoes, each softer and a touch darker."""
    for k in range(echoes + 1):
        note(piano, 'piano', m, t + k * ECHO * BEAT, dur, vel * 0.45 ** k, rel=1.2)

def motif(bar, sym, vel, octave=4, sparse=False):
    tones = ch(sym, octave)
    for beat, idx in (MOTIF[::2] if sparse else MOTIF):
        keys(tones[idx % len(tones)], T(bar, beat), vel)

def pad(sym, t0, bars, cutoff, level, octave=3):
    """Three detuned saws per note through a two-pole low-pass: the warm synth bed."""
    dur = bars * E.BAR + 2.5
    t = np.arange(int(dur * SR)) / SR
    out = np.zeros((2, len(t)), np.float32)
    for m in ch(sym, octave):
        f = 440 * 2 ** ((m - 69) / 12)
        for ch_i, det in enumerate((0.996, 1.004)):
            out[ch_i] += sum(ss.sawtooth(2 * np.pi * f * d * t + ph) for d, ph in ((det, 0), (1.0, 1.3), (1 / det, 2.1))) / 3
    out = ss.sosfilt(ss.butter(2, cutoff, 'low', fs=SR, output='sos'), out)
    env = np.minimum(1, t / 1.4) * np.clip((dur - t) / 2.5, 0, 1)
    E.mix.add('synth', out * env * level * 0.06, t0 - 0.2)

def sub(sym, t0, bars, level):
    t = np.arange(int((bars * E.BAR + 0.5) * SR)) / SR
    f = 440 * 2 ** ((root(sym, 1) - 69) / 12)
    E.mix.add('synth', np.sin(2 * np.pi * f * t) * np.minimum(1, t / 0.05) * np.clip((t[-1] - t) / 0.4, 0, 1) * level * 0.35, t0)

def kick(t, v):
    n = int(0.45 * SR); tt = np.arange(n) / SR
    freq = 45 + 75 * np.exp(-tt * 30)
    body = np.sin(2 * np.pi * np.cumsum(freq) / SR) * np.exp(-tt * 7)
    E.mix.add('perc', body * 0.55 * v, t)

def hat(t, v):
    n = int(0.05 * SR); rng = np.random.default_rng(int(t * 1000))
    x = ss.sosfilt(ss.butter(2, 7000, 'high', fs=SR, output='sos'), rng.normal(0, 1, n)) * np.exp(-np.arange(n) / (0.012 * SR))
    E.mix.add('perc', x * 0.07 * v, t, pan=0.3)

def clap(t, v):
    n = int(0.2 * SR); rng = np.random.default_rng(int(t * 1000) + 7)
    x = ss.sosfilt(ss.butter(2, [900, 3200], 'band', fs=SR, output='sos'), rng.normal(0, 1, n))
    env = sum(np.exp(-np.clip(np.arange(n) - k * 0.011 * SR, 0, None) / (0.02 * SR)) * (np.arange(n) >= k * 0.011 * SR)
              for k in range(3)) * np.exp(-np.arange(n) / (0.09 * SR))
    E.mix.add('perc', x * env * 0.12 * v, t, pan=-0.1)

def beat(bar, v, hats=False, claps=False):
    kick(T(bar), v); kick(T(bar, 2.5), v * 0.8)
    if claps:
        clap(T(bar, 1), v); clap(T(bar, 3), v)
    if hats:
        for j in range(8):
            hat(T(bar, j * 0.5), v * (1.0 if j % 2 else 0.6))

def intro():
    pad('Fmaj7', T(-2), 6, 450, 0.6)
    for (bar, bt, _), m in zip(E.MAP_NODES, [84, 88, 81, 91, 86, 93, 84, 89, 96, 88, 91, 100]):
        keys(m, T(bar, bt), 0.2, echoes=2)
    for b in range(0, 4):
        motif(b, at(b), 0.26, sparse=True)

def arrival():
    for b in range(4, 9):
        motif(b, at(b), 0.34)
        pad(at(b), T(b), 1, 650, 0.8)

def questions():
    for i, b in enumerate(range(9, 17)):
        ramp = i / 7
        sym = at(b) if b < 16 else 'C'
        motif(b, sym, 0.4 + 0.15 * ramp)
        pad(sym, T(b), 1, 800 + 1800 * ramp, 0.9 + 0.3 * ramp)
        beat(b, 0.4 + 0.4 * ramp, hats=b >= 13)
        if b >= 11:
            chord(vla, 'strings', b, ch(sym, 3)[1:3], vel=0.3 + 0.25 * ramp, atk=0.8)
            sub(sym, T(b), 1, 0.4 + 0.3 * ramp)
    E.riser(T(17), 4.0, 0.6)

def breath():
    """The pulse drops out. Piano and pad, the filter closing back down."""
    for b, sym in [(17, 'Bbmaj7'), (18, 'Fmaj7'), (19, 'C')]:
        motif(b, sym, 0.3, sparse=b != 19)
        pad(sym, T(b), 1, 600, 0.8)
    field_beds()

def summit():
    top = [(0, 81, 4), (4, 79, 4), (8, 77, 4), (12, 76, 4)]  # a long, high string line over the cycle
    for i, b in enumerate(range(20, 24)):
        sym = at(b)
        motif(b, sym, 0.6, octave=5); motif(b, sym, 0.45, octave=4)
        pad(sym, T(b), 1, 4200, 1.3)
        sub(sym, T(b), 1, 0.8)
        beat(b, 1.0, hats=True, claps=True)
        chord(vc, 'strings', b, [root(sym, 2), root(sym, 3)], vel=0.65)
        chord(vla, 'strings', b, ch(sym, 4)[:2], vel=0.6)
    line(vln, 'strings', 20, top, 0.75, gain=1.0, atk=0.3)
    pad('C', T(24), 1, 5000, 1.4); sub('C', T(24), 1, 0.9)
    motif(24, 'C', 0.7, octave=5)
    for j in range(8):
        kick(T(24, j * 0.5), 0.4 + 0.07 * j)
    E.riser(T(25), 3.5, 0.9)
    pad('F', T(25), 1.2, 6000, 1.8, octave=3); pad('F', T(25), 1.2, 6000, 1.2, octave=4)   # the title: the filter wide open
    sub('F', T(25), 1, 1.2); kick(T(25), 1.3)
    for m in ch('F', 2) + ch('F', 4):
        note(piano, 'piano', m, T(25), E.BAR, 0.75, rel=0.8)
    chord(vln, 'strings', 25, ch('F', 5), vel=0.85, atk=0.05, rel=0.6)
    chord(vc, 'strings', 25, [41, 53], vel=0.85, atk=0.05, rel=0.6)

def coda():
    coda_fire()
    keys(77, T(26) + 0.35, 0.3)
    for m in ch('Bbmaj7', 3):
        keys(m, T(27), 0.22, echoes=2)
    pad('Bbmaj7', T(27), 1, 500, 0.5)
    for b, sym in [(28, 'Fmaj7'), (29, 'C/E')]:
        motif(b, sym, 0.3)
        pad(sym, T(b), 1, 600, 0.6)
    pad('Dm7', T(30), 1, 550, 0.6)
    for m in ch('Dm7', 3):
        keys(m, T(30), 0.24, echoes=1)
    pad('Bbmaj7', T(31), 2, 700, 0.7)                         # ends open, on the fourth
    for i, m in enumerate(ch('Bbmaj7', 4) + [81]):
        keys(m, T(31) + 0.5 + i * 0.35, 0.24, echoes=2)

if __name__ == '__main__':
    E.render(sys.argv[1] if len(sys.argv) > 1 else 'arnalds.wav', [intro, arrival, questions, breath, summit], [coda], rt=3.0)
