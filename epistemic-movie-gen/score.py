"""Original score for the 3.0 film, rendered from VSCO-2 CE (CC0) samples.

A minor, 72 BPM, 4/4. Every visual cut in film.py is placed on this grid via T().
"""
import glob, os, re, functools
import numpy as np, soundfile as sf, librosa, scipy.signal as ss
import pyloudnorm as pyln
from pedalboard import Pedalboard, Compressor, HighpassFilter
from scipy.ndimage import maximum_filter1d

SR = 44100
BPM = 72
BEAT = 60 / BPM
BAR = 4 * BEAT
PRE = 2                                         # bars before bar 0: the world map fills in
END = (31 + PRE) * 4 * 60 / 72 + 6.33          # Fmaj9 at bar 31, then let it ring (score clock)
S = 'samples/'
ARR = os.environ.get('ARR', 'orchestral')        # orchestral | piano | harp | major | ambient
GENTLE = os.environ.get('GENTLE') == '1'           # the same score with the drama taken out (see note())
QUIET = os.environ.get('QUIET') == '1' or GENTLE or ARR in ('piano', 'ambient')   # no percussion, risers or booms

def T(bar, beat=0.0):
    """Time on the score's own grid: every note is placed here."""
    return (bar + PRE) * BAR + beat * BEAT

# bars the film holds for twice as long. The render plays each of these bars twice, back to back, so the picture gets
# breathing room without the music changing harmony. film.py and variants.py work on this stretched clock (TS).
REPEATS = [4, 5, 6, 8, 18, 19, 21, 23, 23, 29]    # a bar listed twice plays three times

def stretch(t):
    return t + BAR * sum(t >= T(b + 1) - 1e-9 for b in REPEATS)

def TS(bar, beat=0.0):
    return stretch(T(bar, beat))

END_S = END + BAR * len(REPEATS)

# the cold-open world map: nodes arrive faster and faster (bar, beat, label). Shared with film.py.
MAP_NODES = [(-2, 0.5, 'AI agents'), (-2, 2.5, 'climate tipping points'), (-1, 0.0, 'politics'), (-1, 1.5, 'jobs'),
             (-1, 2.5, 'wars'), (-1, 3.5, 'the economy'), (0, 0.0, 'journalism'), (0, 1.0, 'attention'),
             (0, 2.0, 'education'), (0, 2.75, 'water'), (0, 3.5, 'trust'), (1, 0.25, 'meaning')]

# bass drum hits (time, velocity). film.py pulses the picture on these, so they live in one place.
KICKS = ([(T(b), 0.3 + 0.3 * (b - 9) / 7) for b in range(13, 17)] + [(T(19), 0.35), (T(19, 2), 0.35)]
         + [(T(b, k), v) for b in (20, 21, 22, 23, 24) for k, v in ((0, 0.75), (2, 0.75), (3.5, 0.4))])

NOTE_RE = re.compile(r'_([A-G]#?\d)_')
VEL_ORDER = ['ppp', 'pp', 'p', 'mp', 'mf', 'f', 'ff', 'fff', 'v1', 'v2', 'v3', 'v4', 'dyn1', 'dyn2']

class Inst:
    """Nearest-sample, velocity-layered sampler. `octave` fixes VSCO's off-by-one-octave names."""
    def __init__(self, pattern, octave=0, pan=0.0, gain=1.0, pitch=None):
        """`pitch` maps sample path -> midi for sets whose file names carry no note (the organ)."""
        self.samples = {}  # midi -> {layer: [arrays]}
        for p in glob.glob(S + pattern):
            m = NOTE_RE.search(os.path.basename(p) + '_')
            if pitch is not None:
                midi = pitch.get(p)
            elif m:
                midi = librosa.note_to_midi(m.group(1)) + 12 * octave
            else:
                continue
            if midi is None:
                continue
            layer = next((v for v in VEL_ORDER[::-1] if re.search(rf'_{v}(_|\.|$)', os.path.basename(p))), 'v1')
            self.samples.setdefault(midi, {}).setdefault(layer, []).append(p)
        assert self.samples, pattern
        self.keys = np.array(sorted(self.samples))
        self.pan, self.gain = pan, gain
        parts = pattern.split('/')
        self.name = ' '.join(parts[:-1]) + (' pedal' if 'Pedal' in parts[-1] else '')   # the MIDI track name
        self.rr = 0

    def pick(self, midi, vel):
        k = int(self.keys[np.argmin(np.abs(self.keys - midi))])
        layers = sorted(self.samples[k], key=VEL_ORDER.index)
        layer = layers[min(len(layers) - 1, int(vel * len(layers)))]
        paths = self.samples[k][layer]
        self.rr += 1
        return k, paths[self.rr % len(paths)]

