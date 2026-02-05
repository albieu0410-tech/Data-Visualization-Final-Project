import plotly.express as px
import streamlit as st

from utils import apply_css, apply_filters, load_data

st.title("Best Engines")
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

col1, col2 = st.columns(2)

with col1:
    st.subheader("Fastest 0–100 km/h")
    fastest = (
        filtered.dropna(subset=["acceleration_0_100_km_h_s"])
        .nsmallest(15, "acceleration_0_100_km_h_s")
    )
    fig_fast = px.bar(
        fastest,
        x="acceleration_0_100_km_h_s",
        y="engine_signature",
        orientation="h",
        title="Top 15 Fastest Trims",
    )
    st.plotly_chart(fig_fast, width='stretch')

with col2:
    st.subheader("Most Powerful")
    powerful = filtered.dropna(subset=["engine_hp"]).nlargest(15, "engine_hp")
    fig_power = px.bar(
        powerful,
        x="engine_hp",
        y="engine_signature",
        orientation="h",
        title="Top 15 Highest Horsepower",
    )
    st.plotly_chart(fig_power, width='stretch')

col3, col4 = st.columns(2)

with col3:
    st.subheader("Most Efficient")
    efficient = (
        filtered.dropna(subset=["mixed_fuel_consumption_per_100_km_l"])
        .nsmallest(15, "mixed_fuel_consumption_per_100_km_l")
    )
    fig_eff = px.bar(
        efficient,
        x="mixed_fuel_consumption_per_100_km_l",
        y="engine_signature",
        orientation="h",
        title="Top 15 Most Efficient (Lower is Better)",
    )
    st.plotly_chart(fig_eff, width='stretch')

with col4:
    st.subheader("Best Power Density")
    density = filtered.dropna(subset=["hp_per_liter"]).nlargest(15, "hp_per_liter")
    fig_density = px.bar(
        density,
        x="hp_per_liter",
        y="engine_signature",
        orientation="h",
        title="Top 15 HP per Liter",
    )
    st.plotly_chart(fig_density, width='stretch')

st.subheader("Balanced Score Leaderboard")
balanced = filtered.dropna(subset=["balanced_score"]).nlargest(15, "balanced_score")
fig_bal = px.bar(
    balanced,
    x="balanced_score",
    y="engine_signature",
    orientation="h",
    title="Top 15 Balanced Engines (Composite Score)",
)
st.plotly_chart(fig_bal, width='stretch')
