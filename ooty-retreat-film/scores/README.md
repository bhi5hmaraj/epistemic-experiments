# The sound

Every soundtrack here is code. A small sampler plays free orchestral recordings note by note, and
NumPy synthesises the rest. Each score lasts exactly as long as the film, so any of them fits the
picture without a re-render.

## Render

```sh
.venv/bin/python music.py list            # every soundtrack it knows
.venv/bin/python music.py gentle shire    # render the named ones
.venv/bin/python music.py all             # render all 21
```

Each one lands in `out/music/` as `<name>.wav` (24-bit), `<name>.m4a` (to listen) and `<name>.mid`.
The `.mid` file holds every note with one track per instrument. Open it in GarageBand or Logic to
play the same score through better instruments.

To put a soundtrack under the picture, pass it to `variants.py`:

```sh
.venv/bin/python variants.py v4.6 dark --music out/music/shire.wav
```

## The clock

Picture and sound share one clock, defined in `score.py`.

- 72 beats a minute, four beats a bar: one bar is 3.33 s. `T(bar, beat)` gives a time in seconds.
- `PRE = 2` adds two bars before bar 0 for the opening world map.
- `REPEATS` lists bars that play twice, to give a photo or a line of text more time. A bar listed
  twice plays three times. The render repeats the finished audio of that bar, so the harmony stays
  the same.
- Scores write notes on the plain clock `T`. `film.py` and `variants.py` use `TS`, which adds the
  repeats. `stretch(t)` converts one to the other.

The film's sections sit on fixed bars. A new score must keep them:

| Bars | Scene | What the music does there |
|---|---|---|
| -2 to 3 | The world map, then "Most of us..." | Quiet. One note per map node (`MAP_NODES`) |
| 4 to 8 | The hills and the house | The main pattern enters |
| 9 to 16 | The four questions | Builds a little, two bars a question |
| 17 to 19 | The rain | A breath: thinner |
| 20 to 24 | The bonfire and the night, then Rationality meets Wisdom | Fullest |
| 25 | The title | One chord |
| 26 to 31 | The invitation, title card and ending | Quiet. Everything before bar 26 fades out |

## The engine (`score.py`)

- **`Inst`** loads one instrument folder from `samples/`. It plays the nearest recorded note and
  repitches it, and it picks the velocity layer from how hard the note is. Some folders name
  their notes an octave low, so each `Inst` takes an octave fix. The organ has no note names, so
  it reads `data/organ_map.json` instead.
- **`note()` and `sustain()`** place notes on buses (piano, strings, brass, harp, winds, organ,
  synth, perc, fx, field).
- **Mixdown** sends each bus to a synthetic hall reverb, then applies a slow fader curve, a gentle
  compressor, loudness to -14.5 LUFS and a peak limiter at -1.2 dBFS.
- **`write_midi()`** saves every note played, repeats included.
- **Field sound**: the bonfire and hillside recordings come from the retreat's own clips
  (`prep.py` extracts them to `clips/`). `rain()` and `field()` weave them under the night and
  rain scenes.

## Versions of the film's score

`score.py` is the film's own score: piano, strings, horns and percussion in A minor. Switches change
how it plays:

| `music.py` name | Variable | Change |
|---|---|---|
| `orchestral` | none | The full score: swells, timpani, a big hit on the title |
| `gentle` | `GENTLE=1` | The v4.6 soundtrack. No percussion or swells, softer dynamics, a soft fade into the invitation |
| `quiet` | `QUIET=1` | No percussion or swells, otherwise full |
| `piano` | `ARR=piano` | Piano alone carries the melody |
| `harp` | `ARR=harp` | Harp plays the piano's pattern |
| `major` | `ARR=major` | The same melody over C, G, Am, F |
| `ambient` | `ARR=ambient` | No pulse, slow harp notes |

## Alternative scores (`scores/`)

Each file is a standalone score in the manner of a composer, with its own instruments and key.
`common.py` holds shared instruments and the picture-synced sounds. `synth.py` makes what the
samples lack: plucked guitar, electric piano, pads, bells, birdsong, crackle and soft drums.

| Name | In the manner of | Key | Instruments |
|---|---|---|---|
| `zimmer` | Hans Zimmer, Interstellar | A minor | Pipe organ, a ticking clock, piano |
| `djawadi` | Ramin Djawadi, Westworld | D minor | Triplet cello pattern, solo violin, drums |
| `richter` | Max Richter | G minor | String chorale over a falling bass |
| `arnalds` | Olafur Arnalds, Nils Frahm | F major | Piano with tape echo, synth pad, soft beat |
| `hisaishi` | Joe Hisaishi | D major | Flute, pizzicato, harp, glockenspiel |
| `eno` | Brian Eno | D-flat major | Glass bells looping out of phase over a drone |
| `satie` | Erik Satie | D major | One piano in a small room |
| `reich` | Steve Reich, Philip Glass | E major | Two marimbas a quaver apart, clarinets |
| `lofi` | Nujabes | C major | Electric piano, swung beat, vinyl crackle |
| `folk` | Jose Gonzalez | G major | Fingerpicked guitar, shaker, whistle |
| `shire` | The Shire (Howard Shore) | D major | Tin whistle jig, harp, frame drum, birdsong |
| `fireside` | A slow fiddle air | G major | Solo violin, guitar, cello drone |
| `lark` | Vaughan Williams, The Lark Ascending | E major | Solo violin runs over held strings |
| `waltz` | Michael Giacchino, Up | F major | Piano waltz, clarinet, pizzicato |

The first five build to a big title moment. The rest stay calm and render with `calm=True`. That
mode uses a flatter fader curve and fades out over a bar before the invitation.

## Write a new score

1. Copy `scores/satie.py` to `scores/<name>.py`. It is the shortest complete example.
2. Write the notes in `main()` for bars -2 to 25, and in `coda()` for bars 26 to 31. Keep the
   sections in the table above.
3. Call `field_beds()` in `main()` and `coda_fire()` in `coda()` for the recorded fire and rain.
4. End with `E.render(out, [main], [coda], rt=..., calm=True)`.
5. Run `python music.py <name>`. `music.py list` finds the new file on its own.

Check a new score by ear, then by numbers. Every note should sit in the key, and the loudness
should not jump. `pretty_midi` reads the `.mid` file for the first check. `pyloudnorm` measures
the second.
