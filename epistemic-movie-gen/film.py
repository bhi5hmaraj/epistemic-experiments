"""Ooty Alignment Retreat 3.0 - the film. Every frame is computed here and piped to ffmpeg.

Timeline lives on the music grid: T(bar, beat) from score.py (72 BPM, 4/4).
"""
import functools, glob, os, pickle, subprocess, sys
from multiprocessing import Pool
from look import *
from score import TS as T, END_S as END, BAR, BEAT, MAP_NODES

FPS = 24
STYLE = os.environ.get('STYLE', 'bleed')        # page look for the question spreads: clean | night | bleed
PAGE = os.environ.get('PAGE', 'dark')           # text-and-drawing scenes: dark (night ink) | light (paper)
C = 'cache/'
CREAM = (238, 232, 218)
MOON = (156, 180, 228)                          # highlight on night ink and over photos: a soft moonlight blue
PARCHMENT = np.array(PAPER_SOFT, np.float32) / 255

PAL = {
    'light': dict(ink=INK, soft=INK_SOFT, accent=BLUE, line=LINE_STRONG, idx=BLUE, faint=LINE, path=BLUE, start=INK),
    'dark': dict(ink=CREAM, soft=(150, 158, 175), accent=MOON, line=(92, 102, 124), idx=(104, 126, 176),
                 faint=(46, 54, 72), path=(140, 160, 200), start=CREAM),
}[PAGE]

def ease(x):
    x = np.clip(x, 0, 1)
    return 0.5 - 0.5 * np.cos(np.pi * x)

def lerp(a, b, x):
    return a + (b - a) * x

# ---------------------------------------------------------------- assets (lazy, cached per worker)
@functools.lru_cache(maxsize=64)
def img(name):
    return cv2.cvtColor(cv2.imread(C + name), cv2.COLOR_BGR2RGB).astype(np.float32) / 255

@functools.lru_cache(maxsize=None)
def clip(name):
    return sorted(glob.glob(C + name + '/*.jpg'))

@functools.lru_cache(maxsize=4)
def paper_bg(seed=11):
    return paper(W, H, seed)[0]

@functools.lru_cache(maxsize=1)
def grain_bank():
    rng = np.random.default_rng(5)
    return [cv2.GaussianBlur(rng.normal(0, 1, (H, W)).astype(np.float32), (0, 0), 0.9) for _ in range(6)]

@functools.lru_cache(maxsize=1)
def vignette():
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    r = np.hypot((xx - W / 2) / (W / 2), (yy - H / 2) / (H / 2))
    return (1 - 0.28 * np.clip(r - 0.35, 0, 1) ** 1.6)[..., None]

@functools.lru_cache(maxsize=1)
def contour_maps():
    return pickle.load(open(C + 'contours.pkl', 'rb'))

def page():
    return night(None) if PAGE == 'dark' else paper_bg().copy()

@functools.lru_cache(maxsize=16)
def blob(size, color, seed, alpha):
    return wash_blob(size, color, seed, alpha)

# ---------------------------------------------------------------- compositing primitives
def cover(src, z=1.0, c=(0.5, 0.5), out=(W, H)):
    """Scale-to-cover with zoom z around centre c (fractions), clamped inside the image."""
    h, w = src.shape[:2]; ow, oh = out
    s = max(ow / w, oh / h) * z
    cx = np.clip(c[0] * w, ow / (2 * s), w - ow / (2 * s))
    cy = np.clip(c[1] * h, oh / (2 * s), h - oh / (2 * s))
    M = np.float32([[s, 0, ow / 2 - s * cx], [0, s, oh / 2 - s * cy]])
    return cv2.warpAffine(src, M, out, flags=cv2.INTER_AREA if s < 1 else cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)

ZOOM_RATE = 0.006                         # zoom per second. One direction only (in), no pans: nothing to feel seasick about
FADE = 0.5                                # cross-dissolve between photos, centred on the cut

def kb(src, t, t0, t1, z=(1.0, 1.08), c0=(0.5, 0.5), c1=(0.5, 0.5), out=(W, H)):
    """A slow push-in on a fixed framing (the midpoint of c0 and c1)."""
    dur = max(1e-6, t1 - t0)
    x = float(np.clip((t - t0) / dur, 0, 1))
    zoom = z[0] + min(max(z[1] - z[0], 0.0), ZOOM_RATE * dur) * x
    return cover(src, zoom, ((c0[0] + c1[0]) / 2, (c0[1] + c1[1]) / 2), out)

