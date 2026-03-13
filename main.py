#!/usr/bin/env python3
"""
Video → top 5 colours → MIDI. On startup (unless --no-interactive), prompt to select
camera and MIDI output (physical, virtual, or write to file). Poll at interval and send chord.
"""
from __future__ import annotations

import argparse
import os
import shutil
import sys
import time

from camera import CameraFeed, list_devices as list_cameras
from colours import get_top5_colours
from debug_output import write_debug_files
from midi import (
    MidiFileOutput,
    MidiPortOutput,
    colours_to_notes,
    get_output_names as get_midi_output_names,
)


def _prompt_camera() -> tuple[int | None, str | None]:
    """Interactive: list cameras, return (device_index, device_name) or (0, None) for default."""
    devices = list_cameras()
    if not devices:
        print("No cameras found. Using default index 0.")
        return 0, None
    print("Available cameras:")
    for idx, name in devices:
        print(f"  {idx}: {name}")
    try:
        raw = input("Select camera [0]: ").strip() or "0"
        i = int(raw)
        for idx, name in devices:
            if idx == i:
                return idx, name
        return i, None
    except (ValueError, EOFError):
        return 0, None


def _prompt_midi() -> tuple[str | None, bool, str | None]:
    """
    Interactive: list MIDI ports, offer virtual and write-to-file.
    Returns (port_name, use_virtual, file_path).
    - If physical: (port_name, False, None)
    - If virtual: (port_name, True, None)
    - If file: (None, False, path)
    """
    names = get_midi_output_names()
    print("MIDI output options:")
    for i, name in enumerate(names):
        print(f"  {i}: {name}")
    print(f"  v: Create virtual MIDI port (for DAW / VCV Rack)")
    print(f"  f: Write to file (no device)")
    try:
        raw = input("Select [v]: ").strip().lower() or "v"
        if raw == "f":
            path = input("Output file path: ").strip()
            return None, False, path or "midi_out.log"
        if raw == "v":
            name = input("Virtual port name [video-midi]: ").strip() or "video-midi"
            return name, True, None
        i = int(raw)
        if 0 <= i < len(names):
            return names[i], False, None
        return None, True, None  # fallback virtual
    except (ValueError, EOFError):
        return "video-midi", True, None


# Beats per division for sampling (seconds per poll = (60 / bpm) * beats_per_division)
DIVISION_BEATS = {
    "quarter": 1.0,
    "eighth": 0.5,
    "sixteenth": 0.25,
    "triplet": 2.0 / 3.0,       # quarter-note triplet (3 per 2 beats)
    "triplet_eighth": 1.0 / 3.0,  # eighth-note triplet (3 per beat)
}


def poll_interval_from_bpm(bpm: float, division: str) -> float:
    """Seconds between polls for given BPM and note division."""
    beats = DIVISION_BEATS.get(division, 1.0)
    return (60.0 / bpm) * beats


