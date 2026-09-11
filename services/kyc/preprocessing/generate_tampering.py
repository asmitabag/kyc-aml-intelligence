from pathlib import Path
import random

import cv2
import numpy as np
import pandas as pd


BASE_METADATA = Path(
    "data/processed/midv_base/metadata.csv"
)

REGION_METADATA = Path(
    "data/processed/document_regions/metadata.csv"
)

OUTPUT_ROOT = Path(
    "data/processed/forgery_dataset_v2"
)

OUTPUT_IMAGES = OUTPUT_ROOT / "images"
OUTPUT_MASKS = OUTPUT_ROOT / "masks"

OUTPUT_IMAGES.mkdir(
    parents=True,
    exist_ok=True
)

OUTPUT_MASKS.mkdir(
    parents=True,
    exist_ok=True
)


NUM_SOURCE_IMAGES = 30
RANDOM_SEED = 42

random.seed(RANDOM_SEED)
np.random.seed(RANDOM_SEED)


def load_image(path):
    image = cv2.imread(str(path))

    if image is None:
        raise ValueError(
            f"Could not read image: {path}"
        )

    return image


def load_mask(path):
    mask = cv2.imread(
        str(path),
        cv2.IMREAD_GRAYSCALE
    )

    if mask is None:
        raise ValueError(
            f"Could not read mask: {path}"
        )

    return mask


def create_empty_mask(height, width):
    return np.zeros(
        (height, width),
        dtype=np.uint8
    )


def get_document_bbox(document_mask):

    points = cv2.findNonZero(
        document_mask
    )

    if points is None:
        raise ValueError(
            "Document mask is empty"
        )

    x, y, w, h = cv2.boundingRect(
        points
    )

    return x, y, x + w, y + h


