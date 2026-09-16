from pathlib import Path
import json
import sys

import numpy as np
import torch
import torch.nn.functional as F
from torch.utils.data import DataLoader

from transformers import (
    SegformerForSemanticSegmentation,
    SegformerImageProcessor,
)


sys.path.append(
    "services/kyc/datasets"
)

from document_dataset import DocumentForgeryDataset


# =========================================================
# CONFIG
# =========================================================

MODEL_NAME = (
    "nvidia/"
    "segformer-b0-finetuned-ade-512-512"
)

CHECKPOINT_PATH = Path(
    "services/kyc/artifacts/"
    "document_segformer_best.pt"
)

VAL_METADATA = (
    "data/processed/"
    "final_forgery_dataset/"
    "val/metadata.csv"
)

OUTPUT_PATH = Path(
    "services/kyc/artifacts/"
    "document_threshold.json"
)

NUM_CLASSES = 2


# =========================================================
# DEVICE
# =========================================================

if torch.backends.mps.is_available():

    DEVICE = torch.device(
        "mps"
    )

elif torch.cuda.is_available():

    DEVICE = torch.device(
        "cuda"
    )

else:

    DEVICE = torch.device(
        "cpu"
    )


print(
    "Using device:",
    DEVICE
)


# =========================================================
# PROCESSOR
# =========================================================

processor = (
    SegformerImageProcessor.from_pretrained(
        MODEL_NAME,
        do_reduce_labels=False,
        token=False,
    )
)


# =========================================================
# DATASET
# =========================================================

val_dataset = DocumentForgeryDataset(
    VAL_METADATA,
    processor=processor,
)


val_loader = DataLoader(
    val_dataset,
    batch_size=1,
    shuffle=False,
    num_workers=0,
)


print(
    "Validation samples:",
    len(val_dataset)
)


# =========================================================
# MODEL
# =========================================================

id2label = {
    0: "normal",
    1: "tampered",
}

label2id = {
    "normal": 0,
    "tampered": 1,
}


model = (
    SegformerForSemanticSegmentation
    .from_pretrained(
        MODEL_NAME,
        num_labels=NUM_CLASSES,
        id2label=id2label,
        label2id=label2id,
        ignore_mismatched_sizes=True,
        token=False,
    )
)


checkpoint = torch.load(
    CHECKPOINT_PATH,
    map_location="cpu",
)


model.load_state_dict(
    checkpoint[
        "model_state_dict"
    ]
)


model.to(
    DEVICE
)

model.eval()


# =========================================================
# GET IMAGE SCORES
# =========================================================

scores = []

targets = []


print(
    "\nCalculating validation scores..."
)


with torch.no_grad():

    for index, batch in enumerate(
        val_loader
    ):

        pixel_values = (
            batch[
                "pixel_values"
            ]
            .to(
                DEVICE
            )
            .contiguous()
        )


        labels = (
            batch[
                "labels"
            ]
            .to(
                DEVICE
            )
        )


        outputs = model(
            pixel_values=pixel_values
        )


        logits = F.interpolate(
            outputs.logits,
            size=labels.shape[-2:],
            mode="bilinear",
            align_corners=False,
        )


        probabilities = torch.softmax(
            logits,
            dim=1,
        )


        tamper_probability = (
            probabilities[
                0,
                1
            ]
        )


        predicted_tamper_pixels = (
            tamper_probability > 0.5
        )


        tamper_fraction = (
            predicted_tamper_pixels
            .float()
            .mean()
            .item()
        )


        scores.append(
            tamper_fraction
        )


        targets.append(
            int(
                batch[
                    "is_tampered"
                ][0]
            )
        )


        if (
            index % 100 == 0
        ):

            print(
                f"Processed "
                f"{index}/"
                f"{len(val_loader)}"
            )


scores = np.array(
    scores
)

targets = np.array(
    targets
)


# =========================================================
# FIND BEST THRESHOLD
# =========================================================

unique_scores = np.unique(
    scores
)


candidate_thresholds = [
    0.0
]


for i in range(
    len(unique_scores) - 1
):

    midpoint = (
        unique_scores[i]
        +
        unique_scores[i + 1]
    ) / 2.0

    candidate_thresholds.append(
        midpoint
    )


candidate_thresholds.append(
    float(
        unique_scores[-1]
    )
    + 1e-8
)


best_threshold = None

best_f1 = -1.0

best_accuracy = -1.0

best_results = None


for threshold in candidate_thresholds:

    predictions = (
        scores > threshold
    ).astype(
        int
    )


    tp = int(
        np.sum(
            (predictions == 1)
            &
            (targets == 1)
        )
    )


    tn = int(
        np.sum(
            (predictions == 0)
            &
            (targets == 0)
        )
    )


    fp = int(
        np.sum(
            (predictions == 1)
            &
            (targets == 0)
        )
    )


    fn = int(
        np.sum(
            (predictions == 0)
            &
            (targets == 1)
        )
    )


    precision = (
        tp
        /
        max(
            tp + fp,
            1
        )
    )


    recall = (
        tp
        /
        max(
            tp + fn,
            1
        )
    )


    f1 = (
        2
        * precision
        * recall
        /
        max(
            precision
            + recall,
            1e-8
        )
    )


    accuracy = (
        tp + tn
    ) / len(
        targets
    )


    if (
        f1 > best_f1
        or (
            f1 == best_f1
            and accuracy > best_accuracy
        )
    ):

        best_f1 = f1

        best_accuracy = accuracy

        best_threshold = float(
            threshold
        )

        best_results = {
            "tp": tp,
            "tn": tn,
            "fp": fp,
            "fn": fn,
            "precision": precision,
            "recall": recall,
            "f1": f1,
            "accuracy": accuracy,
        }


# =========================================================
# SAVE THRESHOLD
# =========================================================

OUTPUT_PATH.parent.mkdir(
    parents=True,
    exist_ok=True,
)


with open(
    OUTPUT_PATH,
    "w"
) as file:

    json.dump(
        {
            "tamper_fraction_threshold":
                best_threshold,

            "pixel_probability_threshold":
                0.5,

            "validation_f1":
                best_results[
                    "f1"
                ],

            "validation_accuracy":
                best_results[
                    "accuracy"
                ],
        },
        file,
        indent=4,
    )


# =========================================================
# RESULTS
# =========================================================

print(
    "\n=================================="
)

print(
    "THRESHOLD CALIBRATION RESULTS"
)

print(
    "=================================="
)


print(
    f"Best tamper fraction threshold: "
    f"{best_threshold:.8f}"
)


print(
    f"\nAccuracy:  "
    f"{best_results['accuracy']:.4f}"
)

print(
    f"Precision: "
    f"{best_results['precision']:.4f}"
)

print(
    f"Recall:    "
    f"{best_results['recall']:.4f}"
)

print(
    f"F1:        "
    f"{best_results['f1']:.4f}"
)


print(
    "\nCONFUSION COUNTS"
)

print(
    "TP:",
    best_results[
        "tp"
    ]
)

print(
    "TN:",
    best_results[
        "tn"
    ]
)

print(
    "FP:",
    best_results[
        "fp"
    ]
)

print(
    "FN:",
    best_results[
        "fn"
    ]
)


print(
    "\nSaved threshold:"
)

print(
    OUTPUT_PATH
)