@functools.lru_cache(maxsize=None)
def load(path):
    y, sr = sf.read(path, dtype='float32', always_2d=True)
    y = y.T
    if y.shape[0] == 1:
        y = np.vstack([y, y])
    if sr != SR:
        y = librosa.resample(y, orig_sr=sr, target_sr=SR)
    a = np.abs(y).max(0)
    start = max(0, int(np.argmax(a > a.max() * 0.02)) - int(0.004 * SR))  # trim pre-roll so notes land on the grid
    y = y[:, start:]
    return y / (np.abs(y).max() + 1e-9)

@functools.lru_cache(maxsize=None)
def shifted(path, semis):
    y = load(path)
    if semis == 0:
        return y
    return librosa.resample(y, orig_sr=SR * 2 ** (semis / 12), target_sr=SR, res_type='soxr_hq')

class Mix:
    def __init__(self):
        self.buses = {}

    def bus(self, name):
        if name not in self.buses:
            self.buses[name] = np.zeros((2, int(END * SR) + SR * 8), np.float32)
        return self.buses[name]

    def add(self, bus, sig, t, gain=1.0, pan=0.0):
        b = self.bus(bus)
        i = int(t * SR)
        if i < 0:                                   # a sound that starts before the film: keep only what falls inside
            sig, i = sig[..., -i:], 0
        if i >= b.shape[1]:
            return
        n = min(sig.shape[-1], b.shape[1] - i)
        l, r = np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4)
        sig = sig if sig.ndim == 2 else np.vstack([sig, sig])
        b[0, i:i + n] += sig[0, :n] * gain * l * 1.414
        b[1, i:i + n] += sig[1, :n] * gain * r * 1.414

mix = Mix()

NOTES = []                                              # (instrument, midi, start, duration, velocity) for the .mid export

def note(inst, bus, midi, t, dur, vel=0.6, atk=0.005, rel=0.6, gain=1.0):
    if inst in SILENT:
        return
    if GENTLE:                                       # never at full force, and sustained strings/horns swell in softly
        vel = min(vel, 0.62)
        if inst in (vln, vla, vc, cb, horn) and atk < 0.2:
            atk = 0.2
    NOTES.append((inst.name, int(midi), t, dur, vel))
    k, path = inst.pick(midi, vel)
    y = shifted(path, int(midi - k))
    n = min(y.shape[1], int((dur + rel) * SR))
    y = y[:, :n].copy()
    env = np.ones(n, np.float32)
    a = max(1, int(atk * SR)); env[:a] = np.linspace(0, 1, a)
    d = int(dur * SR)
    if d < n:
        env[d:] *= np.exp(-np.arange(n - d) / (rel * SR / 6.9))
    mix.add(bus, y * env, t, gain * inst.gain * (0.25 + 0.75 * vel ** 1.4), inst.pan)

# ---------------------------------------------------------------- instruments
piano = Inst('Keys/Upright Nr1/*.wav', 0, 0.0, 0.9)
vln = Inst('Strings/Violin Section/susVib/*.wav', 1, -0.35, 0.55)
vla = Inst('Strings/Viola Section/susvib/*.wav', 1, 0.15, 0.5)
vc = Inst('Strings/Cello Section/susvib/*.wav', 1, 0.35, 0.6)
cb = Inst('Strings/Solo Contrabass/SusVib/*.wav', 1, 0.25, 0.55)
vln_sp = Inst('Strings/Violin Section/Spic/*.wav', 1, -0.3, 0.35)
vc_sp = Inst('Strings/Cello Section/spic/*.wav', 1, 0.3, 0.4)
horn = Inst('Brass/F Horn/sus/*.wav', 1, -0.15, 0.2 if QUIET else 0.45)
harp = Inst('Strings/Harp/*.wav', 0, -0.4, 0.45)

