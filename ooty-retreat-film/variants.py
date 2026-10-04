"""Mux the rendered picture with each score into the three options. Teaser cuts sit on bar lines from score.T."""
import os, subprocess
from score import TS as T, END_S as END, BAR

AAC = ['-c:a', 'aac', '-b:a', '256k', '-ar', '48000', '-movflags', '+faststart']
SHARE = ['-c:v', 'libx264', '-preset', 'slow', '-crf', '23', '-pix_fmt', 'yuv420p']
TEASER = [(0, T(4)), (T(9), T(13)), (T(24) - BAR, T(26)), (T(28), END)]   # cold open, two questions, the meeting + title, lockup + end

def ff(*args):
    subprocess.run(['ffmpeg', '-v', 'error', '-y', *args], check=True)

def teaser(video, music, out):
    v, a, cat = [], [], ''
    for i, (s, e) in enumerate(TEASER):
        v.append(f'[0:v]trim={s:.4f}:{e:.4f},setpts=PTS-STARTPTS[v{i}]')
        a.append(f'[1:a]atrim={s:.4f}:{e:.4f},asetpts=PTS-STARTPTS,afade=t=in:d=0.02,afade=t=out:st={e - s - 0.06:.4f}:d=0.06[a{i}]')
        cat += f'[v{i}][a{i}]'
    graph = ';'.join(v + a) + f';{cat}concat=n={len(TEASER)}:v=1:a=1[v][a]'
    ff('-i', video, '-i', music, '-filter_complex', graph, '-map', '[v]', '-map', '[a]', *SHARE[:-2], '-crf', '22',
       '-pix_fmt', 'yuv420p', *AAC, out)

OUT = os.environ.get('OUT', 'out/')

def master(tag, film_mp4, music):
    os.makedirs(OUT, exist_ok=True)
    ff('-i', film_mp4, '-i', music, '-map', '0:v', '-map', '1:a', '-c:v', 'copy', *AAC, '-shortest',
       f'{OUT}ooty_retreat_3.0_{tag}_master.mp4')

def extras(tag, film_mp4):
    """Share-size, quiet-score and teaser cuts, derived from a render that already exists."""
    m = f'{OUT}ooty_retreat_3.0_{tag}_'
    ff('-i', m + 'master.mp4', *SHARE, '-c:a', 'copy', '-movflags', '+faststart', m + 'A_orchestral.mp4')
    ff('-i', m + 'A_orchestral.mp4', '-i', f'{OUT}music/quiet.wav', '-map', '0:v', '-map', '1:a', '-c:v', 'copy', *AAC, '-shortest',
       m + 'B_quiet.mp4')
    teaser(film_mp4, f'{OUT}music/orchestral.wav', m + 'C_teaser.mp4')

if __name__ == '__main__':
    import argparse, os, sys
    ap = argparse.ArgumentParser(description='Render the master per page look. --extras derives the smaller cuts.')
    ap.add_argument('version'); ap.add_argument('pages', nargs='*', default=['dark', 'light'])
    ap.add_argument('--extras', action='store_true', help='only derive share/quiet/teaser from existing renders')
    ap.add_argument('--music', default=f'{OUT}music/orchestral.wav', help='soundtrack for the master (see music.py)')
    args = ap.parse_args()
    for page in args.pages:
        out, tag = f'film_silent_{page}.mp4', f'{args.version}_{page}'
        if args.extras:
            extras(tag, out)
            continue
        subprocess.run([sys.executable, 'film.py'], env={**os.environ, 'PAGE': page, 'FILM_OUT': out}, check=True)
        master(tag, out, args.music)
