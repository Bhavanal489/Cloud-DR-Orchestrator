from fastapi import FastAPI
from fastapi.responses import JSONResponse
import urllib.request

app = FastAPI(
    title="DR Traffic Gateway",
    description="Routes traffic to the healthy primary or backup service",
    version="1.0.0"
)

PRIMARY_URL = "http://primary:8000/health"
BACKUP_URL = "http://backup:8000/health"


def check_service(url):
    try:
        with urllib.request.urlopen(url, timeout=2) as response:
            return response.status == 200
    except Exception:
        return False


@app.get("/")
def route_request():

    if check_service(PRIMARY_URL):
        return {
            "active_backend": "primary",
            "message": "Traffic routed to primary server"
        }

    if check_service(BACKUP_URL):
        return {
            "active_backend": "backup",
            "message": "Primary failed. Traffic routed to backup server"
        }

    return JSONResponse(
        status_code=503,
        content={
            "active_backend": "none",
            "message": "Both primary and backup are unavailable"
        }
    )


@app.get("/health")
def gateway_health():
    return {
        "gateway": "healthy",
        "primary": "healthy" if check_service(PRIMARY_URL) else "failed",
        "backup": "healthy" if check_service(BACKUP_URL) else "failed"
    }