if GENTLE:                                               # the driving figures and the horns step back
    vln_sp.gain *= 0.55; vc_sp.gain *= 0.6; horn.gain *= 0.6

SILENT = {'piano': {vln, vla, vc, cb, vln_sp, vc_sp, horn}, 'ambient': {vln_sp, vc_sp}}.get(ARR, set())
LEAD = piano if ARR == 'piano' else vln                  # who sings the theme in acts III and IV

AM, F, C, G, EM = 'Am', 'F', 'C', 'G', 'Em'
ROOT = {AM: 45, F: 41, C: 48, G: 43, EM: 40}             # cello register
ARP = {AM: [64, 69, 72], F: [60, 65, 69], C: [64, 67, 72], G: [62, 67, 71], EM: [64, 67, 71]}
PAD = {AM: [57, 64], F: [57, 60], C: [55, 64], G: [55, 62], EM: [55, 59]}
TOP = {AM: [69, 76, 72, 76], F: [65, 72, 69, 72], C: [67, 76, 72, 76], G: [67, 74, 71, 74], EM: [67, 76, 71, 76]}
if ARR == 'major':                                       # Am F C G becomes C G Am F: same melody, hopeful harmony
    for d in (ROOT, ARP, PAD, TOP):
        d[AM], d[C], d[F], d[G] = d[C], d[AM], d[G], d[F]
# theme over a 4-bar Am F C G phrase: (beat offset, midi, beats)
THEME = [(0, 76, 2), (2, 74, 1), (3, 72, 1), (4, 72, 3), (7, 69, 1),
         (8, 67, 2), (10, 69, 1), (11, 72, 1), (12, 71, 3), (15, 74, 1)]

def ostinato(bar, chord, vel, lh=True):
    """Felt-piano 3+3+2 figure: the heartbeat of the film."""
    a = ARP[chord]
    if ARR == 'ambient':                                 # no pulse: three slow harp notes and a held root
        for i, m in enumerate((a[0], a[2], a[1])):
            note(harp, 'harp', m, T(bar, i * 1.5), 2.0, vel * 0.8, rel=2.5)
        note(piano, 'piano', ROOT[chord], T(bar), BAR * 0.95, vel * 0.6, rel=1.5)
        return
    inst, bus = (harp, 'harp') if ARR == 'harp' else (piano, 'piano')
    fig = [a[0], a[1], a[2], a[0], a[1], a[2], a[0], a[1]]
    for i, m in enumerate(fig):
        acc = 1.0 if i in (0, 3, 6) else 0.82
        note(inst, bus, m, T(bar, i * 0.5), 0.45, vel * acc * (1.3 if inst is harp else 1.0), rel=0.9)
    if lh:
        note(piano, 'piano', ROOT[chord], T(bar), BAR * 0.95, vel * 0.8, rel=1.2)

def theme(inst, bus, bar0, octave, vel, gain=1.0, legato=1.0):
    for off, m, beats in THEME:
        note(inst, bus, m + 12 * octave, T(bar0, off), beats * BEAT * legato, vel, atk=0.06, rel=0.5, gain=gain)

def sustain(inst, bus, bar, notes, bars=1, vel=0.5, atk=0.25, rel=1.2, gain=1.0):
    for m in notes:
        note(inst, bus, m, T(bar) - 0.03, bars * BAR, vel, atk=atk, rel=rel, gain=gain)

# ---------------------------------------------------------------- sound design (synthesis + field audio)
def drone(t0, t1, level):
    """Sub A with slow breathing, felt more than heard."""
    n = int((t1 - t0) * SR); t = np.arange(n) / SR
    sig = np.sin(2 * np.pi * 55 * t) + 0.5 * np.sin(2 * np.pi * 110.3 * t) + 0.25 * np.sin(2 * np.pi * 164.8 * t)
    env = np.minimum(1, t / 3.0) * np.minimum(1, (t1 - t0 - t) / 1.5) * (0.8 + 0.2 * np.sin(2 * np.pi * t / 6.5))
    rng = np.random.default_rng(3)
    air = ss.sosfilt(ss.butter(2, [250, 1800], 'band', fs=SR, output='sos'), rng.normal(0, 1, n)) * 0.35
    mix.add('fx', (sig * 0.5 + air) * env * level, t0)

