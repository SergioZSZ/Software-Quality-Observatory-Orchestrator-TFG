import os
import requests

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI(title="SOCA Superset Embed API")


# Origen desde el que se sirve el portal SOCA
# Ejemplo: http://localhost:8030
PORTAL_ORIGIN = os.getenv("PORTAL_ORIGIN", "http://localhost:8030")


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        PORTAL_ORIGIN,
        "http://127.0.0.1:8030",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# URL que usa emb_api para hablar con Superset.
# Si emb_api está en Docker y Superset está en tu máquina host:
# usa http://host.docker.internal:8088
SUPERSET_URL = os.getenv("SUPERSET_DOMAIN", "http://host.docker.internal:8088")

SUPERSET_USERNAME = os.getenv("SUPERSET_USERNAME", "admin")
SUPERSET_PASSWORD = os.getenv("SUPERSET_PASSWORD")

DASHBOARD_ORG_EMBED_ID = os.getenv("DASHBOARD_ORG_EMBED_ID")
DASHBOARD_REPO_EMBED_ID = os.getenv("DASHBOARD_REPO_EMBED_ID")


@app.get("/health")
def health():
    return {"status": "ok"}


def get_superset_access_token():
    if not SUPERSET_PASSWORD:
        raise HTTPException(
            status_code=500,
            detail="Missing SUPERSET_PASSWORD",
        )

    response = requests.post(
        f"{SUPERSET_URL}/api/v1/security/login",
        json={
            "username": SUPERSET_USERNAME,
            "password": SUPERSET_PASSWORD,
            "provider": "db",
            "refresh": True,
        },
        timeout=15,
    )

    if response.status_code != 200:
        raise HTTPException(
            status_code=500,
            detail=f"Superset login failed: {response.text}",
        )

    return response.json()["access_token"]


def create_guest_token(dashboard_embed_id: str):
    if not dashboard_embed_id:
        raise HTTPException(
            status_code=500,
            detail="Missing dashboard embed id",
        )

    access_token = get_superset_access_token()

    response = requests.post(
        f"{SUPERSET_URL}/api/v1/security/guest_token/",
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        },
        json={
            "user": {
                "username": "soca-portal-viewer",
                "first_name": "SOCA",
                "last_name": "Viewer",
            },
            "resources": [
                {
                    "type": "dashboard",
                    "id": dashboard_embed_id,
                }
            ],
            "rls": [],
        },
        timeout=15,
    )

    if response.status_code != 200:
        raise HTTPException(
            status_code=500,
            detail=f"Guest token creation failed: {response.text}",
        )

    return {"token": response.json()["token"]}


@app.get("/superset/guest-token/org")
def get_org_guest_token():
    return create_guest_token(DASHBOARD_ORG_EMBED_ID)


@app.get("/superset/guest-token/repo")
def get_repo_guest_token():
    return create_guest_token(DASHBOARD_REPO_EMBED_ID)