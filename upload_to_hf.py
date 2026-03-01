"""Upload the selected NSynth audio files and strudel.json to Hugging Face."""

import shutil
import tempfile
from pathlib import Path

from huggingface_hub import HfApi
from tqdm import tqdm

REPO_ID = "vvolhejn/nsynth"
EXPORTED_JSON = Path("strudel.json")
AUDIO_DIR = Path("nsynth-train/audio2")  # Must be relative!


def get_referenced_wavs(exported_json: Path) -> list[str]:
    import json

    data = json.loads(exported_json.read_text())
    wavs = set()
    for key, value in data.items():
        if key == "_base":
            continue
        for note, samples in value.items():
            if isinstance(samples, list):
                wavs.update(samples)
            else:
                wavs.add(samples)
    unique = sorted(wavs)
    print(f"Found {len(unique)} unique wav files referenced in {exported_json}")
    return unique


def main():
    api = HfApi()

    wavs = get_referenced_wavs(EXPORTED_JSON)

    # Verify all files exist
    missing = [w for w in wavs if not (AUDIO_DIR / w).exists()]
    if missing:
        print(f"ERROR: {len(missing)} referenced files not found:")
        for m in missing[:10]:
            print(f"  {m}")
        return

    total_size = sum((AUDIO_DIR / w).stat().st_size for w in wavs)
    print(f"\nWill upload to https://huggingface.co/datasets/{REPO_ID}:")
    print(f"  - {EXPORTED_JSON}")
    print(f"  - {len(wavs)} audio files in {AUDIO_DIR}")
    print(f"  - Total size: {total_size / 1024 / 1024:.1f} MB")

    response = input("\nProceed? [y/N] ").strip().lower()
    if response != "y":
        print("Aborted.")
        return

    # Stage files in a temp directory matching the desired repo layout
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)

        shutil.copy2(EXPORTED_JSON, tmp / EXPORTED_JSON.name)

        audio_dest = tmp / AUDIO_DIR
        audio_dest.mkdir(parents=True)
        for wav in tqdm(wavs, desc="Staging files"):
            (audio_dest / wav).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(AUDIO_DIR / wav, audio_dest / wav)

        print(f"Uploading to https://huggingface.co/datasets/{REPO_ID}...")

        api.upload_large_folder(
            folder_path=tmpdir, repo_id=REPO_ID, repo_type="dataset"
        )

    print("Done!")


if __name__ == "__main__":
    main()
