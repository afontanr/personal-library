from __future__ import annotations

import os
import re
from typing import Any

import httpx

_ISBN13 = re.compile(r"^\d{13}$")
_ISBN10 = re.compile(r"^\d{9}[\dX]$")


def normalize_isbn_for_api(raw: str) -> str | None:
    """Devuelve ISBN listo para el path de FastAPI o None si no coincide con el patrón de la API."""
    cleaned = re.sub(r"[^0-9Xx]", "", (raw or "").strip()).upper()
    if _ISBN13.fullmatch(cleaned):
        return cleaned
    if _ISBN10.fullmatch(cleaned):
        return cleaned
    return None


def default_api_base() -> str:
    return os.environ.get("PERSONAL_LIBRARY_API_BASE", "http://127.0.0.1:8000").rstrip("/")


def lookup_book_for_scan(
    raw: str,
    base_url: str,
    client: httpx.Client,
    *,
    timeout: float = 15.0,
) -> tuple[dict[str, Any] | None, str | None]:
    isbn = normalize_isbn_for_api(raw)
    if isbn is None:
        return None, (
            "El codigo escaneado no tiene formato ISBN-13 (13 digitos) "
            "ni ISBN-10 (9 digitos mas digito de control)."
        )
    url = f"{base_url.rstrip('/')}/api/books/{isbn}"
    try:
        response = client.get(url, timeout=timeout)
    except httpx.RequestError as exc:
        return None, f"No se pudo contactar la API: {exc}"

    if response.status_code == 200:
        return response.json(), None
    if response.status_code == 404:
        return None, "Libro no encontrado para ese ISBN."
    if response.status_code == 502:
        return None, "El servicio de catalogo no respondio correctamente (502)."
    return None, f"Error del servidor ({response.status_code})."
