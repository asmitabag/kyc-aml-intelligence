from pathlib import Path
import argparse
import json
import sys

import cv2
import numpy as np
import torch


# =========================================================
# IMPORT PYTHON-3.9-COMPATIBLE MINIFASNET
# =========================================================

CURRENT_DIR = Path(__file__).resolve().parent

sys.path.insert(
    0,
    str(CURRENT_DIR)
)

from fastnet_compat import MiniFASNetV2


# =========================================================
# CONFIG
# =========================================================

PROJECT_ROOT = Path(
    __file__
).resolve().parents[3]


WEIGHTS_PATH = (
    PROJECT_ROOT
    / "third_party"
    / "face-anti-spoofing"
    / "weights"
    / "MiniFASNetV2.pth"
)


INPUT_SIZE = 80

CROP_SCALE = 2.7


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
# FACE CROP
# =========================================================

def crop_face(
    image,
    bbox,
    scale=2.7,
    output_size=80,
):

    image_height, image_width = (
        image.shape[:2]
    )


    x, y, box_width, box_height = bbox


    if (
        box_width <= 0
        or box_height <= 0
    ):

        raise ValueError(
            "Invalid face bounding box"
        )


    scale = min(
        (image_height - 1)
        / box_height,

        (image_width - 1)
        / box_width,

        scale,
    )


    new_width = (
        box_width
        * scale
    )

    new_height = (
        box_height
        * scale
    )


    center_x = (
        x
        + box_width / 2
    )

    center_y = (
        y
        + box_height / 2
    )


    x1 = max(
        0,
        int(
            center_x
            - new_width / 2
        )
    )


    y1 = max(
        0,
        int(
            center_y
            - new_height / 2
        )
    )


    x2 = min(
        image_width - 1,
        int(
            center_x
            + new_width / 2
        )
    )


    y2 = min(
        image_height - 1,
        int(
            center_y
            + new_height / 2
        )
    )


    cropped = image[
        y1:y2 + 1,
        x1:x2 + 1
    ]


    if cropped.size == 0:

        raise ValueError(
            "Face crop is empty"
        )


    cropped = cv2.resize(
        cropped,
        (
            output_size,
            output_size,
        )
    )


    return cropped


# =========================================================
# LIVENESS DETECTOR
# =========================================================

class LivenessDetector:

    def __init__(self):

        print(
            "Loading MiniFASNetV2..."
        )


        self.model = (
            MiniFASNetV2()
        )


        state_dict = torch.load(
            WEIGHTS_PATH,
            map_location="cpu",
            weights_only=True,
        )


        self.model.load_state_dict(
            state_dict
        )


        self.model.to(
            DEVICE
        )


        self.model.eval()


        cascade_path = (
            cv2.data.haarcascades
            + "haarcascade_frontalface_default.xml"
        )


        self.face_detector = (
            cv2.CascadeClassifier(
                cascade_path
            )
        )


        if self.face_detector.empty():

            raise RuntimeError(
                "Could not load OpenCV face detector"
            )


        print(
            "MiniFASNetV2 loaded on:",
            DEVICE
        )


    # =====================================================
    # FIND LARGEST FACE
    # =====================================================

    def detect_face(
        self,
        image,
    ):

        gray = cv2.cvtColor(
            image,
            cv2.COLOR_BGR2GRAY,
        )


        faces = (
            self.face_detector
            .detectMultiScale(
                gray,

                scaleFactor=1.1,

                minNeighbors=5,

                minSize=(
                    50,
                    50,
                ),
            )
        )


        if len(faces) == 0:

            return None


        largest_face = max(
            faces,

            key=lambda box:
                box[2]
                * box[3]
        )


        return [
            int(value)
            for value
            in largest_face
        ]


    # =====================================================
    # PREDICT
    # =====================================================

    def predict(
        self,
        image_path,
    ):

        image_path = Path(
            image_path
        )


        image = cv2.imread(
            str(
                image_path
            )
        )


        if image is None:

            raise ValueError(
                f"Could not load image: "
                f"{image_path}"
            )


        bbox = self.detect_face(
            image
        )


        if bbox is None:

            return {
                "status":
                    "NO_FACE",

                "is_live":
                    False,

                "label":
                    "NO_FACE",

                "live_score":
                    0.0,

                "confidence":
                    0.0,

                "bbox":
                    None,
            }


        face = crop_face(
            image,
            bbox,
            scale=CROP_SCALE,
            output_size=INPUT_SIZE,
        )


        tensor = (
            torch
            .from_numpy(
                face.transpose(
                    2,
                    0,
                    1
                )
            )
            .float()
            .unsqueeze(0)
            .to(
                DEVICE
            )
        )


        with torch.no_grad():

            output = self.model(
                tensor
            )


            probabilities = (
                torch.softmax(
                    output,
                    dim=1,
                )
                .cpu()
                .numpy()[0]
            )


        predicted_class = int(
            np.argmax(
                probabilities
            )
        )


        confidence = float(
            probabilities[
                predicted_class
            ]
        )


        live_score = float(
            probabilities[1]
        )


        is_live = (
            predicted_class == 1
        )


        label = (
            "REAL"
            if is_live
            else "FAKE"
        )


        return {
            "status":
                "SUCCESS",

            "is_live":
                is_live,

            "label":
                label,

            "live_score":
                round(
                    live_score,
                    4
                ),

            "confidence":
                round(
                    confidence,
                    4
                ),

            "predicted_class":
                predicted_class,

            "class_probabilities":
                [
                    round(
                        float(value),
                        4
                    )
                    for value
                    in probabilities
                ],

            "bbox":
                bbox,
        }


# =========================================================
# COMMAND-LINE TEST
# =========================================================

def main():

    parser = argparse.ArgumentParser()


    parser.add_argument(
        "image",
        help="Path to face image",
    )


    args = parser.parse_args()


    detector = (
        LivenessDetector()
    )


    result = detector.predict(
        args.image
    )


    print(
        "\n=================================="
    )

    print(
        "LIVENESS RESULT"
    )

    print(
        "=================================="
    )


    print(
        json.dumps(
            result,
            indent=4,
        )
    )


if __name__ == "__main__":

    main()