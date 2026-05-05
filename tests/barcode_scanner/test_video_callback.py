import numpy as np
import av

from personal_library.barcode_scanner.app import process_frame


def test_process_frame_returns_video_frame_with_no_barcode():
    blank = np.zeros((480, 640, 3), dtype=np.uint8)
    frame = av.VideoFrame.from_ndarray(blank, format="bgr24")

    result_frame, barcodes = process_frame(frame)

    assert isinstance(result_frame, av.VideoFrame)
    assert barcodes == []
