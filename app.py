import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(page_title="Jaime Sanchez Gomez – Airbnb Dashboard",
                   page_icon="🏠", layout="wide")

# ── Load data ─────────────────────────────────────────────────────────────────
@st.cache_data
def load_data():
    df = pd.read_csv("airbnb.csv")
    # Fix messy last column name
    df.columns = [c.replace(";;", "").strip() for c in df.columns]
    df = df.dropna(subset=["price", "room_type", "neighbourhood"])
    df = df[df["price"] > 0]
    return df

df = load_data()

# ── Title ─────────────────────────────────────────────────────────────────────
st.title("Jaime Sanchez Gomez")
st.subheader("🏠 Airbnb Madrid – Interactive Dashboard")
st.markdown("---")

# ── SIDEBAR – Filters ─────────────────────────────────────────────────────────
with st.sidebar:
    st.header("🔍 Filters")

    # Room type filter
    room_types = sorted(df["room_type"].dropna().unique().tolist())
    selected_rooms = st.multiselect("Room type", room_types, default=room_types)

    # Neighbourhood group filter
    ng_options = sorted(df["neighbourhood_group"].dropna().unique().tolist())
    selected_ng = st.multiselect("District (neighbourhood group)", ng_options, default=ng_options)

    # Price range filter
    price_min, price_max = int(df["price"].min()), int(df["price"].quantile(0.99))
    price_range = st.slider("Price range (€/night)", price_min, price_max,
                            (price_min, price_max))

    # Min reviews filter
    min_reviews = st.slider("Minimum number of reviews", 0,
                            int(df["number_of_reviews"].max()), 0)

    st.markdown("---")
    st.caption("Dashboard by Jaime Sanchez Gomez")

# ── Apply filters ─────────────────────────────────────────────────────────────
filtered = df[
    df["room_type"].isin(selected_rooms) &
    df["neighbourhood_group"].isin(selected_ng) &
    df["price"].between(price_range[0], price_range[1]) &
    (df["number_of_reviews"] >= min_reviews)
]

# ── KPI row ───────────────────────────────────────────────────────────────────
k1, k2, k3, k4 = st.columns(4)
k1.metric("Total listings", f"{len(filtered):,}")
k2.metric("Avg price (€/night)", f"{filtered['price'].mean():.1f}")
k3.metric("Avg reviews / month", f"{filtered['reviews_per_month'].mean():.2f}")
k4.metric("Neighbourhoods", f"{filtered['neighbourhood'].nunique()}")

st.markdown("---")

# ══════════════════════════════════════════════════════════════════════════════
# TABS
# ══════════════════════════════════════════════════════════════════════════════
tab1, tab2 = st.tabs(["📊 Data Analysis", "🤖 Price Simulator"])

