from __future__ import annotations

import os

import pandas as pd
import streamlit as st

from safestep.admin_auth import authenticate_admin
from safestep.deployments import DeploymentRegistry, SignalDeployment
from safestep.models import PedSignal
from safestep.simulation import SCENARIOS, new_simulation, step_simulation
from safestep.state_machine import SignalState


registry = DeploymentRegistry()

st.set_page_config(page_title="SafeStep", layout="wide")
st.title("SafeStep")


def render_simulation_canvas(sim_state, orchestrator) -> str:
    phase = orchestrator.state_machine.state
    vehicle_green = phase == SignalState.VEHICLE_GREEN
    ped_walk = orchestrator.controller.state.ped_signal == PedSignal.WALK

    left_light = "#31c56b" if ped_walk else "#e14c4c"
    right_light = "#31c56b" if ped_walk else "#e14c4c"
    vehicle_color = "#2bbf6a" if vehicle_green else "#d64545"

    cars_svg: list[str] = []
    for x in sim_state.cars_eastbound:
        cars_svg.append(f'<rect x="{x:.1f}" y="138" width="38" height="18" rx="3" fill="#2196f3"/>')
    for x in sim_state.cars_westbound:
        cars_svg.append(f'<rect x="{x - 38:.1f}" y="205" width="38" height="18" rx="3" fill="#ff9800"/>')

    svg = f"""
    <svg viewBox="0 0 900 360" width="100%" height="360" xmlns="http://www.w3.org/2000/svg">
      <rect x="0" y="0" width="900" height="360" fill="#9ccc65"/>
      <rect x="150" y="95" width="600" height="170" fill="#424242"/>
      <line x1="150" y1="180" x2="750" y2="180" stroke="#f9f17a" stroke-width="3" stroke-dasharray="16 10"/>
      <rect x="420" y="95" width="60" height="170" fill="#fafafa" opacity="0.15"/>
      <g fill="#fefefe">
        <rect x="427" y="100" width="8" height="160"/>
        <rect x="442" y="100" width="8" height="160"/>
        <rect x="457" y="100" width="8" height="160"/>
      </g>
      <rect x="150" y="95" width="8" height="170" fill="{vehicle_color}"/>
      <rect x="742" y="95" width="8" height="170" fill="{vehicle_color}"/>
      <circle cx="392" cy="82" r="14" fill="{left_light}"/>
      <circle cx="508" cy="82" r="14" fill="{right_light}"/>
      <text x="332" y="86" font-size="12" fill="#ffffff">Ped Light</text>
      <text x="514" y="86" font-size="12" fill="#ffffff">Ped Light</text>
      <text x="26" y="60" font-size="16" fill="#1f3d1f">Sidewalk</text>
      <text x="784" y="60" font-size="16" fill="#1f3d1f">Sidewalk</text>
      {''.join(cars_svg)}
    </svg>
    """
    return svg


def render_showcase() -> None:
    st.subheader("Simulation Showcase")
    st.caption("This visualization uses SafeStep orchestration directly; if core logic stalls, the simulation stalls too.")

    scenario_key = st.selectbox(
        "Choose a scenario",
        options=list(SCENARIOS.keys()),
        format_func=lambda key: SCENARIOS[key].name,
    )

    if "sim_orchestrator" not in st.session_state or st.session_state.get("sim_scenario") != scenario_key:
        orchestrator, sim_state = new_simulation(scenario_key)
        st.session_state.sim_orchestrator = orchestrator
        st.session_state.sim_state = sim_state
        st.session_state.sim_scenario = scenario_key

    st.info(SCENARIOS[scenario_key].description)

    col_a, col_b, col_c = st.columns([1, 1, 1])
    with col_a:
        if st.button("Advance 1 second", use_container_width=True):
            st.session_state.sim_state = step_simulation(st.session_state.sim_orchestrator, st.session_state.sim_state)
    with col_b:
        if st.button("Advance 10 seconds", use_container_width=True):
            for _ in range(10):
                st.session_state.sim_state = step_simulation(st.session_state.sim_orchestrator, st.session_state.sim_state)
    with col_c:
        if st.button("Reset scenario", use_container_width=True):
            orchestrator, sim_state = new_simulation(scenario_key)
            st.session_state.sim_orchestrator = orchestrator
            st.session_state.sim_state = sim_state

    sim_state = st.session_state.sim_state
    orchestrator = st.session_state.sim_orchestrator

    st.markdown(render_simulation_canvas(sim_state, orchestrator), unsafe_allow_html=True)

    phase = orchestrator.state_machine.state.value
    ped_signal = orchestrator.controller.state.ped_signal.value

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("t (seconds)", sim_state.tick)
    c2.metric("Signal state", phase)
    c3.metric("Pedestrian signal", ped_signal)
    c4.metric("Waiting pedestrians", int(sim_state.ped_left_waiting + sim_state.ped_right_waiting))
    c5.metric("Last outcome", sim_state.last_outcome.value)

    st.write(
        {
            "left_sidewalk_waiting": round(sim_state.ped_left_waiting, 2),
            "right_sidewalk_waiting": round(sim_state.ped_right_waiting, 2),
            "cars_lane_eastbound": len(sim_state.cars_eastbound),
            "cars_lane_westbound": len(sim_state.cars_westbound),
            "crosswalk_occupied": sim_state.crossing_people > 0,
            "model_decision": sim_state.last_outcome.value,
        }
    )


