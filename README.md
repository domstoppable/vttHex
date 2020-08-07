
# Data files
See:
> Jasmin, Kyle and Dick, Frederic and Tierney, Adam (2019): *Multidimensional Battery of Prosody Perception*. Birkbeck College, University of London. doi: https://doi.org/10.18743/DATA.00037

Extract all `.wav` files to to `assets/audio/` with no deeper folders. E.g.:
* `MBOPP/assets/audio/focus20_pitch10_time10.wav`
* `MBOPP/assets/audio/phrase9_pitch70_time70.wav`
* etc.

## Generate TextGrids
Requirements:
* https://github.com/MontrealCorpusTools/Montreal-Forced-Aligner/
* librispeech-lexicon
```bash
# Generate .lab files
python3 -m vttHex.mbopp_data
# Generate .TextGrid files
path/to/mfa/bin/mfa_align -v -q -j 16 -d vttHex/assets/audio/ ./librispeech-lexicon.txt english vttHex/assets/audio/
```

## Generate pitch data
Requirements:
* https://github.com/ardaillon/FCN-f0
* tensorflow
* sampy
```bash
cd vttHex/assets/audio/
python3 path/to/FCN-f0/FCN-f0.py ./*.wav -m 929
```
