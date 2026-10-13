from pathlib import Path
import re

path = Path("apps/api_gateway/main.py")
source = path.read_text(encoding="utf-8")
original = source

# Consolidate the duplicate auth imports.
source = source.replace(
    "from services.auth.tokens import create_access_token, get_current_user\n",
    ""
)
source = source.replace(
    "from services.auth.tokens import (\n"
    "    create_access_token,\n"
    "    get_current_user,\n"
    "    require_analyst,\n"
    ")\n",
    "from services.auth.tokens import (\n"
    "    create_access_token,\n"
    "    get_current_user,\n"
    "    require_analyst,\n"
    ")\n",
)

targets = {
    "list_cases": "def list_cases(db: Session = Depends(get_db)):",
    "get_case_by_id": "def get_case_by_id(case_id: str, db: Session = Depends(get_db)):",
    "update_status": "def update_status(case_id: str, data: CaseStatusUpdate, db: Session = Depends(get_db)):",
    "submit_feedback": "def submit_feedback(case_id: str, feedback: CaseFeedback, db: Session = Depends(get_db)):",
    "feedback_dataset": "def feedback_dataset(db: Session = Depends(get_db)):",
    "generate_case_sar": "def generate_case_sar(case_id: str, db: Session = Depends(get_db)):",
}

for function_name, signature in targets.items():
    if f"def {function_name}(" not in source:
        raise SystemExit(f"STOP: function {function_name} was not found.")

    # Skip a function that already has the dependency.
    start = source.index(f"def {function_name}(")
    next_route = source.find("\n@app.", start)
    if next_route == -1:
        next_route = len(source)
    function_text = source[start:next_route]

    if "Depends(require_analyst)" in function_text:
        continue

    if signature not in source:
        raise SystemExit(
            f"STOP: signature did not match for {function_name}; no file was written."
        )

    if function_name == "list_cases":
        replacement = (
            "def list_cases(\n"
            "    db: Session = Depends(get_db),\n"
            "    analyst: models.User = Depends(require_analyst),\n"
            "):"
        )
    elif function_name == "get_case_by_id":
        replacement = (
            "def get_case_by_id(\n"
            "    case_id: str,\n"
            "    db: Session = Depends(get_db),\n"
            "    analyst: models.User = Depends(require_analyst),\n"
            "):"
        )
    elif function_name == "update_status":
        replacement = (
            "def update_status(\n"
            "    case_id: str,\n"
            "    data: CaseStatusUpdate,\n"
            "    db: Session = Depends(get_db),\n"
            "    analyst: models.User = Depends(require_analyst),\n"
            "):"
        )
    elif function_name == "submit_feedback":
        replacement = (
            "def submit_feedback(\n"
            "    case_id: str,\n"
            "    feedback: CaseFeedback,\n"
            "    db: Session = Depends(get_db),\n"
            "    analyst: models.User = Depends(require_analyst),\n"
            "):"
        )
    elif function_name == "feedback_dataset":
        replacement = (
            "def feedback_dataset(\n"
            "    db: Session = Depends(get_db),\n"
            "    analyst: models.User = Depends(require_analyst),\n"
            "):"
        )
    else:
        replacement = (
            "def generate_case_sar(\n"
            "    case_id: str,\n"
            "    db: Session = Depends(get_db),\n"
            "    analyst: models.User = Depends(require_analyst),\n"
            "):"
        )

    source = source.replace(signature, replacement, 1)

if source == original:
    print("No changes were needed; these routes may already be protected.")
else:
    backup = path.with_suffix(".py.auth-backup")
    backup.write_text(original, encoding="utf-8")
    path.write_text(source, encoding="utf-8")
    print(f"Updated {path}")
    print(f"Backup saved to {backup}")
    print("Protected: " + ", ".join(targets.keys()))
