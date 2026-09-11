from pathlib import Path
import random

import cv2
import numpy as np
import pandas as pd


# ---------------------------------------------------------
# Configuration
# ---------------------------------------------------------

INPUT_ROOT = Path("data/processed/midv_base/images")

OUTPUT_ROOT = Path("data/processed/forgery_dataset")

OUTPUT_IMAGES = OUTPUT_ROOT / "images"
OUTPUT_MASKS = OUTPUT_ROOT / "masks"

OUTPUT_IMAGES.mkdir(parents=True, exist_ok=True)
OUTPUT_MASKS.mkdir(parents=True, exist_ok=True)


# Keep the first run deliberately small.
# We only want to verify the pipeline first.
NUM_SOURCE_IMAGES = 30

RANDOM_SEED = 42

random.seed(RANDOM_SEED)
np.random.seed(RANDOM_SEED)


# ---------------------------------------------------------
# Utility functions
# ---------------------------------------------------------

def load_image(path: Path):
    image = cv2.imread(str(path))

    if image is None:
        raise ValueError(f"Could not read image: {path}")

    return image


def create_empty_mask(height: int, width: int):
    return np.zeros((height, width), dtype=np.uint8)


def choose_random_region(height: int, width: int):
    """
    Select a reasonably small rectangular region.

    We avoid the extreme borders because patches pasted at the
    edges can become invalid or partly outside the image.
    """

    region_width = random.randint(
        max(30, width // 12),
        max(40, width // 5)
    )

    region_height = random.randint(
        max(30, height // 12),
        max(40, height // 5)
    )

    x1 = random.randint(
        width // 10,
        max(width // 10, width - region_width - width // 10)
    )

    y1 = random.randint(
        height // 10,
        max(height // 10, height - region_height - height // 10)
    )

    x2 = x1 + region_width
    y2 = y1 + region_height

    return x1, y1, x2, y2


# ---------------------------------------------------------
# Tampering operations
# ---------------------------------------------------------

def copy_move(image):
    result = image.copy()

    height, width = result.shape[:2]

    x1, y1, x2, y2 = choose_random_region(height, width)

    patch = result[y1:y2, x1:x2].copy()

    patch_height, patch_width = patch.shape[:2]

    max_x = width - patch_width
    max_y = height - patch_height

    destination_x = random.randint(0, max_x)
    destination_y = random.randint(0, max_y)

    result[
        destination_y:destination_y + patch_height,
        destination_x:destination_x + patch_width
    ] = patch

    mask = create_empty_mask(height, width)

    mask[
        destination_y:destination_y + patch_height,
        destination_x:destination_x + patch_width
    ] = 255

    bbox = [
        destination_x,
        destination_y,
        destination_x + patch_width,
        destination_y + patch_height,
    ]

    return result, mask, bbox


def local_blur(image):
    result = image.copy()

    height, width = result.shape[:2]

    x1, y1, x2, y2 = choose_random_region(height, width)

    region = result[y1:y2, x1:x2]

    blurred = cv2.GaussianBlur(
        region,
        (15, 15),
        0
    )

    result[y1:y2, x1:x2] = blurred

    mask = create_empty_mask(height, width)

    mask[y1:y2, x1:x2] = 255

    bbox = [x1, y1, x2, y2]

    return result, mask, bbox


def local_brightness(image):
    result = image.copy()

    height, width = result.shape[:2]

    x1, y1, x2, y2 = choose_random_region(height, width)

    region = result[y1:y2, x1:x2]

    hsv = cv2.cvtColor(region, cv2.COLOR_BGR2HSV)

    value_channel = hsv[:, :, 2].astype(np.int16)

    brightness_change = random.choice([-50, -35, 35, 50])

    value_channel = np.clip(
        value_channel + brightness_change,
        0,
        255
    )

    hsv[:, :, 2] = value_channel.astype(np.uint8)

    modified = cv2.cvtColor(
        hsv,
        cv2.COLOR_HSV2BGR
    )

    result[y1:y2, x1:x2] = modified

    mask = create_empty_mask(height, width)

    mask[y1:y2, x1:x2] = 255

    bbox = [x1, y1, x2, y2]

    return result, mask, bbox


def patch_replace(image, donor_image):
    result = image.copy()

    height, width = result.shape[:2]

    donor = cv2.resize(
        donor_image,
        (width, height)
    )

    x1, y1, x2, y2 = choose_random_region(height, width)

    patch = donor[y1:y2, x1:x2].copy()

    result[y1:y2, x1:x2] = patch

    mask = create_empty_mask(height, width)

    mask[y1:y2, x1:x2] = 255

    bbox = [x1, y1, x2, y2]

    return result, mask, bbox


# ---------------------------------------------------------
# Find available images
# ---------------------------------------------------------

image_paths = sorted(INPUT_ROOT.glob("*.png"))

if not image_paths:
    raise RuntimeError(
        f"No PNG images found inside {INPUT_ROOT}"
    )


print(f"Available MIDV base images: {len(image_paths)}")


# ---------------------------------------------------------
# Select a small debug subset
# ---------------------------------------------------------

selected_images = random.sample(
    image_paths,
    min(NUM_SOURCE_IMAGES, len(image_paths))
)


records = []


# ---------------------------------------------------------
# Generate dataset
# ---------------------------------------------------------

tamper_functions = [
    "copy_move",
    "local_blur",
    "local_brightness",
    "patch_replace",
]


for index, source_path in enumerate(selected_images):

    print(
        f"Processing {index + 1}/{len(selected_images)}: "
        f"{source_path.name}"
    )

    image = load_image(source_path)

    height, width = image.shape[:2]


    # -----------------------------------------------------
    # 1. Save genuine sample
    # -----------------------------------------------------

    genuine_name = f"genuine_{index:04d}.png"

    genuine_mask_name = f"genuine_{index:04d}_mask.png"

    genuine_output = OUTPUT_IMAGES / genuine_name

    genuine_mask_output = OUTPUT_MASKS / genuine_mask_name

    cv2.imwrite(
        str(genuine_output),
        image
    )

    genuine_mask = create_empty_mask(
        height,
        width
    )

    cv2.imwrite(
        str(genuine_mask_output),
        genuine_mask
    )

    records.append(
        {
            "sample_id": f"genuine_{index:04d}",
            "source_image": str(source_path),
            "output_image": str(genuine_output),
            "mask_path": str(genuine_mask_output),
            "is_tampered": 0,
            "tamper_type": "none",
            "x1": -1,
            "y1": -1,
            "x2": -1,
            "y2": -1,
        }
    )


    # -----------------------------------------------------
    # 2. Pick random manipulation
    # -----------------------------------------------------

    tamper_type = random.choice(
        tamper_functions
    )


    if tamper_type == "copy_move":

        tampered, mask, bbox = copy_move(
            image
        )


    elif tamper_type == "local_blur":

        tampered, mask, bbox = local_blur(
            image
        )


    elif tamper_type == "local_brightness":

        tampered, mask, bbox = local_brightness(
            image
        )


    elif tamper_type == "patch_replace":

        donor_candidates = [
            p
            for p in image_paths
            if p != source_path
        ]

        donor_path = random.choice(
            donor_candidates
        )

        donor_image = load_image(
            donor_path
        )

        tampered, mask, bbox = patch_replace(
            image,
            donor_image
        )


    else:

        raise ValueError(
            f"Unknown tamper type: {tamper_type}"
        )


    # -----------------------------------------------------
    # 3. Save manipulated image + mask
    # -----------------------------------------------------

    tampered_name = f"tampered_{index:04d}.png"

    mask_name = f"tampered_{index:04d}_mask.png"

    tampered_output = OUTPUT_IMAGES / tampered_name

    mask_output = OUTPUT_MASKS / mask_name


    cv2.imwrite(
        str(tampered_output),
        tampered
    )

    cv2.imwrite(
        str(mask_output),
        mask
    )


    x1, y1, x2, y2 = bbox


    records.append(
        {
            "sample_id": f"tampered_{index:04d}",
            "source_image": str(source_path),
            "output_image": str(tampered_output),
            "mask_path": str(mask_output),
            "is_tampered": 1,
            "tamper_type": tamper_type,
            "x1": x1,
            "y1": y1,
            "x2": x2,
            "y2": y2,
        }
    )


# ---------------------------------------------------------
# Save metadata
# ---------------------------------------------------------

metadata = pd.DataFrame(records)

metadata_path = OUTPUT_ROOT / "metadata.csv"

metadata.to_csv(
    metadata_path,
    index=False
)


# ---------------------------------------------------------
# Summary
# ---------------------------------------------------------

print("\n----------------------------------")
print("TAMPERING GENERATION COMPLETE")
print("----------------------------------")

print(
    f"Source images used: "
    f"{len(selected_images)}"
)

print(
    f"Total generated samples: "
    f"{len(metadata)}"
)

print(
    f"Images saved to: "
    f"{OUTPUT_IMAGES}"
)

print(
    f"Masks saved to: "
    f"{OUTPUT_MASKS}"
)

print(
    f"Metadata saved to: "
    f"{metadata_path}"
)


print("\nTampering types:")

print(
    metadata[
        metadata["is_tampered"] == 1
    ]["tamper_type"]
    .value_counts()
    .to_string()
)