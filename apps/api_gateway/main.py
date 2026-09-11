from fastapi import FastAPI

app = FastAPI(
    title="KYC-AML Intelligence Platform",
    version="0.1.0"
)


@app.get("/health")
def health():
    return {
        "status": "ok"
    }