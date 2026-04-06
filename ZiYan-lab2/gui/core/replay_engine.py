#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Replay Engine

Loads historical CSV data and provides indexed playback operations.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import pandas as pd

from core.data_parser import SensorData


@dataclass
class ReplayMeta:
    """Metadata for loaded replay file."""
    file_path: str
    total_frames: int
    start_time: Optional[datetime]
    end_time: Optional[datetime]


class ReplayEngine:
    """CSV replay engine with timeline index and speed control."""

    def __init__(self) -> None:
        self.df = pd.DataFrame(columns=["timestamp", "temperature", "humidity", "oled_state"])
        self.current_index = 0
        self.speed = 1.0
        self.meta: Optional[ReplayMeta] = None

    def load_csv(self, file_path: str) -> bool:
        """Load CSV file and normalize columns."""
        csv_path = Path(file_path)
        if not csv_path.exists() or csv_path.suffix.lower() != ".csv":
            return False

        try:
            raw = pd.read_csv(csv_path)
        except Exception:
            return False

        col_map = self._resolve_columns(raw)
        if col_map is None:
            return False

        normalized = pd.DataFrame(
            {
                "timestamp": pd.to_datetime(raw[col_map["timestamp"]], errors="coerce"),
                "temperature": pd.to_numeric(raw[col_map["temperature"]], errors="coerce"),
                "humidity": pd.to_numeric(raw[col_map["humidity"]], errors="coerce"),
                "oled_state": raw[col_map["oled_state"]],
            }
        )

        normalized = normalized.dropna(subset=["temperature", "humidity"]).reset_index(drop=True)
        if normalized.empty:
            return False

        # Normalize oled_state to bool
        normalized["oled_state"] = normalized["oled_state"].astype(str).str.strip().str.lower().isin(
            ["1", "true", "on", "yes"]
        )

        # Fill invalid timestamps with synthetic 2-second spacing
        now = datetime.now()
        fallback_times = [now + timedelta(seconds=i * 2) for i in range(len(normalized))]
        normalized["timestamp"] = normalized["timestamp"].where(
            normalized["timestamp"].notna(), pd.Series(fallback_times)
        )

        self.df = normalized
        self.current_index = 0
        self.speed = 1.0
        self.meta = ReplayMeta(
            file_path=str(csv_path),
            total_frames=len(self.df),
            start_time=self.df["timestamp"].iloc[0].to_pydatetime(),
            end_time=self.df["timestamp"].iloc[-1].to_pydatetime(),
        )
        return True

    def _resolve_columns(self, df: pd.DataFrame) -> Optional[dict]:
        """Resolve required columns in a case-insensitive manner."""
        lower_map = {c.lower(): c for c in df.columns}
        candidates = {
            "timestamp": ["timestamp", "time", "datetime"],
            "temperature": ["temperature", "temp"],
            "humidity": ["humidity", "humi"],
            "oled_state": ["oled_state", "oled", "state"],
        }
        resolved = {}
        for key, names in candidates.items():
            found = next((lower_map[n] for n in names if n in lower_map), None)
            if found is None:
                return None
            resolved[key] = found
        return resolved

    def is_loaded(self) -> bool:
        return self.meta is not None and not self.df.empty

    def total_frames(self) -> int:
        return len(self.df)

    def set_speed(self, speed: float) -> None:
        self.speed = speed if speed > 0 else 1.0

    def seek(self, index: int) -> None:
        if not self.is_loaded():
            self.current_index = 0
            return
        self.current_index = max(0, min(index, self.total_frames() - 1))

    def step_forward(self) -> bool:
        """Move to next frame. Returns False when already at end."""
        if not self.is_loaded():
            return False
        if self.current_index >= self.total_frames() - 1:
            return False
        self.current_index += 1
        return True

    def step_backward(self) -> bool:
        if not self.is_loaded() or self.current_index <= 0:
            return False
        self.current_index -= 1
        return True

    def current_frame(self) -> Optional[SensorData]:
        if not self.is_loaded():
            return None
        row = self.df.iloc[self.current_index]
        return SensorData(
            timestamp=row["timestamp"].to_pydatetime(),
            temperature=float(row["temperature"]),
            humidity=float(row["humidity"]),
            oled_state=bool(row["oled_state"]),
            raw_line=(
                f"DATA,{float(row['temperature']):.1f},"
                f"{float(row['humidity']):.1f},"
                f"{1 if bool(row['oled_state']) else 0}"
            ),
        )