def reverse_swell(path_midi, t_end, dur, gain):
    k, p = piano.pick(path_midi, 0.7)
    y = shifted(p, path_midi - k)[:, :int(dur * SR)][:, ::-1].copy()
    y *= np.linspace(0, 1, y.shape[1]) ** 2
    mix.add('piano', y, t_end - dur, gain)

def riser(t_end, dur, gain):
    """Reversed suspended cymbal + upward noise sweep, landing exactly on t_end."""
    if QUIET:
        return
    y = load(S + 'VSCO 1 Percussion/varMetal/Cymbals/susp/susp_hit_hardmall_f.wav')[:, :int(dur * SR)][:, ::-1].copy()
    y *= np.linspace(0, 1, y.shape[1]) ** 1.5
    mix.add('perc', y, t_end - y.shape[1] / SR, gain)
    n = int(dur * SR); rng = np.random.default_rng(9)
    noise = rng.normal(0, 1, n).astype(np.float32); out = np.zeros(n, np.float32)
    for i, s in enumerate(range(0, n, 2048)):
        fc = 300 * (40 ** (s / n))
        sos = ss.butter(2, [fc * 0.7, min(fc * 1.4, 18000)], 'band', fs=SR, output='sos')
        out[s:s + 2048] = ss.sosfilt(sos, noise[s:s + 2048])
    out *= np.linspace(0, 1, n) ** 2.5
    mix.add('fx', out * 0.08 * gain, t_end - dur)

def boom(t, gain):
    if QUIET:
        return
    for p, g in [('Percussion/BDrumNewhit_v6_rr1_Sum.wav', 0.9), ('Percussion/Timpani/Timpani1_Hit_v3_rr1_Sum.wav', 0.6),
                 ('VSCO 1 Percussion/varMetal/Gong/gong_hit_ff.wav', 0.55)]:
        if os.path.exists(S + p):
            mix.add('perc', load(S + p), t, g * gain)
    n = int(3.0 * SR); tt = np.arange(n) / SR
    f = 28 + 52 * np.exp(-tt * 3.5)
    sub = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * 1.3)
    mix.add('fx', sub * 0.8 * gain, t)

TIMP = sorted(glob.glob(S + 'Percussion/Timpani/Timpani*_Hit_v*_Sum.wav'))
def timp(t, vel):
    if QUIET:
        return
    layer = [p for p in TIMP if ('_v1_' in p) == (vel < 0.5)] or TIMP
    mix.add('perc', load(layer[int(t * 7) % len(layer)]), t, 0.25 + 0.6 * vel)

BD = sorted(glob.glob(S + 'Percussion/BDrumNewhit_v*_rr*_Sum.wav'))
def kick(t, vel):
    if QUIET:
        return
    idx = min(len(BD) - 1, int(vel * len(BD)))
    mix.add('perc', load(BD[idx]), t, 0.3 + 0.5 * vel)

def field(path, t, dur, gain, seg=0.45, seed=0):
    """Granular re-weave of a short phone recording into a longer bed (fire, room)."""
    y = load(path); n = int(dur * SR); out = np.zeros((2, n), np.float32)
    g = int(seg * SR); hop = g // 2; win = np.hanning(g).astype(np.float32)
    rng = np.random.default_rng(seed)
    for s in range(0, n - g, hop):
        src = rng.integers(0, y.shape[1] - g)
        out[:, s:s + g] += y[:, src:src + g] * win
    fade = np.minimum(1, np.minimum(np.arange(n), n - np.arange(n)) / (0.8 * SR))
    mix.add('field', out * fade, t, gain)

def rain(t0, t1, gain):
    n = int((t1 - t0) * SR); rng = np.random.default_rng(4)
    w = rng.normal(0, 1, (2, n)).astype(np.float32)
    bed = ss.sosfilt(ss.butter(2, [500, 7000], 'band', fs=SR, output='sos'), w) * 0.2
    drops = np.zeros((2, n), np.float32)
    for _ in range(int((t1 - t0) * 45)):
        i = rng.integers(0, n - 800); ch = rng.integers(0, 2)
        drops[ch, i:i + 800] += rng.normal(0, 1, 800) * np.exp(-np.arange(800) / 60) * rng.uniform(0.2, 1)
    drops = ss.sosfilt(ss.butter(2, 1500, 'high', fs=SR, output='sos'), drops) * 0.25
    env = np.minimum(1, np.minimum(np.arange(n), n - np.arange(n)) / (1.5 * SR))
    mix.add('field', (bed + drops) * env, t0, gain)

