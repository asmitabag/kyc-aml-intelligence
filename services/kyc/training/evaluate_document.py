from pathlib import Path
import json
import sys

import torch
import torch.nn.functional as F
from torch.utils.data import DataLoader

from transformers import (
    SegformerForSemanticSegmentation,
    SegformerImageProcessor,
)


# =========================================================
# IMPORT DATASET
# =========================================================

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

THRESHOLD_PATH = Path(
    "services/kyc/artifacts/"
    "document_threshold.json"
)

TEST_METADATA = (
    "data/processed/"
    "final_forgery_dataset/"
    "test/metadata.csv"
)

BATCH_SIZE = 1

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
# LOAD CALIBRATED THRESHOLD
# =========================================================

with open(
    THRESHOLD_PATH,
    "r"
) as file:

    threshold_config = json.load(
        file
    )


TAMPER_FRACTION_THRESHOLD = float(
    threshold_config[
        "tamper_fraction_threshold"
    ]
)

PIXEL_PROBABILITY_THRESHOLD = float(
    threshold_config[
        "pixel_probability_threshold"
    ]
)


print(
    "Pixel probability threshold:",
    PIXEL_PROBABILITY_THRESHOLD
)

print(
    "Image tamper fraction threshold:",
    TAMPER_FRACTION_THRESHOLD
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
# TEST DATASET
# =========================================================

test_dataset = (
    DocumentForgeryDataset(
        TEST_METADATA,
        processor=processor,
    )
)


test_loader = DataLoader(
    test_dataset,
    batch_size=BATCH_SIZE,
    shuffle=False,
    num_workers=0,
)


print(
    "Test samples:",
    len(test_dataset)
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


print(
    "Loaded checkpoint from epoch:",
    checkpoint["epoch"]
)

print(
    "Checkpoint validation Dice:",
    checkpoint[
        "best_val_dice"
    ]
)


# =========================================================
# PIXEL-LEVEL COUNTERS
# =========================================================

pixel_true_positive = 0

pixel_false_positive = 0

pixel_false_negative = 0


# =========================================================
# IMAGE-LEVEL COUNTERS
# =========================================================

image_true_positive = 0

image_true_negative = 0

image_false_positive = 0

image_false_negative = 0


# =========================================================
# TEST LOOP
# =========================================================

print(
    "\nEvaluating calibrated model..."
)


with torch.no_grad():

    for index, batch in enumerate(
        test_loader
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
            .contiguous()
        )


        outputs = model(
            pixel_values=pixel_values
        )


        logits = (
            F.interpolate(
                outputs.logits,

                size=labels.shape[
                    -2:
                ],

                mode="bilinear",

                align_corners=False,
            )
            .contiguous()
        )


        # =================================================
        # TAMPER PROBABILITY MAP
        # =================================================

        probabilities = torch.softmax(
            logits,
            dim=1,
        )


        tamper_probability = (
            probabilities[
                :,
                1,
                :,
                :
            ]
        )


        # =================================================
        # PIXEL-LEVEL PREDICTION
        # =================================================

        predicted_tamper = (
            tamper_probability
            >
            PIXEL_PROBABILITY_THRESHOLD
        )


        actual_tamper = (
            labels == 1
        )


        tp = (
            predicted_tamper
            &
            actual_tamper
        ).sum().item()


        fp = (
            predicted_tamper
            &
            (~actual_tamper)
        ).sum().item()


        fn = (
            (~predicted_tamper)
            &
            actual_tamper
        ).sum().item()


        pixel_true_positive += tp

        pixel_false_positive += fp

        pixel_false_negative += fn


        # =================================================
        # IMAGE-LEVEL TAMPER FRACTION
        # =================================================

        tamper_fraction = (
            predicted_tamper
            .float()
            .mean()
            .item()
        )


        predicted_image_tampered = (
            tamper_fraction
            >
            TAMPER_FRACTION_THRESHOLD
        )


        actual_image_tampered = (
            int(
                batch[
                    "is_tampered"
                ][0]
            )
            == 1
        )


        # =================================================
        # IMAGE CONFUSION COUNTS
        # =================================================

        if (
            predicted_image_tampered
            and
            actual_image_tampered
        ):

            image_true_positive += 1


        elif (
            not predicted_image_tampered
            and
            not actual_image_tampered
        ):

            image_true_negative += 1


        elif (
            predicted_image_tampered
            and
            not actual_image_tampered
        ):

            image_false_positive += 1


        else:

            image_false_negative += 1


        if (
            index % 100 == 0
        ):

            print(
                f"Processed "
                f"{index}/"
                f"{len(test_loader)}"
            )


# =========================================================
# PIXEL-LEVEL METRICS
# =========================================================

pixel_precision = (
    pixel_true_positive
    /
    max(
        pixel_true_positive
        + pixel_false_positive,
        1
    )
)


pixel_recall = (
    pixel_true_positive
    /
    max(
        pixel_true_positive
        + pixel_false_negative,
        1
    )
)


pixel_dice = (
    2
    * pixel_true_positive
    /
    max(
        2
        * pixel_true_positive
        + pixel_false_positive
        + pixel_false_negative,
        1
    )
)


pixel_iou = (
    pixel_true_positive
    /
    max(
        pixel_true_positive
        + pixel_false_positive
        + pixel_false_negative,
        1
    )
)


# =========================================================
# IMAGE-LEVEL METRICS
# =========================================================

total_images = (
    image_true_positive
    + image_true_negative
    + image_false_positive
    + image_false_negative
)


image_accuracy = (
    image_true_positive
    + image_true_negative
) / max(
    total_images,
    1
)


image_precision = (
    image_true_positive
    /
    max(
        image_true_positive
        + image_false_positive,
        1
    )
)


image_recall = (
    image_true_positive
    /
    max(
        image_true_positive
        + image_false_negative,
        1
    )
)


image_f1 = (
    2
    * image_precision
    * image_recall
    /
    max(
        image_precision
        + image_recall,
        1e-8
    )
)


# =========================================================
# RESULTS
# =========================================================

print(
    "\n=================================="
)

print(
    "CALIBRATED TEST RESULTS"
)

print(
    "=================================="
)


print(
    "\nTHRESHOLDS"
)

print(
    f"Pixel probability: "
    f"{PIXEL_PROBABILITY_THRESHOLD:.4f}"
)

print(
    f"Tamper fraction:   "
    f"{TAMPER_FRACTION_THRESHOLD:.8f}"
)


print(
    "\nPIXEL-LEVEL"
)

print(
    f"Dice:      "
    f"{pixel_dice:.4f}"
)

print(
    f"IoU:       "
    f"{pixel_iou:.4f}"
)

print(
    f"Precision: "
    f"{pixel_precision:.4f}"
)

print(
    f"Recall:    "
    f"{pixel_recall:.4f}"
)


print(
    "\nIMAGE-LEVEL"
)

print(
    f"Accuracy:  "
    f"{image_accuracy:.4f}"
)

print(
    f"Precision: "
    f"{image_precision:.4f}"
)

print(
    f"Recall:    "
    f"{image_recall:.4f}"
)

print(
    f"F1:        "
    f"{image_f1:.4f}"
)


print(
    "\nCONFUSION COUNTS"
)

print(
    "TP:",
    image_true_positive
)

print(
    "TN:",
    image_true_negative
)

print(
    "FP:",
    image_false_positive
)

print(
    "FN:",
    image_false_negative
)