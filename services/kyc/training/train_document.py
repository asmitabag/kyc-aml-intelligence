from pathlib import Path
import sys
import time

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
# CONFIGURATION
# =========================================================

MODEL_NAME = (
    "nvidia/"
    "segformer-b0-finetuned-ade-512-512"
)

TRAIN_METADATA = (
    "data/processed/"
    "final_forgery_dataset/"
    "train/metadata.csv"
)

VAL_METADATA = (
    "data/processed/"
    "final_forgery_dataset/"
    "val/metadata.csv"
)

OUTPUT_PATH = Path(
    "services/kyc/artifacts/"
    "document_segformer_best.pt"
)


EPOCHS = 5

BATCH_SIZE = 1

LEARNING_RATE = 5e-5

WEIGHT_DECAY = 1e-4

NUM_WORKERS = 0

NUM_CLASSES = 2

CE_WEIGHT = 0.5

DICE_WEIGHT = 0.5

TAMPER_PIXEL_WEIGHT = 5.0


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
# IMAGE PROCESSOR
# =========================================================

processor = (
    SegformerImageProcessor.from_pretrained(
        MODEL_NAME,
        do_reduce_labels=False,
        token=False,
    )
)


# =========================================================
# DATASETS
# =========================================================

train_dataset = (
    DocumentForgeryDataset(
        TRAIN_METADATA,
        processor=processor,
    )
)

val_dataset = (
    DocumentForgeryDataset(
        VAL_METADATA,
        processor=processor,
    )
)


print(
    "Training samples:",
    len(train_dataset)
)

print(
    "Validation samples:",
    len(val_dataset)
)


# =========================================================
# DATA LOADERS
# =========================================================

train_loader = DataLoader(
    train_dataset,
    batch_size=BATCH_SIZE,
    shuffle=True,
    num_workers=NUM_WORKERS,
)

val_loader = DataLoader(
    val_dataset,
    batch_size=BATCH_SIZE,
    shuffle=False,
    num_workers=NUM_WORKERS,
)


# =========================================================
# LABELS
# =========================================================

id2label = {
    0: "normal",
    1: "tampered",
}

label2id = {
    "normal": 0,
    "tampered": 1,
}


# =========================================================
# MODEL
# =========================================================

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


model = model.to(
    DEVICE
)


# =========================================================
# OPTIMIZER
# =========================================================

optimizer = torch.optim.AdamW(
    model.parameters(),
    lr=LEARNING_RATE,
    weight_decay=WEIGHT_DECAY,
)


# =========================================================
# WEIGHTED CROSS ENTROPY
# =========================================================

def weighted_cross_entropy(
    logits,
    labels,
):

    logits = logits.contiguous()

    labels = labels.contiguous()


    log_probabilities = (
        F.log_softmax(
            logits,
            dim=1,
        )
    )


    label_indices = (
        labels
        .unsqueeze(1)
        .contiguous()
    )


    selected_log_probabilities = (
        torch.gather(
            log_probabilities,
            dim=1,
            index=label_indices,
        )
        .squeeze(1)
        .contiguous()
    )


    pixel_weights = torch.ones_like(
        labels,
        dtype=torch.float32,
        device=labels.device,
    )


    pixel_weights = torch.where(
        labels == 1,
        torch.tensor(
            TAMPER_PIXEL_WEIGHT,
            device=labels.device,
            dtype=torch.float32,
        ),
        pixel_weights,
    )


    loss = (
        -selected_log_probabilities
        * pixel_weights
    )


    loss = (
        loss.sum()
        /
        pixel_weights.sum().clamp(
            min=1.0
        )
    )


    return loss


# =========================================================
# DICE LOSS
# =========================================================

def dice_loss(
    logits,
    labels,
):

    logits = logits.contiguous()

    labels = labels.contiguous()


    probabilities = torch.softmax(
        logits,
        dim=1,
    ).contiguous()


    tamper_probability = (
        probabilities[:, 1, :, :]
        .contiguous()
    )


    target_tamper = (
        labels == 1
    ).float().contiguous()


    intersection = (
        tamper_probability
        * target_tamper
    ).sum(
        dim=(1, 2)
    )


    predicted_sum = (
        tamper_probability
        .sum(
            dim=(1, 2)
        )
    )


    target_sum = (
        target_tamper
        .sum(
            dim=(1, 2)
        )
    )


    dice = (
        2.0 * intersection
        + 1.0
    ) / (
        predicted_sum
        + target_sum
        + 1.0
    )


    return (
        1.0
        - dice.mean()
    )


# =========================================================
# COMBINED LOSS
# =========================================================

def combined_loss(
    logits,
    labels,
):

    logits = logits.contiguous()

    labels = labels.contiguous()


    ce = weighted_cross_entropy(
        logits,
        labels,
    )


    dice = dice_loss(
        logits,
        labels,
    )


    total = (
        CE_WEIGHT * ce
        +
        DICE_WEIGHT * dice
    )


    return (
        total,
        ce,
        dice,
    )


# =========================================================
# METRICS
# =========================================================

def calculate_metric_counts(
    logits,
    labels,
):

    predictions = torch.argmax(
        logits,
        dim=1,
    )


    predicted_tamper = (
        predictions == 1
    )

    actual_tamper = (
        labels == 1
    )


    true_positive = (
        predicted_tamper
        &
        actual_tamper
    ).sum().item()


    predicted_positive = (
        predicted_tamper
        .sum()
        .item()
    )


    actual_positive = (
        actual_tamper
        .sum()
        .item()
    )


    union = (
        predicted_tamper
        |
        actual_tamper
    ).sum().item()


    return {
        "intersection":
            true_positive,

        "predicted_pixels":
            predicted_positive,

        "actual_pixels":
            actual_positive,

        "union":
            union,
    }


