from unittest.mock import patch

import av
import numpy as np
from pyzbar.pyzbar import Decoded, Rect

from personal_library.barcode_scanner.app import BarcodeProcessor, process_frame


def test_process_frame_returns_video_frame_with_no_barcode():
    blank = np.zeros((480, 640, 3), dtype=np.uint8)
    frame = av.VideoFrame.from_ndarray(blank, format="bgr24")

    result_frame, barcodes = process_frame(frame)

    assert isinstance(result_frame, av.VideoFrame)
    assert barcodes == []


def _make_fake_barcode(data: str | bytes) -> Decoded:
    raw = data if isinstance(data, bytes) else data.encode("utf-8")
    return Decoded(
        data=raw,
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


@patch("personal_library.barcode_scanner.app.decode")
def test_process_frame_handles_non_utf8_payload(mock_decode):
    mock_decode.return_value = [_make_fake_barcode(b"\xff\xfe\x00invalid")]

    blank = np.zeros((480, 640, 3), dtype=np.uint8)
    frame = av.VideoFrame.from_ndarray(blank, format="bgr24")

    result_frame, barcodes = process_frame(frame)

    assert isinstance(result_frame, av.VideoFrame)
    assert len(barcodes) == 1
    assert "\ufffd" in barcodes[0]


@patch("personal_library.barcode_scanner.app.decode")
def test_barcode_processor_captures_first_result(mock_decode):
    mock_decode.return_value = [_make_fake_barcode("ABC-001")]

    processor = BarcodeProcessor()
    blank = np.zeros((480, 640, 3), dtype=np.uint8)
    frame = av.VideoFrame.from_ndarray(blank, format="bgr24")

    processor.recv(frame)

    assert processor.get_result() == "ABC-001"


@patch("personal_library.barcode_scanner.app.decode")
def test_barcode_processor_ignores_frames_after_first_result(mock_decode):
    mock_decode.return_value = [_make_fake_barcode("FIRST")]

    processor = BarcodeProcessor()
    blank = np.zeros((480, 640, 3), dtype=np.uint8)
    frame = av.VideoFrame.from_ndarray(blank, format="bgr24")

    processor.recv(frame)
    assert processor.get_result() == "FIRST"

    mock_decode.return_value = [_make_fake_barcode("SECOND")]
    processor.recv(frame)

    assert processor.get_result() == "FIRST"
    assert mock_decode.call_count == 1
