from pathlib import Path
import random
import shutil

import cv2
import numpy as np
import pandas as pd


# =========================================================
# CONFIGURATION
# =========================================================

SPLITS_ROOT = Path(
    "data/processed/splits"
)

OUTPUT_ROOT = Path(
    "data/processed/final_forgery_dataset"
)

RANDOM_SEED = 42

random.seed(RANDOM_SEED)
np.random.seed(RANDOM_SEED)

TAMPER_TYPES = [
    "local_blur",
    "local_brightness",
    "copy_move",
    "patch_replace",
]


# =========================================================
# BASIC UTILITIES
# =========================================================

def load_image(path):

    image = cv2.imread(
        str(path)
    )

    if image is None:
        raise RuntimeError(
            f"Could not read image: {path}"
        )

    return image


def load_mask(path):

    mask = cv2.imread(
        str(path),
        cv2.IMREAD_GRAYSCALE
    )

    if mask is None:
        raise RuntimeError(
            f"Could not read mask: {path}"
        )

    return mask


def empty_mask(height, width):

    return np.zeros(
        (height, width),
        dtype=np.uint8
    )


# =========================================================
# DOCUMENT BOUNDING BOX
# =========================================================

def document_bbox(mask):

    ys, xs = np.where(
        mask > 0
    )

    if len(xs) == 0:

        raise RuntimeError(
            "Document mask contains no visible pixels"
        )

    x1 = int(
        xs.min()
    )

    y1 = int(
        ys.min()
    )

    x2 = int(
        xs.max()
    ) + 1

    y2 = int(
        ys.max()
    ) + 1

    return (
        x1,
        y1,
        x2,
        y2
    )


# =========================================================
# SAFE RANDOM INTEGER
# =========================================================

def safe_randint(
    minimum,
    maximum
):

    if maximum <= minimum:

        return minimum

    return random.randint(
        minimum,
        maximum
    )


# =========================================================
# CHOOSE REGION INSIDE DOCUMENT
# =========================================================

def choose_region(mask):

    (
        doc_x1,
        doc_y1,
        doc_x2,
        doc_y2
    ) = document_bbox(
        mask
    )


    doc_width = max(
        1,
        doc_x2 - doc_x1
    )

    doc_height = max(
        1,
        doc_y2 - doc_y1
    )


    # ---------------------------------------------
    # Calculate safe region sizes
    # ---------------------------------------------

    min_width = max(
        1,
        int(
            doc_width * 0.08
        )
    )

    max_width = max(
        1,
        int(
            doc_width * 0.25
        )
    )

    max_width = min(
        max_width,
        doc_width
    )

    min_width = min(
        min_width,
        max_width
    )


    min_height = max(
        1,
        int(
            doc_height * 0.08
        )
    )

    max_height = max(
        1,
        int(
            doc_height * 0.25
        )
    )

    max_height = min(
        max_height,
        doc_height
    )

    min_height = min(
        min_height,
        max_height
    )


    # ---------------------------------------------
    # Try random regions
    # ---------------------------------------------

    for _ in range(300):

        region_width = safe_randint(
            min_width,
            max_width
        )

        region_height = safe_randint(
            min_height,
            max_height
        )


        max_x_start = (
            doc_x2
            - region_width
        )

        max_y_start = (
            doc_y2
            - region_height
        )


        x1 = safe_randint(
            doc_x1,
            max_x_start
        )

        y1 = safe_randint(
            doc_y1,
            max_y_start
        )


        x2 = min(
            doc_x2,
            x1 + region_width
        )

        y2 = min(
            doc_y2,
            y1 + region_height
        )


        if (
            x2 <= x1
            or y2 <= y1
        ):

            continue


        region_mask = mask[
            y1:y2,
            x1:x2
        ]


        if region_mask.size == 0:

            continue


        visible_pixels = (
            np.count_nonzero(
                region_mask
            )
        )


        if visible_pixels >= 1:

            return (
                x1,
                y1,
                x2,
                y2
            )


    # ---------------------------------------------
    # Guaranteed fallback
    #
    # The modification is later applied only to
    # white pixels of the document mask, so using
    # the whole bounding box is still safe.
    # ---------------------------------------------

    return (
        doc_x1,
        doc_y1,
        doc_x2,
        doc_y2
    )


# =========================================================
# BUILD EXACT TAMPER MASK
# =========================================================

