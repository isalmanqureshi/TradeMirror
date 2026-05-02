from fastapi import FastAPI

app = FastAPI(title="TradeMirror API", version="0.1.0")


@app.get("/")
def root() -> dict[str, str]:
    return {"message": "TradeMirror API is running"}


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "api"}
