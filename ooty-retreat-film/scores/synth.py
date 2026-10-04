"""Sounds the sample library does not have, made in code: plucked guitar, electric piano, soft pad, crackle, dusty drums."""
import numpy as np, scipy.signal as ss
import score as E
from score import SR

def hz(m):
    return 440 * 2 ** ((m - 69) / 12)

def _log(name, m, t, dur, vel):
    E.NOTES.append((name, int(m), t, dur, vel))           # synthesized notes go in the .mid export too

def _env(n, atk, rel_at, rel):
    t = np.arange(n) / SR
    return np.minimum(1, t / max(atk, 1e-3)) * np.clip(1 - (t - rel_at) / rel, 0, 1)

def pluck(m, t, dur, vel, bus='harp', bright=0.5, pan=0.0, decay=0.996):
    """Karplus-Strong string: a noise burst circulating in a tuned, slightly lossy delay line. Nylon-guitar-ish."""
    _log('Guitar (plucked)', m, t, dur, vel)
    period = int(round(SR / hz(m)))
    n = int((dur + 0.4) * SR)
    rng = np.random.default_rng(int(t * 1000) + m)
    burst = ss.sosfilt(ss.butter(2, 1200 + 5000 * bright, 'low', fs=SR, output='sos'), rng.normal(0, 1, period))
    x = np.zeros(n); x[:period] = burst
    a = np.zeros(period + 2); a[0] = 1; a[period] = a[period + 1] = -0.5 * decay
    y = ss.lfilter([1.0], a, x)
    body = ss.sosfilt(ss.butter(2, [90, 400], 'band', fs=SR, output='sos'), y)
    y = (y + 0.35 * body) * _env(n, 0.002, dur, 0.4)
    E.mix.add(bus, y / (np.abs(y).max() + 1e-9) * 0.5 * vel, t, 1.0, pan)

def strum(notes, t, vel, bus='harp', spread=0.018, dur=2.5, down=True):
    for i, m in enumerate(notes if down else notes[::-1]):
        pluck(m, t + i * spread, dur, vel * (0.9 + 0.1 * (i == 0)), bus, bright=0.45, pan=-0.15 + 0.06 * i)

def epiano(m, t, dur, vel, bus='piano', pan=0.0):
    """FM electric piano: a sine carrier bent by a decaying modulator, plus the brief 'tine' ping."""
    _log('Electric piano', m, t, dur, vel)
    n = int((dur + 0.8) * SR); tt = np.arange(n) / SR
    fc = hz(m)
    index = (0.4 + 2.2 * vel) * np.exp(-tt / 0.35) + 0.15
    y = np.sin(2 * np.pi * fc * tt + index * np.sin(2 * np.pi * fc * tt))
    y += 0.12 * np.sin(2 * np.pi * fc * 14 * tt) * np.exp(-tt / 0.03)
    y *= np.exp(-tt / 2.5) * _env(n, 0.003, dur, 0.8) * (1 + 0.08 * np.sin(2 * np.pi * 4.5 * tt))
    E.mix.add(bus, y * 0.12 * vel, t, 1.0, pan)

def pad(notes, t, dur, level, bus='synth', cutoff=1800):
    """Soft pad: detuned triangles, slow in and out. Warm, not bright."""
    for m in notes:
        _log('Pad', m, t, dur, 0.4)
    n = int((dur + 2.5) * SR); tt = np.arange(n) / SR
    out = np.zeros((2, n))
    for m in notes:
        for c, det in enumerate((0.997, 1.003)):
            out[c] += ss.sawtooth(2 * np.pi * hz(m) * det * tt, 0.5)
    out = ss.sosfilt(ss.butter(2, cutoff, 'low', fs=SR, output='sos'), out)
    E.mix.add(bus, out * _env(n, 2.0, dur, 2.5) * level * 0.05 / max(1, len(notes) ** 0.5), t)

def bass(m, t, dur, vel, bus='synth'):
    _log('Bass', m, t, dur, vel)
    n = int((dur + 0.3) * SR); tt = np.arange(n) / SR
    y = np.tanh(1.5 * (np.sin(2 * np.pi * hz(m) * tt) + 0.25 * np.sin(4 * np.pi * hz(m) * tt)))
    E.mix.add(bus, y * _env(n, 0.01, dur, 0.3) * 0.22 * vel, t)