def choose_region_inside_document(
    document_mask
):

    height, width = (
        document_mask.shape
    )

    doc_x1, doc_y1, doc_x2, doc_y2 = (
        get_document_bbox(
            document_mask
        )
    )

    doc_width = (
        doc_x2 - doc_x1
    )

    doc_height = (
        doc_y2 - doc_y1
    )

    for _ in range(100):

        region_width = random.randint(
            max(20, doc_width // 8),
            max(30, doc_width // 4)
        )

        region_height = random.randint(
            max(20, doc_height // 8),
            max(30, doc_height // 4)
        )

        if (
            region_width >= doc_width
            or region_height >= doc_height
        ):
            continue

        x1 = random.randint(
            doc_x1,
            doc_x2 - region_width
        )

        y1 = random.randint(
            doc_y1,
            doc_y2 - region_height
        )

        x2 = x1 + region_width
        y2 = y1 + region_height


        region_mask = (
            document_mask[
                y1:y2,
                x1:x2
            ]
        )


        inside_fraction = (
            np.count_nonzero(
                region_mask
            )
            /
            region_mask.size
        )


        if inside_fraction >= 0.95:

            return (
                x1,
                y1,
                x2,
                y2
            )


    raise RuntimeError(
        "Could not find valid region "
        "inside document"
    )


def local_blur(
    image,
    document_mask
):

    result = image.copy()

    height, width = (
        result.shape[:2]
    )

    x1, y1, x2, y2 = (
        choose_region_inside_document(
            document_mask
        )
    )


    region = result[
        y1:y2,
        x1:x2
    ]


    blurred = cv2.GaussianBlur(
        region,
        (15, 15),
        0
    )


    result[
        y1:y2,
        x1:x2
    ] = blurred


    mask = create_empty_mask(
        height,
        width
    )


    mask[
        y1:y2,
        x1:x2
    ] = 255


    return (
        result,
        mask,
        [x1, y1, x2, y2]
    )


def local_brightness(
    image,
    document_mask
):

    result = image.copy()

    height, width = (
        result.shape[:2]
    )


    x1, y1, x2, y2 = (
        choose_region_inside_document(
            document_mask
        )
    )


    region = result[
        y1:y2,
        x1:x2
    ]


    hsv = cv2.cvtColor(
        region,
        cv2.COLOR_BGR2HSV
    )


    value_channel = (
        hsv[:, :, 2]
        .astype(np.int16)
    )


    brightness_change = (
        random.choice(
            [-50, -35, 35, 50]
        )
    )


    value_channel = np.clip(
        value_channel
        + brightness_change,
        0,
        255
    )


    hsv[:, :, 2] = (
        value_channel
        .astype(np.uint8)
    )


    modified = cv2.cvtColor(
        hsv,
        cv2.COLOR_HSV2BGR
    )


    result[
        y1:y2,
        x1:x2
    ] = modified


    mask = create_empty_mask(
        height,
        width
    )


    mask[
        y1:y2,
        x1:x2
    ] = 255


    return (
        result,
        mask,
        [x1, y1, x2, y2]
    )


def copy_move(
    image,
    document_mask
):

    result = image.copy()

    height, width = (
        result.shape[:2]
    )


    sx1, sy1, sx2, sy2 = (
        choose_region_inside_document(
            document_mask
        )
    )


    source_patch = (
        result[
            sy1:sy2,
            sx1:sx2
        ]
        .copy()
    )


    patch_height, patch_width = (
        source_patch.shape[:2]
    )


    for _ in range(100):

        dx1, dy1, dx2, dy2 = (
            choose_region_inside_document(
                document_mask
            )
        )


        destination_width = (
            dx2 - dx1
        )

        destination_height = (
            dy2 - dy1
        )


        if (
            destination_width <= 0
            or destination_height <= 0
        ):
            continue


        resized_patch = cv2.resize(
            source_patch,
            (
                destination_width,
                destination_height
            )
        )


        result[
            dy1:dy2,
            dx1:dx2
        ] = resized_patch


        mask = create_empty_mask(
            height,
            width
        )


        mask[
            dy1:dy2,
            dx1:dx2
        ] = 255


        return (
            result,
            mask,
            [dx1, dy1, dx2, dy2]
        )


    raise RuntimeError(
        "Could not create copy-move"
    )


def patch_replace(
    image,
    donor_image,
    document_mask
):

    result = image.copy()

    height, width = (
        result.shape[:2]
    )


    donor = cv2.resize(
        donor_image,
        (width, height)
    )


    x1, y1, x2, y2 = (
        choose_region_inside_document(
            document_mask
        )
    )


    patch = donor[
        y1:y2,
        x1:x2
    ].copy()


    result[
        y1:y2,
        x1:x2
    ] = patch


    mask = create_empty_mask(
        height,
        width
    )


    mask[
        y1:y2,
        x1:x2
    ] = 255


    return (
        result,
        mask,
        [x1, y1, x2, y2]
    )


base_metadata = pd.read_csv(
    BASE_METADATA
)

region_metadata = pd.read_csv(
    REGION_METADATA
)


metadata = base_metadata.merge(
    region_metadata[
        [
            "sample_id",
            "document_mask",
        ]
    ],
    on="sample_id",
    how="inner"
)


print(
    f"Available samples: "
    f"{len(metadata)}"
)


if len(metadata) == 0:
    raise RuntimeError(
        "No matching MIDV samples found"
    )


selected = metadata.sample(
    n=min(
        NUM_SOURCE_IMAGES,
        len(metadata)
    ),
    random_state=RANDOM_SEED
).reset_index(
    drop=True
)


records = []


tamper_types = [
    "local_blur",
    "local_brightness",
    "copy_move",
    "patch_replace",
]


for index, row in selected.iterrows():

    print(
        f"Processing "
        f"{index + 1}/"
        f"{len(selected)}"
    )


    image_path = Path(
        row["processed_path"]
    )

    mask_path = Path(
        row["document_mask"]
    )


    image = load_image(
        image_path
    )

    document_mask = load_mask(
        mask_path
    )


    height, width = (
        image.shape[:2]
    )


    genuine_name = (
        f"genuine_{index:04d}.png"
    )

    genuine_mask_name = (
        f"genuine_{index:04d}_mask.png"
    )


    genuine_output = (
        OUTPUT_IMAGES
        / genuine_name
    )

    genuine_mask_output = (
        OUTPUT_MASKS
        / genuine_mask_name
    )


    cv2.imwrite(
        str(genuine_output),
        image
    )


    genuine_mask = (
        create_empty_mask(
            height,
            width
        )
    )


    cv2.imwrite(
        str(genuine_mask_output),
        genuine_mask
    )


    records.append(
        {
            "sample_id": (
                f"genuine_{index:04d}"
            ),
            "source_sample_id": (
                row["sample_id"]
            ),
            "source_image": str(
                image_path
            ),
            "output_image": str(
                genuine_output
            ),
            "mask_path": str(
                genuine_mask_output
            ),
            "document_mask": str(
                mask_path
            ),
            "is_tampered": 0,
            "tamper_type": "none",
            "x1": -1,
            "y1": -1,
            "x2": -1,
            "y2": -1,
        }
    )


    tamper_type = random.choice(
        tamper_types
    )


    if tamper_type == "local_blur":

        tampered, mask, bbox = (
            local_blur(
                image,
                document_mask
            )
        )


    elif tamper_type == "local_brightness":

        tampered, mask, bbox = (
            local_brightness(
                image,
                document_mask
            )
        )


    elif tamper_type == "copy_move":

        tampered, mask, bbox = (
            copy_move(
                image,
                document_mask
            )
        )


    elif tamper_type == "patch_replace":

        donor_row = metadata.sample(
            n=1
        ).iloc[0]

        donor_image = load_image(
            Path(
                donor_row[
                    "processed_path"
                ]
            )
        )

        tampered, mask, bbox = (
            patch_replace(
                image,
                donor_image,
                document_mask
            )
        )


    else:

        raise ValueError(
            f"Unknown tamper type: "
            f"{tamper_type}"
        )


    tampered_name = (
        f"tampered_{index:04d}.png"
    )

    tampered_mask_name = (
        f"tampered_{index:04d}_mask.png"
    )


    tampered_output = (
        OUTPUT_IMAGES
        / tampered_name
    )

    tampered_mask_output = (
        OUTPUT_MASKS
        / tampered_mask_name
    )


    cv2.imwrite(
        str(tampered_output),
        tampered
    )


    cv2.imwrite(
        str(tampered_mask_output),
        mask
    )


    x1, y1, x2, y2 = bbox


    records.append(
        {
            "sample_id": (
                f"tampered_{index:04d}"
            ),
            "source_sample_id": (
                row["sample_id"]
            ),
            "source_image": str(
                image_path
            ),
            "output_image": str(
                tampered_output
            ),
            "mask_path": str(
                tampered_mask_output
            ),
            "document_mask": str(
                mask_path
            ),
            "is_tampered": 1,
            "tamper_type": tamper_type,
            "x1": x1,
            "y1": y1,
            "x2": x2,
            "y2": y2,
        }
    )


output_metadata = pd.DataFrame(
    records
)


metadata_path = (
    OUTPUT_ROOT / "metadata.csv"
)


output_metadata.to_csv(
    metadata_path,
    index=False
)


print("\n----------------------------------")
print("DOCUMENT-AWARE TAMPERING COMPLETE")
print("----------------------------------")

print(
    f"Source images: "
    f"{len(selected)}"
)

print(
    f"Generated samples: "
    f"{len(output_metadata)}"
)

print(
    f"Metadata: "
    f"{metadata_path}"
)

print("\nTampering breakdown:")

print(
    output_metadata[
        output_metadata[
            "is_tampered"
        ] == 1
    ][
        "tamper_type"
    ]
    .value_counts()
    .to_string()
)