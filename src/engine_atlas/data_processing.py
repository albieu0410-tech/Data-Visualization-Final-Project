"""Data loading and feature engineering for Engine Atlas."""

from __future__ import annotations

import math
import re
from dataclasses import dataclass
from typing import Iterable

import numpy as np
import pandas as pd


NUMERIC_COLUMNS = [
    "year_from",
    "year_to",
    "engine_hp",
    "max_power_kw",
    "engine_hp_rpm",
    "maximum_torque_n_m",
    "acceleration_0_100_km_h_s",
    "mixed_fuel_consumption_per_100_km_l",
    "city_fuel_per_100km_l",
    "highway_fuel_per_100km_l",
    "co2_emissions_g_km",
    "battery_capacity_kw_per_h",
    "electric_range_km",
    "charging_time_h",
    "number_of_cylinders",
    "valves_per_cylinder",
]


OUTLIER_BOUNDS = {
    "engine_hp": (20, 2000),
    "max_power_kw": (10, 1500),
    "acceleration_0_100_km_h_s": (1.0, 40.0),
    "mixed_fuel_consumption_per_100_km_l": (1.0, 40.0),
    "co2_emissions_g_km": (0.0, 1000.0),
    "number_of_cylinders": (1, 16),
}


@dataclass
class SchemaReport:
    rows: int
    cols: int
    missing_by_col: pd.Series


def load_raw_csv(path: str) -> pd.DataFrame:
    return pd.read_csv(path, low_memory=False)


def standardize_columns(df: pd.DataFrame) -> pd.DataFrame:
    def to_snake(name: str) -> str:
        name = name.strip().lower()
        name = re.sub(r"[\\/]+", "_", name)
        name = re.sub(r"[()\\[\\]]", "", name)
        name = re.sub(r"[\s\-]+", "_", name)
        name = re.sub(r"__+", "_", name)
        return name

    df = df.copy()
    df.columns = [to_snake(c) for c in df.columns]
    if "modle" in df.columns and "model" not in df.columns:
        df = df.rename(columns={"modle": "model"})
    if "acceleration_0_100_km_h_" in df.columns and "acceleration_0_100_km_h_s" not in df.columns:
        df = df.rename(columns={"acceleration_0_100_km_h_": "acceleration_0_100_km_h_s"})
    return df


def coerce_numeric(df: pd.DataFrame, cols: Iterable[str]) -> pd.DataFrame:
    df = df.copy()
    for col in cols:
        if col not in df.columns:
            continue
        cleaned = (
            df[col]
            .astype(str)
            .str.replace(",", "", regex=False)
            .str.replace(r"[^0-9.\\-]", "", regex=True)
        )
        df[col] = pd.to_numeric(cleaned, errors="coerce")
    return df


def parse_bore_stroke(value: str) -> tuple[float | None, float | None]:
    if not isinstance(value, str):
        return None, None
    numbers = re.findall(r"[0-9]+(?:\\.[0-9]+)?", value)
    if len(numbers) >= 2:
        return float(numbers[0]), float(numbers[1])
    if len(numbers) == 1:
        return float(numbers[0]), None
    return None, None


def compute_displacement_l(
    bore_mm: float | None, stroke_mm: float | None, cylinders: float | None
) -> float | None:
    if bore_mm is None or stroke_mm is None or cylinders is None:
        return None
    if bore_mm <= 0 or stroke_mm <= 0 or cylinders <= 0:
        return None
    volume_mm3 = math.pi * (bore_mm / 2.0) ** 2 * stroke_mm * cylinders
    return volume_mm3 / 1_000_000.0


def add_engine_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    if "year_from" in df.columns:
        df["year"] = df["year_from"]

    bore = None
    stroke = None
    if "cylinder_bore_and_stroke_cycle_mm" in df.columns:
        parsed = df["cylinder_bore_and_stroke_cycle_mm"].apply(parse_bore_stroke)
        bore = parsed.apply(lambda x: x[0])
        stroke = parsed.apply(lambda x: x[1])
    if "cylinder_bore_mm" in df.columns:
        if bore is None:
            bore = df["cylinder_bore_mm"]
        else:
            bore = bore.fillna(df["cylinder_bore_mm"])

    df["bore_mm"] = bore
    df["stroke_mm"] = stroke

    if "number_of_cylinders" in df.columns:
        cylinders = df["number_of_cylinders"]
    else:
        cylinders = pd.Series([None] * len(df), index=df.index)

    df["displacement_l"] = [
        compute_displacement_l(b, s, c)
        for b, s, c in zip(df["bore_mm"], df["stroke_mm"], cylinders)
    ]
    if "capacity_cm3" in df.columns:
        capacity_l = pd.to_numeric(df["capacity_cm3"], errors="coerce") / 1000.0
        df["displacement_l"] = df["displacement_l"].fillna(capacity_l)

    if "engine_hp" in df.columns:
        df["hp_per_liter"] = df["engine_hp"] / df["displacement_l"]

    def _text_series(col: str) -> pd.Series:
        if col in df.columns:
            return df[col].astype(str).str.strip()
        return pd.Series([""] * len(df), index=df.index)

    displacement_l = pd.to_numeric(df["displacement_l"], errors="coerce")

    df["engine_signature"] = (
        _text_series("make")
        + " "
        + _text_series("engine_type")
        + " "
        + _text_series("cylinder_layout")
        + " "
        + _text_series("number_of_cylinders")
        + " "
        + displacement_l.round(2).astype(str)
        + "L"
    ).str.replace("nan", "", regex=False).str.strip()

    df["balanced_score"] = compute_balanced_score(df)
    return df


def compute_balanced_score(df: pd.DataFrame) -> pd.Series:
    metrics = {
        "engine_hp": 1.0,
        "acceleration_0_100_km_h_s": -1.0,
        "mixed_fuel_consumption_per_100_km_l": -1.0,
        "co2_emissions_g_km": -1.0,
    }
    zscores = []
    for col, weight in metrics.items():
        if col not in df.columns:
            continue
        series = df[col]
        mean = series.mean(skipna=True)
        std = series.std(skipna=True)
        if std == 0 or np.isnan(std):
            z = pd.Series(0.0, index=df.index)
        else:
            z = (series - mean) / std
        zscores.append(z * weight)
    if not zscores:
        return pd.Series(np.nan, index=df.index)
    stacked = pd.concat(zscores, axis=1)
    return stacked.mean(axis=1, skipna=True)


def clip_outliers(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    for col, (low, high) in OUTLIER_BOUNDS.items():
        if col in df.columns:
            df[col] = df[col].clip(lower=low, upper=high)
    return df


def schema_report(df: pd.DataFrame) -> SchemaReport:
    missing = df.isna().sum().sort_values(ascending=False)
    return SchemaReport(rows=df.shape[0], cols=df.shape[1], missing_by_col=missing)


def clean_engine_data(path: str) -> pd.DataFrame:
    df = load_raw_csv(path)
    df = standardize_columns(df)
    df = coerce_numeric(df, NUMERIC_COLUMNS)
    df = clip_outliers(df)
    df = add_engine_features(df)
    return df