def act1():
    # ACT I - the world map fills in, then: most of us make sense of it alone (bars -2..3).
    drone(0.0, T(4) + 0.5, 0.05)
    pings = [81, 84, 76, 79, 88, 83, 86, 81, 91, 88, 84, 93]          # A minor pentatonic, high and soft
    for (bar, beat, _), m in zip(MAP_NODES, pings):
        note(harp, 'harp', m, T(bar, beat), 1.5, 0.22, rel=2.5, gain=0.8)
    for t, m in [(T(0, 1), 76), (T(0, 3), 74), (T(1, 1), 72)]:
        note(piano, 'piano', m, t, 1.6, 0.34, rel=2.0)
    note(piano, 'piano', 45, T(1, 1), 3.0, 0.22, rel=2.5)
    sustain(vc, 'strings', 2, [45], bars=2, vel=0.25, atk=1.2, rel=2.0, gain=0.7)
    for m in (57, 64):
        note(piano, 'piano', m, T(2), 3.0, 0.26, rel=2.0)
    note(piano, 'piano', 71, T(2, 3), 2.0, 0.26, rel=2.0)
    note(piano, 'piano', 81, T(3, 1), 3.0, 0.30, rel=3.0)            # "We'd rather do it together."
    reverse_swell(69, T(4), 2.2, 0.35)

def act2():
    # ACT II - the mist (bars 4-8). Ostinato enters with the paper; harp draws the map.
    for b, ch, v in [(4, AM, 0.38), (5, F, 0.40), (6, C, 0.43), (7, G, 0.46), (8, F, 0.5)]:
        ostinato(b, ch, v)
    for i, m in enumerate([57, 60, 64, 69, 72, 76, 81]):
        note(harp, 'harp', m, T(4) + i * 0.09, 2.5, 0.5, rel=2.5)
    sustain(vln, 'strings', 5, [76, 81], bars=2, vel=0.2, atk=1.5, rel=2.0, gain=0.6)   # photo emerges from the map
    sustain(vc, 'strings', 6, [48], vel=0.35); sustain(vc, 'strings', 7, [43], vel=0.38)
    sustain(vc, 'strings', 8, [41], vel=0.42); sustain(vla, 'strings', 8, PAD[F], vel=0.35, atk=0.8)
    sustain(vln, 'strings', 8, [72], vel=0.3, atk=1.5)

def act3():
    # ACT III - the questions (bars 9-16). Spiccato engine, theme in violins, timpani.
    prog = [AM, F, C, G, AM, F, C, G]
    for i, ch in enumerate(prog):
        b = 9 + i; ramp = i / 7
        ostinato(b, ch, 0.5 + 0.12 * ramp)
        sustain(vc, 'strings', b, [ROOT[ch]], vel=0.45 + 0.2 * ramp)
        sustain(vla, 'strings', b, PAD[ch], vel=0.35 + 0.25 * ramp, atk=0.2)
        if i >= 2:
            sustain(cb, 'strings', b, [ROOT[ch] - 12], vel=0.4 + 0.2 * ramp)
        step, v = (0.5, 0.42 + 0.1 * ramp) if i < 4 else (0.25, 0.5 + 0.3 * ramp)
        top = TOP[ch]
        for j in range(int(4 / step)):
            note(vln_sp, 'strings', top[j % 4], T(b, j * step), step * BEAT, v * (1.0 if j % 2 == 0 else 0.8), rel=0.15)
        if i >= 4:
            for j in range(8):
                note(vc_sp, 'strings', ROOT[ch], T(b, j * 0.5), 0.4, 0.45 + 0.25 * ramp, rel=0.15)
        if i >= 2:
            timp(T(b), 0.35 + 0.4 * ramp)
        if i >= 4:
            timp(T(b, 2), 0.3 + 0.35 * ramp)
    theme(LEAD, 'piano' if LEAD is piano else 'strings', 13, 0, 0.55, gain=0.9)
    sustain(horn, 'brass', 15, [60, 64], vel=0.35, atk=0.6); sustain(horn, 'brass', 16, [59, 62], vel=0.5, atk=0.6)
    for j in range(8):
        timp(T(16, 2 + j * 0.25), 0.3 + 0.07 * j)
    riser(T(17), 4.0, 0.9)

