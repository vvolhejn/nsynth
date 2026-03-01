import argparse
import json
import logging
import re
import sys
from pathlib import Path

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def midi_to_note(midi_pitch: int) -> str:
    notes = ["C", "Cs", "D", "Ds", "E", "F", "Fs", "G", "Gs", "A", "As", "B"]
    octave = (midi_pitch // 12) - 1
    note_index = midi_pitch % 12
    return f"{notes[note_index]}{octave}"


def note_to_midi(note_name: str) -> int:
    notes = ["C", "Cs", "D", "Ds", "E", "F", "Fs", "G", "Gs", "A", "As", "B"]
    match = re.match(r"([A-G]s?)(-?\d+)", note_name)
    if not match:
        return 0
    name, octave = match.groups()
    return notes.index(name) + (int(octave) + 1) * 12


def instrument_category(name: str) -> str:
    """Extract category prefix, e.g. 'bass_electronic_018' -> 'bass_electronic'."""
    m = re.match(r"(.+)_\d+$", name)
    return m.group(1) if m else name


def load_velocity_matters(comparison_json: Path, threshold: float) -> set[str]:
    """Return set of instrument names where velocity matters (max distance >= threshold)."""
    with open(comparison_json) as f:
        data = json.load(f)

    velocity_instruments = set()
    for instrument, pitches in data["instruments"].items():
        all_dists = []
        for pitch, dist in pitches.items():
            if isinstance(dist, list):
                all_dists.extend(dist)
            else:
                all_dists.append(dist)
        if not all_dists:
            continue
        all_dists.sort()
        median = all_dists[len(all_dists) // 2]
        if median >= threshold:
            velocity_instruments.add(instrument)

    logger.info(
        f"Found {len(velocity_instruments)} velocity-sensitive instruments with median distance >= {threshold}, "
        f"out of {len(data['instruments'])} total instruments"
    )
    return velocity_instruments


VELOCITY_MAPPING = {25: 1, 50: 2, 75: 3, 100: 4, 127: 5}
DEFAULT_VELOCITY = 100
DEFAULT_VELOCITY_DISTANCE_THRESHOLD = 0.03
ALLOWED_NOTE_CLASSES = {"C", "Ds", "Fs", "A"}


def main(
    input_json: Path,
    filter_str: str = None,
    base_url: str = None,
    comparison_json: Path = None,
    velocity_threshold: float = DEFAULT_VELOCITY_DISTANCE_THRESHOLD,
    max_per_category: int = None,
):
    try:
        with open(input_json, "r") as f:
            data = json.load(f)
    except Exception as e:
        print(f"Error reading {input_json}: {e}", file=sys.stderr)
        sys.exit(1)

    velocity_instruments = None
    if comparison_json:
        velocity_instruments = load_velocity_matters(
            comparison_json, velocity_threshold
        )
        print(
            f"# {len(velocity_instruments)} instruments with velocity above threshold {velocity_threshold}",
            file=sys.stderr,
        )

    strudel_samples = {}
    if base_url:
        strudel_samples["_base"] = base_url

    for key, entry in data.items():
        if filter_str and filter_str not in key:
            continue

        instrument_name = entry.get("instrument_str")
        pitch = entry.get("pitch")
        velocity = entry.get("velocity")
        note_str = entry.get("note_str")

        if (
            instrument_name is None
            or pitch is None
            or velocity is None
            or note_str is None
        ):
            continue

        v_idx = VELOCITY_MAPPING.get(velocity)
        if v_idx is None:
            continue

        use_velocity = (
            velocity_instruments is None or instrument_name in velocity_instruments
        )

        if not use_velocity:
            # Only keep the default velocity sample
            if velocity != DEFAULT_VELOCITY:
                continue

        if instrument_name not in strudel_samples:
            strudel_samples[instrument_name] = {}

        note_name = midi_to_note(pitch)
        note_class_match = re.match(r"([A-G]s?)", note_name)
        if not note_class_match:
            continue
        note_class = note_class_match.group(1)
        if note_class not in ALLOWED_NOTE_CLASSES:
            continue

        if use_velocity:
            if note_name not in strudel_samples[instrument_name]:
                strudel_samples[instrument_name][note_name] = [None] * 5
            strudel_samples[instrument_name][note_name][v_idx - 1] = f"{note_str}.wav"
        else:
            strudel_samples[instrument_name][note_name] = f"{note_str}.wav"

    # Limit instruments per category
    if max_per_category is not None:
        category_counts = {}
        filtered = {}
        if "_base" in strudel_samples:
            filtered["_base"] = strudel_samples["_base"]
        for instrument_name in sorted(strudel_samples):
            if instrument_name == "_base":
                continue
            cat = instrument_category(instrument_name)
            category_counts[cat] = category_counts.get(cat, 0) + 1
            if category_counts[cat] <= max_per_category:
                filtered[instrument_name] = strudel_samples[instrument_name]
        strudel_samples = filtered

    # Remove notes with any null in their velocity list, then sort
    for instrument_name in strudel_samples:
        if instrument_name == "_base":
            continue
        if not isinstance(strudel_samples[instrument_name], dict):
            continue
        strudel_samples[instrument_name] = {
            note_name: samples
            for note_name, samples in strudel_samples[instrument_name].items()
            if not (isinstance(samples, list) and None in samples)
        }
        sorted_notes = sorted(
            strudel_samples[instrument_name].items(),
            key=lambda item: note_to_midi(item[0]),
        )
        strudel_samples[instrument_name] = dict(sorted_notes)

    print(json.dumps(strudel_samples))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "input_json",
        type=Path,
    )
    parser.add_argument(
        "--filter",
        type=str,
        default=None,
        help="Filter keys containing this string (e.g. 'bass_synthetic')",
    )
    parser.add_argument(
        "--base-url",
        default="https://huggingface.co/datasets/vvolhejn/nsynth/resolve/main/nsynth-test/audio/",
        help="Base URL for the audio files",
    )
    parser.add_argument(
        "--comparison-json",
        type=Path,
        default=None,
        help="Path to comparison JSON from compare_all.py. Instruments with max distance "
        "below --velocity-threshold will only get one sample per note instead of 5.",
    )
    parser.add_argument(
        "--velocity-threshold",
        type=float,
        default=DEFAULT_VELOCITY_DISTANCE_THRESHOLD,
        help=f"Min spectral distance to include velocity variants (default: {DEFAULT_VELOCITY_DISTANCE_THRESHOLD})",
    )
    parser.add_argument(
        "--max-per-category",
        type=int,
        default=None,
        help="Max instruments per category (e.g. 2 means at most 2 bass_electronic_* instruments)",
    )
    args = parser.parse_args()

    main(
        args.input_json,
        args.filter,
        args.base_url,
        args.comparison_json,
        args.velocity_threshold,
        args.max_per_category,
    )