def dissolve(a_fn, b_fn, t, cut):
    """Cross-fade from a to b over FADE seconds centred on `cut`. Outside that window, whichever side t is on."""
    w = ease((t - (cut - FADE / 2)) / FADE)
    if w <= 0:
        return a_fn(t)
    if w >= 1:
        return b_fn(t)
    return a_fn(t) * (1 - w) + b_fn(t) * w

def multiply(base, layer, x, y, a=1.0):
    h, w = layer.shape[:2]
    reg = base[y:y + h, x:x + w]
    reg *= 1 - a * (1 - layer[:reg.shape[0], :reg.shape[1]])

def put_blob(base, x, y, size, color, seed, alpha=0.3):
    a, col = blob(size, color, seed, alpha)
    x0, y0 = max(0, x), max(0, y); x1, y1 = min(W, x + size), min(H, y + size)
    if x1 <= x0 or y1 <= y0:
        return
    aa = a[y0 - y:y1 - y, x0 - x:x1 - x, None]
    base[y0:y1, x0:x1] *= 1 - aa * (1 - col)

@functools.lru_cache(maxsize=256)
def text_img(s, fname, size, color, tracking=0):
    """Pre-rendered text: (rgb, alpha, width, height). Tracking in px between glyphs (for mono caps)."""
    f = font(fname, size)
    asc, desc = f.getmetrics()
    w = int(f.getlength(s) + tracking * len(s)) + 8; h = asc + desc + 8
    im = Image.new('L', (w, h), 0); d = ImageDraw.Draw(im)
    if tracking:
        x = 4
        for ch in s:
            d.text((x, 4), ch, font=f, fill=255); x += f.getlength(ch) + tracking
    else:
        d.text((4, 4), s, font=f, fill=255)
    a = np.asarray(im).astype(np.float32) / 255
    return np.array(color, np.float32) / 255, a, w, h

def text(base, s, x, y, fname='Spectral-Light.ttf', size=60, color=INK, a=1.0, anchor='l', tracking=0, shadow=0.0):
    if a <= 0 or not s:
        return 0
    col, al, w, h = text_img(s, fname, size, tuple(color), tracking)
    x = int(x - (w / 2 if anchor == 'c' else w if anchor == 'r' else 0)); y = int(y)
    x0, y0 = max(0, x), max(0, y); x1, y1 = min(W, x + w), min(H, y + h)
    if x1 <= x0 or y1 <= y0:
        return w
    al = al[y0 - y:y1 - y, x0 - x:x1 - x]
    if shadow:
        sh = cv2.GaussianBlur(al, (0, 0), size / 9)[..., None] * shadow * a
        base[y0 + 3:y1 + 3, x0:x1] *= 1 - sh[:max(0, min(y1 + 3, H) - (y0 + 3))]
    base[y0:y1, x0:x1] = base[y0:y1, x0:x1] * (1 - al[..., None] * a) + col * al[..., None] * a
    return w

def appear(t, t_in, t_out=None, fade_in=0.3, fade_out=0.35):
    """Hard-ish cut in on the beat (3 frames), soft out."""
    if t < t_in:
        return 0.0
    a = min(1.0, (t - t_in) / fade_in)
    if t_out is not None:
        a *= float(np.clip((t_out - t) / fade_out, 0, 1))
    return a

def draw_contours(base, name, progress, alpha=1.0, color=None, index_color=None, index_every=4):
    """Draw the map on: each line grows from its start as progress goes 0->1, staggered by level."""
    layer = np.zeros((H, W), np.uint8); idx = np.zeros((H, W), np.uint8)
    for k, c in contour_maps()[name]:
        p = np.clip(progress * 1.6 - (k % 7) * 0.09, 0, 1)
        n = int(len(c) * p)
        if n < 2:
            continue
        tgt, th = (idx, 2) if k % index_every == 0 else (layer, 1)
        cv2.polylines(tgt, [c[:n].reshape(-1, 1, 2)], False, 255, th, cv2.LINE_AA)
    for m, col, a in ((layer, color or PAL['line'], 0.8), (idx, index_color or PAL['idx'], 0.6)):
        over(base, m, col, a * alpha)

