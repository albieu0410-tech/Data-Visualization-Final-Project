import plotly.express as px
import streamlit as st

from utils import apply_css, apply_filters, compute_clusters, load_data

st.title("Engine Clusters")
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

if filtered.dropna(
    subset=[
        "engine_hp",
        "acceleration_0_100_km_h_s",
        "mixed_fuel_consumption_per_100_km_l",
        "number_of_cylinders",
    ]
).empty:
    st.info("Not enough data to compute clusters for the current filters.")
    st.stop()

clustered = compute_clusters(filtered, k=4)

fig = px.scatter(
    clustered,
    x="pca_1",
    y="pca_2",
    color="cluster_name",
    hover_data=[
        "engine_hp",
        "number_of_cylinders",
        "acceleration_0_100_km_h_s",
        "mixed_fuel_consumption_per_100_km_l",
    ],
    title="Engine Families (PCA Projection of KMeans Clusters)",
)
st.plotly_chart(fig, width="stretch")

st.subheader("Cluster Summary")
summary = (
    clustered.groupby("cluster_name", as_index=False)[
        [
            "engine_hp",
            "acceleration_0_100_km_h_s",
            "mixed_fuel_consumption_per_100_km_l",
            "number_of_cylinders",
        ]
    ]
    .mean()
    .round(2)
)
st.dataframe(summary, width="stretch")
