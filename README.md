# NSynth for Strudel

WORK IN PROGRESS

A part of the [NSynth](https://magenta.withgoogle.com/datasets/nsynth) dataset formatted for use with the live coding language [Strudel](https://strudel.cc/).

The data itself is hosted on Hugging Face [here](https://huggingface.co/datasets/vvolhejn/nsynth), because it'd be too big for GitHub.

## Usage

TODO

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