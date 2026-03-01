# NSynth for Strudel

A part of the [NSynth](https://magenta.withgoogle.com/datasets/nsynth) dataset formatted for use with the live coding language [Strudel](https://strudel.cc/).

The data itself is hosted on Hugging Face [here](https://huggingface.co/datasets/vvolhejn/nsynth), because it'd be too big for GitHub.

## Usage

```js
samples('github:vvolhejn/nsynth')

// each n from 0 to 4 maps to a velocity, changing the timbre
$: n("0 1 2 3 4@4") 
  .note("<g1 f2 e3 d4>")
  .sound("bass_acoustic_000")
  .release(0.1) // otherwise, each sample plays for 3s
```

NSynth instruments are recorded at multiple MIDI velocities. On piano/keys, this corresponds to how hard the key was pressed, and gives us more expressive instruments.

Strudel also has `.velocity()` but it's normally just a gain multiplier, so above we have to use `.n()` to choose between the samples.
You can use the following workaround to get a MIDI-like velocity working natively:

```js
setCpm(160/4)
samples('github:vvolhejn/nsynth')

$: note("d4 a3 b3 g3 f#3")
  .sound("guitar_electronic_004")
  .velocity(saw.slow(4)) // Velocity should be in [0,1]
  .withValue(x=>Object.assign(x, {n: Math.floor(x.velocity * 4), velocity: 0.5 + x.velocity * 0.5}))
  .release(0.1)
```

### List of available instruments

The instruments in _italics_ are only sampled at one velocity in the dataset, so `.n()` has no effect.

bass_acoustic_000, _bass_electronic_000_, _bass_electronic_001_, bass_electronic_002, bass_electronic_003, bass_electronic_004, bass_synthetic_000, bass_synthetic_001, _bass_synthetic_002_, bass_synthetic_003, bass_synthetic_004, brass_acoustic_000, brass_acoustic_001, brass_acoustic_002, brass_acoustic_003, brass_acoustic_004, flute_acoustic_000, _flute_acoustic_001_, flute_acoustic_003, flute_acoustic_004, _flute_acoustic_005_, flute_synthetic_001, flute_synthetic_002, _flute_synthetic_004_, _flute_synthetic_005_, flute_synthetic_006, guitar_acoustic_000, guitar_acoustic_001, guitar_acoustic_002, _guitar_acoustic_003_, guitar_acoustic_004, guitar_electronic_000, guitar_electronic_001, _guitar_electronic_002_, guitar_electronic_003, guitar_electronic_004, guitar_synthetic_000, guitar_synthetic_001, guitar_synthetic_002, guitar_synthetic_003, guitar_synthetic_004, keyboard_acoustic_000, keyboard_acoustic_001, keyboard_acoustic_002, keyboard_acoustic_003, keyboard_acoustic_005, keyboard_electronic_000, _keyboard_electronic_004_, keyboard_electronic_005, keyboard_electronic_006, keyboard_electronic_007, _keyboard_synthetic_001_, _keyboard_synthetic_002_, keyboard_synthetic_003, _keyboard_synthetic_004_, _keyboard_synthetic_005_, mallet_acoustic_000, mallet_acoustic_001, mallet_acoustic_002, mallet_acoustic_003, mallet_acoustic_004, mallet_electronic_000, mallet_electronic_001, mallet_electronic_002, mallet_electronic_003, mallet_electronic_004, mallet_synthetic_000, mallet_synthetic_001, mallet_synthetic_002, mallet_synthetic_003, mallet_synthetic_004, _organ_electronic_000_, organ_electronic_002, organ_electronic_003, _organ_electronic_004_, _organ_electronic_005_, reed_acoustic_000, reed_acoustic_001, reed_acoustic_002, reed_acoustic_003, reed_acoustic_004, reed_synthetic_001, string_acoustic_000, string_acoustic_001, string_acoustic_002, string_acoustic_003, string_acoustic_004, synth_lead_synthetic_000, synth_lead_synthetic_001, synth_lead_synthetic_002, synth_lead_synthetic_003, synth_lead_synthetic_004, vocal_acoustic_001, vocal_acoustic_002, _vocal_acoustic_003_, _vocal_acoustic_004_, vocal_acoustic_005, _vocal_synthetic_000_, vocal_synthetic_001, vocal_synthetic_002, vocal_synthetic_004, vocal_synthetic_005


## Development

First, download the train split of NSynth in the "json/wav" format from [here](https://magenta.withgoogle.com/datasets/nsynth#files).
Watch out, it's 22 GB when compressed and 35 GB uncompressed!
Valid and test sets can be useful for debugging.

Some of the instruments have different reported velocities even though the audio is exactly or very nearly the same.
For these, we want to only list a single velocity for simplicity and clarity.
Use:

```python
uv run compute_velocity_matters.py nsynth-train/examples.json > velocity_matters_train.json
```

Afterwards, we can generate the `strudel.json` file:

```python
uv run convert_to_strudel.py nsynth-train/examples.json \
    --comparison-json velocity_matters_train.json \
    --max-per-category 5 > strudel.json
```

It's also possible to test without uploading by using `--base-url`, hosting the files using a local server and running Strudel locally as well.

Reorganize the dataset so that the directories aren't too big (Hugging Face doesn't like that), converting to mp3 along the way:

```python
uv run reorganize_dataset.py nsynth-train/ --strudel strudel.json
mv strudel_reorganized.json strudel.json # updated with the new paths
```

Then upload to Hugging Face:

```python
uv run upload_to_hf.py
```

### Frequently asked questions (probably by future me)

- **Why not use the test/valid set?** They don't cover the notes and velocities nearly as densely for the given instruments, for some reason. The train set seems to have maybe 99% velocity/pitch combinations for a given instrument, whereas the two have maybe 20%
- **Why reorganize the directory structure to one directory per instrument?** Hugging Face doesn't allow you to have more than 10k files in one directory
- **Why do we only use some pitches and not all of them?** This matches the behavior of [Strudel's `piano`](https://github.com/felixroos/dough-samples/blob/9eacfc86ec4393e68a463ff52b01c19cfaa77f38/piano.json), plus it does decrease the number of network requests needed

## License

The dataset is made available by Google Inc. under a [Creative Commons Attribution 4.0 International (CC BY 4.0) license](https://creativecommons.org/licenses/by/4.0/).

The code itself is CC0.