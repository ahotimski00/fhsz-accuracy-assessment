# FHSZ change map: accuracy assessment, reproduced and stress-tested

Rebuilt from the raw 317 map/reference points and estimated with Olofsson et al. (2014) good-practice, area-adjusted by the classified raster's per-class pixel counts.

- **Overall accuracy (count-based):** 0.562
- **Overall accuracy (area-adjusted):** 0.671 +/- 0.053 (95% CI)

## Per-class accuracy and area

`map_area_ha` is the raw mapped area (pixel count); `adj_area_ha` is the accuracy-adjusted estimate of true area, with a 95% CI. The three development classes sum to ~16,600 ha of raw mapped area but only ~5,700 ha adjusted, the gap being commission error.

| class                 |   n_ref |   UA |   PA |   map_area_ha |   adj_area_ha |   adj_95CI_ha |
|:----------------------|--------:|-----:|-----:|--------------:|--------------:|--------------:|
| Stable Developed      |      78 | 0.84 | 0.71 |         44107 |         51818 |          7243 |
| Stable Herbaceous     |     120 | 0.83 | 0.73 |         74096 |         85065 |          8425 |
| Stable Tree           |      13 | 0.3  | 0.82 |         29136 |         10747 |          5246 |
| Stable Bare           |      29 | 0.6  | 0.03 |           382 |          7354 |          4089 |
| Herbaceous->Developed |      30 | 0.4  | 0.61 |          4336 |          2826 |          1928 |
| Tree->Developed       |       3 | 0.08 | 0.02 |           255 |           902 |          1729 |
| Bare->Developed       |       6 | 0.12 | 0.74 |         12276 |          1994 |          1693 |
| Stable Other          |      17 | 0.52 | 0.36 |          3846 |          5528 |          3515 |
| Other->Other          |      21 | 0.52 | 0.01 |            54 |          2256 |          2230 |


## Class-merge sensitivity (area-adjusted OA)

| scenario                         |   area_adjusted_OA |
|:---------------------------------|-------------------:|
| baseline (9 classes)             |              0.671 |
| merge Stable Herb + Stable Tree  |              0.787 |
| also merge Herb->Dev + Tree->Dev |              0.788 |


![Confusion matrix](outputs/confusion_matrix.png)

![Per-class accuracy](outputs/per_class_accuracy.png)
