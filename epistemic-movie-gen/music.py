"""Render the film's soundtracks into out/music/ as .wav, .m4a and .mid, each on the same clock as the picture.

python music.py list          every soundtrack this can render
python music.py gentle shire  render the named ones
python music.py all           render everything
"""
import os, subprocess, sys
from concurrent.futures import ThreadPoolExecutor

# The film's own score (score.py) in its switchable versions: name -> environment it renders under.
VERSIONS = {'orchestral': {}, 'gentle': {'GENTLE': '1'}, 'quiet': {'QUIET': '1'}, 'piano': {'ARR': 'piano'},
            'harp': {'ARR': 'harp'}, 'major': {'ARR': 'major'}, 'ambient': {'ARR': 'ambient'}}
# Standalone alternative scores, one file each in scores/ (common.py and synth.py are shared helpers).
ALTERNATIVES = sorted(f[:-3] for f in os.listdir('scores') if f.endswith('.py') and f not in ('common.py', 'synth.py'))
OUT = os.environ.get('OUT', 'out/') + 'music/'

def render(name):
    wav = f'{OUT}{name}.wav'
    if name in VERSIONS:
        cmd, env = [sys.executable, 'score.py'], {**os.environ, **VERSIONS[name], 'MUSIC_OUT': wav}
    else:
        cmd, env = [sys.executable, f'scores/{name}.py', wav], dict(os.environ)
    run = subprocess.run(cmd, env=env, capture_output=True, text=True)
    if run.returncode:
        sys.exit(f'{name} failed:\n{run.stderr[-2000:]}')
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', wav, '-c:a', 'aac', '-b:a', '256k', wav[:-4] + '.m4a'], check=True)
    return name

def main(names):
    if not names or names == ['list']:
        print('versions of the film score:', ' '.join(VERSIONS))
        print('alternative scores:        ', ' '.join(ALTERNATIVES))
        return
    names = list(VERSIONS) + ALTERNATIVES if names == ['all'] else names
    unknown = [n for n in names if n not in VERSIONS and n not in ALTERNATIVES]
    if unknown:
        sys.exit(f'unknown: {unknown}. Run: python music.py list')
    os.makedirs(OUT, exist_ok=True)
    with ThreadPoolExecutor(4) as pool:
        for name in pool.map(render, names):
            print(f'{OUT}{name}.wav  .m4a  .mid')

if __name__ == '__main__':
    main(sys.argv[1:])
