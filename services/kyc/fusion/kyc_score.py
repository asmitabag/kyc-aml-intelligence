import argparse
import json


# =========================================================
# CONFIG
# =========================================================

DOCUMENT_WEIGHT = 0.60
LIVENESS_WEIGHT = 0.40


# =========================================================
# KYC SCORE
# =========================================================

def calculate_kyc_score(
    document_tampered,
    live_score,
):

    # ---------------------------------------------
    # Document risk
    # ---------------------------------------------

    if document_tampered:

        document_risk = 1.0

    else:

        document_risk = 0.0


    # ---------------------------------------------
    # Liveness risk
    # ---------------------------------------------

    live_score = max(
        0.0,
        min(
            1.0,
            float(
                live_score
            )
        )
    )


    liveness_risk = (
        1.0
        - live_score
    )


    # ---------------------------------------------
    # Final KYC risk score
    # ---------------------------------------------

    s_kyc = (
        DOCUMENT_WEIGHT
        * document_risk

        +

        LIVENESS_WEIGHT
        * liveness_risk
    )


    # ---------------------------------------------
    # Risk category
    # ---------------------------------------------

    if s_kyc < 0.30:

        risk_level = (
            "LOW"
        )

        decision = (
            "PASS"
        )


    elif s_kyc < 0.60:

        risk_level = (
            "MEDIUM"
        )

        decision = (
            "MANUAL_REVIEW"
        )


    else:

        risk_level = (
            "HIGH"
        )

        decision = (
            "REJECT"
        )


    # ---------------------------------------------
    # Explanation
    # ---------------------------------------------

    reasons = []


    if document_tampered:

        reasons.append(
            "Document forgery/tampering detected"
        )

    else:

        reasons.append(
            "No document tampering detected"
        )


    if live_score >= 0.5:

        reasons.append(
            "Face passed liveness verification"
        )

    else:

        reasons.append(
            "Face failed liveness verification"
        )


    return {

        "S_kyc":
            round(
                s_kyc,
                4
            ),

        "risk_level":
            risk_level,

        "decision":
            decision,

        "document": {

            "tampered":
                bool(
                    document_tampered
                ),

            "risk_score":
                round(
                    document_risk,
                    4
                ),
        },

        "liveness": {

            "live_score":
                round(
                    live_score,
                    4
                ),

            "risk_score":
                round(
                    liveness_risk,
                    4
                ),

            "is_live":
                live_score
                >= 0.5,
        },

        "weights": {

            "document":
                DOCUMENT_WEIGHT,

            "liveness":
                LIVENESS_WEIGHT,
        },

        "reasons":
            reasons,
    }


# =========================================================
# COMMAND LINE
# =========================================================

def main():

    parser = argparse.ArgumentParser()


    parser.add_argument(
        "--document-tampered",

        type=int,

        choices=[
            0,
            1
        ],

        required=True,
    )


    parser.add_argument(
        "--live-score",

        type=float,

        required=True,
    )


    args = parser.parse_args()


    result = calculate_kyc_score(

        document_tampered=bool(
            args.document_tampered
        ),

        live_score=args.live_score,
    )


    print(
        "\n=================================="
    )

    print(
        "KYC RISK RESULT"
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