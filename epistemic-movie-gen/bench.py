"""Render-speed experiments on a short, heavy clip. One configuration per process, timed from outside."""
import json, os, subprocess, sys, time
import film
from score import TS as T

CLIP = (T(16), T(16) + 10.0)            # last question, the dissolve into the forest, the rain shots
CODECS = {
    'x264_slow': film.X264,
    'h264_vt': ['-c:v', 'h264_videotoolbox', '-b:v', '40M', '-pix_fmt', 'yuv420p'],
    'hevc_vt': ['-c:v', 'hevc_videotoolbox', '-q:v', '70', '-tag:v', 'hvc1', '-pix_fmt', 'yuv420p'],
    'prores_vt': ['-c:v', 'prores_videotoolbox', '-profile:v', 'hq'],
    'hevc_vt80': ['-c:v', 'hevc_videotoolbox', '-q:v', '80', '-tag:v', 'hvc1', '-pix_fmt', 'yuv420p'],
    'hevc_vt88': ['-c:v', 'hevc_videotoolbox', '-q:v', '88', '-tag:v', 'hvc1', '-pix_fmt', 'yuv420p'],
    'hevc_vt10b': ['-c:v', 'hevc_videotoolbox', '-q:v', '80', '-tag:v', 'hvc1', '-profile:v', 'main10', '-pix_fmt', 'p010le'],
    'null': ['-f', 'null'],
    'reference': ['-c:v', 'libx264', '-preset', 'ultrafast', '-qp', '0', '-pix_fmt', 'yuv420p'],
}

if __name__ == '__main__':
    name, codec, workers, chunk = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4])
    mode = sys.argv[5] if len(sys.argv) > 5 else 'pipe'
    ext = '.mov' if codec.startswith('prores') else '.mp4'
    out = '/dev/null' if codec == 'null' else f'bench/{name}{ext}'
    os.makedirs('bench', exist_ok=True)
    t0 = time.time()
    if mode == 'segments':
        film.main_segments(out, *CLIP, codec=CODECS[codec], workers=workers)
    else:
        film.main(out, *CLIP, codec=CODECS[codec], workers=workers, chunksize=chunk)
    print(json.dumps({'name': name, 'wall': round(time.time() - t0, 2)}))