def act4():
    # ACT IV - the body (bars 17-25). Breath in the rain, the whole theme over the night, then everything.
    rain(T(17) - 0.2, T(20) + 1.0, 0.07)
    for b, ch, v in [(17, F, 0.34), (18, C, 0.36), (19, G, 0.42)]:
        ostinato(b, ch, v)
        sustain(vla, 'strings', b, PAD[ch], vel=0.22, atk=0.8, gain=0.7)
    sustain(vln, 'strings', 18, [79], bars=2, vel=0.2, atk=1.5, gain=0.5)
    sustain(vc, 'strings', 19, [43], vel=0.45, atk=0.5)
    for j in range(8):
        note(vc_sp, 'strings', 43, T(19, j * 0.5), 0.4, 0.3 + 0.04 * j, rel=0.15)
    riser(T(20), 2.5, 0.5)
    for t, v in KICKS:
        kick(t, v)
    for b, ch in [(20, AM), (21, F), (22, C), (23, EM), (24, G)]:
        ostinato(b, ch, 0.62)
        sustain(vc, 'strings', b, [ROOT[ch], ROOT[ch] + 12], vel=0.7)
        sustain(cb, 'strings', b, [ROOT[ch] - 12], vel=0.7)
        sustain(vla, 'strings', b, PAD[ch], vel=0.6, atk=0.15)
        sustain(horn, 'brass', b, [PAD[ch][0], PAD[ch][1]], vel=0.6, atk=0.3)
        for j in range(16):
            note(vln_sp, 'strings', TOP[ch][j % 4] + 12 * (j % 8 == 0), T(b, j * 0.25), 0.2, 0.7 * (1 if j % 2 == 0 else 0.8), rel=0.12)
        for k in (0, 2):
            timp(T(b, k), 0.8)
    for off, m, beats in THEME:                                        # the theme, finally sung out, all of it
        note(LEAD, 'piano' if LEAD is piano else 'strings', m + 12, T(20, off), beats * BEAT, 0.8, atk=0.05, rel=0.4, gain=1.1)
        note(horn, 'brass', m - 12, T(20, off), beats * BEAT, 0.7, atk=0.05, rel=0.4, gain=0.8)
    note(vln, 'strings', 83, T(24), 2 * BEAT, 0.85, atk=0.05, gain=1.1); note(vln, 'strings', 86, T(24, 2), 2 * BEAT, 0.9, atk=0.05, gain=1.1)
    for j in range(16):
        timp(T(24, 2 + j * 0.125), 0.4 + 0.035 * j)
    riser(T(25), 3.5, 1.2)
    field('clips/IMG_1289.wav', T(20) - 0.3, 7.5, 0.25, seed=1)
    field('clips/IMG_1296.wav', T(19) - 0.2, 3.6, 1.2, seed=2)
    title_hit()

def title_hit():
    # the title hit (bar 25): C major, everything at once
    boom(T(25), 1.0)
    full = [36, 48, 55, 60, 64, 67, 72, 76, 79, 84]
    for m in full:
        inst = vln if m >= 67 else vla if m >= 55 else vc
        note(inst, 'strings', m, T(25), BAR * 0.9, 0.85, atk=0.02, rel=0.5, gain=0.9)
    for m in (24, 36, 48):
        note(cb if m < 36 else vc, 'strings', m + 12 if m == 24 else m, T(25), BAR * 0.9, 0.9, atk=0.02, rel=0.5)
    sustain(horn, 'brass', 25, [55, 60, 64], vel=0.85, atk=0.02, rel=0.5)
    for m in (24, 36, 43, 48):
        note(piano, 'piano', m, T(25), BAR, 0.9, rel=0.5)

