"""Shared Streamlit utilities for Engine Atlas."""

from __future__ import annotations

from pathlib import Path
import sys
import json
import urllib.parse
import urllib.request

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.append(str(SRC))

from engine_atlas.data_processing import clean_engine_data


DATA_PATH = ROOT / "data" / "Car Dataset 1945-2020.csv"
WIKI_API_URL = "https://en.wikipedia.org/w/api.php"


def apply_css() -> None:
    css = ROOT.joinpath("assets/styles.css").read_text()
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


@st.cache_data(show_spinner=False)
def load_data() -> pd.DataFrame:
    return clean_engine_data(str(DATA_PATH))


def apply_filters(
    df: pd.DataFrame,
    makes: list[str],
    years: tuple[int, int],
    engine_types: list[str],
    cylinders: list[int],
) -> pd.DataFrame:
    filtered = df.copy()
    if makes:
        filtered = filtered[filtered["make"].isin(makes)]
    if engine_types:
        filtered = filtered[filtered["engine_type"].isin(engine_types)]
    if cylinders:
        filtered = filtered[filtered["number_of_cylinders"].isin(cylinders)]
    if "year" in filtered.columns:
        filtered = filtered[
            (filtered["year"] >= years[0]) & (filtered["year"] <= years[1])
        ]
    return filtered


def compute_clusters(df: pd.DataFrame, k: int = 4) -> pd.DataFrame:
    features = [
        "engine_hp",
        "acceleration_0_100_km_h_s",
        "mixed_fuel_consumption_per_100_km_l",
        "number_of_cylinders",
    ]
    subset = df[features].dropna()
    scaler = StandardScaler()
    scaled = scaler.fit_transform(subset)
    kmeans = KMeans(n_clusters=k, random_state=42, n_init="auto")
    labels = kmeans.fit_predict(scaled)
    subset = subset.copy()
    subset["cluster_id"] = labels

    pca = PCA(n_components=2, random_state=42)
    coords = pca.fit_transform(scaled)
    subset["pca_1"] = coords[:, 0]
    subset["pca_2"] = coords[:, 1]

    cluster_names = label_clusters(kmeans.cluster_centers_, features)
    subset["cluster_name"] = subset["cluster_id"].map(cluster_names)
    return subset


def label_clusters(centers: np.ndarray, features: list[str]) -> dict[int, str]:
    labels: dict[int, str] = {}
    feature_idx = {name: idx for idx, name in enumerate(features)}
    for idx, center in enumerate(centers):
        hp = center[feature_idx["engine_hp"]]
        accel = center[feature_idx["acceleration_0_100_km_h_s"]]
        fuel = center[feature_idx["mixed_fuel_consumption_per_100_km_l"]]
        cylinders = center[feature_idx["number_of_cylinders"]]

        if fuel < -0.5:
            labels[idx] = "Efficient"
        elif hp > 0.7:
            labels[idx] = "High Power"
        elif accel < -0.3:
            labels[idx] = "Quick Accel"
        elif cylinders > 0.6:
            labels[idx] = "Big Cyl"
        else:
            labels[idx] = "Balanced"
    return labels


def line_trend(df: pd.DataFrame, y_col: str, title: str, y_label: str):
    data = df.dropna(subset=["year", y_col])
    grouped = data.groupby("year", as_index=False)[y_col].mean()
    fig = px.line(grouped, x="year", y=y_col, title=title, markers=True)
    fig.update_layout(yaxis_title=y_label)
    return fig


def _wiki_request(params: dict[str, str]) -> dict:
    query = urllib.parse.urlencode(params)
    url = f"{WIKI_API_URL}?{query}"
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "EngineAtlas/1.0 (https://example.com)"},
    )
    with urllib.request.urlopen(request, timeout=10) as response:
        payload = response.read().decode("utf-8")
    return json.loads(payload)


def _fetch_wikipedia_image_url(query: str) -> str | None:
    if not query:
        return None
    direct = _wiki_request(
        {
            "action": "query",
            "format": "json",
            "prop": "pageimages",
            "piprop": "original",
            "titles": query,
        }
    )
    pages = direct.get("query", {}).get("pages", {})
    if pages:
        first_page = next(iter(pages.values()), {})
        image_url = first_page.get("original", {}).get("source")
        if image_url:
            return image_url
    search = _wiki_request(
        {
            "action": "query",
            "format": "json",
            "list": "search",
            "srsearch": query,
            "srlimit": "1",
        }
    )
    results = search.get("query", {}).get("search", [])
    if not results:
        return None
    title = results[0].get("title")
    if not title:
        return None
    page = _wiki_request(
        {
            "action": "query",
            "format": "json",
            "prop": "pageimages",
            "piprop": "original",
            "titles": title,
        }
    )
    pages = page.get("query", {}).get("pages", {})
    if not pages:
        return None
    first_page = next(iter(pages.values()), {})
    return first_page.get("original", {}).get("source")


@st.cache_data(show_spinner=False, ttl=86400)
def get_wikipedia_image_url(queries: tuple[str, ...]) -> str | None:
    for query in queries:
        url = _fetch_wikipedia_image_url(query)
        if url:
            return url
    return None
