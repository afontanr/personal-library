# barcode-detector (vendored)

Served as-is (no build step) by `scan.html`.

| File | Source | Version |
| --- | --- | --- |
| `ponyfill.js` | `https://cdn.jsdelivr.net/npm/barcode-detector@3.2.3/dist/iife/ponyfill.js` (MIT) | 3.2.3 |
| `zxing_reader.wasm` | `https://cdn.jsdelivr.net/npm/zxing-wasm@3.1.6/dist/reader/zxing_reader.wasm` (MIT, ZXing-C++ Apache-2.0) | 3.1.6 |

`zxing_reader.wasm` SHA-256: `5003fb4b88c4fbd1fd518a2fd8c8ad365c519e183a08c03a322dddfea3cea84e`
(must match `ZXING_WASM_SHA256` inside `ponyfill.js`; update both together).