def dotted_path(base, pts, progress, color=None, spacing=16, r=3):
    """Brand motif: a dotted route between two nodes, drawn on as progress goes 0->1."""
    pts = np.asarray(pts, np.float32)
    seg = np.hypot(*np.diff(pts, axis=0).T); cum = np.concatenate([[0], np.cumsum(seg)])
    total = cum[-1] * progress
    layer = np.zeros((H, W), np.uint8)
    for d in np.arange(0, total, spacing):
        i = min(np.searchsorted(cum, d, side='right') - 1, len(seg) - 1)
        q = pts[i] + (pts[i + 1] - pts[i]) * ((d - cum[i]) / max(seg[i], 1e-6))
        cv2.circle(layer, (int(q[0]), int(q[1])), r, 255, -1, cv2.LINE_AA)
    over(base, layer, color or PAL['path'], 1.0)

def dot(base, x, y, r, color, a=1.0):
    layer = np.zeros((H, W), np.uint8); cv2.circle(layer, (int(x), int(y)), int(r), 255, -1, cv2.LINE_AA)
    al = layer.astype(np.float32)[..., None] / 255 * a
    base[:] = base * (1 - al) + np.array(color, np.float32) / 255 * al

def ring(base, x, y, r, color, a=1.0, th=2):
    layer = np.zeros((H, W), np.uint8); cv2.circle(layer, (int(x), int(y)), int(r), 255, th, cv2.LINE_AA)
    al = layer.astype(np.float32)[..., None] / 255 * a
    base[:] = base * (1 - al) + np.array(color, np.float32) / 255 * al

@functools.lru_cache(maxsize=1)
def scrim_mask():
    y = np.linspace(0, 1, H, dtype=np.float32)
    return (np.clip((y - 0.5) / 0.5, 0, 1) ** 1.4 * 0.62)[:, None, None]

def scrim(f, a=1.0):
    """Night-ink gradient under the lower third so cream text reads over any photo."""
    night = np.array(NIGHT, np.float32) / 255
    m = scrim_mask() * a
    return f * (1 - m) + night * m

def finish(frame, t, grain=0.022, vig=False):
    g = grain_bank()[int(t * FPS) % 6][..., None]
    frame = frame * (1 + g * grain)
    if vig:
        frame = frame * vignette()
    return frame

# ---------------------------------------------------------------- scenes
def night(t):
    return np.ones((H, W, 3), np.float32) * np.array(NIGHT, np.float32) / 255

NODE_XY = [(1380, 250), (520, 300), (1560, 760), (330, 700), (1180, 170), (1700, 330), (760, 190), (1480, 430),
           (1080, 820), (1760, 620), (250, 390), (660, 860)]           # clustered on purpose: unevenly distributed
NODE_COL = [MOON, CREAM, (150, 170, 145), (140, 160, 200), CREAM, MOON, (150, 170, 145), CREAM,
            (140, 160, 200), MOON, CREAM, (150, 170, 145)]

def over(base, mask, color, a):
    al = mask.astype(np.float32)[..., None] / 255 * a
    base[:] = base * (1 - al) + np.array(color, np.float32) / 255 * al

def dots_along(layer, p, q, progress, spacing=14, r=2):
    """Dotted, gently curved route from p to q (the brand's path motif), drawn on to `progress`."""
    p, q = np.float32(p), np.float32(q)
    mid = (p + q) / 2 + np.float32([-(q - p)[1], (q - p)[0]]) * 0.18
    n = int(np.hypot(*(q - p)) / spacing)
    for i in range(int(n * progress)):
        s = i / max(n, 1)
        pt = (1 - s) ** 2 * p + 2 * (1 - s) * s * mid + s ** 2 * q
        cv2.circle(layer, (int(pt[0]), int(pt[1])), r, 255, -1, cv2.LINE_AA)

def world_map(f, t, alpha):
    """State of the world, as a map that keeps getting denser."""
    paths = np.zeros((H, W), np.uint8)
    for i, (bar, beat, _) in enumerate(MAP_NODES):
        ti = T(bar, beat)
        if t < ti or i == 0:
            continue
        d = [np.hypot(NODE_XY[i][0] - NODE_XY[j][0], NODE_XY[i][1] - NODE_XY[j][1]) for j in range(i)]
        for j in np.argsort(d)[:2]:
            dots_along(paths, NODE_XY[j], NODE_XY[i], ease((t - ti) / 0.9))
    over(f, paths, (120, 130, 150), 0.8 * alpha)
    for i, (bar, beat, label) in enumerate(MAP_NODES):
        ti = T(bar, beat)
        if t < ti:
            continue
        x, y = NODE_XY[i]; a = appear(t, ti) * alpha
        rip = (t - ti) / 1.2
        if rip < 1:
            ring(f, x, y, 8 + 38 * rip, NODE_COL[i], a * (1 - rip) * 0.8, 1)
        ring(f, x, y, 13, NODE_COL[i], a * 0.5, 1)
        dot(f, x, y, 5, NODE_COL[i], a)
        text(f, label, x + 20, y - 16, 'IBMPlexMono-Regular.ttf', 19, CREAM, a * 0.75, tracking=1)

