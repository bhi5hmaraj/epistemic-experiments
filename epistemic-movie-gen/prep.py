"""One-time asset prep: graded stills, ink plates, contour maps, clip frames -> cache/."""
import os, pickle, subprocess
from concurrent.futures import ProcessPoolExecutor
from look import *
import faces

PHOTOS = os.environ.get('PHOTOS', 'photos/')     # the retreat archives, unzipped: see README
R1, R2, EXTRA = PHOTOS + 'retreat1/', PHOTOS + 'retreat2/', PHOTOS + 'extra/'
FULL = {  # full-bleed "territory" stills
    'hills': R2 + 'IMG20250625183721.heic', 'balcony': R2 + 'PXL_20250625_110552351.jpg',
    'trio': R2 + 'PXL_20250625_105709792.jpg', 'debate': R2 + 'PXL_20250628_051436261.jpg',
    'umbrella1': R2 + 'PXL_20250625_113214748.jpg', 'umbrella2': R2 + 'PXL_20250625_113217049.jpg',
    'road': R1 + 'PXL_20240621_023316618.jpg', 'campfire': R2 + 'PXL_20250625_160122809.jpg',
    'kitchen': R2 + 'PXL_20250625_192542471.jpg', 'poker': R2 + 'PXL_20250626_144541058.MP.jpg',
    'movie': R2 + 'PXL_20250627_155623863.MP.jpg', 'fireumb': R2 + 'IMG20250625195529.heic',
    'lake': R2 + 'PXL_20250630_063708562.jpg',
    'walk': R2 + 'PXL_20250630_061053786.jpg',
}
PLATES = {  # (source, crop box as fractions x0,y0,x1,y1) printed as navy-ink plates
    'agidoc': (R2 + 'PXL_20250627_103228160.MP.jpg', (0.52, 0.18, 1.0, 0.86)),
    'board': (R2 + 'PXL_20250627_095359350.MP.jpg', (0.0, 0.0, 1.0, 1.0)),
    'talk4': (R2 + 'PXL_20250626_112315053.MP.jpg', (0.1, 0.0, 0.9, 1.0)),
    'couch24': (R1 + 'PXL_20240623_084850048.jpg', (0.0, 0.0, 1.0, 1.0)),
    'market': (R2 + 'PXL_20250628_052548258.jpg', (0.1, 0.0, 0.9, 1.0)),
    'distrib': (R2 + 'PXL_20250629_053042077.jpg', (0.1, 0.0, 0.9, 1.0)),
    'disagree': (R2 + 'PXL_20250628_051440978.jpg', (0.0, 0.0, 0.8, 1.0)),
    'couch': (R2 + 'PXL_20250626_152453148.jpg', (0.1, 0.0, 0.9, 1.0)),
    'capability': (R2 + 'PXL_20250629_052744408.MP.jpg', (0.05, 0.0, 0.85, 1.0)),
    'talk2': (R2 + 'PXL_20250624_093211946.MP.jpg', (0.05, 0.22, 0.95, 1.0)),
    'present': (R2 + 'PXL_20250625_090720785.MP.jpg', (0.1, 0.15, 0.9, 1.0)),
    'laptop24': (R1 + 'PXL_20240624_092046496.jpg', (0.0, 0.3, 1.0, 1.0)),
    'water': (R2 + 'PXL_20250626_112610776.MP.jpg', (0.15, 0.0, 0.95, 1.0)),
    'oversimp': (R2 + 'PXL_20250626_113955396.MP.jpg', (0.0, 0.0, 0.8, 1.0)),
    'dayone': (R2 + 'PXL_20250623_070734989.MP.jpg', (0.1, 0.0, 0.9, 1.0)),
    'calendar': (R2 + 'PXL_20250625_033837218.jpg', (0.2, 0.0, 1.0, 1.0)),
    'trio': (R2 + 'PXL_20250625_105709792.jpg', (0.0, 0.40, 1.0, 0.82)),
    'debate': (R2 + 'PXL_20250628_051436261.jpg', (0.0, 0.0, 0.85, 1.0)),
    'meta1': (EXTRA + 'PXL_20250626_111903901.jpg', (0.0, 0.0, 1.0, 1.0)),
    'meta2': (EXTRA + 'PXL_20250626_114307425.jpg', (0.0, 0.0, 1.0, 1.0)),
}
C = 'cache/'