def create_changed_mask(
    original,
    modified,
    document_mask
):

    changed = np.any(
        original != modified,
        axis=2
    )

    changed = (
        changed
        &
        (document_mask > 0)
    )


    output_mask = np.zeros(
        document_mask.shape,
        dtype=np.uint8
    )

    output_mask[
        changed
    ] = 255


    if not np.any(
        changed
    ):

        return (
            None,
            None
        )


    ys, xs = np.where(
        changed
    )


    bbox = [
        int(
            xs.min()
        ),
        int(
            ys.min()
        ),
        int(
            xs.max()
        ) + 1,
        int(
            ys.max()
        ) + 1,
    ]


    return (
        output_mask,
        bbox
    )


# =========================================================
# BRIGHTNESS TAMPERING
# =========================================================

def local_brightness(
    image,
    document_mask
):

    bbox = choose_region(
        document_mask
    )


    x1, y1, x2, y2 = (
        bbox
    )


    document_pixels = (
        document_mask[
            y1:y2,
            x1:x2
        ] > 0
    )


    # Try different brightness changes until
    # something definitely changes.
    for change in [
        45,
        -45,
        70,
        -70,
    ]:

        result = (
            image.copy()
        )


        original_region = image[
            y1:y2,
            x1:x2
        ].copy()


        changed_region = np.clip(
            original_region.astype(
                np.int16
            )
            + change,
            0,
            255
        ).astype(
            np.uint8
        )


        result_region = result[
            y1:y2,
            x1:x2
        ]


        result_region[
            document_pixels
        ] = changed_region[
            document_pixels
        ]


        (
            mask,
            final_bbox
        ) = create_changed_mask(
            image,
            result,
            document_mask
        )


        if mask is not None:

            return (
                result,
                mask,
                final_bbox
            )


    # Extremely unusual saturation case:
    # invert visible pixels.

    result = (
        image.copy()
    )


    region = image[
        y1:y2,
        x1:x2
    ]


    inverted = (
        255 - region
    )


    result_region = result[
        y1:y2,
        x1:x2
    ]


    result_region[
        document_pixels
    ] = inverted[
        document_pixels
    ]


    (
        mask,
        final_bbox
    ) = create_changed_mask(
        image,
        result,
        document_mask
    )


    if mask is None:

        raise RuntimeError(
            "Unable to modify visible document pixels"
        )


    return (
        result,
        mask,
        final_bbox
    )


# =========================================================
# LOCAL BLUR
# =========================================================

def local_blur(
    image,
    document_mask
):

    bbox = choose_region(
        document_mask
    )


    x1, y1, x2, y2 = (
        bbox
    )


    region = image[
        y1:y2,
        x1:x2
    ].copy()


    region_height = (
        y2 - y1
    )

    region_width = (
        x2 - x1
    )


    # Tiny regions cannot be meaningfully blurred.
    if (
        region_height < 3
        or region_width < 3
    ):

        return local_brightness(
            image,
            document_mask
        )


    kernel = min(
        15,
        region_height,
        region_width
    )


    if kernel % 2 == 0:

        kernel -= 1


    if kernel < 3:

        return local_brightness(
            image,
            document_mask
        )


    blurred = cv2.GaussianBlur(
        region,
        (
            kernel,
            kernel
        ),
        0
    )


    result = (
        image.copy()
    )


    document_pixels = (
        document_mask[
            y1:y2,
            x1:x2
        ] > 0
    )


    result_region = result[
        y1:y2,
        x1:x2
    ]


    result_region[
        document_pixels
    ] = blurred[
        document_pixels
    ]


    (
        mask,
        final_bbox
    ) = create_changed_mask(
        image,
        result,
        document_mask
    )


    # Blur sometimes makes no visible difference.
    if mask is None:

        return local_brightness(
            image,
            document_mask
        )


    return (
        result,
        mask,
        final_bbox
    )


# =========================================================
# COPY-MOVE TAMPERING
# =========================================================

