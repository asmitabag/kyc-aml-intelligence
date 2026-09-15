import torch
from torch.utils.data import DataLoader

from document_dataset import (
    DocumentForgeryDataset
)


TRAIN_METADATA = (
    "data/processed/"
    "final_forgery_dataset/"
    "train/metadata.csv"
)


dataset = DocumentForgeryDataset(
    TRAIN_METADATA
)


print(
    "Dataset size:",
    len(dataset)
)


sample = dataset[0]


print(
    "Sample ID:",
    sample["sample_id"]
)

print(
    "Tampered:",
    sample["is_tampered"]
)

print(
    "Tamper type:",
    sample["tamper_type"]
)

print(
    "Pixel values shape:",
    sample["pixel_values"].shape
)

print(
    "Labels shape:",
    sample["labels"].shape
)

print(
    "Image dtype:",
    sample["pixel_values"].dtype
)

print(
    "Label dtype:",
    sample["labels"].dtype
)

print(
    "Unique mask values:",
    torch.unique(
        sample["labels"]
    )
)


loader = DataLoader(
    dataset,
    batch_size=4,
    shuffle=True,
)


batch = next(
    iter(loader)
)


print(
    "\nBatch pixel shape:",
    batch[
        "pixel_values"
    ].shape
)

print(
    "Batch label shape:",
    batch[
        "labels"
    ].shape
)

print(
    "Batch sample IDs:",
    batch[
        "sample_id"
    ][:4]
)