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
        video_frame_callback=_make_callback(st),
        media_stream_constraints={"video": True, "audio": False},
        async_processing=True,
    )

    if ctx.state.playing and "pending_barcode" in st.session_state:
        st.session_state["scanned_barcode"] = st.session_state.pop("pending_barcode")
        st.rerun()


def _make_callback(st):  # type: ignore[no-untyped-def]
    """Return a video frame callback that writes the first detected barcode."""

    def video_frame_callback(frame: av.VideoFrame) -> av.VideoFrame:
        if "pending_barcode" in st.session_state:
            return frame
        annotated_frame, decoded_values = process_frame(frame)
        if decoded_values:
            st.session_state["pending_barcode"] = decoded_values[0]
        return annotated_frame

    return video_frame_callback


if __name__ == "__page__" or __name__ == "__main__":
    main()