def calculate_final_metrics(
    totals,
):

    intersection = (
        totals[
            "intersection"
        ]
    )

    predicted = (
        totals[
            "predicted_pixels"
        ]
    )

    actual = (
        totals[
            "actual_pixels"
        ]
    )

    union = (
        totals[
            "union"
        ]
    )


    dice = (
        2.0 * intersection + 1.0
    ) / (
        predicted
        + actual
        + 1.0
    )


    iou = (
        intersection + 1.0
    ) / (
        union + 1.0
    )


    precision = (
        intersection + 1.0
    ) / (
        predicted + 1.0
    )


    recall = (
        intersection + 1.0
    ) / (
        actual + 1.0
    )


    return (
        dice,
        iou,
        precision,
        recall,
    )


# =========================================================
# TRAIN ONE EPOCH
# =========================================================

def train_epoch():

    model.train()

    total_loss = 0.0


    for batch_index, batch in enumerate(
        train_loader
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


        optimizer.zero_grad(
            set_to_none=True
        )


        outputs = model(
            pixel_values=pixel_values
        )


        logits = (
            outputs.logits
            .contiguous()
        )


        logits = (
            F.interpolate(
                logits,
                size=labels.shape[
                    -2:
                ],
                mode="bilinear",
                align_corners=False,
            )
            .contiguous()
        )


        (
            loss,
            ce,
            dice
        ) = combined_loss(
            logits,
            labels,
        )


        loss.backward()


        torch.nn.utils.clip_grad_norm_(
            model.parameters(),
            max_norm=1.0,
        )


        optimizer.step()


        total_loss += (
            loss.item()
        )


        if (
            batch_index % 100
            == 0
        ):

            print(
                f"  batch "
                f"{batch_index}/"
                f"{len(train_loader)} "
                f"loss="
                f"{loss.item():.4f} "
                f"ce="
                f"{ce.item():.4f} "
                f"dice_loss="
                f"{dice.item():.4f}"
            )


    average_loss = (
        total_loss
        /
        len(train_loader)
    )


    return average_loss


# =========================================================
# VALIDATION
# =========================================================

@torch.no_grad()
def validate():

    model.eval()

    total_loss = 0.0


    totals = {
        "intersection": 0,
        "predicted_pixels": 0,
        "actual_pixels": 0,
        "union": 0,
    }


    for batch in val_loader:

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
            outputs.logits
            .contiguous()
        )


        logits = (
            F.interpolate(
                logits,
                size=labels.shape[
                    -2:
                ],
                mode="bilinear",
                align_corners=False,
            )
            .contiguous()
        )


        (
            loss,
            _,
            _
        ) = combined_loss(
            logits,
            labels,
        )


        total_loss += (
            loss.item()
        )


        batch_metrics = (
            calculate_metric_counts(
                logits,
                labels,
            )
        )


        for key in totals:

            totals[key] += (
                batch_metrics[
                    key
                ]
            )


    (
        dice,
        iou,
        precision,
        recall,
    ) = calculate_final_metrics(
        totals
    )


    average_loss = (
        total_loss
        /
        len(val_loader)
    )


    return (
        average_loss,
        dice,
        iou,
        precision,
        recall,
    )


# =========================================================
# TRAINING LOOP
# =========================================================

best_dice = -1.0


print(
    "\nStarting training..."
)


for epoch in range(
    1,
    EPOCHS + 1
):

    print(
        "\n=================================="
    )

    print(
        f"EPOCH {epoch}/{EPOCHS}"
    )

    print(
        "=================================="
    )


    start_time = time.time()


    train_loss = (
        train_epoch()
    )


    (
        val_loss,
        val_dice,
        val_iou,
        val_precision,
        val_recall,
    ) = validate()


    elapsed = (
        time.time()
        -
        start_time
    )


    print(
        f"\nTrain loss: "
        f"{train_loss:.4f}"
    )

    print(
        f"Validation loss: "
        f"{val_loss:.4f}"
    )

    print(
        f"Validation Dice: "
        f"{val_dice:.4f}"
    )

    print(
        f"Validation IoU: "
        f"{val_iou:.4f}"
    )

    print(
        f"Validation Precision: "
        f"{val_precision:.4f}"
    )

    print(
        f"Validation Recall: "
        f"{val_recall:.4f}"
    )

    print(
        f"Epoch time: "
        f"{elapsed / 60:.1f} min"
    )


    if (
        val_dice
        >
        best_dice
    ):

        best_dice = (
            val_dice
        )


        OUTPUT_PATH.parent.mkdir(
            parents=True,
            exist_ok=True,
        )


        torch.save(
            {
                "model_state_dict":
                    model.state_dict(),

                "best_val_dice":
                    best_dice,

                "epoch":
                    epoch,

                "model_name":
                    MODEL_NAME,

                "num_labels":
                    NUM_CLASSES,

                "id2label":
                    id2label,

                "label2id":
                    label2id,
            },

            OUTPUT_PATH,
        )


        print(
            "\nSaved new best model:"
        )

        print(
            OUTPUT_PATH
        )


    if (
        DEVICE.type
        == "mps"
    ):

        torch.mps.empty_cache()


print(
    "\n=================================="
)

print(
    "TRAINING COMPLETE"
)

print(
    "=================================="
)


print(
    f"Best validation Dice: "
    f"{best_dice:.4f}"
)


print(
    f"Best model: "
    f"{OUTPUT_PATH}"
)