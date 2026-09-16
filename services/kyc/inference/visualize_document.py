from pathlib import Path
import argparse
import sys

import cv2
import numpy as np
import torch
import torch.nn.functional as F
from PIL import Image


# =========================================================
# PATH SETUP
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
        / "inference"
    )
)

from run_kyc import DocumentForgeryDetector


# =========================================================
# VISUALIZE
# =========================================================

def visualize_document(
    document_path,
    output_path,
):

    document_path = Path(
        document_path
    )

    output_path = Path(
        output_path
    )


    detector = (
        DocumentForgeryDetector()
    )


    original_pil = Image.open(
        document_path
    ).convert(
        "RGB"
    )


    encoded = (
        detector.processor(
            images=original_pil,
            return_tensors="pt",
        )
    )


    pixel_values = (
        encoded[
            "pixel_values"
        ]
        .to(
            next(
                detector.model.parameters()
            ).device
        )
        .contiguous()
    )


    with torch.no_grad():

        outputs = (
            detector.model(
                pixel_values=pixel_values
            )
        )


        logits = (
            F.interpolate(
                outputs.logits,

                size=(
                    512,
                    512,
                ),

                mode="bilinear",

                align_corners=False,
            )
        )


        probabilities = (
            torch.softmax(
                logits,
                dim=1,
            )
        )


    tamper_probability = (
        probabilities[
            0,
            1
        ]
        .cpu()
        .numpy()
    )


    predicted_mask = (
        tamper_probability
        >
        detector.pixel_threshold
    ).astype(
        np.uint8
    )


    tamper_fraction = float(
        predicted_mask.mean()
    )


    is_tampered = (
        tamper_fraction
        >
        detector.tamper_fraction_threshold
    )


    # =====================================================
    # ORIGINAL IMAGE
    # =====================================================

    original = np.array(
        original_pil.resize(
            (
                512,
                512,
            )
        )
    )


    original = cv2.cvtColor(
        original,
        cv2.COLOR_RGB2BGR,
    )


    # =====================================================
    # MASK IMAGE
    # =====================================================

    mask_image = (
        predicted_mask
        * 255
    ).astype(
        np.uint8
    )


    mask_image = cv2.cvtColor(
        mask_image,
        cv2.COLOR_GRAY2BGR,
    )


    # =====================================================
    # OVERLAY
    # =====================================================

    overlay = (
        original.copy()
    )


    red_layer = np.zeros_like(
        overlay
    )


    red_layer[
        :,
        :,
        2
    ] = 255


    tamper_pixels = (
        predicted_mask
        == 1
    )


    overlay[
        tamper_pixels
    ] = (
        0.55
        * overlay[
            tamper_pixels
        ]
        +
        0.45
        * red_layer[
            tamper_pixels
        ]
    ).astype(
        np.uint8
    )


    # =====================================================
    # LABELS
    # =====================================================

    status = (
        "TAMPERED"
        if is_tampered
        else "GENUINE"
    )


    cv2.putText(
        original,
        "Original",
        (
            15,
            35,
        ),
        cv2.FONT_HERSHEY_SIMPLEX,
        1,
        (
            0,
            255,
            0,
        ),
        2,
    )


    cv2.putText(
        mask_image,
        "Predicted Tamper Mask",
        (
            15,
            35,
        ),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        (
            0,
            255,
            0,
        ),
        2,
    )


    cv2.putText(
        overlay,
        f"Overlay: {status}",
        (
            15,
            35,
        ),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        (
            0,
            255,
            0,
        ),
        2,
    )


    cv2.putText(
        overlay,
        (
            f"Tamper fraction: "
            f"{tamper_fraction:.4f}"
        ),
        (
            15,
            70,
        ),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.65,
        (
            0,
            255,
            0,
        ),
        2,
    )


    # =====================================================
    # COMBINE
    # =====================================================

    combined = cv2.hconcat(
        [
            original,
            mask_image,
            overlay,
        ]
    )


    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )


    cv2.imwrite(
        str(
            output_path
        ),
        combined
    )


    print(
        "\n=================================="
    )

    print(
        "FORGERY VISUALIZATION"
    )

    print(
        "=================================="
    )

    print(
        "Document:",
        document_path
    )

    print(
        "Prediction:",
        status
    )

    print(
        "Tamper fraction:",
        round(
            tamper_fraction,
            6
        )
    )

    print(
        "Threshold:",
        round(
            detector.tamper_fraction_threshold,
            6
        )
    )

    print(
        "Saved:",
        output_path
    )


# =========================================================
# CLI
# =========================================================

def main():

    parser = argparse.ArgumentParser()


    parser.add_argument(
        "--document",
        required=True,
    )


    parser.add_argument(
        "--output",
        default=(
            "services/kyc/artifacts/"
            "forgery_visualization.jpg"
        ),
    )


    args = (
        parser.parse_args()
    )


    visualize_document(
        args.document,
        args.output,
    )


if __name__ == "__main__":

    main()