def act5():
    # ACT V - the invitation (bars 26-31). Silence, then the theme alone under the title card.
    field('clips/IMG_1289.wav', T(26), 6.0, 0.07, seed=3)
    note(piano, 'piano', 69, T(26) + 0.35, 2.5, 0.28, rel=2.5)
    for m in (41, 57, 60, 69):
        note(piano, 'piano', m, T(27), 3.0, 0.26, rel=2.5)
    for off, m, beats in THEME[:8]:
        note(piano, 'piano', m, T(28, off), beats * BEAT, 0.34, rel=1.5)
    for b, m in [(28, 45), (29, 41)]:
        note(piano, 'piano', m, T(b), BAR, 0.24, rel=1.5)
        sustain(vc, 'strings', b, [m], vel=0.25, atk=0.8, gain=0.6)
    for m in (43, 59, 62, 71):                                         # "Come think with us." hangs on G
        note(piano, 'piano', m, T(30), BAR, 0.3, rel=2.0)
    sustain(vla, 'strings', 30, [55, 62], vel=0.22, atk=1.0, gain=0.6)
    for m in (29, 41, 48, 57, 64, 67):                                  # ...and opens onto Fmaj9, unresolved
        note(piano, 'piano', m + (12 if m == 29 else 0), T(31), 5.5, 0.3, rel=3.0)
    sustain(vc, 'strings', 31, [41], bars=1.6, vel=0.3, atk=1.0, rel=2.5, gain=0.6)
    sustain(vln, 'strings', 31, [76, 81], bars=1.6, vel=0.2, atk=1.5, rel=2.5, gain=0.5)
    for i, m in enumerate([65, 69, 72, 76, 79, 81]):
        note(harp, 'harp', m, T(31) + 0.9 + i * 0.11, 3.0, 0.35, rel=3.0)

# ---------------------------------------------------------------- mixdown
def hall_ir(rt=2.8, seed=0):
    rng = np.random.default_rng(seed)
    n = int(rt * 1.3 * SR); t = np.arange(n) / SR
    ir = np.zeros((2, n), np.float32)
    bands = [(20, 250, rt * 1.2), (250, 1000, rt), (1000, 4000, rt * 0.75), (4000, 16000, rt * 0.45)]
    for ch in range(2):
        w = rng.normal(0, 1, n)
        for lo, hi, r in bands:
            sos = ss.butter(2, [lo, hi], 'band', fs=SR, output='sos')
            ir[ch] += ss.sosfilt(sos, w) * np.exp(-6.9 * t / r)
        for _ in range(14):                                   # sparse early reflections
            i = int(rng.uniform(0.008, 0.07) * SR); ir[ch, i] += rng.uniform(0.3, 0.7) * rng.choice([-1, 1])
    pre = int(0.022 * SR)
    ir = np.concatenate([np.zeros((2, pre), np.float32), ir], 1)
    return ir / np.sqrt((ir ** 2).sum() / 2)

SENDS = {'piano': 0.32, 'strings': 0.42, 'brass': 0.45, 'harp': 0.5, 'perc': 0.3, 'fx': 0.15, 'field': 0.1,
         'organ': 0.4, 'synth': 0.3, 'winds': 0.45}
LEVELS = {'piano': 1.0, 'strings': 0.9, 'brass': 0.8, 'harp': 0.7, 'perc': 0.85, 'fx': 0.9, 'field': 0.9,
          'organ': 0.8, 'synth': 0.8, 'winds': 0.85}

def bounce(buses, ir, n):
    """Buses -> stereo with the shared hall."""
    dry = np.zeros((2, n), np.float32); wet_in = np.zeros((2, n), np.float32)
    for name, b in buses.items():
        b = b[:, :n] * LEVELS[name]
        if name == 'piano':                                   # felt piano: soften the hammer
            b = ss.sosfilt(ss.butter(2, 3200, 'low', fs=SR, output='sos'), b).astype(np.float32)
        dry += b; wet_in += b * SENDS[name]
    wet = np.stack([ss.oaconvolve(wet_in[c], ir[c])[:n] for c in range(2)]).astype(np.float32)
    return dry + wet * 0.55

# master fader: the arc of the film in dB (time, gain); Act V is mixed separately after the drop
FADER = [(0, 0), (T(4), -8), (T(8), -6), (T(9), -6), (T(13), -3), (T(16, 3), 0), (T(17), -1), (T(20), 0), (T(25), 1.5)]

def limit(y, ceiling_db=-1.2, look=0.004, release=0.12):
    """Look-ahead peak limiter: gain follows the upcoming peak, recovers exponentially."""
    c = 10 ** (ceiling_db / 20)
    peak = maximum_filter1d(np.abs(y).max(0), size=int(look * SR) * 2 + 1)
    want = np.minimum(1.0, c / (peak + 1e-9))
    a = np.exp(-1 / (release * SR))
    g = ss.lfilter([1 - a], [1, -a], want - 1) + 1          # smooth recovery
    g = np.minimum(g, want)                                 # never exceed the instantaneous need
    return (y * g).astype(np.float32)

