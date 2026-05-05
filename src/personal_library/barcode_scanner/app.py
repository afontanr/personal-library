from __future__ import annotations

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


def main() -> None:
    import streamlit as st
    from streamlit_webrtc import WebRtcMode, webrtc_streamer

    st.set_page_config(page_title="Lector de Codigos de Barras", layout="centered")
    st.title("Lector de codigos de barras")
    st.write("Pulsa **START** para abrir la camara y escanear un codigo de barras.")

    result_placeholder = st.empty()

    def video_frame_callback(frame: av.VideoFrame) -> av.VideoFrame:
        annotated_frame, decoded_values = process_frame(frame)
        if decoded_values:
            st.session_state["last_barcode"] = decoded_values[-1]
        return annotated_frame

    webrtc_streamer(
        key="barcode-scanner",
        mode=WebRtcMode.SENDRECV,
        video_frame_callback=video_frame_callback,
        media_stream_constraints={"video": True, "audio": False},
        async_processing=True,
    )

    if "last_barcode" in st.session_state:
        result_placeholder.success(
            f"Codigo detectado: **{st.session_state['last_barcode']}**"
        )


if __name__ == "__page__" or __name__ == "__main__":
    main()
