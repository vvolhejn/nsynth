#!/usr/bin/env python3
"""Reorganize an NSynth dataset folder into per-instrument subdirectories, converting WAV to MP3."""

import argparse
import json
import os
from multiprocessing import Pool, cpu_count
from pathlib import Path

import librosa
import numpy as np
import soundfile as sf
from pydub import AudioSegment
from tqdm import tqdm


def wav_to_mp3_path(wav_name: str) -> str:
    """Convert e.g. 'bass_acoustic_000-024-025.wav' to 'bass_acoustic_000/024-025.mp3'."""
    stem = wav_name.removesuffix(".wav")
    parts = stem.rsplit("-", 2)
    return f"{parts[0]}/{parts[1]}-{parts[2]}.mp3"


def convert_one(args):
    src, dest, dest_dir = args
    dest_dir.mkdir(exist_ok=True)
    if dest.exists():
        return
    y, sr = librosa.load(str(src), sr=None)
    pcm = (y * 32767).astype(np.int16)
    audio = AudioSegment(
        pcm.tobytes(),
        frame_rate=sr,
        sample_width=2,
        channels=1,
    )
    audio.export(str(dest), format="mp3", bitrate="192k")


def main():
    parser = argparse.ArgumentParser(
        description="Reorganize NSynth dataset into per-instrument folders with MP3 conversion"
    )
    parser.add_argument("dataset_dir", help="Path to dataset folder (e.g. nsynth-test)")
    parser.add_argument(
        "--strudel",
        type=str,
        default=None,
        help="Path to strudel.json; only convert files referenced there",
    )
    parser.add_argument(
        "-j",
        "--jobs",
        type=int,
        default=cpu_count(),
        help="Number of parallel workers (default: CPU count)",
    )
    args = parser.parse_args()

    dataset_dir = Path(args.dataset_dir)
    audio_dir = dataset_dir / "audio"
    output_dir = dataset_dir / "audio2"
    output_dir.mkdir(exist_ok=True)

    if args.strudel:
        with open(args.strudel) as f:
            strudel = json.load(f)
        referenced = set()
        for key, value in strudel.items():
            if key == "_base":
                continue
            for note, samples in value.items():
                if isinstance(samples, list):
                    referenced.update(samples)
                else:
                    referenced.add(samples)
        print(f"Found {len(referenced)} unique files in {args.strudel}")
    else:
        examples_path = dataset_dir / "examples.json"
        with open(examples_path) as f:
            examples = json.load(f)
        referenced = {f"{note_str}.wav" for note_str in examples}

    tasks = []
    for wav_name in referenced:
        stem = wav_name.removesuffix(".wav")
        parts = stem.rsplit("-", 2)
        instrument = parts[0]
        suffix = f"{parts[1]}-{parts[2]}"

        src = audio_dir / wav_name
        if not src.exists():
            continue

        dest_dir = output_dir / instrument
        dest = dest_dir / f"{suffix}.mp3"
        tasks.append((src, dest, dest_dir))

    # Write strudel_reorganized.json with mp3 paths
    if args.strudel:
        new_strudel = {}
        for key, value in strudel.items():
            if key == "_base":
                new_strudel[key] = value
                continue
            new_instrument = {}
            for note, samples in value.items():
                if isinstance(samples, list):
                    new_instrument[note] = [wav_to_mp3_path(s) for s in samples]
                else:
                    new_instrument[note] = wav_to_mp3_path(samples)
            new_strudel[key] = new_instrument

        out_path = Path(args.strudel).with_name("strudel_reorganized.json")
        with open(out_path, "w") as f:
            json.dump(new_strudel, f)
        print(f"Wrote {out_path}")

    with Pool(args.jobs) as pool:
        list(
            tqdm(
                pool.imap_unordered(convert_one, tasks),
                total=len(tasks),
                desc="Converting",
            )
        )


if __name__ == "__main__":
    main()
