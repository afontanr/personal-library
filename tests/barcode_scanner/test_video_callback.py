from unittest.mock import patch

import av
import numpy as np
from pyzbar.pyzbar import Decoded, Rect

from personal_library.barcode_scanner.app import process_frame


def test_process_frame_returns_video_frame_with_no_barcode():
    blank = np.zeros((480, 640, 3), dtype=np.uint8)
    frame = av.VideoFrame.from_ndarray(blank, format="bgr24")

    result_frame, barcodes = process_frame(frame)

    assert isinstance(result_frame, av.VideoFrame)
    assert barcodes == []


def _make_fake_barcode(data: str) -> Decoded:
    return Decoded(
        data=data.encode("utf-8"),
        type="CODE128",
        rect=Rect(left=10, top=10, width=100, height=50),
        polygon=[],
        quality=1,
        orientation="UP",
    )


@patch("personal_library.barcode_scanner.app.decode")
def test_process_frame_detects_barcode(mock_decode):
    mock_decode.return_value = [_make_fake_barcode("1234567890")]

    blank = np.zeros((480, 640, 3), dtype=np.uint8)
    frame = av.VideoFrame.from_ndarray(blank, format="bgr24")

    result_frame, barcodes = process_frame(frame)

    assert isinstance(result_frame, av.VideoFrame)
    assert barcodes == ["1234567890"]
    mock_decode.assert_called_once()
