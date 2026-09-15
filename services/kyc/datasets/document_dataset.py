from pathlib import Path

import numpy as np
import pandas as pd
from PIL import Image

from torch.utils.data import Dataset

from transformers import SegformerImageProcessor


MODEL_NAME = (
    "nvidia/"
    "segformer-b0-finetuned-ade-512-512"
)


class DocumentForgeryDataset(Dataset):

    def __init__(
        self,
        metadata_path,
        processor=None,
    ):

        self.metadata_path = Path(
            metadata_path
        )

        self.data = pd.read_csv(
            self.metadata_path
        )

        if processor is None:

            self.processor = (
                SegformerImageProcessor.from_pretrained(
                    MODEL_NAME,
                    do_reduce_labels=False,
                    token=False,
                )
            )

        else:

            self.processor = processor


    def __len__(self):

        return len(
            self.data
        )


    def __getitem__(
        self,
        index
    ):

        row = self.data.iloc[
            index
        ]


        image_path = Path(
            row["image_path"]
        )

        mask_path = Path(
            row["mask_path"]
        )


        image = Image.open(
            image_path
        ).convert(
            "RGB"
        )


        mask = Image.open(
            mask_path
        ).convert(
            "L"
        )


        mask_array = np.array(
            mask
        )


        mask_array = (
            mask_array > 0
        ).astype(
            np.uint8
        )


        mask = Image.fromarray(
            mask_array
        )


        encoded = self.processor(
            images=image,
            segmentation_maps=mask,
            return_tensors="pt",
        )


        pixel_values = (
            encoded[
                "pixel_values"
            ].squeeze(0)
        )


        labels = (
            encoded[
                "labels"
            ].squeeze(0)
        )


        return {
            "pixel_values":
                pixel_values,

            "labels":
                labels.long(),

            "sample_id":
                row["sample_id"],

            "is_tampered":
                int(
                    row["is_tampered"]
                ),

            "tamper_type":
                row["tamper_type"],
        }