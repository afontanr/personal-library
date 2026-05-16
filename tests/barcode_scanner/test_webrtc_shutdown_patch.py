import threading

from personal_library.barcode_scanner.webrtc_shutdown_patch import (
    _safe_stop,
    apply_session_shutdown_observer_patch,
)


class FakeObserver:
    def __init__(self, polling_thread=None):
        self._polling_thread = polling_thread
        self._polling_thread_stop_event = threading.Event()


def test_safe_stop_no_polling_thread():
    obs = FakeObserver()
    _safe_stop(obs)

    assert obs._polling_thread is None


def test_safe_stop_with_active_thread():
    started = threading.Event()
    done = threading.Event()

    def worker():
        started.set()
        done.wait()

    thread = threading.Thread(target=worker)
    obs = FakeObserver(polling_thread=thread)
    thread.start()
    started.wait()

    _safe_stop(obs)
    thread.join(timeout=1.0)

    assert obs._polling_thread is None
    assert obs._polling_thread_stop_event.is_set()


def test_safe_stop_already_cleared_by_concurrent_call():
    started = threading.Event()
    done = threading.Event()

    def worker():
        started.set()
        done.wait()

    thread = threading.Thread(target=worker)
    obs = FakeObserver(polling_thread=thread)
    thread.start()
    started.wait()

    obs._polling_thread = None

    _safe_stop(obs)
    thread.join(timeout=1.0)

    assert obs._polling_thread is None


def test_safe_stop_called_from_polling_thread():
    started = threading.Event()
    return_flag = threading.Event()

    def worker():
        obs2 = FakeObserver(polling_thread=threading.current_thread())
        started.set()
        _safe_stop(obs2, timeout=0.1)
        return_flag.set()

    thread = threading.Thread(target=worker)
    thread.start()
    started.wait()
    thread.join(timeout=1.0)

    assert return_flag.is_set()


def test_safe_stop_thread_does_not_exit_cleanly():
    running = threading.Event()
    block = threading.Event()

    def worker():
        running.set()
        block.wait()

    thread = threading.Thread(target=worker, daemon=True)
    obs = FakeObserver(polling_thread=thread)
    thread.start()
    running.wait()

    _safe_stop(obs, timeout=0.05)

    assert obs._polling_thread is None
    assert thread.is_alive()


def test_apply_patch_replaces_stop_method():
    apply_session_shutdown_observer_patch()

    import streamlit_webrtc.shutdown as shutdown

    assert shutdown.SessionShutdownObserver.stop is _safe_stop
