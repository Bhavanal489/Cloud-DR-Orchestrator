import os
from fastapi import FastAPI

service_name = os.getenv("SERVICE_NAME", "unknown")

app = FastAPI(
    title=f"{service_name} Server"
)


@app.get("/health")
def health():
    return {
        "service": service_name,
        "status": "healthy"
    }
    