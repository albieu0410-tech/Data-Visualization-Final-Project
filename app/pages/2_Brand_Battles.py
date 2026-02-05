import plotly.express as px
import streamlit as st

from utils import apply_css, apply_filters, load_data

st.title("Brand Battles")
apply_css()

df = load_data()

with st.sidebar:
    st.header("Filters")
    make_options = sorted(df["make"].dropna().unique().tolist())
    engine_options = sorted(df["engine_type"].dropna().unique().tolist())
    cylinder_options = (
        df["number_of_cylinders"].dropna().sort_values().unique().astype(int).tolist()
    )
    min_year = int(df["year"].min())
    max_year = int(df["year"].max())
    selected_makes = st.multiselect("Brand", make_options)
    selected_engine = st.multiselect("Engine type", engine_options)
    selected_cyl = st.multiselect("Cylinders", cylinder_options)
    selected_years = st.slider("Year range", min_year, max_year, (min_year, max_year))

filtered = apply_filters(df, selected_makes, selected_years, selected_engine, selected_cyl)

st.subheader("Median Horsepower by Brand")
hp_by_make = (
    filtered.dropna(subset=["make", "engine_hp"])
    .groupby("make", as_index=False)["engine_hp"]
    .median()
    .sort_values("engine_hp", ascending=False)
    .head(20)
)
fig_hp = px.bar(
    hp_by_make,
    x="engine_hp",
    y="make",
    orientation="h",
    title="Top 20 Brands by Median Horsepower",
)
st.plotly_chart(fig_hp, width='stretch')

st.subheader("Median Fuel Consumption by Brand")
fuel_by_make = (
    filtered.dropna(subset=["make", "mixed_fuel_consumption_per_100_km_l"])
    .groupby("make", as_index=False)["mixed_fuel_consumption_per_100_km_l"]
    .median()
    .sort_values("mixed_fuel_consumption_per_100_km_l", ascending=True)
    .head(20)
)
fig_fuel = px.bar(
    fuel_by_make,
    x="mixed_fuel_consumption_per_100_km_l",
    y="make",
    orientation="h",
    title="Top 20 Brands by Efficiency (Lower is Better)",
)
st.plotly_chart(fig_fuel, width='stretch')

st.subheader("Horsepower Distribution by Brand")
sampled = (
    filtered.dropna(subset=["make", "engine_hp"])
    .groupby("make")
    .filter(lambda g: len(g) >= 50)
)
fig_box = px.box(
    sampled,
    x="make",
    y="engine_hp",
    title="Horsepower Distribution (Brands with 50+ rows)",
)
fig_box.update_layout(xaxis_tickangle=45)
st.plotly_chart(fig_box, width='stretch')
