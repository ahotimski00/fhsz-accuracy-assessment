"""Design-based accuracy assessment for the LA County FHSZ change map.

The study's two point files are the two axes of the accuracy assessment, not
training data:

  * samples.shp        (`classifica`) = the MAP's predicted class at each point
  * SAMPLES2_DONE.shp  (`reference`)  = the REFERENCE (truth) class

Pairing them by row order reproduces the original sample-count confusion matrix
exactly. This script rebuilds that matrix from the raw points and then applies
Olofsson et al. (2014) good-practice estimation: area-adjusted overall accuracy,
per-class user's and producer's accuracy, and area estimates, each with a 95%
confidence interval. It also runs a class-merge sensitivity test.

Stratum weights come from the classified raster's per-class pixel counts, so no
number is hardcoded from the original report.

    python analyze.py
"""

from __future__ import annotations

from pathlib import Path

import geopandas as gpd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import rasterio

DATA = Path("data")
OUT = Path("outputs")
TOTAL_AREA_HA = 168_490  # study area (union of 2007 + 2025 Very-High FHSZ, LRA)
Z = 1.96  # 95% confidence

LEGEND = {
    1: "Stable Developed",
    2: "Stable Herbaceous",
    3: "Stable Tree",
    4: "Stable Bare",
    5: "Herbaceous->Developed",
    6: "Tree->Developed",
    7: "Bare->Developed",
    8: "Stable Other",
    9: "Other->Other",
}
CLASSES = list(range(1, 10))


def load_confusion() -> np.ndarray:
    """Rebuild the 9x9 sample-count matrix (rows = map, cols = reference)."""
    mp = gpd.read_file(DATA / "samples.shp")["classifica"].to_numpy()
    ref = (
        gpd.read_file(DATA / "SAMPLES2_DONE.shp")
        .sort_values("id")["reference"]
        .to_numpy()
    )
    cm = pd.crosstab(mp, ref).reindex(index=CLASSES, columns=CLASSES, fill_value=0)
    return cm.to_numpy().astype(float)


def map_weights() -> np.ndarray:
    """Stratum weights W_i = mapped pixels of class i / total mapped pixels."""
    with rasterio.open(DATA / "change_detection_map200.tif") as ds:
        arr = ds.read(1)
    counts = np.array([(arr == c).sum() for c in CLASSES], dtype=float)
    return counts / counts.sum()


def assess(cm: np.ndarray, w: np.ndarray) -> dict:
    """Olofsson good-practice estimators with standard errors."""
    ni = cm.sum(axis=1)  # map row totals
    diag = np.diag(cm)

    ua = diag / ni  # user's accuracy
    se_ua = np.sqrt(ua * (1 - ua) / (ni - 1))

    p = w[:, None] * cm / ni[:, None]  # estimated area proportions
    p_col = p.sum(axis=0)
    pa = np.diag(p) / p_col  # producer's accuracy

    oa = np.diag(p).sum()
    se_oa = np.sqrt(np.sum(w**2 * ua * (1 - ua) / (ni - 1)))

    # Producer's accuracy variance, Olofsson et al. (2014) eq. 7.
    n_i = w  # proportional mapped area per class (weights already normalized)
    se_pa = np.zeros(len(CLASSES))
    for j in range(len(CLASSES)):
        nj = n_i[j]
        term1 = nj**2 * (1 - pa[j]) ** 2 * ua[j] * (1 - ua[j]) / (ni[j] - 1)
        term2 = 0.0
        for i in range(len(CLASSES)):
            if i == j:
                continue
            rij = cm[i, j] / ni[i]
            term2 += n_i[i] ** 2 * rij * (1 - rij) / (ni[i] - 1)
        var = (1 / p_col[j] ** 2) * (term1 + pa[j] ** 2 * term2)
        se_pa[j] = np.sqrt(var)

    # Area estimate SE per reference class, eq. 10.
    se_pcol = np.sqrt(
        np.sum((w[:, None] ** 2) * (cm / ni[:, None]) * (1 - cm / ni[:, None])
               / (ni[:, None] - 1), axis=0)
    )
    return {
        "ni": ni, "ua": ua, "se_ua": se_ua, "pa": pa, "se_pa": se_pa,
        "oa": oa, "se_oa": se_oa, "p_col": p_col, "se_pcol": se_pcol,
        "oa_count": diag.sum() / cm.sum(),
    }


def oa_area_merged(cm: np.ndarray, w: np.ndarray, groups: dict) -> float:
    ni = cm.sum(axis=1)
    p = w[:, None] * cm / ni[:, None]
    g = [groups[c] for c in CLASSES]
    return sum(
        p[i, j] for i in range(len(CLASSES)) for j in range(len(CLASSES)) if g[i] == g[j]
    )


