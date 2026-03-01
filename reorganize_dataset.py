#!/usr/bin/env python3
"""Reorganize an NSynth dataset folder into per-instrument subdirectories, converting WAV to MP3."""

import argparse
import json
import os
from pathlib import Path

import librosa
import numpy as np
import soundfile as sf
from pydub import AudioSegment
from tqdm import tqdm


def main():
    parser = argparse.ArgumentParser(
        description="Reorganize NSynth dataset into per-instrument folders with MP3 conversion"
    )
    parser.add_argument("dataset_dir", help="Path to dataset folder (e.g. nsynth-test)")
    args = parser.parse_args()

    dataset_dir = Path(args.dataset_dir)
    audio_dir = dataset_dir / "audio"
    output_dir = dataset_dir / "audio2"
    examples_path = dataset_dir / "examples.json"
    output_dir.mkdir(exist_ok=True)

    with open(examples_path) as f:
        examples = json.load(f)

    for note_str, meta in tqdm(examples.items(), desc="Converting"):
        instrument = meta["instrument_str"]
        # note_str is like "bass_synthetic_068-049-025", strip the instrument prefix
        suffix = note_str[len(instrument) + 1 :]  # "049-025"

        src = audio_dir / f"{note_str}.wav"
        if not src.exists():
            print(f"Warning: source file {src} not found, skipping")
            continue

        dest_dir = output_dir / instrument
        dest_dir.mkdir(exist_ok=True)
        dest = dest_dir / f"{suffix}.mp3"

        if dest.exists():
            continue

        y, sr = librosa.load(str(src), sr=None)
        # Convert to 16-bit PCM for pydub
        pcm = (y * 32767).astype(np.int16)
        audio = AudioSegment(
            pcm.tobytes(),
            frame_rate=sr,
            sample_width=2,
            channels=1,
        )
        audio.export(str(dest), format="mp3", bitrate="192k")


if __name__ == "__main__":
    main()