def run(
    camera_index: int | None = None,
    camera_name: str | None = None,
    midi_port: str | None = None,
    midi_virtual: bool = False,
    midi_out_file: str | None = None,
    poll_interval_sec: float | None = None,
    bpm: float = 90.0,
    division: str = "quarter",
    midi_note_min: int = 36,
    midi_note_max: int = 84,
    scale: str = "chromatic",
    no_interactive: bool = False,
    debug: bool = False,
    debug_dir: str = ".",
) -> None:
    # Resolve camera
    if not no_interactive and camera_index is None and camera_name is None:
        camera_index, camera_name = _prompt_camera()
    if camera_index is None:
        camera_index = 0

    # Resolve MIDI
    if not no_interactive and midi_port is None and midi_out_file is None and not midi_virtual:
        midi_port, midi_virtual, midi_out_file = _prompt_midi()
    elif no_interactive and midi_port is None and midi_out_file is None and not midi_virtual:
        midi_port = "video-midi"
        midi_virtual = True

    # Open MIDI output
    midi_output = None
    file_output = None
    if midi_out_file:
        file_output = MidiFileOutput(midi_out_file)
        file_output.open()
    else:
        port_name = midi_port or "video-midi"
        midi_output = MidiPortOutput(port_name, virtual=midi_virtual)
        midi_output.open()

    # Clear debug directory at start of run (avoid wiping cwd if --debug-dir .)
    if debug and debug_dir and os.path.normpath(debug_dir) != "." and os.path.isdir(debug_dir):
        shutil.rmtree(debug_dir)
    if debug and debug_dir:
        os.makedirs(debug_dir, exist_ok=True)

    if poll_interval_sec is None:
        poll_interval_sec = poll_interval_from_bpm(bpm, division)

    # Open camera and run loop
    feed = CameraFeed(device_index=camera_index, device_name=camera_name)
    if not feed.open():
        print("Failed to open camera.", file=sys.stderr)
        if file_output:
            file_output.close()
        sys.exit(1)

    last_poll = 0.0
    try:
        while True:
            ret, frame = feed.read()
            if not ret or frame is None:
                continue
            now = time.time()
            if now - last_poll >= poll_interval_sec:
                last_poll = now
                colours = get_top5_colours(frame)
                notes_vel = colours_to_notes(
                    colours, note_min=midi_note_min, note_max=midi_note_max, scale=scale
                )
                if midi_output:
                    midi_output.send_chord(notes_vel)
                if file_output:
                    file_output.append_log(int(now), colours, notes_vel)
                if debug:
                    write_debug_files(debug_dir, colours, notes_vel, timestamp=int(now), frame=frame)
    except KeyboardInterrupt:
        pass
    finally:
        feed.release()
        if midi_output:
            midi_output.close()
        if file_output:
            file_output.close()


def main() -> None:
    p = argparse.ArgumentParser(description="Video → top 5 colours → MIDI")
    p.add_argument("--camera-index", type=int, default=None, help="Camera device index (default 0)")
    p.add_argument("--camera-name", type=str, default=None, help="Camera device name (e.g. FaceTime HD Camera)")
    p.add_argument("--midi-port", type=str, default=None, help="MIDI output port name")
    p.add_argument("--midi-virtual", action="store_true", help="Create virtual MIDI port (for DAW/VCV Rack)")
    p.add_argument("--midi-out-file", type=str, default=None, help="Write colour→MIDI log to file instead of MIDI")
    p.add_argument("--poll-interval", type=float, default=None, dest="poll_interval_sec", help="Seconds between colour/MIDI updates (overrides --bpm/--division if set)")
    p.add_argument("--bpm", type=float, default=90.0, help="Beats per minute for sampling (default 90)")
    p.add_argument("--division", choices=("quarter", "eighth", "sixteenth", "triplet", "triplet_eighth"), default="quarter", help="Note division: quarter, eighth, sixteenth, triplet (quarter-note triplets), triplet_eighth (default quarter)")
    p.add_argument("--midi-note-min", type=int, default=36, help="Minimum MIDI note")
    p.add_argument("--midi-note-max", type=int, default=84, help="Maximum MIDI note")
    p.add_argument("--scale", choices=("chromatic", "pentatonic", "blues_pentatonic", "ionian", "dorian", "phrygian", "lydian", "mixolydian", "aeolian", "locrian"), default="chromatic", help="Scale for note quantization: chromatic, pentatonic, blues_pentatonic, or major-scale modes (ionian, dorian, phrygian, lydian, mixolydian, aeolian, locrian)")
    p.add_argument("--no-interactive", action="store_true", help="Skip startup prompts; use CLI/env only")
    p.add_argument("--debug", action="store_true", help="Write timestamped .png and .log each poll")
    p.add_argument("--debug-dir", type=str, default=".", help="Directory for debug files")
    args = p.parse_args()

    run(
        camera_index=args.camera_index,
        camera_name=args.camera_name,
        midi_port=args.midi_port,
        midi_virtual=args.midi_virtual,
        midi_out_file=args.midi_out_file,
        poll_interval_sec=args.poll_interval_sec,
        bpm=args.bpm,
        division=args.division,
        midi_note_min=args.midi_note_min,
        midi_note_max=args.midi_note_max,
        scale=args.scale,
        no_interactive=args.no_interactive,
        debug=args.debug,
        debug_dir=args.debug_dir,
    )


if __name__ == "__main__":
    main()
