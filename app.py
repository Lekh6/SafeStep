from __future__ import annotations

import pandas as pd
import streamlit as st

from safestep.prototype import DEFAULT_PITCH_SCENARIO, run_pitch_scenario

st.set_page_config(page_title="SafeStep Pitch Prototype", layout="wide")
st.title("🚦 SafeStep Pitch Prototype")
st.caption("Interactive scenario replay for pedestrian-first smart crossing control.")

with st.sidebar:
    st.header("Scenario Controls")
    max_step = len(DEFAULT_PITCH_SCENARIO)
    step = st.slider("Replay first N ticks", min_value=1, max_value=max_step, value=max_step)
    run_btn = st.button("Run Scenario")

if run_btn or "results" not in st.session_state:
    ticks = DEFAULT_PITCH_SCENARIO[:step]
    st.session_state.results = run_pitch_scenario(ticks=ticks)

results = st.session_state.results
rows = [
    {
        "second": r.second,
        "decision": r.outcome.value,
        "mode": r.mode,
        "ped_signal": r.ped_signal,
        "vehicle_phase": r.vehicle_phase,
        "logged_events": r.event_count,
    }
    for r in results
]

df = pd.DataFrame(rows)

c1, c2, c3 = st.columns(3)
c1.metric("Ticks processed", len(df))
c2.metric("Final mode", df.iloc[-1]["mode"])
c3.metric("Violation/incident records", int(df.iloc[-1]["logged_events"]))

st.subheader("Decision Timeline")
st.dataframe(df, use_container_width=True)

decision_counts = df["decision"].value_counts().rename_axis("decision").reset_index(name="count")
st.subheader("Decision Distribution")
st.bar_chart(decision_counts.set_index("decision"))

st.info(
    "Prototype highlights: dynamic pedestrian prioritization, emergency all-red, violation logging, and mode transitions for pitch storytelling."
)
