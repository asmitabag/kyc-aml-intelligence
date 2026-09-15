from pathlib import Path
import os

from midv500.download_dataset import midv500_links
from midv500.utils import download, unzip


OUTPUT_DIR = Path("data/raw/midv500")

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# We already have document types 01, 02, 03.
# Download 04 through 12.
SELECTED_LINKS = midv500_links[3:6] + midv500_links[7:13]

for link in SELECTED_LINKS:

    filename = link.split("/")[-1]

    folder_name = filename.replace(
        ".zip",
        ""
    )

    folder_path = (
        OUTPUT_DIR / folder_name
    )


    if folder_path.exists():

        print(
            f"Skipping {folder_name} "
            "- already downloaded"
        )

        continue


    print("\n----------------------------------")
    print(
        f"Downloading: {filename}"
    )


    download(
        link,
        str(OUTPUT_DIR)
    )


    zip_path = (
        OUTPUT_DIR / filename
    )


    print(
        f"Unzipping: {filename}"
    )


    unzip(
        str(zip_path),
        str(OUTPUT_DIR)
    )


    print(
        f"Finished: {folder_name}"
    )


    if zip_path.exists():

        os.remove(
            zip_path
        )


print("\n----------------------------------")
print("SELECTED MIDV DOWNLOAD COMPLETE")
print("----------------------------------")