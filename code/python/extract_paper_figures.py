"""Extract the cited spectral figure from the supplied Beaudry et al. PDF.

The source PDF is intentionally kept outside the website repository in ../papers.
This script records precisely which source page was rendered for the course figure.
"""

from pathlib import Path

import pymupdf


COURSE = Path(__file__).resolve().parents[2]
SOURCE = COURSE.parent / "papers" / "Putting the Cycle Back into Business Cycle Analysis (2).pdf"
EMPIRICAL_OUTPUT = COURSE / "figures" / "frequency" / "beaudry-galizia-portier-spectra.png"
MODELS_OUTPUT = COURSE / "figures" / "frequency" / "beaudry-galizia-portier-dsge-spectra.png"
CLIMATE_SOURCE = COURSE.parent / "papers" / "Sustainable Development - 2026 - Yin - The Impact of Climate Risks on Growth‐at‐Risk.pdf"
CLIMATE_OUTPUT = COURSE / "figures" / "growth-at-risk" / "yin-climate-physical-risk-distribution.png"

# PDF page 13 contains Figure 3 (several empirical spectra); page 15 contains
# Figure 4 (hours spectra from six benchmark DSGE models). Cropping retains the
# figures themselves rather than embedding a full article page in the course.
document = pymupdf.open(SOURCE)
scale = pymupdf.Matrix(2.4, 2.4)
document[12].get_pixmap(matrix=scale, clip=pymupdf.Rect(35, 55, 525, 405), alpha=False).save(EMPIRICAL_OUTPUT)
document[14].get_pixmap(matrix=scale, clip=pymupdf.Rect(45, 55, 525, 360), alpha=False).save(MODELS_OUTPUT)

# Page 11 contains the article's Figure 3.  The crop retains the physical-risk
# density comparison and its caption, while omitting the unrelated policy-risk
# figure placed above it on the same page.
climate = pymupdf.open(CLIMATE_SOURCE)
climate[10].get_pixmap(
    matrix=scale,
    clip=pymupdf.Rect(35, 378, 560, 785),
    alpha=False,
).save(CLIMATE_OUTPUT)
