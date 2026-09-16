from pathlib import Path
import argparse
import json
import sys

import numpy as np
from PIL import Image

import torch
import torch.nn.functional as F

from transformers import (
    SegformerForSemanticSegmentation,
    SegformerImageProcessor,
)


# =========================================================
# PATHS
# =========================================================

PROJECT_ROOT = Path(
    __file__
).resolve().parents[3]


sys.path.insert(
    0,
    str(
        PROJECT_ROOT
        / "services"
        / "kyc"
        / "liveness"
    )
)

sys.path.insert(
    0,
    str(
        PROJECT_ROOT
        / "services"
        / "kyc"
        / "fusion"
    )
)


from liveness_service import LivenessDetector
from kyc_score import calculate_kyc_score


# =========================================================
# CONFIG
# =========================================================

MODEL_NAME = (
    "nvidia/"
    "segformer-b0-finetuned-ade-512-512"
)


CHECKPOINT_PATH = (
    PROJECT_ROOT
    / "services"
    / "kyc"
    / "artifacts"
    / "document_segformer_best.pt"
)


THRESHOLD_PATH = (
    PROJECT_ROOT
    / "services"
    / "kyc"
    / "artifacts"
    / "document_threshold.json"
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


# =========================================================
# DOCUMENT DETECTOR
# =========================================================

class DocumentForgeryDetector:

    def __init__(self):

        print(
            "Loading document forgery model..."
        )


        with open(
            THRESHOLD_PATH,
            "r"
        ) as file:

            threshold_config = (
                json.load(
                    file
                )
            )


        self.pixel_threshold = float(
            threshold_config[
                "pixel_probability_threshold"
            ]
        )


        self.tamper_fraction_threshold = float(
            threshold_config[
                "tamper_fraction_threshold"
            ]
        )


        self.processor = (
            SegformerImageProcessor.from_pretrained(
                MODEL_NAME,
                do_reduce_labels=False,
                token=False,
            )
        )


        id2label = {
            0: "normal",
            1: "tampered",
        }


        label2id = {
            "normal": 0,
            "tampered": 1,
        }


        self.model = (
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


        self.model.load_state_dict(
            checkpoint[
                "model_state_dict"
            ]
        )


        self.model.to(
            DEVICE
        )


        self.model.eval()


        print(
            "Document model loaded on:",
            DEVICE
        )


    # =====================================================
    # PREDICT DOCUMENT
    # =====================================================

    def predict(
        self,
        image_path,
    ):

        image_path = Path(
            image_path
        )


        if not image_path.exists():

            raise FileNotFoundError(
                f"Document image not found: "
                f"{image_path}"
            )


        image = Image.open(
            image_path
        ).convert(
            "RGB"
        )


        encoded = self.processor(
            images=image,
            return_tensors="pt",
        )


        pixel_values = (
            encoded[
                "pixel_values"
            ]
            .to(
                DEVICE
            )
            .contiguous()
        )


        with torch.no_grad():

            outputs = self.model(
                pixel_values=pixel_values
            )


            logits = (
                F.interpolate(
                    outputs.logits,

                    size=pixel_values.shape[
                        -2:
                    ],

                    mode="bilinear",

                    align_corners=False,
                )
                .contiguous()
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
            tamper_probability
            >
            self.pixel_threshold
        )


        tamper_fraction = float(
            predicted_tamper_pixels
            .float()
            .mean()
            .item()
        )


        is_tampered = (
            tamper_fraction
            >
            self.tamper_fraction_threshold
        )


        max_tamper_probability = float(
            tamper_probability
            .max()
            .item()
        )


        mean_tamper_probability = float(
            tamper_probability
            .mean()
            .item()
        )


        tamper_pixel_count = int(
            predicted_tamper_pixels
            .sum()
            .item()
        )


        total_pixels = int(
            predicted_tamper_pixels
            .numel()
        )


        return {

            "is_tampered":
                bool(
                    is_tampered
                ),

            "label":
                (
                    "TAMPERED"
                    if is_tampered
                    else "GENUINE"
                ),

            "tamper_fraction":
                round(
                    tamper_fraction,
                    6
                ),

            "tamper_fraction_threshold":
                round(
                    self.tamper_fraction_threshold,
                    6
                ),

            "pixel_probability_threshold":
                self.pixel_threshold,

            "max_tamper_probability":
                round(
                    max_tamper_probability,
                    4
                ),

            "mean_tamper_probability":
                round(
                    mean_tamper_probability,
                    4
                ),

            "tampered_pixels":
                tamper_pixel_count,

            "total_pixels":
                total_pixels,
        }


# =========================================================
# COMPLETE KYC PIPELINE
# =========================================================

def run_kyc(
    document_path,
    face_path,
):

    print(
        "\n=================================="
    )

    print(
        "MODULE 1 — AI KYC"
    )

    print(
        "=================================="
    )


    # -----------------------------------------------------
    # DOCUMENT
    # -----------------------------------------------------

    document_detector = (
        DocumentForgeryDetector()
    )


    document_result = (
        document_detector.predict(
            document_path
        )
    )


    print(
        "\nDocument result:"
    )

    print(
        document_result[
            "label"
        ]
    )


    # -----------------------------------------------------
    # LIVENESS
    # -----------------------------------------------------

    liveness_detector = (
        LivenessDetector()
    )


    liveness_result = (
        liveness_detector.predict(
            face_path
        )
    )


    print(
        "\nLiveness result:"
    )

    print(
        liveness_result[
            "label"
        ]
    )


    # -----------------------------------------------------
    # FUSION
    # -----------------------------------------------------

    live_score = float(
        liveness_result.get(
            "live_score",
            0.0
        )
    )


    kyc_result = (
        calculate_kyc_score(

            document_tampered=
                document_result[
                    "is_tampered"
                ],

            live_score=
                live_score,
        )
    )


    # -----------------------------------------------------
    # COMPLETE RESPONSE
    # -----------------------------------------------------

    final_result = {

        "module":
            "AI KYC",

        "document_analysis":
            document_result,

        "liveness_analysis":
            liveness_result,

        "kyc_result":
            kyc_result,
    }


    print(
        "\n=================================="
    )

    print(
        "FINAL KYC RESULT"
    )

    print(
        "=================================="
    )


    print(
        json.dumps(
            final_result,
            indent=4,
        )
    )


    return final_result


# =========================================================
# COMMAND LINE
# =========================================================

def main():

    parser = argparse.ArgumentParser()


    parser.add_argument(
        "--document",

        required=True,

        help=(
            "Path to identity "
            "document image"
        ),
    )


    parser.add_argument(
        "--face",

        required=True,

        help=(
            "Path to face image"
        ),
    )


    args = parser.parse_args()


    run_kyc(
        args.document,
        args.face,
    )


if __name__ == "__main__":

    main()