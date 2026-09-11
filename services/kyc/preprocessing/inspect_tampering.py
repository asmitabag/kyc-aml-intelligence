from pathlib import Path

import cv2
import matplotlib.pyplot as plt
import pandas as pd


METADATA_PATH = Path(
    "data/processed/forgery_dataset/metadata.csv"
)


metadata = pd.read_csv(
    METADATA_PATH
)


tampered_rows = metadata[
    metadata["is_tampered"] == 1
]


row = tampered_rows.iloc[0]


source = cv2.imread(
    row["source_image"]
)

tampered = cv2.imread(
    row["output_image"]
)

mask = cv2.imread(
    row["mask_path"],
    cv2.IMREAD_GRAYSCALE
)


source = cv2.cvtColor(
    source,
    cv2.COLOR_BGR2RGB
)

tampered = cv2.cvtColor(
    tampered,
    cv2.COLOR_BGR2RGB
)


plt.figure(figsize=(15, 5))


plt.subplot(1, 3, 1)
plt.imshow(source)
plt.title("Original")
plt.axis("off")


plt.subplot(1, 3, 2)
plt.imshow(tampered)
plt.title(
    f"Tampered: {row['tamper_type']}"
)
plt.axis("off")


plt.subplot(1, 3, 3)
plt.imshow(
    mask,
    cmap="gray"
)
plt.title("Ground Truth Mask")
plt.axis("off")


plt.tight_layout()

plt.show()