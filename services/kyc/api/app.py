from pathlib import Path
import shutil
import sys
import tempfile

from fastapi import (
    FastAPI,
    File,
    HTTPException,
    UploadFile,
)


# =========================================================
# PROJECT PATHS
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


from run_kyc import DocumentForgeryDetector

from liveness_service import LivenessDetector

from kyc_score import calculate_kyc_score


# =========================================================
# FASTAPI
# =========================================================

app = FastAPI(
    title="AI KYC Module",
    description=(
        "Document forgery detection + "
        "face liveness + KYC risk fusion"
    ),
    version="1.0.0",
)


# =========================================================
# LOAD MODELS ONCE
# =========================================================

print(
    "\nLoading Module 1 models..."
)


document_detector = (
    DocumentForgeryDetector()
)


liveness_detector = (
    LivenessDetector()
)


print(
    "\nModule 1 models ready."
)


# =========================================================
# HEALTH CHECK
# =========================================================

@app.get("/health")
def health():

    return {
        "status":
            "ok",

        "module":
            "AI KYC",

        "document_model":
            "SegFormer-B0",

        "liveness_model":
            "MiniFASNetV2",
    }


# =========================================================
# KYC ENDPOINT
# =========================================================

@app.post("/kyc/verify")
async def verify_kyc(

    document: UploadFile = File(
        ...
    ),

    face: UploadFile = File(
        ...
    ),
):

    document_temp = None

    face_temp = None


    try:

        # -------------------------------------------------
        # SAVE DOCUMENT TEMPORARILY
        # -------------------------------------------------

        document_suffix = (
            Path(
                document.filename
                or "document.jpg"
            )
            .suffix
            or ".jpg"
        )


        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=document_suffix,
        ) as temp_document:

            shutil.copyfileobj(
                document.file,
                temp_document,
            )

            document_temp = (
                temp_document.name
            )


        # -------------------------------------------------
        # SAVE FACE TEMPORARILY
        # -------------------------------------------------

        face_suffix = (
            Path(
                face.filename
                or "face.jpg"
            )
            .suffix
            or ".jpg"
        )


        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=face_suffix,
        ) as temp_face:

            shutil.copyfileobj(
                face.file,
                temp_face,
            )

            face_temp = (
                temp_face.name
            )


        # -------------------------------------------------
        # DOCUMENT ANALYSIS
        # -------------------------------------------------

        document_result = (
            document_detector.predict(
                document_temp
            )
        )


        # -------------------------------------------------
        # LIVENESS ANALYSIS
        # -------------------------------------------------

        liveness_result = (
            liveness_detector.predict(
                face_temp
            )
        )


        if (
            liveness_result[
                "status"
            ]
            != "SUCCESS"
        ):

            raise HTTPException(
                status_code=400,
                detail=(
                    "No valid face detected "
                    "in uploaded face image"
                ),
            )


        # -------------------------------------------------
        # KYC FUSION
        # -------------------------------------------------

        kyc_result = (
            calculate_kyc_score(

                document_tampered=
                    document_result[
                        "is_tampered"
                    ],

                live_score=
                    liveness_result[
                        "live_score"
                    ],
            )
        )


        # -------------------------------------------------
        # FINAL RESPONSE
        # -------------------------------------------------

        return {

            "module":
                "AI KYC",

            "document_analysis":
                document_result,

            "liveness_analysis":
                liveness_result,

            "kyc_result":
                kyc_result,
        }


    except HTTPException:

        raise


    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=str(
                error
            ),
        )


    finally:

        if (
            document_temp
            and Path(
                document_temp
            ).exists()
        ):

            Path(
                document_temp
            ).unlink()


        if (
            face_temp
            and Path(
                face_temp
            ).exists()
        ):

            Path(
                face_temp
            ).unlink()