def s_open(t):
    """ACT I - the world map fills in. Most of us make sense of it alone. We'd rather do it together."""
    f = night(t)
    dim = 1 - 0.5 * float(np.clip((t - T(0)) / 1.0, 0, 1))                   # the map steps back for the words
    world_map(f, t, dim * (1 - ease((t - T(3, 2.5)) / 1.2)))
    fn, size = 'Spectral-Light.ttf', 58
    text(f, "The future is already here.", W / 2, 440, fn, size, CREAM, appear(t, T(0, 1), T(1, 3.6)), 'c', shadow=0.8)
    text(f, "It's just not evenly distributed.", W / 2, 520, fn, size, CREAM, appear(t, T(0, 3), T(1, 3.6)), 'c', shadow=0.8)
    text(f, "WILLIAM GIBSON", W / 2, 620, 'IBMPlexMono-Regular.ttf', 18, CREAM, 0.7 * appear(t, T(1, 1.5), T(1, 3.6)), 'c',
         tracking=3)
    text(f, "Most of us are making sense of it alone.", W / 2, 440, fn, size, CREAM, appear(t, T(2), T(3, 3.4)), 'c', shadow=0.8)
    text(f, "We'd rather do it together.", W / 2, 530, 'Spectral-LightItalic.ttf', 64, MOON,
         appear(t, T(2, 3), T(3, 3.4)), 'c', shadow=0.8)
    return finish(f, t, 0.03)

def s_map(t):
    """ACT II - the map is drawn from the territory, then the territory arrives."""
    t0, t_photo, t1 = T(4), T(5), T(6)
    f = page()
    z = lerp(1.0, 1.06, (t - t0) / (t1 - t0))
    photo = cover(img('full_hills.jpg'), z, (0.5, 0.5))
    a_photo = ease((t - t_photo) / 1.4)
    if a_photo > 0:
        printed = photo if PAGE == 'dark' else f * photo                   # on paper it prints, on night it glows
        f = f * (1 - a_photo) + printed * a_photo
    f = scrim(f, a_photo)
    a_map = 1 - ease((t - t_photo - 1.0) / 1.6)
    if a_map > 0:
        draw_contours(f, 'hills', ease((t - t0) / 5.0), a_map)      # the hills bar plays twice: draw slower
        text(f, "2,240 m", 1330, 300, 'IBMPlexMono-Regular.ttf', 22, PAL['accent'], appear(t, T(4, 2)) * a_map, tracking=1)
    text(f, "So we went up into the hills.", 120, 880, 'Spectral-Regular.ttf', 58, PAL['ink'], appear(t, T(4, 1), t_photo))
    text(f, "To think as a group, with integrity and our whole body.", 120, 880, 'Spectral-Regular.ttf', 58, CREAM, appear(t, T(5, 1)), shadow=0.6)
    return finish(f, t, 0.02, vig=a_photo > 0.5)

D = '  \u00b7  '
ACT2 = [  # (t0, t1, source, zoom, framing c0, framing c1, line)
    (T(6), T(7) - BAR, 'full_balcony.jpg', (1.02, 1.08), (0.40, 0.5), (0.55, 0.5), None),
    (T(7) - BAR, T(7), 'full_trio.jpg', (1.0, 1.05), (0.5, 0.6), (0.5, 0.6), None),
    (T(7), T(8), 'room', (1.0, 1.04), (0.5, 0.5), (0.5, 0.5), "One house in the hills."),
    (T(8), T(9), 'full_debate.jpg', (1.02, 1.1), (0.45, 0.5), (0.6, 0.45), "Thinking out loud, not debating to win."),
]

def clip_frame(name, t_local, speed=1.0, fps=None):
    files = clip(name)
    fps = fps or {'room': 60, 'hillside': 120, 'fire': 34 / 1.8}[name]
    i = min(len(files) - 1, int(t_local * speed * fps))
    return img(files[i][len(C):])

def shot_frame(shot, t):
    t0, t1, src, z, c0, c1, line = shot
    if src.endswith('.jpg'):
        f = kb(img(src), t, t0, t1, z, c0, c1)
    else:                                       # a real clip: for these, z is playback speed. No added motion.
        speed = z if isinstance(z, float) else 1.0
        f = cover(clip_frame(src, max(0.0, t - t0), speed), 1.0, c0)
    f = scrim(f)
    if line:
        text(f, line, 120, 880, 'Spectral-Regular.ttf', 58, CREAM, appear(t, t0 - FADE / 2), shadow=0.6)   # arrives with its photo
    return f

