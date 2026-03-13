# video-midi

Video feed → top 5 dominant colours → MIDI notes. Uses a USB or built-in camera, computes the five most prevalent colours at a polled interval, maps them to MIDI (hue → pitch, brightness → velocity), and sends to a physical device, virtual port (e.g. DAW / VCV Rack), or a log file.

**macOS only.** Requires a camera and (optionally) a MIDI output.

## Setup

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Run

```bash
python main.py
```

On first run you’ll be prompted to select a camera and a MIDI output (physical port, virtual port for DAW/VCV Rack, or write to file). Use `--no-interactive` and CLI options to skip prompts.

## Options

**Camera**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--camera-index` | int | 0 | Camera device index (e.g. 0 for first camera). |
| `--camera-name` | str | — | Camera by name (e.g. `"FaceTime HD Camera"`). |

**MIDI output**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--midi-port` | str | — | Physical MIDI output port name (from system). |
| `--midi-virtual` | flag | — | Create a virtual MIDI port (e.g. for DAW / VCV Rack). |
| `--midi-out-file` | str | — | Write colour→MIDI log to a file instead of sending MIDI. |

**Sampling (when to analyse and send)**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--bpm` | float | 90 | Beats per minute (used with `--division`). |
| `--division` | choice | quarter | Note division: `quarter`, `eighth`, `sixteenth`, `triplet`, `triplet_eighth`. |
| `--poll-interval` | float | — | Seconds between updates; if set, overrides `--bpm` / `--division`. |

**MIDI mapping**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--midi-note-min` | int | 36 | Minimum MIDI note (0–127). |
| `--midi-note-max` | int | 84 | Maximum MIDI note (0–127). |
| `--scale` | choice | chromatic | Quantize notes to scale: `chromatic`, `pentatonic`, `blues_pentatonic`, or modes `ionian`, `dorian`, `phrygian`, `lydian`, `mixolydian`, `aeolian`, `locrian`. |

**Behaviour**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--no-interactive` | flag | — | Skip startup prompts; use only CLI/env values. |

**Debug**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--debug` | flag | — | Each poll: write `{timestamp}-frame.png`, `{timestamp}.png` (5 colour bars), and `{timestamp}.log`. |
| `--debug-dir` | str | . | Directory for debug files. Cleared at start unless set to `.`. |

## Examples

- Virtual MIDI (e.g. for Logic / VCV Rack): choose `v` at the MIDI prompt, or run with `--no-interactive --midi-virtual`.
- Write to file: choose `f` at the prompt, or use `--midi-out-file path/to/log.txt`.
- Headless, default 90 BPM quarter notes:  
  `python main.py --no-interactive --camera-index 0 --midi-virtual`
- 160 BPM, triplets:  
  `python main.py --no-interactive --camera-index 0 --midi-virtual --bpm 160 --division triplet`
- Fixed 0.5 s interval:  
  `python main.py --no-interactive --camera-index 0 --midi-virtual --poll-interval 0.5`
- Scale: e.g. `--scale aeolian` or `--scale blues_pentatonic`.
- Debug:  
  `python main.py --no-interactive --camera-index 0 --midi-virtual --debug --debug-dir debug_out`

## Tests

```bash
pytest tests/ -v
```

No camera or MIDI device required; tests use synthetic frames and mocks.
