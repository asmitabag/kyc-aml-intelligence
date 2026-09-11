from pathlib import Path

import cv2
import matplotlib.pyplot as plt
import pandas as pd


METADATA_PATH = Path(
    "data/processed/document_regions/metadata.csv"
)


metadata = pd.read_csv(
    METADATA_PATH
)


# Pick the first example
row = metadata.iloc[750]


image = cv2.imread(
    row["processed_image"]
)

mask = cv2.imread(
    row["document_mask"],
    cv2.IMREAD_GRAYSCALE
)


if image is None:
    raise RuntimeError(
        "Unable to read image"
    )


if mask is None:
    raise RuntimeError(
        "Unable to read mask"
    )


# OpenCV loads BGR.
# Matplotlib expects RGB.

image_rgb = cv2.cvtColor(
    image,
    cv2.COLOR_BGR2RGB
)


# ---------------------------------------------------------
# Find document boundary
# ---------------------------------------------------------

contours, _ = cv2.findContours(
    mask,
    cv2.RETR_EXTERNAL,
    cv2.CHAIN_APPROX_SIMPLE
)


overlay = image.copy()


cv2.drawContours(
    overlay,
    contours,
    -1,
    (0, 255, 0),
    8
)


overlay_rgb = cv2.cvtColor(
    overlay,
    cv2.COLOR_BGR2RGB
)


# ---------------------------------------------------------
# Show results
# ---------------------------------------------------------

plt.figure(
    figsize=(15, 5)
)


plt.subplot(
    1,
    3,
    1
)

plt.imshow(
    image_rgb
)

plt.title(
    "Original MIDV Frame"
)

plt.axis(
    "off"
)


plt.subplot(
    1,
    3,
    2
)

plt.imshow(
    mask,
    cmap="gray"
)

plt.title(
    "MIDV Document Mask"
)

plt.axis(
    "off"
)


plt.subplot(
    1,
    3,
    3
)

plt.imshow(
    overlay_rgb
)

plt.title(
    "Document Boundary Overlay"
)

plt.axis(
    "off"
)


plt.tight_layout()

plt.show()