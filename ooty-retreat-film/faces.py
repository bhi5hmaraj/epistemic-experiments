"""Face privacy: detect with YuNet, then a soft feathered blur - shallow focus, not a censor bar."""
import functools, os
import numpy as np, cv2

# boxes the detector misses (profiles, firelight, backs of heads), as fractions of the source: x, y, w, h
MANUAL = {
    'umbrella1': [(0.49, 0.425, 0.024, 0.05)],
    'umbrella2': [(0.928, 0.43, 0.026, 0.055)],
}

@functools.lru_cache(maxsize=1)
def detector():
    return cv2.FaceDetectorYN.create('models/yunet.onnx', '', (320, 320), score_threshold=0.6, nms_threshold=0.3, top_k=200)

def detect(img, max_side=1920):
    """Faces in an RGB float image, as pixel boxes (x, y, w, h) in the image's own resolution."""
    h, w = img.shape[:2]
    s = min(1.0, max_side / max(h, w))
    small = cv2.resize((img * 255).astype(np.uint8), (int(w * s), int(h * s)), interpolation=cv2.INTER_AREA)
    d = detector(); d.setInputSize((small.shape[1], small.shape[0]))
    _, faces = d.detect(cv2.cvtColor(small, cv2.COLOR_RGB2BGR))
    return [] if faces is None else [tuple(f[:4] / s) for f in faces]

def blur(img, boxes, grow=1.45, strength=1.0):
    """Feathered elliptical blur over each box. Sigma scales with face size so small and large faces read alike."""
    if not boxes:
        return img
    out = img.copy(); h, w = img.shape[:2]
    for x, y, bw, bh in boxes:
        cx, cy = x + bw / 2, y + bh / 2
        rx, ry = bw * grow / 2, bh * grow * 1.1 / 2
        x0, y0 = int(max(0, cx - rx * 1.6)), int(max(0, cy - ry * 1.6))
        x1, y1 = int(min(w, cx + rx * 1.6)), int(min(h, cy + ry * 1.6))
        if x1 - x0 < 4 or y1 - y0 < 4:
            continue
        region = out[y0:y1, x0:x1]
        sigma = max(2.0, bw / 6 * strength)
        soft = cv2.GaussianBlur(region, (0, 0), sigma)
        yy, xx = np.mgrid[y0:y1, x0:x1].astype(np.float32)
        r = np.hypot((xx - cx) / rx, (yy - cy) / ry)
        m = np.clip((1.25 - r) / 0.45, 0, 1)[..., None]           # soft edge, no visible outline
        out[y0:y1, x0:x1] = region * (1 - m) + soft * m
    return out

BLUR = os.environ.get('BLUR', '0') == '1'           # off: everyone pictured has given permission (v4.3 on)

def anonymise(img, key=None):
    if not BLUR:
        return img, []
    boxes = detect(img)
    h, w = img.shape[:2]
    boxes += [(fx * w, fy * h, fw * w, fh * h) for fx, fy, fw, fh in MANUAL.get(key, [])]
    return blur(img, boxes), boxes
