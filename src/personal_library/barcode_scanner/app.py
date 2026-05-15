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
        data = barcode.data.decode("utf-8", errors="replace")
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
                self.result = decoded_values[0]
            return annotated_frame

    def get_result(self) -> str | None:
        with self._lock:
            return self.result


def main() -> None:
    import time

    from personal_library.barcode_scanner.webrtc_shutdown_patch import (
        apply_session_shutdown_observer_patch,
    )

    apply_session_shutdown_observer_patch()

    import httpx
    import streamlit as st
    from streamlit_webrtc import WebRtcMode, webrtc_streamer

    from personal_library.barcode_scanner.isbn_lookup import (
        default_api_base,
        lookup_book_for_scan,
    )

    st.set_page_config(page_title="Lector de Codigos de Barras", layout="centered")
    st.title("Lector de codigos de barras")

    if "scanned_barcode" in st.session_state:
        scanned = st.session_state["scanned_barcode"]

        if st.session_state.get("book_lookup_for") != scanned:
            base = default_api_base()
            with st.spinner("Buscando libro en la API..."):
                with httpx.Client() as client:
                    payload, error = lookup_book_for_scan(scanned, base, client)
            st.session_state["book_lookup_for"] = scanned
            st.session_state["book_payload"] = payload
            st.session_state["book_lookup_error"] = error

        st.success(f"Codigo detectado: **{scanned}**")

        if st.session_state.get("book_lookup_error"):
            st.error(st.session_state["book_lookup_error"])

        book = st.session_state.get("book_payload")
        if book:
            st.subheader(book["title"])
            if book.get("authors"):
                st.write(", ".join(book["authors"]))
            cover_url = book.get("cover_image_url")
            if cover_url:
                st.image(cover_url)
            description = book.get("description")
            if description:
                with st.expander("Descripcion"):
                    st.write(description)

        if st.button("Escanear otro"):
            keys_to_clear = (
                "scanned_barcode",
                "book_lookup_for",
                "book_payload",
                "book_lookup_error",
            )
            for key in keys_to_clear:
                st.session_state.pop(key, None)
            st.session_state["scan_count"] = (
                st.session_state.get("scan_count", 0) + 1
            )
            st.rerun()
        return

    st.write("Pulsa **START** para abrir la camara y escanear un codigo de barras.")

    # La key cambia con cada escaneo para forzar la reinicializacion del
    # componente WebRTC en el navegador; sin esto la camara no se reabre.
    scan_key = f"barcode-scanner-{st.session_state.get('scan_count', 0)}"

    ctx = webrtc_streamer(
        key=scan_key,
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
            # streamlit-webrtc no expone callbacks al hilo principal, por lo
            # que se necesita polling. 200 ms es un compromiso entre latencia
            # de deteccion y carga de servidor; aceptable para uso local.
            time.sleep(0.2)
            st.rerun()


if __name__ == "__page__" or __name__ == "__main__":
    main()
