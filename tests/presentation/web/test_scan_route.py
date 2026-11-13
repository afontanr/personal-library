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
    assert "scanner-reader" in response.text


@pytest.mark.asyncio
async def test_scan_route_loads_isbn_reader_with_local_wasm():
    app = create_app()

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/scan")

    assert response.status_code == 200
    assert "js/vendor/barcode-detector/ponyfill.js" in response.text
    assert "js/isbn-reader.js" in response.text
    assert (
        'data-wasm-url="http://test/static/js/vendor/barcode-detector/'
        'zxing_reader.wasm"' in response.text
    )
    assert "html5-qrcode" not in response.text


@pytest.mark.asyncio
async def test_zxing_wasm_is_served_as_wasm():
    app = create_app()

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get(
            "/static/js/vendor/barcode-detector/zxing_reader.wasm"
        )

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/wasm"


@pytest.mark.asyncio
async def test_scan_page_offers_manual_isbn_entry():
    app = create_app()

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/scan")

    assert 'id="manual-isbn-form"' in response.text
    assert 'id="manual-isbn-input"' in response.text


@pytest.mark.asyncio
async def test_scan_form_offers_futuras_compras():
    app = create_app()

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/scan")

    assert '<option value="to_buy">Por comprar</option>' in response.text
    assert 'id="scan-to-buy-btn"' in response.text
    assert "Añadir a futuras compras" in response.text
