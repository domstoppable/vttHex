
# Data files
See:
> Jasmin, Kyle and Dick, Frederic and Tierney, Adam (2019): *Multidimensional Battery of Prosody Perception*. Birkbeck College, University of London. doi: https://doi.org/10.18743/DATA.00037

Extract all `.wav` files to to `assets/audio/` with no deeper folders. E.g.:
* `MBOPP/assets/audio/focus20_pitch10_time10.wav`
* `MBOPP/assets/audio/phrase9_pitch70_time70.wav`
* etc.

## Generate TextGrids
Requirements:
* [Montreal Forced Aligner](https://github.com/MontrealCorpusTools/Montreal-Forced-Aligner/releases)
  * Also find `libgfortran.so.3` and plot it in the `lib/` directory
* [librispeech-lexicon.txt](https://drive.google.com/open?id=1dAvxdsHWbtA1ZIh3Ex9DPn9Nemx9M1-L)

Each `.wav` needs to have a matching `.lab` in order to generate TextGrids

To generate Lab files from filenames:
```bash
python3 -m vttHex.generateLabFromFilenames *.wav
```

To generate lab files for MBOPP stimuli:
```bash
python3 -m vttHex.mbopp_data
```

Then generate `.TextGrid` files
```bash
MFA=/path/to/mfa
WAV_DIR=path/to/audio/and/.lab/files/
LEX_FILE=path/to/librispeech-lexicon.txt
GRID_DIR=textgrid/output/path/

"$MFA/bin/mfa_align" -v -q -j 16 -d "$WAV_DIR" "$LEX_FILE" english "$GRID_DIR"
cat "$WAV_DIR/oovs_found.txt"
```
Check `$WAV_DIR/oovs_found.txt` for missing pronunciations. If any, add them to the lexicon file and re-run


### Convert .TextGrid files to .csv
```bash
cd vttHex/assets/audio/
python ~/code/vttHex/software/vttHex/textgridToCSV.py *.TextGrid
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

## Make VTT binary
