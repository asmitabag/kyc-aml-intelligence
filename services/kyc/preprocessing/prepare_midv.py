from pathlib import Path
from PIL import Image
import pandas as pd


# ---------------------------------------------------------
# Configuration
# ---------------------------------------------------------

RAW_ROOT = Path("data/raw/midv500")

OUTPUT_ROOT = Path("data/processed/midv_base")

OUTPUT_IMAGES = OUTPUT_ROOT / "images"

DOCUMENT_TYPES = [
    "01_alb_id",
    "02_aut_drvlic_new",
    "03_aut_id_old",
]


# ---------------------------------------------------------
# Create output directories
# ---------------------------------------------------------

OUTPUT_IMAGES.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------
# Metadata container
# ---------------------------------------------------------

records = []


# ---------------------------------------------------------
# Process each MIDV document type
# ---------------------------------------------------------

for document_type in DOCUMENT_TYPES:

    images_root = RAW_ROOT / document_type / "images"

    if not images_root.exists():
        print(f"WARNING: Missing folder: {images_root}")
        continue

    print(f"\nProcessing {document_type}")

    # Each condition is stored inside folders such as
    # CA, CS, PS, PA, etc.
    condition_folders = [
        folder
        for folder in images_root.iterdir()
        if folder.is_dir()
    ]

    for condition_folder in sorted(condition_folders):

        condition = condition_folder.name

        image_files = sorted(
            list(condition_folder.glob("*.tif"))
            + list(condition_folder.glob("*.tiff"))
            + list(condition_folder.glob("*.jpg"))
            + list(condition_folder.glob("*.jpeg"))
            + list(condition_folder.glob("*.png"))
        )

        for image_index, image_path in enumerate(image_files):

            # Open image
            image = Image.open(image_path)

            # Standardize all images to RGB
            image = image.convert("RGB")

            # Create unique filename
            output_name = (
                f"{document_type}_{condition}_{image_index:03d}.png"
            )

            output_path = OUTPUT_IMAGES / output_name

            # Save as PNG
            image.save(output_path)

            records.append(
                {
                    "sample_id": output_name.replace(".png", ""),
                    "document_type": document_type,
                    "condition": condition,
                    "source_path": str(image_path),
                    "processed_path": str(output_path),
                    "width": image.width,
                    "height": image.height,
                }
            )


# ---------------------------------------------------------
# Save metadata CSV
# ---------------------------------------------------------

metadata = pd.DataFrame(records)

metadata_path = OUTPUT_ROOT / "metadata.csv"

metadata.to_csv(metadata_path, index=False)


# ---------------------------------------------------------
# Summary
# ---------------------------------------------------------

print("\n----------------------------------")
print("MIDV PREPARATION COMPLETE")
print("----------------------------------")
print(f"Total processed images: {len(metadata)}")
print(f"Metadata saved to: {metadata_path}")
print(f"Images saved to: {OUTPUT_IMAGES}")

if not metadata.empty:

    print("\nImages per document type:")

    print(
        metadata.groupby("document_type")
        .size()
        .to_string()
    )

    print("\nImages per condition:")

    print(
        metadata.groupby("condition")
        .size()
        .to_string()
    )