def s_territory(t, shots):
    """The shot under t (clamped to the list), dissolving into its neighbour near each cut."""
    i = max(0, min(len(shots) - 1, sum(s[0] <= t for s in shots) - 1))
    cur = shots[i]
    if i > 0 and t < cur[0] + FADE / 2:
        return dissolve(lambda u: shot_frame(shots[i - 1], u), lambda u: shot_frame(cur, u), t, cur[0])
    if i + 1 < len(shots) and t > cur[1] - FADE / 2:
        return dissolve(lambda u: shot_frame(cur, u), lambda u: shot_frame(shots[i + 1], u), t, cur[1])
    return shot_frame(cur, t)

def s_act2(t):
    f = s_territory(t, ACT2)
    return finish(f, t, 0.025, vig=True)

QUESTIONS = [  # lines, plates (sharing the question's two bars evenly)
    (["Do you actually", "live by what", "you believe?"],
     [('board', 'WRITING IT DOWN'), ('trio', 'A FOREST WALK')]),
    (["When you change", "your mind, does", "your life change", "with it?"],
     [('disagree', 'A DISAGREEMENT'), ('market', 'A PREDICTION MARKET')]),
    (["What does it mean", "to be wise when", "AI can do our", "thinking work?"],
     [('capability', 'CAPABILITY VS SIZE'), ('calendar', 'VIBE CODING')]),
    (["Why do our", "\u201csolutions\u201d keep", "creating new", "problems?"],
     [('meta1', 'THE METACRISIS TALK'), ('meta2', 'THE METACRISIS TALK')]),
]
PLATE_X, PLATE_Y, PLATE_W, PLATE_H = 960, 170, 840, 630

@functools.lru_cache(maxsize=2)
def clean_page():
    """Flat brand paper with a faint field-notebook dot grid. No parchment, no blotches."""
    f = np.ones((H, W, 3), np.float32) * np.array(PAPER, np.float32) / 255
    grid = np.zeros((H, W), np.uint8)
    for y in range(36, H, 36):
        for x in range(36, W, 36):
            cv2.circle(grid, (x, y), 1, 255, -1, cv2.LINE_AA)
    al = grid.astype(np.float32)[..., None] / 255 * 0.5
    return f * (1 - al) + np.array(LINE, np.float32) / 255 * al

@functools.lru_cache(maxsize=32)
def plate_colour(name):
    from prep import PLATES
    import faces
    p, (x0, y0, x1, y1) = PLATES[name]
    im = load(p, 2000); h, w = im.shape[:2]
    return faces.anonymise(im[int(y0 * h):int(y1 * h), int(x0 * w):int(x1 * w)], name)[0]

def question_slots():
    """(question, plate, start, end) for every photo in Act III, in order."""
    out = []
    for q, (_, plates) in enumerate(QUESTIONS):
        t0, slot = T(9 + 2 * q), 8 * BEAT / len(plates)
        out += [(q, k, t0 + k * slot, t0 + (k + 1) * slot) for k in range(len(plates))]
    return out

def s_questions(t):
    """ACT III - one photo at a time behind the question, dissolving on the beat."""
    slots = question_slots()
    i = max(0, min(len(slots) - 1, sum(s[2] <= t for s in slots) - 1))
    if i > 0 and t < slots[i][2] + FADE / 2:
        return dissolve(lambda u: question_frame(slots[i - 1], u), lambda u: question_frame(slots[i], u), t, slots[i][2])
    if i + 1 < len(slots) and t > slots[i][3] - FADE / 2:
        return dissolve(lambda u: question_frame(slots[i], u), lambda u: question_frame(slots[i + 1], u), t, slots[i][3])
    return question_frame(slots[i], t)

