"""Compare consecutive velocity pairs for every instrument+pitch in a dataset.

Groups notes by instrument and pitch, sorts by velocity, and compares each
consecutive pair using spectral distance from compare_audio.py.
"""

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

from tqdm import tqdm

from compare_audio import spectral_distance

VELOCITIES = [25, 50, 75, 100, 127]


def main():
    parser = argparse.ArgumentParser(
        description="Compare consecutive velocity pairs across an NSynth dataset"
    )
    parser.add_argument("examples_json", type=Path)
    parser.add_argument(
        "-o", "--output",
        type=Path,
        default=None,
        help="output JSON path (default: stdout)",
    )
    args = parser.parse_args()

    if not args.examples_json.exists():
        print(f"Error: {args.examples_json} not found", file=sys.stderr)
        sys.exit(1)

    audio_dir = args.examples_json.parent / "audio"
    if not audio_dir.is_dir():
        print(f"Error: audio directory {audio_dir} not found", file=sys.stderr)
        sys.exit(1)

    with open(args.examples_json) as f:
        data = json.load(f)

    # Group by (instrument_str, pitch) → sorted list of (velocity, note_str)
    groups = defaultdict(list)
    for note_str, entry in data.items():
        key = (entry["instrument_str"], entry["pitch"])
        groups[key].append((entry["velocity"], note_str))

    for group in groups.values():
        group.sort()

    # Only keep groups that have at least 2 velocities
    groups = {k: v for k, v in groups.items() if len(v) >= 2}

    # instruments → { pitch → distance }
    instruments = defaultdict(dict)

    with tqdm(total=len(groups), desc="Comparing") as pbar:
        for (instrument, pitch), notes in sorted(groups.items()):
            # Compare min velocity vs max velocity only
            min_note = notes[0][1]   # lowest velocity
            max_note = notes[-1][1]  # highest velocity
            path_a = audio_dir / f"{min_note}.wav"
            path_b = audio_dir / f"{max_note}.wav"

            if path_a.exists() and path_b.exists():
                dist = spectral_distance(path_a, path_b)
                instruments[instrument][pitch] = round(float(dist), 8)
            pbar.update(1)

    output = {
        "instruments": {
            instr: {
                str(pitch): dist
                for pitch, dist in sorted(pitches.items())
            }
            for instr, pitches in sorted(instruments.items())
        },
    }

    text = json.dumps(output, indent=2)
    if args.output:
        args.output.write_text(text)
        print(f"Wrote {len(instruments)} instruments to {args.output}")
    else:
        print(text)


if __name__ == "__main__":
    main()