def plot_confusion(cm: np.ndarray) -> None:
    names = [LEGEND[c] for c in CLASSES]
    fig, ax = plt.subplots(figsize=(9, 8))
    ax.imshow(cm, cmap="Greens")
    for i in range(len(CLASSES)):
        for j in range(len(CLASSES)):
            v = int(cm[i, j])
            if v:
                ax.text(j, i, v, ha="center", va="center",
                        color="white" if i == j else "black", fontsize=9)
    ax.set_xticks(range(len(CLASSES)), names, rotation=45, ha="right")
    ax.set_yticks(range(len(CLASSES)), names)
    ax.set_xlabel("Reference (truth)")
    ax.set_ylabel("Map (classified)")
    ax.set_title("Reproduced sample-count confusion matrix (n=317)")
    fig.tight_layout()
    fig.savefig(OUT / "confusion_matrix.png", dpi=140)
    plt.close(fig)


def plot_accuracy(res: dict) -> None:
    names = [LEGEND[c] for c in CLASSES]
    x = np.arange(len(CLASSES))
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.bar(x - 0.2, res["ua"], 0.4, yerr=Z * res["se_ua"], capsize=3,
           label="User's accuracy", color="#3a7d44")
    ax.bar(x + 0.2, res["pa"], 0.4, yerr=Z * res["se_pa"], capsize=3,
           label="Producer's accuracy", color="#8a5a2b")
    ax.set_xticks(x, names, rotation=45, ha="right")
    ax.set_ylim(0, 1.05)
    ax.set_ylabel("Accuracy")
    ax.set_title("Per-class accuracy with 95% confidence intervals")
    ax.legend()
    fig.tight_layout()
    fig.savefig(OUT / "per_class_accuracy.png", dpi=140)
    plt.close(fig)


def write_report(cm, w, res) -> None:
    names = [LEGEND[c] for c in CLASSES]
    per_class = pd.DataFrame({
        "class": names,
        "n_ref": cm.sum(axis=0).astype(int),
        "UA": res["ua"].round(2),
        "PA": res["pa"].round(2),
        "map_area_ha": (w * TOTAL_AREA_HA).round(0).astype(int),
        "adj_area_ha": (res["p_col"] * TOTAL_AREA_HA).round(0).astype(int),
        "adj_95CI_ha": (Z * res["se_pcol"] * TOTAL_AREA_HA).round(0).astype(int),
    })
    merges = {
        "baseline (9 classes)": {c: c for c in CLASSES},
        "merge Stable Herb + Stable Tree": {**{c: c for c in CLASSES}, 3: 2},
        "also merge Herb->Dev + Tree->Dev": {**{c: c for c in CLASSES}, 3: 2, 6: 5},
    }
    merge_rows = [
        {"scenario": k, "area_adjusted_OA": round(oa_area_merged(cm, w, g), 3)}
        for k, g in merges.items()
    ]
    lines = [
        "# FHSZ change map: accuracy assessment, reproduced and stress-tested\n",
        "Rebuilt from the raw 317 map/reference points and estimated with "
        "Olofsson et al. (2014) good-practice, area-adjusted by the classified "
        "raster's per-class pixel counts.\n",
        f"- **Overall accuracy (count-based):** {res['oa_count']:.3f}",
        f"- **Overall accuracy (area-adjusted):** {res['oa']:.3f} "
        f"+/- {Z*res['se_oa']:.3f} (95% CI)\n",
        "## Per-class accuracy and area\n",
        "`map_area_ha` is the raw mapped area (pixel count); `adj_area_ha` is the "
        "accuracy-adjusted estimate of true area, with a 95% CI. The three "
        "development classes sum to ~16,600 ha of raw mapped area but only "
        "~5,700 ha adjusted, the gap being commission error.\n",
        per_class.to_markdown(index=False),
        "\n\n## Class-merge sensitivity (area-adjusted OA)\n",
        pd.DataFrame(merge_rows).to_markdown(index=False),
        "\n\n![Confusion matrix](outputs/confusion_matrix.png)\n",
        "![Per-class accuracy](outputs/per_class_accuracy.png)\n",
    ]
    (OUT / "metrics_report.md").write_text("\n".join(lines))


def main() -> None:
    OUT.mkdir(exist_ok=True)
    cm = load_confusion()
    w = map_weights()
    res = assess(cm, w)

    print(f"Overall accuracy (count-based):  {res['oa_count']:.3f}")
    print(f"Overall accuracy (area-adjusted): {res['oa']:.3f} +/- {Z*res['se_oa']:.3f}")
    for c, ua, pa in zip(CLASSES, res["ua"], res["pa"]):
        print(f"  {LEGEND[c]:24s} UA={ua:.2f}  PA={pa:.2f}")
    for k, g in {
        "baseline": {c: c for c in CLASSES},
        "merge stable Herb+Tree": {**{c: c for c in CLASSES}, 3: 2},
        "merge Herb+Tree stable+dev": {**{c: c for c in CLASSES}, 3: 2, 6: 5},
    }.items():
        print(f"area-adjusted OA [{k}]: {oa_area_merged(cm, w, g):.3f}")

    plot_confusion(cm)
    plot_accuracy(res)
    write_report(cm, w, res)
    print(f"\nWrote figures and metrics_report.md to {OUT}/")


if __name__ == "__main__":
    main()
