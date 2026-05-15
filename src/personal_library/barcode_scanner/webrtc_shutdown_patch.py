"""Mitigate race in streamlit-webrtc SessionShutdownObserver.stop().

When ICE disconnects, asyncio may invoke ``stop()`` concurrently. One call can set
``_polling_thread`` to ``None`` before another reaches ``is_alive()`` on the
shared attribute, causing ``AttributeError``. Holding the thread in a local and
only clearing when still assigned avoids that.
"""

from __future__ import annotations

import logging
import threading
from typing import Any

logger = logging.getLogger(__name__)


def _safe_stop(self: Any, timeout: float = 1.0) -> None:
    thread = getattr(self, "_polling_thread", None)
    if thread is None:
        return

    self._polling_thread_stop_event.set()

    if threading.current_thread() is not thread:
        thread.join(timeout=timeout)
        if thread.is_alive():
            logger.warning("ShutdownPolling thread did not exit cleanly")
        else:
            logger.debug("ShutdownPolling thread stopped cleanly")
    else:
        logger.debug("Stop called from polling thread itself, skipping join.")

    if self._polling_thread is thread:
        self._polling_thread = None


def apply_session_shutdown_observer_patch() -> None:
    import streamlit_webrtc.shutdown as shutdown

    shutdown.SessionShutdownObserver.stop = _safe_stop  # type: ignore[method-assign]