def question_frame(s, t):
    q, k, pt0, pt1 = s
    t0 = T(9 + 2 * q)
    lines, plates = QUESTIONS[q]
    slot = pt1 - pt0
    name, cap = plates[k]
    ink, soft, accent = INK, INK_SOFT, BLUE
    if STYLE == 'bleed':
        f = scrim(kb(grade_q(name), t, pt0, pt0 + slot, (1.0, 1.04)))
        side = np.clip(1 - np.linspace(0, 1, W, dtype=np.float32) / 0.75, 0, 1)[None, :, None] * 0.9
        f = f * (1 - side) + np.array(NIGHT, np.float32) / 255 * side
        ink, soft, accent = CREAM, CREAM, MOON
    else:
        f = night(t) if STYLE == 'night' else clean_page().copy()
        pl = kb(img(f'plate_{name}.jpg'), t, pt0, pt0 + slot, (1.0, 1.05), (0.5, 0.5), (0.5, 0.5), (PLATE_W, PLATE_H))
        if STYLE == 'night':
            f[PLATE_Y:PLATE_Y + PLATE_H, PLATE_X:PLATE_X + PLATE_W] = pl * np.array(PAPER, np.float32) / 255
            ink, soft, accent = CREAM, (150, 158, 175), MOON
        else:
            multiply(f, pl, PLATE_X, PLATE_Y)
            border = np.zeros((H, W), np.uint8)
            cv2.rectangle(border, (PLATE_X, PLATE_Y), (PLATE_X + PLATE_W - 1, PLATE_Y + PLATE_H - 1), 255, 1)
            over(f, border, LINE_STRONG, 0.6)
        text(f, cap, PLATE_X, PLATE_Y + PLATE_H + 22, 'IBMPlexMono-Regular.ttf', 19, soft, 1.0, tracking=1)
    y0 = PLATE_Y + PLATE_H // 2 - len(lines) * 43                        # centre the question on the plate
    for i, line in enumerate(lines):
        text(f, line, 116, y0 + i * 86, 'Spectral-Light.ttf', 74, ink, appear(t, t0 + i * BEAT * 0.5, None, 0.08),
             shadow=0.8 if STYLE == 'bleed' else 0)
    return finish(f, t, 0.018)

@functools.lru_cache(maxsize=16)
def grade_q(name):
    from prep import grade
    return grade(plate_colour(name))

ACT4 = [
    (T(17), T(18), 'full_umbrella1.jpg', (1.02, 1.09), (0.5, 0.5), (0.56, 0.48), "Not only from the neck up."),
    (T(18), T(19) - BAR, 'full_umbrella2.jpg', (1.0, 1.06), (0.55, 0.5), (0.5, 0.5), "Stare at the sky."),
    (T(19) - BAR, T(19), 'full_road.jpg', (1.0, 1.05), (0.5, 0.45), (0.5, 0.45), "Move your body."),
    (T(19), T(20) - BAR, 'hillside', 0.62, (0.5, 0.5), (0.5, 0.5), None),
    (T(20) - BAR, T(20), 'full_lake.jpg', (1.0, 1.03), (0.5, 0.5), (0.5, 0.5), None),   # the whole-body line continues here
    (T(20), T(21), 'full_campfire.jpg', (1.02, 1.06), (0.5, 0.5), (0.52, 0.5), "Rich friendships."),
    (T(21), T(22) - BAR, 'full_kitchen.jpg', (1.0, 1.03), (0.5, 0.5), (0.45, 0.5), None),
    (T(22) - BAR, T(22), 'full_poker.jpg', (1.0, 1.03), (0.5, 0.4), (0.5, 0.5), None),
    (T(22), T(23), 'fire', 0.55, (0.5, 0.62), (0.5, 0.62), "Keeping the flame alive."),
    (T(23), T(24) - 2 * BAR, 'full_movie.jpg', (1.0, 1.03), (0.5, 0.5), (0.5, 0.5), None),
    (T(24) - 2 * BAR, T(24) - BAR, 'full_fireumb.jpg', (1.02, 1.05), (0.5, 0.55), (0.5, 0.55), None),
]

def s_act4(t):
    f = s_territory(t, ACT4)
    if T(19) <= t < T(20):
        text(f, "Let your whole body", 120, 800, 'Spectral-Regular.ttf', 58, CREAM, appear(t, T(19, 0.1)), shadow=0.6)
        text(f, "take part in the decision.", 120, 880, 'Spectral-Regular.ttf', 58, CREAM, appear(t, T(19, 0.35)), shadow=0.6)
    return finish(f, t, 0.025, vig=True)