admin_tab, showcase_tab = st.tabs(["Admin dashboard", "Simulation showcase"])

with showcase_tab:
    render_showcase()

with admin_tab:
    st.subheader("SafeStep Admin Dashboard")

    admin_user = os.getenv("SAFESTEP_ADMIN_USER", "admin")
    admin_pass = os.getenv("SAFESTEP_ADMIN_PASSWORD", "admin123")

    if "authed" not in st.session_state:
        st.session_state.authed = False

    if not st.session_state.authed:
        st.caption(
            "Use the configured credential values (defaults: username `admin`, password `admin123`). "
            "If needed, entering env var keys such as `SAFESTEP_ADMIN_USER` will resolve to their values."
        )
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            if authenticate_admin(username, password, admin_user, admin_pass):
                st.session_state.authed = True
                st.success("Logged in")
                st.rerun()
            else:
                st.error("Invalid credentials")
        st.stop()

    st.subheader("Deployed Signals")

    with st.form("add_signal"):
        signal_id = st.text_input("Signal ID", placeholder="SIG-001")
        location = st.text_input("Location", placeholder="Main St & 4th")
        controller_endpoint = st.text_input("Controller Endpoint", placeholder="tcp://controller.local:502")
        emergency_contact = st.text_input("Emergency Contact", placeholder="911")
        camera_ids_raw = st.text_area("Camera IDs (comma-separated)", placeholder="CAM-01,CAM-02")

        submitted = st.form_submit_button("Add / Update Deployment")

        if submitted:
            camera_ids = [item.strip() for item in camera_ids_raw.split(",") if item.strip()]
            if not signal_id.strip() or not location.strip() or not controller_endpoint.strip() or not emergency_contact.strip():
                st.error("Please fill all required deployment fields.")
            else:
                registry.add_deployment(
                    SignalDeployment(
                        signal_id=signal_id.strip(),
                        location=location.strip(),
                        controller_endpoint=controller_endpoint.strip(),
                        emergency_contact=emergency_contact.strip(),
                        camera_ids=camera_ids,
                    )
                )
                st.success(f"Deployment saved: {signal_id.strip()}")

    rows = []
    for deployment in registry.list_deployments():
        rows.append(
            {
                "Signal ID": deployment.signal_id,
                "Location": deployment.location,
                "Controller Endpoint": deployment.controller_endpoint,
                "Emergency Contact": deployment.emergency_contact,
                "Camera IDs": ", ".join(deployment.camera_ids),
                "Camera Count": len(deployment.camera_ids),
            }
        )

    if rows:
        st.dataframe(pd.DataFrame(rows), use_container_width=True)
    else:
        st.info("No deployed signals yet. Add one above.")

    st.subheader("Connected Cameras")
    selected_signal = st.selectbox(
        "Select Signal",
        options=[d.signal_id for d in registry.list_deployments()],
        index=None,
        placeholder="Choose a signal",
    )

    if selected_signal:
        connections = registry.get_camera_connections(selected_signal)
        camera_rows = [{"Camera ID": c.camera_id, "Connected": c.connected} for c in connections]
        if camera_rows:
            st.dataframe(pd.DataFrame(camera_rows), use_container_width=True)
        else:
            st.warning("No cameras configured for this signal.")
