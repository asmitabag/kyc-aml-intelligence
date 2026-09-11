from pathlib import Path
import json

import cv2
import numpy as np
import pandas as pd


# ---------------------------------------------------------
# Paths
# ---------------------------------------------------------

MIDV_METADATA = Path(
    "data/processed/midv_base/metadata.csv"
)

OUTPUT_ROOT = Path(
    "data/processed/document_regions"
)

OUTPUT_MASKS = OUTPUT_ROOT / "masks"

OUTPUT_MASKS.mkdir(
    parents=True,
    exist_ok=True
)


# ---------------------------------------------------------
# Load MIDV metadata created in Step 8
# ---------------------------------------------------------

metadata = pd.read_csv(
    MIDV_METADATA
)

print(
    f"Loaded {len(metadata)} processed MIDV images"
)


records = []


# ---------------------------------------------------------
# Helper: derive annotation path
# ---------------------------------------------------------

def get_annotation_path(source_path: Path) -> Path:
    """
    Converts a MIDV image path such as:

    data/raw/midv500/01_alb_id/images/CA/CA01_12.tif

    into:

    data/raw/midv500/01_alb_id/ground_truth/CA/CA01_12.json
    """

    path_parts = list(source_path.parts)

    try:
        images_index = path_parts.index("images")
    except ValueError:
        raise ValueError(
            f"'images' not found in path: {source_path}"
        )

    path_parts[images_index] = "ground_truth"

    annotation_path = Path(
        *path_parts
    ).with_suffix(".json")

    return annotation_path


# ---------------------------------------------------------
# Process every image
# ---------------------------------------------------------

for index, row in metadata.iterrows():

    source_path = Path(
        row["source_path"]
    )

    processed_path = Path(
        row["processed_path"]
    )

    sample_id = row["sample_id"]


    # -----------------------------------------------------
    # Find corresponding annotation
    # -----------------------------------------------------

    annotation_path = get_annotation_path(
        source_path
    )


    if not annotation_path.exists():

        print(
            f"WARNING: annotation missing for "
            f"{source_path}"
        )

        continue


    # -----------------------------------------------------
    # Load image
    # -----------------------------------------------------

    image = cv2.imread(
        str(processed_path)
    )


    if image is None:

        print(
            f"WARNING: unable to read "
            f"{processed_path}"
        )

        continue


    height, width = image.shape[:2]


    # -----------------------------------------------------
    # Load JSON ground truth
    # -----------------------------------------------------

    with open(
        annotation_path,
        "r",
        encoding="utf-8"
    ) as file:

        annotation = json.load(file)


    if "quad" not in annotation:

        print(
            f"WARNING: no 'quad' found in "
            f"{annotation_path}"
        )

        continue


    quad = np.array(
        annotation["quad"],
        dtype=np.float32
    )


    # -----------------------------------------------------
    # Validate the annotation
    # -----------------------------------------------------

    if quad.shape != (4, 2):

        print(
            f"WARNING: invalid quad shape "
            f"{quad.shape} in {annotation_path}"
        )

        continue


    # Some MIDV points can be outside the image.
    # Clip them to valid pixel coordinates.

    quad[:, 0] = np.clip(
        quad[:, 0],
        0,
        width - 1
    )

    quad[:, 1] = np.clip(
        quad[:, 1],
        0,
        height - 1
    )


    quad_int = quad.astype(
        np.int32
    )


    # -----------------------------------------------------
    # Create binary document mask
    # -----------------------------------------------------

    mask = np.zeros(
        (height, width),
        dtype=np.uint8
    )


    cv2.fillPoly(
        mask,
        [quad_int],
        255
    )


    # -----------------------------------------------------
    # Save mask
    # -----------------------------------------------------

    mask_name = (
        f"{sample_id}_document_mask.png"
    )

    mask_path = (
        OUTPUT_MASKS / mask_name
    )


    cv2.imwrite(
        str(mask_path),
        mask
    )


    # -----------------------------------------------------
    # Calculate document area
    # -----------------------------------------------------

    document_pixels = np.count_nonzero(
        mask
    )

    total_pixels = (
        height * width
    )

    document_fraction = (
        document_pixels / total_pixels
    )


    # -----------------------------------------------------
    # Save metadata
    # -----------------------------------------------------

    records.append(
        {
            "sample_id": sample_id,
            "processed_image": str(
                processed_path
            ),
            "annotation_path": str(
                annotation_path
            ),
            "document_mask": str(
                mask_path
            ),
            "width": width,
            "height": height,
            "document_fraction": (
                document_fraction
            ),
            "p1_x": quad_int[0][0],
            "p1_y": quad_int[0][1],
            "p2_x": quad_int[1][0],
            "p2_y": quad_int[1][1],
            "p3_x": quad_int[2][0],
            "p3_y": quad_int[2][1],
            "p4_x": quad_int[3][0],
            "p4_y": quad_int[3][1],
        }
    )


# ---------------------------------------------------------
# Save metadata
# ---------------------------------------------------------

region_metadata = pd.DataFrame(
    records
)


metadata_output = (
    OUTPUT_ROOT / "metadata.csv"
)


region_metadata.to_csv(
    metadata_output,
    index=False
)


# ---------------------------------------------------------
# Summary
# ---------------------------------------------------------

print("\n----------------------------------")
print("DOCUMENT MASK CREATION COMPLETE")
print("----------------------------------")

print(
    f"Successfully processed: "
    f"{len(region_metadata)}"
)

print(
    f"Skipped: "
    f"{len(metadata) - len(region_metadata)}"
)

print(
    f"Masks saved to: "
    f"{OUTPUT_MASKS}"
)

print(
    f"Metadata saved to: "
    f"{metadata_output}"
)


if not region_metadata.empty:

    print(
        "\nAverage fraction of image "
        "occupied by document:"
    )

    print(
        round(
            region_metadata[
                "document_fraction"
            ].mean(),
            4
        )
    )