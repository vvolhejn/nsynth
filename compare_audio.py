"""Compare two audio files by their spectral characteristics.

Uses MFCC (Mel-frequency cepstral coefficients) to capture timbral shape,
normalized to be amplitude-invariant. This distinguishes instruments whose
timbre changes with dynamics (e.g. acoustic bass) from those that stay
consistent (e.g. organ).
"""

import argparse
import sys
from pathlib import Path

import librosa
import numpy as np


def compute_normalized_mfcc(path: str | Path, n_mfcc: int = 20) -> np.ndarray:
    """Load audio and return amplitude-normalized MFCCs (n_mfcc x T)."""
    y, sr = librosa.load(path, sr=None)
    # Normalize amplitude so we compare shape, not loudness
    y = y / (np.max(np.abs(y)) + 1e-10)
    mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=n_mfcc)
    return mfcc


def spectral_distance(path_a: str | Path, path_b: str | Path) -> float:
    """Max cosine distance across time frames between MFCC profiles."""
    a = compute_normalized_mfcc(path_a)  # (n_mfcc, T_a)
    b = compute_normalized_mfcc(path_b)  # (n_mfcc, T_b)
    # Truncate to the shorter length so frames align
    T = min(a.shape[1], b.shape[1])
    a, b = a[:, :T], b[:, :T]
    # Cosine similarity per time frame
    dots = np.sum(a * b, axis=0)
    norms = np.linalg.norm(a, axis=0) * np.linalg.norm(b, axis=0) + 1e-10
    cos_dist = 1.0 - dots / norms
    return float(np.max(cos_dist))


def main():
    parser = argparse.ArgumentParser(
        description="Compare two audio files by spectral similarity"
    )
    parser.add_argument("file_a", type=Path)
    parser.add_argument("file_b", type=Path)
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.0001,
        help="cosine distance threshold (default: 0.0001)",
    )
    args = parser.parse_args()

    for p in (args.file_a, args.file_b):
        if not p.exists():
            print(f"Error: {p} not found", file=sys.stderr)
            sys.exit(1)

    dist = spectral_distance(args.file_a, args.file_b)
    same = dist < args.threshold

    print(f"Distance: {dist:.6f}")
    print(f"Threshold: {args.threshold}")
    print(f"Result: {'SAME' if same else 'DIFFERENT'}")
    sys.exit(0 if same else 1)


if __name__ == "__main__":
    main()
