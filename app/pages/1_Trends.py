import plotly.express as px
import streamlit as st

from utils import apply_css, apply_filters, line_trend, load_data

st.title("Trends (1945–2020)")
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

st.plotly_chart(
    line_trend(filtered, "engine_hp", "Average Horsepower Over Time", "Horsepower"),
    width='stretch',
)
st.plotly_chart(
    line_trend(
        filtered,
        "acceleration_0_100_km_h_s",
        "Average 0–100 km/h Acceleration Over Time",
        "Seconds",
    ),
    width='stretch',
)

if "number_of_cylinders" in filtered.columns:
    cyl_by_year = (
        filtered.dropna(subset=["year", "number_of_cylinders"])
        .groupby("year", as_index=False)["number_of_cylinders"]
        .median()
    )
    fig_cyl = px.line(
        cyl_by_year,
        x="year",
        y="number_of_cylinders",
        title="Median Cylinder Count Over Time",
        markers=True,
    )
    st.plotly_chart(fig_cyl, width='stretch')

st.plotly_chart(
    line_trend(filtered, "co2_emissions_g_km", "Average CO2 Emissions Over Time", "g/km"),
    width='stretch',
)
