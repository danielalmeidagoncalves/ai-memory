from __future__ import annotations

import threading

from memoria.gardener.gardener import Gardener


class MemoryScheduler:
    def __init__(self, gardener: Gardener) -> None:
        self._gardener = gardener
        self._scheduler: object | None = None
        self._timer: threading.Timer | None = None
        self._running = False
        self._lock = threading.Lock()
        self._apscheduler_available = False

        try:
            from apscheduler.schedulers.background import BackgroundScheduler

            self._scheduler = BackgroundScheduler()
            self._apscheduler_available = True
        except ImportError:
            self._apscheduler_available = False

    @property
    def using_apscheduler(self) -> bool:
        return self._apscheduler_available and self._scheduler is not None

    def start(self, interval_seconds: int = 3600) -> None:
        with self._lock:
            if self._running:
                return
            self._running = True

        if self.using_apscheduler:
            self._start_apscheduler(interval_seconds)
        else:
            self._start_threading(interval_seconds)

    def _start_apscheduler(self, interval_seconds: int) -> None:
        from apscheduler.schedulers.background import BackgroundScheduler

        assert isinstance(self._scheduler, BackgroundScheduler)
        self._scheduler.add_job(
            self._gardener.run,
            "interval",
            seconds=interval_seconds,
            id="memoria_garden",
            replace_existing=True,
        )
        self._scheduler.start()

    def _start_threading(self, interval_seconds: int) -> None:
        self._run_threading_loop(interval_seconds)

    def _run_threading_loop(self, interval_seconds: int) -> None:
        with self._lock:
            if not self._running:
                return

        try:
            self._gardener.run()
        except Exception:
            pass

        with self._lock:
            if not self._running:
                return
            self._timer = threading.Timer(
                float(interval_seconds),
                self._run_threading_loop,
                args=[interval_seconds],
            )
            self._timer.daemon = True
            self._timer.start()

    def stop(self) -> None:
        with self._lock:
            self._running = False
            if self._timer is not None:
                self._timer.cancel()
                self._timer = None

        if self.using_apscheduler and self._scheduler is not None:
            self._scheduler.shutdown(wait=False)
            from apscheduler.schedulers.background import BackgroundScheduler

            assert isinstance(self._scheduler, BackgroundScheduler)
            self._scheduler = BackgroundScheduler()

    @property
    def is_running(self) -> bool:
        with self._lock:
            return self._running