def crackle(t0, t1, level=1.0):
    """Vinyl: sparse clicks plus a faint band-limited hiss."""
    n = int((t1 - t0) * SR); rng = np.random.default_rng(11)
    x = np.zeros(n)
    idx = rng.integers(0, n, int((t1 - t0) * 25)); x[idx] = rng.normal(0, 1, len(idx)) * rng.uniform(0.2, 1, len(idx))
    x = ss.sosfilt(ss.butter(2, 1500, 'high', fs=SR, output='sos'), x)
    hiss = ss.sosfilt(ss.butter(2, [800, 6000], 'band', fs=SR, output='sos'), rng.normal(0, 1, n)) * 0.02
    E.mix.add('fx', (x * 0.25 + hiss) * _env(n, 1.0, (t1 - t0) - 1.0, 1.0) * level, t0)

def _noise(t, n):
    return np.random.default_rng(int(t * 997)).normal(0, 1, n)

def dusty_kick(t, v):
    n = int(0.4 * SR); tt = np.arange(n) / SR
    y = np.tanh(2 * np.sin(2 * np.pi * np.cumsum(50 + 60 * np.exp(-tt * 40)) / SR)) * np.exp(-tt * 9)
    E.mix.add('perc', y * 0.4 * v, t)

def dusty_snare(t, v):
    n = int(0.25 * SR); tt = np.arange(n) / SR
    noise = ss.sosfilt(ss.butter(2, [1500, 5000], 'band', fs=SR, output='sos'), _noise(t, n)) * np.exp(-tt * 18)
    tone = np.sin(2 * np.pi * 190 * tt) * np.exp(-tt * 30)
    E.mix.add('perc', (noise * 0.6 + tone * 0.4) * 0.25 * v, t, pan=0.05)

def dusty_hat(t, v):
    n = int(0.06 * SR)
    y = ss.sosfilt(ss.butter(2, 7500, 'high', fs=SR, output='sos'), _noise(t, n)) * np.exp(-np.arange(n) / (0.012 * SR))
    E.mix.add('perc', y * 0.06 * v, t, pan=0.3)

def bell(m, t, dur, vel, bus='synth', pan=0.0):
    """Glass bell: FM with an inharmonic ratio, a soft attack and a long ring."""
    _log('Glass bell', m, t, dur, vel)
    n = int((dur + 3.0) * SR); tt = np.arange(n) / SR
    fc = hz(m)
    index = 1.2 * np.exp(-tt / 0.8) + 0.1
    y = np.sin(2 * np.pi * fc * tt + index * np.sin(2 * np.pi * fc * 3.5 * tt))
    y *= np.minimum(1, tt / 0.02) * np.exp(-tt / (1.6 + dur * 0.3))
    E.mix.add(bus, y * 0.1 * vel, t, 1.0, pan)

def birdsong(t0, t1, density=0.35, level=1.0, seed=0):
    """Sparse songbird phrases: quick FM-free sine chirps sweeping up and down, far off in the trees."""
    rng = np.random.default_rng(seed)
    t = t0
    while t < t1:
        t += rng.exponential(1 / density)
        if t >= t1:
            break
        base = rng.uniform(2800, 4200)
        for k in range(int(rng.integers(2, 6))):              # one phrase: a few syllables
            n = int(rng.uniform(0.05, 0.11) * SR); tt = np.arange(n) / SR
            sweep = base * (1 + rng.uniform(-0.25, 0.35) * np.sin(np.pi * tt / tt[-1]) + rng.uniform(-0.1, 0.1) * tt / tt[-1])
            y = np.sin(2 * np.pi * np.cumsum(sweep) / SR) * np.sin(np.pi * np.arange(n) / n) ** 2
            E.mix.add('fx', y * 0.018 * level * rng.uniform(0.5, 1), t + k * rng.uniform(0.08, 0.16), 1.0, rng.uniform(-0.6, 0.6))
