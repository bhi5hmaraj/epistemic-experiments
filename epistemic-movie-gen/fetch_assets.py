"""Download what the film needs and git does not hold: instrument samples, fonts, the face-detection model."""
import os, urllib.parse, urllib.request
from concurrent.futures import ThreadPoolExecutor

VSCO = 'https://raw.githubusercontent.com/sgossner/VSCO-2-CE/master/'
FONTS = 'https://raw.githubusercontent.com/google/fonts/main/ofl/'
FONT_FILES = ['spectral/Spectral-Light.ttf', 'spectral/Spectral-Regular.ttf', 'spectral/Spectral-Italic.ttf',
              'spectral/Spectral-LightItalic.ttf', 'ibmplexmono/IBMPlexMono-Regular.ttf', 'ibmplexmono/IBMPlexMono-Medium.ttf']
YUNET = 'https://github.com/opencv/opencv_zoo/raw/main/models/face_detection_yunet/face_detection_yunet_2023mar.onnx'

def get(url, dest):
    if os.path.exists(dest) and os.path.getsize(dest) > 0:
        return
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    urllib.request.urlretrieve(url, dest + '.part')
    os.rename(dest + '.part', dest)

def main():
    jobs = [(VSCO + urllib.parse.quote(p), 'samples/' + p) for p in open('data/vsco_samples.txt').read().split('\n') if p]
    jobs += [(FONTS + f, 'fonts/' + os.path.basename(f)) for f in FONT_FILES]
    jobs.append((YUNET, 'models/yunet.onnx'))
    with ThreadPoolExecutor(16) as pool:
        list(pool.map(lambda job: get(*job), jobs))
    print(f'{len(jobs)} files in samples/, fonts/, models/')

if __name__ == '__main__':
    main()
