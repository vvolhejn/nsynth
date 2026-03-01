# NSynth for Strudel

WORK IN PROGRESS

A part of the [NSynth](https://magenta.withgoogle.com/datasets/nsynth) dataset formatted for use with the live coding language [Strudel](https://strudel.cc/).

The dataset is made available by Google Inc. under a [Creative Commons Attribution 4.0 International (CC BY 4.0) license](https://creativecommons.org/licenses/by/4.0/).

## Usage

TODO

## Development

First, download the train split of NSynth in the "json/wav" format from [here](https://magenta.withgoogle.com/datasets/nsynth#files).
Valid and test sets can be useful for debugging.

Some of the instruments have different reported velocities even though the audio is exactly or very nearly the same.
For these, we want to only list a single velocity for simplicity and clarity.
