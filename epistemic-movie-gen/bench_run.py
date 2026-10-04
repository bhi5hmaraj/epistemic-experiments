"""Run each render configuration in its own process; report wall time, fps and CPU use."""
import re, subprocess, sys
FRAMES = 240
CONFIGS = [l.split() for l in sys.stdin.read().strip().splitlines()]
for name, codec, workers, chunk, mode in CONFIGS:
    r = subprocess.run(['/usr/bin/time', '-p', '../.venv/bin/python', 'bench.py', name, codec, workers, chunk, mode],
                       capture_output=True, text=True)
    t = dict(re.findall(r'^(real|user|sys) ([\d.]+)', r.stderr, re.M))
    if r.returncode or 'real' not in t:
        print(f'{name:22s} FAILED: {r.stderr.strip().splitlines()[-1] if r.stderr.strip() else r.returncode}'); continue
    real, cpu = float(t['real']), float(t['user']) + float(t['sys'])
    print(f'{name:22s} {real:6.1f}s  {FRAMES / real:5.1f} fps  CPU {100 * cpu / real:5.0f}%  (sys {t["sys"]}s)', flush=True)
