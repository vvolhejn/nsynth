"""Classify instruments by whether velocity affects their timbre.

Reads the JSON output of compare_all.py and reports, for each instrument,
the median spectral distance across consecutive velocity pairs. Instruments
with a median distance >= threshold are classified as velocity-sensitive.
"""

import argparse
import json
import statistics
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(
        description="Classify instruments by velocity sensitivity"
    )
    parser.add_argument("results_json", type=Path, nargs="+")
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.03,
        help="average distance threshold",
    )
    args = parser.parse_args()

    # Merge instruments across all input files
    all_distances: dict[str, list[float]] = {}
    for path in args.results_json:
        if not path.exists():
            print(f"Error: {path} not found", file=sys.stderr)
            sys.exit(1)
        with open(path) as f:
            data = json.load(f)
        for instrument, pitches in data["instruments"].items():
            dists = all_distances.setdefault(instrument, [])
            for pitch_dists in pitches.values():
                if isinstance(pitch_dists, list):
                    dists.extend(pitch_dists)
                else:
                    assert isinstance(pitch_dists, (int, float)), (
                        f"Unexpected type for distance: {type(pitch_dists)}"
                    )
                    dists.append(pitch_dists)  # just a float

    # Classify and report
    results = []
    for instrument in sorted(all_distances):
        dists = all_distances[instrument]
        median = statistics.median(dists)
        results.append((instrument, median))

    # Sort by median descending
    results.sort(key=lambda x: x[1], reverse=True)

    matters = [(i, m) for i, m in results if m >= args.threshold]
    does_not_matter = [(i, m) for i, m in results if m < args.threshold]

    print(f"Velocity matters ({len(matters)}):")
    for instrument, median in matters:
        print(f"  {instrument}: {median:.8f}")

    print(f"\nVelocity does not matter ({len(does_not_matter)}):")
    for instrument, median in does_not_matter:
        print(f"  {instrument}: {median:.8f}")


if __name__ == "__main__":
    main()
