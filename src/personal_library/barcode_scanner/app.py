from __future__ import annotations

import threading

import av
import cv2
from pyzbar.pyzbar import decode


def process_frame(frame: av.VideoFrame) -> tuple[av.VideoFrame, list[str]]:
    """Decode barcodes from a video frame.

    Returns the annotated frame and a list of decoded barcode strings.
    """
    img = frame.to_ndarray(format="bgr24")
    barcodes = decode(img)
    decoded_values: list[str] = []

    for barcode in barcodes:
        data = barcode.data.decode("utf-8")
        decoded_values.append(data)
        x, y, w, h = barcode.rect
        cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), 2)
        cv2.putText(
            img,
            data,
            (x, y - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (0, 255, 0),
            2,
        )

    return av.VideoFrame.from_ndarray(img, format="bgr24"), decoded_values


class BarcodeProcessor:
    """Video processor that stops after the first successful barcode read."""

    def __init__(self) -> None:
        self.result: str | None = None
        self._lock = threading.Lock()

    def recv(self, frame: av.VideoFrame) -> av.VideoFrame:
        with self._lock:
            if self.result is not None:
                return frame

        annotated_frame, decoded_values = process_frame(frame)

        if decoded_values:
            with self._lock:
                self.result = decoded_values[0]

        return annotated_frame

    def get_result(self) -> str | None:
        with self._lock:
            return self.result


def main() -> None:
    import time

    import streamlit as st
    from streamlit_webrtc import WebRtcMode, webrtc_streamer

    st.set_page_config(page_title="Lector de Codigos de Barras", layout="centered")
    st.title("Lector de codigos de barras")

    if "scanned_barcode" in st.session_state:
        st.success(f"Codigo detectado: **{st.session_state['scanned_barcode']}**")
        if st.button("Escanear otro"):
            del st.session_state["scanned_barcode"]
            st.rerun()
        return

    st.write("Pulsa **START** para abrir la camara y escanear un codigo de barras.")

    ctx = webrtc_streamer(
        key="barcode-scanner",
        mode=WebRtcMode.SENDRECV,
        video_processor_factory=BarcodeProcessor,
        media_stream_constraints={"video": True, "audio": False},
        async_processing=True,
    )

    if ctx.state.playing and ctx.video_processor:
        result = ctx.video_processor.get_result()
        if result:
            st.session_state["scanned_barcode"] = result
            st.rerun()
        else:
            time.sleep(0.2)
            st.rerun()


if __name__ == "__page__" or __name__ == "__main__":
    main()
