import pytest
from httpx import ASGITransport, AsyncClient

from personal_library.main import create_app


@pytest.mark.asyncio
async def test_scan_route_returns_200():
    app = create_app()

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/scan")

    assert response.status_code == 200
    assert "Escanea" in response.text
    assert "camera-view" in response.text