def s_meet(t):
    """Rationality (the whiteboard) meets Wisdom (the forest walk): two halves of one frame, both in colour."""
    f = page()
    left = scrim(kb(grade_q('board'), t, T(24) - BAR, T(25), (1.0, 1.04), (0.45, 0.5), (0.45, 0.5), (W // 2, H)))
    f[:, :W // 2] = left
    text(f, "Rationality", 480, 880, 'Spectral-Light.ttf', 104, CREAM, appear(t, T(24) - BAR + 0.2, None, 0.8), 'c', shadow=0.6)
    a = ease((t - T(24)) / 1.2)                                             # Wisdom fades up in place, on the build
    if a > 0:
        right = scrim(kb(img('full_walk.jpg'), t, T(24), T(25), (1.0, 1.04), (0.52, 0.6), (0.52, 0.6), (W // 2, H)))
        f[:, W // 2:] = f[:, W // 2:] * (1 - a) + right * a
        text(f, "meets Wisdom.", W // 2 + 480, 880, 'Spectral-LightItalic.ttf', 104, CREAM, appear(t, T(24, 0.5), None, 0.9), 'c',
             shadow=0.6)
    return finish(f, t, 0.022)

def s_title(t):
    f = page()
    z = lerp(1.0, 1.035, (t - T(25)) / BAR)
    draw_contours(f, 'hills', 1.0, 0.55)
    if z != 1.0:
        f = cover(f, z)
    text(f, "OOTY ALIGNMENT RETREAT", W / 2, 440, 'Spectral-Light.ttf', 88, PAL['ink'], 1.0, 'c', tracking=7)
    text(f, "3.0", W / 2, 590, 'Spectral-Italic.ttf', 96, PAL['accent'], appear(t, T(25, 1)), 'c')
    return finish(f, t, 0.02)

def s_invite(t):
    f = night(t)
    text(f, "Everyone comes with something to give.", W / 2, 440, 'Spectral-Light.ttf', 60, CREAM, appear(t, T(26) + 0.35, T(28) - 0.35), 'c')
    text(f, "A rough thought. A half-baked idea. An unreleased project.", W / 2, 540, 'Spectral-LightItalic.ttf', 48, MOON,
         appear(t, T(26, 2.5), T(28) - 0.35), 'c')
    return finish(f, t, 0.03)

def s_lockup(t):
    f = page()
    draw_contours(f, 'balcony', 1.0, 0.5, PAL['faint'], PAL['faint'])
    text(f, "EPISTEMIC EXPERIMENTS PRESENTS", W / 2, 330, 'IBMPlexMono-Medium.ttf', 22, PAL['accent'], appear(t, T(28), T(30) - 0.3), 'c', tracking=4)
    text(f, "Ooty Alignment Retreat 3.0", W / 2, 400, 'Spectral-Light.ttf', 104, PAL['ink'], appear(t, T(28, 1), T(30) - 0.3), 'c')
    text(f, "Rationality meets Wisdom", W / 2, 560, 'Spectral-Italic.ttf', 54, PAL['accent'], appear(t, T(28, 2), T(30) - 0.3), 'c')
    text(f, "MEDITATION" + D + "FOREST WALKS" + D + "DEBATES" + D + "CIRCLING" + D + "FORECASTING", W / 2, 650,
         'IBMPlexMono-Regular.ttf', 20, PAL['soft'], appear(t, T(28, 3), T(30) - 0.3), 'c', tracking=2)
    a = appear(t, T(29), T(30) - 0.3)
    if a:
        f[700:702, W // 2 - 260:W // 2 + 260] = f[700:702, W // 2 - 260:W // 2 + 260] * (1 - a) + np.array(PAL['line'], np.float32) / 255 * a
    text(f, "APPLICATIONS OPENING SOON", W / 2, 730, 'IBMPlexMono-Regular.ttf', 24, PAL['soft'], a, 'c', tracking=5)
    return finish(f, t, 0.018)

ROUTE = [(700, 640), (790, 640), (880, 590), (970, 590), (1040, 690), (1130, 700), (1220, 660)]

def s_end(t):
    """Come think with us: the brand's dotted path draws from one dot to the terracotta one."""
    f = page()
    text(f, "Come think with us.", W / 2, 400, 'Spectral-Light.ttf', 92, PAL['ink'], appear(t, T(30)), 'c')
    a = appear(t, T(31) - 0.2)
    if a:
        dot(f, *ROUTE[0], 12, PAL['start'], a)
        dotted_path(f, ROUTE, ease((t - T(31)) / 2.4))
        b = appear(t, T(31) + 2.3)
        ring(f, *ROUTE[-1], 22, PAL['accent'], b); dot(f, *ROUTE[-1], 14, PAL['accent'], b)
    text(f, "epistemic-experiments.org", W / 2, 820, 'IBMPlexMono-Regular.ttf', 28, PAL['soft'], appear(t, T(31) + 2.8), 'c', tracking=2)
    out = ease((t - (END - 1.6)) / 1.4)
    f = f * (1 - out) + night(t) * out
    return finish(f, t, 0.018)

SCENES = [(T(4), s_open), (T(6), s_map), (T(9), s_act2), (T(17), s_questions), (T(24) - BAR, s_act4), (T(25), s_meet),
          (T(26), s_title), (T(28), s_invite), (T(30), s_lockup), (END + 1, s_end)]

DISSOLVES = [T(6), T(9), T(17), T(24) - BAR, T(28), T(30)]   # hills->balcony, ->questions, ->forest, ->Rationality, ->card, ->end

def scene_at(t):
    return next(fn for t_end, fn in SCENES if t < t_end)

def frame(i):
    t = i / FPS
    cut = next((c for c in DISSOLVES if abs(t - c) < FADE / 2), None)
    if cut is None:
        f = scene_at(t)(t)
    else:
        f = dissolve(scene_at(cut - 1e-3), scene_at(cut + 1e-3), t, cut)
    return (np.clip(f, 0, 1) * 255).astype(np.uint8).tobytes()

X264 = ['-c:v', 'libx264', '-preset', 'slow', '-crf', '16', '-tune', 'grain', '-pix_fmt', 'yuv420p']
HEVC_HW = ['-c:v', 'hevc_videotoolbox', '-q:v', '88', '-tag:v', 'hvc1', '-pix_fmt', 'yuv420p']   # VMAF 98.4 vs x264's 98.0

def main(out=os.environ.get('FILM_OUT', 'film_silent.mp4'), start=0.0, end=END, scale=1.0, codec=X264, workers=12, chunksize=4):
    n0, n1 = int(start * FPS), int(end * FPS)
    vf = [] if scale == 1.0 else ['-vf', f'scale={int(W * scale)}:-2']
    ff = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS),
                           '-i', '-', *vf, *codec, out], stdin=subprocess.PIPE)
    with Pool(workers) as pool:
        for k, buf in enumerate(pool.imap(frame, range(n0, n1), chunksize=chunksize)):
            ff.stdin.write(buf)
            if k % 240 == 0:
                print(f'{(n0 + k) / FPS:6.1f}s', flush=True)
    ff.stdin.close(); ff.wait()

def default_codec():
    """Hardware HEVC on a Mac with VideoToolbox, software x264 everywhere else."""
    encoders = subprocess.run(['ffmpeg', '-hide_banner', '-encoders'], capture_output=True, text=True).stdout
    return HEVC_HW if 'hevc_videotoolbox' in encoders else X264

def render_segment(args):
    """One worker, one contiguous slice of the timeline, its own encoder: frames never cross a process boundary."""
    out, n0, n1, codec = args
    ff = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS),
                           '-i', '-', *codec, out], stdin=subprocess.PIPE)
    for i in range(n0, n1):
        ff.stdin.write(frame(i))
    ff.stdin.close(); ff.wait()
    return out

def main_segments(out, start=0.0, end=END, codec=X264, workers=12, chunk_s=3.0):
    """Cut the timeline into short chunks and hand them to `workers` processes as each frees up, so heavy scenes
    (the opening map costs ~9x a photo frame) spread across everyone. Each chunk is encoded by its own worker,
    then all are joined without re-encoding."""
    n0, n1 = int(start * FPS), int(end * FPS)
    cuts = np.unique(np.append(np.arange(n0, n1, int(chunk_s * FPS)), n1))
    ext = os.path.splitext(out)[1] or '.mp4'
    parts = [f'{out}.part{j:03d}{ext}' for j in range(len(cuts) - 1)]
    with Pool(workers) as pool:
        list(pool.imap_unordered(render_segment, [(p, cuts[j], cuts[j + 1], codec) for j, p in enumerate(parts)]))
    listing = out + '.parts.txt'
    with open(listing, 'w') as fh:
        fh.writelines(f"file '{os.path.abspath(p)}'\n" for p in parts)
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', listing, '-c', 'copy', out], check=True)
    for p in parts + [listing]:
        os.remove(p)

def stills(times, prefix='still'):
    for t in times:
        buf = frame(int(t * FPS))
        Image.frombytes('RGB', (W, H), buf).save(f'{prefix}_{t:06.2f}.jpg', quality=88)

if __name__ == '__main__':
    if sys.argv[1:2] == ['stills']:
        stills([float(x) for x in sys.argv[2:]])
    else:
        main_segments(os.environ.get('FILM_OUT', 'film_silent.mp4'), codec=default_codec(), workers=6)
