import streamlit as st

from components.engine_dna import EngineDNA, render_engine_dna
from utils import apply_css, apply_filters, get_wikipedia_image_url, load_data

st.set_page_config(page_title="Engine Atlas", layout="wide")
apply_css()

df = load_data()

st.title("Engine Atlas")
st.caption("Data-driven analysis of car engine performance, efficiency, and evolution (1945–2020).")

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

def mean_or_na(series, fmt: str) -> str:
    value = series.mean()
    if value != value:
        return "N/A"
    return fmt.format(value)

col1, col2, col3, col4 = st.columns(4)
col1.metric("Models", f"{filtered['model'].nunique():,}")
col2.metric("Avg HP", mean_or_na(filtered["engine_hp"], "{:.0f}"))
col3.metric(
    "Avg 0-100",
    f"{mean_or_na(filtered['acceleration_0_100_km_h_s'], '{:.1f}')}s",
)
col4.metric(
    "Avg CO2",
    f"{mean_or_na(filtered['co2_emissions_g_km'], '{:.0f}')} g/km",
)

st.subheader("Engine DNA Card")
if filtered.empty:
    st.info("No rows match the current filters.")
else:
    dna_fields = [
        "make",
        "model",
        "trim",
        "engine_type",
        "cylinder_layout",
        "number_of_cylinders",
        "engine_hp",
        "displacement_l",
        "acceleration_0_100_km_h_s",
        "mixed_fuel_consumption_per_100_km_l",
    ]
    sample_pool = filtered.dropna(subset=dna_fields)
    if sample_pool.empty:
        sample = filtered.dropna(subset=["make", "model"]).iloc[0]
    else:
        sample = sample_pool.iloc[0]
    dna = EngineDNA(
        make=str(sample.get("make", "")),
        model=str(sample.get("model", "")),
        trim=str(sample.get("trim", "")),
        engine_type=str(sample.get("engine_type", "")),
        cylinder_layout=str(sample.get("cylinder_layout", "")),
        cylinders=sample.get("number_of_cylinders"),
        hp=sample.get("engine_hp"),
        displacement_l=sample.get("displacement_l"),
        accel=sample.get("acceleration_0_100_km_h_s"),
        fuel=sample.get("mixed_fuel_consumption_per_100_km_l"),
    )
    st.markdown(render_engine_dna(dna), unsafe_allow_html=True)

    st.subheader("Vehicle Images")
    make = dna.make.strip()
    model = dna.model.strip()
    trim = dna.trim.strip()
    car_queries = tuple(
        q
        for q in [
            " ".join(part for part in [make, model, trim, "car"] if part),
            " ".join(part for part in [make, model, "car"] if part),
        ]
        if q
    )
    car_image = get_wikipedia_image_url(car_queries)
    st.markdown("**Car photo**")
    if car_image:
        st.image(car_image, width="stretch")
    else:
        st.info("No car image found on Wikipedia.")
