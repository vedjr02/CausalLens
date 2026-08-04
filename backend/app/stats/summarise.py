"""Turning raw samples into things a chart can draw."""

import numpy as np
from pydantic import BaseModel


class HistogramBin(BaseModel):
    start: float
    end: float
    centre: float
    count: int


class Distribution(BaseModel):
    """A histogram of one group, plus the summary lines worth drawing on it."""

    name: str
    bins: list[HistogramBin]
    mean: float
    std_dev: float
    n: int


def histogram(values: np.ndarray | list[float], name: str, bin_count: int = 30) -> Distribution:
    arr = np.asarray(values, dtype=float)
    counts, edges = np.histogram(arr, bins=bin_count)

    return Distribution(
        name=name,
        bins=[
            HistogramBin(
                start=float(edges[i]),
                end=float(edges[i + 1]),
                centre=float((edges[i] + edges[i + 1]) / 2),
                count=int(counts[i]),
            )
            for i in range(len(counts))
        ],
        mean=float(arr.mean()),
        std_dev=float(arr.std(ddof=1)) if arr.size > 1 else 0.0,
        n=int(arr.size),
    )


def shared_histogram(
    control: np.ndarray, treatment: np.ndarray, bin_count: int = 30
) -> tuple[Distribution, Distribution]:
    """Histogram both groups on a common set of bin edges.

    Two histograms with different edges cannot be honestly overlaid — the eye
    reads the bin widths as part of the shape.
    """
    combined = np.concatenate([control, treatment])
    edges = np.histogram_bin_edges(combined, bins=bin_count)

    def build(values: np.ndarray, name: str) -> Distribution:
        counts, _ = np.histogram(values, bins=edges)
        return Distribution(
            name=name,
            bins=[
                HistogramBin(
                    start=float(edges[i]),
                    end=float(edges[i + 1]),
                    centre=float((edges[i] + edges[i + 1]) / 2),
                    count=int(counts[i]),
                )
                for i in range(len(counts))
            ],
            mean=float(values.mean()),
            std_dev=float(values.std(ddof=1)) if values.size > 1 else 0.0,
            n=int(values.size),
        )

    return build(control, "Control"), build(treatment, "Treatment")
