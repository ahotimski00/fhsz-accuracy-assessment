# FHSZ change map: accuracy assessment, reproduced and stress-tested

A rigorous follow-up to the LA County Fire Hazard Severity Zone change-detection
study. It rebuilds the study's accuracy assessment from the raw sample points and
applies Olofsson et al. (2014) good-practice estimation: area-adjusted overall
accuracy, per-class user's and producer's accuracy, and area estimates, each with
a 95% confidence interval, plus a class-merge sensitivity test.

## Data design

The study's two point files are the two axes of the accuracy assessment, not
training data:

- **`samples.shp`** (`classifica`) = the map's predicted class at each point
- **`SAMPLES2_DONE.shp`** (`reference`) = the reference (truth) class

Pairing them by row order reproduces the original sample-count confusion matrix
exactly (overall agreement 178/317 = 0.562). Stratum weights come from the
classified raster's per-class pixel counts, so nothing is hardcoded from the
original report.

## Run

```bash
python3.13 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
python analyze.py       # writes outputs/
```

Requires `samples.shp`, `SAMPLES2_DONE.shp`, and `change_detection_map200.tif`
under `data/` (not tracked).

## What it shows

**1. Faithful reproduction.** Area-adjusted overall accuracy is **0.67 +/- 0.05**,
matching the study's reported figure, and the per-class producer's accuracies
match class-for-class.

**2. The rare development classes are unreliable.** Tree->Developed and
Bare->Developed have user's accuracy of 0.08 and 0.12 with confidence intervals
that nearly span the whole 0-1 range: they have only 3 and 6 reference points.
Their individual accuracy cannot be pinned down from this sample.

**3. Merging spectrally-similar classes recovers a lot of "error."** Collapsing
Stable Herbaceous + Stable Tree lifts area-adjusted overall accuracy from 0.67 to
**0.79**. Most of the disagreement is green-vegetation confusion, not
development-detection error.

| scenario | area-adjusted OA |
|---|---|
| baseline (9 classes) | 0.671 |
| merge Stable Herb + Stable Tree | 0.787 |
| also merge Herb->Dev + Tree->Dev | 0.788 |

**4. Raw map area overstates new development.** The map's raw Bare->Developed area
is ~12,000 ha, but that class's user's accuracy is only 0.12, so most of those
pixels are commission error. The area-adjusted estimate is ~2,000 ha with a wide
interval. Summed across the three development classes, the raw map area of
~16,600 ha corrects to a design-based estimate of roughly ~5,700 ha, and the
qualitative finding (development inside hazard zones) holds while the magnitude is
much smaller and uncertain. This is exactly why good-practice reporting adjusts
for accuracy rather than counting pixels.

## Limitations

- The rare development classes rest on only 3-6 reference points, so their
  per-class accuracy and adjusted area carry wide intervals regardless of method;
  more reference points are the only real fix.

The estimates are design-based on the study's stratified random sample, so the
confidence intervals are design-unbiased and do not depend on the spatial
arrangement of the points.

*Legend confirmed against the study's 9-class schema. The original slide's
user's-accuracy row appears mislabeled; the values here are computed directly
(diagonal / mapped-class total).*
