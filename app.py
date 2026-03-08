# ThermalGuard - main app
import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from dotenv import load_dotenv
import os

from utils.physics import calculate_wet_bulb, apply_clothing_adjustment, categorize_risk, get_activity_modifier
from utils.weather_api import get_current_weather, get_forecast, search_cities

load_dotenv()

# Page setup
st.set_page_config(page_title="ThermalGuard DSS", page_icon="TG", layout="wide")

# Minimal styling - just dark theme basics
st.markdown("""
<style>
    .stApp { background-color: #0d1117; }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# Environment variables
API_KEY = os.getenv("OPENWEATHER_API_KEY", "")

# Title
st.title("ThermalGuard DSS")
st.caption("Occupational Heat Stress Decision Support System — OSHA / NIOSH Compliant")

st.divider()

# --- Control Panel ---
st.subheader("Control Panel")

col1, col2, col3 = st.columns([2, 2, 2])

with col1:
    location_query = st.text_input(
        "Location / City Search",
        value="",
        placeholder="e.g. Dubai, New York, Tokyo",
        help="Type any city in the world to fetch live data"
    )

    suggestions = search_cities(location_query, API_KEY, limit=5)

    if suggestions:
        loc_map = {s["label"]: s for s in suggestions}
        location_label = st.selectbox("Select Location", options=list(loc_map.keys()))
        selected_loc = loc_map.get(location_label)
    elif location_query:
        st.error("No results found. Try a different spelling.")
        selected_loc = None
    else:
        selected_loc = None

with col2:
    activity = st.selectbox(
        "Activity Intensity",
        options=["Light", "Moderate", "Heavy"],
        index=1,
        help="Light: inspecting, sitting  |  Moderate: walking, carrying  |  Heavy: excavation, climbing"
    )

with col3:
    st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
    ppe_on = st.toggle("Heavy PPE / Protective Clothing", value=False, help="Adds +5°C penalty per OSHA guidelines")
    acclimatized = st.checkbox("Crew is Acclimatized (>14 days)", value=True, help="Unacclimatized workers have stricter safety thresholds")

activity_info = get_activity_modifier(activity)
st.caption(f"**Activity Profile**: {activity_info['label']} — *{activity_info['examples']}* (Metabolic Rate: ≤{activity_info['metabolic_w']} W)")

st.divider()

# --- Main Logic ---
if selected_loc:
    weather = get_current_weather(selected_loc["lat"], selected_loc["lon"], API_KEY)
    wet_bulb = calculate_wet_bulb(weather["temp_c"], weather["humidity"])
    adjusted_tw = apply_clothing_adjustment(wet_bulb, ppe_on)
    risk = categorize_risk(adjusted_tw, acclimatized, activity)
else:
    st.warning("Please type a location in the search box to begin the safety assessment.")
    st.stop()

# --- Current Conditions ---
st.subheader(f"Current Conditions — {weather['city_name']}, {weather.get('country', '')}")

m1, m2, m3, m4 = st.columns(4)
m1.metric("Ambient Temp", f"{weather['temp_c']}°C")
m2.metric("Humidity", f"{weather['humidity']}%")
m3.metric("Wind Speed", f"{weather['wind_speed_kmh']} km/h")
m4.metric("Wet Bulb (Adj.)", f"{adjusted_tw}°C", delta=f"{round(adjusted_tw - risk['thresholds'][0], 1)}°C from safe limit")

st.divider()

# --- Safety Assessment ---
st.subheader("Safety Assessment")

gauge_col, info_col = st.columns([3, 2])

with gauge_col:
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=adjusted_tw,
        number={"suffix": "°C", "font": {"size": 48, "color": "white"}},
        delta={"reference": risk["thresholds"][0], "suffix": "°C", "increasing": {"color": "#ff5252"}, "decreasing": {"color": "#69f0ae"}},
        title={"text": "Adjusted Wet Bulb Temperature", "font": {"size": 16, "color": "rgba(255,255,255,0.7)"}},
        gauge={
            "axis": {
                "range": [10, 45],
                "tickwidth": 1,
                "tickcolor": "rgba(255,255,255,0.3)",
                "tickfont": {"color": "rgba(255,255,255,0.5)"},
            },
            "bar": {"color": risk["color"], "thickness": 0.3},
            "bgcolor": "rgba(255,255,255,0.05)",
            "borderwidth": 0,
            "steps": [
                {"range": [10, risk["thresholds"][0]], "color": "rgba(0, 200, 83, 0.2)"},
                {"range": [risk["thresholds"][0], risk["thresholds"][1]], "color": "rgba(255, 214, 0, 0.2)"},
                {"range": [risk["thresholds"][1], risk["thresholds"][2]], "color": "rgba(255, 109, 0, 0.2)"},
                {"range": [risk["thresholds"][2], risk["thresholds"][3]], "color": "rgba(255, 23, 68, 0.2)"},
                {"range": [risk["thresholds"][3], 45], "color": "rgba(213, 0, 0, 0.25)"},
            ],
            "threshold": {
                "line": {"color": "white", "width": 3},
                "thickness": 0.8,
                "value": adjusted_tw,
            },
        },
    ))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=300,
        margin=dict(t=60, b=20, l=40, r=40),
    )
    st.plotly_chart(fig, use_container_width=True)

with info_col:
    # Risk level
    st.markdown(f"### Risk Level: **{risk['level']}**")

    st.markdown(f"""
    | Metric | Value |
    |--------|-------|
    | Raw Wet Bulb | {wet_bulb}°C |
    | PPE Penalty | {"+ 5.0°C" if ppe_on else "None"} |
    | Acclimatized | {"Yes" if acclimatized else "No — Stricter Thresholds"} |
    """)

# Alert messages
if risk["level"] in ("Danger", "Extreme Danger"):
    for action in risk["actions"]:
        st.error(action)
elif risk["level"] == "Warning":
    for action in risk["actions"]:
        st.warning(action)
elif risk["level"] == "Caution":
    for action in risk["actions"]:
        st.warning(action)
elif risk["level"] == "Safe":
    st.success("Conditions are within safe limits. Normal operations may proceed.")

st.divider()

# --- SOPs ---
st.subheader("Mandated Safety Instructions (SOPs)")

sop1, sop2 = st.columns(2)

with sop1:
    st.info(f"**Work / Rest Schedule**\n\n{risk['work_rest']}")

with sop2:
    st.info(f"**Hydration Protocol**\n\n{risk['hydration']}")

st.divider()

# --- Predictive Planner ---
st.subheader("Predictive Planner — Next 24 Hours")

forecast_data = get_forecast(selected_loc["lat"], selected_loc["lon"], API_KEY)

if forecast_data:
    fc_df = pd.DataFrame(forecast_data)
    fc_df["wet_bulb"] = fc_df.apply(lambda r: calculate_wet_bulb(r["temp_c"], r["humidity"]), axis=1)
    fc_df["adjusted_tw"] = fc_df["wet_bulb"].apply(lambda tw: apply_clothing_adjustment(tw, ppe_on))
    fc_df["time"] = pd.to_datetime(fc_df["timestamp"])

    safe_threshold = risk["thresholds"][0]
    danger_threshold = risk["thresholds"][2]

    fig_fc = go.Figure()

    # Safe zone
    fig_fc.add_hrect(
        y0=0, y1=safe_threshold,
        fillcolor="rgba(0, 200, 83, 0.15)", line_width=0,
        annotation_text="Safe Zone", annotation_position="top left",
        annotation=dict(font_size=12, font_color="#00e676", font_weight="bold")
    )

    # Danger zone
    fig_fc.add_hrect(
        y0=danger_threshold, y1=55,
        fillcolor="rgba(255, 61, 0, 0.15)", line_width=0,
        annotation_text="Danger Zone", annotation_position="bottom left",
        annotation=dict(font_size=12, font_color="#ff5252", font_weight="bold")
    )

    # Threshold lines
    fig_fc.add_hline(y=safe_threshold, line=dict(color="#00e676", dash="dash", width=2))
    fig_fc.add_hline(y=danger_threshold, line=dict(color="#ff5252", dash="dash", width=2))

    # Ambient temp line
    fig_fc.add_trace(go.Scatter(
        x=fc_df["time"], y=fc_df["temp_c"],
        name="Ambient Temp",
        line=dict(color="rgba(255,255,255,0.3)", width=2, dash="dot"),
    ))

    # Wet bulb line
    fig_fc.add_trace(go.Scatter(
        x=fc_df["time"], y=fc_df["adjusted_tw"],
        name="Adj. Wet Bulb",
        line=dict(color="#74b9ff", width=3),
        fill="tozeroy",
        fillcolor="rgba(116, 185, 255, 0.08)",
    ))

    fig_fc.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=350,
        margin=dict(t=30, b=40, l=50, r=30),
        legend=dict(
            orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1,
            font=dict(color="rgba(255,255,255,0.6)", size=11),
        ),
        xaxis=dict(
            gridcolor="rgba(255,255,255,0.05)",
            tickfont=dict(color="rgba(255,255,255,0.5)"),
            title="Time",
            title_font=dict(color="rgba(255,255,255,0.4)"),
        ),
        yaxis=dict(
            gridcolor="rgba(255,255,255,0.05)",
            tickfont=dict(color="rgba(255,255,255,0.5)"),
            title="Temperature (°C)",
            title_font=dict(color="rgba(255,255,255,0.4)"),
        ),
    )
    st.plotly_chart(fig_fc, use_container_width=True)
else:
    st.info("Forecast data unavailable. Check your API key configuration.")

st.divider()

# --- Assessment Summary ---
st.subheader("Assessment Summary")

summary_data = {
    "Metric": ["Location", "Ambient Temp", "Humidity", "Wind Speed", "Raw Wet Bulb", "Adjusted Wet Bulb", "PPE Active", "Acclimatized", "Activity Level", "Risk Level", "Work/Rest", "Hydration"],
    "Value": [
        f"{weather['city_name']}, {weather.get('country', '')}",
        f"{weather['temp_c']}°C",
        f"{weather['humidity']}%",
        f"{weather['wind_speed_kmh']} km/h",
        f"{wet_bulb}°C",
        f"{adjusted_tw}°C",
        "Yes (+5°C)" if ppe_on else "No",
        "Yes" if acclimatized else "No",
        activity,
        risk["level"],
        risk["work_rest"],
        risk["hydration"],
    ]
}

st.dataframe(pd.DataFrame(summary_data), use_container_width=True, hide_index=True)

st.divider()

# Footer
st.caption("ThermalGuard DSS v1.0 — Built with Streamlit · Powered by OpenWeatherMap · OSHA/NIOSH Compliant")
