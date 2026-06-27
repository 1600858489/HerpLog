from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="HerpLog API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root() -> dict[str, str]:
    return {"message": "HerpLog API is running"}


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}