# ─────────────────────────────────────────────────────────────────────────────
# TAB 1 – Data Analysis
# ─────────────────────────────────────────────────────────────────────────────
with tab1:

    # ── Row 1: Listing type vs accommodates ──────────────────────────────────
    st.subheader("1 · Relationship between listing type and number of people")
    col1, col2 = st.columns(2)

    with col1:
        # Box plot: room_type vs minimum_nights as proxy for "people capacity"
        # We use minimum_nights; the dataset has no "accommodates" column so we
        # use price tiers. Best available: count by room_type
        room_counts = (filtered.groupby("room_type")
                       .size().reset_index(name="count"))
        fig1 = px.bar(room_counts, x="room_type", y="count",
                      color="room_type",
                      title="Number of listings by room type",
                      labels={"room_type": "Room type", "count": "# Listings"},
                      color_discrete_sequence=px.colors.qualitative.Pastel)
        fig1.update_layout(showlegend=False)
        st.plotly_chart(fig1, use_container_width=True)

    with col2:
        # Avg price by room type → proxy for "people" (entire homes cost more)
        avg_price_rt = (filtered.groupby("room_type")["price"]
                        .mean().reset_index(name="avg_price"))
        fig2 = px.bar(avg_price_rt, x="room_type", y="avg_price",
                      color="room_type",
                      title="Average price by room type",
                      labels={"room_type": "Room type", "avg_price": "Avg price (€)"},
                      color_discrete_sequence=px.colors.qualitative.Pastel)
        fig2.update_layout(showlegend=False)
        st.plotly_chart(fig2, use_container_width=True)

    st.markdown("---")

    # ── Row 2: Two more graphs ────────────────────────────────────────────────
    st.subheader("2 · Top neighbourhoods by reviews per month")
    col3, col4 = st.columns(2)

    with col3:
        top_n = st.slider("Top N neighbourhoods", 5, 20, 10, key="topn")
        top_neigh = (filtered.groupby("neighbourhood")["reviews_per_month"]
                     .mean()
                     .nlargest(top_n)
                     .reset_index())
        top_neigh.columns = ["neighbourhood", "avg_reviews_per_month"]
        fig3 = px.bar(top_neigh, x="avg_reviews_per_month", y="neighbourhood",
                      orientation="h",
                      title=f"Top {top_n} neighbourhoods – avg reviews/month",
                      labels={"avg_reviews_per_month": "Avg reviews/month",
                              "neighbourhood": "Neighbourhood"},
                      color="avg_reviews_per_month",
                      color_continuous_scale="Blues")
        fig3.update_layout(yaxis={"categoryorder": "total ascending"},
                           coloraxis_showscale=False)
        st.plotly_chart(fig3, use_container_width=True)

    with col4:
        # Scatter: number_of_reviews vs price (cap price for readability)
        _scatter_df = filtered[filtered["price"] <= 400]
        sample = _scatter_df.sample(
            min(2000, len(_scatter_df)), random_state=42)
        fig4 = px.scatter(sample, x="number_of_reviews", y="price",
                          color="room_type",
                          title="Number of reviews vs Price",
                          labels={"number_of_reviews": "# Reviews",
                                  "price": "Price (€/night)",
                                  "room_type": "Room type"},
                          opacity=0.5,
                          color_discrete_sequence=px.colors.qualitative.Bold)
        st.plotly_chart(fig4, use_container_width=True)

    st.markdown("---")

    # ── Row 3: Map ────────────────────────────────────────────────────────────
    st.subheader("3 · Listing map")
    map_sample = filtered.dropna(subset=["latitude", "longitude"]).sample(
        min(3000, len(filtered)), random_state=1)
    fig_map = px.scatter_mapbox(
        map_sample, lat="latitude", lon="longitude",
        color="room_type", size="price",
        hover_name="name",
        hover_data={"price": True, "neighbourhood": True,
                    "number_of_reviews": True},
        zoom=10, height=500,
        title="Listing locations (sample)",
        color_discrete_sequence=px.colors.qualitative.Bold
    )
    fig_map.update_layout(mapbox_style="open-street-map", margin={"r":0,"t":40,"l":0,"b":0})
    st.plotly_chart(fig_map, use_container_width=True)

# ─────────────────────────────────────────────────────────────────────────────
# TAB 2 – Price Simulator
# ─────────────────────────────────────────────────────────────────────────────
with tab2:
    st.subheader("🤖 Price Simulator")
    st.markdown(
        "Enter the characteristics of your apartment and we will recommend "
        "a **price range** based on similar listings in the dataset."
    )

    sim_col1, sim_col2 = st.columns(2)

    with sim_col1:
        sim_ng = st.selectbox("District", sorted(df["neighbourhood_group"].dropna().unique()))
        sim_rt = st.selectbox("Room type", sorted(df["room_type"].dropna().unique()))
        sim_min_nights = st.number_input("Minimum nights", min_value=1, max_value=30, value=2)

    with sim_col2:
        sim_reviews = st.slider("Expected reviews per month", 0.0, 10.0, 1.0, 0.1)
        sim_availability = st.slider("Availability (days/year)", 0, 365, 180)

    if st.button("💡 Get price recommendation", use_container_width=True):
        # Filter similar listings
        similar = df[
            (df["neighbourhood_group"] == sim_ng) &
            (df["room_type"] == sim_rt) &
            (df["price"] > 0)
        ]

        if len(similar) < 5:
            st.warning("Not enough similar listings to make a recommendation. Try different filters.")
        else:
            p25 = similar["price"].quantile(0.25)
            p50 = similar["price"].quantile(0.50)
            p75 = similar["price"].quantile(0.75)

            st.success(f"Based on **{len(similar):,}** similar listings in **{sim_ng}**:")

            r1, r2, r3 = st.columns(3)
            r1.metric("💰 Budget range (P25)", f"€{p25:.0f}/night")
            r2.metric("🎯 Recommended (median)", f"€{p50:.0f}/night")
            r3.metric("⭐ Premium range (P75)", f"€{p75:.0f}/night")

            # Price distribution of similar listings
            fig_sim = px.histogram(
                similar[similar["price"] <= similar["price"].quantile(0.95)],
                x="price", nbins=40,
                title=f"Price distribution – {sim_rt} in {sim_ng}",
                labels={"price": "Price (€/night)", "count": "# Listings"},
                color_discrete_sequence=["#FF5A5F"]
            )
            fig_sim.add_vline(x=p50, line_dash="dash", line_color="green",
                              annotation_text=f"Median: €{p50:.0f}")
            st.plotly_chart(fig_sim, use_container_width=True)

            st.info(
                f"💡 **Tip:** A listing with your characteristics in {sim_ng} "
                f"typically prices between **€{p25:.0f}** and **€{p75:.0f}** per night. "
                f"We recommend starting around **€{p50:.0f}** to stay competitive."
            )