def grade(img):
    """Territory grade: gentle, warm, blacks lifted toward the brand's night-ink."""
    hsv = cv2.cvtColor(img, cv2.COLOR_RGB2HSV); hsv[..., 1] *= 0.9
    img = cv2.cvtColor(hsv, cv2.COLOR_HSV2RGB)
    img = np.clip(0.5 + (img - 0.5) * 1.05, 0, 1)
    img = img + img ** 2 * np.array([0.025, 0.01, -0.02], np.float32)
    night = np.array(NIGHT, np.float32) / 255
    return np.clip(img * (1 - 0.05) + night * 0.05 + 0.012, 0, 1)

def save(path, img):
    cv2.imwrite(path, cv2.cvtColor((np.clip(img, 0, 1) * 255).astype(np.uint8), cv2.COLOR_RGB2BGR), [cv2.IMWRITE_JPEG_QUALITY, 95])

def do_full(item):
    k, p = item
    save(C + f'full_{k}.jpg', grade(faces.anonymise(load(p, 2600), k)[0]))

def do_plate(item):
    k, (p, (x0, y0, x1, y1)) = item
    img = load(p, 2000); h, w = img.shape[:2]
    img = img[int(y0 * h):int(y1 * h), int(x0 * w):int(x1 * w)]
    save(C + f'plate_{k}.jpg', plate(faces.anonymise(img, k)[0], 'ink', seed=hash(k) % 1000))

def contours(src, levels=16, sigma=22, min_len=140):
    """Contour lines of a photo's light: the map drawn from the territory."""
    img = load(src, 1920); img = cv2.resize(img, (W, H))
    L = cv2.GaussianBlur(cv2.cvtColor(img, cv2.COLOR_RGB2GRAY), (0, 0), sigma)
    out = []
    for k, lv in enumerate(np.linspace(np.percentile(L, 3), np.percentile(L, 97), levels)):
        cs, _ = cv2.findContours((L > lv).astype(np.uint8), cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE)
        for c in cs:
            c = c[:, 0, :]
            edge = (c[:, 0] <= 1) | (c[:, 0] >= W - 2) | (c[:, 1] <= 1) | (c[:, 1] >= H - 2)
            c = c[~edge]                                  # drop the frame border segments
            if len(c) > min_len:
                out.append((k, c))
    return out

def clip_audio(src, name):
    """The camera's own sound, for the score's fire and hillside beds."""
    os.makedirs('clips', exist_ok=True)
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', src, '-vn', '-ac', '2', '-ar', '44100', f'clips/{name}.wav'], check=True)

def clip_frames(src, name, start=0.0, dur=None):
    os.makedirs(C + name, exist_ok=True)
    cmd = ['ffmpeg', '-v', 'error', '-y', '-ss', str(start), '-i', src]
    cmd += (['-t', str(dur)] if dur else []) + ['-vf', 'scale=1920:-2', '-q:v', '2', C + name + '/%04d.jpg']
    subprocess.run(cmd, check=True)

if __name__ == '__main__':
    os.makedirs(C, exist_ok=True)
    with ProcessPoolExecutor(12) as ex:
        list(ex.map(do_full, FULL.items())); list(ex.map(do_plate, PLATES.items()))
    pickle.dump({'hills': contours(FULL['hills']), 'balcony': contours(FULL['balcony'], 14, 26)}, open(C + 'contours.pkl', 'wb'))
    clip_frames(R2 + 'PXL_20250624_052056183.mp4', 'room', 1.0, 3.6)
    clip_frames(R2 + 'IMG_1296.MP4', 'hillside')
    clip_frames(R2 + 'IMG_1289.MP4', 'fire')
    clip_audio(R2 + 'IMG_1289.MP4', 'IMG_1289')
    clip_audio(R2 + 'IMG_1296.MP4', 'IMG_1296')
    print({k: len(os.listdir(C + k)) for k in ('room', 'hillside', 'fire')})
