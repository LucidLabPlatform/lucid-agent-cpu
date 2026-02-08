from __future__ import annotations

import logging
import threading
from datetime import datetime, timezone
from typing import Optional

import psutil
from lucid_agent_core.components.base import Component


class CpuMonitorComponent(Component):
    component_id = "cpu_monitor"
    _PUBLISH_INTERVAL_SECONDS = 5.0

    def __init__(self, context):
        super().__init__(context)
        self.context = context
        self.logger = logging.getLogger(f"lucid.component.{self.component_id}")
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._temperature_available = True

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return

        self._temperature_available = self._detect_temperature_available()
        if not self._temperature_available:
            self.logger.info("CPU temperature is unavailable on this host")

        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._run_loop,
            name="CpuMonitorComponentLoop",
            daemon=True,
        )
        self._thread.start()
        self.logger.info("Component started: %s", self.component_id)

    def stop(self) -> None:
        thread = self._thread
        if not thread:
            return

        self._stop_event.set()
        thread.join(timeout=1.0)
        self._thread = None
        self.logger.info("Component stopped: %s", self.component_id)

    def _run_loop(self) -> None:
        while not self._stop_event.is_set():
            try:
                self._publish_metrics()
            except Exception:
                self.logger.exception("Failed to publish CPU metrics")
            if self._stop_event.wait(self._PUBLISH_INTERVAL_SECONDS):
                break

    def _publish_metrics(self) -> None:
        cpu_percent = float(psutil.cpu_percent(interval=None))
        temperature_c = self._read_temperature()
        payload = {
            "cpu_percent": cpu_percent,
            "temperature_c": temperature_c,
            "timestamp": self._utc_timestamp(),
        }
        topic = f"lucid/agents/{self.context.agent_id}/status/{self.component_id}/metrics"
        self.context.mqtt.publish(topic, payload, qos=0, retain=False)
        self.logger.debug("Published CPU metrics: %s", payload)

    def _read_temperature(self) -> Optional[float]:
        if not self._temperature_available:
            return None

        entries = self._temperature_entries()
        for entry in entries:
            current = getattr(entry, "current", None)
            if current is None:
                continue
            try:
                return float(current)
            except (TypeError, ValueError):
                continue
        return None

    def _detect_temperature_available(self) -> bool:
        return bool(self._temperature_entries())

    def _temperature_entries(self) -> list[object]:
        sensors_fn = getattr(psutil, "sensors_temperatures", None)
        if not callable(sensors_fn):
            return []

        try:
            sensors = sensors_fn()
        except Exception:
            return []

        if not isinstance(sensors, dict):
            return []

        entries: list[object] = []
        for values in sensors.values():
            if isinstance(values, list):
                entries.extend(values)
        return entries

    @staticmethod
    def _utc_timestamp() -> str:
        return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