def copy_move(
    image,
    document_mask
):

    source_bbox = choose_region(
        document_mask
    )

    destination_bbox = choose_region(
        document_mask
    )


    (
        sx1,
        sy1,
        sx2,
        sy2
    ) = source_bbox


    (
        dx1,
        dy1,
        dx2,
        dy2
    ) = destination_bbox


    source_patch = image[
        sy1:sy2,
        sx1:sx2
    ].copy()


    destination_width = (
        dx2 - dx1
    )

    destination_height = (
        dy2 - dy1
    )


    if (
        source_patch.size == 0
        or destination_width < 1
        or destination_height < 1
    ):

        return local_brightness(
            image,
            document_mask
        )


    resized_patch = cv2.resize(
        source_patch,
        (
            destination_width,
            destination_height
        ),
        interpolation=cv2.INTER_LINEAR
    )


    result = (
        image.copy()
    )


    document_pixels = (
        document_mask[
            dy1:dy2,
            dx1:dx2
        ] > 0
    )


    result_region = result[
        dy1:dy2,
        dx1:dx2
    ]


    result_region[
        document_pixels
    ] = resized_patch[
        document_pixels
    ]


    (
        mask,
        final_bbox
    ) = create_changed_mask(
        image,
        result,
        document_mask
    )


    if mask is None:

        return local_brightness(
            image,
            document_mask
        )


    return (
        result,
        mask,
        final_bbox
    )


# =========================================================
# PATCH REPLACEMENT
# =========================================================

def patch_replace(
    image,
    donor_image,
    document_mask
):

    height, width = (
        image.shape[:2]
    )


    donor = cv2.resize(
        donor_image,
        (
            width,
            height
        ),
        interpolation=cv2.INTER_LINEAR
    )


    bbox = choose_region(
        document_mask
    )


    x1, y1, x2, y2 = (
        bbox
    )


    donor_patch = donor[
        y1:y2,
        x1:x2
    ].copy()


    if donor_patch.size == 0:

        return local_brightness(
            image,
            document_mask
        )


    result = (
        image.copy()
    )


    document_pixels = (
        document_mask[
            y1:y2,
            x1:x2
        ] > 0
    )


    result_region = result[
        y1:y2,
        x1:x2
    ]


    result_region[
        document_pixels
    ] = donor_patch[
        document_pixels
    ]


    (
        mask,
        final_bbox
    ) = create_changed_mask(
        image,
        result,
        document_mask
    )


    if mask is None:

        return local_brightness(
            image,
            document_mask
        )


    return (
        result,
        mask,
        final_bbox
    )


# =========================================================
# GENERATE ONE SPLIT
# =========================================================

