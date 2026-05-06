from __future__ import annotations

import json
import os
import re
from typing import Any

import httpx

_ISBN13 = re.compile(r"^\d{13}$")
_ISBN10 = re.compile(r"^\d{9}[\dX]$")

MSG_INVALID_ISBN = (
    "El codigo escaneado no tiene formato ISBN-13 (13 digitos) "
    "ni ISBN-10 (9 digitos mas digito de control)."
)
MSG_NOT_FOUND = "Libro no encontrado para ese ISBN."
MSG_UPSTREAM_502 = "El servicio de catalogo no respondio correctamente (502)."
MSG_INVALID_JSON = "La API devolvio un cuerpo que no es JSON valido."


def normalize_isbn_for_api(raw: str | None) -> str | None:
    """Devuelve ISBN listo para el path de FastAPI o None si no coincide."""
    if raw is None:
        return None
    cleaned = re.sub(r"[^0-9Xx]", "", raw.strip()).upper()
    if _ISBN13.fullmatch(cleaned):
        return cleaned
    if _ISBN10.fullmatch(cleaned):
        return cleaned
    return None


def default_api_base() -> str:
    return os.environ.get("PERSONAL_LIBRARY_API_BASE", "http://127.0.0.1:8000").rstrip("/")


def lookup_book_for_scan(
    raw: str | None,
    base_url: str,
    client: httpx.Client,
    *,
    timeout: float = 15.0,
) -> tuple[dict[str, Any] | None, str | None]:
    isbn = normalize_isbn_for_api(raw)
    if isbn is None:
        return None, MSG_INVALID_ISBN
    url = f"{base_url.rstrip('/')}/api/books/{isbn}"
    try:
        response = client.get(url, timeout=timeout)
    except httpx.RequestError as exc:
        return None, f"No se pudo contactar la API: {exc}"

    if response.status_code == 200:
        try:
            return response.json(), None
        except json.JSONDecodeError:
            return None, MSG_INVALID_JSON
    if response.status_code == 404:
        return None, MSG_NOT_FOUND
    if response.status_code == 502:
        return None, MSG_UPSTREAM_502
    return None, f"Error del servidor ({response.status_code})."