def repeat_bars(y, xfade=0.025):
    """Play each REPEATS bar twice. At the jump back, the original's continuation fades out under the copy's start,
    so the output is exactly one bar longer per repeat. The copy ends where the original continues: seamless."""
    out, prev, n = [], 0, int(xfade * SR)
    ramp = np.linspace(0, 1, n, dtype=np.float32)
    for b in sorted(REPEATS):
        s0, s1 = int(T(b) * SR), int(T(b + 1) * SR)
        copy = y[:, s0:s1].copy()
        copy[:, :n] = y[:, s1:s1 + n] * (1 - ramp) + copy[:, :n] * ramp
        out += [y[:, prev:s1], copy]
        prev = s1
    out.append(y[:, prev:])
    return np.concatenate(out, axis=1)

def write_midi(path):
    """Every sampled note, on the film's clock (repeated bars included), one track per instrument."""
    import pretty_midi
    pm = pretty_midi.PrettyMIDI(initial_tempo=BPM)
    tracks = {}
    for name, midi, t, dur, vel in NOTES:
        copies = sum(T(b) <= t < T(b + 1) for b in REPEATS)
        starts = [stretch(t) + j * BAR for j in range(copies + 1)]
        tr = tracks.setdefault(name, pretty_midi.Instrument(program=0, name=name))
        for s0 in starts:
            tr.notes.append(pretty_midi.Note(int(20 + 107 * min(1.0, vel)), midi, s0, s0 + max(0.05, dur)))
    pm.instruments = list(tracks.values())
    pm.write(path)

# a gentle arc for the undramatic scores: no swell into the title, no plunge after it
CALM_FADER = [(0, -1), (T(4), -3), (T(9), -2), (T(17), -3), (T(20), -1), (T(25), -1)]

def render(out=os.environ.get('MUSIC_OUT', 'music.wav'), main_acts=None, coda_acts=None, rt=2.8, calm=False):
    """Acts before the drop are gated to silence at bar 26. Coda acts sound after it. Defaults: this file's score."""
    global mix
    calm = calm or GENTLE
    n = int(END * SR); ir = hall_ir(rt)
    mix = Mix()
    for act in main_acts or (act1, act2, act3, act4):
        act()
    main = bounce(mix.buses, ir, n)
    mix = Mix()
    for act in coda_acts or (act5,):
        act()
    coda = bounce(mix.buses, ir, n)
    t = np.arange(n) / SR
    fader = 10 ** (np.interp(t, *zip(*(CALM_FADER if calm else FADER))) / 20)
    # the drop: gate everything before Act V, reverb included. Calm scores fade out over a bar instead of cutting.
    g = np.ones(n, np.float32); a, b = int((T(26) - (BAR if calm else 0.3)) * SR), int(T(26) * SR)
    g[a:b] = np.linspace(1, 0, b - a) ** 2; g[b:] = 0
    y = main * fader * g + coda * 0.8
    y = Pedalboard([HighpassFilter(30), Compressor(threshold_db=-22, ratio=1.2 if calm else 1.6, attack_ms=30, release_ms=300)])(y, SR)
    meter = pyln.Meter(SR)
    lufs = meter.integrated_loudness(y.T)
    y = limit(y * 10 ** ((-14.5 - lufs) / 20))
    y = repeat_bars(y)
    k = int(2.5 * SR); y[:, -k:] *= np.linspace(1, 0, k) ** 2
    sf.write(out, y.T, SR, subtype='PCM_24')
    write_midi(out.rsplit('.', 1)[0] + '.mid')
    print(f'wrote {out}: {lufs:.1f} -> {meter.integrated_loudness(y.T):.1f} LUFS, peak {20*np.log10(np.abs(y).max()):.1f} dBFS')
    bars = [meter.integrated_loudness(y[:, int(T(i) * SR):int(T(i + 1) * SR)].T) for i in range(30)]
    print('per-bar LUFS:', ' '.join(f'{i}:{v:.0f}' for i, v in enumerate(bars)))

if __name__ == '__main__':
    render()