def generate_split(
    split_name
):

    print(
        f"\nProcessing split: "
        f"{split_name}"
    )


    split_csv = (
        SPLITS_ROOT
        / f"{split_name}.csv"
    )


    data = pd.read_csv(
        split_csv
    )


    split_root = (
        OUTPUT_ROOT
        / split_name
    )


    images_dir = (
        split_root
        / "images"
    )


    masks_dir = (
        split_root
        / "masks"
    )


    images_dir.mkdir(
        parents=True,
        exist_ok=True
    )


    masks_dir.mkdir(
        parents=True,
        exist_ok=True
    )


    records = []


    for index, row in data.iterrows():

        if (
            index % 100 == 0
            or index
            == len(data) - 1
        ):

            print(
                f"{split_name}: "
                f"{index + 1}/"
                f"{len(data)}"
            )


        image_path = Path(
            row[
                "processed_path"
            ]
        )


        document_mask_path = Path(
            row[
                "document_mask"
            ]
        )


        image = load_image(
            image_path
        )


        document_mask = load_mask(
            document_mask_path
        )


        height, width = (
            image.shape[:2]
        )


        # -------------------------------------------------
        # GENUINE SAMPLE
        # -------------------------------------------------

        genuine_name = (
            f"{row['sample_id']}"
            "_genuine.png"
        )


        genuine_mask_name = (
            f"{row['sample_id']}"
            "_genuine_mask.png"
        )


        genuine_path = (
            images_dir
            / genuine_name
        )


        genuine_mask_path = (
            masks_dir
            / genuine_mask_name
        )


        cv2.imwrite(
            str(
                genuine_path
            ),
            image
        )


        cv2.imwrite(
            str(
                genuine_mask_path
            ),
            empty_mask(
                height,
                width
            )
        )


        records.append(
            {
                "sample_id":
                    row["sample_id"]
                    + "_genuine",

                "source_sample_id":
                    row["sample_id"],

                "document_type":
                    row["document_type"],

                "split":
                    split_name,

                "image_path":
                    str(
                        genuine_path
                    ),

                "mask_path":
                    str(
                        genuine_mask_path
                    ),

                "is_tampered":
                    0,

                "tamper_type":
                    "none",

                "x1":
                    -1,

                "y1":
                    -1,

                "x2":
                    -1,

                "y2":
                    -1,
            }
        )


        # -------------------------------------------------
        # SELECT TAMPERING TYPE
        # -------------------------------------------------

        requested_tamper_type = (
            TAMPER_TYPES[
                index
                % len(
                    TAMPER_TYPES
                )
            ]
        )


        actual_tamper_type = (
            requested_tamper_type
        )


        # -------------------------------------------------
        # GENERATE TAMPERING
        # -------------------------------------------------

        try:

            if (
                requested_tamper_type
                == "local_blur"
            ):

                (
                    tampered,
                    tamper_mask,
                    bbox
                ) = local_blur(
                    image,
                    document_mask
                )


            elif (
                requested_tamper_type
                == "local_brightness"
            ):

                (
                    tampered,
                    tamper_mask,
                    bbox
                ) = local_brightness(
                    image,
                    document_mask
                )


            elif (
                requested_tamper_type
                == "copy_move"
            ):

                (
                    tampered,
                    tamper_mask,
                    bbox
                ) = copy_move(
                    image,
                    document_mask
                )


            elif (
                requested_tamper_type
                == "patch_replace"
            ):

                donor_index = (
                    random.randrange(
                        len(data)
                    )
                )


                if (
                    donor_index
                    == index
                ):

                    donor_index = (
                        donor_index + 1
                    ) % len(data)


                donor_row = (
                    data.iloc[
                        donor_index
                    ]
                )


                donor_image = load_image(
                    Path(
                        donor_row[
                            "processed_path"
                        ]
                    )
                )


                (
                    tampered,
                    tamper_mask,
                    bbox
                ) = patch_replace(
                    image,
                    donor_image,
                    document_mask
                )


            else:

                raise RuntimeError(
                    "Unknown tamper type"
                )


        except Exception as error:

            print(
                f"WARNING: "
                f"{row['sample_id']} "
                f"{requested_tamper_type} "
                f"failed: {error}"
            )

            print(
                "Using guaranteed "
                "brightness fallback."
            )


            actual_tamper_type = (
                "local_brightness_fallback"
            )


            (
                tampered,
                tamper_mask,
                bbox
            ) = local_brightness(
                image,
                document_mask
            )


        # -------------------------------------------------
        # SAVE TAMPERED SAMPLE
        # -------------------------------------------------

        tampered_name = (
            f"{row['sample_id']}"
            "_tampered.png"
        )


        tampered_mask_name = (
            f"{row['sample_id']}"
            "_tampered_mask.png"
        )


        tampered_path = (
            images_dir
            / tampered_name
        )


        tampered_mask_path = (
            masks_dir
            / tampered_mask_name
        )


        cv2.imwrite(
            str(
                tampered_path
            ),
            tampered
        )


        cv2.imwrite(
            str(
                tampered_mask_path
            ),
            tamper_mask
        )


        (
            x1,
            y1,
            x2,
            y2
        ) = bbox


        records.append(
            {
                "sample_id":
                    row["sample_id"]
                    + "_tampered",

                "source_sample_id":
                    row["sample_id"],

                "document_type":
                    row["document_type"],

                "split":
                    split_name,

                "image_path":
                    str(
                        tampered_path
                    ),

                "mask_path":
                    str(
                        tampered_mask_path
                    ),

                "is_tampered":
                    1,

                "tamper_type":
                    actual_tamper_type,

                "x1":
                    x1,

                "y1":
                    y1,

                "x2":
                    x2,

                "y2":
                    y2,
            }
        )


    # -----------------------------------------------------
    # SAVE METADATA
    # -----------------------------------------------------

    metadata = pd.DataFrame(
        records
    )


    metadata_path = (
        split_root
        / "metadata.csv"
    )


    metadata.to_csv(
        metadata_path,
        index=False
    )


    print(
        f"\n{split_name} complete: "
        f"{len(metadata)} samples"
    )


    print(
        "\nTampering breakdown:"
    )


    print(
        metadata[
            metadata[
                "is_tampered"
            ] == 1
        ][
            "tamper_type"
        ]
        .value_counts()
        .to_string()
    )


# =========================================================
# CLEAN OLD INCOMPLETE OUTPUT
# =========================================================

if OUTPUT_ROOT.exists():

    shutil.rmtree(
        OUTPUT_ROOT
    )


OUTPUT_ROOT.mkdir(
    parents=True,
    exist_ok=True
)


# =========================================================
# GENERATE TRAIN / VAL / TEST
# =========================================================

for split_name in [
    "train",
    "val",
    "test",
]:

    generate_split(
        split_name
    )


print(
    "\n=================================="
)

print(
    "FINAL FORGERY DATASET COMPLETE"
)

print(
    "=================================="
)