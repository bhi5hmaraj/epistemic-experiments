"""Shared visual toolkit: brand palette, paper, watercolor plates, contours, text."""
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont, ImageOps
import pillow_heif; pillow_heif.register_heif_opener()

W, H = 1920, 1080
F = 'fonts/'
# epistemic-experiments.org palette (RGB)
PAPER = (251, 248, 239); PAPER_SOFT = (246, 240, 228); SURFACE = (240, 234, 219)
INK = (37, 48, 68); INK_SOFT = (61, 70, 88); BLUE = (51, 79, 143); TERRA = (150, 83, 66)
SAGE = (127, 143, 120); LINE = (217, 208, 189); LINE_STRONG = (139, 131, 114); NIGHT = (16, 20, 30)

def font(name, size): return ImageFont.truetype(F + name, size)

def fbm(h, w, seed, octaves=5, base=4):
    rng = np.random.default_rng(seed); out = np.zeros((h, w), np.float32); amp = 1.0
    for o in range(octaves):
        s = base * 2 ** o
        n = rng.normal(0, 1, (s * h // max(h, w) + 2, s * w // max(h, w) + 2)).astype(np.float32)
        out += cv2.resize(n, (w, h), interpolation=cv2.INTER_CUBIC) * amp; amp *= 0.5
    return out / 1.9

def paper(w=W, h=H, seed=0, color=PAPER_SOFT):
    """Cold-press watercolor paper: tooth + faint mottling. float32 0..1 RGB."""
    rng = np.random.default_rng(seed)
    tooth = cv2.GaussianBlur(rng.normal(0, 1, (h, w)).astype(np.float32), (0, 0), 1.6)
    tooth = tooth / (tooth.std() + 1e-6)
    mott = fbm(h, w, seed + 7, 4, 3)
    base = np.array(color, np.float32) / 255
    shade = 1 + tooth[..., None] * 0.012 + mott[..., None] * 0.018
    return np.clip(base[None, None] * shade, 0, 1), tooth

def load(path, max_side=2400):
    im = ImageOps.exif_transpose(Image.open(path)).convert('RGB')
    im.thumbnail((max_side, max_side), Image.LANCZOS)
    return np.asarray(im).astype(np.float32) / 255

def watercolor(img, seed=0, tooth=None):
    """Photo -> transparent watercolor pigment layer (RGB 0..1, multiply over paper)."""
    u8 = (img * 255).astype(np.uint8)
    flat = cv2.stylization(u8[..., ::-1], sigma_s=45, sigma_r=0.35)[..., ::-1].astype(np.float32) / 255
    flat = cv2.edgePreservingFilter((flat * 255).astype(np.uint8), flags=1, sigma_s=30, sigma_r=0.3).astype(np.float32) / 255
    hsv = cv2.cvtColor(flat, cv2.COLOR_RGB2HSV)
    hsv[..., 1] *= 0.55                                  # watercolor is never saturated
    col = cv2.cvtColor(hsv, cv2.COLOR_HSV2RGB)
    lum = col.mean(2, keepdims=True)
    col = 1 - (1 - col) * 0.82                           # transparent: lift toward paper
    col = col * 0.93 + np.array(INK, np.float32)[None, None] / 255 * 0.07 * (1 - lum)  # shadows lean navy ink
    # pigment pools at region edges
    g = cv2.cvtColor(flat, cv2.COLOR_RGB2GRAY)
    e = np.abs(cv2.Sobel(g, cv2.CV_32F, 1, 0, 3)) + np.abs(cv2.Sobel(g, cv2.CV_32F, 0, 1, 3))
    e = cv2.GaussianBlur(np.clip(e * 2.5, 0, 1), (0, 0), 1.2)
    col *= (1 - 0.18 * e[..., None])
    # granulation: pigment settles in paper tooth, more in darker washes
    h, w = g.shape
    gran = fbm(h, w, seed + 3, 3, 60)
    col *= 1 + gran[..., None] * 0.05 * (1 - lum)
    # graphite underdrawing
    edges = cv2.Canny((g * 255).astype(np.uint8), 60, 140)
    edges = cv2.GaussianBlur(edges.astype(np.float32) / 255, (0, 0), 0.7)
    col *= 1 - 0.22 * edges[..., None]
    return np.clip(col, 0, 1)

def bleed_mask(h, w, seed=0, margin=0.06, soft=0.05):
    """Irregular watercolor edge: wash fades out raggedly before the plate border."""
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    dx = np.minimum(xx, w - 1 - xx) / w; dy = np.minimum(yy, h - 1 - yy) / h
    d = np.minimum(dx * w, dy * h) / min(h, w)
    n = fbm(h, w, seed, 5, 6) * 0.05
    m = np.clip((d - margin + n) / soft, 0, 1)
    rim = np.exp(-((d - margin + n) / 0.012) ** 2) * 0.35   # backrun: darker tide-line at the edge
    return m, rim

def plate(img, mode='ink', seed=0):
    """Photo printed onto cream paper. 'ink' = single navy ink (field-guide plate), 'print' = soft colour print."""
    h, w = img.shape[:2]
    g = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    lo, hi = np.percentile(g, 1.5), np.percentile(g, 99.5)
    g = np.clip((g - lo) / (hi - lo + 1e-6), 0, 1)
    if mode == 'ink':
        d = (1 - g) ** 1.15 * 0.92
        rng = np.random.default_rng(seed)
        d *= 1 + cv2.GaussianBlur(rng.normal(0, 1, (h, w)).astype(np.float32), (0, 0), 0.8)[..., None][..., 0] * 0.10
        ink = np.array(INK, np.float32) / 255
        # sage wash sits in the midtones, like a second plate
        s = np.clip(1 - np.abs(g - 0.62) * 3.2, 0, 1) * 0.22
        sage = np.array(SAGE, np.float32) / 255
        return (1 - d[..., None] * (1 - ink)) * (1 - s[..., None] * (1 - sage))
    hsv = cv2.cvtColor(img, cv2.COLOR_RGB2HSV); hsv[..., 1] *= 0.7
    c = cv2.cvtColor(hsv, cv2.COLOR_HSV2RGB)
    c = np.clip((c - lo) / (hi - lo + 1e-6), 0, 1) ** 1.05
    return 1 - (1 - c) * 0.9          # ink never fully covers: paper shows through the lights

def wash_blob(size, color, seed=0, alpha=0.35):
    """Procedural watercolor bloom: ragged disc, pigment darker at the tide-line."""
    s = size; yy, xx = np.mgrid[0:s, 0:s].astype(np.float32)
    r = np.hypot(xx - s / 2, yy - s / 2) / (s / 2)
    n = fbm(s, s, seed, 4, 3) * 0.10
    inside = np.clip((0.86 - r + n) / 0.03, 0, 1)
    tide = np.exp(-((0.86 - r + n) / 0.05) ** 2) * 0.6
    body = 0.55 + fbm(s, s, seed + 5, 3, 5) * 0.2
    a = np.clip(inside * body + tide * inside, 0, 1) * alpha
    return a, np.array(color, np.float32) / 255
