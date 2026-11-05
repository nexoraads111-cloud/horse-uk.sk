"""Enumerate audio input/output devices."""

from __future__ import annotations

from typing import Any


def list_input_devices() -> list[dict[str, Any]]:
    try:
        import sounddevice as sd

        devices = sd.query_devices()
        hostapis = sd.query_hostapis()
        result = []
        for i, d in enumerate(devices):
            if d["max_input_channels"] > 0:
                api = hostapis[d["hostapi"]]["name"] if d["hostapi"] < len(hostapis) else ""
                result.append(
                    {
                        "index": i,
                        "name": d["name"],
                        "channels": d["max_input_channels"],
                        "sample_rate": d["default_samplerate"],
                        "hostapi": api,
                    }
                )
        return result
    except Exception:
        return []


def list_output_devices() -> list[dict[str, Any]]:
    try:
        import sounddevice as sd

        devices = sd.query_devices()
        result = []
        for i, d in enumerate(devices):
            if d["max_output_channels"] > 0:
                result.append(
                    {
                        "index": i,
                        "name": d["name"],
                        "channels": d["max_output_channels"],
                        "sample_rate": d["default_samplerate"],
                    }
                )
        return result
    except Exception:
        return []
