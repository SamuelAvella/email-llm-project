"""
email_api_server.py
====================
FastAPI simulada · Fase 1 — Fuente de Datos Mock

Los datos viven en mock_emails.py — este archivo solo contiene lógica HTTP.
Para añadir emails nuevos edita mock_emails.py, no este archivo.

Endpoints:
    GET /health
    GET /emails?limit=50&skip=0
    GET /emails/{email_id}

Inicio rápido:
    pip install fastapi uvicorn
    uvicorn email_api_server:app --reload --port 8000
"""

from __future__ import annotations

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse

from mock_emails import MOCK_EMAILS

app = FastAPI(
    title="Email Pipeline — Mock API",
    description="Simula la Gmail API para desarrollo local sin OAuth2.",
    version="1.0.0",
)


@app.get("/health", tags=["Meta"])
def health_check() -> dict:
    """Verifica que el servidor está operativo."""
    return {"status": "ok", "emails_available": len(MOCK_EMAILS)}


@app.get("/emails", tags=["Emails"])
def get_emails(
    limit: int = Query(default=50, ge=1, le=200, description="Máximo de emails a devolver"),
    skip:  int = Query(default=0,  ge=0,           description="Emails a saltar (paginación)"),
) -> JSONResponse:
    """Devuelve una lista paginada de emails mock."""
    page = MOCK_EMAILS[skip : skip + limit]
    return JSONResponse(content={
        "emails":   page,
        "total":    len(MOCK_EMAILS),
        "returned": len(page),
        "skip":     skip,
        "limit":    limit,
    })


@app.get("/emails/{email_id}", tags=["Emails"])
def get_email_by_id(email_id: str) -> JSONResponse:
    """Devuelve un email concreto por su ID."""
    match = next((e for e in MOCK_EMAILS if e["id"] == email_id), None)
    if match is None:
        raise HTTPException(status_code=404, detail=f"Email '{email_id}' not found.")
    return JSONResponse(content=match)